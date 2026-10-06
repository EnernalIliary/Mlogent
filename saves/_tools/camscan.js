// camscan.js —— 全库机械枚举：谁在写 Core.camera.position
// 用法: node camscan.js
// 原理: 扫 class 文件常量池，找 (a) 同时引用 Camera.position 的类
//       (b) 引用 Camera 且包含方位动词方法的类 —— 后者才是"写入点"
const fs = require('fs'), path = require('path'), zlib = require('zlib');

const JAR = 'E:\\Program Files (x86)\\Steam\\steamapps\\common\\Mindustry\\jre\\desktop.jar';
const MODS = 'E:\\Program Files (x86)\\Steam\\steamapps\\common\\Mindustry\\saves\\mods';

// ---- 极简 zip 读取（只读中央目录 + 解压需要的条目）----
function readZip(buf) {
  const out = [];
  // 找 EOCD
  let eocd = -1;
  for (let i = buf.length - 22; i >= 0 && i > buf.length - 66000; i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) return out;
  let n = buf.readUInt16LE(eocd + 10);
  let p = buf.readUInt32LE(eocd + 16);
  for (let k = 0; k < n; k++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) break;
    const method = buf.readUInt16LE(p + 10);
    const csize = buf.readUInt32LE(p + 20);
    const usize = buf.readUInt32LE(p + 24);
    const nlen = buf.readUInt16LE(p + 28);
    const elen = buf.readUInt16LE(p + 30);
    const clen = buf.readUInt16LE(p + 32);
    const lho = buf.readUInt32LE(p + 42);
    const name = buf.toString('utf8', p + 46, p + 46 + nlen);
    out.push({ name, method, csize, usize, lho });
    p += 46 + nlen + elen + clen;
  }
  return out;
}
function readEntry(buf, e) {
  const nlen = buf.readUInt16LE(e.lho + 26);
  const elen = buf.readUInt16LE(e.lho + 28);
  const start = e.lho + 30 + nlen + elen;
  const data = buf.subarray(start, start + e.csize);
  return e.method === 0 ? data : zlib.inflateRawSync(data);
}

// 常量池粗解析：抽出所有 UTF8 字符串
function stringsOf(classBuf) {
  const out = new Set();
  try {
    if (classBuf.readUInt32BE(0) !== 0xCAFEBABE) return out;
    let p = 8;
    const cpCount = classBuf.readUInt16BE(p); p += 2;
    const utf8At = new Array(cpCount);
    for (let i = 1; i < cpCount; i++) {
      const tag = classBuf[p++];
      if (tag === 1) {
        const len = classBuf.readUInt16BE(p); p += 2;
        utf8At[i] = classBuf.toString('utf8', p, p + len); p += len;
      } else if (tag === 7 || tag === 8 || tag === 16 || tag === 19 || tag === 20) p += 2;
      else if (tag === 15) p += 3;
      else if (tag === 3 || tag === 4 || tag === 9 || tag === 10 || tag === 11 || tag === 12 || tag === 17 || tag === 18) p += 4;
      else if (tag === 5 || tag === 6) { p += 8; i++; }
      else break;
    }
    // 把 NameAndType / Methodref 组合成 "Owner.name:desc" 形式太麻烦，
    // 直接收集全部 UTF8 + 用名字空间判断。够用。
    for (let i = 1; i < cpCount; i++) if (utf8At[i]) out.add(utf8At[i]);
  } catch (e) { /* 忽略损坏条目 */ }
  return out;
}

const CAMERA = 'arc/graphics/Camera';
const CAM_DESC = 'Larc/graphics/Camera;';
// 方位/写入动词（出现即说明"朝相机做什么"）
const VERBS = ['set', 'add', 'sub', 'lerp', 'lerpDelta', 'lerpPast', 'mulAdd',
               'clamp', 'limit', 'nor', 'scl', 'setToRandom', 'setZero', 'trns'];

function owner(desc) { return (desc || '').replace(/^L|;$/g, ''); }

const hits = [];   // {src, cls, verbs:[], camRefs:n}

function scan(source, zipBuf) {
  const entries = readZip(zipBuf);
  for (const e of entries) {
    if (!e.name.endsWith('.class')) continue;
    const s = stringsOf(readEntry(zipBuf, e));
    if (!s.has(CAMERA) && !s.has(CAM_DESC)) continue;
    // 找 "position" 且字段归属 Camera
    if (!s.has('position')) continue;
    // 哪些动词出现？
    const verbs = VERBS.filter(v => s.has(v));
    // 只保留"看起来在改 position"的：字符串里同时有 position 和至少一个 Vec2 动词
    if (verbs.length === 0) continue;
    // 线索：类里出现 camera 相关命名
    const ctx = [...s].filter(x => /camera|Camera|focus|Focus|recenter|Recent|center|eye|look/i.test(x))
                      .filter(x => x.length < 60).slice(0, 12);
    hits.push({ src: source, cls: e.name.replace(/\.class$/, '').replace(/\//g, '.'), verbs, ctx });
  }
}

// 游戏本体
scan('desktop.jar', fs.readFileSync(JAR));
// 所有 mod
const modFiles = fs.readdirSync(MODS).filter(f => /\.(zip|jar)$/i.test(f));
for (const f of modFiles) {
  try {
    const b = fs.readFileSync(path.join(MODS, f));
    if (!/^(PK)/.test(b.toString('latin1', 0, 2))) continue;
    scan(f, b);
  } catch (e) { /* 非 zip */ }
}

// 输出：按来源分组
const bySrc = {};
for (const h of hits) (bySrc[h.src] = bySrc[h.src] || []).push(h);
for (const src of Object.keys(bySrc)) {
  console.log('\n===== ' + src + ' =====');
  for (const h of bySrc[src]) {
    console.log('  ' + h.cls);
    console.log('      动词: ' + h.verbs.join(', '));
    console.log('      线索: ' + h.ctx.join(' | '));
  }
}
console.log('\n共 ' + hits.length + ' 个类引用 Camera.position 且带写入动词。');
