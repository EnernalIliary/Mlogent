import java.io.*;

/** 用 JDK 自带 javap 工具，反汇编 desktop.jar 里的类（-c 出字节码，-p 出私有成员） */
public class JavapRun{
    public static void main(String[] args) throws Exception{
        String cp = args[0];
        String cls = args[1];
        boolean bytecode = args.length > 2 && args[2].equals("-c");

        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        PrintStream old = System.out;
        PrintStream cap = new PrintStream(buf, true, "UTF-8");
        System.setOut(cap);
        int rc;
        try{
            rc = com.sun.tools.javap.Main.run(
                bytecode ? new String[]{"-p", "-c", "-cp", cp, cls}
                         : new String[]{"-p", "-constants", "-cp", cp, cls},
                cap);
        }finally{
            System.setOut(old);
        }
        cap.flush();
        old.print(buf.toString("UTF-8"));
        old.println("[javap exit=" + rc + "]");
    }
}
