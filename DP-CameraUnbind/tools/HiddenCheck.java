import arc.files.*;
import arc.struct.*;
import arc.util.serialization.*;
import arc.util.serialization.Jval.*;
import mindustry.mod.Mods.*;

/**
 * 免装机制验证：用游戏**真实的**元文件解析 + 真实的过滤逻辑，
 * 检查把 mod 标成 hidden 之后，客户端还会不会把它上报给服务器。
 *
 * 上报点只有一处：NetClient.java:108  `c.mods = mods.getModStrings();`
 * 而 getModStrings() 的定义是（Mods.java:940）:
 *     mods.select(l -> !l.meta.hidden && l.enabled()).map(l -> l.name + ":" + l.meta.version)
 */
public class HiddenCheck{
    public static void main(String[] args) throws Exception{
        // 1) 用游戏自己的解析器读 meta（与 Mods.findMeta 完全一致的方式）
        String json = new Fi("F:/OneDrive/桌面/AtomicStates/DP-CameraUnbind/mod.hjson").readString();
        Jval jval = Jval.read(json);
        ModMeta meta = new Json().fromJson(ModMeta.class, jval.toString(Jformat.plain));
        meta.cleanup();

        System.out.println("解析结果：");
        System.out.println("  name        = " + meta.name);
        System.out.println("  internalName= " + meta.internalName);
        System.out.println("  version     = " + meta.version);
        System.out.println("  main        = " + meta.main);
        System.out.println("  hidden      = " + meta.hidden);

        // 2) 复刻 getModStrings() 的过滤，对比 hidden 开关的影响
        System.out.println();
        System.out.println("上报给服务器的字符串（getModStrings）：");
        System.out.println("  hidden=false → \"" + meta.name + ":" + meta.version + "\"   → 服务器会要求客户端也有它");
        if(meta.hidden){
            System.out.println("  hidden=true  → 不上报                        → 原版客户端可直接进服");
        }else{
            System.out.println("  hidden=true  → 不上报                        → 原版客户端可直接进服（当前不是）");
        }

        if(args.length > 0 && args[0].equals("--apply")){
            System.out.println();
            System.out.println("（--apply 模式：下面是应写入的 mod.hjson 内容）");
            String out = json.replaceAll("(?m)^", "").trim();
            if(out.contains("hidden:")){
                out = out.replaceAll("hidden:\\s*\\w+", "hidden: true");
            }else{
                out = out + "\nhidden: true\n";
            }
            System.out.println(out);
        }
    }
}
