import arc.math.geom.Vec2;

/**
 * 探针用子类：继承 arc.math.geom.Vec2，覆写所有会改变坐标的方法。
 * 由 CamAgent 把它替换到 arc.math.geom.Vec2 这个类名上（capabilities 关闭）,
 * 因此所有对 Vec2 的调用都会走这里；只有接受者是 Core.camera.position 时才记录。
 */
public class CamVec extends Vec2 {
    public static boolean ACTIVE = false;

    public CamVec() { super(); }

    public static void hit(String m) {
        if (ACTIVE) CamProbe.note(m);
    }

    @Override public Vec2 set(Vec2 v) { hit("set"); return super.set(v); }
    @Override public Vec2 set(float x, float y) { hit("set"); return super.set(x, y); }
    @Override public Vec2 add(Vec2 v) { hit("add"); return super.add(v); }
    @Override public Vec2 add(float x, float y) { hit("add"); return super.add(x, y); }
    @Override public Vec2 sub(Vec2 v) { hit("sub"); return super.sub(v); }
    @Override public Vec2 scl(float s) { hit("scl"); return super.scl(s); }
    @Override public Vec2 limit(float l) { hit("limit"); return super.limit(l); }
    @Override public Vec2 nor() { hit("nor"); return super.nor(); }
    @Override public Vec2 setZero() { hit("setZero"); return super.setZero(); }
    @Override public Vec2 lerp(Vec2 t, float p) { hit("lerp"); return super.lerp(t, p); }
    @Override public Vec2 lerpDelta(Vec2 t, float p) { hit("lerpDelta"); return super.lerpDelta(t, p); }
    @Override public Vec2 lerpDelta(float x, float y, float p) { hit("lerpDelta"); return super.lerpDelta(x, y, p); }
    @Override public Vec2 lerpPast(Vec2 t, float p) { hit("lerpPast"); return super.lerpPast(t, p); }
    @Override public Vec2 mulAdd(Vec2 v, float s) { hit("mulAdd"); return super.mulAdd(v, s); }
    @Override public Vec2 clamp(float a, float b) { hit("clamp"); return super.clamp(a, b); }
    @Override public Vec2 trns(float a, float b) { hit("trns"); return super.trns(a, b); }
}
