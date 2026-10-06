import arc.files.*;
import arc.util.serialization.*;
import arc.util.serialization.Jval.*;
import mindustry.mod.Mods.*;
import java.io.*;
import java.util.*;
import java.util.zip.ZipFile;

/**
 * 扫描一个 mods 目录，报告每个 mod 的 meta —— 重点是有没有 hidden。
 *
 * 原理（对应 NetServer.java:210-224 的 join 校验）：
 *   客户端 join 时上报 `getModStrings()`（NetClient.java:108），它只包含
 *   `!meta.hidden && enabled()` 的 mod。凡是**没标 hidden** 的启用 mod，
 *   都会被服务端视为"多余 mod"（extraMods）而踢你下线。
 */
public class ModsScan{
    public static void main(String[] args) throws Exception{
        String dir = args.length > 0 ? args[0]
            : "E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods";
        File[] files = new File(dir).listFiles();
        if(files == null){ System.out.println("目录不存在: " + dir); return; }
        Arrays.sort(files, Comparator.comparing(File::getName));

        Json json = new Json();
        int blocked = 0, hiddenCnt = 0, checked = 0;

        System.out.println("扫描: " + dir);
        System.out.println();
        System.out.printf("%-46s %-16s %-9s %s%n", "文件", "内部名", "hidden", "join 影响");
        System.out.println("-".repeat(96));

        for(File f : files){
            if(f.isDirectory() || !f.getName().toLowerCase().endsWith(".zip")) continue;
            try(ZipFile zf = new ZipFile(f)){
                String metaName = null;
                for(String cand : new String[]{"mod.json", "mod.hjson", "plugin.json", "plugin.hjson"}){
                    if(zf.getEntry(cand) != null){ metaName = cand; break; }
                }
                if(metaName == null){
                    System.out.printf("%-46s %-16s %-9s %s%n", cut(f.getName(), 44), "(无 meta)", "-", "跳过");
                    continue;
                }
                String text = new String(zf.getInputStream(zf.getEntry(metaName)).readAllBytes());
                ModMeta meta = json.fromJson(ModMeta.class, Jval.read(text).toString(Jformat.plain));
                meta.cleanup();
                checked++;
                boolean hid = meta.hidden;
                if(hid) hiddenCnt++; else blocked++;
                System.out.printf("%-46s %-16s %-9s %s%n",
                    cut(f.getName(), 44),
                    cut(meta.name == null ? "?" : meta.name, 14),
                    hid ? "true" : "false",
                    hid ? "不影响（不上报）" : "会被当成多余 mod → 可能被踢");
            }catch(Exception e){
                System.out.printf("%-46s %-16s %-9s %s%n", cut(f.getName(), 44), "(读取失败)", "-", e.getClass().getSimpleName());
            }
        }

        System.out.println();
        System.out.println("共检查 " + checked + " 个 zip：hidden " + hiddenCnt + " 个，"
            + "非 hidden " + blocked + " 个");
        System.out.println(blocked > 0
            ? "→ 上面标了「可能被踢」的那些 mod，会让原版服务器认为你装了服务端没有的 mod。\n"
              + "  只改自己手的模组应当加 `hidden: true`（见 MindustryX 的做法）。"
            : "→ 全部 hidden，不会因为 mod 清单被踢。");
    }

    static String cut(String s, int n){ return s.length() <= n ? s : s.substring(0, n - 1) + "…"; }
}
