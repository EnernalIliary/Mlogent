import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.jar.JarFile;

/**
 * CamAgent —— 运行时探针：把 arc.math.geom.Vec2 换成追踪版 CameraVec2。
 *
 * 原理（无第三方依赖，直接改常量池）：
 *   1) CameraVec2 编译出来是  "public class CameraVec2 extends arc.math.geom.Vec2"
 *   2) 解析它的常量池，把 Utf8 常量里的 "CameraVec2" 改成 "arc/math/geom/Vec2"、
 *      把 "arc/math/geom/Vec2" 改成 "CameraVec2"（包含 super.xxx() 的 owner 与字段/方法描述符），
 *      并按新长度重建常量池，同步交换 this_class / super_class 索引。
 *      结果类变成 "public class arc.math.geom.Vec2 extends CameraVec2"
 *      —— 名字顶替了原类，父类反而是真正原始的 Vec2，super 调用自然落到原始实现。
 *   3) transform() 拦截 arc/math/geom/Vec2 的加载并返回这份字节。
 *
 * 关键坑（踩过）：
 *   -javaagent 的 jar 会被追加进 **系统类路径**，所以追踪类 CameraVec2 **不能放进 agent jar**：
 *   否则 Class.forName("CameraVec2") 会取到未改名的原始 CameraVec2.class 并把它定义成 CameraVec2，
 *   shim 的父类链接解析到那个错误的类，加载 shim 时报
 *   "NoClassDefFoundError: arc/math/geom/Vec2 (wrong name: CameraVec2)"。
 *   正确做法：追踪类单独打成 cam-trace.jar，运行时用 appendToSystemClassLoaderSearch 注册。
 *
 * 用法: java -javaagent:CamAgent.jar -cp desktop.jar mindustry.desktop.DesktopLauncher
 */
public class CamAgent {

    static final String NAME_NEW = "CameraVec2";           // 追踪类原名（改完后成为父类名）
    static final String NAME_OLD = "arc/math/geom/Vec2";   // 要顶替的目标类名

    /** 由 CameraVec2 改名而来、真正顶替 arc/math/geom/Vec2 的字节 */
    static byte[] shim;

    /** renameClass 顺带留下的槽位表，仅供 dumpIdentity 自检使用 */
    static java.util.ArrayList<int[]> lastMeta;
    static java.util.ArrayList<byte[]> lastData;
    static int lastCpCount;

    public static void premain(String args, Instrumentation inst) throws Exception {
        // 追踪类放在 agent jar 外面（见类注释的坑），这里显式注册给系统加载器
        File here = agentDir();
        File trace = resolveTraceJar(here);
        if (trace == null) throw new IllegalStateException("找不到 cam-trace.jar（应在 " + here + " 旁边）");
        inst.appendToSystemClassLoaderSearch(new JarFile(trace));
        System.err.println("[CamAgent] 追踪类 jar: " + trace);

        // 注意：这里不能再断言 getResource("CameraVec2.class") == null ——
        // appendToSystemClassLoaderSearch 刚把 cam-trace.jar 挂进系统加载器，
        // 此时这个资源本来就该能取到（取到的是追踪类本尊，正是我们要的）。
        try {
            Files.write(new File(here, "agent-diag.txt").toPath(),
                    ("LEAKURL=" + CamAgent.class.getClassLoader().getResource("CameraVec2.class")
                            + "\r\nCLASSLOADER=" + CamAgent.class.getClassLoader()
                            + "\r\nCODE=" + CamAgent.class.getProtectionDomain().getCodeSource().getLocation()
                            + "\r\nTRACEJAR=" + trace + "\r\n").getBytes(StandardCharsets.UTF_8));
        } catch (Throwable ignored) { }

        // 只读资源，不触发类加载 —— 这是关键：CameraVec2 extends arc.math.geom.Vec2，
        // 一旦 Class.forName(NAME_NEW) 先跑，父类 Vec2 就会从 desktop.jar 被解析进来并永久
        // 缓存在系统加载器里（此时 transform 还没装上），之后夹具拿到的永远是原版 Vec2
        // （症状：父类 = java.lang.Object、identity 相同 = false）。踩过这个坑。
        byte[] raw = readResource(NAME_NEW + ".class");
        shim = renameClass(raw);
        try {
            Files.write(new File(here, "cam-shim.class").toPath(), shim);
        } catch (Throwable ignored) { }
        diag("SHIM raw=" + raw.length + " -> shim=" + shim.length);
        dumpIdentity(shim, lastMeta, lastData, lastCpCount);
        System.err.println("[CamAgent] shim 生成: " + raw.length + " -> " + shim.length + " 字节");

        final byte[] myShim = shim;
        inst.addTransformer(new ClassFileTransformer() {
            @Override
            public byte[] transform(ClassLoader loader, String name, Class<?> beingRedefined,
                                    ProtectionDomain pd, byte[] buf) {
                if (NAME_OLD.equals(name)) {
                    System.err.println("[CamAgent] 替换 " + name + " (" + buf.length + " -> " + myShim.length + " 字节)");
                    return myShim;
                }
                return null;
            }
        }, true);

        // 现在才加载追踪类本尊：它 extends arc.math.geom.Vec2，会把 Vec2 拉起来，
        // 但 transform 已经装上，所以这次拿到的是 shim（shim 的父类链接正好指向它自己）。
        Class<?> par = Class.forName(NAME_NEW);
        if (!NAME_NEW.equals(par.getName())) {
            throw new IllegalStateException("追踪类身份不对: " + par.getName());
        }
        diag("PARENT=" + par.getName() + " super=" + (par.getSuperclass() == null ? "(null)" : par.getSuperclass().getName()));
        System.err.println("[CamAgent] 已安装");
        startArmThread();
    }

