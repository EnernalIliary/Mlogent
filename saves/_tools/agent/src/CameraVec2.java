import arc.*;
import arc.math.geom.*;

/** 追踪版 Vec2：所有会改坐标的方法都先报告调用点，再走原实现。 */
public class CameraVec2 extends Vec2 {
    @Override public Vec2 set(Vec2 v) { return (Vec2) CamProbe.before("set", this, super.set(v)); }
    @Override public Vec2 set(float x, float y) { return (Vec2) CamProbe.before("set", this, super.set(x, y)); }
    @Override public Vec2 add(Vec2 v) { return (Vec2) CamProbe.before("add", this, super.add(v)); }
    @Override public Vec2 add(float x, float y) { return (Vec2) CamProbe.before("add", this, super.add(x, y)); }
    @Override public Vec2 sub(Vec2 v) { return (Vec2) CamProbe.before("sub", this, super.sub(v)); }
    @Override public Vec2 scl(float s) { return (Vec2) CamProbe.before("scl", this, super.scl(s)); }
    @Override public Vec2 limit(float l) { return (Vec2) CamProbe.before("limit", this, super.limit(l)); }
    @Override public Vec2 nor() { return (Vec2) CamProbe.before("nor", this, super.nor()); }
    @Override public Vec2 setZero() { return (Vec2) CamProbe.before("setZero", this, super.setZero()); }
    @Override public Vec2 lerp(Vec2 t, float p) { return (Vec2) CamProbe.before("lerp", this, super.lerp(t, p)); }
    @Override public Vec2 lerpDelta(Position t, float p) { return (Vec2) CamProbe.before("lerpDelta", this, super.lerpDelta(t, p)); }
    @Override public Vec2 lerpDelta(float x, float y, float p) { return (Vec2) CamProbe.before("lerpDelta", this, super.lerpDelta(x, y, p)); }
    @Override public Vec2 mulAdd(Vec2 v, float s) { return (Vec2) CamProbe.before("mulAdd", this, super.mulAdd(v, s)); }
    @Override public Vec2 clamp(float a, float b) { return (Vec2) CamProbe.before("clamp", this, super.clamp(a, b)); }
}
