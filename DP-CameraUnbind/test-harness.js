// Logic test harness for DP-CameraUnbind. ASCII-only output on purpose (see README history:
// this file was once destroyed by a PowerShell codepage round-trip that ate every CJK char).
//
//   node test-harness.js            normal run
//   PROBE=1 node test-harness.js    extra load logging
//
// It fakes the minimum of Arc/Mindustry that scripts/main.js touches, then drives the
// per-frame order the real game uses:
//     gamePanningUpdate() -> gamePanCam() -> updateMovement() -> Events.fire(Trigger.update)
// and the things the mod promises are checked against that:
//   1) holding the unit-move key makes the unit walk to the *mouse*, not the screen centre;
//   2) holding the unit-move key does NOT let the camera get pushed toward the mouse,
//      including when the pan key is held at the same time (that combination was the
//      user-reported bug: keys are pan = middle, unit move = right, pressed together);
//   3) death -> respawn returns the camera to the pre-death view.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

let pass = 0, fail = 0;
const failures = [];
function ok(cond, label){
  if(cond){ pass++; console.log('  [OK] ' + label); }
  else { fail++; failures.push(label); console.log('  [FAIL] ' + label); }
}
function section(t){ console.log('\n== ' + t + ' =='); }

// ---------------------------------------------------------------- arc mock
class Vec2 {
  constructor(x = 0, y = 0){ this.x = x; this.y = y; }
  set(a, b){
    if(typeof a === 'number'){ this.x = a; this.y = b; }
    else { this.x = a.x; this.y = a.y; }
    return this;
  }
  setZero(){ return this.set(0, 0); }
  add(a, b){
    if(typeof a === 'number'){ this.x += a; this.y += b; }
    else { this.x += a.x; this.y += a.y; }
    return this;
  }
  sub(a, b){
    if(typeof a === 'number'){ this.x -= a; this.y -= b; }
    else { this.x -= a.x; this.y -= a.y; }
    return this;
  }
  scl(v){ this.x *= v; this.y *= v; return this; }
  addMul(a, s){ this.x += a.x * s; this.y += a.y * s; return this; }
  lerp(to, a){ this.x += (to.x - this.x) * a; this.y += (to.y - this.y) * a; return this; }
  nor(){
    const l = this.len();
    if(l > 0.000001){ this.x /= l; this.y /= l; }
    return this;
  }
  limit(max){
    const l2 = this.len2();
    if(l2 > max * max){ this.scl(max / Math.sqrt(l2)); }
    return this;
  }
  clamp(lo, hi){
    const l = this.len();
    if(l > 0){
      const v = Math.max(lo, Math.min(hi, l)) / l;
      this.x *= v; this.y *= v;
    }
    return this;
  }
  mulAdd(v, s){ this.x += v.x * s; this.y += v.y * s; return this; }
  len(){ return Math.sqrt(this.x * this.x + this.y * this.y); }
  len2(){ return this.x * this.x + this.y * this.y; }
  dst(v){ return Math.hypot(this.x - v.x, this.y - v.y); }
  within(v, r){ return this.dst(v) <= r; }
  cpy(){ return new Vec2(this.x, this.y); }
  isZero(){ return this.x === 0 && this.y === 0; }
  approachDelta(v, s){
    const d = this.dst(v);
    if(d > 0.000001){ this.x += (v.x - this.x) * Math.min(1, s / d); this.y += (v.y - this.y) * Math.min(1, s / d); }
    return this;
  }
}
Vec2.ZERO = new Vec2(0, 0);

const Time = { delta: 1 / 60, millis: () => Date.now(), timeSinceMillis: t => Date.now() - t };
const Angles = { mouseAngle: (x, y, tx, ty) => Math.atan2(ty - y, tx - x) };
const Tmp = { v1: new Vec2(), v2: new Vec2(), v3: new Vec2() };
const Mathf = { clamp: (v, lo, hi) => Math.max(lo, Math.min(hi, v)) };

