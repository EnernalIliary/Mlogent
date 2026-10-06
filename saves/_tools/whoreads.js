// whoreads.js —— 全库找"读 recentRespawnTimer"的类
const fs = require('fs'), zlib = require('zlib');
const JAR = 'E:\\Program Files (x86)\\Steam\\steamapps\\common\\Mindustry\\jre\\desktop.jar';
const MODS = 'E:\\Program Files (x86)\\Steam\\steamapps\\common\\Mindustry\\saves\\mods';
const NEEDLE = 'recentRespawnTimer';

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
// 直接数字节出现次数（常量池 UTF8 里会有名字），并统计修饰符(0x0002 private / 0x0001 public)
function scan(source, buf) {
  const res = [];
  for (const e of readZip(buf)) {
    if (!e.name.endsWith('.class')) continue;
    let c; try { c = readEntry(buf, e); } catch (x) { continue; }
    if (!/recentRespawnTimer/.test(c.toString('latin1'))) continue;
    // 统计 class 内出现的次数
    let cnt = 0, i = 0; const hay = c.toString('latin1');
    while ((i = hay.indexOf(NEEDLE, i)) >= 0) { cnt++; i += NEEDLE.length; }
    res.push({ src: source, cls: e.name.replace(/\.class$/, '').replace(/\//g, '.'), cnt });
  }
  return res;
}
let all = [];
try { all = all.concat(scan('desktop.jar', fs.readFileSync(JAR))); } catch (e) { console.log('jar err ' + e.message); }
for (const f of fs.readdirSync(MODS).filter(f => /\.(zip|jar)$/i.test(f))) {
  try {
    const b = fs.readFileSync(MODS + '\\' + f);
    if (b.toString('latin1', 0, 2) !== 'PK') continue;
    all = all.concat(scan(f, b));
  } catch (e) { }
}
console.log('包含 recentRespawnTimer 的类：');
for (const h of all) console.log('  [' + h.src + '] ' + h.cls + '   (出现 ' + h.cnt + ' 次)');
if (!all.length) console.log('  （无）');
