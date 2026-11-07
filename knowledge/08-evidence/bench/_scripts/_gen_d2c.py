# -*- coding: utf-8 -*-
"""域 13-15：电力与热 / 液体与物流 / 战斗与单位。"""
from _gen_core import *

def build_power():
    D = "电力与热"
    short(D, "PowerGenerator 的默认发电量 powerProduction 是多少？", "0（由子类赋值）",
          "world/blocks/power/PowerGenerator.java:23。", F_PGEN, "v159.3_src", 1)
    short(D, "PowerGenerator 的默认血量爆炸半径 explosionRadius 是多少？", "12",
          "PowerGenerator.java:27 explosionRadius = 12。", F_PGEN, "v159.3_src", 1)
    short(D, "impact-reactor 的发电量是多少？", "25（power=25）",
          "tools/block_attrs.json#impact-reactor: power=\"25\"。", F_ATTR + "#impact-reactor", "v159.3_src", 1)
    mc(D, "ConsumePower 的 usage 字段表示什么？", "每 tick 耗电量",
       ["电力容量", "缓存电量", "发电量"], "ConsumePower.java:10 usage；每个 tick 从电网扣 usage。", F_CPOWER + ":10", "v159.3_src", 1)
    mc(D, "ConsumePower 的 capacity 表示什么？", "可缓存的电量上限",
       ["每 tick 耗电", "电网总量", "发电倍率"], "ConsumePower.java:12 capacity。", F_CPOWER + ":12", "v159.3_src", 1)
    mc(D, "ConsumePower 的 buffered 表示什么？", "是否允许电力缓冲（battery 行为）",
       ["已缓存电量数值", "是否耗电", "是否是发电机"], "ConsumePower.java:14 buffered；ignore() 直接返回 buffered。", F_CPOWER + ":14", "v159.3_src", 2)
    mc(D, "方块的电力状态 power.status 取值范围是？", "0~1 的满足率（1 表示电力充足）",
       ["0~100 的百分比整数", "只取 0 或 1", "毫秒数"], "ConsumePower.apply 中 efficiency 取 build.power.status，即按需分配后的满足比例。", F_CPOWER, "v159.3_src", 2)
    mc(D, "为什么电力不足时工厂产量会同比下降？", "power.status 作为效率乘子进入生产计算",
       ["电力直接买物品", "缺电会摧毁方块", "缺电只影响血量"], "ConsumePower 把 build.power.status 作为 efficiency 供 consume 使用。", F_CPOWER, "v159.3_src", 2)
    mc(D, "solar-panel 的建造成本是？", "lead 10 + silicon 8",
       ["copper 10", "lead 20 + silicon 20", "titanium 10"], "tools/block_attrs.json#solar-panel: build.cost。", F_ATTR + "#solar-panel", "v159.3_src", 2)
    mc(D, "battery 的建造成本是？", "copper 5 + lead 20",
       ["lead 10", "silicon 10 + copper 5", "titanium 20"], "tools/block_attrs.json#battery: build.cost = [copper:5, lead:20]。", F_ATTR + "#battery", "v159.3_src", 2)
    mc(D, "impact-reactor 需要什么液体冷却，速率多少？", "cryofluid，15/s",
       ["water，10/s", "oil，5/s", "不需要液体"], "tools/block_attrs.json#impact-reactor: liquids=[cryofluid:15/s]、liquidCapacity=80。", F_ATTR + "#impact-reactor", "v159.3_src", 2)
    mc(D, "combustion-generator 在 block_attrs 里带有哪两个危险属性？", "explodes 与 flammable",
       ["solid 与 hidden", "power 与 inputs", "accepts 与 recipe"], "tools/block_attrs.json#combustion-generator: explodes=true, flammable=true。", F_ATTR + "#combustion-generator", "v159.3_src", 2)
    mc(D, "PowerGenerator 的 generationType 默认取哪个统计量？", "Stat.basePowerGeneration",
       ["Stat.powerProduced", "Stat.health", "Stat.itemsMoved"], "PowerGenerator.java:25 generationType = Stat.basePowerGeneration。", F_PGEN + ":25", "v159.3_src", 2)
    mc(D, "solarMultiplier 规则（LogicRule.solarMultiplier）作用是？", "缩放全图太阳能发电倍率",
       ["缩放电力消耗", "缩放电池容量", "缩放光照颜色"], "logic/LogicRule.java 含 solarMultiplier；对应 Rules.solarMultiplier。", F_LRULE, "v159.3_src", 2)
    mc(D, "电力不足会导致下列哪种结果？", "耗电方块效率按满足率下降",
       ["方块被自动拆除", "电力网络断开", "物品消失"], "ConsumePower 的 efficiency = build.power.status。", F_CPOWER, "v159.3_src", 2)
    mc(D, "power-node 与 power-node-large 的占地分别是？", "power-node 为 1×1，power-node-large 为 2×2",
       ["都是 1×1", "都是 2×2", "2×2 与 3×3"], "tools/block_attrs.json: power-node size=1、power-node-large size=2。", F_ATTR + "#power-node-large", "v159.3_src", 2)
    mc(D, "battery-large 的占地与成本是？", "size=3，titanium 20 + lead 50 + silicon 30",
       ["size=2，copper 10", "size=3，lead 100", "size=4，silicon 100"], "tools/block_attrs.json#battery-large: size=3、build.cost 三项。", F_ATTR + "#battery-large", "v159.3_src", 3)
    mc(D, "电力单位与 tick 的换算关系是？", "1 电力单位/tick = 60 电力单位/秒",
       ["1/tick = 1/s", "1/tick = 30/s", "电力与时间无关"], "knowledge/VERSION.md：1 tick = 1/60 s。", F_VER, "both", 2)
    calc(D, "impact-reactor 每秒消耗多少 cryofluid？", "15 / 60", "0.25 /tick（即 15/s）",
         "attrs 写 cryofluid:15/s；tick 换算 15/60 = 0.25 每 tick。", F_ATTR + "#impact-reactor", "v159.3_src", 2)
    mc(D, "PowerGenerator 爆炸时默认会产生多少个液体坑？", "10（explosionPuddles=10，每个 amount=100）",
       ["1 个", "5 个", "100 个"], "PowerGenerator.java:31-36 explosionPuddles=10、explosionPuddleAmount=100。", F_PGEN + ":31-36", "v159.3_src", 3)
    mc(D, "PowerGenerator 爆炸的默认伤害与震屏时长是？", "explosionDamage=0、explosionShakeDuration=6",
       ["explosionDamage=100、时长 10", "伤害 50、时长 3", "无爆炸"], "PowerGenerator.java:29-40。", F_PGEN + ":29-40", "v159.3_src", 3)
    mc(D, "想让反应堆不爆炸，源码层面的可控点是？", "设置方块实例的 explosionDamage/explosionRadius 等字段（如 impact-reactor 伤害为 0）",
       ["把 ipt 设为 0", "断开电网", "降低温度"], "PowerGenerator 把爆炸参数暴露为可覆写字段，impact-reactor 覆盖为 0 伤害。", F_PGEN + ":23-40", "v159.3_src", 3)
    mc(D, "Rules.lighting 与 solarMultiplier 的关系是？", "相互独立：lighting 控制光照强度，solarMultiplier 是额外倍率",
       ["完全等价", "lighting 是 solarMultiplier 的子集", "solarMultiplier 覆盖 lighting"], "game/Rules.java 中两者为独立字段；LogicRule 亦分别暴露。", F_RULES, "v159.3_src", 3)
    mc(D, "电池（battery）在电力网络中的角色是？", "带 electricity 缓冲的储能方块（buffered）",
       ["发电机", "变压器", "固定耗电负载"], "ConsumePower.java:14 buffered 字段即储能开关；battery 的 cost/容量由 Blocks.java 定义。", F_CPOWER + ":14", "v159.3_src", 3)
    mc(D, "PowerGenerator 的 explosionShake 默认值为？", "6",
       ["0", "12", "24"], "PowerGenerator.java:40 explosionShake = explosionShakeDuration = 6。", F_PGEN + ":40", "v159.3_src", 3)

