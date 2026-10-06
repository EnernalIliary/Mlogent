import arc.*;
import arc.math.geom.*;
import arc.util.*;
import mindustry.*;
import mindustry.game.Team;
import mindustry.gen.*;
import mindustry.input.*;
import static arc.Core.*;
import static mindustry.Vars.*;

/**
 * 类型校验：把这次改动新增/改动的表达式原样写一遍，对着 desktop.jar 编译。
 * 只为验证类型与 API 存在性，不参与游戏运行。
 * 注意：DesktopInput 继承的类里有 `import static arc.Core.*`，所以 `settings` 指的是 Core.settings。
 */
public class PatchCheck{
    Unit unit;
    Input input;

    void checkMovement(){
        float speed = 1f;

        // ↓↓↓ 新增的表达式（与 DesktopInput.updateMovement 里一致）
        Vec2 targetPos = settings.getBool("freecam-cursor-move", true) && Core.input.keyDown(Binding.mouseMove)
            ? Tmp.v1.set(input.mouseWorld()) : Core.camera.position;

        Vec2 movement = new Vec2();
        movement.set(targetPos).sub(player).limit(speed);

        float arrive = settings.getBool("freecam-cursor-move", true) ? 6f : 15f;

        if(settings.getBool("freecam-cursor-move", true) && !Core.input.keyDown(Binding.mouseMove)){
            movement.setZero();
            unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2f);
        }else if(player.within(targetPos, arrive)){
            movement.setZero();
            unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2f);
        }
        // ↑↑↑
    }

    void checkRecenterGate(){
        // ↓↓↓ 新增的开关判断（与 DesktopInput.update 里一致）
        boolean panning = false;
        if((!player.dead() || true) && !panning && settings.getBool("freecam-recenter", true)){
            Team corePanTeam = state.won ? state.rules.waveTeam : player.team();
            Position coreTarget = state.gameOver && !state.rules.pvp && corePanTeam.data().lastCore != null
                ? corePanTeam.data().lastCore : null;
            Position panTarget = coreTarget != null ? coreTarget : null;
            Core.camera.position.lerpDelta(panTarget == null ? player : panTarget, settings.getBool("smoothcamera") ? 0.08f : 1f);
        }
        // ↑↑↑
    }
}
