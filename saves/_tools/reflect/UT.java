public class UT {
  public static void main(String[] a) throws Exception {
    Class<?> c = Class.forName("mindustry.type.UnitType");
    for(String n : new String[]{"hasWeapons","faceTarget","omniMovement","accel","speed","type"}){
      try { System.out.println("UnitType." + n + " -> " + c.getField(n)); }
      catch(Exception e1){
        try { System.out.println("UnitType." + n + " -> " + c.getMethod(n)); }
        catch(Exception e2){ System.out.println("UnitType." + n + " -> NOT FOUND"); }
      }
    }
    Class<?> u = Class.forName("mindustry.gen.Unit");
    for(String n : new String[]{"type","vel","speed","aimX"}){
      try { System.out.println("Unit." + n + " -> " + u.getField(n)); }
      catch(Exception e1){
        try { System.out.println("Unit." + n + " -> " + u.getMethod(n)); }
        catch(Exception e2){ System.out.println("Unit." + n + " -> NOT FOUND"); }
      }
    }
  }
}