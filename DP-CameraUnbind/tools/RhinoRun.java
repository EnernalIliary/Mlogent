import rhino.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

/** 尽量贴近游戏的真实脚本环境：ImporterTopLevel + 游戏自带 scripts/global.js */
public class RhinoRun{
    public static void main(String[] args) throws Exception{
        String scriptFile = args[0];
        String globalJs = args.length > 1 ? args[1] : null;
        String script = new String(Files.readAllBytes(Paths.get(scriptFile)), StandardCharsets.UTF_8);

        Context cx = Context.enter();
        try{
            cx.setLanguageVersion(Context.VERSION_ES6);
            cx.setOptimizationLevel(-1);
            Scriptable scope = new ImporterTopLevel(cx);

            ScriptableObject.putProperty(scope, "print", new BaseFunction(){
                @Override public Object call(Context c, Scriptable s, Scriptable t, Object[] a){
                    System.out.println(a.length > 0 ? String.valueOf(a[0]) : "");
                    return Undefined.instance;
                }
            });
            ScriptableObject.putProperty(scope, "quit", new BaseFunction(){
                @Override public Object call(Context c, Scriptable s, Scriptable t, Object[] a){
                    System.exit(a.length > 0 ? ((Number)a[0]).intValue() : 0);
                    return Undefined.instance;
                }
            });

            if(globalJs != null){
                String g = new String(Files.readAllBytes(Paths.get(globalJs)), StandardCharsets.UTF_8);
                cx.evaluateString(scope, g, "global.js", 1);
                System.out.println("[已加载 global.js]");
            }

            Object result = cx.evaluateString(scope, "(function(){'use strict';\n" + script + "\n})();",
                scriptFile, 1);
            System.out.println("[脚本返回值] " + Context.toString(result));
        }catch(Throwable e){
            System.out.println("[异常] " + e);
            e.printStackTrace(System.out);
        }finally{
            Context.exit();
        }
    }
}
