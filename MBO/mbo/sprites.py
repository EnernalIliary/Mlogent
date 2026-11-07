"""原版贴图（v160.7）：把方块贴图接进 preview。

贴图来源是工作区里的 `assetsraw/assets-raw/sprites/`（游戏 jar 里拆出来的原始素材）：

    sprites/blocks/<分类>/<方块名>.png        # 32 px / 格，2×2 机器就是 64×64

带子这类“可旋转 + 多混合位 + 多帧”的方块文件名是 `<名字>-<混合位>-<帧>`，
预览取无混合的 `-0-0`；方向由方块自身的 rotation 决定（`Draw.rect(..., rotation * 90)`，
逆时针），所以渲染时对底图做 `rotation * 90` 度逆时针旋转即可。

找不到贴图（或没装贴图）时调用方回落到色块，不影响主流程。
"""

from __future__ import annotations

import os
import pathlib

CELL_PX = 32                       # 一格 32 px
ENV_VAR = "MBO_SPRITES"            # 显式覆盖贴图根目录
CANDIDATES = (
    "assetsraw/assets-raw/sprites",   # 工作区里的原始素材（默认）
    "assets/sprites",                 # 从 jar 的 sprites.png 图集裁出来的（可选）
)


def find_root(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """按「环境变量 → 向上找工作区 assetsraw → 当前目录」的顺序定位贴图根目录。"""
    env = os.environ.get(ENV_VAR)
    if env:
        p = pathlib.Path(env)
        return p if (p / "blocks").is_dir() else None

    here = pathlib.Path(start or pathlib.Path.cwd()).resolve()
    for base in [here, *here.parents]:
        for cand in CANDIDATES:
            p = base / cand
            if (p / "blocks").is_dir():
                return p
    return None


class SpriteSet:
    """方块名 → 贴图文件的索引；按需加载、按 rotation 旋转、按格数缩放。"""

    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.index: dict[str, pathlib.Path] = {}
        blocks = self.root / "blocks"
        for p in sorted(blocks.rglob("*.png")):
            # 同名多份（如团队色变体）取第一个；comm 前缀的补充素材跳过
            self.index.setdefault(p.stem, p)
        self._cache: dict[tuple, object] = {}
        self._loaded = 0

    # ---------------------------------------------------------------- 查找
    @classmethod
    def discover(cls, root=None) -> "SpriteSet | None":
        p = pathlib.Path(root) if root else find_root()
        return cls(p) if p and (pathlib.Path(p) / "blocks").is_dir() else None

    def path(self, name: str) -> pathlib.Path | None:
        if name in self.index:
            return self.index[name]
        # 带子/管道：<名字>-<混合位>-<帧>.png
        for alt in ("%s-0-0" % name, "%s-0" % name):
            if alt in self.index:
                return self.index[alt]
        return None

    def names(self) -> int:
        return len(self.index)

    # ---------------------------------------------------------------- 渲染
    def tile_image(self, name: str, size: int, rotation: int, rotate: bool,
                   cell_px: int = CELL_PX):
        """返回 RGBA 图，边长 = size * cell_px；没有贴图时返回 None。"""
        from PIL import Image

        key = (name, size, rotation if rotate else 0, bool(rotate), cell_px)
        if key in self._cache:
            return self._cache[key]

        p = self.path(name)
        img = None
        if p is not None:
            try:
                img = Image.open(p).convert("RGBA")
                self._loaded += 1
            except Exception:
                img = None
        if img is not None:
            want = size * cell_px
            if img.size != (want, want):
                img = img.resize((want, want), Image.LANCZOS)
            if rotate and rotation % 4:
                img = img.rotate(90 * (rotation % 4), expand=False)  # 逆时针
        self._cache[key] = img
        return img


def discover(root=None):
    """模块级入口：定位并加载贴图（没有贴图就返回 None）。"""
    return SpriteSet.discover(root)


def make(root=None):
    """便捷入口：拿一个可用的 SpriteSet，没有贴图就返回 None。"""
    return discover(root)
