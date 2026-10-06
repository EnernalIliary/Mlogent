// whoreads2.js —— 直接搜常量池里 "mindustry/input/InputHandler.recentRespawnTimer" 这条 Fieldref
// 用它就能区分 getfield(读) / putfield(写)，并打印所属方法
const fs = require('fs'), zlib = require('zlib');
const JAR = 'E:\\Program Files (x86)\\Steam\\steamapps\\common\\Mindustry\\jre\\desktop.jar';
const NEEDLE = 'mindustry/input/InputHandler.recentRespawnTimer';

function readZip(buf) {
  const out = []; let eocd = -1;
  for (let i = buf.length - 22; i >= 0 && i > buf.length - 66000; i--)
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0) return out;
  let n = buf.readUInt16LE(eocd + 10), p = buf.readUInt32LE(eocd + 16);
  for (let k = 0; k < n; k++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) break;
    const method = buf.readUInt16LE(p + 10), csize = buf.readUInt32LE(p + 20);
    const nlen = buf.readUInt16LE(p + 28), elen = buf.readUInt16LE(p + 30), clen = buf.readUInt16LE(p + 32);
    out.push({ name: buf.toString('utf8', p + 46, p + 46 + nlen), method, csize, lho: buf.readUInt32LE(p + 42) });
    p += 46 + nlen + elen + clen;
  }
  return out;
}
function readEntry(buf, e) {
  const nlen = buf.readUInt16LE(e.lho + 26), elen = buf.readUInt16LE(e.lho + 28);
  const s = e.lho + 30 + nlen + elen, d = buf.subarray(s, s + e.csize);
  return e.method === 0 ? d : zlib.inflateRawSync(d);
}
// 极简 class 解析：常量池 + 方法表，定位每条 getfield/putfield 引用
function analyze(c) {
  const out = [];
  let p = 8;
  const cpCount = c.readUInt16BE(p); p += 2;
  const utf8 = new Array(cpCount), fref = new Array(cpCount);
  for (let i = 1; i < cpCount; i++) {
    const tag = c[p++];
    if (tag === 1) { const L = c.readUInt16BE(p); p += 2; utf8[i] = c.toString('utf8', p, p + L); p += L; }
    else if (tag === 7 || tag === 8 || tag === 16 || tag === 19 || tag === 20) p += 2;
    else if (tag === 15) p += 3;
    else if (tag === 9 || tag === 10 || tag === 11 || tag === 12) { const a = c.readUInt16BE(p), b = c.readUInt16BE(p + 2); p += 4; if (tag === 9) fref[i] = [a, b]; }
    else if (tag === 3 || tag === 4 || tag === 17 || tag === 18) p += 4;
    else if (tag === 5 || tag === 6) { p += 8; i++; }
    else return out;
  }
  // 找引用目标 Fieldref 的 cp 索引
  const targets = new Set(); const owners = new Set();
  for (let i = 1; i < cpCount; i++) {
    if (!fref[i]) continue;
    const [clsIdx, ntIdx] = fref[i];
    const cls = utf8[clsIdx], nt = utf8[ntIdx];
    if (nt === 'recentRespawnTimer:F') { targets.add(i); owners.add(cls); }
  }
  if (!targets.size) return out;
  out.owners = [...owners];
  // 扫方法体
  p += 6; // access, this, super
  const ifCount = c.readUInt16BE(p); p += 2 + ifCount * 2;
  const fieldCount = c.readUInt16BE(p); p += 2;
  for (let i = 0; i < fieldCount; i++) { p += 6; const ac = c.readUInt16BE(p); p += 2 + ac * 2; }
  const mCount = c.readUInt16BE(p); p += 2;
  for (let m = 0; m < mCount; m++) {
    p += 2;
    const nameIdx = c.readUInt16BE(p), descIdx = c.readUInt16BE(p + 2); p += 4;
    const ac = c.readUInt16BE(p); p += 2 + ac * 2;
    const attrs = c.readUInt16BE(p); p += 2;
    for (let a = 0; a < attrs; a++) {
      const anIdx = c.readUInt16BE(p), alen = c.readUInt32BE(p + 2); p += 6;
      if (utf8[anIdx] === 'Code') {
        const codeLen = c.readUInt32BE(p + 4);
        const code = c.subarray(p + 8, p + 8 + codeLen);
        for (let q = 0; q + 3 <= code.length; q++) {
          const op = code[q];
          if (op === 0xB4 || op === 0xB5) { // getfield / putfield
            const idx = code.readUInt16BE(q + 1);
            if (targets.has(idx)) out.push({ method: utf8[nameIdx] + utf8[descIdx], op: op === 0xB4 ? 'READ(getfield)' : 'WRITE(putfield)', off: q });
          }
        }
      }
      p += alen;
    }
  }
  return out;
}
const buf = fs.readFileSync(JAR);
console.log('扫描 desktop.jar 中所有对 InputHandler.recentRespawnTimer 的字段访问：\n');
let n = 0;
for (const e of readZip(buf)) {
  if (!e.name.endsWith('.class')) continue;
  let c; try { c = readEntry(buf, e); } catch (x) { continue; }
  if (c.toString('latin1').indexOf('recentRespawnTimer') < 0) continue;
  const r = analyze(c); if (r.owners) console.log('   (owner: ' + r.owners.join(', ') + ')');
  for (const x of r) { n++; console.log('  ' + e.name.replace(/\.class$/, '').replace(/\//g, '.') + '  ' + x.method); console.log('      ' + x.op + '  @bytecode ' + x.off); }
}
console.log('\n共 ' + n + ' 处字段访问。');
