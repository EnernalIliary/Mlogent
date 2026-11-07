"""探针：读 Mindustry 的 sprites.aatls（Arc TextureAtlas 数据），确认能不能解析。"""
import io
import struct
import zipfile

JAR = r"E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\desktop.jar"
z = zipfile.ZipFile(JAR)
data = z.read("sprites/sprites.aatls")
print("aatls bytes:", len(data))
print("head:", data[:48].hex(" "))
print("first ints:", struct.unpack("<5i", data[:20]))

# 试 arc 的 AtlasData 格式：int count，然后每个 region 是 UTF 名字 + 8 个 int + 可选 splits/pads
def utf(r):
    n = struct.unpack(">H", r.read(2))[0]
    return r.read(n).decode("utf-8")

r = io.BytesIO(data)
count = struct.unpack(">i", r.read(4))[0]
print("count:", count)
regs = []
try:
    for i in range(count):
        name = utf(r)
        w, h, x, y, ow, oh, ox, oy = struct.unpack(">8i", r.read(32))
        ns = struct.unpack(">i", r.read(4))[0]
        for _ in range(ns * 4):
            struct.unpack(">i", r.read(4))
        npads = struct.unpack(">i", r.read(4))[0]
        for _ in range(npads * 2):
            struct.unpack(">i", r.read(4))
        regs.append((name, x, y, w, h, ow, oh, ox, oy))
    print("parsed ok, remaining", len(data) - r.tell())
except Exception as e:
    print("parse failed at", len(regs), ":", repr(e))

print("regions:", len(regs))
print(regs[:5])
names = [x[0] for x in regs]
print("conveyor-ish:", [n for n in names if "conveyor" in n][:12])
print("graphite:", [n for n in names if "graphite" in n][:12])
print("press:", [n for n in names if "press" in n][:12])
