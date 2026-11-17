// strscan.js —— 扫 jar 里所有 class 的字符串常量池，找含关键词的类。
// 用法: node strscan.js <jar> <关键词1> [关键词2] ...
const fs = require('fs');
const zlib = require('zlib');

function zipEntries(buf){
  const out = []; let eocd = -1;
  for(let i = buf.length - 22; i >= 0 && i > buf.length - 70000; i--){
    if(buf.readUInt32LE(i) === 0x06054b50){ eocd = i; break; }
  }
  const n = buf.readUInt16LE(eocd + 10); let p = buf.readUInt32LE(eocd + 16);
  for(let i = 0; i < n; i++){
    const method = buf.readUInt16LE(p + 10), csize = buf.readUInt32LE(p + 20);
    const nl = buf.readUInt16LE(p + 28), el = buf.readUInt16LE(p + 30), cl = buf.readUInt16LE(p + 32);
    const lho = buf.readUInt32LE(p + 42);
    out.push({ name: buf.toString('utf8', p + 46, p + 46 + nl), method, csize, lho });
    p += 46 + nl + el + cl;
  }
  return out;
}
function readEntry(buf, ent){
  const nl = buf.readUInt16LE(ent.lho + 26), el = buf.readUInt16LE(ent.lho + 28);
  const start = ent.lho + 30 + nl + el;
  const raw = buf.subarray(start, start + ent.csize);
  return ent.method === 8 ? zlib.inflateRawSync(raw) : raw;
}

// 只取 Utf8 常量，别的 tag 跳过
function utf8Strings(b){
  const cpCount = b.readUInt16BE(8);
  let p = 10;
  const out = [];
  for(let i = 1; i < cpCount; i++){
    const t = b[p++];
    switch(t){
      case 1: { const len = b.readUInt16BE(p); p += 2; out.push(b.toString('utf8', p, p + len)); p += len; break; }
      case 3: case 4: case 9: case 10: case 11: case 12: case 17: case 18: p += 4; break;
      case 5: case 6: p += 8; i++; break;
      case 7: case 8: case 16: case 19: case 20: p += 2; break;
      case 15: p += 3; break;
      default: p += 2; break;
    }
  }
  return out;
}

const [,, jar, ...keys] = process.argv;
const buf = fs.readFileSync(jar);
const es = zipEntries(buf);
const lowered = keys.map(k => k.toLowerCase());
for(const e of es){
  if(!e.name.endsWith('.class')) continue;
  let b; try { b = readEntry(buf, e); } catch(err){ continue; }
  let strs; try { strs = utf8Strings(b); } catch(err){ continue; }
  const hits = [];
  for(const s of strs){
    const ls = s.toLowerCase();
    for(let i = 0; i < lowered.length; i++){
      if(ls.includes(lowered[i])) hits.push(s);
    }
  }
  if(hits.length){
    const uniq = [...new Set(hits)];
    console.log('\n' + e.name);
    for(const h of uniq.slice(0, 12)) console.log('   ' + JSON.stringify(h).slice(0, 160));
  }
}
