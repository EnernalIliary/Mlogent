import arc.Core;
import arc.math.geom.Vec2;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.lang.reflect.Field;

/**
 * CamProbe —— 只记录"谁在改 Core.camera.position"。
 * 由 CamAgent 注入；替换后的 arc.math.geom.Vec2（= CameraVec2）在每次变换时调用 before()。
 *
 * 输出: <游戏工作目录>/cam-trace.log
 * 控制: <游戏工作目录>/cam-trace-ctl.txt 内容 "on" / "off" / "count" / "reset" / "quit"
 *
 * 三种模式：
 *   normal  —— 只按"调用点|方法"去重计数（极廉价，长期开着也不卡）
 *   capture —— 打印每一处变换的调用点 + 相机坐标变化（要取堆栈，会慢，短时用）
 *   count   —— 累计每 500 次变换打一行平均坐标位移（用来把没定性的抖动也纳入统计）
 */
public class CamProbe {
    static final ThreadLocal<Boolean> BUSY = ThreadLocal.withInitial(() -> Boolean.FALSE);
    public static volatile boolean capture = false;
    static PrintWriter out;
    static Vec2 CAM;                 // Core.camera.position 的真实身份
    public static int camIdentity() { return CAM == null ? 0 : System.identityHashCode(CAM); }
    static boolean ready = false, armed = false;
    static int boom = 0;

    static long t0 = System.currentTimeMillis();
    static String lastKey = "";
    static int repeat = 0;
    static long lastFlush = 0;
    static Object lastUnit = null;
    static float lastCx = Float.NaN, lastCy = Float.NaN;

    static long count = 0;
    static float sumDx = 0, sumDy = 0;
    static int countRow = 0;
    static String ctlLast = "";

    /** 每次 Vec2 变换都会经过这里；接受者不是相机就立刻返回（极廉价） */
    public static Object before(String m, Vec2 self, Object ret) {
        if (self != CAM) return ret;
        if (BUSY.get()) return ret;
        BUSY.set(Boolean.TRUE);
        try {
            trace(m);
        } catch (Throwable t) {
            if (boom++ < 5) System.err.println("[CamProbe] " + t);
        } finally {
            BUSY.set(Boolean.FALSE);
        }
        return ret;
    }

    /** 启动后调用：定位 Camera.position、开日志、起控制文件轮询线程 */
    public static synchronized void arm() {
        if (armed) return;
        armed = true;
        try {
            Object cam = Core.class.getField("camera").get(null);
            if (cam == null) { armed = false; return; }
            Field p = cam.getClass().getField("position");
            CAM = (Vec2) p.get(cam);
            out = new PrintWriter(new OutputStreamWriter(new FileOutputStream("cam-trace.log", false), StandardCharsets.UTF_8), true);
            ready = true;
            say("=== CamProbe armed ===");
            say("CAM identity = " + System.identityHashCode(CAM) + "  x=" + CAM.x + " y=" + CAM.y);
            say("控制文件: cam-trace-ctl.txt  值 on/off/count/reset/quit");
            Thread th = new Thread(CamProbe::watch, "CamProbe-watch");
            th.setDaemon(true);
            th.start();
        } catch (Throwable t) {
            System.err.println("[CamProbe] arm failed: " + t);
        }
    }

    static void say(String s) {
        if (out != null) out.println(s);
        System.out.println("[CamProbe] " + s);
    }

    /** 轮询控制文件：随时开关抓取，不用改脚本重开游戏 */
    static void watch() {
        File f = new File("cam-trace-ctl.txt");
        while (true) {
            try {
                Thread.sleep(500);
                if (f.isFile()) {
                    String v = new String(Files.readAllBytes(Paths.get("cam-trace-ctl.txt")), StandardCharsets.UTF_8).trim().toLowerCase();
                    if (!v.equals(ctlLast)) {
                        ctlLast = v;
                        if (v.startsWith("on")) { capture = true; say(">>> 抓取开启"); }
                        else if (v.startsWith("off")) { capture = false; say(">>> 抓取关闭"); }
                        else if (v.startsWith("count")) { countMode(); }
                        else if (v.startsWith("reset")) { count = 0; sumDx = 0; sumDy = 0; countRow = 0; say(">>> 统计清零"); }
                        else if (v.startsWith("quit")) { say(">>> 退出控制线程"); return; }
                    }
                }
                if (countRow > 0 && count % countRow == 0 && count > 0) {
                    say("统计: " + count + " 次变换  平均 |d| = " + fmt(sumDx / count) + "," + fmt(sumDy / count));
                }
            } catch (InterruptedException ie) {
                return;
            } catch (Throwable t) {
                /* 控制文件读失败就当没开 */
            }
        }
    }

    static void countMode() {
        count = 0; sumDx = 0; sumDy = 0; countRow = 500;
        say(">>> 统计模式：每 500 次变换打一行平均位移");
    }

    static String fmt(float f) {
        return String.format(java.util.Locale.ROOT, "%.1f", f);
    }

    static String caller() {
        StackTraceElement[] st = new Throwable().getStackTrace();
        for (int i = 1; i < st.length; i++) {
            String cn = st[i].getClassName();
            if (cn.equals("CameraVec2") || cn.equals("CamProbe")) continue;
            String f = st[i].getFileName();
            return cn + "." + st[i].getMethodName() + "(" + (f == null ? "?" : f) + ":" + st[i].getLineNumber() + ")";
        }
        return "?";
    }

    static void trace(String method) {
        if (!ready) return;
        float cx = CAM.x, cy = CAM.y;
        if (countRow > 0) {
            count++;
            sumDx += Math.abs(cx - lastCx);
            sumDy += Math.abs(cy - lastCy);
        }
        Object pl = null, un = null;
        boolean dead = false;
        try { pl = Class.forName("mindustry.Vars").getField("player").get(null); } catch (Throwable ignored) { }
        try {
            if (pl != null) {
                dead = (Boolean) pl.getClass().getMethod("dead").invoke(pl);
                un = pl.getClass().getMethod("unit").invoke(pl);
            }
        } catch (Throwable ignored) { }

        long ms = System.currentTimeMillis() - t0;
        boolean unitChanged = (un != lastUnit);
        // 单位变化永远记（这是要找的关键事件），其余只在抓取模式下记
        if (!capture && !unitChanged) {
            lastCx = cx; lastCy = cy;
            return;
        }

        String call = caller();
        String key = call + "|" + method;

        if (unitChanged) {
            out.printf("[%7d ms] *** 单位变化 %s -> %s (dead=%s) 相机 %.0f,%.0f%n", ms,
                    lastUnit == null ? "null" : String.valueOf(System.identityHashCode(lastUnit)),
                    un == null ? "null" : String.valueOf(System.identityHashCode(un)),
                    dead, cx, cy);
            out.printf("              改相机的是: %s (%s)%n", call, method);
            lastUnit = un;
        }
        if (!key.equals(lastKey)) {
            if (repeat > 0) out.println("              ^ 上一处重复 " + repeat + " 次");
            repeat = 0;
            lastKey = key;
            out.printf("[%7d ms] %-10s  相机 %.0f,%.0f -> %.0f,%.0f   调用点 %s%n",
                    ms, method, lastCx, lastCy, cx, cy, call);
            lastFlush = ms;
        } else {
            repeat++;
            if (ms - lastFlush > 2000) {
                lastFlush = ms;
                out.printf("[%7d ms] (同一处继续: %-9s x%-4d 相机 %.0f,%.0f)%n", ms, method, repeat, cx, cy);
            }
        }
        lastCx = cx; lastCy = cy;
    }
}
