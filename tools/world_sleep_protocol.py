"""Small, bounded ArcNet front end; game packets remain opaque, including LZ4.

Front and backend connection IDs differ. Complete both TCP/UDP registrations,
then relay the original ConnectPacket and subsequent packets without rewriting
game contents. No JVM is required while sleeping.
"""
import asyncio
import collections
import logging
import secrets
import struct
import time

TITLE_TEXT = 'Mlogent.execute(Mindustry);'
SERVER_TITLE = '[gray]' + TITLE_TEXT + '[]'


def gradient_title(text, start='#8abcd1', end='#ffb6c1', max_bytes=None):
    parts = list(text)
    if max_bytes is not None and len(text.encode('utf-8')) + len(parts) * 9 + 2 > max_bytes:
        # Discovery names have a one-byte length. Keep every letter colored;
        # punctuation can inherit its preceding letter's color to fit the wire.
        parts = []
        for char in text:
            if parts and char in '.();':
                parts[-1] += char
            else:
                parts.append(char)
    first = tuple(bytes.fromhex(start.lstrip('#')))
    last = tuple(bytes.fromhex(end.lstrip('#')))
    colors = (''.join('%02x' % round(a + (b - a) * i / max(1, len(parts) - 1))
                      for a, b in zip(first, last)) for i in range(len(parts)))
    result = ''.join('[#' + color + ']' + part for color, part in zip(colors, parts)) + '[]'
    if max_bytes is not None and len(result.encode('utf-8')) > max_bytes:
        raise ValueError('Gradient title exceeds discovery name byte limit')
    return result


RUNNING_TITLE = gradient_title(TITLE_TEXT, max_bytes=255)
RUNNING_DESCRIPTION = '[highlight]Mlogent[white]附属服务器,点个star吧！\n[gray]EnernalIliary/Mlogent'


def running_discovery(packet, port, description=None):
    # Native NetworkIO truncates names at 100 bytes, midway through color tags.
    # The wire format supports 255; replace the name while preserving map/stats.
    if description is not None:
        def after_string(offset):
            if offset >= len(packet):
                raise ValueError('Truncated discovery string')
            end = offset + 1 + packet[offset]
            if end > len(packet):
                raise ValueError('Truncated discovery payload')
            return end
        # name, map, players/wave/version, version type, mode, player limit, desc.
        cursor = after_string(after_string(0)) + 12
        description_start = after_string(cursor) + 5
        description_end = after_string(description_start)
        text = str(description).encode('utf-8')[:240].decode('utf-8', 'ignore').encode('utf-8')
        packet = packet[:description_start] + bytes([len(text)]) + text + packet[description_end:]
    title = RUNNING_TITLE.encode('utf-8')
    result = bytearray(bytes([len(title)]) + title + packet[1 + packet[0]:])
    result[-2:] = port.to_bytes(2, 'big')
    return bytes(result)


SLEEP_TEXT = '大肥鱼休眠中，可发起连接请求以唤醒。首次连接需要约 20 秒。'
WAKE_TEXT = '正在唤醒大肥鱼，这通常需要几十秒，如果链接超时，可以稍等再次尝试链接。'
FRAMEWORK = 254
DISCOVER = b'\xfe\x01'
KEEPALIVE = b'\xfe\x02'


def frame(payload):
    return struct.pack('>H', len(payload)) + payload


def register(kind, identity=0):
    return struct.pack('>BBi', FRAMEWORK, kind, identity)


async def read_packet(reader):
    size, = struct.unpack('>H', await reader.readexactly(2))
    if not 1 <= size <= 65535:
        raise ValueError('Invalid ArcNet packet length')
    return await reader.readexactly(size)