def build_liquid():
    D = "液体与物流"
    short(D, "data/game/liquids.json 收录了多少种液体？", "11 种",
          "liquids.json 为 11 条：water,slag,oil,cryofluid,neoplasm,arkycite,gallium,ozone,hydrogen,nitrogen,cyanogen。", F_LIQJSON, "both", 1)
    short(D, "Liquid 的默认温度 temperature 是多少？", "0.5",
          "type/Liquid.java:40 temperature = 0.5f。", F_LIQ + ":40", "v159.3_src", 1)
    short(D, "Liquid 的默认热容 heatCapacity 是多少？", "0.5",
          "Liquid.java:42 heatCapacity = 0.5f。", F_LIQ + ":42", "v159.3_src", 1)
    short(D, "Liquid 的默认粘度 viscosity 是多少？", "0.5",
          "Liquid.java:44 viscosity = 0.5f。", F_LIQ + ":44", "v159.3_src", 1)
    short(D, "conduit（导管）的液体容量是多少？", "20",
          "tools/block_attrs.json#conduit: liquidCapacity=20。", F_ATTR + "#conduit", "v159.3_src", 1)
    mc(D, "Liquid.gas 为 true 表示什么？", "该液体是气体（渲染与流动行为不同）",
       ["易燃", "有爆炸性", "不可运输"], "Liquid.java:28 gas=false 默认；ozone/hydrogen 等置 true。", F_LIQ + ":28", "v159.3_src", 1)
    mc(D, "水的热容 heatCapacity 是多少？", "0.4",
       ["0.5", "0.9", "1.0"], "content/Liquids.java: water.heatCapacity = 0.4f。", F_LIQS, "v159.3_src", 2)
    mc(D, "cryofluid 的温度与热容是？", "temperature=0.25，heatCapacity=0.9",
       ["0.5 / 0.4", "0.25 / 0.4", "1.0 / 0.5"], "content/Liquids.java: cryofluid heatCapacity=0.9、temperature=0.25。", F_LIQS, "v159.3_src", 2)
    mc(D, "slag 的温度与粘度是？", "temperature=1，viscosity=0.7",
       ["0.5 / 0.5", "1 / 0.75", "0.75 / 0.7"], "content/Liquids.java: slag temperature=1f、viscosity=0.7f。", F_LIQS, "v159.3_src", 2)
    mc(D, "oil 的易燃性与爆炸性是？", "flammability=1.2，explosiveness=1.2",
       ["0.5 / 0.5", "1.0 / 1.0", "1.2 / 0"], "content/Liquids.java: oil flammability=1.2f、explosiveness=1.2f。", F_LIQS, "v159.3_src", 2)
    mc(D, "neoplasm 的可燃性是多少？", "0",
       ["0.4", "1.0", "1.2"], "content/Liquids.java: neoplasm flammability=0f（但温度 0.54、粘度 0.85）。", F_LIQS, "v159.3_src", 2)
    mc(D, "哪种液体在源码中被标记为 hidden=true？", "gallium",
       ["ozone", "hydrogen", "arkycite"], "content/Liquids.java: gallium hidden=true、coolant=false。", F_LIQS, "v159.3_src", 2)
    mc(D, "block_attrs.json 里液体速率写成什么格式？", "形如 cryofluid:15/s 的字符串",
       ["纯数字", "每 tick 数字", "中文描述"], "tools/block_attrs.json#impact-reactor: liquids=[cryofluid:15/s]。", F_ATTR + "#impact-reactor", "v159.3_src", 2)
    mc(D, "liquid-tank 与 liquid-container 的容量分别是？", "1800（3×3）与 700（2×2）",
       ["1000 / 500", "1800 / 300", "700 / 1800"], "tools/block_attrs.json: liquid-tank liquidCapacity=1800 size=3；liquid-container 700 size=2。", F_ATTR + "#liquid-tank", "v159.3_src", 2)
    mc(D, "气体的 explosiveness 可以使用什么值？", "臭氧与氢气均为 1（气体也可爆）",
       ["气体 explosiveness 恒为 0", "只能取 0 或 0.5", "由 gas=false 决定"], "content/Liquids.java: ozone explosiveness=1f、flammability=1f；hydrogen flammability=1f、gas=true。", F_LIQS, "v159.3_src", 2)
    mc(D, "lash（液体）在管道网络中传播速度受哪个字段影响？", "viscosity（粘度）",
       ["temperature", "heatCapacity", "flammability"], "Liquid.java:44 viscosity 控制流动阻力（0.5 默认）。", F_LIQ + ":44", "v159.3_src", 2)
    mc(D, "液体方块要接受某液体，源码层面靠什么？", "方块的 liquidFilter / acceptsLiquid 逻辑（attrs 的 liquids 字段是其投影）",
       ["blocks.json 的 requirements", "craftTime 字段", "hasPower 字段"], "block_attrs.json 的 liquids 字段由 Blocks.java 的液体配置抽取；接受与否在方块类里判定。", F_ATTR + "#liquids", "v159.3_src", 2)
    calc(D, "15/s 的液体消耗换算成每 tick 是多少？", "15 / 60", "0.25 /tick",
         "1 tick = 1/60 s（knowledge/VERSION.md）。", F_VER, "both", 2)
    mc(D, "conveyor、router、sorter 同属哪个 build.category？", "distribution",
       ["liquid", "power", "production"], "tools/block_attrs.json: 三者 build.category 均为 distribution。", F_ATTR + "#conveyor", "v159.3_src", 2)
    mc(D, "为什么液体速度在游戏里显得比物品慢？", "液体按 viscosity 与方块的液体容量逐 tick 传输，非瞬时",
       ["因为液体没有物理模拟", "因为 conduit 容量为 0", "因为液体只走管道不流动"], "Liquid.viscosity（Liquid.java:44）+ 方块 liquidCapacity（如 conduit=20）。", F_LIQ + ":44", "v159.3_src", 3)
    mc(D, "liquids.json 的 color 字段用途是？", "该液体的渲染颜色（十六进制）",
       ["温度值", "粘度", "物品 ID"], "data/game/liquids.json 每条带 color 十六进制字段。", F_LIQJSON, "both", 3)
    mc(D, "11 种液体里哪一种是气体且可燃但不作为冷却液？", "ozone（gas=true、flammability=1、explosiveness=1）",
       ["water", "cryofluid", "slag"], "content/Liquids.java: ozone gas=true 且 flammability/explosiveness 均为 1。", F_LIQS, "v159.3_src", 3)
    mc(D, "gallium 的 coolant 字段是？", "false（且 hidden=true）",
       ["true", "未定义", "依赖温度"], "content/Liquids.java: gallium coolant=false、hidden=true。", F_LIQS, "v159.3_src", 3)
    mc(D, "液体温度 temperature 影响什么？", "热交换/冷却相关计算（如反应堆冷却效率）",
       ["液体颜色", "管道容量", "传送带速度"], "Liquid.java:40 temperature 参与热计算；cryofluid temperature=0.25 用于降温。", F_LIQ + ":40", "v159.3_src", 3)
    mc(D, "哪一种液体的粘度最高（0.85）？", "neoplasm",
       ["water", "oil", "gallium"], "content/Liquids.java: neoplasm viscosity=0.85f（oil 0.75、water 默认 0.5）。", F_LIQS, "v159.3_src", 3)

