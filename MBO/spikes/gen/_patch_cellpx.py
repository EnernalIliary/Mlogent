"""修两处：tile_image 支持目标像素尺寸（渲染格边长）；自检脚本路径。"""
import pathlib

R = pathlib.Path(__file__).resolve().parents[2]

# ---- sprites.py：加上 cell_px 参数（缓存键也要带上）
p = R / "mbo" / "sprites.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '''    def tile_image(self, name: str, size: int, rotation: int, rotate: bool):
        """返回 RGBA 图，边长 = size * CELL_PX；没有贴图时返回 None。"""
        from PIL import Image

        key = (name, size, rotation if rotate else 0, bool(rotate))''',
    '''    def tile_image(self, name: str, size: int, rotation: int, rotate: bool,
                   cell_px: int = CELL_PX):
        """返回 RGBA 图，边长 = size * cell_px；没有贴图时返回 None。"""
        from PIL import Image

        key = (name, size, rotation if rotate else 0, bool(rotate), cell_px)''')
s = s.replace(
    '''            want = size * CELL_PX''',
    '''            want = size * cell_px''')
p.write_text(s, encoding="utf-8")

# ---- preview.py：传渲染格边长
p = R / "mbo" / "preview.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '''            tex = sprites.tile_image(t.block, s, t.rotation, bool(getattr(blk, "rotate", False)))''',
    '''            tex = sprites.tile_image(t.block, s, t.rotation,
                                     bool(getattr(blk, "rotate", False)), cell_px=int(cell))''')
p.write_text(s, encoding="utf-8")

# ---- 自检脚本：路径与参考图尺寸
p = R / "spikes" / "gen" / "_check_sprites.py"
s = p.read_text(encoding="utf-8")
s = s.replace('run = R / "MBO/runs/p-one"', 'run = R / "runs/p-one"')
s = s.replace('ref = ss.tile_image("conveyor", 1, rot, True).resize(crop.size)',
              'ref = ss.tile_image("conveyor", 1, rot, True, cell_px=cell).resize(crop.size)')
p.write_text(s, encoding="utf-8")
print("patched")