// ---------------------------------------------------------------- bindings
class Binding {
  constructor(name){ this.name = name; this.value = { key: name }; }
}
const bindings = {};
for(const n of ['mouseMove', 'pan', 'moveX', 'moveY', 'boost', 'respawn', 'dropCargo',
                'pickupCargo', 'planetMap', 'detachCamera']){
  bindings[n] = new Binding(n);
}
bindings.mouseMove.value.key = 'KEY_MOUSEMOVE';
bindings.pan.value.key = 'KEY_PAN';
bindings.moveX.value.key = 'KEY_A';
bindings.moveY.value.key = 'KEY_D';

// ---------------------------------------------------------------- input
const keys = { down: new Set() };
const input = {
  panScale: 1 / 1500,
  panSpeed: 4.5,
  panBoostSpeed: 9,
  panning: true,
  movement: new Vec2(),
  keyDown(b){ return keys.down.has(b.value.key); },
  keyTap(b){ return this.keyDown(b); },
  axis(b){
    if(b === bindings.moveX) return keys.down.has('KEY_A') ? -1 : (keys.down.has('KEY_D') ? 1 : 0);
    if(b === bindings.moveY) return keys.down.has('KEY_S') ? -1 : (keys.down.has('KEY_W') ? 1 : 0);
    return 0;
  },
  mouseWorld(){ return new Vec2(world.mouseWorldX, world.mouseWorldY); }
};

// ---------------------------------------------------------------- camera
class Camera {
  constructor(){ this.position = new Vec2(); this.mat = { m00: 1, m01: 0, m10: 0, m11: 1 }; }
  update(){ }               // no-op: mouseWorld() is faked directly
}
const camera = new Camera();

// ---------------------------------------------------------------- graphics
const graphics = { getWidth: () => 800, getHeight: () => 600 };

// ---------------------------------------------------------------- settings
// Faithful to arc's Settings API: defaults() only fills in missing keys (it must
// NEVER overwrite a player's saved choice), put() writes, has() probes.
// NOTE: the mod's settingOn() swallows exceptions and returns false, so a missing
// method here does not fail loudly -- it silently turns the whole mod OFF.
const settingStore = {};
const settings = {
  getBool: (k, d) => (k in settingStore ? settingStore[k] : !!d),
  put(k, v){ settingStore[k] = v; },
  defaults(k, v){ if(!(k in settingStore)) settingStore[k] = v; },
  has(k){ return k in settingStore; }
};

// ---------------------------------------------------------------- units
// Faithful to the shape main.js actually touches (it re-implements all of
// DesktopInput.updateMovement, so the whole unit surface is exercised).
class UnitType {
  constructor(name, speed, accel){
    this.name = name; this.speed = speed; this.accel = accel;
    this.omniMovement = true; this.faceTarget = false;
    this.hasWeapons = () => false;    // vanilla: method, not field
  }
}
class Unit {
  constructor(id, type, x, y){
    this.id = id; this._type = type; this.x = x; this.y = y;
    this.vel = new Vec2(); this._valid = true;
    this._commands = [];
    this.controller = { hit(){} };
    this.aimX = 0; this.aimY = 0;     // vanilla: FIELDS, not methods
    this.rotation = 0;
  }
  type(){ return this._type; }
  speed(){ return this._type.speed; }
  isValid(){ return this._valid; }
  isPlayer(){ return true; }
  // arc Position#within has both overloads; main.js uses within(x, y, r).
  within(a, b, c){
    if(typeof a === 'number') return Math.hypot(this.x - a, this.y - b) <= c;
    return Math.hypot(this.x - a.x, this.y - a.y) <= b;
  }
  isCommandable(){ return true; }
  isAI(){ return false; }
  canMove(){ return true; }
  isFlying(){ return false; }
  isGrounded(){ return true; }
  isMechanical(){ return false; }
  isPayload(){ return false; }
  getPlayer(){ return null; }
  team(){ return { id: 1 }; }
  move(v){ this._commands.push(v.cpy()); }
  movePref(){ }                     // called with the movement vector; no-op
  lookAt(a){ this.rotation = a; }
  prefRotation(){ return 0; }
  aim(v){ this.aimX = v.x; this.aimY = v.y; }
  controlWeapons(){ }
}