    /** agent jar 所在目录；-javaagent 里给的就是绝对路径 */
    static File agentDir() {
        try {
            String p = CamAgent.class.getProtectionDomain().getCodeSource().getLocation().getPath();
            p = java.net.URLDecoder.decode(p, "UTF-8");
            File f = new File(p);
            return f.isFile() ? f.getParentFile() : f;
        } catch (Throwable t) {
            return new File(".").getAbsoluteFile();
        }
    }

    static File resolveTraceJar(File dir) {
        File f = new File(dir, "cam-trace.jar");
        return f.isFile() ? f : null;
    }

    /** 等 arc.Core.camera 就绪后再 arm()；期间 Core 可能正在初始化，所以要退避重试 */
    static void startArmThread() {
        Thread th = new Thread(new Runnable() {
            @Override
            public void run() {
                for (int i = 0; i < 1200; i++) {
                    try {
                        Thread.sleep(500);
                        Object cam = Class.forName("arc.Core").getField("camera").get(null);
                        if (cam != null) {
                            Thread.sleep(2000);          // 让类初始化彻底结束再反射
                            CamProbe.arm();
                            if (CamProbe.armed && CamProbe.camIdentity() != 0) {
                                System.err.println("[CamAgent] 探针已就位 identity=" + CamProbe.camIdentity());
                                return;
                            }
                        }
                    } catch (Throwable ignored) {
                        /* 还没就绪，继续等 */
                    }
                }
                System.err.println("[CamAgent] arm 超时");
            }
        }, "CamAgent-arm");
        th.setDaemon(true);
        th.start();
    }

    static byte[] readResource(String n) throws Exception {
        try (InputStream in = CamAgent.class.getClassLoader().getResourceAsStream(n)) {
            if (in == null) throw new IllegalStateException("找不到 " + n);
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            byte[] b = new byte[8192];
            int k;
            while ((k = in.read(b)) > 0) bo.write(b, 0, k);
            return bo.toByteArray();
        }
    }

    static int u1(byte[] b, int o) { return b[o] & 0xFF; }

    static int u2(byte[] b, int o) { return ((b[o] & 0xFF) << 8) | (b[o + 1] & 0xFF); }

