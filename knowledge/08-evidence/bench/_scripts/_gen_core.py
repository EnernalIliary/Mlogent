# -*- coding: utf-8 -*-
"""题库核心：真源加载 + 题目构造助手。所有数值均从真源读取，不凭记忆。"""
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import json, os, random
from pathlib import Path

REPO = Path(os.environ.get("AS_REPO", str(Path(__file__).resolve().parents[4])))
OUT = Path(__file__).resolve().parent

def _j(rel):
    return json.loads((REPO / rel).read_text(encoding="utf-8"))

BLOCKS = {b["name"]: b for b in _j("data/game/blocks.json")}
UNITS  = {u["name"]: u for u in _j("data/game/units.json")}
ITEMS  = {i["name"]: i for i in _j("data/game/items.json")}
LIQS   = {l["name"]: l for l in _j("data/game/liquids.json")}
ALIAS  = _j("data/game/aliases.json")
ATTRS  = _j("tools/block_attrs.json")["blocks"]
SIZES  = _j("tools/block_sizes.json")
INSTR  = _j("tools/instr_semantics.json")
INS    = INSTR["instructions"]
OPS    = INSTR["ops"]

SRC = "Mindustry-Source/core/src/mindustry/"
F_EXEC   = SRC + "logic/LExecutor.java"
F_STMT   = SRC + "logic/LStatements.java"
F_LOGICB = SRC + "world/blocks/logic/LogicBlock.java"
F_DISP   = SRC + "world/blocks/logic/LogicDisplay.java"
F_DMG    = SRC + "entities/Damage.java"
F_BULLET = SRC + "entities/bullet/BulletType.java"
F_STATUS = SRC + "type/StatusEffect.java"
F_LIQ    = SRC + "type/Liquid.java"
F_LIQS   = SRC + "content/Liquids.java"
F_STATUSES = SRC + "content/StatusEffects.java"
F_WAVES  = SRC + "game/Waves.java"
F_RULES  = SRC + "game/Rules.java"
F_CPOWER = SRC + "world/consumers/ConsumePower.java"
F_COP    = SRC + "logic/ConditionOp.java"
F_LOP    = SRC + "logic/LogicOp.java"
F_VER    = "knowledge/VERSION.md"
F_CONV   = "knowledge/CONVENTIONS.md"
F_INSTR  = "tools/instr_semantics.json"
F_BLOCK  = SRC + "content/Blocks.java"
F_MEM    = SRC + "world/blocks/logic/MemoryBlock.java"
F_LACC   = SRC + "logic/LAccess.java"
F_GV     = SRC + "logic/GlobalVars.java"
F_TLAYER = SRC + "logic/TileLayer.java"
F_LRULE  = SRC + "logic/LogicRule.java"
F_MSGT   = SRC + "logic/MessageType.java"
F_CUT    = SRC + "logic/CutsceneAction.java"
F_QTYPE  = SRC + "logic/QueryType.java"
F_QSHAPE = SRC + "logic/QueryShape.java"
F_FETCH  = SRC + "logic/FetchType.java"
F_UCTL   = SRC + "logic/LUnitControl.java"
F_LOC    = SRC + "logic/LLocate.java"
F_RTGT   = SRC + "logic/RadarTarget.java"
F_RSORT  = SRC + "logic/RadarSort.java"
F_CONSUM = SRC + "world/consumers/ConsumePower.java"
F_MSG    = SRC + "world/blocks/logic/MessageBlock.java"
F_VARS   = SRC + "Vars.java"
F_UNIT   = SRC + "type/UnitType.java"
F_LOGB   = SRC + "world/blocks/logic/LogicBlock.java"

_QS = []
_rng = random.Random(20261108)

def _fmt(v):
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else ("%.2f" % v).rstrip("0").rstrip(".")
    return str(v)

def num(v):
    return _fmt(v)

def q(domain, qtext, typ, answer, why, src, ver, diff):
    _QS.append(dict(domain=domain, q=qtext, type=typ, answer=answer,
                    why=why, src=src, ver=ver, difficulty=diff))

def mc(domain, stem, correct, distractors, why, src, ver, diff):
    """4 选项选择题；答案打乱后给出字母+文本。"""
    opts = [correct] + list(distractors)
    assert len(opts) == 4, stem
    rng = random.Random(hash(stem) & 0xffffff)
    idx = list(range(4)); rng.shuffle(idx)
    shuffled = [opts[i] for i in idx]
    letters = "ABCD"
    lines = [f"{letters[i]}) {shuffled[i]}" for i in range(4)]
    ans = letters[shuffled.index(correct)] + ") " + correct
    q(domain, stem + "\n" + "\n".join(lines), "mc", ans, why, src, ver, diff)

def short(domain, stem, answer, why, src, ver, diff):
    q(domain, stem, "short", answer, why, src, ver, diff)

def calc(domain, stem, expr, value, why, src, ver, diff):
    q(domain, stem, "calc", f"= {value}（{expr}）", why + f"\n算式：{expr} = {value}", src, ver, diff)

def code(domain, stem, code_lines, answer, why, src, ver, diff):
    assert len(code_lines) <= 15, "code 题不得超过 15 行"
    bt = chr(96) * 3
    q(domain, stem + "\n" + bt + "mlog\n" + "\n".join(code_lines) + "\n" + bt, "code", answer, why, src, ver, diff)

def all_questions():
    return _QS

def block_cost(name):
    b = BLOCKS[name]
    return sum(r["amount"] for r in b["requirements"]), b["requirements"]

# —— 数据/属性文件与其余源码路径（d2a-d2c 引用）——
F_ATTR     = "tools/block_attrs.json"
F_SIZES    = "tools/block_sizes.json"
F_BJSON    = "data/game/blocks.json"
F_UNITSJSON = "data/game/units.json"
F_LIQJSON  = "data/game/liquids.json"
F_ITEMSJSON = "data/game/items.json"
F_METAJSON = "data/game/meta.json"
F_ALIAS    = "data/game/aliases.json"
# 2026-11-17: docs/游戏速查/ 的薄投影已删，母本改指 00-data/*.json
F_DOCS_BLOCK = "knowledge/00-data/blocks.json"
F_DOCS_UNIT  = "knowledge/00-data/units.json"
F_DOCS_ITEM  = "knowledge/00-data/items.json"
F_DOCS_RECIPE = "knowledge/00-data/blocks.json"
F_PGEN     = SRC + "world/blocks/power/PowerGenerator.java"
F_BUILD    = SRC + "world/Block.java"


def attr(name, key, default=None):
    return ATTRS.get(name, {}).get(key, default)