// ---------------------------------------------------------------- world / Vars
const world = {
  mouseX: 400, mouseY: 300,          // screen centre = still, no vanilla pan push
  mouseWorldX: 1000, mouseWorldY: 1000,
  cutscene: false,
  fixedMouseWorld: null,
  uiBusy: false
};

const player = {
  x: 1000, y: 1000,
  _unit: null, _dead: false, core: new Vec2(5000, 5000),
  unit(){ return this._unit; },
  dead(){ return this._dead; },
  bestCore(){ return { x: this.core.x, y: this.core.y }; },
  team(){ return { id: 1 }; },
  // Player is an arc Position too; main.js calls player.within(x, y, r).
  within(a, b, c){
    if(typeof a === 'number') return Math.hypot(this.x - a, this.y - b) <= c;
    return Math.hypot(this.x - a.x, this.y - a.y) <= b;
  },
  shooting: false, boosting: false, mouseX: 0, mouseY: 0
};
player._unit = new Unit(1, new UnitType('flare', 4.5, 0.2), 1000, 1000);

const events = {};
const ET = {
  Trigger: { update: 'Trigger.update' },
  WorldLoadEvent: 'WorldLoadEvent',
  ResetEvent: 'ResetEvent',
  ClientLoadEvent: 'ClientLoadEvent',
  UnitDestroyEvent: 'UnitDestroyEvent',
  UnitChangeEvent: 'UnitChangeEvent',
  UnitCreateEvent: 'UnitCreateEvent',
  GameOverEvent: 'GameOverEvent',
  ResizeEvent: 'ResizeEvent',
  StateChangeEvent: 'StateChangeEvent',
  PlayEvent: 'PlayEvent',
  UnlockEvent: 'UnlockEvent',
  WorldLoadBeginEvent: 'WorldLoadBeginEvent'
};
const Events = {
  on(name, fn){ (events[name] = events[name] || []).push(fn); },
  fire(name, arg){ (events[name] || []).forEach(f => f(arg)); },
  run(name, fn){ (events[name] = events[name] || []).push(fn); }
};

// Control.setInput(handler): the real one (arc/Control) stores the handler and
// registers/unregisters listeners. main.js swaps it to install its override, so
// this must actually take effect -- a no-op stub silently voids every override test.
const control = {
  input,
  setInput(h){ this.input = h; },
  unit: null
};
const renderer = { isCutscene: () => world.cutscene };
const bundle = { get: (k, d) => (d !== undefined ? d : k), has: () => false, getLocale: () => 'en' };
const ui = { chatfrag: null, hudfrag: null };

const Vars = {
  control,
  player,
  renderer,
  ui,
  state: { isGame: () => true, isEditor: () => false },   // vanilla: methods, not fields
  mods: {
    getScripts: () => ({ scope: scriptScope, name: 'camera-unbind' }),
    // checkHidden() walks Vars.mods.getMods(); Seq needs .size (field) + .get(i).
    getMods: () => ({ size: 1, get: () => ({ name: 'camera-unbind', meta: { hidden: true } }) }),
    getModStrings: () => ({ size: 0, get: () => '' })
  },
  world: { units: [] },
  net: null
};

// ---------------------------------------------------------------- DesktopInput
// The real DesktopInput.updateMovement() steers toward the *screen centre* while
// detached. scripts/main.js overrides this method, so the mock must be faithful
// enough that "did the override change the target?" is observable.
// NOTE: written as a function + prototype (not `class`) on purpose -- Java classes
// are not ES classes, and the fixture needs DesktopInput.apply(input) to re-tag an
// existing object as an instance.
function DesktopInput(){
  this.movement = new Vec2();
  this.panning = true;
  this.panScale = 1 / 1500;
  this.panSpeed = 4.5;
  this.panBoostSpeed = 9;
  this.spectating = false;
  this.lastPayloadKeyTapMillis = 0;
  this.lastPayloadKeyHoldMillis = 0;
}
DesktopInput.prototype.locked = function(){ return false; };
DesktopInput.prototype.updateMovement = function(unit){
  const targetPos = new Vec2(camera.position.x, camera.position.y);   // screen centre
  const movement = this.movement;
  movement.set(targetPos).sub(unit).limit(unit.speed());
  return movement;
};
DesktopInput.prototype.panCamera = function(position){
  if(!this.locked()){
    this.panning = true;
    camera.position.set(position);
    camera.update();
  }
};