    /**
     * 把 CameraVec2.class 改写成顶替 arc/math/geom/Vec2 的 shim。
     * 做法：完整解析常量池 → 逐个 Utf8 互换两个类名（按新长度重建）→
     * 拼回字段/方法/属性区 → 交换 this_class / super_class 索引。
     */
    static byte[] renameClass(byte[] src) {
        int cpCount = u2(src, 8);
        int p = 10;
        java.util.ArrayList<int[]> meta = new java.util.ArrayList<int[]>();   // {tag, oldOff, oldSize}
        java.util.ArrayList<byte[]> data = new java.util.ArrayList<byte[]>(); // 改写后的 Utf8 内容，或 null
        for (int i = 1; i < cpCount; i++) {
            int tag = u1(src, p);
            int size;
            switch (tag) {
                case 1: {
                    int len = u2(src, p + 1), d = p + 3;
                    String s = new String(src, d, len, StandardCharsets.UTF_8);
                    String t = swapNames(s);
                    byte[] nw = t.equals(s) ? null : t.getBytes(StandardCharsets.UTF_8);
                    if (nw != null) {
                        System.err.println("[CamAgent]   #" + i + " " + s + " -> " + t);
                        diag("EDIT #" + i + " len " + len + " -> " + nw.length + "  [" + s + "]");
                    }
                    meta.add(new int[]{tag, p, 3 + len, i});
                    data.add(nw);
                    // 必须 continue：break 只跳出 switch，会落到下面的公共尾部再 add 一次，
                    // 导致每个 Utf8 槽位被记两次、常量池被算大（踩过：970 -> 1616，shim 2249 -> 2895）
                    p += 3 + len;
                    continue;
                }
                case 7: case 8: case 16: case 19: case 20: size = 3; break;
                case 15: size = 4; break;
                case 3: case 4: case 9: case 10: case 11: case 12: case 17: case 18: size = 5; break;
                case 5: case 6:
                    meta.add(new int[]{tag, p, 9, i});
                    data.add(null);
                    meta.add(new int[]{-1, p + 5, 0, i});   // long/double 的第二格占位
                    data.add(null);
                    p += 9;
                    i++;
                    continue;
                default: throw new IllegalStateException("未知常量池 tag=" + tag + " @ " + p);
            }
            meta.add(new int[]{tag, p, size, i});
            data.add(null);
            p += size;
        }
        int tailStart = p;
        int cpSize = 0;
        for (int k = 0; k < meta.size(); k++) {
            int[] m = meta.get(k);
            if (m[0] == -1) continue;
            cpSize += (m[0] == 1 && data.get(k) != null) ? 3 + data.get(k).length : m[2];
        }
        int tailLen = src.length - tailStart;
        byte[] out = new byte[10 + cpSize + tailLen];
        System.arraycopy(src, 0, out, 0, 10);
        int w = 10;
        java.util.ArrayList<Integer> clsOffInOut = new java.util.ArrayList<Integer>();
        for (int k = 0; k < meta.size(); k++) {
            int[] m = meta.get(k);
            if (m[0] == -1) {                       // long/double 的第二格，补零占位
                out[w++] = 0; out[w++] = 0;
                continue;
            }
            if (m[0] == 7) clsOffInOut.add(w);
            byte[] repl = m[0] == 1 ? data.get(k) : null;
            if (repl == null) {
                System.arraycopy(src, m[1], out, w, m[2]);
                w += m[2];
            } else {
                out[w] = 1;
                out[w + 1] = (byte) (repl.length >> 8);
                out[w + 2] = (byte) repl.length;
                System.arraycopy(repl, 0, out, w + 3, repl.length);
                w += 3 + repl.length;
            }
        }
        System.arraycopy(src, tailStart, out, w, tailLen);
        // 两个类名互换了 Utf8：Class#2 原本指向 "arc/math/geom/Vec2" 的 Utf8，现在那里
        // 写的是 "CameraVec2"，所以每个 Class 条目的 name_index 必须一起换，否则
        // Class#2 会被解析成 CameraVec2、Class#71 解析成 Vec2，shim 的 this/super 就反了
        // （踩过：JVM 报 "NoClassDefFoundError: arc/math/geom/Vec2 (wrong name: CameraVec2)"）。
        int thisClass = u2(src, tailStart + 2), superClass = u2(src, tailStart + 4);
        for (int i = 0; i < clsOffInOut.size(); i++) {
            int co = clsOffInOut.get(i);
            int ni = u2(out, co + 1);
            if (ni == superClass) { out[co + 1] = (byte) (thisClass >> 8); out[co + 2] = (byte) thisClass; }
            else if (ni == thisClass) { out[co + 1] = (byte) (superClass >> 8); out[co + 2] = (byte) superClass; }
        }
        System.err.println("[CamAgent] 常量池 " + cpCount + " 条: " + (tailStart - 10) + " -> " + (w - 10)
                + " 字节; this #" + thisClass + " / super #" + superClass + " ; Class 条目重指向 " + clsOffInOut.size() + " 个");
        diag("RENAME cpCount=" + cpCount + " cpSize=" + (tailStart - 10) + "->" + (w - 10)
                + " this=#" + thisClass + " super=#" + superClass + " clsEntries=" + clsOffInOut.size());
        lastMeta = meta;
        lastData = data;
        lastCpCount = cpCount;
        return out;
    }