def build_combat():
    D = "战斗与单位"
    short(D, "BulletType 的默认 lifetime 是多少？", "40",
          "entities/bullet/BulletType.java:33 lifetime = 40f。", F_BULLET + ":33", "v159.3_src", 1)
    short(D, "BulletType 的默认伤害 damage 是多少？", "1",
          "BulletType.java:41 damage = 1f。", F_BULLET + ":41", "v159.3_src", 1)
    short(D, "BulletType 的默认速度 speed 是多少？", "1",
          "BulletType.java:37 speed = 1f。", F_BULLET + ":37", "v159.3_src", 1)
    short(D, "data/game/units.json 收录了多少个单位？", "70 个",
          "units.json 为 70 条；meta.json 记录 units=70。", F_UNITSJSON, "both", 1)
    short(D, "Vars.minArmorDamage 的值是多少？", "0.1",
          "Vars.java:133 public static final float minArmorDamage = 0.1f。", F_VARS + ":133", "v159.3_src", 1)
    mc(D, "BulletType 的默认 hitSize 是多少？", "4",
       ["1", "8", "16"], "BulletType.java:43 hitSize = 4f。", F_BULLET + ":43", "v159.3_src", 1)
    mc(D, "护甲减伤公式是？", "max(damage - armor, 0.1 × damage)",
       ["damage - armor", "damage × (1 - armor)", "damage / armor"], "Damage.java:659-660 Math.max(damage - armor, minArmorDamage * damage)，minArmorDamage=0.1（Vars.java:133）。", F_DMG + ":659-660", "v159.3_src", 2)
    mc(D, "BulletType 默认的 pierceCap 是多少？", "-1（不限制穿透数）",
       ["0", "1", "10"], "BulletType.java:57 pierceCap = -1f。", F_BULLET + ":57", "v159.3_src", 2)
    mc(D, "BulletType 默认 removeAfterPierce 是？", "true（穿透后移除）",
       ["false", "取决于速度", "取决于伤害"], "BulletType.java:63 removeAfterPierce = true。", F_BULLET + ":63", "v159.3_src", 2)
    mc(D, "StatusEffect 默认给单位施加的伤害倍率是？", "1（不影响）",
       ["0.5", "1.5", "2"], "type/StatusEffect.java:19-29 六个倍率（damage/health/speed/reload/buildSpeed/drag）默认均为 1。", F_STATUS + ":19-29", "v159.3_src", 2)
    mc(D, "StatusEffect 默认的 effectChance 是多少？", "0.15",
       ["0.05", "0.5", "1.0"], "StatusEffect.java:43 effectChance = 0.15f。", F_STATUS + ":43", "v159.3_src", 2)
    mc(D, "status 语句的第一个参数为什么不能用普通数值？", "index 0 是布尔字面量（是否永久/是否作用于自身）",
       ["只能是字符串", "必须是 @unit", "必须是液体名"], "LStatements.java:1568-1625 StatusStatement：第 0 个参数是布尔字面量；ApplyEffectI 在 LExecutor.java:1739-1750。", F_STMT + ":1568-1625", "v159.3_src", 2)
    mc(D, "dagger 的基础血量与护甲是？", "hp 150，armor 0",
       ["hp 100 / armor 2", "hp 150 / armor 2", "hp 200 / armor 0"], "data/game/units.json: dagger health=150, armor=0。", F_UNITSJSON, "both", 2)
    mc(D, "stell 的护甲与单发伤害是？", "armor 6，dmg 30",
       ["armor 4 / dmg 20", "armor 6 / dmg 15", "armor 8 / dmg 30"], "units.json: stell armor=6；武器 dmg=30、reload=50。", F_UNITSJSON, "both", 2)
    mc(D, "UnitType 默认的 rotateSpeed 是多少？", "5",
       ["1", "10", "0.5"], "type/UnitType.java:56 rotateSpeed = 5f。", F_UNIT + ":56", "v159.3_src", 2)
    mc(D, "UnitType 默认的 itemCapacity 是多少？", "-1（不能携带物品）",
       ["0", "10", "100"], "UnitType.java:378 itemCapacity = -1。", F_UNIT + ":378", "v159.3_src", 2)
    calc(D, "dagger 的 9 点伤害打 armor=6 的 stell，每发实际掉多少血？", "max(9-6, 0.1*9)", "3",
         "Damage.java:659-660：max(9-6, 0.9) = 3。", F_DMG + ":659-660", "v159.3_src", 2)
    mc(D, "Waves 的 waveVersion 当前是多少？", "7",
       ["5", "6", "8"], "game/Waves.java:13 waveVersion = 7。", F_WAVES + ":13", "v159.3_src", 2)
    mc(D, "第一波（dagger 组）在源码里的 end 与 max 是？", "end=10、unitScaling=2、max=30",
       ["end=5、max=10", "end=20、max=50", "begin=10、max=30"], "Waves.java:17-40 new SpawnGroup(dagger){{end=10;unitScaling=2f;max=30}}。", F_WAVES + ":17-40", "v159.3_src", 3)
    mc(D, "crawler 组的 begin/end/unitAmount 是？", "begin=4、end=13、unitAmount=2",
       ["begin=1、end=10、amount=1", "begin=4、end=13、amount=4", "begin=10、end=20、amount=2"], "Waves.java:17-40 crawler SpawnGroup。", F_WAVES + ":17-40", "v159.3_src", 3)
    mc(D, "子弹的 pierceDamageFactor 默认为 0，含义是？", "穿透目标后不再造成衰减伤害（0 表示不按比例保留）",
       ["穿透伤害翻倍", "禁止穿透", "穿透后伤害保留 0%"], "BulletType.java:59 pierceDamageFactor = 0f。", F_BULLET + ":59", "v159.3_src", 3)
    mc(D, "maxDamageFraction 默认 -1 表示？", "不限制单次伤害占比",
       ["伤害为 0", "伤害翻倍", "只对建筑生效"], "BulletType.java:61 maxDamageFraction = -1f。", F_BULLET + ":61", "v159.3_src", 3)
    mc(D, "StatusEffect 的 transitionDamage 默认值与作用？", "0，切换状态时造成的伤害为 0",
       ["1，切换即造成 1 点伤害", "-1，无定义", "等于 effectChance"], "StatusEffect.java:31 transitionDamage = 0f。", F_STATUS + ":31", "v159.3_src", 3)
    mc(D, "disarm 状态会让单位怎样？", "无法攻击（disarm=true）",
       ["无法移动", "无法治疗", "立即死亡"], "StatusEffect.java:33 disarm = false 默认；置 true 的单位不能开火。", F_STATUS + ":33", "v159.3_src", 3)
    mc(D, "为什么打高护甲单位时低伤武器几乎无效？", "applyArmor 把伤害压到 0.1×damage 的下限，低伤武器只剩 10%",
       ["护甲会反弹全部伤害", "护甲提升血量", "护甲免疫状态"], "Damage.java:659-660 与 Vars.java:133 minArmorDamage=0.1。", F_DMG + ":659-660", "v159.3_src", 3)