// JavaAdapter(superclass, obj) -- Rhino sugar yielding an instance of a
// superclass whose members come from obj. Faithful for instanceof + calls.
//
// IMPORTANT (fixture fidelity): the mod writes panSpeed through `Core.input`
// (the live DesktopInput) and reads movement through `this.movement` of the
// adapter. In the real game both are THE SAME OBJECT. Here the adapter is a
// separate instance, so it is made to DELEGATE its base state to the fixture's
// `input` (prototype chain): adapter.panSpeed then reflects Core.input.panSpeed,
// and adapter.movement is the very same Vec2 the assertions read.
// The active handler also becomes Core.input, mirroring Control.setInput().
function JavaAdapter(superclass, obj){
  const inst = Object.create(input);
  for(const k of Object.keys(obj)) inst[k] = obj[k];
  // Control.setInput() also repoints the game's live handler; Core.input follows
  // it in the real game (Core.input is assigned from control.input on init).
  Core.input = inst;
  control.input = inst;
  return inst;
}

// The game's live input handler IS a DesktopInput (that is exactly why
// main.js checks `input instanceof DesktopInput` before overriding). Turn the
// fixture's plain `input` object into one, in place, so Vars.control.input === input.
// NOTE: applying the constructor copies the fields; only setPrototypeOf() makes
// `input instanceof DesktopInput` true -- the fixture's input object is a plain
// object literal, and that is the check installOverride() gates on.
DesktopInput.apply(input);
Object.setPrototypeOf(input, DesktopInput.prototype);
input.panScale = 1 / 1500;

// ---------------------------------------------------------------- script scope
const scriptScope = {};

// Core == Packages.arc.Core (the script reaches it both ways).
const Core = { camera, input, settings, graphics, bundle, scene: { hasKeyboard: () => false } };

// ---------------------------------------------------------------- Packages mock
// In Rhino the mod script runs *inside* arc's scope, so `Packages.arc.<name>` is
// literally the same object as the plain global `<name>`. That matters for
// DesktopInput: main.js does `input instanceof Packages.mindustry.input.DesktopInput`,
// and the fixture's live `input` must be an instance of that very same function.
const arcNamespace = {
  Core,
  math: { Angles, Mathf },
  util: { Time, Tmp, Timer: { schedule: () => ({}) } },
  input: { KeyCode: { v: 'KEY_V', mouseBack: 'KEY_MOUSEBACK', mouseForward: 'KEY_MOUSEFORWARD' } },
  Events
};
const Packages = {
  arc: arcNamespace,
  mindustry: {
    Vars,
    input: { Binding: bindings, DesktopInput },
    game: { EventType: ET },
    ui: { dialogs: { SettingsMenuDialog: { SettingsTable: { CheckSetting: function(){} } } } },
    gen: { Mechc: function(){}, Payloadc: function(){} }
  },
  rhino: {
    ScriptableObject: {
      putProperty(scope, name, value){ scope[name] = value; },
      getProperty(scope, name){ return scope[name]; }
    }
  }
};
arcNamespace.math.geom = { Vec2 };

// ---------------------------------------------------------------- globals
const sandbox = {
  Packages, Vec2, Time, Angles, Tmp, Mathf, Events, ET, Vars, control, camera,
  settings, graphics, input, bindings, player, world, ui, bundle, DesktopInput, Core,
  JavaAdapter, console, Math, JSON, Date, String, Number, Boolean, Array, Object, Error,
  parseInt, parseFloat, isNaN, isFinite
};
sandbox.globalThis = sandbox;
sandbox.log = (...a) => { if(process.env.PROBE) console.log('    [script] ' + a.join(' ')); };
sandbox.print = sandbox.log;
let _an = 0;
let _gn = 0;
let _mn = 0;
let _cn = 0;
let _ln = 0;
let _hn = 0;

sandbox.Packages = Packages;

