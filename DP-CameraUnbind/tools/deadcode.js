// 死代码扫描：找出"定义了但没被调用"的函数/变量，以及只写不读的字段。
// 用法: node tools/deadcode.js
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', 'scripts', 'main.js'), 'utf8');

// 去掉注释，避免注释里的提及被当成"使用"
const code = src.replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '');

function occurrences(name){
  const re = new RegExp('\\b' + name.replace(/\$/g, '\\$') + '\\b', 'g');
  return (code.match(re) || []).length;
}

console.log('=== 函数：定义 + 引用次数（1 = 只有定义处，疑似死代码）===');
const fns = [...code.matchAll(/^\s*function\s+(\w+)/gm)].map(m => m[1]);
const dead = [];
for(const fn of fns){
  const n = occurrences(fn);
  const flag = n <= 1 ? '   <-- 疑似死代码' : '';
  if(n <= 1) dead.push(fn);
  console.log('  ' + fn.padEnd(24) + n + flag);
}

console.log();
console.log('=== 顶层 var：定义 + 引用次数 ===');
const vars = [...code.matchAll(/^\s*var\s+(\w+)\s*=/gm)].map(m => m[1]);
const deadVars = [];
for(const v of vars){
  const n = occurrences(v);
  const flag = n <= 1 ? '   <-- 疑似死代码' : '';
  if(n <= 1) deadVars.push(v);
  console.log('  ' + v.padEnd(24) + n + flag);
}

console.log();
console.log('=== 只写不读的对象字段（DBG.x / OV.x / camSave.x）===');
for(const obj of ['DBG', 'OV', 'camSave']){
  const fields = new Set();
  for(const m of code.matchAll(new RegExp('\\b' + obj + '\\.(\\w+)\\s*=', 'g'))) fields.add(m[1]);
  for(const f of fields){
    const writes = (code.match(new RegExp('\\b' + obj + '\\.' + f + '\\s*=', 'g')) || []).length;
    const reads = (code.match(new RegExp('\\b' + obj + '\\.' + f + '\\b(?!\\s*=[^=])', 'g')) || []).length;
    if(reads === 0) console.log('  ' + obj + '.' + f + '  只写不读（写 ' + writes + ' 次）  <-- 死字段');
  }
}

console.log();
console.log('=== API 成员：是否只被赋值、从未在本文件内被读取 ===');
const apiMembers = [...code.matchAll(/\bapi\.(\w+)\s*=/g)].map(m => m[1]);
for(const a of new Set(apiMembers)){
  const reads = (code.match(new RegExp('api\\.' + a + '\\b(?!\\s*=)', 'g')) || []).length;
  console.log('  api.' + a.padEnd(14) + ' 文件内读取 ' + reads + ' 次（这种是给控制台用的，0 次正常）');
}

console.log();
console.log('疑似死代码汇总: ' + (dead.length + deadVars.length) + ' 个');
if(dead.length) console.log('  函数: ' + dead.join(', '));
if(deadVars.length) console.log('  变量: ' + deadVars.join(', '));