def discovery(text, port, version=160, map_name='大肥鱼的调试世界', player_limit=30):
    def string(value, maximum):
        data = value.encode('utf-8')[:maximum].decode('utf-8', 'ignore').encode('utf-8')
        return bytes([len(data)]) + data
    return (string(SERVER_TITLE, 100) + string(map_name, 64) + struct.pack('>iii', 0, 0, version)
            + string('official', 32) + b'\x01' + struct.pack('>i', player_limit)
            + string(text, 240) + string('', 50) + struct.pack('>H', port))


class BackendUDP(asyncio.DatagramProtocol):
    def __init__(self, session):
        self.session = session

    def datagram_received(self, data, addr):
        session = self.session
        if session.udp_address:
            session.proxy.udp.sendto(data, session.udp_address)


class PublicUDP(asyncio.DatagramProtocol):
    def __init__(self, proxy):
        self.proxy = proxy

    def datagram_received(self, data, addr):
        proxy = self.proxy
        if data == DISCOVER:
            # Browsing never wakes the game. Cache is refreshed by the supervisor.
            packet = proxy.owner.discovery_packet()
            if len(packet) <= 500 and proxy.allow_discovery(addr[0]):
                proxy.udp.sendto(packet, addr)
            return
        if len(data) == 6 and data[:2] == b'\xfe\x03':
            identity, = struct.unpack('>i', data[2:])
            session = proxy.sessions.get(identity)
            if session and session.address[0] == addr[0] and session.udp_address in (None, addr):
                session.udp_address = addr
                proxy.udp_sessions[addr] = session
                session.send(register(3))
            return
        session = proxy.udp_sessions.get(addr)
        if session and session.backend_udp:
            session.backend_udp.sendto(data)


class Session:
    def __init__(self, proxy, identity, reader, writer):
        self.proxy, self.identity = proxy, identity
        self.reader, self.writer = reader, writer
        self.address = writer.get_extra_info('peername')
        self.udp_address = None
        self.backend_writer = self.backend_udp = None
        self.tasks = []
        self.join_packet = None
        self.closed = False

    def send(self, packet):
        if not self.closed:
            self.writer.write(frame(packet))

    async def keepalive(self):
        while True:
            await asyncio.sleep(2)
            self.send(KEEPALIVE)
            await self.writer.drain()

    async def frontend(self):
        while True:
            packet = await read_packet(self.reader)
            if self.backend_writer:
                self.backend_writer.write(frame(packet))
                await self.backend_writer.drain()
            elif packet == KEEPALIVE:
                continue
            elif len(packet) == 7 and packet[:2] == b'\xfe\x00':
                self.send(packet[:6] + b'\x01')
            elif self.join_packet is None and packet[0] == 3 and self.udp_address:
                # ArcNet complete; actual game login is the wake trigger, not a SYN.
                self.join_packet = packet
                self.tasks.append(asyncio.create_task(self.attach()))
            else:
                raise ValueError('Unexpected packet before game registration')

    async def attach(self):
        attached = False
        try:
            # Leave time for the original client's ~30s world-data deadline.
            await asyncio.wait_for(self.proxy.owner.ensure_awake(), 24)
            reader, writer = await asyncio.open_connection('127.0.0.1', self.proxy.backend_port)
            packet = await asyncio.wait_for(read_packet(reader), 4)
            if packet[:2] != b'\xfe\x04' or len(packet) != 6:
                raise ValueError('Backend did not register TCP')
            backend_id, = struct.unpack('>i', packet[2:])
            transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: BackendUDP(self), remote_addr=('127.0.0.1', self.proxy.backend_port))
            self.backend_udp = transport
            # Registration acknowledgment travels over TCP, with retries over UDP.
            registration = asyncio.create_task(read_packet(reader))
            for _ in range(12):
                transport.sendto(register(3, backend_id))
                try:
                    reply = await asyncio.wait_for(asyncio.shield(registration), .3)
                    if reply[:2] == b'\xfe\x03':
                        break
                except asyncio.TimeoutError:
                    continue
            else:
                registration.cancel()
                await asyncio.gather(registration, return_exceptions=True)
                raise RuntimeError('Backend UDP registration timed out')
            # Restore the actual peer before submitting game login (IP bans/trace).
            await self.proxy.owner.restore_peer(backend_id, self.address[0])
            self.backend_writer = writer
            writer.write(frame(self.join_packet))
            await writer.drain()
            attached = True
            logging.info('player bridge attached peer=%s id=%s', self.address[0], backend_id)
            while True:
                self.send(await read_packet(reader))
                await self.writer.drain()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logging.warning('player bridge unavailable peer=%s: %s', self.address[0], exc)
            # EOF after a real game session (including a native kick) must not
            # append the unrelated wake-up kick and replace its actual reason.
            if not attached and self.proxy.owner.kick_packet:
                self.send(self.proxy.owner.kick_packet)
                await self.writer.drain()
                await asyncio.sleep(.2)
        finally:
            self.writer.close()
            if 'writer' in locals():
                writer.close()

    async def run(self):
        self.send(register(4, self.identity))
        self.tasks.append(asyncio.create_task(self.keepalive()))
        try:
            # Unauthenticated idle connections cannot pin the game indefinitely.
            await asyncio.wait_for(self.wait_for_join(), 6)
            await self.frontend()
        except (OSError, ValueError, asyncio.IncompleteReadError, asyncio.TimeoutError):
            pass
        finally:
            self.closed = True
            for task in self.tasks:
                task.cancel()
            await asyncio.gather(*self.tasks, return_exceptions=True)
            if self.backend_udp:
                self.backend_udp.close()
            if self.backend_writer:
                self.backend_writer.close()
            self.writer.close()
            self.proxy.sessions.pop(self.identity, None)
            if self.udp_address:
                self.proxy.udp_sessions.pop(self.udp_address, None)

    async def wait_for_join(self):
        # Read until frontend schedules attach; normal frontend then continues.
        while self.join_packet is None:
            packet = await read_packet(self.reader)
            if packet == KEEPALIVE:
                continue
            if packet[0] != 3 or not self.udp_address:
                raise ValueError('Expected registered ConnectPacket')
            self.join_packet = packet
            self.tasks.append(asyncio.create_task(self.attach()))