// ---------------------------------------------------------------- load main.js
const mainPath = path.join(__dirname, 'scripts', 'main.js');
const code = fs.readFileSync(mainPath, 'utf8');
vm.createContext(sandbox);
try {
  vm.runInContext(code, sandbox, { filename: 'scripts/main.js' });
} catch(e){
  console.error('FAILED to load scripts/main.js: ' + e);
  process.exit(2);
}

// ClientLoadEvent installs the override; the real game fires it once after load.
Events.fire(ET.ClientLoadEvent, {});
section('load');
ok(typeof scriptScope.camVersion === 'function', 'camVersion() exported');
ok(scriptScope.camVersion() === '5.6', 'camVersion() = ' + scriptScope.camVersion());
ok(typeof scriptScope.camWhere === 'function', 'camWhere() exported');
ok(typeof scriptScope.camClearHold === 'function', 'camClearHold() exported (test hook)');
ok(scriptScope.camOverride() === 'installed', 'override installed: ' + scriptScope.camOverride());

const where = () => JSON.parse(scriptScope.camWhere());

// ---------------------------------------------------------------- frame driver
function setCamera(x, y){ camera.position.set(x, y); }
// Faithful frame order (this is the whole basis of the mod's design):
//   Control.update() -> input.update()          [vanilla writes the camera]
//   logic.update()   -> Events.fire(Trigger)    [the mod clamps, last word]
function fireUpdate(opts){
  opts = opts || {};
  if(opts.cutscene !== undefined) world.cutscene = opts.cutscene;
  // 1) vanilla panning decision (DesktopInput.update lines 273/278)
  if(keys.down.has('KEY_MOUSEMOVE') || keys.down.has('KEY_W') || keys.down.has('KEY_A')){
    input.panning = false;
  } else if(keys.down.has('KEY_PAN') || settings.getBool('detach-camera', false)){
    input.panning = true;
  }
  // 2) vanilla movement: input.update() calls updateMovement(unit)
  control.input.updateMovement(player._unit);
  // 3) vanilla pan push. Real DesktopInput gates this on its LOCAL panCam flag
  //    (set purely by the "pan" binding), NOT on `panning`: while detached,
  //    panning is true regardless of the move key. Gating it on panning+move
  //    here would make the mod's panSpeed-zeroing look like it stopped the
  //    camera for the wrong reason -- that was a fixture bug, not a mod bug.
  if(keys.down.has('KEY_PAN')){
    const camSpeed = control.input.panSpeed * Time.delta;
    const dx = Math.max(-1, Math.min(1, (world.mouseX - graphics.getWidth() / 2) * input.panScale)) * camSpeed;
    const dy = Math.max(-1, Math.min(1, (world.mouseY - graphics.getHeight() / 2) * input.panScale)) * camSpeed;
    camera.position.x += dx;
    camera.position.y += dy;
  }
  // 4) the event the mod hooks
  Events.fire(ET.Trigger.update, {});
}
function press(key, on = true){ if(on) keys.down.add(key); else keys.down.delete(key); }
function holdMove(on = true){ press('KEY_MOUSEMOVE', on); }
function pressPan(on = true){ press('KEY_PAN', on); }
function moveLen(){ return Math.hypot(input.movement.x, input.movement.y); }

// Enable free camera for everything below (the mod does nothing otherwise).
settingStore['detach-camera'] = true;

// ================================================================ case 1
section('1) hold unit-move key alone: camera pinned, unit walks to mouse');
setCamera(1000, 1000);
player._unit.x = 1000; player._unit.y = 1000;
world.mouseX = 700;                       // off-centre so vanilla WOULD push
world.mouseWorldX = 1600; world.mouseWorldY = 900;
holdMove(true);
fireUpdate();                             // let suppression take over
const c1 = camera.position.cpy();
for(let i = 0; i < 10; i++) fireUpdate();
ok(control.input.panSpeed === 0, 'panSpeed forced to 0 while holding move key (' + control.input.panSpeed + ')');
ok(Math.abs(camera.position.x - c1.x) < 0.01 && Math.abs(camera.position.y - c1.y) < 0.01,
   'camera stayed put 10 frames (' + c1.x.toFixed(2) + ',' + c1.y.toFixed(2) + ' -> '
   + camera.position.x.toFixed(2) + ',' + camera.position.y.toFixed(2) + ')');
