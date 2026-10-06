// 扫描 main.js 里**所有**覆写方法体，逐个对照规则表检查成员访问形态。
// 规则来自 RefDump（对 desktop.jar 反射得到的真实成员形态）。
//
// ⚠ 必须覆盖每一个覆写方法：曾经因为漏检 aimX 而用 unit.aimX() 崩掉游戏。
//   新增覆写方法时，只要它落在下面 SCAN 区间里就会被自动覆盖。
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'scripts', 'main.js'), 'utf8');

// 要扫描的区间：[起点标记, 终点标记]（左闭右开，按出现顺序）
const SCAN = [
  ['function realUpdateMovement(', '// 对外的覆写入口'],
  ['def.panCamera = function(',  'return def;'],
];
const segments = [];
for(const [a, b] of SCAN){
  const s = src.indexOf(a);
  const e = s < 0 ? -1 : src.indexOf(b, s);
  if(s < 0 || e < 0){ console.log('[FAIL] 找不到扫描区间：' + a); process.exit(1); }
  segments.push(src.slice(s, e));
}
const body = segments.join('\n')
  .replace(/\/\/[^\n]*/g, '')        // 行注释
  .replace(/\/\*[\s\S]*?\*\//g, ''); // 块注释

// 规则：成员名 -> 形态（field 必须不带括号；method 必须带括号）
const rules = {
  'aimX': 'field', 'aimY': 'field',
  'x': 'field', 'y': 'field',
  'vel': 'field',
  // ⚠ type 是**方法**：Unit.type() 返回 UnitType，写成 unit.type.omniMovement 会抛
  //   TypeError（undefined 上取属性）→ 被覆写的安全网吞掉 → superBroken=true 永久卸载覆写，
  //   表现为"整块逻辑无声失效"。v5.5 前一直是错的，靠这条规则抓出来。
  'type': 'method',
  'omniMovement': 'field', 'accel': 'field', 'faceTarget': 'field',
  'shooting': 'field', 'boosting': 'field', 'mouseX': 'field', 'mouseY': 'field',
  'movement': 'field', 'lastPayloadKeyTapMillis': 'field', 'lastPayloadKeyHoldMillis': 'field',
  'speed': 'method', 'lookAt': 'method', 'prefRotation': 'method', 'movePref': 'method',
  'aim': 'method', 'controlWeapons': 'method', 'isFlying': 'method', 'hasWeapons': 'method',
  'tryPickupPayload': 'method', 'tryDropPayload': 'method', 'within': 'method',
  'axis': 'method', 'keyDown': 'method', 'keyTap': 'method', 'mouseWorld': 'method',
  'timeSinceMillis': 'method', 'millis': 'method', 'set': 'method', 'setZero': 'method',
  'sub': 'method', 'limit': 'method', 'nor': 'method', 'scl': 'method',
  'add': 'method', 'approachDelta': 'method', 'setInput': 'method',
};

let bad = 0, checked = 0;
for(const [name, kind] of Object.entries(rules)){
  // 找出所有 `something.name` 后跟 ( 或不跟 ( 的用法
  // (?![A-Za-z0-9_$]) 保证不会把 setZero 里的 set 当成 set
  const re = new RegExp('\\.' + name + '(?![A-Za-z0-9_$])\\s*(\\()?', 'g');
  let m;
  while((m = re.exec(body))){
    const hasParen = !!m[1];
    checked++;
    if(kind === 'field' && hasParen){
      console.log('[FAIL] .' + name + ' 是字段，却被当成方法调用：' + body.slice(Math.max(0, m.index - 30), m.index + 20).replace(/\n/g, ' '));
      bad++;
    }
    if(kind === 'method' && !hasParen){
      console.log('[FAIL] .' + name + ' 是方法，却没加括号：' + body.slice(Math.max(0, m.index - 30), m.index + 20).replace(/\n/g, ' '));
      bad++;
    }
  }
}

// 额外①：realUpdateMovement 拿到的是 self 参数，里面**不能**用 this
//   （踩过：def.panCamera 里误用 updateMovement 的 self，运行时 ReferenceError）
const rm = segments[0];
const thisInRm = rm.match(/\bthis\.[A-Za-z_$][\w$]*/g);
if(thisInRm){ console.log('[FAIL] realUpdateMovement 里误用 this（应当用 self）：' + thisInRm.join(', ')); bad++; }

// 额外②：panCamera 是被当方法调用的，必须用 this（不能用 self）
const pc = segments[1];
const selfInPc = pc.match(/\bself\.[A-Za-z_$][\w$]*/g);
if(selfInPc){ console.log('[FAIL] def.panCamera 里误用 self（应当用 this）：' + selfInPc.join(', ')); bad++; }
// 输入处理器自己的字段/方法也要形态正确
for(const [n, kind] of [['panning','field'], ['locked','method'],
                        ['movement','field'], ['panSpeed','field'], ['panBoostSpeed','field']]){
  const re = new RegExp('\\.' + n + '(?![A-Za-z0-9_$])\\s*(\\()?', 'g');
  let m;
  while((m = re.exec(pc))){
    checked++;
    const hasParen = !!m[1];
    if(kind === 'field' && hasParen){ console.log('[FAIL] panCamera: .' + n + ' 是字段，不能加括号'); bad++; }
    if(kind === 'method' && !hasParen){ console.log('[FAIL] panCamera: .' + n + ' 是方法，必须加括号'); bad++; }
  }
}

// 额外③：两个覆写都必须有 try/catch 安全网（异常冒到主循环会崩游戏）
const wrapStart = src.indexOf('// 对外的覆写入口');
const wrapEnd = src.indexOf('return def;', wrapStart);
if(wrapStart < 0 || wrapEnd < 0 || src.slice(wrapStart, wrapEnd).indexOf('catch(e)') < 0){
  console.log('[FAIL] def.updateMovement 没有 try/catch 安全网'); bad++;
}
if(pc.indexOf('catch(e)') < 0){ console.log('[FAIL] def.panCamera 没有 try/catch 安全网'); bad++; }

console.log('\n检查了 ' + checked + ' 处成员访问；问题 ' + bad + ' 个');
process.exit(bad ? 1 : 0);