class Proxy:
    def __init__(self, owner, port, backend_port, bind='0.0.0.0'):
        self.owner, self.port, self.backend_port, self.bind = owner, port, backend_port, bind
        self.sessions, self.udp_sessions = {}, {}
        self.rates = collections.OrderedDict()
        self.discovery_rates = collections.OrderedDict()
        self.server = self.udp = None

    def _allow(self, table, ip, count, interval):
        now = time.monotonic()
        deadline, used = table.pop(ip, (now + interval, 0))
        if deadline < now:
            deadline, used = now + interval, 0
        table[ip] = (deadline, used + 1)
        if len(table) > 4096:
            table.popitem(last=False)
        return used < count

    def allow_discovery(self, ip):
        return self._allow(self.discovery_rates, ip, 10, 5)

    async def accept(self, reader, writer):
        ip = writer.get_extra_info('peername')[0]
        if (len(self.sessions) >= 64 or sum(s.address[0] == ip for s in self.sessions.values()) >= 8
                or not self._allow(self.rates, ip, 20, 60)):
            writer.close()
            return
        identity = secrets.randbelow(2147483646) + 1
        while identity in self.sessions:
            identity = secrets.randbelow(2147483646) + 1
        session = Session(self, identity, reader, writer)
        self.sessions[identity] = session
        await session.run()

    async def start(self):
        self.server = await asyncio.start_server(self.accept, self.bind, self.port, limit=131072)
        if self.port == 0:
            self.port = self.server.sockets[0].getsockname()[1]
        try:
            self.udp, _ = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: PublicUDP(self), local_addr=(self.bind, self.port))
        except BaseException:
            self.server.close()
            await self.server.wait_closed()
            raise

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for session in list(self.sessions.values()):
            session.writer.close()
        if self.udp:
            self.udp.close()
