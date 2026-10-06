/**
 * class-members.js —— 从 jar 里的 class 文件直接读出「成员名 -> 字段还是方法」。
 *
 * 为什么需要它（本机三条路都堵着）：
 *   · Mindustry 自带的 jre 里**没有 javap**，而且 jdk.compiler 被剔掉了 ——
 *     `java Foo.java`（单文件源码模式）也要 jdk.compiler，所以连工具类都跑不起来；
 *   · 系统里只有 Java 8，读不了 17 的 class 文件；
 *   · 反射要 `-cp desktop.jar` 把类加载起来，缺 Arc 依赖就 NoClassDefFoundError。
 * 所以直接在 Node 里解析 ZIP + class 文件格式，**不加载类、不需要 JVM**。
 *
 * 用法:
 *   node tools/class-members.js <jar> <类名(点分)> [成员名...]
 *   node tools/class-members.js <jar> <类名> --all          # 列出全部成员
 *   node tools/class-members.js <jar> --grep <正则>         # 跨类搜成员名
 */
const fs = require('fs');
const zlib = require('zlib');

const jarPath = process.argv[2];
const clsArg = process.argv[3];
const rest = process.argv.slice(4);

// ---------------------------------------------------------------- ZIP
function zipEntries(buf){
  const out = [];
  let eocd = -1;
  for(let i = buf.length - 22; i >= 0 && i > buf.length - 70000; i--){
    if(buf.readUInt32LE(i) === 0x06054b50){ eocd = i; break; }
  }
  if(eocd < 0) throw new Error('找不到 ZIP 中央目录（EOCD）');
  const n = buf.readUInt16LE(eocd + 10);
  let p = buf.readUInt32LE(eocd + 16);
  for(let i = 0; i < n; i++){
    if(buf.readUInt32LE(p) !== 0x02014b50) throw new Error('中央目录条目签名不对 @' + p);
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
  const lmethod = buf.readUInt16LE(ent.lho + 8);
  const lcsize = buf.readUInt32LE(ent.lho + 18);
  const lusize = buf.readUInt32LE(ent.lho + 22);
  if(process.env.CM_DEBUG){
    console.log('[dbg] 条目 ' + ent.name + ' 中央目录: method=' + ent.method + ' csize=' + ent.csize + ' usize=' + ent.usize +
      ' | 本地头: method=' + lmethod + ' csize=' + lcsize + ' usize=' + lusize);
  }
  const nameLen = buf.readUInt16LE(ent.lho + 26);
  const extraLen = buf.readUInt16LE(ent.lho + 28);
  const start = ent.lho + 30 + nameLen + extraLen;
  // ⚠ 有的写入器在本地头里把 csize/usize 写成 0、把真值放进数据描述符（flag bit 3）。
  //   所以以中央目录为准，缺了就用本地头兜底。
  const csize = ent.csize || lcsize;
  const raw = buf.subarray(start, start + csize);
  if(ent.method === 0) return raw;
  if(ent.method === 8){
    const out = zlib.inflateRawSync(raw);
    if(process.env.CM_DEBUG) console.log('[dbg] 解压后 ' + out.length + ' 字节（期望 ' + (ent.usize || lusize) + '）');
    return out;
  }
  throw new Error('不支持的压缩方式 ' + ent.method + ' (' + ent.name + ')');
}

// ---------------------------------------------------------------- class 文件
function parseClass(b){
  if(b.readUInt32BE(0) !== 0xCAFEBABE) throw new Error('不是 class 文件');
  const cpCount = b.readUInt16BE(8);
  const tag = new Array(cpCount).fill(0);
  const val = new Array(cpCount).fill(null);
  let p = 10;
  for(let i = 1; i < cpCount; i++){
    const pBefore = p;
    const t = b[p++];
    tag[i] = t;
    switch(t){
      case 1: { const len = b.readUInt16BE(p); p += 2; val[i] = b.toString('utf8', p, p + len); p += len; break; }
      case 3: case 4: p += 4; break;
      case 5: case 6: p += 8; i++; break;
      case 7: case 8: case 16: case 19: case 20: val[i] = b.readUInt16BE(p); p += 2; break;
      case 15: p += 3; break;
      case 9: case 10: case 11: case 12: case 17: case 18: p += 4; break;
      default: p += 2; break;
    }
    if(process.env.CM_DEBUG && i >= Number(process.env.CM_FROM || 0) && i <= Number(process.env.CM_TO || 0)){
      console.log('[dbg] i=' + i + ' tag=' + t + ' p_before=' + pBefore + ' p_after=' + p +
        ' utf8=' + JSON.stringify(val[i] || null).slice(0, 40) +
        (process.env.CM_HEX && pBefore >= Number(process.env.CM_HEX) && pBefore <= Number(process.env.CM_HEX) + 60
          ? '   bytes=' + b.subarray(pBefore, pBefore + 24).toString('hex') : ''));
    }
    if(process.env.CM_DEBUG && i % 400 === 0){
      console.log('[dbg] i=' + i + ' tag=' + t + ' p=' + p + ' / ' + b.length);
    }
  }
  // Class/String/MethodType 常量要再跳一层：它们指向的是 CONSTANT_Utf8 的索引，
  // 直接按 Utf8 取会拿到 "?10" 这种编号。（tag 7/8/16/19/20）
  const utf = i => {
    if(!(i > 0 && i < cpCount)) return '?' + i;
    const t = tag[i];
    if(t === 1) return val[i];
    if(t === 7 || t === 8 || t === 16 || t === 19 || t === 20){
      const ref = val[i];
      if(ref > 0 && ref < cpCount && tag[ref] === 1) return val[ref];
    }
    return '?' + i;
  };
  if(process.env.CM_DEBUG){
    console.log('[dbg] 文件 ' + b.length + ' 字节, cpCount=' + cpCount + ', 常量池结束于 p=' + p);
    console.log('[dbg] 这里读到的 access_flags=' + b.readUInt16BE(p) +
      ' this=' + utf(b.readUInt16BE(p + 2)) + ' super=' + utf(b.readUInt16BE(p + 4)));
    console.log('[dbg] 前 24 字节: ' + b.subarray(0, 24).toString('hex'));
  }
  p += 2;                                    // access_flags
  const thisCls = b.readUInt16BE(p); p += 2;
  p += 2;                                    // super
  const ifCount = b.readUInt16BE(p); p += 2 + ifCount * 2;
  const members = [];
  for(const isField of [true, false]){
    const n = b.readUInt16BE(p); p += 2;
    for(let i = 0; i < n; i++){
      const flags = b.readUInt16BE(p); p += 2;
      const nameI = b.readUInt16BE(p); p += 2;
      const descI = b.readUInt16BE(p); p += 2;
      const attrN = b.readUInt16BE(p); p += 2;
      for(let a = 0; a < attrN; a++){
        p += 2;                              // attribute_name_index
        const len = b.readUInt32BE(p); p += 4 + len;
      }
      members.push({
        field: isField,
        name: utf(nameI),
        desc: utf(descI),
        isStatic: (flags & 0x0008) !== 0,
        isPublic: (flags & 0x0001) !== 0,
        isFinal: (flags & 0x0010) !== 0,
      });
    }
  }
  return { className: utf(thisCls), members };
}

// ---------------------------------------------------------------- 主流程
const buf = fs.readFileSync(jarPath);
const entries = zipEntries(buf);
const classes = entries.filter(e => e.name.endsWith('.class'));

function showClass(ent, want, all){
  const info = parseClass(readEntry(buf, ent));
  const rows = info.members.filter(m => all || want.includes(m.name));
  if(!rows.length && !all) return false;
  console.log('\n类 ' + info.className + '   (' + ent.name + ')');
  for(const m of rows){
    const kind = m.field ? '字段' : '方法';
    const mods = [m.isPublic ? 'public' : '', m.isStatic ? 'static' : '', m.isFinal ? 'final' : '']
      .filter(Boolean).join(' ');
    const parent = ent.name.split('/').slice(0, -1).join('/');
    const src = parent + '/' + ent.name.split('/').pop().replace(/\.class$/, '') + '.java';
    console.log('  ' + kind + '  ' + m.name + ' ' + m.desc + '   ' + mods +
      '   https://github.com/Anuken/Mindustry/blob/master/core/src/' + src);
  }
  if(all) console.log('  --- 共 ' + rows.length + ' 个成员 ---');
  return true;
}

if(clsArg === '--grep'){
  const re = new RegExp(rest[0], 'i');
  let hits = 0;
  for(const e of classes){
    let info;
    try { info = parseClass(readEntry(buf, e)); } catch(err){ continue; }
    const rows = info.members.filter(m => re.test(m.name));
    if(!rows.length) continue;
    hits++;
    console.log('\n类 ' + info.className);
    for(const m of rows) console.log('  ' + (m.field ? '字段' : '方法') + '  ' + m.name + ' ' + m.desc);
  }
  console.log('\n命中 ' + hits + ' 个类');
  process.exit(0);
}

const target = clsArg.replace(/\./g, '/') + '.class';
const ent = classes.find(e => e.name === target);
if(!ent){
  const fuzzy = classes.filter(e => e.name.endsWith('/' + clsArg.split('.').pop() + '.class'));
  console.log('!! jar 里没有 ' + target);
  if(fuzzy.length) console.log('   名字相近的：' + fuzzy.slice(0, 10).map(e => e.name).join(', '));
  process.exit(1);
}
const all = rest.includes('--all');
const want = rest.filter(x => x !== '--all');
showClass(ent, want, all);
