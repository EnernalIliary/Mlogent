import arc.files.*;
import arc.struct.*;
import java.io.File;

/** 用 arc 自己的 ZipFi 验证：游戏能不能在压缩包里找到 scripts/main.js */
public class ZipProbe{
    public static void main(String[] args){
        for(String path : args){
            System.out.println("=== " + path + " ===");
            Fi zip = new Fi(new File(path));
            System.out.println("  zip.exists() = " + zip.exists());
            ZipFi root = new ZipFi(zip);
            System.out.println("  root.path()  = [" + root.path() + "]");
            System.out.println("  root.name()  = [" + root.name() + "]");

            Fi scripts = root.child("scripts");
            System.out.println("  root.child(\"scripts\")        .exists() = " + scripts.exists());

            Fi all = root.child("scripts");
            Seq<Fi> js = all.findAll(f -> f.extEquals("js"));
            System.out.println("  scripts.findAll(js).size   = " + js.size);
            for(Fi f : js) System.out.println("      -> [" + f.path() + "]  name=[" + f.name() + "]  extEquals(js)=" + f.extEquals("js"));

            Fi main = root.child("scripts").child("main.js");
            System.out.println("  root/scripts/main.js .exists() = " + main.exists() + "  isDirectory=" + main.isDirectory());

            Fi main2 = root.child("scripts").child("main.js");
            System.out.println("  main.name() = [" + main2.name() + "]");

            // 顺带看看 list() 里到底是什么
            System.out.println("  root.list() = ");
            for(Fi f : root.list()) System.out.println("      [" + f.path() + "]");

            // 对照：已经跑通的模组压缩包
            Fi folder = root.child("bundles");
            System.out.println("  root.child(\"bundles\").exists() = " + folder.exists());
        }
    }
}
