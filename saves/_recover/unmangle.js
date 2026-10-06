// 把受损的 test-harness.js 还原成"936 视图"的 UTF-8，并导出所有 `?` 位置的上下文，
// 供逐条重建被吃掉的字符。注意：`?` 是 Set-Content 按 CP936 编码时对不可映射字符写的
// 0x3F，**丢失的字节不可逆推**，只能按上下文重建。
const fs = require('fs');
const p = process.argv[2];
const raw = fs.readFileSync(p);
let s = new TextDecoder('gbk').decode(raw);
if(s.charCodeAt(0) === 0xFEFF) s = s.slice(1);
// 归一化行尾：GBK 解码不会动 0x0D/0x0A
fs.writeFileSync(p, s, 'utf8');
console.log('写出 UTF-8: ' + Buffer.byteLength(s, 'utf8') + ' bytes, 行数=' + s.split('\n').length);

const lines = s.split('\n');
let n = 0;
const out = [];
lines.forEach((ln, i) => {
  if(!ln.includes('?')) return;
  const marks = [];
  for(let k = 0; k < ln.length; k++){
    if(ln[k] === '?') marks.push(k);
  }
  n += marks.length;
  out.push('L' + (i + 1) + ' [' + marks.length + ']: ' + ln.trim());
});
console.log('含 ? 的行数 = ' + out.length + '，? 总数 = ' + n);
fs.writeFileSync(p.replace(/\.js$/, '.damage.txt'), out.join('\n'), 'utf8');
console.log('上下文报告 -> ' + p.replace(/\.js$/, '.damage.txt'));