    /**
     * 自检：把已生成字节的 this/super 解析回字符串，写进 agent-diag.txt（UTF-8，避免控制台乱码）。
     * 注意：这里的槽位表必须用 renameClass 已经建好的那份 —— 重新解析 shim 会因
     * long/double 占两格而错位（踩过：IndexOutOfBoundsException: Index 1378 out of bounds for length 90）。
     */
    static void dumpIdentity(byte[] b, java.util.ArrayList<int[]> meta, java.util.ArrayList<byte[]> data, int cpCount) {
        try {
            // off 必须是 **out 里** 的偏移：renameClass 重建常量池后偏移全变了，
            // 旧实现拿 meta 的 src 偏移去 b 上解析，所以读出 "Index 21600" 这种鬼值。
            java.util.ArrayList<Integer> tag = new java.util.ArrayList<Integer>();
            java.util.ArrayList<Integer> off = new java.util.ArrayList<Integer>();
            int w = 10;
            for (int k = 0; k < meta.size(); k++) {
                int[] m = meta.get(k);
                if (m[0] == -1) { w += 2; tag.add(-1); off.add(w - 2); continue; }
                tag.add(m[0]);
                off.add(w);
                w += (m[0] == 1 && data.get(k) != null) ? 3 + data.get(k).length : m[2];
            }
            int thisI = u2(b, w + 2), superI = u2(b, w + 4);
            diag("SELFCHECK cpCount=" + cpCount + " cpSize=" + (w - 10)
                    + " thisI=" + thisI + " -> " + clsName(b, tag, off, thisI)
                    + " superI=" + superI + " -> " + clsName(b, tag, off, superI)
                    + " shimLen=" + b.length);
        } catch (Throwable e) {
            diag("SELFCHECK 失败: " + e);
        }
    }

    /** 追加一行诊断到 agent-diag.txt（UTF-8） */
    static void diag(String line) {
        try {
            Files.write(new File(agentDir(), "agent-diag.txt").toPath(),
                    (line + "\r\n").getBytes(StandardCharsets.UTF_8),
                    java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch (Throwable ignored) { }
    }

    static String clsName(byte[] b, java.util.ArrayList<Integer> tag, java.util.ArrayList<Integer> off, int clsIdx) {
        if (clsIdx <= 0) return "(none)";
        if (tag.get(clsIdx - 1) != 7) return "(不是 Class 条目, tag=" + tag.get(clsIdx - 1) + ")";
        int nameIdx = u2(b, off.get(clsIdx - 1) + 1);
        if (tag.get(nameIdx - 1) != 1) return "(名字不是 Utf8, tag=" + tag.get(nameIdx - 1) + ")";
        int no = off.get(nameIdx - 1), len = u2(b, no + 1);
        return new String(b, no + 3, len, StandardCharsets.UTF_8);
    }

    /** 先换长的（arc/math/geom/Vec2），再换短的（CameraVec2），避免交叉污染 */
    static String swapNames(String s) {
        if (s.indexOf(NAME_OLD) < 0 && s.indexOf(NAME_NEW) < 0) return s;
        String t = s.replace(NAME_OLD, "\u0001");
        t = t.replace(NAME_NEW, NAME_OLD);
        return t.replace("\u0001", NAME_NEW);
    }
}