const w1 = where();
ok(w1.hold === true, 'camWhere().hold = true while dragging');
ok(Math.abs(camera.position.x - Number(w1.pinX)) < 1.5,
   'camera is at the pin (' + camera.position.x.toFixed(2) + ' vs pinX ' + w1.pinX + ')');
ok(moveLen() > 0.01, 'movement non-zero while holding move key (' + moveLen().toFixed(2) + ')');

// ================================================================ case 2 (reported bug)
section('2) pan key + unit-move key held together (user setup: middle + right)');
setCamera(1000, 1000);
player._unit.x = 1000; player._unit.y = 1000;
input.panSpeed = 4.5;
pressPan(true);
holdMove(true);
world.mouseX = 700;
fireUpdate();                             // let suppression take over first
const c2 = camera.position.cpy();
const sub = [];
for(let i = 0; i < 10; i++){
  fireUpdate();
  sub.push(camera.position.x.toFixed(2));
}
ok(control.input.panSpeed === 0, 'panSpeed forced to 0 with both keys held (' + control.input.panSpeed + ')');
ok(Math.abs(camera.position.x - c2.x) < 0.01 && Math.abs(camera.position.y - c2.y) < 0.01,
   'camera pinned with pan+move held (frames: ' + sub.join(' ') + ')');
ok(where().pin !== 'none', 'pin still active with pan held (pin=' + where().pin + ')');
const mx = input.movement.x, my = input.movement.y;
const toMouseX = world.mouseWorldX - player._unit.x, toMouseY = world.mouseWorldY - player._unit.y;
const dot = (mx * toMouseX + my * toMouseY) / (Math.hypot(mx, my) * Math.hypot(toMouseX, toMouseY) || 1);
ok(Math.hypot(mx, my) > 0.01, 'movement non-zero with both keys held (' + mx.toFixed(2) + ',' + my.toFixed(2) + ')');
ok(dot > 0.99, 'movement points at the mouse (cos=' + dot.toFixed(3) + ')');

// ================================================================ case 3
section('3) release both keys: hand back to vanilla');
pressPan(false);
holdMove(false);
fireUpdate();
ok(control.input.panSpeed > 0, 'panSpeed restored after release (' + control.input.panSpeed + ')');
const c3 = camera.position.cpy();
for(let i = 0; i < 10; i++) fireUpdate();
ok(Math.abs(camera.position.x - c3.x) < 0.01, 'mod no longer writes the camera after release');

// ================================================================ case 4
section('4) pan key alone: vanilla panning must still work');
scriptScope.camClearHold();
setCamera(1000, 1000);
world.mouseX = 700;
pressPan(true);
for(let i = 0; i < 10; i++) fireUpdate();
ok(camera.position.x > 1000.05,
   'holding pan alone pushes the camera (1000 -> ' + camera.position.x.toFixed(2) + ')');
ok(control.input.panSpeed > 0, 'panSpeed untouched when pan is held alone (' + control.input.panSpeed + ')');
pressPan(false);
fireUpdate();

// ================================================================ case 5
section('5) switch off: byte-for-byte vanilla');
scriptScope.camCursor(false);
// Camera deliberately AWAY from the unit: with the mod off, vanilla must steer the
// unit toward the screen centre (camera.position) -- the original behaviour.
setCamera(2000, 2000);
player._unit.x = 1000; player._unit.y = 1000;
world.mouseWorldX = 1600; world.mouseWorldY = 900;
holdMove(true);
fireUpdate();
const mv = input.movement.cpy();
ok(Math.hypot(mv.x, mv.y) > 0,
   'movement recomputed by the game while the mod is off (' + mv.x.toFixed(2) + ',' + mv.y.toFixed(2) + ')');
ok(control.input.panSpeed > 0, 'panSpeed untouched when the mod is off (' + control.input.panSpeed + ')');
holdMove(false);
scriptScope.camCursor(true);
fireUpdate();

