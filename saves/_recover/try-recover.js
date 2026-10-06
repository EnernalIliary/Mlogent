// 尝试逆推 PowerShell 5.1 的 Set-Content 代码页往返：
//   原文(UTF-8) --按 CP936 解码--> (至少一个 U+FFFD) --写入时按 CP936 编码--> 现文件
// 若是这样，现文件按 CP936 读成字节、再按 UTF-8 解码即可还原（除了吃掉换行/空格的差异）。
const fs = require('fs');

const files = process.argv.slice(2);
for(const f of files){
  const cur = fs.readFileSync(f);
  const asUtf8Text = cur.toString('utf8').replace(/^\uFEFF/, '');
  console.log('=== ' + f + '  (' + cur.length + ' bytes, U+FFFD=' +
    (asUtf8Text.match(/\uFFFD/g) || []).length + ')');
  for(const enc of ['gbk', 'gb18030', 'latin1']){
    let bytes;
    try { bytes = Buffer.from(asUtf8Text, enc); } catch(e){ console.log('  ' + enc + ': 编码失败 ' + e.message); continue; }
    const back = bytes.toString('utf8');
    const bad = (back.match(/\uFFFD/g) || []).length;
    // 合法性：不允许出现孤立的 0xEF 0xBF 0xBD 之外的替换字符
    console.log('  ' + enc.padEnd(8) + ' -> ' + bytes.length + ' bytes, 再解码 U+FFFD=' + bad);
    if(bad === 0){
      const out = f + '.recovered';
      fs.writeFileSync(out, back);
      console.log('    ✓ 零损失，已写出 ' + out);
    }
  }
}
