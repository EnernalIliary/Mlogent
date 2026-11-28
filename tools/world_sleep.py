#!/usr/bin/env python3
"""On-demand world owner: save only when empty, retain a small ArcNet proxy.

Linux service entry point. The private backend port MUST be firewalled from
remote hosts. MCP access uses a mode-0600 Unix socket; no public admin API.
"""
import argparse
import asyncio
import base64
import json
import logging
import math
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time

import world_client
from world_sleep_protocol import Proxy, SLEEP_TEXT, WAKE_TEXT, RUNNING_TITLE, RUNNING_DESCRIPTION, discovery, running_discovery
from world_ops_bridge import running_description, player_limit

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / 'out/_world'

CHECK = r"""
var live=false, q=this._mcpWorldWork, now=java.lang.System.currentTimeMillis();
if(q){for(var k in q.leases){if(q.leases[k]>now){live=true;}}}
var veto=this._mcpVeto;
if(veto){for(var key in veto.jobs){var job=veto.jobs[key];if(job.state==='pending'&&job.deadline>now-60000){live=true;}}}
var count=0,it=Vars.net.getConnections().iterator();while(it.hasNext()){var con=it.next();if(con.isConnected()){count++;}}
"""

INSPECT = CHECK + r"""
var buffer=Packages.mindustry.net.NetworkIO.writeServerData();
var wire=String(java.util.Base64.getEncoder().encodeToString(java.util.Arrays.copyOf(buffer.array(),buffer.position())));
sb.append(JSON.stringify({players:Groups.player.size(),connections:count,work:live,game:Vars.state.isGame(),discovery:wire}));
"""

SAVE = CHECK + r"""
if(Groups.player.size()!==0||count!==0||live||!Vars.state.isGame()){sb.append('busy');}
else{
 var file=new Packages.arc.files.Fi('config/saves/SAVENAME.msav');
 Packages.mindustry.io.SaveIO.save(file);
 if(!Packages.mindustry.io.SaveIO.isSaveValid(file)){throw new Error('Hibernate save validation failed');}
 /* Same game-thread action as the final empty/lease check. */
 Vars.net.closeServer();sb.append('saved');
}
"""