// ================================================================ case 6
section('6) death -> respawn returns to the pre-death view');
scriptScope.camClearHold();
setCamera(1200, 1300);                    // pre-death view
fireUpdate();
ok(where().deathSnap === 'none', 'no snapshot while alive');
player._dead = true;
fireUpdate();                             // death frame -> snapshot taken
const atDeath = where();
ok(atDeath.deathSnap === '1200,1300',
   'snapshot taken at death = pre-death view (' + atDeath.deathSnap + ')');
world.cutscene = true;                    // landing animation
setCamera(6000, 6000);
for(let i = 0; i < 5; i++) fireUpdate();
ok(where().deathSnap === '1200,1300', 'snapshot survives the landing animation');
world.cutscene = false;
player._unit._valid = false;              // respawn: new unit at the core
fireUpdate();
player._unit = new Unit(9, new UnitType('alpha', 4.5, 0.2), 6000, 6000);
player._dead = false;
player.x = 6000; player.y = 6000;
setCamera(6000, 6000);
fireUpdate();
ok(Math.abs(camera.position.x - 1200) < 1.5,
   'camera returned to the pre-death view (x=' + camera.position.x.toFixed(2) + ', want ~1200)');
ok(where().deathSnap === 'none', 'snapshot consumed exactly once');
for(let i = 0; i < 10; i++) fireUpdate();
ok(Math.abs(camera.position.x - 1200) < 1.5,
   'grace period keeps the view without holding any key (x=' + camera.position.x.toFixed(2) + ')');

// ================================================================ case 7
section('7) world reset clears every piece of state');
Events.fire(ET.ResetEvent, {});
const afterReset = where();
ok(afterReset.deathSnap === 'none', 'deathSnap cleared on reset');

// ================================================================ case 8
section('8) legacy mode (v146 academic-build feel): unit walks to the screen centre');
scriptScope.camClearHold();
scriptScope.camCursor(true);              // main switch on
scriptScope.camLegacy(true);
ok(where().legacy === true, 'camWhere().legacy = ' + where().legacy);
ok(where().moveTarget === 'camera', 'moveTarget = ' + where().moveTarget);

// Camera and mouse deliberately in DIFFERENT directions from the unit, so
// "walked to the camera" and "walked to the mouse" cannot be confused.
setCamera(2000, 2000);                    // unit -> camera = (+1000,+1000) = 45 degrees
player._unit.x = 1000; player._unit.y = 1000;
world.mouseWorldX = 1200; world.mouseWorldY = 1600;   // unit -> mouse = (+200,+600) = ~72 degrees
holdMove(true);
const camBefore8 = camera.position.x;
fireUpdate();
const m8 = input.movement.cpy();
ok(Math.abs(m8.x - m8.y) < 1e-6,
   'movement points at the CAMERA, not the mouse (45deg, not 72deg): '
   + m8.x.toFixed(3) + ',' + m8.y.toFixed(3));
ok(Math.abs(camera.position.x - camBefore8) < 1e-6,
   'camera still pinned while the move key is held (' + camera.position.x.toFixed(2) + ')');
ok(control.input.panSpeed === 0,
   'panSpeed still zeroed in legacy mode (' + control.input.panSpeed + ')');
holdMove(false);

// WASD must NOT count as "the player is moving the unit" here: in legacy mode
// vanilla uses WASD to pan the camera, so pinning it would break the mode.
press('KEY_W', true);
fireUpdate();
ok(where().hold === false, 'WASD does not pin the camera in legacy mode (hold=' + where().hold + ')');
press('KEY_W', false);
fireUpdate();

scriptScope.camLegacy(false);
ok(where().moveTarget === 'mouse', 'camLegacy(false) restores mouse targeting');
ok(where().legacy === false, 'camWhere().legacy = ' + where().legacy);
fireUpdate();

// ---------------------------------------------------------------- summary
console.log('\nResult: ' + pass + ' passed / ' + fail + ' failed');
if(fail){
  console.log('Failures:');
  failures.forEach(f => console.log('  - ' + f));
}
process.exit(fail ? 1 : 0);
