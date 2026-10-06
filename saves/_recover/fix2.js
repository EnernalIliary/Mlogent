// 两次往返修复：文件当前是"GBK 字符串被 UTF-8 编码"的双重编码状态。
//   步骤 1：按 UTF-8 解码 → 得到 GBK 语义字符串 → 按 CP936 编回字节 = 原始（受损）字节
//   步骤 2：把这些原始字节按 CP936 解码 → 得到真正的文本（不可映射字符已变成 '?'）
//           → 按 UTF-8 写出
const fs = require('fs');
const p = process.argv[2];
const utf8Text = fs.readFileSync(p, 'utf8');          // 双重编码的字符串
fs.writeFileSync(p + '.raw', Buffer.from(utf8Text, 'latin1')); // 占位，真正还原见下

// CP936 编码表：用 TextDecoder 反查代价高，直接用一张从 Node 拿不到的编码器 ——
// 改用 .NET 的 936 编码在 PowerShell 侧做，这里只负责把"双重编码文本"落盘成中间产物。
fs.writeFileSync(p + '.double.txt', utf8Text, 'utf8');
console.log('双重编码文本已落盘: ' + p + '.double.txt (' + Buffer.byteLength(utf8Text, 'utf8') + ' bytes)');
