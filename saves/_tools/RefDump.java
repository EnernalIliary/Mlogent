import java.lang.reflect.*;
import java.util.*;

/** 把脚本覆写里用到的成员逐个核对：是字段还是方法、什么类型。 */
public class RefDump{
    public static void main(String[] args) throws Exception{
        check("mindustry.gen.Unit",
            "type", "speed", "vel", "lookAt", "prefRotation", "movePref", "aim", "controlWeapons",
            "aimX", "aimY", "x", "y", "isFlying", "shooting", "isBuilding");
        check("mindustry.gen.Player",
            "shooting", "boosting", "mouseX", "mouseY", "x", "y", "dead", "unit", "team", "within");
        check("mindustry.input.InputHandler",
            "movement", "lastPayloadKeyTapMillis", "lastPayloadKeyHoldMillis",
            "tryPickupPayload", "tryDropPayload", "spectating", "locked");
        check("mindustry.type.UnitType", "omniMovement", "accel", "hasWeapons", "faceTarget", "rotateSpeed");
        check("arc.Input", "axis", "keyDown", "keyTap", "mouseWorld");
        check("mindustry.input.Binding",
            "moveX", "moveY", "mouseMove", "boost", "pickupCargo", "dropCargo");
    }

    static void check(String cls, String... names){
        try{
            Class<?> c = Class.forName(cls);
            System.out.println("=== " + cls + " ===");
            for(String n : names){
                boolean found = false;
                try{
                    Field f = c.getField(n);
                    System.out.println("  字段  " + n + " : " + simple(f.getType()) + "   [用 unit." + n + " 取值]");
                    found = true;
                }catch(NoSuchFieldException ignored){}
                if(!found){
                    for(Method m : c.getMethods()){
                        if(m.getName().equals(n)){
                            StringBuilder ps = new StringBuilder();
                            for(Class<?> p : m.getParameterTypes()){
                                if(ps.length() > 0) ps.append(", ");
                                ps.append(simple(p));
                            }
                            System.out.println("  方法  " + n + "(" + ps + ") : " + simple(m.getReturnType()) + "   [用 unit." + n + "(...)]");
                            found = true;
                        }
                    }
                }
                if(!found) System.out.println("  !!!! 找不到 " + n);
            }
        }catch(ClassNotFoundException e){
            System.out.println("=== " + cls + " : 类不存在 ===");
        }
    }

    static String simple(Class<?> c){
        if(c.isArray()) return simple(c.getComponentType()) + "[]";
        return c.getName();
    }
}
