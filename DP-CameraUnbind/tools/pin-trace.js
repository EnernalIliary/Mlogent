// 一次性诊断：按住移动键后连续 30 帧，相机每帧在哪、锚点在哪。
const fs = require('fs');
const path = require('path');
const h = fs.readFileSync(path.join(__dirname, '..', 'test-harness.js'), 'utf8');
// 截到 [3] 之前（复用它的环境与工具）
const cut = h.indexOf("console.log('\\n[3]");
const head = h.slice(0, cut);
const env = new Function('require', 'console', 'process', '__dirname',
  head + `
  return { world, control, keys, scriptScope, fireUpdate, setCamera, holdMouseMove,
           pressPan, Events, ET, ui, inputAdapterRef: () => inputAdapter };
`)(require, console, process, path.join(__dirname, '..'));

const { world, control, keys, scriptScope, fireUpdate, setCamera, holdMouseMove } = env;

world.settings.put('detach-camera', true);
world.settings.put('dp-camera-unbind', true);
env.Events.fire(env.ET.ClientLoadEvent);

// 对齐到自由视角静止态
for(let i = 0; i < 3; i++) fireUpdate({ panning: true });

setCamera(1000, 1000);
fireUpdate({ panning: true });
console.log('起始：相机 =', world.camera.position.x.toFixed(1), ' 锚点 =', scriptScope.camWhere().match(/"pin":"([^"]*)"/)[1]);

holdMouseMove(true);
console.log('\n帧  相机x     锚点x     hold  panSpeed   pin');
for(let i = 0; i < 12; i++){
  fireUpdate();
  const w = JSON.parse(scriptScope.camWhere());
  console.log(String(i).padStart(2) + '  '
    + world.camera.position.x.toFixed(2).padStart(8) + '  '
    + String(w.pinX).padStart(8) + '  '
    + String(w.hold).padStart(5) + '  '
    + String(control.input.panSpeed).padStart(8) + '  ' + w.pin);
}