PROTOCOL = r"""
function encode(p){var b=java.nio.ByteBuffer.allocate(4096);
 new Packages.mindustry.net.ArcNetProvider.PacketSerializer().write(b,p);
 return String(java.util.Base64.getEncoder().encodeToString(java.util.Arrays.copyOf(b.array(),b.position())));}
var p=new Packages.mindustry.gen.KickCallPacket();p.reason=MESSAGE;
var b=Packages.mindustry.net.NetworkIO.writeServerData();
sb.append(JSON.stringify({kick:encode(p),discovery:String(java.util.Base64.getEncoder().encodeToString(java.util.Arrays.copyOf(b.array(),b.position()))),version:Packages.mindustry.core.Version.build}));
"""


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class Supervisor:
    def __init__(self, args):
        self.args = args
        self.lock = asyncio.Lock()
        self.child = None
        self.boot_task = None
        self.state = 'sleeping'
        self.manual_off = False
        self.last_activity = time.monotonic()
        self.last_error = None
        self.control_failures = 0
        self.thread_dumped = False
        self.state_path = WORLD / 'sleep-state.json'
        try:
            self.persisted = json.loads(self.state_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.persisted = {}
        self.kick_packet = base64.b64decode(self.persisted.get('kick', ''))
        self.version = self.persisted.get('version', 160)
        self.real_discovery = None
        self.proxy = Proxy(self, args.port, args.backend_port, args.bind)

    async def direct(self, request, timeout=30):
        # Explicit handshake bypasses the optional world_client supervisor route.
        hs = world_client.handshake()
        return await asyncio.to_thread(world_client.call, request, timeout, hs)

    async def js(self, code, timeout=30):
        result = await self.direct({'op': 'js', 'code': code}, timeout)
        if not result.get('ok') or not result.get('lines'):
            raise RuntimeError('World JS failed: ' + str(result))
        return result['lines'][0]

    def discovery_packet(self):
        if self.state == 'running' and self.real_discovery:
            return self.real_discovery
        text = WAKE_TEXT if self.state == 'waking' else SLEEP_TEXT
        map_name = self.persisted.get('status', {}).get('map') or self.args.map
        return discovery(text, self.args.port, self.version, map_name=map_name, player_limit=player_limit(30))

    def status(self):
        return {'ok': True, **self.persisted.get('status', {}),
                'sleepState': self.state, 'sleeping': self.state == 'sleeping',
                'hosted': self.state == 'running', 'gamePort': self.args.port,
                'backendPort': self.args.backend_port, 'players': 0, 'paused': True,
                'manualStop': self.manual_off, 'cached': True,
                'message': WAKE_TEXT if self.state == 'waking' else SLEEP_TEXT,
                'lastError': self.last_error}

    async def refresh(self):
        self.persisted['status'] = await self.direct({'op': 'status'})
        self.persisted['maps'] = await self.direct({'op': 'maps'})
        protocol = json.loads(await self.js(PROTOCOL.replace('MESSAGE', json.dumps(WAKE_TEXT, ensure_ascii=True))))
        self.kick_packet = base64.b64decode(protocol['kick'])
        self.version = protocol['version']
        self.real_discovery = running_discovery(base64.b64decode(protocol['discovery']), self.args.port,
                                                running_description(RUNNING_DESCRIPTION))
        self.persisted.update({k: protocol[k] for k in ('kick', 'version')})
        atomic_json(self.state_path, self.persisted)

    async def ensure_awake(self):
        if self.manual_off:
            raise RuntimeError('World was explicitly stopped; world_start is required')
        if self.state == 'running' and self.child and self.child.poll() is None:
            return
        if not self.boot_task or self.boot_task.done():
            self.boot_task = asyncio.create_task(self.boot())
        # A player's timeout must not cancel the shared boot of other players/MCP.
        await asyncio.shield(self.boot_task)

    async def boot(self):
        async with self.lock:
            if self.manual_off:
                raise RuntimeError('World explicitly stopped before boot')
            if self.state == 'running' and self.child and self.child.poll() is None:
                return
            self.state = 'waking'
            started = time.monotonic()
            WORLD.mkdir(parents=True, exist_ok=True)
            Path(world_client.HANDSHAKE).unlink(missing_ok=True)
            env = dict(os.environ, MLOG_WORLD_SLEEP_MANAGED='1')
            saved = self.persisted.get('save')
            if saved:
                if not re.fullmatch(r'mcp-hibernate-[0-9]+', saved):
                    raise RuntimeError('Invalid hibernation save name')
                env['MLOG_WORLD_RESUME_SAVE'] = saved
            command = [sys.executable, str(ROOT / 'tools/world_server.py'), '--map', self.args.map,
                       '--game-port', str(self.args.backend_port), '--java', self.args.java,
                       '--no-push-admin', '--paused', '--name', RUNNING_TITLE]
            self.child = subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=True)
            try:
                deadline = time.monotonic() + 100
                while time.monotonic() < deadline:
                    if self.child.poll() is not None:
                        raise RuntimeError('World startup process exited')
                    if Path(world_client.HANDSHAKE).exists():
                        info = await self.direct({'op': 'ping'}, timeout=5)
                        if info.get('ok'):
                            break
                    await asyncio.sleep(.2)
                else:
                    raise RuntimeError('World startup exceeded 100 seconds')
                if world_client.handshake()['gamePort'] != self.args.backend_port:
                    raise RuntimeError('World changed backend port; refusing a broken bridge')
                await self.refresh()
                await self.js("Core.settings.put('autoPause',true);sb.append('ready');")
                self.state = 'running'
                self.last_activity = time.monotonic()
                self.last_error = None
                logging.info('world awake in %.2fs', time.monotonic() - started)
            except BaseException as exc:
                self.last_error = str(exc)
                await self.stop_child()
                self.state = 'sleeping'
                raise

    async def restore_peer(self, identity, address):
        # ArcConnection.address is the game's authoritative IP for bans and trace.
        # The backend is private; only this trusted controller may set this value.
        code = """
var found=false,it=Vars.net.getConnections().iterator();while(it.hasNext()){var con=it.next();
 if(con.connection.getID()===IDENTITY){
  var f=java.lang.Class.forName('mindustry.net.NetConnection').getDeclaredField('address');
  f.setAccessible(true);f.set(con,ADDRESS);found=true;
 }}
if(!found){throw new Error('Proxy peer connection not found');}sb.append('ready');
""".replace('IDENTITY', str(int(identity))).replace('ADDRESS', json.dumps(address))
        async with self.lock:
            if await self.js(code) != 'ready':
                raise RuntimeError('Cannot restore original player IP')

    async def stop_child(self):
        child = self.child
        if child and child.poll() is None:
            try:
                await self.direct({'op': 'shutdown'}, timeout=8)
                await asyncio.to_thread(child.wait, 12)
            except Exception:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                    await asyncio.to_thread(child.wait, 5)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    pass
        if child:
            # Kill any JVM left in this owned session, including on daemon crash.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.child = None
        Path(world_client.HANDSHAKE).unlink(missing_ok=True)

    async def checkpoint_stop(self):
        """Called with the lifecycle lock held, before terminating a live JVM."""
        await self.refresh()
        name = 'mcp-hibernate-' + str(time.time_ns())
        code = SAVE.replace('SAVENAME', name).replace(
            'Groups.player.size()!==0||count!==0||live||!Vars.state.isGame()',
            '!Vars.state.isGame()')
        if await self.js(code, timeout=60) != 'saved':
            raise RuntimeError('Shutdown checkpoint was not saved; world left running')
        updated = {**self.persisted, 'save': name}
        try:
            atomic_json(self.state_path, updated)
        except Exception:
            # A disk/metadata error must not strand the live world behind a closed
            # listener, nor stop it using an obsolete recovery pointer.
            await self.js("if(!Vars.net.server()){Vars.netServer.openServer();}sb.append('ready');")
            raise
        self.persisted = updated
        return name

    def prune_saves(self):
        directory = WORLD / 'server/config/saves'
        snapshots = sorted((path for path in directory.glob('mcp-hibernate-*.msav')
                            if re.fullmatch(r'mcp-hibernate-[0-9]{19}', path.stem)), reverse=True)
        for path in snapshots[5:]:
            if path.stem != self.persisted.get('save'):
                path.unlink(missing_ok=True)

    async def try_sleep(self):
        async with self.lock:
            if self.state != 'running':
                return False
            inspect = json.loads(await self.js(INSPECT))
            self.control_failures = 0
            self.thread_dumped = False
            if inspect.get('discovery'):
                self.real_discovery = running_discovery(base64.b64decode(inspect['discovery']), self.args.port,
                                                        running_description(RUNNING_DESCRIPTION))
            # Front sessions include clients loading the world, before player join.
            if (inspect['players'] or inspect['connections'] or inspect['work']
                    or self.proxy.sessions or not inspect['game']):
                self.last_activity = time.monotonic()
                return False
            if time.monotonic() - self.last_activity < self.args.idle_seconds:
                return False
            await self.refresh()
            if self.proxy.sessions:
                self.last_activity = time.monotonic()
                return False
            name = 'mcp-hibernate-' + str(time.time_ns())
            self.state = 'saving'
            try:
                result = await self.js(SAVE.replace('SAVENAME', name), timeout=60)
            except BaseException:
                self.state = 'running'
                raise
            if result != 'saved':
                self.state = 'running'
                self.last_activity = time.monotonic()
                return False
            self.persisted['save'] = name
            atomic_json(self.state_path, self.persisted)
            await self.stop_child()
            self.state = 'sleeping'
            try:
                self.prune_saves()
            except OSError:
                logging.exception('snapshot retention cleanup failed')
            logging.info('empty world saved and sleeping: %s', name)
            return True

    def dump_java_threads(self):
        """Ask every Java descendant in the owned process tree for a JVM dump.

        SIGQUIT writes the dump to the JVM's existing stdout/stderr log. Keep the
        world alive: a failed control request does not prove that unsaved game
        state can be discarded safely.
        """
        child = self.child
        if not child or child.poll() is not None or not Path('/proc').is_dir():
            return False
        parents = {}
        commands = {}
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                stat = (entry / 'stat').read_text()
                tail = stat[stat.rfind(')') + 2:].split()
                parents[int(entry.name)] = int(tail[1])
                commands[int(entry.name)] = (entry / 'cmdline').read_bytes().replace(b'\\0', b' ').decode(errors='replace')
            except (OSError, ValueError, IndexError):
                continue
        descendants = {child.pid}
        changed = True
        while changed:
            more = {pid for pid, ppid in parents.items() if ppid in descendants}
            changed = not more.issubset(descendants)
            descendants.update(more)
        java_pids = [pid for pid in descendants if 'java' in commands.get(pid, '').lower()]
        for pid in java_pids:
            try:
                os.kill(pid, signal.SIGQUIT)
            except ProcessLookupError:
                continue
        if java_pids:
            logging.error('control API failed %d consecutive times; SIGQUIT thread dump requested for JVM pid(s) %s; world left running to protect unsaved progress',
                          self.control_failures, ','.join(map(str, java_pids)))
            return True
        logging.error('control API failed %d consecutive times; could not find JVM for thread dump; world left running',
                      self.control_failures)
        return False

    async def monitor(self):
        while True:
            # Status/discovery probing is intentionally low frequency; MCP
            # requests remain on demand and player wake-up stays immediate.
            await asyncio.sleep(15)
            try:
                if self.state == 'running':
                    if not self.child or self.child.poll() is not None:
                        await self.stop_child()
                        self.state = 'sleeping'
                        self.last_error = 'World process exited; latest hibernation save retained'
                    else:
                        await self.try_sleep()
            except Exception:
                # Fail closed: unknown occupancy / failed save never authorizes stop.
                logging.exception('idle inspection failed; leaving world running')
                self.control_failures += 1
                if self.control_failures >= 3 and not self.thread_dumped:
                    self.dump_java_threads()
                    self.thread_dumped = True

    async def dispatch(self, payload):
        op = payload.get('op')
        if op == 'supervisor_status':
            return self.status()
        if op == 'stop_if_sleeping':
            async with self.lock:
                if self.state != 'sleeping' or (self.child and self.child.poll() is None):
                    # Keep idle shutdown from racing the caller's next step:
                    # installing the in-game 60-second veto queue.
                    self.last_activity = time.monotonic()
                    return {'ok': True, 'handled': False}
                self.manual_off = True
                return {'ok': True, 'handled': True, 'status': 'stopped',
                        'bye': True, 'manualStop': True, 'sleeping': True}
        if op == 'idle_policy':
            value = float(payload['idleSeconds'])
            if not math.isfinite(value) or value < 10:
                raise ValueError('idleSeconds must be finite and >=10')
            self.args.idle_seconds = value
            return {'ok': True, 'idleSeconds': value}
        if op == 'start':
            if payload.get('arguments'):
                raise ValueError('Managed world_start currently accepts no overrides')
            self.manual_off = False
            await self.ensure_awake()
            status = await self.direct({'op': 'status'})
            status.update(gamePort=self.args.port, backendPort=self.args.backend_port, sleepState='running', sleeping=False)
            return {'ok': True, 'status': status, 'gamePort': self.args.port}
        if op != 'call':
            raise ValueError('Unknown private supervisor operation')
        req = payload['request']
        action = req.get('op')
        if action == 'shutdown':
            async with self.lock:
                # Explicit shutdown remains explicit; it does not wake a sleeping game.
                saved = self.persisted.get('save')
                if self.child and self.child.poll() is None:
                    previous_state = self.state
                    self.state = 'saving'
                    try:
                        saved = await self.checkpoint_stop()
                    except BaseException:
                        self.state = previous_state
                        raise
                self.manual_off = True
                await self.stop_child()
                self.state = 'sleeping'
                return {'ok': True, 'status': 'stopped', 'bye': True,
                        'manualStop': True, 'save': saved}
        if self.state != 'running':
            if action in ('status', 'ping'):
                return self.status()
            if action == 'players':
                return {'ok': True, 'rows': [], 'count': 0, 'truncated': False, 'sleeping': True}
            if action == 'maps':
                return {**self.persisted.get('maps', {'ok': True, 'maps': []}), 'cached': True, 'sleeping': True}
            if action in ('units', 'unit', 'buildings', 'building', 'logic', 'logic_code',
                          'logic_graph', 'logic_snapshot', 'logic_vars', 'changes', 'chat', 'push',
                          'doors', 'taps', 'projstat', 'sblog'):
                return {'ok': False, 'sleeping': True, 'error': 'World is sleeping; read-only query did not wake it'}
            await self.ensure_awake()
        async with self.lock:
            result = await self.direct(req, timeout=180)
            if action in ('ping', 'status') and result.get('ok'):
                result.update(gamePort=self.args.port, backendPort=self.args.backend_port, sleepState='running', sleeping=False)
            return result

    async def control(self, reader, writer):
        try:
            data = await asyncio.wait_for(reader.readline(), 5)
            result = await self.dispatch(json.loads(data))
        except Exception as exc:
            result = {'ok': False, 'supervisorError': True, 'error': str(exc)}
        try:
            writer.write((json.dumps(result, ensure_ascii=False) + '\n').encode())
            await writer.drain()
        finally:
            writer.close()

    async def run(self):
        WORLD.mkdir(parents=True, exist_ok=True)
        control = WORLD / 'sleep.sock'
        control.unlink(missing_ok=True)
        server = await asyncio.start_unix_server(self.control, str(control), limit=8 * 1024 * 1024)
        os.chmod(control, 0o600)
        await self.proxy.start()
        notify = os.environ.get('NOTIFY_SOCKET')
        if notify:
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as ready:
                ready.connect('\0' + notify[1:] if notify.startswith('@') else notify)
                ready.sendall(b'READY=1\nSTATUS=Sleep proxy ready')
        monitor = asyncio.create_task(self.monitor())
        stopping = asyncio.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_running_loop().add_signal_handler(sig, stopping.set)
        try:
            await stopping.wait()
        finally:
            monitor.cancel()
            await asyncio.gather(monitor, return_exceptions=True)
            # Service maintenance must not discard an active world.
            async with self.lock:
                if self.child and self.child.poll() is None:
                    try:
                        await self.checkpoint_stop()
                    except Exception:
                        logging.exception('maintenance save failed')
                await self.stop_child()
            await self.proxy.close()
            server.close()
            await server.wait_closed()
            control.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=6567)
    parser.add_argument('--backend-port', type=int, default=16567)
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--idle-seconds', type=float, default=300)
    parser.add_argument('--java', required=True)
    parser.add_argument('--map', default='大肥鱼的调试世界')
    args = parser.parse_args()
    if args.port == args.backend_port or args.idle_seconds < 10:
        parser.error('Separate ports and idle interval >=10s are required')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    asyncio.run(Supervisor(args).run())


if __name__ == '__main__':
    main()
