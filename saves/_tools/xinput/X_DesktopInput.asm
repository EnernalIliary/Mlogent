javap.exe : ����: �ļ� F:\OneDrive\����\AtomicStates\saves\_tools\xinput\X_DesktopInput.class �������� X_DesktopInput
所在位置 行:4 字符: 1
+ & $javap -p -c -cp "$t;$jar" 'X_DesktopInput' 2>&1 | Out-File (Join-P ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (����: �ļ� F:\On... X_DesktopInput:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
Compiled from "DesktopInput.java"
public class mindustry.input.DesktopInput extends mindustry.input.InputHandler {
  public arc.math.geom.Vec2 movement;

  public arc.Graphics$Cursor cursorType;

  public int selectX;

  public int selectY;

  public int schemX;

  public int schemY;

  public int lastLineX;

  public int lastLineY;

  public int schematicX;

  public int schematicY;

  public mindustry.input.PlaceMode mode;

  public float selectScale;

  public mindustry.entities.units.BuildPlan splan;

  public boolean deleting;

  public boolean shouldShoot;

  public boolean panning;

  public boolean movedPlan;

  public float panScale;

  public float panSpeed;

  public float panBoostSpeed;

  public long selectMillis;

  public mindustry.world.Tile prevSelected;

  public int lastCtrlGroup;

  public long lastCtrlGroupSelectMillis;

  public long lastPayloadKeyTapMillis;

  public long lastPayloadKeyHoldMillis;

  private float buildPlanMouseOffsetX;

  private float buildPlanMouseOffsetY;

  private boolean changedCursor;

  private boolean pressedCommandRect;

  public mindustry.gen.Teamc target;

  public mindustry.input.DesktopInput();
    Code:
       0: aload_0
       1: invokespecial #3                  // Method mindustry/input/InputHandler."<init>":()V
       4: aload_0
       5: new           #9                  // class arc/math/geom/Vec2
       8: dup
       9: invokespecial #11                 // Method arc/math/geom/Vec2."<init>":()V
      12: putfield      #12                 // Field movement:Larc/math/geom/Vec2;
      15: aload_0
      16: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
      19: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
      22: aload_0
      23: iconst_m1
      24: putfield      #28                 // Field selectX:I
      27: aload_0
      28: iconst_m1
      29: putfield      #32                 // Field selectY:I
      32: aload_0
      33: iconst_m1
      34: putfield      #35                 // Field schemX:I
      37: aload_0
      38: iconst_m1
      39: putfield      #38                 // Field schemY:I
      42: aload_0
      43: iconst_0
      44: putfield      #41                 // Field deleting:Z
      47: aload_0
      48: iconst_0
      49: putfield      #45                 // Field shouldShoot:Z
      52: aload_0
      53: iconst_0
      54: putfield      #48                 // Field panning:Z
      57: aload_0
      58: iconst_0
      59: putfield      #51                 // Field movedPlan:Z
      62: aload_0
      63: ldc           #54                 // float 0.005f
      65: putfield      #55                 // Field panScale:F
      68: aload_0
      69: ldc           #59                 // float 4.5f
      71: putfield      #60                 // Field panSpeed:F
      74: aload_0
      75: ldc           #63                 // float 15.0f
      77: putfield      #64                 // Field panBoostSpeed:F
      80: aload_0
      81: lconst_0
      82: putfield      #67                 // Field selectMillis:J
      85: return

  boolean showHint();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #75                 // Field mindustry/core/UI.hudfrag:Lmindustry/ui/fragments/HudFragment;
       6: invokevirtual #81                 // Method mindustry/ui/fragments/HudFragment.shown:()Z
       9: ifeq          97
      12: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      15: ldc           #93                 // String hints
      17: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      20: ifeq          97
      23: aload_0
      24: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      27: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
      30: ifeq          97
      33: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      36: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
      39: ifne          97
      42: aload_0
      43: getfield      #119                // Field isBuilding:Z
      46: ifne          60
      49: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      52: ldc           #122                // String buildautopause
      54: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      57: ifeq          93
      60: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      63: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      66: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
      69: ifne          93
      72: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      75: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
      78: ifne          97
      81: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      84: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      87: invokevirtual #132                // Method mindustry/gen/Unit.spawnedByCore:()Z
      90: ifne          97
      93: iconst_1
      94: goto          98
      97: iconst_0
      98: ireturn

  public void reset();
    Code:
       0: aload_0
       1: invokespecial #135                // Method mindustry/input/InputHandler.reset:()V
       4: aload_0
       5: iconst_0
       6: putfield      #45                 // Field shouldShoot:Z
       9: aload_0
      10: iconst_0
      11: putfield      #41                 // Field deleting:Z
      14: return

  public void buildUI(arc.scene.Group);
    Code:
       0: aload_1
       1: aload_0
       2: invokedynamic #138,  0            // InvokeDynamic #0:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
       7: invokevirtual #142                // Method arc/scene/Group.fill:(Larc/func/Cons;)V
      10: aload_1
      11: aload_0
      12: invokedynamic #148,  0            // InvokeDynamic #1:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      17: invokevirtual #142                // Method arc/scene/Group.fill:(Larc/func/Cons;)V
      20: return

  public void drawTop();
    Code:
       0: aload_0
       1: getfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
       4: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
       7: if_acmpeq     33
      10: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
      13: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
      16: ifeq          33
      19: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
      22: aload_0
      23: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
      26: dup_x1
      27: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
      30: invokevirtual #162                // Method arc/Graphics.cursor:(Larc/Graphics$Cursor;)V
      33: fconst_1
      34: invokestatic  #168                // Method arc/graphics/g2d/Lines.stroke:(F)V
      37: aload_0
      38: getstatic     #174                // Field arc/Core.input:Larc/Input;
      41: invokevirtual #178                // Method arc/Input.mouseX:()I
      44: i2f
      45: invokevirtual #184                // Method tileX:(F)I
      48: istore_1
      49: aload_0
      50: getstatic     #174                // Field arc/Core.input:Larc/Input;
      53: invokevirtual #188                // Method arc/Input.mouseY:()I
      56: i2f
      57: invokevirtual #191                // Method tileY:(F)I
      60: istore_2
      61: aload_0
      62: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
      65: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
      68: if_acmpne     122
      71: aload_0
      72: aload_0
      73: getfield      #28                 // Field selectX:I
      76: aload_0
      77: getfield      #32                 // Field selectY:I
      80: iload_1
      81: iload_2
      82: getstatic     #174                // Field arc/Core.input:Larc/Input;
      85: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
      88: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
      91: ifeq          110
      94: aload_0
      95: getfield      #35                 // Field schemX:I
      98: iconst_m1
      99: if_icmpeq     110
     102: aload_0
     103: getfield      #38                 // Field schemY:I
     106: iconst_m1
     107: if_icmpne     115
     110: bipush        100
     112: goto          118
     115: getstatic     #213                // Field mindustry/Vars.maxSchematicSize:I
     118: iconst_0
     119: invokevirtual #216                // Method drawBreakSelection:(IIIIIZ)V
     122: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     125: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
     128: ifne          215
     131: aload_0
     132: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     135: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
     138: if_acmpeq     215
     141: getstatic     #174                // Field arc/Core.input:Larc/Input;
     144: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     147: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     150: ifeq          189
     153: aload_0
     154: getfield      #35                 // Field schemX:I
     157: iconst_m1
     158: if_icmpeq     189
     161: aload_0
     162: getfield      #38                 // Field schemY:I
     165: iconst_m1
     166: if_icmpeq     189
     169: aload_0
     170: aload_0
     171: getfield      #35                 // Field schemX:I
     174: aload_0
     175: getfield      #38                 // Field schemY:I
     178: iload_1
     179: iload_2
     180: getstatic     #213                // Field mindustry/Vars.maxSchematicSize:I
     183: invokevirtual #223                // Method drawSelection:(IIIII)V
     186: goto          215
     189: getstatic     #174                // Field arc/Core.input:Larc/Input;
     192: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     195: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     198: ifeq          215
     201: aload_0
     202: aload_0
     203: getfield      #35                 // Field schemX:I
     206: aload_0
     207: getfield      #38                 // Field schemY:I
     210: iload_1
     211: iload_2
     212: invokevirtual #230                // Method drawRebuildSelection:(IIII)V
     215: invokestatic  #234                // Method arc/graphics/g2d/Draw.reset:()V
     218: return

  public void drawBottom();
    Code:
       0: aload_0
       1: getstatic     #174                // Field arc/Core.input:Larc/Input;
       4: invokevirtual #178                // Method arc/Input.mouseX:()I
       7: i2f
       8: invokevirtual #184                // Method tileX:(F)I
      11: istore_1
      12: aload_0
      13: getstatic     #174                // Field arc/Core.input:Larc/Input;
      16: invokevirtual #188                // Method arc/Input.mouseY:()I
      19: i2f
      20: invokevirtual #191                // Method tileY:(F)I
      23: istore_2
      24: aload_0
      25: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      28: ifnull        215
      31: aload_0
      32: aload_0
      33: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      36: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
      39: aload_0
      40: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      43: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
      46: aload_0
      47: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      50: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      53: aload_0
      54: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      57: getfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
      60: aload_0
      61: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      64: invokevirtual #256                // Method validPlace:(IILmindustry/world/Block;ILmindustry/entities/units/BuildPlan;)Z
      67: istore_3
      68: aload_0
      69: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      72: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      75: getfield      #260                // Field mindustry/world/Block.rotate:Z
      78: ifeq          127
      81: aload_0
      82: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      85: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      88: getfield      #265                // Field mindustry/world/Block.drawArrow:Z
      91: ifeq          127
      94: aload_0
      95: aload_0
      96: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      99: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     102: aload_0
     103: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     106: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     109: aload_0
     110: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     113: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     116: aload_0
     117: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     120: getfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
     123: iload_3
     124: invokevirtual #268                // Method drawArrow:(Lmindustry/world/Block;IIIZ)V
     127: aload_0
     128: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     131: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     134: aload_0
     135: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     138: aload_0
     139: getfield      #271                // Field allPlans:Larc/util/Eachable;
     142: iload_3
     143: invokevirtual #275                // Method mindustry/world/Block.drawPlan:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;Z)V
     146: aload_0
     147: aload_0
     148: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     151: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     154: aload_0
     155: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     158: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     161: aload_0
     162: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     165: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     168: aload_0
     169: aload_0
     170: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     173: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     176: aload_0
     177: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     180: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     183: aload_0
     184: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     187: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     190: getfield      #279                // Field mindustry/world/Block.size:I
     193: aload_0
     194: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     197: invokevirtual #282                // Method getPlan:(IIILmindustry/entities/units/BuildPlan;)Lmindustry/entities/units/BuildPlan;
     200: ifnull        209
     203: getstatic     #286                // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     206: goto          212
     209: getstatic     #292                // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
     212: invokevirtual #295                // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
     215: aload_0
     216: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     219: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
     222: if_acmpne     279
     225: aload_0
     226: invokevirtual #302                // Method isPlacing:()Z
     229: ifne          279
     232: aload_0
     233: iload_1
     234: iload_2
     235: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
     238: astore_3
     239: aload_3
     240: ifnull        279
     243: aload_0
     244: aload_3
     245: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     248: aload_3
     249: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     252: aload_3
     253: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
     256: ifeq          269
     259: aload_3
     260: invokevirtual #310                // Method mindustry/entities/units/BuildPlan.tile:()Lmindustry/world/Tile;
     263: invokevirtual #314                // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
     266: goto          273
     269: aload_3
     270: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     273: getstatic     #292                // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
     276: invokevirtual #295                // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
     279: aload_0
     280: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     283: getfield      #319                // Field arc/struct/Seq.items:[Ljava/lang/Object;
     286: checkcast     #323                // class "[Lmindustry/entities/units/BuildPlan;"
     289: astore_3
     290: aload_0
     291: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     294: getfield      #325                // Field arc/struct/Seq.size:I
     297: istore        4
     299: iconst_0
     300: istore        5
     302: iload         5
     304: iload         4
     306: if_icmpge     333
     309: aload_3
     310: iload         5
     312: aaload
     313: astore        6
     315: aload         6
     317: fconst_1
     318: putfield      #326                // Field mindustry/entities/units/BuildPlan.animScale:F
     321: aload_0
     322: aload         6
     324: invokevirtual #329                // Method drawPlan:(Lmindustry/entities/units/BuildPlan;)V
     327: iinc          5, 1
     330: goto          302
     333: iconst_0
     334: istore        5
     336: iload         5
     338: iload         4
     340: if_icmpge     366
     343: aload_3
     344: iload         5
     346: aaload
     347: astore        6
     349: aload_0
     350: aload         6
     352: aload         6
     354: getfield      #332                // Field mindustry/entities/units/BuildPlan.cachedValid:Z
     357: invokevirtual #335                // Method drawOverPlan:(Lmindustry/entities/units/BuildPlan;Z)V
     360: iinc          5, 1
     363: goto          336
     366: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     369: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
     372: ifeq          748
     375: aload_0
     376: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     379: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
     382: if_acmpne     518
     385: aload_0
     386: getfield      #345                // Field block:Lmindustry/world/Block;
     389: ifnull        518
     392: iconst_0
     393: istore        5
     395: iload         5
     397: aload_0
     398: getfield      #346                // Field linePlans:Larc/struct/Seq;
     401: getfield      #325                // Field arc/struct/Seq.size:I
     404: if_icmpge     502
     407: aload_0
     408: getfield      #346                // Field linePlans:Larc/struct/Seq;
     411: iload         5
     413: invokevirtual #349                // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     416: checkcast     #242                // class mindustry/entities/units/BuildPlan
     419: astore        6
     421: iload         5
     423: aload_0
     424: getfield      #346                // Field linePlans:Larc/struct/Seq;
     427: getfield      #325                // Field arc/struct/Seq.size:I
     430: iconst_1
     431: isub
     432: if_icmpne     480
     435: aload         6
     437: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     440: getfield      #260                // Field mindustry/world/Block.rotate:Z
     443: ifeq          480
     446: aload         6
     448: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     451: getfield      #265                // Field mindustry/world/Block.drawArrow:Z
     454: ifeq          480
     457: aload_0
     458: aload_0
     459: getfield      #345                // Field block:Lmindustry/world/Block;
     462: aload         6
     464: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     467: aload         6
     469: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     472: aload         6
     474: getfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
     477: invokevirtual #352                // Method drawArrow:(Lmindustry/world/Block;III)V
     480: aload_0
     481: aload_0
     482: getfield      #346                // Field linePlans:Larc/struct/Seq;
     485: iload         5
     487: invokevirtual #349                // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     490: checkcast     #242                // class mindustry/entities/units/BuildPlan
     493: invokevirtual #329                // Method drawPlan:(Lmindustry/entities/units/BuildPlan;)V
     496: iinc          5, 1
     499: goto          395
     502: aload_0
     503: getfield      #346                // Field linePlans:Larc/struct/Seq;
     506: aload_0
     507: invokedynamic #355,  0            // InvokeDynamic #2:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
     512: invokevirtual #356                // Method arc/struct/Seq.each:(Larc/func/Cons;)V
     515: goto          748
     518: aload_0
     519: invokevirtual #302                // Method isPlacing:()Z
     522: ifeq          748
     525: aload_0
     526: getfield      #345                // Field block:Lmindustry/world/Block;
     529: ifnonnull     539
     532: aload_0
     533: getfield      #359                // Field rotation:I
     536: goto          550
     539: aload_0
     540: getfield      #345                // Field block:Lmindustry/world/Block;
     543: aload_0
     544: getfield      #359                // Field rotation:I
     547: invokevirtual #360                // Method mindustry/world/Block.planRotation:(I)I
     550: istore        5
     552: aload_0
     553: getfield      #345                // Field block:Lmindustry/world/Block;
     556: getfield      #260                // Field mindustry/world/Block.rotate:Z
     559: ifeq          584
     562: aload_0
     563: getfield      #345                // Field block:Lmindustry/world/Block;
     566: getfield      #265                // Field mindustry/world/Block.drawArrow:Z
     569: ifeq          584
     572: aload_0
     573: aload_0
     574: getfield      #345                // Field block:Lmindustry/world/Block;
     577: iload_1
     578: iload_2
     579: iload         5
     581: invokevirtual #352                // Method drawArrow:(Lmindustry/world/Block;III)V
     584: invokestatic  #364                // Method arc/graphics/g2d/Draw.color:()V
     587: aload_0
     588: iload_1
     589: iload_2
     590: aload_0
     591: getfield      #345                // Field block:Lmindustry/world/Block;
     594: iload         5
     596: invokevirtual #367                // Method validPlace:(IILmindustry/world/Block;I)Z
     599: istore        6
     601: aload_0
     602: iload_1
     603: iload_2
     604: aload_0
     605: getfield      #345                // Field block:Lmindustry/world/Block;
     608: iload         5
     610: invokevirtual #370                // Method drawPlan:(IILmindustry/world/Block;I)V
     613: aload_0
     614: getfield      #345                // Field block:Lmindustry/world/Block;
     617: iload_1
     618: iload_2
     619: iload         5
     621: iload         6
     623: invokevirtual #373                // Method mindustry/world/Block.drawPlace:(IIIZ)V
     626: aload_0
     627: getfield      #345                // Field block:Lmindustry/world/Block;
     630: getfield      #377                // Field mindustry/world/Block.saveConfig:Z
     633: ifeq          736
     636: iload         6
     638: ifne          647
     641: getstatic     #380                // Field mindustry/graphics/Pal.breakInvalid:Larc/graphics/Color;
     644: goto          650
     647: getstatic     #383                // Field arc/graphics/Color.white:Larc/graphics/Color;
     650: iload         6
     652: ifne          661
     655: ldc_w         #388                // float 0.4f
     658: goto          664
     661: ldc_w         #389                // float 0.24f
     664: getstatic     #390                // Field arc/util/Time.globalTime:F
     667: ldc_w         #395                // float 6.0f
     670: ldc_w         #396                // float 0.28f
     673: invokestatic  #397                // Method arc/math/Mathf.absin:(FFF)F
     676: fadd
     677: invokestatic  #403                // Method arc/graphics/g2d/Draw.mixcol:(Larc/graphics/Color;F)V
     680: aload_0
     681: getfield      #407                // Field bplan:Lmindustry/entities/units/BuildPlan;
     684: iload_1
     685: iload_2
     686: iload         5
     688: aload_0
     689: getfield      #345                // Field block:Lmindustry/world/Block;
     692: invokevirtual #410                // Method mindustry/entities/units/BuildPlan.set:(IIILmindustry/world/Block;)Lmindustry/entities/units/BuildPlan;
     695: pop
     696: aload_0
     697: getfield      #407                // Field bplan:Lmindustry/entities/units/BuildPlan;
     700: aload_0
     701: getfield      #345                // Field block:Lmindustry/world/Block;
     704: getfield      #414                // Field mindustry/world/Block.lastConfig:Ljava/lang/Object;
     707: putfield      #418                // Field mindustry/entities/units/BuildPlan.config:Ljava/lang/Object;
     710: aload_0
     711: getfield      #345                // Field block:Lmindustry/world/Block;
     714: aload_0
     715: getfield      #407                // Field bplan:Lmindustry/entities/units/BuildPlan;
     718: aload_0
     719: getfield      #271                // Field allPlans:Larc/util/Eachable;
     722: invokevirtual #421                // Method mindustry/world/Block.drawPlanConfig:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;)V
     725: aload_0
     726: getfield      #407                // Field bplan:Lmindustry/entities/units/BuildPlan;
     729: aconst_null
     730: putfield      #418                // Field mindustry/entities/units/BuildPlan.config:Ljava/lang/Object;
     733: invokestatic  #234                // Method arc/graphics/g2d/Draw.reset:()V
     736: aload_0
     737: aload_0
     738: getfield      #345                // Field block:Lmindustry/world/Block;
     741: iload_1
     742: iload_2
     743: iload         6
     745: invokevirtual #425                // Method drawOverlapCheck:(Lmindustry/world/Block;IIZ)V
     748: invokestatic  #234                // Method arc/graphics/g2d/Draw.reset:()V
     751: return

  public void update();
    Code:
       0: aload_0
       1: invokespecial #429                // Method mindustry/input/InputHandler.update:()V
       4: getstatic     #432                // Field mindustry/Vars.net:Lmindustry/net/Net;
       7: invokevirtual #436                // Method mindustry/net/Net.active:()Z
      10: ifeq          85
      13: getstatic     #174                // Field arc/Core.input:Larc/Input;
      16: getstatic     #441                // Field mindustry/input/Binding.playerList:Larc/input/KeyBind;
      19: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
      22: ifeq          85
      25: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
      28: invokevirtual #447                // Method arc/scene/Scene.getKeyboardFocus:()Larc/scene/Element;
      31: ifnull        76
      34: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
      37: invokevirtual #447                // Method arc/scene/Scene.getKeyboardFocus:()Larc/scene/Element;
      40: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
      43: getfield      #451                // Field mindustry/core/UI.listfrag:Lmindustry/ui/fragments/PlayerListFragment;
      46: getfield      #455                // Field mindustry/ui/fragments/PlayerListFragment.content:Larc/scene/ui/layout/Table;
      49: invokevirtual #461                // Method arc/scene/Element.isDescendantOf:(Larc/scene/Element;)Z
      52: ifne          76
      55: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
      58: invokevirtual #447                // Method arc/scene/Scene.getKeyboardFocus:()Larc/scene/Element;
      61: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
      64: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
      67: getfield      #471                // Field mindustry/ui/fragments/MinimapFragment.elem:Larc/scene/Element;
      70: invokevirtual #461                // Method arc/scene/Element.isDescendantOf:(Larc/scene/Element;)Z
      73: ifeq          85
      76: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
      79: getfield      #451                // Field mindustry/core/UI.listfrag:Lmindustry/ui/fragments/PlayerListFragment;
      82: invokevirtual #477                // Method mindustry/ui/fragments/PlayerListFragment.toggle:()V
      85: aload_0
      86: invokevirtual #480                // Method locked:()Z
      89: istore_1
      90: iconst_0
      91: istore_2
      92: getstatic     #174                // Field arc/Core.input:Larc/Input;
      95: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
      98: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     101: ifne          111
     104: aload_0
     105: getfield      #60                 // Field panSpeed:F
     108: goto          115
     111: aload_0
     112: getfield      #64                 // Field panBoostSpeed:F
     115: getstatic     #486                // Field arc/util/Time.delta:F
     118: fmul
     119: fstore_3
     120: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
     123: ldc_w         #489                // String detach-camera
     126: iconst_0
     127: invokevirtual #491                // Method arc/Settings.getBool:(Ljava/lang/String;Z)Z
     130: istore        4
     132: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     135: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
     138: ifne          391
     141: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     144: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
     147: ifne          391
     150: getstatic     #174                // Field arc/Core.input:Larc/Input;
     153: getstatic     #500                // Field mindustry/input/Binding.debugHitboxes:Larc/input/KeyBind;
     156: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     159: ifeq          171
     162: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
     165: ldc_w         #503                // String drawhitboxes
     168: invokevirtual #505                // Method arc/Settings.toggle:(Ljava/lang/String;)V
     171: getstatic     #174                // Field arc/Core.input:Larc/Input;
     174: getstatic     #508                // Field mindustry/input/Binding.teleportCursor:Larc/input/KeyBind;
     177: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     180: ifeq          259
     183: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     186: getfield      #515                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
     189: getfield      #521                // Field mindustry/game/Rules.editor:Z
     192: ifne          207
     195: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     198: getfield      #515                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
     201: getfield      #526                // Field mindustry/game/Rules.infiniteResources:Z
     204: ifeq          259
     207: getstatic     #432                // Field mindustry/Vars.net:Lmindustry/net/Net;
     210: invokevirtual #529                // Method mindustry/net/Net.client:()Z
     213: ifne          259
     216: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     219: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     222: ifeq          244
     225: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
     228: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
     231: getstatic     #174                // Field arc/Core.input:Larc/Input;
     234: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     237: invokevirtual #545                // Method arc/math/geom/Vec2.set:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
     240: pop
     241: goto          259
     244: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     247: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     250: getstatic     #174                // Field arc/Core.input:Larc/Input;
     253: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     256: invokevirtual #548                // Method mindustry/gen/Unit.set:(Larc/math/geom/Position;)V
     259: getstatic     #174                // Field arc/Core.input:Larc/Input;
     262: getstatic     #551                // Field mindustry/input/Binding.detachCamera:Larc/input/KeyBind;
     265: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     268: ifeq          311
     271: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
     274: ldc_w         #489                // String detach-camera
     277: iload         4
     279: ifne          286
     282: iconst_1
     283: goto          287
     286: iconst_0
     287: dup
     288: istore        4
     290: invokestatic  #554                // Method java/lang/Boolean.valueOf:(Z)Ljava/lang/Boolean;
     293: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
     296: iload         4
     298: ifne          306
     301: aload_0
     302: iconst_0
     303: putfield      #48                 // Field panning:Z
     306: aload_0
     307: aconst_null
     308: putfield      #564                // Field spectating:Lmindustry/gen/Unit;
     311: getstatic     #174                // Field arc/Core.input:Larc/Input;
     314: getstatic     #568                // Field mindustry/input/Binding.pan:Larc/input/KeyBind;
     317: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     320: ifeq          335
     323: iconst_1
     324: istore_2
     325: aload_0
     326: iconst_1
     327: putfield      #48                 // Field panning:Z
     330: aload_0
     331: aconst_null
     332: putfield      #564                // Field spectating:Lmindustry/gen/Unit;
     335: getstatic     #174                // Field arc/Core.input:Larc/Input;
     338: getstatic     #571                // Field mindustry/input/Binding.moveX:Larc/input/KeyBind;
     341: invokevirtual #574                // Method arc/Input.axis:(Larc/input/KeyBind;)F
     344: invokestatic  #578                // Method java/lang/Math.abs:(F)F
     347: fconst_0
     348: fcmpl
     349: ifgt          381
     352: getstatic     #174                // Field arc/Core.input:Larc/Input;
     355: getstatic     #584                // Field mindustry/input/Binding.moveY:Larc/input/KeyBind;
     358: invokevirtual #574                // Method arc/Input.axis:(Larc/input/KeyBind;)F
     361: invokestatic  #578                // Method java/lang/Math.abs:(F)F
     364: fconst_0
     365: fcmpl
     366: ifgt          381
     369: getstatic     #174                // Field arc/Core.input:Larc/Input;
     372: getstatic     #587                // Field mindustry/input/Binding.mouseMove:Larc/input/KeyBind;
     375: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     378: ifeq          391
     381: aload_0
     382: iconst_0
     383: putfield      #48                 // Field panning:Z
     386: aload_0
     387: aconst_null
     388: putfield      #564                // Field spectating:Lmindustry/gen/Unit;
     391: aload_0
     392: dup
     393: getfield      #48                 // Field panning:Z
     396: iload         4
     398: ior
     399: putfield      #48                 // Field panning:Z
     402: iload_1
     403: ifne          772
     406: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     409: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     412: ifne          429
     415: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     418: invokevirtual #590                // Method mindustry/core/GameState.isPaused:()Z
     421: ifne          429
     424: iload         4
     426: ifeq          520
     429: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
     432: getfield      #593                // Field mindustry/core/UI.chatfrag:Lmindustry/ui/fragments/ChatFragment;
     435: invokevirtual #597                // Method mindustry/ui/fragments/ChatFragment.shown:()Z
     438: ifne          520
     441: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     444: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
     447: ifne          520
     450: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     453: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
     456: ifne          520
     459: getstatic     #174                // Field arc/Core.input:Larc/Input;
     462: getstatic     #587                // Field mindustry/input/Binding.mouseMove:Larc/input/KeyBind;
     465: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     468: ifeq          473
     471: iconst_1
     472: istore_2
     473: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
     476: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
     479: getstatic     #600                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     482: invokevirtual #605                // Method arc/math/geom/Vec2.setZero:()Larc/math/geom/Vec2;
     485: getstatic     #174                // Field arc/Core.input:Larc/Input;
     488: getstatic     #571                // Field mindustry/input/Binding.moveX:Larc/input/KeyBind;
     491: invokevirtual #574                // Method arc/Input.axis:(Larc/input/KeyBind;)F
     494: getstatic     #174                // Field arc/Core.input:Larc/Input;
     497: getstatic     #584                // Field mindustry/input/Binding.moveY:Larc/input/KeyBind;
     500: invokevirtual #574                // Method arc/Input.axis:(Larc/input/KeyBind;)F
     503: invokevirtual #608                // Method arc/math/geom/Vec2.add:(FF)Larc/math/geom/Vec2;
     506: invokevirtual #612                // Method arc/math/geom/Vec2.nor:()Larc/math/geom/Vec2;
     509: fload_3
     510: invokevirtual #615                // Method arc/math/geom/Vec2.scl:(F)Larc/math/geom/Vec2;
     513: invokevirtual #619                // Method arc/math/geom/Vec2.add:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
     516: pop
     517: goto          678
     520: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     523: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     526: ifeq          536
     529: aload_0
     530: getfield      #564                // Field spectating:Lmindustry/gen/Unit;
     533: ifnull        678
     536: aload_0
     537: getfield      #48                 // Field panning:Z
     540: ifne          678
     543: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     546: getfield      #621                // Field mindustry/core/GameState.won:Z
     549: ifeq          564
     552: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     555: getfield      #515                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
     558: getfield      #624                // Field mindustry/game/Rules.waveTeam:Lmindustry/game/Team;
     561: goto          570
     564: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     567: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     570: astore        5
     572: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     575: getfield      #632                // Field mindustry/core/GameState.gameOver:Z
     578: ifeq          615
     581: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     584: getfield      #515                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
     587: getfield      #635                // Field mindustry/game/Rules.pvp:Z
     590: ifne          615
     593: aload         5
     595: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
     598: getfield      #644                // Field mindustry/game/Teams$TeamData.lastCore:Lmindustry/world/blocks/storage/CoreBlock$CoreBuild;
     601: ifnull        615
     604: aload         5
     606: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
     609: getfield      #644                // Field mindustry/game/Teams$TeamData.lastCore:Lmindustry/world/blocks/storage/CoreBlock$CoreBuild;
     612: goto          616
     615: aconst_null
     616: astore        6
     618: aload         6
     620: ifnull        628
     623: aload         6
     625: goto          645
     628: aload_0
     629: getfield      #564                // Field spectating:Lmindustry/gen/Unit;
     632: ifnull        642
     635: aload_0
     636: getfield      #564                // Field spectating:Lmindustry/gen/Unit;
     639: goto          645
     642: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     645: astore        7
     647: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
     650: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
     653: aload         7
     655: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
     658: ldc_w         #650                // String smoothcamera
     661: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
     664: ifeq          673
     667: ldc_w         #652                // float 0.08f
     670: goto          674
     673: fconst_1
     674: invokevirtual #653                // Method arc/math/geom/Vec2.lerpDelta:(Larc/math/geom/Position;F)Larc/math/geom/Vec2;
     677: pop
     678: iload_2
     679: ifeq          772
     682: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
     685: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
     688: dup
     689: getfield      #657                // Field arc/math/geom/Vec2.x:F
     692: getstatic     #174                // Field arc/Core.input:Larc/Input;
     695: invokevirtual #178                // Method arc/Input.mouseX:()I
     698: i2f
     699: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
     702: invokevirtual #659                // Method arc/Graphics.getWidth:()I
     705: i2f
     706: fconst_2
     707: fdiv
     708: fsub
     709: aload_0
     710: getfield      #55                 // Field panScale:F
     713: fmul
     714: ldc_w         #662                // float -1.0f
     717: fconst_1
     718: invokestatic  #663                // Method arc/math/Mathf.clamp:(FFF)F
     721: fload_3
     722: fmul
     723: fadd
     724: putfield      #657                // Field arc/math/geom/Vec2.x:F
     727: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
     730: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
     733: dup
     734: getfield      #666                // Field arc/math/geom/Vec2.y:F
     737: getstatic     #174                // Field arc/Core.input:Larc/Input;
     740: invokevirtual #188                // Method arc/Input.mouseY:()I
     743: i2f
     744: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
     747: invokevirtual #668                // Method arc/Graphics.getHeight:()I
     750: i2f
     751: fconst_2
     752: fdiv
     753: fsub
     754: aload_0
     755: getfield      #55                 // Field panScale:F
     758: fmul
     759: ldc_w         #662                // float -1.0f
     762: fconst_1
     763: invokestatic  #663                // Method arc/math/Mathf.clamp:(FFF)F
     766: fload_3
     767: fmul
     768: fadd
     769: putfield      #666                // Field arc/math/geom/Vec2.y:F
     772: aload_0
     773: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     776: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
     779: ifne          799
     782: iload_1
     783: ifne          799
     786: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     789: invokevirtual #671                // Method mindustry/core/GameState.isEditor:()Z
     792: ifne          799
     795: iconst_1
     796: goto          800
     799: iconst_0
     800: putfield      #45                 // Field shouldShoot:Z
     803: iload_1
     804: ifne          933
     807: aload_0
     808: getfield      #345                // Field block:Lmindustry/world/Block;
     811: ifnonnull     933
     814: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     817: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
     820: ifne          933
     823: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     826: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
     829: ifne          933
     832: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     835: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     838: ifne          874
     841: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     844: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     847: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     850: getfield      #678                // Field mindustry/type/UnitType.canBoost:Z
     853: ifeq          874
     856: getstatic     #683                // Field mindustry/input/Binding.commandMode:Larc/input/KeyBind;
     859: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     862: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
     865: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     868: invokevirtual #692                // Method arc/input/KeyBind$Axis.equals:(Ljava/lang/Object;)Z
     871: ifne          933
     874: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
     877: ldc_w         #698                // String commandmodehold
     880: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
     883: ifeq          902
     886: aload_0
     887: getstatic     #174                // Field arc/Core.input:Larc/Input;
     890: getstatic     #683                // Field mindustry/input/Binding.commandMode:Larc/input/KeyBind;
     893: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     896: putfield      #700                // Field commandMode:Z
     899: goto          938
     902: getstatic     #174                // Field arc/Core.input:Larc/Input;
     905: getstatic     #683                // Field mindustry/input/Binding.commandMode:Larc/input/KeyBind;
     908: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     911: ifeq          938
     914: aload_0
     915: aload_0
     916: getfield      #700                // Field commandMode:Z
     919: ifne          926
     922: iconst_1
     923: goto          927
     926: iconst_0
     927: putfield      #700                // Field commandMode:Z
     930: goto          938
     933: aload_0
     934: iconst_0
     935: putfield      #700                // Field commandMode:Z
     938: aload_0
     939: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
     942: invokedynamic #705,  0            // InvokeDynamic #3:get:()Larc/func/Boolf;
     947: invokevirtual #708                // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
     950: pop
     951: aload_0
     952: getfield      #700                // Field commandMode:Z
     955: ifeq          1843
     958: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     961: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
     964: ifne          1843
     967: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     970: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
     973: ifne          1843
     976: getstatic     #174                // Field arc/Core.input:Larc/Input;
     979: getstatic     #712                // Field mindustry/input/Binding.selectAllUnits:Larc/input/KeyBind;
     982: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     985: ifeq          1143
     988: aload_0
     989: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
     992: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     995: pop
     996: aload_0
     997: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1000: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1003: pop
    1004: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1007: getstatic     #722                // Field mindustry/input/Binding.selectAcrossScreen:Larc/input/KeyBind;
    1010: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1013: ifeq          1072
    1016: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1019: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1022: invokevirtual #729                // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
    1025: pop
    1026: aload_0
    1027: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1030: aload_0
    1031: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1034: getfield      #733                // Field arc/math/geom/Rect.x:F
    1037: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1040: getfield      #736                // Field arc/math/geom/Rect.y:F
    1043: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1046: getfield      #737                // Field arc/math/geom/Rect.width:F
    1049: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1052: getfield      #740                // Field arc/math/geom/Rect.height:F
    1055: invokevirtual #743                // Method selectedCommandUnits:(FFFF)Larc/struct/Seq;
    1058: invokedynamic #747,  0            // InvokeDynamic #4:get:()Larc/func/Boolf;
    1063: invokevirtual #708                // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
    1066: invokevirtual #748                // Method arc/struct/Seq.set:(Larc/struct/Seq;)V
    1069: goto          1143
    1072: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1075: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    1078: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
    1081: getfield      #751                // Field mindustry/game/Teams$TeamData.units:Larc/struct/Seq;
    1084: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1087: astore        5
    1089: aload         5
    1091: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1096: ifeq          1143
    1099: aload         5
    1101: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1106: checkcast     #129                // class mindustry/gen/Unit
    1109: astore        6
    1111: aload         6
    1113: invokevirtual #767                // Method mindustry/gen/Unit.isCommandable:()Z
    1116: ifeq          1140
    1119: aload         6
    1121: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
    1124: getfield      #770                // Field mindustry/type/UnitType.controlSelectGlobal:Z
    1127: ifeq          1140
    1130: aload_0
    1131: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1134: aload         6
    1136: invokevirtual #773                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
    1139: pop
    1140: goto          1089
    1143: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1146: getstatic     #776                // Field mindustry/input/Binding.selectAllUnitTransport:Larc/input/KeyBind;
    1149: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1152: ifeq          1304
    1155: aload_0
    1156: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1159: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1162: pop
    1163: aload_0
    1164: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1167: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1170: pop
    1171: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1174: getstatic     #722                // Field mindustry/input/Binding.selectAcrossScreen:Larc/input/KeyBind;
    1177: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1180: ifeq          1236
    1183: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1186: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1189: invokevirtual #729                // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
    1192: pop
    1193: aload_0
    1194: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1197: aload_0
    1198: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1201: getfield      #733                // Field arc/math/geom/Rect.x:F
    1204: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1207: getfield      #736                // Field arc/math/geom/Rect.y:F
    1210: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1213: getfield      #737                // Field arc/math/geom/Rect.width:F
    1216: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1219: getfield      #740                // Field arc/math/geom/Rect.height:F
    1222: invokedynamic #779,  0            // InvokeDynamic #5:get:()Larc/func/Boolf;
    1227: invokevirtual #780                // Method selectedCommandUnits:(FFFFLarc/func/Boolf;)Larc/struct/Seq;
    1230: invokevirtual #748                // Method arc/struct/Seq.set:(Larc/struct/Seq;)V
    1233: goto          1304
    1236: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1239: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    1242: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
    1245: getfield      #751                // Field mindustry/game/Teams$TeamData.units:Larc/struct/Seq;
    1248: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1251: astore        5
    1253: aload         5
    1255: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1260: ifeq          1304
    1263: aload         5
    1265: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1270: checkcast     #129                // class mindustry/gen/Unit
    1273: astore        6
    1275: aload         6
    1277: invokevirtual #767                // Method mindustry/gen/Unit.isCommandable:()Z
    1280: ifeq          1301
    1283: aload         6
    1285: instanceof    #783                // class mindustry/gen/Payloadc
    1288: ifeq          1301
    1291: aload_0
    1292: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1295: aload         6
    1297: invokevirtual #773                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
    1300: pop
    1301: goto          1253
    1304: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1307: getstatic     #785                // Field mindustry/input/Binding.selectAllUnitFactories:Larc/input/KeyBind;
    1310: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1313: ifeq          1427
    1316: aload_0
    1317: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1320: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1323: pop
    1324: aload_0
    1325: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1328: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1331: pop
    1332: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1335: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    1338: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
    1341: getfield      #788                // Field mindustry/game/Teams$TeamData.buildings:Larc/struct/Seq;
    1344: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1347: astore        5
    1349: aload         5
    1351: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1356: ifeq          1392
    1359: aload         5
    1361: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1366: checkcast     #791                // class mindustry/gen/Building
    1369: astore        6
    1371: aload         6
    1373: invokevirtual #793                // Method mindustry/gen/Building.isCommandable:()Z
    1376: ifeq          1389
    1379: aload_0
    1380: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1383: aload         6
    1385: invokevirtual #773                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
    1388: pop
    1389: goto          1349
    1392: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1395: getstatic     #722                // Field mindustry/input/Binding.selectAcrossScreen:Larc/input/KeyBind;
    1398: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1401: ifeq          1427
    1404: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1407: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1410: invokevirtual #729                // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
    1413: pop
    1414: aload_0
    1415: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1418: invokedynamic #794,  0            // InvokeDynamic #6:get:()Larc/func/Boolf;
    1423: invokevirtual #795                // Method arc/struct/Seq.retainAll:(Larc/func/Boolf;)Larc/struct/Seq;
    1426: pop
    1427: iconst_0
    1428: istore        5
    1430: iload         5
    1432: getstatic     #798                // Field controlGroupBindings:[Larc/input/KeyBind;
    1435: arraylength
    1436: if_icmpge     1843
    1439: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1442: getstatic     #798                // Field controlGroupBindings:[Larc/input/KeyBind;
    1445: iload         5
    1447: aaload
    1448: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1451: ifeq          1837
    1454: aload_0
    1455: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1458: iload         5
    1460: aaload
    1461: ifnonnull     1478
    1464: aload_0
    1465: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1468: iload         5
    1470: new           #806                // class arc/struct/IntSeq
    1473: dup
    1474: invokespecial #808                // Method arc/struct/IntSeq."<init>":()V
    1477: aastore
    1478: aload_0
    1479: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1482: iload         5
    1484: aaload
    1485: astore        6
    1487: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1490: getstatic     #809                // Field mindustry/input/Binding.createControlGroup:Larc/input/KeyBind;
    1493: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1496: istore        7
    1498: iload         7
    1500: ifeq          1589
    1503: aload         6
    1505: invokevirtual #812                // Method arc/struct/IntSeq.clear:()V
    1508: aload_0
    1509: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1512: invokedynamic #814,  0            // InvokeDynamic #7:get:()Larc/func/Intf;
    1517: invokevirtual #817                // Method arc/struct/Seq.mapInt:(Larc/func/Intf;)Larc/struct/IntSeq;
    1520: astore        8
    1522: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    1525: ldc_w         #821                // String distinctcontrolgroups
    1528: iconst_1
    1529: invokevirtual #491                // Method arc/Settings.getBool:(Ljava/lang/String;Z)Z
    1532: ifeq          1582
    1535: aload_0
    1536: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1539: astore        9
    1541: aload         9
    1543: arraylength
    1544: istore        10
    1546: iconst_0
    1547: istore        11
    1549: iload         11
    1551: iload         10
    1553: if_icmpge     1582
    1556: aload         9
    1558: iload         11
    1560: aaload
    1561: astore        12
    1563: aload         12
    1565: ifnull        1576
    1568: aload         12
    1570: aload         8
    1572: invokevirtual #823                // Method arc/struct/IntSeq.removeAll:(Larc/struct/IntSeq;)Z
    1575: pop
    1576: iinc          11, 1
    1579: goto          1549
    1582: aload         6
    1584: aload         8
    1586: invokevirtual #826                // Method arc/struct/IntSeq.addAll:(Larc/struct/IntSeq;)V
    1589: iconst_0
    1590: istore        8
    1592: iload         8
    1594: aload         6
    1596: getfield      #830                // Field arc/struct/IntSeq.size:I
    1599: if_icmpge     1658
    1602: getstatic     #831                // Field mindustry/gen/Groups.unit:Lmindustry/entities/EntityGroup;
    1605: aload         6
    1607: iload         8
    1609: invokevirtual #836                // Method arc/struct/IntSeq.get:(I)I
    1612: invokevirtual #838                // Method mindustry/entities/EntityGroup.getByID:(I)Lmindustry/gen/Entityc;
    1615: checkcast     #129                // class mindustry/gen/Unit
    1618: astore        9
    1620: aload         9
    1622: ifnull        1641
    1625: aload         9
    1627: invokevirtual #767                // Method mindustry/gen/Unit.isCommandable:()Z
    1630: ifeq          1641
    1633: aload         9
    1635: invokevirtual #844                // Method mindustry/gen/Unit.isValid:()Z
    1638: ifne          1652
    1641: aload         6
    1643: iload         8
    1645: invokevirtual #847                // Method arc/struct/IntSeq.removeIndex:(I)I
    1648: pop
    1649: iinc          8, -1
    1652: iinc          8, 1
    1655: goto          1592
    1658: aload         6
    1660: invokevirtual #850                // Method arc/struct/IntSeq.isEmpty:()Z
    1663: ifne          1837
    1666: iload         7
    1668: ifne          1837
    1671: aload_0
    1672: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1675: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1678: pop
    1679: aload_0
    1680: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1683: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1686: pop
    1687: aload         6
    1689: aload_0
    1690: invokedynamic #851,  0            // InvokeDynamic #8:get:(Lmindustry/input/DesktopInput;)Larc/func/Intc;
    1695: invokevirtual #854                // Method arc/struct/IntSeq.each:(Larc/func/Intc;)V
    1698: aload_0
    1699: getfield      #857                // Field lastCtrlGroup:I
    1702: iload         5
    1704: if_icmpne     1818
    1707: aload_0
    1708: getfield      #860                // Field lastCtrlGroupSelectMillis:J
    1711: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
    1714: ldc2_w        #867                // long 400l
    1717: lcmp
    1718: ifge          1818
    1721: fconst_0
    1722: fstore        8
    1724: fconst_0
    1725: fstore        9
    1727: aload_0
    1728: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1731: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1734: astore        10
    1736: aload         10
    1738: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1743: ifeq          1781
    1746: aload         10
    1748: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1753: checkcast     #129                // class mindustry/gen/Unit
    1756: astore        11
    1758: fload         8
    1760: aload         11
    1762: getfield      #869                // Field mindustry/gen/Unit.x:F
    1765: fadd
    1766: fstore        8
    1768: fload         9
    1770: aload         11
    1772: getfield      #870                // Field mindustry/gen/Unit.y:F
    1775: fadd
    1776: fstore        9
    1778: goto          1736
    1781: aload_0
    1782: iconst_1
    1783: putfield      #48                 // Field panning:Z
    1786: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1789: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
    1792: fload         8
    1794: aload_0
    1795: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1798: getfield      #325                // Field arc/struct/Seq.size:I
    1801: i2f
    1802: fdiv
    1803: fload         9
    1805: aload_0
    1806: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1809: getfield      #325                // Field arc/struct/Seq.size:I
    1812: i2f
    1813: fdiv
    1814: invokevirtual #871                // Method arc/math/geom/Vec2.set:(FF)Larc/math/geom/Vec2;
    1817: pop
    1818: aload_0
    1819: iload         5
    1821: putfield      #857                // Field lastCtrlGroup:I
    1824: aload_0
    1825: invokestatic  #873                // Method arc/util/Time.millis:()J
    1828: putfield      #860                // Field lastCtrlGroupSelectMillis:J
    1831: getstatic     #877                // Field mindustry/game/EventType$Trigger.unitCommandChange:Lmindustry/game/EventType$Trigger;
    1834: invokestatic  #883                // Method arc/Events.fire:(Ljava/lang/Enum;)V
    1837: iinc          5, 1
    1840: goto          1430
    1843: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1846: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    1849: ifne          1948
    1852: iload_1
    1853: ifne          1948
    1856: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    1859: getfield      #515                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
    1862: getfield      #889                // Field mindustry/game/Rules.possessionAllowed:Z
    1865: ifeq          1948
    1868: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1871: getstatic     #892                // Field mindustry/input/Binding.control:Larc/input/KeyBind;
    1874: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1877: ifeq          1948
    1880: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1883: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    1886: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1889: ifeq          1948
    1892: aload_0
    1893: invokevirtual #898                // Method selectedUnit:()Lmindustry/gen/Unit;
    1896: astore        5
    1898: aload_0
    1899: invokevirtual #901                // Method selectedControlBuild:()Lmindustry/gen/Building;
    1902: astore        6
    1904: aload         5
    1906: ifnull        1930
    1909: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1912: aload         5
    1914: invokestatic  #905                // Method mindustry/gen/Call.unitControl:(Lmindustry/gen/Player;Lmindustry/gen/Unit;)V
    1917: aload_0
    1918: iconst_0
    1919: putfield      #45                 // Field shouldShoot:Z
    1922: aload_0
    1923: fconst_1
    1924: putfield      #911                // Field recentRespawnTimer:F
    1927: goto          1948
    1930: aload         6
    1932: ifnull        1948
    1935: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1938: aload         6
    1940: invokestatic  #914                // Method mindustry/gen/Call.buildingControlSelect:(Lmindustry/gen/Player;Lmindustry/gen/Building;)V
    1943: aload_0
    1944: fconst_1
    1945: putfield      #911                // Field recentRespawnTimer:F
    1948: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1951: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    1954: ifne          2028
    1957: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    1960: invokevirtual #590                // Method mindustry/core/GameState.isPaused:()Z
    1963: ifne          2028
    1966: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1969: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
    1972: ifne          2028
    1975: iload_1
    1976: ifne          2028
    1979: getstatic     #918                // Field mindustryX/features/LogicExt.noUpdatePlayerMovement:Z
    1982: ifne          1995
    1985: aload_0
    1986: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1989: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    1992: invokevirtual #923                // Method updateMovement:(Lmindustry/gen/Unit;)V
    1995: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1998: getstatic     #927                // Field mindustry/input/Binding.respawn:Larc/input/KeyBind;
    2001: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2004: ifeq          2028
    2007: aload_0
    2008: aconst_null
    2009: putfield      #930                // Field controlledType:Lmindustry/type/UnitType;
    2012: aload_0
    2013: fconst_1
    2014: putfield      #911                // Field recentRespawnTimer:F
    2017: aload_0
    2018: iconst_0
    2019: putfield      #933                // Field droppingItem:Z
    2022: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2025: invokestatic  #936                // Method mindustry/gen/Call.unitClear:(Lmindustry/gen/Player;)V
    2028: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2031: invokevirtual #940                // Method mindustry/core/GameState.isGame:()Z
    2034: ifeq          2282
    2037: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2040: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
    2043: ifne          2282
    2046: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2049: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
    2052: ifne          2282
    2055: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2058: getstatic     #943                // Field mindustry/input/Binding.minimap:Larc/input/KeyBind;
    2061: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2064: ifeq          2076
    2067: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2070: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
    2073: invokevirtual #946                // Method mindustry/ui/fragments/MinimapFragment.toggle:()V
    2076: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2079: getstatic     #947                // Field mindustry/input/Binding.planetMap:Larc/input/KeyBind;
    2082: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2085: ifeq          2106
    2088: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2091: invokevirtual #950                // Method mindustry/core/GameState.isCampaign:()Z
    2094: ifeq          2106
    2097: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2100: getfield      #953                // Field mindustry/core/UI.planet:Lmindustry/ui/dialogs/PlanetDialog;
    2103: invokevirtual #957                // Method mindustry/ui/dialogs/PlanetDialog.toggle:()V
    2106: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2109: getstatic     #960                // Field mindustry/input/Binding.research:Larc/input/KeyBind;
    2112: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2115: ifeq          2136
    2118: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2121: invokevirtual #950                // Method mindustry/core/GameState.isCampaign:()Z
    2124: ifeq          2136
    2127: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2130: getfield      #963                // Field mindustry/core/UI.research:Lmindustry/ui/dialogs/ResearchDialog;
    2133: invokevirtual #966                // Method mindustry/ui/dialogs/ResearchDialog.toggle:()V
    2136: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2139: getstatic     #969                // Field mindustry/input/Binding.schematicMenu:Larc/input/KeyBind;
    2142: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2145: ifeq          2157
    2148: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2151: getfield      #972                // Field mindustry/core/UI.schematics:Lmindustry/ui/dialogs/SchematicsDialog;
    2154: invokevirtual #976                // Method mindustry/ui/dialogs/SchematicsDialog.toggle:()V
    2157: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2160: getstatic     #979                // Field mindustry/input/Binding.toggleBlockStatus:Larc/input/KeyBind;
    2163: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2166: ifeq          2198
    2169: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2172: ldc_w         #982                // String blockstatus
    2175: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2178: ldc_w         #982                // String blockstatus
    2181: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
    2184: ifne          2191
    2187: iconst_1
    2188: goto          2192
    2191: iconst_0
    2192: invokestatic  #554                // Method java/lang/Boolean.valueOf:(Z)Ljava/lang/Boolean;
    2195: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2198: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2201: getstatic     #984                // Field mindustry/input/Binding.togglePowerLines:Larc/input/KeyBind;
    2204: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2207: ifeq          2282
    2210: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2213: ldc_w         #987                // String lasersopacity
    2216: invokevirtual #989                // Method arc/Settings.getInt:(Ljava/lang/String;)I
    2219: ifne          2248
    2222: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2225: ldc_w         #987                // String lasersopacity
    2228: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2231: ldc_w         #993                // String preferredlaseropacity
    2234: bipush        100
    2236: invokevirtual #995                // Method arc/Settings.getInt:(Ljava/lang/String;I)I
    2239: invokestatic  #998                // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
    2242: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2245: goto          2282
    2248: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2251: ldc_w         #993                // String preferredlaseropacity
    2254: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2257: ldc_w         #987                // String lasersopacity
    2260: invokevirtual #989                // Method arc/Settings.getInt:(Ljava/lang/String;)I
    2263: invokestatic  #998                // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
    2266: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2269: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2272: ldc_w         #987                // String lasersopacity
    2275: iconst_0
    2276: invokestatic  #998                // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
    2279: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2282: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2285: invokevirtual #1003               // Method mindustry/core/GameState.isMenu:()Z
    2288: ifne          2300
    2291: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2294: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
    2297: ifeq          2378
    2300: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2303: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2306: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2309: ifne          2319
    2312: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2315: iconst_0
    2316: putfield      #1006               // Field mindustry/gen/Player.shooting:Z
    2319: aload_0
    2320: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2323: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    2326: if_acmpne     2348
    2329: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2332: getstatic     #1009               // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    2335: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2338: ifne          2348
    2341: aload_0
    2342: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2345: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2348: aload_0
    2349: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2352: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    2355: if_acmpne     2377
    2358: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2361: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2364: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2367: ifne          2377
    2370: aload_0
    2371: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2374: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2377: return
    2378: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2381: invokevirtual #1012               // Method arc/scene/Scene.hasScroll:()Z
    2384: ifeq          2399
    2387: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2390: getstatic     #1015               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    2393: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2396: ifeq          2533
    2399: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2402: getfield      #593                // Field mindustry/core/UI.chatfrag:Lmindustry/ui/fragments/ChatFragment;
    2405: invokevirtual #597                // Method mindustry/ui/fragments/ChatFragment.shown:()Z
    2408: ifne          2533
    2411: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2414: getfield      #1018               // Field mindustry/core/UI.consolefrag:Lmindustry/ui/fragments/ConsoleFragment;
    2417: invokevirtual #1022               // Method mindustry/ui/fragments/ConsoleFragment.shown:()Z
    2420: ifne          2533
    2423: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2426: getstatic     #1025               // Field mindustry/input/Binding.zoom:Larc/input/KeyBind;
    2429: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2432: invokestatic  #578                // Method java/lang/Math.abs:(F)F
    2435: fconst_0
    2436: fcmpl
    2437: ifle          2533
    2440: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2443: getstatic     #1031               // Field mindustry/input/Binding.rotatePlaced:Larc/input/KeyBind;
    2446: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2449: ifne          2533
    2452: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2455: getstatic     #1015               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    2458: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2461: ifne          2518
    2464: getstatic     #1025               // Field mindustry/input/Binding.zoom:Larc/input/KeyBind;
    2467: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
    2470: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2473: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
    2476: invokevirtual #692                // Method arc/input/KeyBind$Axis.equals:(Ljava/lang/Object;)Z
    2479: ifeq          2518
    2482: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2485: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    2488: ifeq          2508
    2491: aload_0
    2492: invokevirtual #302                // Method isPlacing:()Z
    2495: ifeq          2508
    2498: aload_0
    2499: getfield      #345                // Field block:Lmindustry/world/Block;
    2502: getfield      #260                // Field mindustry/world/Block.rotate:Z
    2505: ifne          2533
    2508: aload_0
    2509: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2512: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    2515: ifeq          2533
    2518: getstatic     #1036               // Field mindustry/Vars.renderer:Lmindustry/core/Renderer;
    2521: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2524: getstatic     #1025               // Field mindustry/input/Binding.zoom:Larc/input/KeyBind;
    2527: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2530: invokevirtual #1040               // Method mindustry/core/Renderer.scaleCamera:(F)V
    2533: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2536: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2539: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2542: ifeq          2587
    2545: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2548: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    2551: ifne          2587
    2554: getstatic     #1045               // Field mindustry/Vars.world:Lmindustry/core/World;
    2557: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2560: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
    2563: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2566: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
    2569: invokevirtual #1056               // Method mindustry/core/World.tileWorld:(FF)Lmindustry/world/Tile;
    2572: astore        5
    2574: aload         5
    2576: ifnull        2587
    2579: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2582: aload         5
    2584: invokestatic  #1062               // Method mindustry/gen/Call.tileTap:(Lmindustry/gen/Player;Lmindustry/world/Tile;)V
    2587: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2590: getstatic     #1066               // Field mindustry/input/Binding.ping:Larc/input/KeyBind;
    2593: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2596: ifeq          2670
    2599: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2602: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    2605: ifne          2670
    2608: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2611: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
    2614: ifne          2670
    2617: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2620: invokevirtual #1069               // Method arc/Input.ctrl:()Z
    2623: ifeq          2651
    2626: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2629: ldc_w         #1072               // String
    2632: ldc_w         #1074               // String @ping.text
    2635: bipush        40
    2637: ldc_w         #1072               // String
    2640: invokedynamic #1076,  0           // InvokeDynamic #9:get:()Larc/func/Cons;
    2645: invokevirtual #1079               // Method mindustry/core/UI.showTextInput:(Ljava/lang/String;Ljava/lang/String;ILjava/lang/String;Larc/func/Cons;)V
    2648: goto          2670
    2651: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2654: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2657: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
    2660: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2663: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
    2666: aconst_null
    2667: invokestatic  #1083               // Method mindustry/gen/Call.pingLocation:(Lmindustry/gen/Player;FFLjava/lang/String;)V
    2670: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2673: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2676: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    2679: ifeq          2693
    2682: aload_0
    2683: getfield      #1090               // Field commandRect:Z
    2686: ifeq          2693
    2689: aload_0
    2690: invokevirtual #1093               // Method selectUnitsRect:()V
    2693: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2696: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    2699: ifne          2706
    2702: iload_1
    2703: ifeq          2743
    2706: aload_0
    2707: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2710: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2713: iload_1
    2714: ifne          2747
    2717: aload_0
    2718: invokevirtual #1096               // Method pollInputNoPlayer:()V
    2721: getstatic     #1099               // Field mindustryX/features/RenderExt.deadOverlay:LmindustryX/features/SettingsV2$CheckPref;
    2724: invokevirtual #1105               // Method mindustryX/features/SettingsV2$CheckPref.get:()Ljava/lang/Object;
    2727: checkcast     #555                // class java/lang/Boolean
    2730: invokevirtual #1109               // Method java/lang/Boolean.booleanValue:()Z
    2733: ifeq          2747
    2736: aload_0
    2737: invokevirtual #1112               // Method pollInputPlayer:()V
    2740: goto          2747
    2743: aload_0
    2744: invokevirtual #1112               // Method pollInputPlayer:()V
    2747: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2750: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2753: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    2756: ifeq          2772
    2759: getstatic     #918                // Field mindustryX/features/LogicExt.noUpdatePlayerMovement:Z
    2762: ifne          2772
    2765: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2768: iconst_0
    2769: putfield      #1006               // Field mindustry/gen/Player.shooting:Z
    2772: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2775: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    2778: ifne          2825
    2781: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2784: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
    2787: invokevirtual #1115               // Method mindustry/ui/fragments/MinimapFragment.shown:()Z
    2790: ifne          2825
    2793: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
    2796: aload_0
    2797: getfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2800: invokevirtual #162                // Method arc/Graphics.cursor:(Larc/Graphics$Cursor;)V
    2803: aload_0
    2804: aload_0
    2805: getfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2808: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2811: if_acmpeq     2818
    2814: iconst_1
    2815: goto          2819
    2818: iconst_0
    2819: putfield      #1116               // Field changedCursor:Z
    2822: goto          2853
    2825: aload_0
    2826: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2829: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2832: aload_0
    2833: getfield      #1116               // Field changedCursor:Z
    2836: ifeq          2853
    2839: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
    2842: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2845: invokevirtual #162                // Method arc/Graphics.cursor:(Larc/Graphics$Cursor;)V
    2848: aload_0
    2849: iconst_0
    2850: putfield      #1116               // Field changedCursor:Z
    2853: return

  public void useSchematic(mindustry.game.Schematic, boolean);
    Code:
       0: aload_0
       1: aconst_null
       2: putfield      #345                // Field block:Lmindustry/world/Block;
       5: aload_0
       6: aload_0
       7: aload_0
       8: invokevirtual #1119               // Method getMouseX:()F
      11: invokevirtual #184                // Method tileX:(F)I
      14: putfield      #1122               // Field schematicX:I
      17: aload_0
      18: aload_0
      19: aload_0
      20: invokevirtual #1125               // Method getMouseY:()F
      23: invokevirtual #191                // Method tileY:(F)I
      26: putfield      #1128               // Field schematicY:I
      29: aload_0
      30: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      33: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      36: pop
      37: aload_0
      38: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      41: getstatic     #1131               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
      44: aload_1
      45: aload_0
      46: getfield      #1122               // Field schematicX:I
      49: aload_0
      50: getfield      #1128               // Field schematicY:I
      53: iload_2
      54: invokevirtual #1134               // Method mindustry/game/Schematics.toPlans:(Lmindustry/game/Schematic;IIZ)Larc/struct/Seq;
      57: invokevirtual #1140               // Method arc/struct/Seq.addAll:(Larc/struct/Seq;)Larc/struct/Seq;
      60: pop
      61: aload_0
      62: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
      65: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
      68: return

  public boolean isBreaking();
    Code:
       0: aload_0
       1: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
       4: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
       7: if_acmpne     14
      10: iconst_1
      11: goto          15
      14: iconst_0
      15: ireturn

  public void buildPlacementUI(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: invokevirtual #1143               // Method arc/scene/ui/layout/Table.left:()Larc/scene/ui/layout/Table;
       4: fconst_0
       5: invokevirtual #1149               // Method arc/scene/ui/layout/Table.margin:(F)Larc/scene/ui/layout/Table;
       8: invokevirtual #1153               // Method arc/scene/ui/layout/Table.defaults:()Larc/scene/ui/layout/Cell;
      11: ldc_w         #1157               // float 48.0f
      14: invokevirtual #1158               // Method arc/scene/ui/layout/Cell.size:(F)Larc/scene/ui/layout/Cell;
      17: invokevirtual #1163               // Method arc/scene/ui/layout/Cell.left:()Larc/scene/ui/layout/Cell;
      20: pop
      21: aload_1
      22: getstatic     #1165               // Field mindustry/gen/Icon.paste:Larc/scene/style/TextureRegionDrawable;
      25: getstatic     #1171               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
      28: invokedynamic #1177,  0           // InvokeDynamic #10:run:()Ljava/lang/Runnable;
      33: invokevirtual #1181               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      36: ldc_w         #1185               // String @schematics
      39: invokevirtual #1187               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
      42: pop
      43: aload_1
      44: getstatic     #1191               // Field mindustry/gen/Icon.book:Larc/scene/style/TextureRegionDrawable;
      47: getstatic     #1171               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
      50: invokedynamic #1194,  0           // InvokeDynamic #11:run:()Ljava/lang/Runnable;
      55: invokevirtual #1181               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      58: ldc_w         #1195               // String @database
      61: invokevirtual #1187               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
      64: pop
      65: aload_1
      66: getstatic     #1197               // Field mindustry/gen/Icon.tree:Larc/scene/style/TextureRegionDrawable;
      69: getstatic     #1171               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
      72: invokedynamic #1200,  0           // InvokeDynamic #12:run:()Ljava/lang/Runnable;
      77: invokevirtual #1181               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      80: invokedynamic #1201,  0           // InvokeDynamic #13:get:()Larc/func/Boolp;
      85: invokevirtual #1204               // Method arc/scene/ui/layout/Cell.visible:(Larc/func/Boolp;)Larc/scene/ui/layout/Cell;
      88: ldc_w         #1208               // String @research
      91: invokevirtual #1187               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
      94: pop
      95: aload_1
      96: getstatic     #1210               // Field mindustry/gen/Icon.map:Larc/scene/style/TextureRegionDrawable;
      99: getstatic     #1171               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
     102: invokedynamic #1213,  0           // InvokeDynamic #14:run:()Ljava/lang/Runnable;
     107: invokevirtual #1181               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
     110: invokedynamic #1214,  0           // InvokeDynamic #15:get:()Larc/func/Boolp;
     115: invokevirtual #1204               // Method arc/scene/ui/layout/Cell.visible:(Larc/func/Boolp;)Larc/scene/ui/layout/Cell;
     118: ldc_w         #1215               // String @planetmap
     121: invokevirtual #1187               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
     124: pop
     125: return

  void pollInputNoPlayer();
    Code:
       0: getstatic     #174                // Field arc/Core.input:Larc/Input;
       3: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
       6: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
       9: ifeq          93
      12: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
      15: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
      18: ifne          93
      21: aload_0
      22: iconst_0
      23: putfield      #1217               // Field tappedOne:Z
      26: aload_0
      27: getstatic     #174                // Field arc/Core.input:Larc/Input;
      30: invokevirtual #178                // Method arc/Input.mouseX:()I
      33: i2f
      34: getstatic     #174                // Field arc/Core.input:Larc/Input;
      37: invokevirtual #188                // Method arc/Input.mouseY:()I
      40: i2f
      41: invokevirtual #1220               // Method tileAt:(FF)Lmindustry/world/Tile;
      44: astore_1
      45: aload_0
      46: getfield      #700                // Field commandMode:Z
      49: ifeq          80
      52: aload_0
      53: iconst_1
      54: putfield      #1090               // Field commandRect:Z
      57: aload_0
      58: getstatic     #174                // Field arc/Core.input:Larc/Input;
      61: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
      64: putfield      #1223               // Field commandRectX:F
      67: aload_0
      68: getstatic     #174                // Field arc/Core.input:Larc/Input;
      71: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
      74: putfield      #1226               // Field commandRectY:F
      77: goto          93
      80: aload_1
      81: ifnull        93
      84: aload_0
      85: aload_1
      86: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      89: invokevirtual #1233               // Method tileTapped:(Lmindustry/gen/Building;)Z
      92: pop
      93: return

  void pollInputPlayer();
    Code:
       0: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
       3: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
       6: ifeq          10
       9: return
      10: aload_0
      11: getstatic     #174                // Field arc/Core.input:Larc/Input;
      14: invokevirtual #178                // Method arc/Input.mouseX:()I
      17: i2f
      18: getstatic     #174                // Field arc/Core.input:Larc/Input;
      21: invokevirtual #188                // Method arc/Input.mouseY:()I
      24: i2f
      25: invokevirtual #1220               // Method tileAt:(FF)Lmindustry/world/Tile;
      28: astore_1
      29: aload_0
      30: getstatic     #174                // Field arc/Core.input:Larc/Input;
      33: invokevirtual #178                // Method arc/Input.mouseX:()I
      36: i2f
      37: invokevirtual #184                // Method tileX:(F)I
      40: istore_2
      41: aload_0
      42: getstatic     #174                // Field arc/Core.input:Larc/Input;
      45: invokevirtual #188                // Method arc/Input.mouseY:()I
      48: i2f
      49: invokevirtual #191                // Method tileY:(F)I
      52: istore_3
      53: getstatic     #174                // Field arc/Core.input:Larc/Input;
      56: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      59: getfield      #657                // Field arc/math/geom/Vec2.x:F
      62: invokestatic  #1237               // Method mindustry/core/World.toTile:(F)I
      65: istore        4
      67: getstatic     #174                // Field arc/Core.input:Larc/Input;
      70: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      73: getfield      #666                // Field arc/math/geom/Vec2.y:F
      76: invokestatic  #1237               // Method mindustry/core/World.toTile:(F)I
      79: istore        5
      81: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      84: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
      87: ifne          130
      90: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      93: ldc           #122                // String buildautopause
      95: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      98: ifeq          130
     101: aload_0
     102: getfield      #119                // Field isBuilding:Z
     105: ifeq          130
     108: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     111: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     114: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
     117: ifne          130
     120: aload_0
     121: iconst_0
     122: putfield      #119                // Field isBuilding:Z
     125: aload_0
     126: iconst_1
     127: putfield      #1240               // Field buildWasAutoPaused:Z
     130: aload_0
     131: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     134: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     137: ifne          196
     140: iload         4
     142: aload_0
     143: getfield      #1122               // Field schematicX:I
     146: isub
     147: istore        6
     149: iload         5
     151: aload_0
     152: getfield      #1128               // Field schematicY:I
     155: isub
     156: istore        7
     158: aload_0
     159: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     162: iload         6
     164: iload         7
     166: invokedynamic #1243,  0           // InvokeDynamic #16:get:(II)Larc/func/Cons;
     171: invokevirtual #356                // Method arc/struct/Seq.each:(Larc/func/Cons;)V
     174: aload_0
     175: dup
     176: getfield      #1122               // Field schematicX:I
     179: iload         6
     181: iadd
     182: putfield      #1122               // Field schematicX:I
     185: aload_0
     186: dup
     187: getfield      #1128               // Field schematicY:I
     190: iload         7
     192: iadd
     193: putfield      #1128               // Field schematicY:I
     196: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     199: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     202: ifne          268
     205: getstatic     #174                // Field arc/Core.input:Larc/Input;
     208: getstatic     #1246               // Field mindustry/input/Binding.deselect:Larc/input/KeyBind;
     211: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     214: ifeq          268
     217: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
     220: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
     223: invokevirtual #1115               // Method mindustry/ui/fragments/MinimapFragment.shown:()Z
     226: ifne          268
     229: aload_0
     230: invokevirtual #302                // Method isPlacing:()Z
     233: ifne          268
     236: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     239: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     242: getfield      #1249               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     245: invokevirtual #1253               // Method arc/struct/Queue.isEmpty:()Z
     248: ifeq          268
     251: aload_0
     252: getfield      #700                // Field commandMode:Z
     255: ifne          268
     258: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     261: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     264: aconst_null
     265: putfield      #1256               // Field mindustry/gen/Unit.mineTile:Lmindustry/world/Tile;
     268: getstatic     #174                // Field arc/Core.input:Larc/Input;
     271: getstatic     #1260               // Field mindustry/input/Binding.clearBuilding:Larc/input/KeyBind;
     274: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     277: ifeq          298
     280: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     283: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     286: ifne          298
     289: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     292: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     295: invokevirtual #1263               // Method mindustry/gen/Unit.clearBuilding:()V
     298: getstatic     #174                // Field arc/Core.input:Larc/Input;
     301: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     304: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     307: ifne          322
     310: getstatic     #174                // Field arc/Core.input:Larc/Input;
     313: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     316: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     319: ifeq          353
     322: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     325: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
     328: ifne          353
     331: aload_0
     332: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     335: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
     338: if_acmpeq     353
     341: aload_0
     342: iload         4
     344: putfield      #35                 // Field schemX:I
     347: aload_0
     348: iload         5
     350: putfield      #38                 // Field schemY:I
     353: getstatic     #174                // Field arc/Core.input:Larc/Input;
     356: getstatic     #1260               // Field mindustry/input/Binding.clearBuilding:Larc/input/KeyBind;
     359: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     362: ifne          372
     365: aload_0
     366: invokevirtual #302                // Method isPlacing:()Z
     369: ifeq          385
     372: aload_0
     373: aconst_null
     374: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
     377: aload_0
     378: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     381: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     384: pop
     385: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     388: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
     391: ifne          558
     394: aload_0
     395: getfield      #28                 // Field selectX:I
     398: iconst_m1
     399: if_icmpne     558
     402: aload_0
     403: getfield      #32                 // Field selectY:I
     406: iconst_m1
     407: if_icmpne     558
     410: aload_0
     411: getfield      #35                 // Field schemX:I
     414: iconst_m1
     415: if_icmpeq     558
     418: aload_0
     419: getfield      #38                 // Field schemY:I
     422: iconst_m1
     423: if_icmpeq     558
     426: getstatic     #174                // Field arc/Core.input:Larc/Input;
     429: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     432: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     435: ifeq          508
     438: aload_0
     439: getstatic     #1131               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
     442: aload_0
     443: getfield      #35                 // Field schemX:I
     446: aload_0
     447: getfield      #38                 // Field schemY:I
     450: iload         4
     452: iload         5
     454: invokevirtual #1269               // Method mindustry/game/Schematics.create:(IIII)Lmindustry/game/Schematic;
     457: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
     460: aload_0
     461: aload_0
     462: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
     465: invokevirtual #1273               // Method useSchematic:(Lmindustry/game/Schematic;)V
     468: aload_0
     469: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     472: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     475: ifeq          483
     478: aload_0
     479: aconst_null
     480: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
     483: getstatic     #174                // Field arc/Core.input:Larc/Input;
     486: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     489: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     492: ifne          558
     495: aload_0
     496: iconst_m1
     497: putfield      #35                 // Field schemX:I
     500: aload_0
     501: iconst_m1
     502: putfield      #38                 // Field schemY:I
     505: goto          558
     508: getstatic     #174                // Field arc/Core.input:Larc/Input;
     511: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     514: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     517: ifeq          558
     520: aload_0
     521: aload_0
     522: getfield      #35                 // Field schemX:I
     525: aload_0
     526: getfield      #38                 // Field schemY:I
     529: iload         4
     531: iload         5
     533: invokevirtual #1277               // Method rebuildArea:(IIII)V
     536: getstatic     #174                // Field arc/Core.input:Larc/Input;
     539: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     542: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     545: ifne          558
     548: aload_0
     549: iconst_m1
     550: putfield      #35                 // Field schemX:I
     553: aload_0
     554: iconst_m1
     555: putfield      #38                 // Field schemY:I
     558: aload_0
     559: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     562: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     565: ifne          610
     568: getstatic     #174                // Field arc/Core.input:Larc/Input;
     571: getstatic     #1280               // Field mindustry/input/Binding.schematicFlipX:Larc/input/KeyBind;
     574: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     577: ifeq          589
     580: aload_0
     581: aload_0
     582: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     585: iconst_1
     586: invokevirtual #1283               // Method flipPlans:(Larc/struct/Seq;Z)V
     589: getstatic     #174                // Field arc/Core.input:Larc/Input;
     592: getstatic     #1287               // Field mindustry/input/Binding.schematicFlipY:Larc/input/KeyBind;
     595: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     598: ifeq          610
     601: aload_0
     602: aload_0
     603: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     606: iconst_0
     607: invokevirtual #1283               // Method flipPlans:(Larc/struct/Seq;Z)V
     610: aload_0
     611: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     614: ifnull        710
     617: getstatic     #174                // Field arc/Core.input:Larc/Input;
     620: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     623: getfield      #657                // Field arc/math/geom/Vec2.x:F
     626: aload_0
     627: getfield      #1290               // Field buildPlanMouseOffsetX:F
     630: fadd
     631: ldc_w         #1293               // float 8.0f
     634: fdiv
     635: invokestatic  #1294               // Method java/lang/Math.round:(F)I
     638: istore        6
     640: getstatic     #174                // Field arc/Core.input:Larc/Input;
     643: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     646: getfield      #666                // Field arc/math/geom/Vec2.y:F
     649: aload_0
     650: getfield      #1297               // Field buildPlanMouseOffsetY:F
     653: fadd
     654: ldc_w         #1293               // float 8.0f
     657: fdiv
     658: invokestatic  #1294               // Method java/lang/Math.round:(F)I
     661: istore        7
     663: aload_0
     664: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     667: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     670: iload         6
     672: if_icmpne     687
     675: aload_0
     676: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     679: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     682: iload         7
     684: if_icmpeq     710
     687: aload_0
     688: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     691: iload         6
     693: putfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     696: aload_0
     697: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     700: iload         7
     702: putfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     705: aload_0
     706: iconst_1
     707: putfield      #51                 // Field movedPlan:Z
     710: aload_0
     711: getfield      #345                // Field block:Lmindustry/world/Block;
     714: ifnull        727
     717: aload_0
     718: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     721: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
     724: if_acmpeq     735
     727: aload_0
     728: getfield      #346                // Field linePlans:Larc/struct/Seq;
     731: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     734: pop
     735: getstatic     #174                // Field arc/Core.input:Larc/Input;
     738: getstatic     #1300               // Field mindustry/input/Binding.pauseBuilding:Larc/input/KeyBind;
     741: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     744: ifeq          782
     747: aload_0
     748: aload_0
     749: getfield      #119                // Field isBuilding:Z
     752: ifne          759
     755: iconst_1
     756: goto          760
     759: iconst_0
     760: putfield      #119                // Field isBuilding:Z
     763: aload_0
     764: iconst_0
     765: putfield      #1240               // Field buildWasAutoPaused:Z
     768: aload_0
     769: getfield      #119                // Field isBuilding:Z
     772: ifeq          782
     775: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     778: iconst_0
     779: putfield      #1006               // Field mindustry/gen/Player.shooting:Z
     782: aload_0
     783: invokevirtual #302                // Method isPlacing:()Z
     786: ifeq          861
     789: aload_0
     790: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     793: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
     796: if_acmpne     861
     799: iload_2
     800: aload_0
     801: getfield      #1303               // Field lastLineX:I
     804: if_icmpne     839
     807: iload_3
     808: aload_0
     809: getfield      #1306               // Field lastLineY:I
     812: if_icmpne     839
     815: getstatic     #174                // Field arc/Core.input:Larc/Input;
     818: getstatic     #1015               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
     821: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     824: ifne          839
     827: getstatic     #174                // Field arc/Core.input:Larc/Input;
     830: getstatic     #1015               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
     833: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     836: ifeq          861
     839: aload_0
     840: aload_0
     841: getfield      #28                 // Field selectX:I
     844: aload_0
     845: getfield      #32                 // Field selectY:I
     848: invokevirtual #1309               // Method updateLine:(II)V
     851: aload_0
     852: iload_2
     853: putfield      #1303               // Field lastLineX:I
     856: aload_0
     857: iload_3
     858: putfield      #1306               // Field lastLineY:I
     861: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     864: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     867: ifne          963
     870: getstatic     #174                // Field arc/Core.input:Larc/Input;
     873: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
     876: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     879: ifeq          963
     882: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     885: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
     888: ifne          963
     891: aload_0
     892: iload_2
     893: iload_3
     894: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
     897: astore        6
     899: aload         6
     901: ifnull        963
     904: aload_0
     905: getfield      #51                 // Field movedPlan:Z
     908: ifne          963
     911: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     914: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     917: getfield      #1249               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     920: aload         6
     922: iconst_1
     923: invokevirtual #1313               // Method arc/struct/Queue.indexOf:(Ljava/lang/Object;Z)I
     926: istore        7
     928: iload         7
     930: iconst_m1
     931: if_icmpeq     963
     934: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     937: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     940: getfield      #1249               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     943: iload         7
     945: invokevirtual #1317               // Method arc/struct/Queue.removeIndex:(I)Ljava/lang/Object;
     948: pop
     949: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     952: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     955: getfield      #1249               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     958: aload         6
     960: invokevirtual #1319               // Method arc/struct/Queue.addFirst:(Ljava/lang/Object;)V
     963: getstatic     #174                // Field arc/Core.input:Larc/Input;
     966: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
     969: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     972: ifeq          1453
     975: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     978: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
     981: ifne          1453
     984: aload_0
     985: iconst_0
     986: putfield      #1217               // Field tappedOne:Z
     989: aload_0
     990: iload_2
     991: iload_3
     992: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
     995: astore        6
     997: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1000: getstatic     #1009               // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1003: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1006: ifeq          1019
    1009: aload_0
    1010: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1013: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1016: goto          1438
    1019: aload_0
    1020: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1023: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    1026: ifne          1054
    1029: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1032: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    1035: ifeq          1046
    1038: aload_0
    1039: aload_0
    1040: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1043: invokevirtual #1323               // Method flushPlans:(Larc/struct/Seq;)V
    1046: aload_0
    1047: iconst_1
    1048: putfield      #51                 // Field movedPlan:Z
    1051: goto          1438
    1054: aload_0
    1055: invokevirtual #302                // Method isPlacing:()Z
    1058: ifeq          1103
    1061: aload_0
    1062: iload_2
    1063: putfield      #28                 // Field selectX:I
    1066: aload_0
    1067: iload_3
    1068: putfield      #32                 // Field selectY:I
    1071: aload_0
    1072: iload_2
    1073: putfield      #1303               // Field lastLineX:I
    1076: aload_0
    1077: iload_3
    1078: putfield      #1306               // Field lastLineY:I
    1081: aload_0
    1082: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    1085: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1088: aload_0
    1089: aload_0
    1090: getfield      #28                 // Field selectX:I
    1093: aload_0
    1094: getfield      #32                 // Field selectY:I
    1097: invokevirtual #1309               // Method updateLine:(II)V
    1100: goto          1438
    1103: aload         6
    1105: ifnull        1208
    1108: aload         6
    1110: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
    1113: ifne          1208
    1116: aload_0
    1117: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1120: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1123: if_acmpne     1208
    1126: aload         6
    1128: getfield      #1326               // Field mindustry/entities/units/BuildPlan.initialized:Z
    1131: ifne          1208
    1134: aload         6
    1136: getfield      #1329               // Field mindustry/entities/units/BuildPlan.progress:F
    1139: fconst_0
    1140: fcmpg
    1141: ifgt          1208
    1144: aload_0
    1145: aload         6
    1147: putfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    1150: aload_0
    1151: iconst_0
    1152: putfield      #51                 // Field movedPlan:Z
    1155: aload_0
    1156: aload_0
    1157: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    1160: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
    1163: bipush        8
    1165: imul
    1166: i2f
    1167: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1170: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1173: getfield      #657                // Field arc/math/geom/Vec2.x:F
    1176: fsub
    1177: putfield      #1290               // Field buildPlanMouseOffsetX:F
    1180: aload_0
    1181: aload_0
    1182: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    1185: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
    1188: bipush        8
    1190: imul
    1191: i2f
    1192: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1195: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1198: getfield      #666                // Field arc/math/geom/Vec2.y:F
    1201: fsub
    1202: putfield      #1297               // Field buildPlanMouseOffsetY:F
    1205: goto          1438
    1208: aload         6
    1210: ifnull        1229
    1213: aload         6
    1215: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
    1218: ifeq          1229
    1221: aload_0
    1222: iconst_1
    1223: putfield      #41                 // Field deleting:Z
    1226: goto          1438
    1229: aload_0
    1230: getfield      #700                // Field commandMode:Z
    1233: ifeq          1264
    1236: aload_0
    1237: iconst_1
    1238: putfield      #1090               // Field commandRect:Z
    1241: aload_0
    1242: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1245: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
    1248: putfield      #1223               // Field commandRectX:F
    1251: aload_0
    1252: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1255: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
    1258: putfield      #1226               // Field commandRectY:F
    1261: goto          1438
    1264: aload_0
    1265: invokevirtual #1332               // Method checkConfigTap:()Z
    1268: ifne          1419
    1271: aload_1
    1272: ifnull        1419
    1275: aload_0
    1276: aload_1
    1277: invokevirtual #1335               // Method tryRepairDerelict:(Lmindustry/world/Tile;)Z
    1280: ifne          1419
    1283: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1286: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    1289: ifne          1438
    1292: aload_0
    1293: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1296: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1299: getfield      #657                // Field arc/math/geom/Vec2.x:F
    1302: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1305: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1308: getfield      #666                // Field arc/math/geom/Vec2.y:F
    1311: invokevirtual #1339               // Method tryTapPlayer:(FF)Z
    1314: ifne          1438
    1317: aload_0
    1318: aload_1
    1319: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    1322: invokevirtual #1233               // Method tileTapped:(Lmindustry/gen/Building;)Z
    1325: ifne          1438
    1328: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1331: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    1334: invokevirtual #1343               // Method mindustry/gen/Unit.activelyBuilding:()Z
    1337: ifne          1438
    1340: aload_0
    1341: getfield      #933                // Field droppingItem:Z
    1344: ifne          1438
    1347: aload_0
    1348: aload_1
    1349: invokevirtual #1346               // Method tryStopMine:(Lmindustry/world/Tile;)Z
    1352: ifne          1438
    1355: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    1358: ldc_w         #1349               // String doubletapmine
    1361: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
    1364: ifeq          1389
    1367: aload_1
    1368: aload_0
    1369: getfield      #1351               // Field prevSelected:Lmindustry/world/Tile;
    1372: if_acmpne     1397
    1375: aload_0
    1376: getfield      #67                 // Field selectMillis:J
    1379: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
    1382: ldc2_w        #1354               // long 500l
    1385: lcmp
    1386: ifge          1397
    1389: aload_0
    1390: aload_1
    1391: invokevirtual #1356               // Method tryBeginMine:(Lmindustry/world/Tile;)Z
    1394: ifne          1438
    1397: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1400: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
    1403: ifne          1438
    1406: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1409: aload_0
    1410: getfield      #45                 // Field shouldShoot:Z
    1413: putfield      #1006               // Field mindustry/gen/Player.shooting:Z
    1416: goto          1438
    1419: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1422: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
    1425: ifne          1438
    1428: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1431: aload_0
    1432: getfield      #45                 // Field shouldShoot:Z
    1435: putfield      #1006               // Field mindustry/gen/Player.shooting:Z
    1438: aload_0
    1439: invokestatic  #873                // Method arc/util/Time.millis:()J
    1442: putfield      #67                 // Field selectMillis:J
    1445: aload_0
    1446: aload_1
    1447: putfield      #1351               // Field prevSelected:Lmindustry/world/Tile;
    1450: goto          1616
    1453: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1456: getstatic     #1246               // Field mindustry/input/Binding.deselect:Larc/input/KeyBind;
    1459: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1462: ifeq          1487
    1465: aload_0
    1466: invokevirtual #302                // Method isPlacing:()Z
    1469: ifeq          1487
    1472: aload_0
    1473: aconst_null
    1474: putfield      #345                // Field block:Lmindustry/world/Block;
    1477: aload_0
    1478: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1481: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1484: goto          1616
    1487: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1490: getstatic     #1246               // Field mindustry/input/Binding.deselect:Larc/input/KeyBind;
    1493: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1496: ifeq          1525
    1499: aload_0
    1500: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1503: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    1506: ifne          1525
    1509: aload_0
    1510: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1513: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1516: pop
    1517: aload_0
    1518: aconst_null
    1519: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
    1522: goto          1616
    1525: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1528: getstatic     #1009               // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1531: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1534: ifeq          1616
    1537: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1540: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    1543: ifne          1616
    1546: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1549: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    1552: ifeq          1616
    1555: aload_0
    1556: getfield      #700                // Field commandMode:Z
    1559: ifne          1616
    1562: aload_0
    1563: iconst_0
    1564: putfield      #41                 // Field deleting:Z
    1567: aload_0
    1568: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    1571: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1574: aload_0
    1575: aload_0
    1576: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1579: invokevirtual #178                // Method arc/Input.mouseX:()I
    1582: i2f
    1583: invokevirtual #184                // Method tileX:(F)I
    1586: putfield      #28                 // Field selectX:I
    1589: aload_0
    1590: aload_0
    1591: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1594: invokevirtual #188                // Method arc/Input.mouseY:()I
    1597: i2f
    1598: invokevirtual #191                // Method tileY:(F)I
    1601: putfield      #32                 // Field selectY:I
    1604: aload_0
    1605: iload         4
    1607: putfield      #35                 // Field schemX:I
    1610: aload_0
    1611: iload         5
    1613: putfield      #38                 // Field schemY:I
    1616: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1619: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    1622: ifne          1700
    1625: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1628: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    1631: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1634: ifeq          1700
    1637: aload_0
    1638: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1641: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1644: if_acmpne     1700
    1647: aload_0
    1648: invokevirtual #302                // Method isPlacing:()Z
    1651: ifne          1700
    1654: aload_0
    1655: getfield      #41                 // Field deleting:Z
    1658: ifeq          1700
    1661: aload_0
    1662: iload_2
    1663: iload_3
    1664: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
    1667: astore        6
    1669: aload         6
    1671: ifnull        1697
    1674: aload         6
    1676: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
    1679: ifeq          1697
    1682: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1685: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    1688: invokevirtual #1359               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
    1691: aload         6
    1693: invokevirtual #1362               // Method arc/struct/Queue.remove:(Ljava/lang/Object;)Z
    1696: pop
    1697: goto          1705
    1700: aload_0
    1701: iconst_0
    1702: putfield      #41                 // Field deleting:Z
    1705: aload_0
    1706: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1709: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    1712: if_acmpne     1810
    1715: aload_0
    1716: getfield      #345                // Field block:Lmindustry/world/Block;
    1719: ifnull        1810
    1722: aload_0
    1723: getfield      #1364               // Field overrideLineRotation:Z
    1726: ifne          1815
    1729: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1732: getstatic     #1015               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    1735: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1738: ifne          1815
    1741: aload_0
    1742: getfield      #28                 // Field selectX:I
    1745: iload_2
    1746: if_icmpne     1757
    1749: aload_0
    1750: getfield      #32                 // Field selectY:I
    1753: iload_3
    1754: if_icmpeq     1815
    1757: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1760: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    1763: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    1766: f2i
    1767: ifeq          1815
    1770: aload_0
    1771: aload_0
    1772: getfield      #28                 // Field selectX:I
    1775: i2f
    1776: aload_0
    1777: getfield      #32                 // Field selectY:I
    1780: i2f
    1781: iload_2
    1782: i2f
    1783: iload_3
    1784: i2f
    1785: invokestatic  #1367               // Method arc/math/Angles.angle:(FFFF)F
    1788: ldc_w         #1373               // float 45.0f
    1791: fadd
    1792: ldc_w         #1374               // float 90.0f
    1795: fdiv
    1796: f2i
    1797: iconst_4
    1798: irem
    1799: putfield      #359                // Field rotation:I
    1802: aload_0
    1803: iconst_1
    1804: putfield      #1364               // Field overrideLineRotation:Z
    1807: goto          1815
    1810: aload_0
    1811: iconst_0
    1812: putfield      #1364               // Field overrideLineRotation:Z
    1815: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1818: getstatic     #1009               // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1821: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    1824: ifeq          1881
    1827: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1830: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
    1833: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1836: ifeq          1881
    1839: aload_0
    1840: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1843: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    1846: if_acmpne     1881
    1849: aload_0
    1850: getstatic     #1131               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
    1853: aload_0
    1854: getfield      #35                 // Field schemX:I
    1857: aload_0
    1858: getfield      #38                 // Field schemY:I
    1861: iload         4
    1863: iload         5
    1865: invokevirtual #1269               // Method mindustry/game/Schematics.create:(IIII)Lmindustry/game/Schematic;
    1868: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
    1871: aload_0
    1872: iconst_m1
    1873: putfield      #35                 // Field schemX:I
    1876: aload_0
    1877: iconst_m1
    1878: putfield      #38                 // Field schemY:I
    1881: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1884: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    1887: ifne          2207
    1890: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1893: getstatic     #1009               // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1896: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    1899: ifne          1914
    1902: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1905: getstatic     #895                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    1908: invokevirtual #1087               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    1911: ifeq          2207
    1914: aload_0
    1915: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1918: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    1921: if_acmpne     1983
    1924: aload_0
    1925: getfield      #345                // Field block:Lmindustry/world/Block;
    1928: ifnull        1983
    1931: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1934: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
    1937: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1940: ifeq          1954
    1943: aload_0
    1944: aload_0
    1945: getfield      #346                // Field linePlans:Larc/struct/Seq;
    1948: invokevirtual #1375               // Method flushPlansReverse:(Larc/struct/Seq;)V
    1951: goto          1962
    1954: aload_0
    1955: aload_0
    1956: getfield      #346                // Field linePlans:Larc/struct/Seq;
    1959: invokevirtual #1323               // Method flushPlans:(Larc/struct/Seq;)V
    1962: aload_0
    1963: getfield      #346                // Field linePlans:Larc/struct/Seq;
    1966: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1969: pop
    1970: new           #1378               // class mindustry/game/EventType$LineConfirmEvent
    1973: dup
    1974: invokespecial #1380               // Method mindustry/game/EventType$LineConfirmEvent."<init>":()V
    1977: invokestatic  #1381               // Method arc/Events.fire:(Ljava/lang/Object;)V
    1980: goto          2047
    1983: aload_0
    1984: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1987: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    1990: if_acmpne     2047
    1993: aload_0
    1994: aload_0
    1995: getfield      #28                 // Field selectX:I
    1998: aload_0
    1999: getfield      #32                 // Field selectY:I
    2002: iload_2
    2003: iload_3
    2004: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2007: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
    2010: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2013: ifne          2021
    2016: bipush        100
    2018: goto          2024
    2021: getstatic     #213                // Field mindustry/Vars.maxSchematicSize:I
    2024: invokevirtual #1383               // Method removeSelection:(IIIII)V
    2027: aload_0
    2028: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
    2031: ifnull        2047
    2034: aload_0
    2035: aload_0
    2036: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
    2039: invokevirtual #1273               // Method useSchematic:(Lmindustry/game/Schematic;)V
    2042: aload_0
    2043: aconst_null
    2044: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
    2047: aload_0
    2048: iconst_m1
    2049: putfield      #28                 // Field selectX:I
    2052: aload_0
    2053: iconst_m1
    2054: putfield      #32                 // Field selectY:I
    2057: aload_0
    2058: aload_1
    2059: ifnonnull     2066
    2062: aconst_null
    2063: goto          2070
    2066: aload_1
    2067: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2070: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2073: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2076: getfield      #657                // Field arc/math/geom/Vec2.x:F
    2079: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2082: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2085: getfield      #666                // Field arc/math/geom/Vec2.y:F
    2088: invokevirtual #1386               // Method tryDropItems:(Lmindustry/gen/Building;FF)V
    2091: aload_0
    2092: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2095: ifnull        2200
    2098: aload_0
    2099: aload_0
    2100: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2103: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
    2106: aload_0
    2107: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2110: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
    2113: aload_0
    2114: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2117: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
    2120: getfield      #279                // Field mindustry/world/Block.size:I
    2123: aload_0
    2124: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2127: invokevirtual #282                // Method getPlan:(IIILmindustry/entities/units/BuildPlan;)Lmindustry/entities/units/BuildPlan;
    2130: ifnull        2151
    2133: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2136: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    2139: invokevirtual #1359               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
    2142: aload_0
    2143: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2146: iconst_1
    2147: invokevirtual #1390               // Method arc/struct/Queue.remove:(Ljava/lang/Object;Z)Z
    2150: pop
    2151: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2154: invokevirtual #1069               // Method arc/Input.ctrl:()Z
    2157: ifeq          2188
    2160: aload_0
    2161: getfield      #1393               // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
    2164: invokevirtual #1397               // Method mindustry/ui/fragments/BlockInventoryFragment.hide:()V
    2167: aload_0
    2168: getfield      #1402               // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
    2171: invokevirtual #1405               // Method mindustry/ui/fragments/BlockConfigFragment.hideConfig:()V
    2174: aload_0
    2175: getfield      #1410               // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
    2178: aload_0
    2179: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2182: invokevirtual #1414               // Method mindustry/ui/fragments/PlanConfigFragment.showConfig:(Lmindustry/entities/units/BuildPlan;)V
    2185: goto          2195
    2188: aload_0
    2189: getfield      #1410               // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
    2192: invokevirtual #1419               // Method mindustry/ui/fragments/PlanConfigFragment.hide:()V
    2195: aload_0
    2196: aconst_null
    2197: putfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2200: aload_0
    2201: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2204: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2207: aload_0
    2208: invokevirtual #302                // Method isPlacing:()Z
    2211: ifne          2231
    2214: aload_0
    2215: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2218: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    2221: if_acmpne     2231
    2224: aload_0
    2225: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2228: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2231: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2234: getfield      #1006               // Field mindustry/gen/Player.shooting:Z
    2237: ifeq          2254
    2240: aload_0
    2241: invokevirtual #1420               // Method canShoot:()Z
    2244: ifne          2254
    2247: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2250: iconst_0
    2251: putfield      #1006               // Field mindustry/gen/Player.shooting:Z
    2254: aload_0
    2255: invokevirtual #302                // Method isPlacing:()Z
    2258: ifeq          2295
    2261: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2264: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    2267: ifeq          2295
    2270: aload_0
    2271: getstatic     #1423               // Field arc/Graphics$Cursor$SystemCursor.hand:Larc/Graphics$Cursor$SystemCursor;
    2274: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2277: aload_0
    2278: aload_0
    2279: getfield      #1426               // Field selectScale:F
    2282: fconst_1
    2283: ldc_w         #1429               // float 0.2f
    2286: invokestatic  #1430               // Method arc/math/Mathf.lerpDelta:(FFF)F
    2289: putfield      #1426               // Field selectScale:F
    2292: goto          2300
    2295: aload_0
    2296: fconst_0
    2297: putfield      #1426               // Field selectScale:F
    2300: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2303: getstatic     #1015               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    2306: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2309: ifne          2461
    2312: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2315: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2318: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2321: f2i
    2322: invokestatic  #1432               // Method java/lang/Math.abs:(I)I
    2325: ifle          2461
    2328: aload_0
    2329: aload_0
    2330: getfield      #359                // Field rotation:I
    2333: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2336: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2339: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2342: f2i
    2343: iadd
    2344: iconst_4
    2345: invokestatic  #1434               // Method arc/math/Mathf.mod:(II)I
    2348: putfield      #359                // Field rotation:I
    2351: aload_0
    2352: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2355: ifnull        2387
    2358: aload_0
    2359: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2362: aload_0
    2363: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2366: getfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
    2369: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2372: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2375: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2378: f2i
    2379: iadd
    2380: iconst_4
    2381: invokestatic  #1434               // Method arc/math/Mathf.mod:(II)I
    2384: putfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
    2387: aload_0
    2388: invokevirtual #302                // Method isPlacing:()Z
    2391: ifeq          2419
    2394: aload_0
    2395: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2398: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    2401: if_acmpne     2419
    2404: aload_0
    2405: aload_0
    2406: getfield      #28                 // Field selectX:I
    2409: aload_0
    2410: getfield      #32                 // Field selectY:I
    2413: invokevirtual #1309               // Method updateLine:(II)V
    2416: goto          2461
    2419: aload_0
    2420: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2423: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    2426: ifne          2461
    2429: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2432: getfield      #593                // Field mindustry/core/UI.chatfrag:Lmindustry/ui/fragments/ChatFragment;
    2435: invokevirtual #597                // Method mindustry/ui/fragments/ChatFragment.shown:()Z
    2438: ifne          2461
    2441: aload_0
    2442: aload_0
    2443: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2446: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2449: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2452: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2455: invokestatic  #1438               // Method arc/math/Mathf.sign:(F)I
    2458: invokevirtual #1441               // Method rotatePlans:(Larc/struct/Seq;I)V
    2461: aload_0
    2462: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2465: invokevirtual #178                // Method arc/Input.mouseX:()I
    2468: i2f
    2469: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2472: invokevirtual #188                // Method arc/Input.mouseY:()I
    2475: i2f
    2476: invokevirtual #1220               // Method tileAt:(FF)Lmindustry/world/Tile;
    2479: astore        6
    2481: aload_0
    2482: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2485: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2488: aload         6
    2490: ifnull        2982
    2493: aload         6
    2495: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2498: ifnull        2530
    2501: aload         6
    2503: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2506: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2509: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2512: invokevirtual #1445               // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
    2515: ifeq          2530
    2518: aload_0
    2519: aload         6
    2521: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2524: invokevirtual #1449               // Method mindustry/gen/Building.getCursor:()Larc/Graphics$Cursor;
    2527: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2530: aload_0
    2531: aload         6
    2533: invokevirtual #1453               // Method canRepairDerelict:(Lmindustry/world/Tile;)Z
    2536: ifeq          2570
    2539: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2542: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    2545: ifne          2570
    2548: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2551: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    2554: invokevirtual #1456               // Method mindustry/gen/Unit.canBuild:()Z
    2557: ifeq          2570
    2560: aload_0
    2561: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2564: getfield      #1459               // Field mindustry/core/UI.repairCursor:Larc/Graphics$Cursor;
    2567: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2570: aload_0
    2571: invokevirtual #302                // Method isPlacing:()Z
    2574: ifeq          2586
    2577: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2580: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    2583: ifne          2596
    2586: aload_0
    2587: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2590: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    2593: ifne          2603
    2596: aload_0
    2597: getstatic     #1423               // Field arc/Graphics$Cursor$SystemCursor.hand:Larc/Graphics$Cursor$SystemCursor;
    2600: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2603: aload_0
    2604: invokevirtual #302                // Method isPlacing:()Z
    2607: ifne          2629
    2610: aload_0
    2611: aload         6
    2613: invokevirtual #1462               // Method canMine:(Lmindustry/world/Tile;)Z
    2616: ifeq          2629
    2619: aload_0
    2620: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2623: getfield      #1465               // Field mindustry/core/UI.drillCursor:Larc/Graphics$Cursor;
    2626: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2629: aload_0
    2630: getfield      #700                // Field commandMode:Z
    2633: ifeq          2803
    2636: aload_0
    2637: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    2640: invokevirtual #1468               // Method arc/struct/Seq.any:()Z
    2643: ifeq          2803
    2646: aload         6
    2648: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2651: ifnull        2692
    2654: aload         6
    2656: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2659: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2662: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2665: invokevirtual #1471               // Method mindustry/gen/Building.inFogTo:(Lmindustry/game/Team;)Z
    2668: ifne          2692
    2671: aload         6
    2673: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2676: getfield      #1474               // Field mindustry/gen/Building.team:Lmindustry/game/Team;
    2679: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2682: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2685: if_acmpeq     2692
    2688: iconst_1
    2689: goto          2693
    2692: iconst_0
    2693: istore        7
    2695: iload         7
    2697: ifne          2739
    2700: aload_0
    2701: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2704: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
    2707: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2710: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
    2713: invokevirtual #1476               // Method selectedEnemyUnit:(FF)Lmindustry/gen/Unit;
    2716: astore        8
    2718: aload         8
    2720: ifnull        2739
    2723: aload_0
    2724: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    2727: aload         8
    2729: invokedynamic #1480,  0           // InvokeDynamic #17:get:(Lmindustry/gen/Unit;)Larc/func/Boolf;
    2734: invokevirtual #1483               // Method arc/struct/Seq.contains:(Larc/func/Boolf;)Z
    2737: istore        7
    2739: iload         7
    2741: ifeq          2754
    2744: aload_0
    2745: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2748: getfield      #1487               // Field mindustry/core/UI.targetCursor:Larc/Graphics$Cursor;
    2751: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2754: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2757: getstatic     #1490               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
    2760: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2763: ifeq          2803
    2766: getstatic     #1490               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
    2769: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
    2772: getfield      #1493               // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
    2775: getfield      #1497               // Field arc/input/KeyCode.type:Larc/input/KeyCode$KeyType;
    2778: getstatic     #1502               // Field arc/input/KeyCode$KeyType.mouse:Larc/input/KeyCode$KeyType;
    2781: if_acmpeq     2803
    2784: aload_0
    2785: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2788: invokevirtual #178                // Method arc/Input.mouseX:()I
    2791: i2f
    2792: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2795: invokevirtual #188                // Method arc/Input.mouseY:()I
    2798: i2f
    2799: iconst_1
    2800: invokevirtual #1507               // Method commandTap:(FFZ)V
    2803: aload_0
    2804: aload         6
    2806: getfield      #1511               // Field mindustry/world/Tile.x:S
    2809: aload         6
    2811: getfield      #1514               // Field mindustry/world/Tile.y:S
    2814: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
    2817: ifnull        2837
    2820: aload_0
    2821: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2824: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2827: if_acmpne     2837
    2830: aload_0
    2831: getstatic     #1423               // Field arc/Graphics$Cursor$SystemCursor.hand:Larc/Graphics$Cursor$SystemCursor;
    2834: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2837: aload_0
    2838: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2841: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2844: getfield      #657                // Field arc/math/geom/Vec2.x:F
    2847: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2850: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2853: getfield      #666                // Field arc/math/geom/Vec2.y:F
    2856: invokevirtual #1516               // Method canTapPlayer:(FF)Z
    2859: ifeq          2872
    2862: aload_0
    2863: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2866: getfield      #1519               // Field mindustry/core/UI.unloadCursor:Larc/Graphics$Cursor;
    2869: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2872: aload         6
    2874: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2877: ifnull        2982
    2880: aload         6
    2882: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2885: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2888: invokevirtual #1522               // Method mindustry/world/Tile.interactable:(Lmindustry/game/Team;)Z
    2891: ifeq          2982
    2894: aload_0
    2895: invokevirtual #302                // Method isPlacing:()Z
    2898: ifne          2982
    2901: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2904: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2907: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2910: invokestatic  #578                // Method java/lang/Math.abs:(F)F
    2913: fconst_0
    2914: fcmpl
    2915: ifle          2982
    2918: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2921: getstatic     #1031               // Field mindustry/input/Binding.rotatePlaced:Larc/input/KeyBind;
    2924: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2927: ifeq          2982
    2930: aload         6
    2932: invokevirtual #314                // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
    2935: getfield      #260                // Field mindustry/world/Block.rotate:Z
    2938: ifeq          2982
    2941: aload         6
    2943: invokevirtual #314                // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
    2946: getfield      #1523               // Field mindustry/world/Block.quickRotate:Z
    2949: ifeq          2982
    2952: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2955: aload         6
    2957: getfield      #1229               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2960: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2963: getstatic     #1034               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2966: invokevirtual #1028               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2969: fconst_0
    2970: fcmpl
    2971: ifle          2978
    2974: iconst_1
    2975: goto          2979
    2978: iconst_0
    2979: invokestatic  #1526               // Method mindustry/gen/Call.rotateBlock:(Lmindustry/gen/Player;Lmindustry/gen/Building;Z)V
    2982: return

  public boolean tap(float, float, int, arc.input.KeyCode);
    Code:
       0: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
       3: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
       6: ifne          16
       9: aload_0
      10: getfield      #700                // Field commandMode:Z
      13: ifne          18
      16: iconst_0
      17: ireturn
      18: aload_0
      19: iconst_1
      20: putfield      #1217               // Field tappedOne:Z
      23: aload         4
      25: getstatic     #1530               // Field arc/input/KeyCode.mouseLeft:Larc/input/KeyCode;
      28: if_acmpne     47
      31: iload_3
      32: iconst_2
      33: if_icmplt     43
      36: aload_0
      37: invokevirtual #1533               // Method selectTypedUnits:()V
      40: goto          47
      43: aload_0
      44: invokevirtual #1536               // Method tapCommandUnit:()V
      47: aload_0
      48: fload_1
      49: fload_2
      50: iload_3
      51: aload         4
      53: invokespecial #1539               // Method mindustry/input/InputHandler.tap:(FFILarc/input/KeyCode;)Z
      56: ireturn

  public boolean touchDown(float, float, int, arc.input.KeyCode);
    Code:
       0: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
       3: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
       6: ifne          16
       9: aload_0
      10: getfield      #700                // Field commandMode:Z
      13: ifne          18
      16: iconst_0
      17: ireturn
      18: aload         4
      20: getstatic     #1543               // Field arc/input/KeyCode.mouseRight:Larc/input/KeyCode;
      23: if_acmpne     32
      26: aload_0
      27: fload_1
      28: fload_2
      29: invokevirtual #1546               // Method commandTap:(FF)V
      32: aload         4
      34: getstatic     #1490               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
      37: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      40: getfield      #1493               // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
      43: if_acmpne     71
      46: getstatic     #174                // Field arc/Core.input:Larc/Input;
      49: getstatic     #1490               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
      52: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      55: getfield      #1549               // Field arc/input/KeyBind$Axis.modifiers:I
      58: invokevirtual #1552               // Method arc/Input.matchModifiers:(I)Z
      61: ifeq          71
      64: aload_0
      65: fload_1
      66: fload_2
      67: iconst_1
      68: invokevirtual #1507               // Method commandTap:(FFZ)V
      71: aload_0
      72: fload_1
      73: fload_2
      74: iload_3
      75: aload         4
      77: invokespecial #1556               // Method mindustry/input/InputHandler.touchDown:(FFILarc/input/KeyCode;)Z
      80: ireturn

  public boolean selectedBlock();
    Code:
       0: aload_0
       1: invokevirtual #302                // Method isPlacing:()Z
       4: ifeq          21
       7: aload_0
       8: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
      11: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
      14: if_acmpeq     21
      17: iconst_1
      18: goto          22
      21: iconst_0
      22: ireturn

  public float getMouseX();
    Code:
       0: getstatic     #174                // Field arc/Core.input:Larc/Input;
       3: invokevirtual #178                // Method arc/Input.mouseX:()I
       6: i2f
       7: freturn

  public float getMouseY();
    Code:
       0: getstatic     #174                // Field arc/Core.input:Larc/Input;
       3: invokevirtual #188                // Method arc/Input.mouseY:()I
       6: i2f
       7: freturn

  public void updateState();
    Code:
       0: aload_0
       1: invokespecial #1559               // Method mindustry/input/InputHandler.updateState:()V
       4: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       7: invokevirtual #1003               // Method mindustry/core/GameState.isMenu:()Z
      10: ifeq          48
      13: aload_0
      14: aconst_null
      15: putfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
      18: aload_0
      19: iconst_0
      20: putfield      #933                // Field droppingItem:Z
      23: aload_0
      24: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
      27: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
      30: aload_0
      31: aconst_null
      32: putfield      #345                // Field block:Lmindustry/world/Block;
      35: aload_0
      36: aconst_null
      37: putfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
      40: aload_0
      41: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      44: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      47: pop
      48: return

  public void panCamera(arc.math.geom.Vec2);
    Code:
       0: aload_0
       1: invokevirtual #480                // Method locked:()Z
       4: ifne          23
       7: aload_0
       8: iconst_1
       9: putfield      #48                 // Field panning:Z
      12: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
      15: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
      18: aload_1
      19: invokevirtual #545                // Method arc/math/geom/Vec2.set:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
      22: pop
      23: return

  protected void updateMovement(mindustry.gen.Unit);
    Code:
       0: aload_1
       1: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
       4: getfield      #1562               // Field mindustry/type/UnitType.omniMovement:Z
       7: istore_2
       8: aload_1
       9: invokevirtual #1565               // Method mindustry/gen/Unit.speed:()F
      12: fstore_3
      13: getstatic     #174                // Field arc/Core.input:Larc/Input;
      16: getstatic     #571                // Field mindustry/input/Binding.moveX:Larc/input/KeyBind;
      19: invokevirtual #574                // Method arc/Input.axis:(Larc/input/KeyBind;)F
      22: fstore        4
      24: getstatic     #174                // Field arc/Core.input:Larc/Input;
      27: getstatic     #584                // Field mindustry/input/Binding.moveY:Larc/input/KeyBind;
      30: invokevirtual #574                // Method arc/Input.axis:(Larc/input/KeyBind;)F
      33: fstore        5
      35: aload_1
      36: instanceof    #1568               // class mindustry/gen/Mechc
      39: ifeq          53
      42: aload_1
      43: invokevirtual #1570               // Method mindustry/gen/Unit.isFlying:()Z
      46: ifeq          53
      49: iconst_1
      50: goto          54
      53: iconst_0
      54: istore        6
      56: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      59: ldc_w         #489                // String detach-camera
      62: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      65: ifeq          145
      68: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
      71: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
      74: astore        7
      76: aload_0
      77: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
      80: aload         7
      82: invokevirtual #545                // Method arc/math/geom/Vec2.set:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
      85: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      88: invokevirtual #1573               // Method arc/math/geom/Vec2.sub:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
      91: fload_3
      92: invokevirtual #1577               // Method arc/math/geom/Vec2.limit:(F)Larc/math/geom/Vec2;
      95: pop
      96: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      99: aload         7
     101: ldc           #63                 // float 15.0f
     103: invokevirtual #1580               // Method mindustry/gen/Player.within:(Larc/math/geom/Position;F)Z
     106: ifeq          142
     109: aload_0
     110: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
     113: invokevirtual #605                // Method arc/math/geom/Vec2.setZero:()Larc/math/geom/Vec2;
     116: pop
     117: aload_1
     118: getfield      #1584               // Field mindustry/gen/Unit.vel:Larc/math/geom/Vec2;
     121: getstatic     #1587               // Field arc/math/geom/Vec2.ZERO:Larc/math/geom/Vec2;
     124: aload_1
     125: invokevirtual #1565               // Method mindustry/gen/Unit.speed:()F
     128: aload_1
     129: invokevirtual #1590               // Method mindustry/gen/Unit.type:()Lmindustry/type/UnitType;
     132: getfield      #1593               // Field mindustry/type/UnitType.accel:F
     135: fmul
     136: fconst_2
     137: fdiv
     138: invokevirtual #1596               // Method arc/math/geom/Vec2.approachDelta:(Larc/math/geom/Vec2;F)Larc/math/geom/Vec2;
     141: pop
     142: goto          208
     145: aload_0
     146: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
     149: fload         4
     151: fload         5
     153: invokevirtual #871                // Method arc/math/geom/Vec2.set:(FF)Larc/math/geom/Vec2;
     156: invokevirtual #612                // Method arc/math/geom/Vec2.nor:()Larc/math/geom/Vec2;
     159: fload_3
     160: invokevirtual #615                // Method arc/math/geom/Vec2.scl:(F)Larc/math/geom/Vec2;
     163: pop
     164: getstatic     #174                // Field arc/Core.input:Larc/Input;
     167: getstatic     #587                // Field mindustry/input/Binding.mouseMove:Larc/input/KeyBind;
     170: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     173: ifeq          208
     176: aload_0
     177: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
     180: getstatic     #174                // Field arc/Core.input:Larc/Input;
     183: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     186: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     189: invokevirtual #1573               // Method arc/math/geom/Vec2.sub:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
     192: ldc_w         #1600               // float 0.04f
     195: fload_3
     196: fmul
     197: invokevirtual #615                // Method arc/math/geom/Vec2.scl:(F)Larc/math/geom/Vec2;
     200: invokevirtual #619                // Method arc/math/geom/Vec2.add:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
     203: fload_3
     204: invokevirtual #1577               // Method arc/math/geom/Vec2.limit:(F)Larc/math/geom/Vec2;
     207: pop
     208: iload_2
     209: ifeq          250
     212: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     215: getfield      #1006               // Field mindustry/gen/Player.shooting:Z
     218: ifeq          250
     221: aload_1
     222: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     225: invokevirtual #1601               // Method mindustry/type/UnitType.hasWeapons:()Z
     228: ifeq          250
     231: aload_1
     232: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     235: getfield      #1604               // Field mindustry/type/UnitType.faceTarget:Z
     238: ifeq          250
     241: iload         6
     243: ifne          250
     246: iconst_1
     247: goto          251
     250: iconst_0
     251: istore        7
     253: iload         7
     255: ifeq          277
     258: aload_1
     259: aload_1
     260: aload_1
     261: getfield      #1607               // Field mindustry/gen/Unit.aimX:F
     264: aload_1
     265: getfield      #1610               // Field mindustry/gen/Unit.aimY:F
     268: invokevirtual #1613               // Method mindustry/gen/Unit.angleTo:(FF)F
     271: invokevirtual #1617               // Method mindustry/gen/Unit.lookAt:(F)V
     274: goto          285
     277: aload_1
     278: aload_1
     279: invokevirtual #1620               // Method mindustry/gen/Unit.prefRotation:()F
     282: invokevirtual #1617               // Method mindustry/gen/Unit.lookAt:(F)V
     285: aload_1
     286: aload_0
     287: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
     290: invokevirtual #1623               // Method mindustry/gen/Unit.movePref:(Larc/math/geom/Vec2;)V
     293: aload_1
     294: getstatic     #174                // Field arc/Core.input:Larc/Input;
     297: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
     300: getstatic     #174                // Field arc/Core.input:Larc/Input;
     303: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
     306: iconst_1
     307: invokevirtual #1627               // Method mindustry/gen/Unit.aim:(FFZ)V
     310: aload_1
     311: iconst_1
     312: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     315: getfield      #1006               // Field mindustry/gen/Player.shooting:Z
     318: ifeq          330
     321: iload         6
     323: ifne          330
     326: iconst_1
     327: goto          331
     330: iconst_0
     331: invokevirtual #1630               // Method mindustry/gen/Unit.controlWeapons:(ZZ)V
     334: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     337: getstatic     #174                // Field arc/Core.input:Larc/Input;
     340: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
     343: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     346: putfield      #1634               // Field mindustry/gen/Player.boosting:Z
     349: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     352: aload_1
     353: invokevirtual #1637               // Method mindustry/gen/Unit.aimX:()F
     356: putfield      #1639               // Field mindustry/gen/Player.mouseX:F
     359: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     362: aload_1
     363: invokevirtual #1641               // Method mindustry/gen/Unit.aimY:()F
     366: putfield      #1643               // Field mindustry/gen/Player.mouseY:F
     369: aload_1
     370: instanceof    #783                // class mindustry/gen/Payloadc
     373: ifeq          524
     376: getstatic     #174                // Field arc/Core.input:Larc/Input;
     379: getstatic     #1645               // Field mindustry/input/Binding.pickupCargo:Larc/input/KeyBind;
     382: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     385: ifeq          399
     388: aload_0
     389: invokevirtual #1648               // Method tryPickupPayload:()V
     392: aload_0
     393: invokestatic  #873                // Method arc/util/Time.millis:()J
     396: putfield      #1651               // Field lastPayloadKeyTapMillis:J
     399: getstatic     #174                // Field arc/Core.input:Larc/Input;
     402: getstatic     #1645               // Field mindustry/input/Binding.pickupCargo:Larc/input/KeyBind;
     405: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     408: ifeq          450
     411: aload_0
     412: getfield      #1654               // Field lastPayloadKeyHoldMillis:J
     415: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     418: ldc2_w        #1657               // long 20l
     421: lcmp
     422: ifle          450
     425: aload_0
     426: getfield      #1651               // Field lastPayloadKeyTapMillis:J
     429: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     432: ldc2_w        #1659               // long 200l
     435: lcmp
     436: ifle          450
     439: aload_0
     440: invokevirtual #1648               // Method tryPickupPayload:()V
     443: aload_0
     444: invokestatic  #873                // Method arc/util/Time.millis:()J
     447: putfield      #1654               // Field lastPayloadKeyHoldMillis:J
     450: getstatic     #174                // Field arc/Core.input:Larc/Input;
     453: getstatic     #1661               // Field mindustry/input/Binding.dropCargo:Larc/input/KeyBind;
     456: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     459: ifeq          473
     462: aload_0
     463: invokevirtual #1664               // Method tryDropPayload:()V
     466: aload_0
     467: invokestatic  #873                // Method arc/util/Time.millis:()J
     470: putfield      #1651               // Field lastPayloadKeyTapMillis:J
     473: getstatic     #174                // Field arc/Core.input:Larc/Input;
     476: getstatic     #1661               // Field mindustry/input/Binding.dropCargo:Larc/input/KeyBind;
     479: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     482: ifeq          524
     485: aload_0
     486: getfield      #1654               // Field lastPayloadKeyHoldMillis:J
     489: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     492: ldc2_w        #1657               // long 20l
     495: lcmp
     496: ifle          524
     499: aload_0
     500: getfield      #1651               // Field lastPayloadKeyTapMillis:J
     503: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     506: ldc2_w        #1659               // long 200l
     509: lcmp
     510: ifle          524
     513: aload_0
     514: invokevirtual #1664               // Method tryDropPayload:()V
     517: aload_0
     518: invokestatic  #873                // Method arc/util/Time.millis:()J
     521: putfield      #1654               // Field lastPayloadKeyHoldMillis:J
     524: return

  private static boolean lambda$pollInputPlayer$27(mindustry.gen.Unit, mindustry.gen.Unit);
    Code:
       0: aload_1
       1: aload_0
       2: invokevirtual #1667               // Method mindustry/gen/Unit.canTarget:(Lmindustry/gen/Teamc;)Z
       5: ireturn

  private static void lambda$pollInputPlayer$26(int, int, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_2
       1: dup
       2: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
       5: iload_0
       6: iadd
       7: putfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
      10: aload_2
      11: dup
      12: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
      15: iload_1
      16: iadd
      17: putfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
      20: return

  private static boolean lambda$buildPlacementUI$25();
    Code:
       0: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       3: invokevirtual #950                // Method mindustry/core/GameState.isCampaign:()Z
       6: ireturn

  private static void lambda$buildPlacementUI$24();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #953                // Field mindustry/core/UI.planet:Lmindustry/ui/dialogs/PlanetDialog;
       6: invokevirtual #1671               // Method mindustry/ui/dialogs/PlanetDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static boolean lambda$buildPlacementUI$23();
    Code:
       0: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       3: invokevirtual #950                // Method mindustry/core/GameState.isCampaign:()Z
       6: ireturn

  private static void lambda$buildPlacementUI$22();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #963                // Field mindustry/core/UI.research:Lmindustry/ui/dialogs/ResearchDialog;
       6: invokevirtual #1675               // Method mindustry/ui/dialogs/ResearchDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static void lambda$buildPlacementUI$21();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #1676               // Field mindustry/core/UI.database:Lmindustry/ui/dialogs/DatabaseDialog;
       6: invokevirtual #1680               // Method mindustry/ui/dialogs/DatabaseDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static void lambda$buildPlacementUI$20();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #972                // Field mindustry/core/UI.schematics:Lmindustry/ui/dialogs/SchematicsDialog;
       6: invokevirtual #1683               // Method mindustry/ui/dialogs/SchematicsDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static void lambda$update$19(java.lang.String);
    Code:
       0: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: getstatic     #174                // Field arc/Core.input:Larc/Input;
       6: invokevirtual #1049               // Method arc/Input.mouseWorldX:()F
       9: getstatic     #174                // Field arc/Core.input:Larc/Input;
      12: invokevirtual #1053               // Method arc/Input.mouseWorldY:()F
      15: aload_0
      16: invokestatic  #1684               // Method mindustry/core/UI.formatIcons:(Ljava/lang/String;)Ljava/lang/String;
      19: invokestatic  #1083               // Method mindustry/gen/Call.pingLocation:(Lmindustry/gen/Player;FFLjava/lang/String;)V
      22: return

  private void lambda$update$18(int);
    Code:
       0: getstatic     #831                // Field mindustry/gen/Groups.unit:Lmindustry/entities/EntityGroup;
       3: iload_1
       4: invokevirtual #838                // Method mindustry/entities/EntityGroup.getByID:(I)Lmindustry/gen/Entityc;
       7: checkcast     #129                // class mindustry/gen/Unit
      10: astore_2
      11: aload_2
      12: ifnull        31
      15: aload_0
      16: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
      19: iconst_1
      20: anewarray     #129                // class mindustry/gen/Unit
      23: dup
      24: iconst_0
      25: aload_2
      26: aastore
      27: invokevirtual #1688               // Method arc/struct/Seq.addAll:([Ljava/lang/Object;)Larc/struct/Seq;
      30: pop
      31: return

  private static int lambda$update$17(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: getfield      #1691               // Field mindustry/gen/Unit.id:I
       4: ireturn

  private static boolean lambda$update$16(mindustry.gen.Building);
    Code:
       0: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
       3: aload_0
       4: getfield      #1694               // Field mindustry/gen/Building.x:F
       7: aload_0
       8: invokevirtual #1695               // Method mindustry/gen/Building.hitSize:()F
      11: fconst_2
      12: fdiv
      13: fsub
      14: aload_0
      15: getfield      #1698               // Field mindustry/gen/Building.y:F
      18: aload_0
      19: invokevirtual #1695               // Method mindustry/gen/Building.hitSize:()F
      22: fconst_2
      23: fdiv
      24: fsub
      25: aload_0
      26: invokevirtual #1695               // Method mindustry/gen/Building.hitSize:()F
      29: aload_0
      30: invokevirtual #1695               // Method mindustry/gen/Building.hitSize:()F
      33: invokevirtual #1699               // Method arc/math/geom/Rect.overlaps:(FFFF)Z
      36: ireturn

  private static boolean lambda$update$15(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: instanceof    #783                // class mindustry/gen/Payloadc
       4: ireturn

  private static boolean lambda$update$14(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
       4: getfield      #770                // Field mindustry/type/UnitType.controlSelectGlobal:Z
       7: ifne          14
      10: iconst_1
      11: goto          15
      14: iconst_0
      15: ireturn

  private static boolean lambda$update$13(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: invokevirtual #1703               // Method mindustry/gen/Unit.allowCommand:()Z
       4: ifeq          27
       7: aload_0
       8: invokevirtual #844                // Method mindustry/gen/Unit.isValid:()Z
      11: ifeq          27
      14: aload_0
      15: getfield      #1706               // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
      18: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      21: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      24: if_acmpeq     31
      27: iconst_1
      28: goto          32
      31: iconst_0
      32: ireturn

  private void lambda$buildUI$12(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: aload_0
       2: invokedynamic #1707,  0           // InvokeDynamic #18:get:(Lmindustry/input/DesktopInput;)Larc/func/Boolp;
       7: invokevirtual #1710               // Method arc/scene/ui/layout/Table.visible:(Larc/func/Boolp;)Larc/scene/Element;
      10: pop
      11: aload_1
      12: invokevirtual #1713               // Method arc/scene/ui/layout/Table.bottom:()Larc/scene/ui/layout/Table;
      15: pop
      16: aload_1
      17: getstatic     #1716               // Field mindustry/ui/Styles.black6:Larc/scene/style/Drawable;
      20: aload_0
      21: invokedynamic #1720,  0           // InvokeDynamic #19:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      26: invokevirtual #1721               // Method arc/scene/ui/layout/Table.table:(Larc/scene/style/Drawable;Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      29: ldc_w         #395                // float 6.0f
      32: invokevirtual #1725               // Method arc/scene/ui/layout/Cell.margin:(F)Larc/scene/ui/layout/Cell;
      35: pop
      36: return

  private void lambda$buildUI$11(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: invokevirtual #1153               // Method arc/scene/ui/layout/Table.defaults:()Larc/scene/ui/layout/Cell;
       4: invokevirtual #1163               // Method arc/scene/ui/layout/Cell.left:()Larc/scene/ui/layout/Cell;
       7: pop
       8: aload_1
       9: invokedynamic #1727,  0           // InvokeDynamic #20:get:()Larc/func/Prov;
      14: invokevirtual #1730               // Method arc/scene/ui/layout/Table.label:(Larc/func/Prov;)Larc/scene/ui/layout/Cell;
      17: getstatic     #1734               // Field mindustry/ui/Styles.outlineLabel:Larc/scene/ui/Label$LabelStyle;
      20: invokevirtual #1738               // Method arc/scene/ui/layout/Cell.style:(Larc/scene/style/Style;)Larc/scene/ui/layout/Cell;
      23: invokedynamic #1742,  0           // InvokeDynamic #21:get:()Larc/func/Boolp;
      28: invokevirtual #1204               // Method arc/scene/ui/layout/Cell.visible:(Larc/func/Boolp;)Larc/scene/ui/layout/Cell;
      31: pop
      32: aload_1
      33: invokevirtual #1743               // Method arc/scene/ui/layout/Table.row:()Larc/scene/ui/layout/Table;
      36: pop
      37: aload_1
      38: aload_0
      39: invokedynamic #1746,  0           // InvokeDynamic #22:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      44: invokevirtual #1747               // Method arc/scene/ui/layout/Table.table:(Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      47: pop
      48: aload_1
      49: invokevirtual #1743               // Method arc/scene/ui/layout/Table.row:()Larc/scene/ui/layout/Table;
      52: pop
      53: aload_1
      54: aload_0
      55: invokedynamic #1750,  0           // InvokeDynamic #23:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      60: invokevirtual #1747               // Method arc/scene/ui/layout/Table.table:(Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      63: pop
      64: return

  private void lambda$buildUI$10(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: ldc_w         #1751               // String @schematic.preview
       4: getstatic     #1753               // Field mindustry/gen/Icon.info:Larc/scene/style/TextureRegionDrawable;
       7: aload_0
       8: invokedynamic #1756,  0           // InvokeDynamic #24:run:(Lmindustry/input/DesktopInput;)Ljava/lang/Runnable;
      13: invokevirtual #1759               // Method arc/scene/ui/layout/Table.button:(Ljava/lang/String;Larc/scene/style/Drawable;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      16: iconst_2
      17: invokevirtual #1762               // Method arc/scene/ui/layout/Cell.colspan:(I)Larc/scene/ui/layout/Cell;
      20: ldc_w         #1766               // float 250.0f
      23: ldc_w         #1767               // float 50.0f
      26: invokevirtual #1768               // Method arc/scene/ui/layout/Cell.size:(FF)Larc/scene/ui/layout/Cell;
      29: aload_0
      30: invokedynamic #1771,  0           // InvokeDynamic #25:get:(Lmindustry/input/DesktopInput;)Larc/func/Boolf;
      35: invokevirtual #1774               // Method arc/scene/ui/layout/Cell.disabled:(Larc/func/Boolf;)Larc/scene/ui/layout/Cell;
      38: pop
      39: return

  private boolean lambda$buildUI$9(arc.scene.ui.TextButton);
    Code:
       0: aload_0
       1: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
       4: ifnull        17
       7: aload_0
       8: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
      11: getfield      #1778               // Field mindustry/game/Schematic.file:Larc/files/Fi;
      14: ifnull        21
      17: iconst_1
      18: goto          22
      21: iconst_0
      22: ireturn

  private void lambda$buildUI$8(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: ldc_w         #1784               // String @schematic.add
       4: getstatic     #1786               // Field mindustry/gen/Icon.save:Larc/scene/style/TextureRegionDrawable;
       7: aload_0
       8: invokedynamic #1789,  0           // InvokeDynamic #26:run:(Lmindustry/input/DesktopInput;)Ljava/lang/Runnable;
      13: invokevirtual #1759               // Method arc/scene/ui/layout/Table.button:(Ljava/lang/String;Larc/scene/style/Drawable;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      16: iconst_2
      17: invokevirtual #1762               // Method arc/scene/ui/layout/Cell.colspan:(I)Larc/scene/ui/layout/Cell;
      20: ldc_w         #1766               // float 250.0f
      23: ldc_w         #1767               // float 50.0f
      26: invokevirtual #1768               // Method arc/scene/ui/layout/Cell.size:(FF)Larc/scene/ui/layout/Cell;
      29: aload_0
      30: invokedynamic #1790,  0           // InvokeDynamic #27:get:(Lmindustry/input/DesktopInput;)Larc/func/Boolf;
      35: invokevirtual #1774               // Method arc/scene/ui/layout/Cell.disabled:(Larc/func/Boolf;)Larc/scene/ui/layout/Cell;
      38: pop
      39: return

  private boolean lambda$buildUI$7(arc.scene.ui.TextButton);
    Code:
       0: aload_0
       1: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
       4: ifnull        17
       7: aload_0
       8: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
      11: getfield      #1778               // Field mindustry/game/Schematic.file:Larc/files/Fi;
      14: ifnull        21
      17: iconst_1
      18: goto          22
      21: iconst_0
      22: ireturn

  private static boolean lambda$buildUI$6();
    Code:
       0: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
       3: ldc           #93                 // String hints
       5: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
       8: ireturn

  private static java.lang.CharSequence lambda$buildUI$5();
    Code:
       0: getstatic     #1791               // Field arc/Core.bundle:Larc/util/I18NBundle;
       3: ldc_w         #1795               // String schematic.flip
       6: iconst_2
       7: anewarray     #1797               // class java/lang/Object
      10: dup
      11: iconst_0
      12: getstatic     #1280               // Field mindustry/input/Binding.schematicFlipX:Larc/input/KeyBind;
      15: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      18: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
      21: aastore
      22: dup
      23: iconst_1
      24: getstatic     #1287               // Field mindustry/input/Binding.schematicFlipY:Larc/input/KeyBind;
      27: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      30: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
      33: aastore
      34: invokevirtual #1805               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
      37: areturn

  private boolean lambda$buildUI$4();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #75                 // Field mindustry/core/UI.hudfrag:Lmindustry/ui/fragments/HudFragment;
       6: invokevirtual #81                 // Method mindustry/ui/fragments/HudFragment.shown:()Z
       9: ifeq          33
      12: aload_0
      13: getfield      #1265               // Field lastSchematic:Lmindustry/game/Schematic;
      16: ifnull        33
      19: aload_0
      20: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      23: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
      26: ifne          33
      29: iconst_1
      30: goto          34
      33: iconst_0
      34: ireturn

  private void lambda$buildUI$3(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: getfield      #1811               // Field arc/scene/ui/layout/Table.color:Larc/graphics/Color;
       4: fconst_0
       5: putfield      #1813               // Field arc/graphics/Color.a:F
       8: aload_1
       9: aload_0
      10: aload_1
      11: invokedynamic #1816,  0           // InvokeDynamic #28:get:(Lmindustry/input/DesktopInput;Larc/scene/ui/layout/Table;)Larc/func/Boolp;
      16: invokevirtual #1710               // Method arc/scene/ui/layout/Table.visible:(Larc/func/Boolp;)Larc/scene/Element;
      19: pop
      20: aload_1
      21: invokevirtual #1713               // Method arc/scene/ui/layout/Table.bottom:()Larc/scene/ui/layout/Table;
      24: pop
      25: aload_1
      26: getstatic     #1716               // Field mindustry/ui/Styles.black6:Larc/scene/style/Drawable;
      29: aload_0
      30: invokedynamic #1819,  0           // InvokeDynamic #29:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      35: invokevirtual #1721               // Method arc/scene/ui/layout/Table.table:(Larc/scene/style/Drawable;Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      38: ldc_w         #1820               // float 10.0f
      41: invokevirtual #1725               // Method arc/scene/ui/layout/Cell.margin:(F)Larc/scene/ui/layout/Cell;
      44: pop
      45: return

  private void lambda$buildUI$2(arc.scene.ui.layout.Table);
    Code:
       0: new           #1821               // class java/lang/StringBuilder
       3: dup
       4: invokespecial #1823               // Method java/lang/StringBuilder."<init>":()V
       7: astore_2
       8: aload_1
       9: invokevirtual #1153               // Method arc/scene/ui/layout/Table.defaults:()Larc/scene/ui/layout/Cell;
      12: invokevirtual #1163               // Method arc/scene/ui/layout/Cell.left:()Larc/scene/ui/layout/Cell;
      15: pop
      16: aload_1
      17: aload_0
      18: aload_2
      19: invokedynamic #1824,  0           // InvokeDynamic #30:get:(Lmindustry/input/DesktopInput;Ljava/lang/StringBuilder;)Larc/func/Prov;
      24: invokevirtual #1730               // Method arc/scene/ui/layout/Table.label:(Larc/func/Prov;)Larc/scene/ui/layout/Cell;
      27: getstatic     #1734               // Field mindustry/ui/Styles.outlineLabel:Larc/scene/ui/Label$LabelStyle;
      30: invokevirtual #1738               // Method arc/scene/ui/layout/Cell.style:(Larc/scene/style/Style;)Larc/scene/ui/layout/Cell;
      33: pop
      34: return

  private java.lang.CharSequence lambda$buildUI$1(java.lang.StringBuilder);
    Code:
       0: aload_0
       1: invokevirtual #1827               // Method showHint:()Z
       4: ifne          9
       7: aload_1
       8: areturn
       9: aload_1
      10: iconst_0
      11: invokevirtual #1830               // Method java/lang/StringBuilder.setLength:(I)V
      14: aload_0
      15: getfield      #119                // Field isBuilding:Z
      18: ifne          77
      21: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      24: ldc           #122                // String buildautopause
      26: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      29: ifne          77
      32: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      35: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      38: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
      41: ifne          77
      44: aload_1
      45: getstatic     #1791               // Field arc/Core.bundle:Larc/util/I18NBundle;
      48: ldc_w         #1834               // String enablebuilding
      51: iconst_1
      52: anewarray     #1797               // class java/lang/Object
      55: dup
      56: iconst_0
      57: getstatic     #1300               // Field mindustry/input/Binding.pauseBuilding:Larc/input/KeyBind;
      60: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      63: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
      66: aastore
      67: invokevirtual #1805               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
      70: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      73: pop
      74: goto          200
      77: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      80: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      83: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
      86: ifeq          200
      89: aload_1
      90: getstatic     #1791               // Field arc/Core.bundle:Larc/util/I18NBundle;
      93: aload_0
      94: getfield      #119                // Field isBuilding:Z
      97: ifeq          106
     100: ldc_w         #1840               // String pausebuilding
     103: goto          109
     106: ldc_w         #1842               // String resumebuilding
     109: iconst_1
     110: anewarray     #1797               // class java/lang/Object
     113: dup
     114: iconst_0
     115: getstatic     #1300               // Field mindustry/input/Binding.pauseBuilding:Larc/input/KeyBind;
     118: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     121: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
     124: aastore
     125: invokevirtual #1805               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     128: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     131: ldc_w         #1844               // String \n
     134: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     137: getstatic     #1791               // Field arc/Core.bundle:Larc/util/I18NBundle;
     140: ldc_w         #1846               // String cancelbuilding
     143: iconst_1
     144: anewarray     #1797               // class java/lang/Object
     147: dup
     148: iconst_0
     149: getstatic     #1260               // Field mindustry/input/Binding.clearBuilding:Larc/input/KeyBind;
     152: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     155: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
     158: aastore
     159: invokevirtual #1805               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     162: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     165: ldc_w         #1844               // String \n
     168: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     171: getstatic     #1791               // Field arc/Core.bundle:Larc/util/I18NBundle;
     174: ldc_w         #1848               // String selectschematic
     177: iconst_1
     178: anewarray     #1797               // class java/lang/Object
     181: dup
     182: iconst_0
     183: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     186: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     189: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
     192: aastore
     193: invokevirtual #1805               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     196: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     199: pop
     200: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     203: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     206: ifne          270
     209: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     212: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     215: invokevirtual #132                // Method mindustry/gen/Unit.spawnedByCore:()Z
     218: ifne          270
     221: aload_1
     222: aload_1
     223: invokevirtual #1850               // Method java/lang/StringBuilder.length:()I
     226: ifeq          235
     229: ldc_w         #1844               // String \n
     232: goto          238
     235: ldc_w         #1072               // String
     238: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     241: getstatic     #1791               // Field arc/Core.bundle:Larc/util/I18NBundle;
     244: ldc_w         #1853               // String respawn
     247: iconst_1
     248: anewarray     #1797               // class java/lang/Object
     251: dup
     252: iconst_0
     253: getstatic     #927                // Field mindustry/input/Binding.respawn:Larc/input/KeyBind;
     256: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     259: invokestatic  #1799               // Method mindustry/ui/dialogs/KeybindDialog.keyName:(Larc/input/KeyBind$Axis;)Ljava/lang/String;
     262: aastore
     263: invokevirtual #1805               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     266: invokevirtual #1836               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     269: pop
     270: aload_1
     271: areturn

  private boolean lambda$buildUI$0(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: getfield      #1811               // Field arc/scene/ui/layout/Table.color:Larc/graphics/Color;
       4: aload_1
       5: getfield      #1811               // Field arc/scene/ui/layout/Table.color:Larc/graphics/Color;
       8: getfield      #1813               // Field arc/graphics/Color.a:F
      11: aload_0
      12: invokevirtual #1827               // Method showHint:()Z
      15: invokestatic  #1854               // Method arc/math/Mathf.num:(Z)I
      18: i2f
      19: ldc_w         #1858               // float 0.15f
      22: invokestatic  #1430               // Method arc/math/Mathf.lerpDelta:(FFF)F
      25: dup_x1
      26: putfield      #1813               // Field arc/graphics/Color.a:F
      29: ldc_w         #1859               // float 0.001f
      32: fcmpl
      33: ifle          40
      36: iconst_1
      37: goto          41
      40: iconst_0
      41: ireturn
}
