"""Sleep proxy regressions: native ArcNet framing, reconnect-free delayed attach,
split TCP/UDP IDs, no wake on discovery, and fail-closed empty-world shutdown.
"""
import asyncio
import base64
import json
import random
import re
from pathlib import Path
import socket
import struct
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import world_sleep as sleep
from world_sleep_protocol import Proxy, DISCOVER, KEEPALIVE, SLEEP_TEXT, WAKE_TEXT, frame, read_packet, register, discovery, running_discovery


class RunningDiscoveryTests(unittest.TestCase):
    def test_mlogent_titles_keep_full_name_and_gradient_within_wire_limit(self):
        import world_sleep_protocol as protocol
        title = 'Mlogent.execute(Mindustry);'
        self.assertEqual(protocol.SERVER_TITLE, '[gray]' + title + '[]')
        self.assertEqual(re.sub(r'\[[^\]]*\]', '', protocol.RUNNING_TITLE), title)
        self.assertTrue(protocol.RUNNING_TITLE.startswith('[#8abcd1]M'))
        self.assertTrue(protocol.RUNNING_TITLE.endswith('[#ffb6c1]y);[]'))
        self.assertLessEqual(len(protocol.RUNNING_TITLE.encode('utf-8')), 255)
        packet = running_discovery(discovery('unchanged notice', 16567), 6567)
        self.assertEqual(packet[1:1+packet[0]].decode('utf-8'), protocol.RUNNING_TITLE)
        self.assertIn(b'unchanged notice', packet)
        self.assertLessEqual(len(packet), 500)
        with self.assertRaises(ValueError):
            protocol.gradient_title('X' * 30, max_bytes=255)

    def test_full_runtime_message_replaces_native_truncation_without_changing_map_stats(self):
        message='[highlight]Mlogent[white]附属服务器、点个[yellow]\ue809[]吧！\n[gray]\uf308：EnernalIliary/Mlogent'
        native=discovery('native-truncated',16567,map_name='test map')
        def fields(packet):
            position=0
            def string():
                nonlocal position
                length=packet[position];position+=1
                value=packet[position:position+length].decode('utf-8');position+=length
                return value
            name,map_name=string(),string()
            stats=packet[position:position+12];position+=12
            version=string();mode=packet[position:position+5];position+=5
            desc,custom_mode=string(),string()
            return dict(name=name,map=map_name,stats=stats,version=version,mode=mode,
                        desc=desc,custom_mode=custom_mode,port=int.from_bytes(packet[position:position+2],'big'))
        before=fields(native);result=running_discovery(native,6567,message);after=fields(result)
        self.assertEqual(after['desc'],message);self.assertEqual(after['port'],6567)
        for key in ['map','stats','version','mode','custom_mode']:self.assertEqual(before[key],after[key])
        self.assertLessEqual(len(result),500)

    def test_description_bound_keeps_valid_utf8_and_rejects_malformed_packets(self):
        packet=running_discovery(discovery('old',16567),6567,'月'*200)
        self.assertIn(('月'*80).encode(),packet)
        with self.assertRaises(ValueError):running_discovery(b'\xffx',6567,'new')


class UDPReceiver(asyncio.DatagramProtocol):
    def __init__(self):
        self.received = asyncio.Queue()

    def datagram_received(self, data, addr):
        self.received.put_nowait((data, addr))


class SleepProxyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.owner = SimpleNamespace(ensure_awake=AsyncMock(), restore_peer=AsyncMock(),
            kick_packet=b'fake-kick', discovery_packet=lambda: discovery(SLEEP_TEXT, self.proxy.port))
        self.proxy = Proxy(self.owner, 0, 0, '127.0.0.1')
        # start() requires matching TCP/UDP port; reserve an actual port first.
        for _ in range(50):
            self.proxy.port = random.randint(10000, 19999)
            try:
                await self.proxy.start()
                break
            except OSError:
                continue
        else:
            self.fail('No available TCP+UDP test port')
        self.transport, self.udp = await asyncio.get_running_loop().create_datagram_endpoint(
            UDPReceiver, local_addr=('127.0.0.1', 0))
        self.writers = []
        self.backend = None
        self.backend_transport = None

    async def asyncTearDown(self):
        for writer in self.writers:
            writer.close()
        await self.proxy.close()
        self.transport.close()
        if self.backend:
            self.backend.close(); await self.backend.wait_closed()
        if self.backend_transport:
            self.backend_transport.close()
        await asyncio.sleep(.03)

    async def connect(self):
        reader, writer = await asyncio.open_connection('127.0.0.1', self.proxy.port)
        self.writers.append(writer)
        packet = await read_packet(reader)
        identity, = struct.unpack('>i', packet[2:])
        self.transport.sendto(register(3, identity), ('127.0.0.1', self.proxy.port))
        self.assertEqual(await read_packet(reader), register(3))
        return reader, writer

    async def test_discovery_and_bare_handshake_do_not_wake(self):
        self.transport.sendto(DISCOVER, ('127.0.0.1', self.proxy.port))
        data, _ = await asyncio.wait_for(self.udp.received.get(), 1)
        self.assertIn(SLEEP_TEXT.encode(), data)
        await self.connect()
        self.owner.ensure_awake.assert_not_called()

    async def test_delayed_backend_preserves_same_front_connection_and_udp(self):
        async def delayed():
            await asyncio.sleep(.15)
        self.owner.ensure_awake.side_effect = delayed
        backend_id = 901
        backend_reader = None
        registered = asyncio.Event()
        async def tcp(reader, writer):
            nonlocal backend_reader
            self.writers.append(writer)
            backend_reader = reader
            writer.write(frame(register(4, backend_id))); await writer.drain()
            await registered.wait()
            writer.write(frame(register(3))); await writer.drain()
            login = await read_packet(reader)
            writer.write(frame(b'world-stream:' + login)); await writer.drain()
            later = await read_packet(reader)
            writer.write(frame(later)); await writer.drain()
            writer.write(frame(b'actual-kick-reason')); await writer.drain()
            writer.close()
        class BackUDP(asyncio.DatagramProtocol):
            def connection_made(inner, transport): inner.transport = transport
            def datagram_received(inner, data, addr):
                if data == register(3, backend_id): registered.set()
                else: inner.transport.sendto(b'echo:' + data, addr)
        for _ in range(50):
            self.proxy.backend_port = random.randint(10000, 19999)
            try:
                self.backend = await asyncio.start_server(tcp, '127.0.0.1', self.proxy.backend_port)
                self.backend_transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
                    BackUDP, local_addr=('127.0.0.1', self.proxy.backend_port))
                break
            except OSError:
                if self.backend:
                    self.backend.close(); await self.backend.wait_closed()
        else:
            self.fail('No available backend TCP+UDP test port')
        reader, writer = await self.connect()
        writer.write(frame(b'\x03\x00\x01\x00X')); await writer.drain()
        self.assertEqual(await asyncio.wait_for(read_packet(reader), 2), b'world-stream:\x03\x00\x01\x00X')
        self.owner.restore_peer.assert_awaited_once_with(901, '127.0.0.1')
        self.transport.sendto(b'udp-update', ('127.0.0.1', self.proxy.port))
        data, _ = await asyncio.wait_for(self.udp.received.get(), 1)
        self.assertEqual(data, b'echo:udp-update')
        writer.write(frame(b'game-update')); await writer.drain()
        self.assertEqual(await read_packet(reader), b'game-update')
        self.assertEqual(await read_packet(reader), b'actual-kick-reason')
        # A normal backend close cannot append the proxy's fake wake kick.
        self.assertEqual(await asyncio.wait_for(reader.read(), 1), b'')

    async def test_failed_boot_returns_configured_kick_and_closes(self):
        self.owner.ensure_awake.side_effect = RuntimeError('boot failed')
        reader, writer = await self.connect()
        writer.write(frame(b'\x03hello')); await writer.drain()
        self.assertEqual(await asyncio.wait_for(read_packet(reader), 1), b'fake-kick')
        self.assertEqual(await asyncio.wait_for(reader.read(), 1), b'')


class SleepLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.patch = patch.object(sleep, 'WORLD', Path(self.temp.name))
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.owner = sleep.Supervisor(SimpleNamespace(port=6567, backend_port=16567, bind='127.0.0.1', idle_seconds=10))
        self.owner.state = 'running'
        self.owner.last_activity = time.monotonic() - 20
        self.owner.refresh = AsyncMock()
        self.owner.stop_child = AsyncMock()

    async def test_players_connections_work_and_front_waiters_prevent_sleep(self):
        for field in ('players', 'connections', 'work'):
            state = dict(players=0, connections=0, work=False, game=True)
            state[field] = 1
            self.owner.js = AsyncMock(return_value=json.dumps(state))
            self.assertFalse(await self.owner.try_sleep())
        self.owner.js = AsyncMock(return_value=json.dumps(dict(players=0, connections=0, work=False, game=True)))
        self.owner.proxy.sessions[1] = object()
        self.assertFalse(await self.owner.try_sleep())
        self.owner.stop_child.assert_not_called()

    async def test_save_failure_never_stops_world(self):
        self.owner.js = AsyncMock(side_effect=[json.dumps(dict(players=0, connections=0, work=False, game=True)), RuntimeError('disk full')])
        with self.assertRaisesRegex(RuntimeError, 'disk full'):
            await self.owner.try_sleep()
        self.owner.stop_child.assert_not_called()
        self.assertEqual(self.owner.state, 'running')

    async def test_successful_save_is_recorded_before_process_stops(self):
        self.owner.js = AsyncMock(side_effect=[json.dumps(dict(players=0, connections=0, work=False, game=True)), 'saved'])
        async def stop():
            saved = json.loads(self.owner.state_path.read_text())
            self.assertTrue(saved['save'].startswith('mcp-hibernate-'))
        self.owner.stop_child.side_effect = stop
        self.assertTrue(await self.owner.try_sleep())
        self.assertEqual(self.owner.state, 'sleeping')

    async def test_sleeping_status_maps_and_players_never_boot(self):
        self.owner.state = 'sleeping'
        self.owner.ensure_awake = AsyncMock()
        self.owner.persisted['maps'] = {'ok': True, 'maps': ['map']}
        for op in ('status', 'ping', 'maps', 'players', 'logic_vars'):
            result = await self.owner.dispatch({'op': 'call', 'request': {'op': op}})
            self.assertTrue(result.get('sleeping'))
        self.owner.ensure_awake.assert_not_called()

    async def test_cancelled_player_does_not_cancel_shared_boot(self):
        self.owner.state = 'sleeping'
        finished = asyncio.Event()
        async def boot():
            await asyncio.sleep(.08)
            finished.set()
        self.owner.boot = boot
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(self.owner.ensure_awake(), .01)
        await asyncio.wait_for(finished.wait(), 1)

    async def test_sleeping_stop_is_idempotent_and_never_starts_game(self):
        self.owner.state = 'sleeping'
        self.owner.ensure_awake = AsyncMock()
        self.owner.js = AsyncMock()
        for _ in range(2):
            result = await self.owner.dispatch({'op': 'stop_if_sleeping'})
            self.assertTrue(result['handled'])
            self.assertEqual(result['status'], 'stopped')
        self.assertTrue(self.owner.manual_off)
        self.owner.ensure_awake.assert_not_called()
        self.owner.js.assert_not_called()
        self.owner.stop_child.assert_not_called()

    async def test_running_stop_cannot_bypass_veto_via_sleeping_check(self):
        result = await self.owner.dispatch({'op': 'stop_if_sleeping'})
        self.assertFalse(result['handled'])
        self.assertFalse(self.owner.manual_off)
        self.owner.stop_child.assert_not_called()

    async def test_manual_shutdown_publishes_recovery_point_before_terminating(self):
        self.owner.child = Mock()
        self.owner.child.poll.return_value = None
        self.owner.js = AsyncMock(return_value='saved')
        self.owner.persisted['save'] = 'old-snapshot'
        async def stopped():
            state = json.loads(self.owner.state_path.read_text())
            self.assertNotEqual(state['save'], 'old-snapshot')
            self.assertEqual(self.owner.persisted['save'], state['save'])
            self.assertTrue(self.owner.manual_off)
        self.owner.stop_child.side_effect = stopped
        result = await self.owner.dispatch({'op': 'call', 'request': {'op': 'shutdown'}})
        self.assertEqual(result['save'], self.owner.persisted['save'])
        self.assertEqual(result['status'], 'stopped')
        self.assertEqual(self.owner.state, 'sleeping')

    async def test_manual_shutdown_save_failure_keeps_world_running(self):
        self.owner.child = Mock()
        self.owner.child.poll.return_value = None
        self.owner.js = AsyncMock(side_effect=RuntimeError('disk full'))
        with self.assertRaisesRegex(RuntimeError, 'disk full'):
            await self.owner.dispatch({'op': 'call', 'request': {'op': 'shutdown'}})
        self.owner.stop_child.assert_not_called()
        self.assertEqual(self.owner.state, 'running')
        self.assertFalse(self.owner.manual_off)

    async def test_recovery_pointer_failure_preserves_old_pointer_and_reopens_listener(self):
        self.owner.child = Mock()
        self.owner.child.poll.return_value = None
        self.owner.persisted['save'] = 'old-snapshot'
        self.owner.js = AsyncMock(side_effect=['saved', 'ready'])
        with patch.object(sleep, 'atomic_json', side_effect=OSError('metadata disk full')):
            with self.assertRaisesRegex(OSError, 'metadata disk full'):
                await self.owner.dispatch({'op': 'call', 'request': {'op': 'shutdown'}})
        self.assertEqual(self.owner.persisted['save'], 'old-snapshot')
        self.assertIn('Vars.netServer.openServer()', self.owner.js.call_args.args[0])
        self.owner.stop_child.assert_not_called()
        self.assertFalse(self.owner.manual_off)


if __name__ == '__main__':
    unittest.main()
