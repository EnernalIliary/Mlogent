// classinfo.js —— 打印 jar 里的条目与 class 文件版本（major），并可按正则筛选条目。
// 用法: node classinfo.js <jar> [entryRegex]
const fs = require('fs');
const zlib = require('zlib');

function zipEntries(buf){
  const out = [];
  let eocd = -1;
  for(let i = buf.length - 22; i >= 0 && i > buf.length - 70000; i--){
    if(buf.readUInt32LE(i) === 0x06054b50){ eocd = i; break; }
  }
  if(eocd < 0) throw new Error('no EOCD');
  const n = buf.readUInt16LE(eocd + 10);
  let p = buf.readUInt32LE(eocd + 16);
  for(let i = 0; i < n; i++){
    const method = buf.readUInt16LE(p + 10);
    const csize = buf.readUInt32LE(p + 20);
    const usize = buf.readUInt32LE(p + 24);
    const nameLen = buf.readUInt16LE(p + 28);
    const extraLen = buf.readUInt16LE(p + 30);
    const cmtLen = buf.readUInt16LE(p + 32);
    const lho = buf.readUInt32LE(p + 42);
    const name = buf.toString('utf8', p + 46, p + 46 + nameLen);
    out.push({ name, method, csize, usize, lho });
    p += 46 + nameLen + extraLen + cmtLen;
  }
  return out;
}
function readEntry(buf, ent){
  const nameLen = buf.readUInt16LE(ent.lho + 26);
  const extraLen = buf.readUInt16LE(ent.lho + 28);
  const start = ent.lho + 30 + nameLen + extraLen;
  const raw = buf.subarray(start, start + (ent.csize || buf.readUInt32LE(ent.lho + 18)));
  return ent.method === 8 ? zlib.inflateRawSync(raw) : raw;
}

const jar = process.argv[2];
const re = process.argv[3] ? new RegExp(process.argv[3], 'i') : null;
const buf = fs.readFileSync(jar);
const es = zipEntries(buf);
console.log('jar: ' + jar + '  entries=' + es.length);
const byVersion = {};
for(const e of es){
  if(!e.name.endsWith('.class')) continue;
  let b;
  try { b = readEntry(buf, e); } catch(err){ continue; }
  const major = b.readUInt16BE(6);
  byVersion[major] = (byVersion[major] || 0) + 1;
}
console.log('class 版本分布: ' + JSON.stringify(byVersion));
if(re){
  const hits = es.filter(e => re.test(e.name));
  console.log('匹配 "' + process.argv[3] + '" 的条目 (' + hits.length + '):');
  for(const h of hits.slice(0, 120)) console.log('  ' + h.name + '  (' + h.usize + ' B)');
}
