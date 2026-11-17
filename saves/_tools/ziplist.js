const fs=require('fs'),zlib=require('zlib');
function zipEntries(buf){const out=[];let e=-1;
 for(let i=buf.length-22;i>=0&&i>buf.length-70000;i--){if(buf.readUInt32LE(i)===0x06054b50){e=i;break}}
 const n=buf.readUInt16LE(e+10);let p=buf.readUInt32LE(e+16);
 for(let i=0;i<n;i++){const m=buf.readUInt16LE(p+10),cs=buf.readUInt32LE(p+20),us=buf.readUInt32LE(p+24),nl=buf.readUInt16LE(p+28),el=buf.readUInt16LE(p+30),cl=buf.readUInt16LE(p+32),lho=buf.readUInt32LE(p+42);
  out.push({name:buf.toString('utf8',p+46,p+46+nl),method:m,csize:cs,usize:us,lho});p+=46+nl+el+cl}
 return out}
const [,,inJar,outTxt]=process.argv;
const es=zipEntries(fs.readFileSync(inJar));
fs.writeFileSync(outTxt, es.map(e=>e.name).sort().join('\n'),'utf8');
console.log(inJar+' -> '+es.length+' entries -> '+outTxt);