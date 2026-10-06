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
     804: ifne          936
     807: aload_0
     808: getfield      #345                // Field block:Lmindustry/world/Block;
     811: ifnonnull     936
     814: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     817: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
     820: ifne          936
     823: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     826: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
     829: ifne          936
     832: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     835: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     838: ifne          877
     841: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     844: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     847: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     850: getfield      #678                // Field mindustry/type/UnitType.canBoost:Z
     853: ifeq          877
     856: getstatic     #683                // Field mindustry/input/Binding.commandMode:Larc/input/KeyBind;
     859: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     862: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
     865: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
     868: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     871: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
     874: if_acmpeq     936
     877: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
     880: ldc_w         #698                // String commandmodehold
     883: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
     886: ifeq          905
     889: aload_0
     890: getstatic     #174                // Field arc/Core.input:Larc/Input;
     893: getstatic     #683                // Field mindustry/input/Binding.commandMode:Larc/input/KeyBind;
     896: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     899: putfield      #700                // Field commandMode:Z
     902: goto          941
     905: getstatic     #174                // Field arc/Core.input:Larc/Input;
     908: getstatic     #683                // Field mindustry/input/Binding.commandMode:Larc/input/KeyBind;
     911: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     914: ifeq          941
     917: aload_0
     918: aload_0
     919: getfield      #700                // Field commandMode:Z
     922: ifne          929
     925: iconst_1
     926: goto          930
     929: iconst_0
     930: putfield      #700                // Field commandMode:Z
     933: goto          941
     936: aload_0
     937: iconst_0
     938: putfield      #700                // Field commandMode:Z
     941: aload_0
     942: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
     945: invokedynamic #705,  0            // InvokeDynamic #3:get:()Larc/func/Boolf;
     950: invokevirtual #708                // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
     953: pop
     954: aload_0
     955: getfield      #700                // Field commandMode:Z
     958: ifeq          1840
     961: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     964: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
     967: ifne          1840
     970: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     973: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
     976: ifne          1840
     979: getstatic     #174                // Field arc/Core.input:Larc/Input;
     982: getstatic     #712                // Field mindustry/input/Binding.selectAllUnits:Larc/input/KeyBind;
     985: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     988: ifeq          1146
     991: aload_0
     992: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
     995: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     998: pop
     999: aload_0
    1000: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1003: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1006: pop
    1007: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1010: getstatic     #722                // Field mindustry/input/Binding.selectAcrossScreen:Larc/input/KeyBind;
    1013: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1016: ifeq          1075
    1019: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1022: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1025: invokevirtual #729                // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
    1028: pop
    1029: aload_0
    1030: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1033: aload_0
    1034: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1037: getfield      #733                // Field arc/math/geom/Rect.x:F
    1040: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1043: getfield      #736                // Field arc/math/geom/Rect.y:F
    1046: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1049: getfield      #737                // Field arc/math/geom/Rect.width:F
    1052: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1055: getfield      #740                // Field arc/math/geom/Rect.height:F
    1058: invokevirtual #743                // Method selectedCommandUnits:(FFFF)Larc/struct/Seq;
    1061: invokedynamic #747,  0            // InvokeDynamic #4:get:()Larc/func/Boolf;
    1066: invokevirtual #708                // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
    1069: invokevirtual #748                // Method arc/struct/Seq.set:(Larc/struct/Seq;)V
    1072: goto          1146
    1075: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1078: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    1081: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
    1084: getfield      #751                // Field mindustry/game/Teams$TeamData.units:Larc/struct/Seq;
    1087: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1090: astore        5
    1092: aload         5
    1094: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1099: ifeq          1146
    1102: aload         5
    1104: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1109: checkcast     #129                // class mindustry/gen/Unit
    1112: astore        6
    1114: aload         6
    1116: invokevirtual #767                // Method mindustry/gen/Unit.isCommandable:()Z
    1119: ifeq          1143
    1122: aload         6
    1124: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
    1127: getfield      #770                // Field mindustry/type/UnitType.controlSelectGlobal:Z
    1130: ifeq          1143
    1133: aload_0
    1134: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1137: aload         6
    1139: invokevirtual #773                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
    1142: pop
    1143: goto          1092
    1146: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1149: getstatic     #776                // Field mindustry/input/Binding.selectAllUnitTransport:Larc/input/KeyBind;
    1152: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1155: ifeq          1307
    1158: aload_0
    1159: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1162: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1165: pop
    1166: aload_0
    1167: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1170: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1173: pop
    1174: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1177: getstatic     #722                // Field mindustry/input/Binding.selectAcrossScreen:Larc/input/KeyBind;
    1180: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1183: ifeq          1239
    1186: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1189: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1192: invokevirtual #729                // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
    1195: pop
    1196: aload_0
    1197: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1200: aload_0
    1201: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1204: getfield      #733                // Field arc/math/geom/Rect.x:F
    1207: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1210: getfield      #736                // Field arc/math/geom/Rect.y:F
    1213: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1216: getfield      #737                // Field arc/math/geom/Rect.width:F
    1219: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1222: getfield      #740                // Field arc/math/geom/Rect.height:F
    1225: invokedynamic #779,  0            // InvokeDynamic #5:get:()Larc/func/Boolf;
    1230: invokevirtual #780                // Method selectedCommandUnits:(FFFFLarc/func/Boolf;)Larc/struct/Seq;
    1233: invokevirtual #748                // Method arc/struct/Seq.set:(Larc/struct/Seq;)V
    1236: goto          1307
    1239: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1242: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    1245: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
    1248: getfield      #751                // Field mindustry/game/Teams$TeamData.units:Larc/struct/Seq;
    1251: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1254: astore        5
    1256: aload         5
    1258: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1263: ifeq          1307
    1266: aload         5
    1268: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1273: checkcast     #129                // class mindustry/gen/Unit
    1276: astore        6
    1278: aload         6
    1280: invokevirtual #767                // Method mindustry/gen/Unit.isCommandable:()Z
    1283: ifeq          1304
    1286: aload         6
    1288: instanceof    #783                // class mindustry/gen/Payloadc
    1291: ifeq          1304
    1294: aload_0
    1295: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1298: aload         6
    1300: invokevirtual #773                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
    1303: pop
    1304: goto          1256
    1307: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1310: getstatic     #785                // Field mindustry/input/Binding.selectAllUnitFactories:Larc/input/KeyBind;
    1313: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1316: ifeq          1430
    1319: aload_0
    1320: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1323: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1326: pop
    1327: aload_0
    1328: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1331: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1334: pop
    1335: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1338: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    1341: invokevirtual #638                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
    1344: getfield      #788                // Field mindustry/game/Teams$TeamData.buildings:Larc/struct/Seq;
    1347: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1350: astore        5
    1352: aload         5
    1354: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1359: ifeq          1395
    1362: aload         5
    1364: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1369: checkcast     #791                // class mindustry/gen/Building
    1372: astore        6
    1374: aload         6
    1376: invokevirtual #793                // Method mindustry/gen/Building.isCommandable:()Z
    1379: ifeq          1392
    1382: aload_0
    1383: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1386: aload         6
    1388: invokevirtual #773                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
    1391: pop
    1392: goto          1352
    1395: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1398: getstatic     #722                // Field mindustry/input/Binding.selectAcrossScreen:Larc/input/KeyBind;
    1401: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1404: ifeq          1430
    1407: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1410: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
    1413: invokevirtual #729                // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
    1416: pop
    1417: aload_0
    1418: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1421: invokedynamic #794,  0            // InvokeDynamic #6:get:()Larc/func/Boolf;
    1426: invokevirtual #795                // Method arc/struct/Seq.retainAll:(Larc/func/Boolf;)Larc/struct/Seq;
    1429: pop
    1430: iconst_0
    1431: istore        5
    1433: iload         5
    1435: getstatic     #798                // Field controlGroupBindings:[Larc/input/KeyBind;
    1438: arraylength
    1439: if_icmpge     1840
    1442: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1445: getstatic     #798                // Field controlGroupBindings:[Larc/input/KeyBind;
    1448: iload         5
    1450: aaload
    1451: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1454: ifeq          1834
    1457: aload_0
    1458: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1461: iload         5
    1463: aaload
    1464: ifnonnull     1481
    1467: aload_0
    1468: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1471: iload         5
    1473: new           #806                // class arc/struct/IntSeq
    1476: dup
    1477: invokespecial #808                // Method arc/struct/IntSeq."<init>":()V
    1480: aastore
    1481: aload_0
    1482: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1485: iload         5
    1487: aaload
    1488: astore        6
    1490: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1493: getstatic     #809                // Field mindustry/input/Binding.createControlGroup:Larc/input/KeyBind;
    1496: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1499: istore        7
    1501: iload         7
    1503: ifeq          1592
    1506: aload         6
    1508: invokevirtual #812                // Method arc/struct/IntSeq.clear:()V
    1511: aload_0
    1512: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1515: invokedynamic #814,  0            // InvokeDynamic #7:get:()Larc/func/Intf;
    1520: invokevirtual #817                // Method arc/struct/Seq.mapInt:(Larc/func/Intf;)Larc/struct/IntSeq;
    1523: astore        8
    1525: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    1528: ldc_w         #821                // String distinctcontrolgroups
    1531: iconst_1
    1532: invokevirtual #491                // Method arc/Settings.getBool:(Ljava/lang/String;Z)Z
    1535: ifeq          1585
    1538: aload_0
    1539: getfield      #802                // Field controlGroups:[Larc/struct/IntSeq;
    1542: astore        9
    1544: aload         9
    1546: arraylength
    1547: istore        10
    1549: iconst_0
    1550: istore        11
    1552: iload         11
    1554: iload         10
    1556: if_icmpge     1585
    1559: aload         9
    1561: iload         11
    1563: aaload
    1564: astore        12
    1566: aload         12
    1568: ifnull        1579
    1571: aload         12
    1573: aload         8
    1575: invokevirtual #823                // Method arc/struct/IntSeq.removeAll:(Larc/struct/IntSeq;)Z
    1578: pop
    1579: iinc          11, 1
    1582: goto          1552
    1585: aload         6
    1587: aload         8
    1589: invokevirtual #826                // Method arc/struct/IntSeq.addAll:(Larc/struct/IntSeq;)V
    1592: iconst_0
    1593: istore        8
    1595: iload         8
    1597: aload         6
    1599: getfield      #830                // Field arc/struct/IntSeq.size:I
    1602: if_icmpge     1661
    1605: getstatic     #831                // Field mindustry/gen/Groups.unit:Lmindustry/entities/EntityGroup;
    1608: aload         6
    1610: iload         8
    1612: invokevirtual #836                // Method arc/struct/IntSeq.get:(I)I
    1615: invokevirtual #838                // Method mindustry/entities/EntityGroup.getByID:(I)Lmindustry/gen/Entityc;
    1618: checkcast     #129                // class mindustry/gen/Unit
    1621: astore        9
    1623: aload         9
    1625: ifnull        1644
    1628: aload         9
    1630: invokevirtual #767                // Method mindustry/gen/Unit.isCommandable:()Z
    1633: ifeq          1644
    1636: aload         9
    1638: invokevirtual #844                // Method mindustry/gen/Unit.isValid:()Z
    1641: ifne          1655
    1644: aload         6
    1646: iload         8
    1648: invokevirtual #847                // Method arc/struct/IntSeq.removeIndex:(I)I
    1651: pop
    1652: iinc          8, -1
    1655: iinc          8, 1
    1658: goto          1595
    1661: aload         6
    1663: invokevirtual #850                // Method arc/struct/IntSeq.isEmpty:()Z
    1666: ifne          1834
    1669: iload         7
    1671: ifne          1834
    1674: aload_0
    1675: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1678: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1681: pop
    1682: aload_0
    1683: getfield      #719                // Field commandBuildings:Larc/struct/Seq;
    1686: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1689: pop
    1690: aload         6
    1692: aload_0
    1693: invokedynamic #851,  0            // InvokeDynamic #8:get:(Lmindustry/input/DesktopInput;)Larc/func/Intc;
    1698: invokevirtual #854                // Method arc/struct/IntSeq.each:(Larc/func/Intc;)V
    1701: aload_0
    1702: getfield      #857                // Field lastCtrlGroup:I
    1705: iload         5
    1707: if_icmpne     1821
    1710: aload_0
    1711: getfield      #860                // Field lastCtrlGroupSelectMillis:J
    1714: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
    1717: ldc2_w        #867                // long 400l
    1720: lcmp
    1721: ifge          1821
    1724: fconst_0
    1725: fstore        8
    1727: fconst_0
    1728: fstore        9
    1730: aload_0
    1731: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1734: invokevirtual #754                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
    1737: astore        10
    1739: aload         10
    1741: invokeinterface #758,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
    1746: ifeq          1784
    1749: aload         10
    1751: invokeinterface #763,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
    1756: checkcast     #129                // class mindustry/gen/Unit
    1759: astore        11
    1761: fload         8
    1763: aload         11
    1765: getfield      #869                // Field mindustry/gen/Unit.x:F
    1768: fadd
    1769: fstore        8
    1771: fload         9
    1773: aload         11
    1775: getfield      #870                // Field mindustry/gen/Unit.y:F
    1778: fadd
    1779: fstore        9
    1781: goto          1739
    1784: aload_0
    1785: iconst_1
    1786: putfield      #48                 // Field panning:Z
    1789: getstatic     #532                // Field arc/Core.camera:Larc/graphics/Camera;
    1792: getfield      #536                // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
    1795: fload         8
    1797: aload_0
    1798: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1801: getfield      #325                // Field arc/struct/Seq.size:I
    1804: i2f
    1805: fdiv
    1806: fload         9
    1808: aload_0
    1809: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    1812: getfield      #325                // Field arc/struct/Seq.size:I
    1815: i2f
    1816: fdiv
    1817: invokevirtual #871                // Method arc/math/geom/Vec2.set:(FF)Larc/math/geom/Vec2;
    1820: pop
    1821: aload_0
    1822: iload         5
    1824: putfield      #857                // Field lastCtrlGroup:I
    1827: aload_0
    1828: invokestatic  #873                // Method arc/util/Time.millis:()J
    1831: putfield      #860                // Field lastCtrlGroupSelectMillis:J
    1834: iinc          5, 1
    1837: goto          1433
    1840: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1843: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    1846: ifne          1945
    1849: iload_1
    1850: ifne          1945
    1853: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    1856: getfield      #515                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
    1859: getfield      #877                // Field mindustry/game/Rules.possessionAllowed:Z
    1862: ifeq          1945
    1865: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1868: getstatic     #880                // Field mindustry/input/Binding.control:Larc/input/KeyBind;
    1871: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1874: ifeq          1945
    1877: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1880: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    1883: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1886: ifeq          1945
    1889: aload_0
    1890: invokevirtual #886                // Method selectedUnit:()Lmindustry/gen/Unit;
    1893: astore        5
    1895: aload_0
    1896: invokevirtual #889                // Method selectedControlBuild:()Lmindustry/gen/Building;
    1899: astore        6
    1901: aload         5
    1903: ifnull        1927
    1906: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1909: aload         5
    1911: invokestatic  #893                // Method mindustry/gen/Call.unitControl:(Lmindustry/gen/Player;Lmindustry/gen/Unit;)V
    1914: aload_0
    1915: iconst_0
    1916: putfield      #45                 // Field shouldShoot:Z
    1919: aload_0
    1920: fconst_1
    1921: putfield      #899                // Field recentRespawnTimer:F
    1924: goto          1945
    1927: aload         6
    1929: ifnull        1945
    1932: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1935: aload         6
    1937: invokestatic  #902                // Method mindustry/gen/Call.buildingControlSelect:(Lmindustry/gen/Player;Lmindustry/gen/Building;)V
    1940: aload_0
    1941: fconst_1
    1942: putfield      #899                // Field recentRespawnTimer:F
    1945: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1948: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    1951: ifne          2019
    1954: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    1957: invokevirtual #590                // Method mindustry/core/GameState.isPaused:()Z
    1960: ifne          2019
    1963: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1966: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
    1969: ifne          2019
    1972: iload_1
    1973: ifne          2019
    1976: aload_0
    1977: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1980: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    1983: invokevirtual #906                // Method updateMovement:(Lmindustry/gen/Unit;)V
    1986: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1989: getstatic     #910                // Field mindustry/input/Binding.respawn:Larc/input/KeyBind;
    1992: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1995: ifeq          2019
    1998: aload_0
    1999: aconst_null
    2000: putfield      #913                // Field controlledType:Lmindustry/type/UnitType;
    2003: aload_0
    2004: fconst_1
    2005: putfield      #899                // Field recentRespawnTimer:F
    2008: aload_0
    2009: iconst_0
    2010: putfield      #916                // Field droppingItem:Z
    2013: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2016: invokestatic  #919                // Method mindustry/gen/Call.unitClear:(Lmindustry/gen/Player;)V
    2019: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2022: invokevirtual #923                // Method mindustry/core/GameState.isGame:()Z
    2025: ifeq          2273
    2028: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2031: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
    2034: ifne          2273
    2037: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2040: invokevirtual #494                // Method arc/scene/Scene.hasField:()Z
    2043: ifne          2273
    2046: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2049: getstatic     #926                // Field mindustry/input/Binding.minimap:Larc/input/KeyBind;
    2052: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2055: ifeq          2067
    2058: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2061: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
    2064: invokevirtual #929                // Method mindustry/ui/fragments/MinimapFragment.toggle:()V
    2067: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2070: getstatic     #930                // Field mindustry/input/Binding.planetMap:Larc/input/KeyBind;
    2073: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2076: ifeq          2097
    2079: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2082: invokevirtual #933                // Method mindustry/core/GameState.isCampaign:()Z
    2085: ifeq          2097
    2088: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2091: getfield      #936                // Field mindustry/core/UI.planet:Lmindustry/ui/dialogs/PlanetDialog;
    2094: invokevirtual #940                // Method mindustry/ui/dialogs/PlanetDialog.toggle:()V
    2097: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2100: getstatic     #943                // Field mindustry/input/Binding.research:Larc/input/KeyBind;
    2103: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2106: ifeq          2127
    2109: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2112: invokevirtual #933                // Method mindustry/core/GameState.isCampaign:()Z
    2115: ifeq          2127
    2118: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2121: getfield      #946                // Field mindustry/core/UI.research:Lmindustry/ui/dialogs/ResearchDialog;
    2124: invokevirtual #949                // Method mindustry/ui/dialogs/ResearchDialog.toggle:()V
    2127: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2130: getstatic     #952                // Field mindustry/input/Binding.schematicMenu:Larc/input/KeyBind;
    2133: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2136: ifeq          2148
    2139: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2142: getfield      #955                // Field mindustry/core/UI.schematics:Lmindustry/ui/dialogs/SchematicsDialog;
    2145: invokevirtual #959                // Method mindustry/ui/dialogs/SchematicsDialog.toggle:()V
    2148: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2151: getstatic     #962                // Field mindustry/input/Binding.toggleBlockStatus:Larc/input/KeyBind;
    2154: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2157: ifeq          2189
    2160: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2163: ldc_w         #965                // String blockstatus
    2166: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2169: ldc_w         #965                // String blockstatus
    2172: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
    2175: ifne          2182
    2178: iconst_1
    2179: goto          2183
    2182: iconst_0
    2183: invokestatic  #554                // Method java/lang/Boolean.valueOf:(Z)Ljava/lang/Boolean;
    2186: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2189: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2192: getstatic     #967                // Field mindustry/input/Binding.togglePowerLines:Larc/input/KeyBind;
    2195: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2198: ifeq          2273
    2201: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2204: ldc_w         #970                // String lasersopacity
    2207: invokevirtual #972                // Method arc/Settings.getInt:(Ljava/lang/String;)I
    2210: ifne          2239
    2213: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2216: ldc_w         #970                // String lasersopacity
    2219: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2222: ldc_w         #976                // String preferredlaseropacity
    2225: bipush        100
    2227: invokevirtual #978                // Method arc/Settings.getInt:(Ljava/lang/String;I)I
    2230: invokestatic  #981                // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
    2233: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2236: goto          2273
    2239: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2242: ldc_w         #976                // String preferredlaseropacity
    2245: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2248: ldc_w         #970                // String lasersopacity
    2251: invokevirtual #972                // Method arc/Settings.getInt:(Ljava/lang/String;)I
    2254: invokestatic  #981                // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
    2257: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2260: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    2263: ldc_w         #970                // String lasersopacity
    2266: iconst_0
    2267: invokestatic  #981                // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
    2270: invokevirtual #560                // Method arc/Settings.put:(Ljava/lang/String;Ljava/lang/Object;)V
    2273: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
    2276: invokevirtual #986                // Method mindustry/core/GameState.isMenu:()Z
    2279: ifne          2291
    2282: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2285: invokevirtual #497                // Method arc/scene/Scene.hasDialog:()Z
    2288: ifeq          2369
    2291: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2294: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2297: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2300: ifne          2310
    2303: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2306: iconst_0
    2307: putfield      #989                // Field mindustry/gen/Player.shooting:Z
    2310: aload_0
    2311: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2314: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    2317: if_acmpne     2339
    2320: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2323: getstatic     #992                // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    2326: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2329: ifne          2339
    2332: aload_0
    2333: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2336: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2339: aload_0
    2340: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2343: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    2346: if_acmpne     2368
    2349: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2352: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2355: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2358: ifne          2368
    2361: aload_0
    2362: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2365: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2368: return
    2369: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2372: invokevirtual #995                // Method arc/scene/Scene.hasScroll:()Z
    2375: ifeq          2390
    2378: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2381: getstatic     #998                // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    2384: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2387: ifeq          2524
    2390: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2393: getfield      #593                // Field mindustry/core/UI.chatfrag:Lmindustry/ui/fragments/ChatFragment;
    2396: invokevirtual #597                // Method mindustry/ui/fragments/ChatFragment.shown:()Z
    2399: ifne          2524
    2402: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2405: getfield      #1001               // Field mindustry/core/UI.consolefrag:Lmindustry/ui/fragments/ConsoleFragment;
    2408: invokevirtual #1005               // Method mindustry/ui/fragments/ConsoleFragment.shown:()Z
    2411: ifne          2524
    2414: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2417: getstatic     #1008               // Field mindustry/input/Binding.zoom:Larc/input/KeyBind;
    2420: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2423: invokestatic  #578                // Method java/lang/Math.abs:(F)F
    2426: fconst_0
    2427: fcmpl
    2428: ifle          2524
    2431: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2434: getstatic     #1014               // Field mindustry/input/Binding.rotatePlaced:Larc/input/KeyBind;
    2437: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2440: ifne          2524
    2443: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2446: getstatic     #998                // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    2449: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2452: ifne          2509
    2455: getstatic     #1008               // Field mindustry/input/Binding.zoom:Larc/input/KeyBind;
    2458: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
    2461: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2464: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
    2467: invokevirtual #1019               // Method arc/input/KeyBind$Axis.equals:(Ljava/lang/Object;)Z
    2470: ifeq          2509
    2473: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2476: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    2479: ifeq          2499
    2482: aload_0
    2483: invokevirtual #302                // Method isPlacing:()Z
    2486: ifeq          2499
    2489: aload_0
    2490: getfield      #345                // Field block:Lmindustry/world/Block;
    2493: getfield      #260                // Field mindustry/world/Block.rotate:Z
    2496: ifne          2524
    2499: aload_0
    2500: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2503: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    2506: ifeq          2524
    2509: getstatic     #1023               // Field mindustry/Vars.renderer:Lmindustry/core/Renderer;
    2512: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2515: getstatic     #1008               // Field mindustry/input/Binding.zoom:Larc/input/KeyBind;
    2518: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2521: invokevirtual #1027               // Method mindustry/core/Renderer.scaleCamera:(F)V
    2524: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2527: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2530: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2533: ifeq          2578
    2536: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2539: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    2542: ifne          2578
    2545: getstatic     #1032               // Field mindustry/Vars.world:Lmindustry/core/World;
    2548: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2551: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
    2554: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2557: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
    2560: invokevirtual #1043               // Method mindustry/core/World.tileWorld:(FF)Lmindustry/world/Tile;
    2563: astore        5
    2565: aload         5
    2567: ifnull        2578
    2570: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2573: aload         5
    2575: invokestatic  #1049               // Method mindustry/gen/Call.tileTap:(Lmindustry/gen/Player;Lmindustry/world/Tile;)V
    2578: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2581: getstatic     #1053               // Field mindustry/input/Binding.ping:Larc/input/KeyBind;
    2584: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2587: ifeq          2661
    2590: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2593: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    2596: ifne          2661
    2599: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2602: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
    2605: ifne          2661
    2608: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2611: invokevirtual #1056               // Method arc/Input.ctrl:()Z
    2614: ifeq          2642
    2617: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2620: ldc_w         #1059               // String
    2623: ldc_w         #1061               // String @ping.text
    2626: bipush        40
    2628: ldc_w         #1059               // String
    2631: invokedynamic #1063,  0           // InvokeDynamic #9:get:()Larc/func/Cons;
    2636: invokevirtual #1066               // Method mindustry/core/UI.showTextInput:(Ljava/lang/String;Ljava/lang/String;ILjava/lang/String;Larc/func/Cons;)V
    2639: goto          2661
    2642: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2645: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2648: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
    2651: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2654: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
    2657: aconst_null
    2658: invokestatic  #1070               // Method mindustry/gen/Call.pingLocation:(Lmindustry/gen/Player;FFLjava/lang/String;)V
    2661: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2664: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2667: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    2670: ifeq          2684
    2673: aload_0
    2674: getfield      #1077               // Field commandRect:Z
    2677: ifeq          2684
    2680: aload_0
    2681: invokevirtual #1080               // Method selectUnitsRect:()V
    2684: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2687: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    2690: ifne          2697
    2693: iload_1
    2694: ifeq          2715
    2697: aload_0
    2698: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2701: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2704: iload_1
    2705: ifne          2719
    2708: aload_0
    2709: invokevirtual #1083               // Method pollInputNoPlayer:()V
    2712: goto          2719
    2715: aload_0
    2716: invokevirtual #1086               // Method pollInputPlayer:()V
    2719: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2722: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    2725: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    2728: ifeq          2738
    2731: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2734: iconst_0
    2735: putfield      #989                // Field mindustry/gen/Player.shooting:Z
    2738: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    2741: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    2744: ifne          2791
    2747: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2750: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
    2753: invokevirtual #1089               // Method mindustry/ui/fragments/MinimapFragment.shown:()Z
    2756: ifne          2791
    2759: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
    2762: aload_0
    2763: getfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2766: invokevirtual #162                // Method arc/Graphics.cursor:(Larc/Graphics$Cursor;)V
    2769: aload_0
    2770: aload_0
    2771: getfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2774: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2777: if_acmpeq     2784
    2780: iconst_1
    2781: goto          2785
    2784: iconst_0
    2785: putfield      #1090               // Field changedCursor:Z
    2788: goto          2819
    2791: aload_0
    2792: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2795: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2798: aload_0
    2799: getfield      #1090               // Field changedCursor:Z
    2802: ifeq          2819
    2805: getstatic     #158                // Field arc/Core.graphics:Larc/Graphics;
    2808: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2811: invokevirtual #162                // Method arc/Graphics.cursor:(Larc/Graphics$Cursor;)V
    2814: aload_0
    2815: iconst_0
    2816: putfield      #1090               // Field changedCursor:Z
    2819: return

  public void useSchematic(mindustry.game.Schematic, boolean);
    Code:
       0: aload_0
       1: aconst_null
       2: putfield      #345                // Field block:Lmindustry/world/Block;
       5: aload_0
       6: aload_0
       7: aload_0
       8: invokevirtual #1093               // Method getMouseX:()F
      11: invokevirtual #184                // Method tileX:(F)I
      14: putfield      #1096               // Field schematicX:I
      17: aload_0
      18: aload_0
      19: aload_0
      20: invokevirtual #1099               // Method getMouseY:()F
      23: invokevirtual #191                // Method tileY:(F)I
      26: putfield      #1102               // Field schematicY:I
      29: aload_0
      30: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      33: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      36: pop
      37: aload_0
      38: getfield      #101                // Field selectPlans:Larc/struct/Seq;
      41: getstatic     #1105               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
      44: aload_1
      45: aload_0
      46: getfield      #1096               // Field schematicX:I
      49: aload_0
      50: getfield      #1102               // Field schematicY:I
      53: iload_2
      54: invokevirtual #1108               // Method mindustry/game/Schematics.toPlans:(Lmindustry/game/Schematic;IIZ)Larc/struct/Seq;
      57: invokevirtual #1114               // Method arc/struct/Seq.addAll:(Larc/struct/Seq;)Larc/struct/Seq;
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
       1: invokevirtual #1117               // Method arc/scene/ui/layout/Table.left:()Larc/scene/ui/layout/Table;
       4: fconst_0
       5: invokevirtual #1123               // Method arc/scene/ui/layout/Table.margin:(F)Larc/scene/ui/layout/Table;
       8: invokevirtual #1127               // Method arc/scene/ui/layout/Table.defaults:()Larc/scene/ui/layout/Cell;
      11: ldc_w         #1131               // float 48.0f
      14: invokevirtual #1132               // Method arc/scene/ui/layout/Cell.size:(F)Larc/scene/ui/layout/Cell;
      17: invokevirtual #1137               // Method arc/scene/ui/layout/Cell.left:()Larc/scene/ui/layout/Cell;
      20: pop
      21: aload_1
      22: getstatic     #1139               // Field mindustry/gen/Icon.paste:Larc/scene/style/TextureRegionDrawable;
      25: getstatic     #1145               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
      28: invokedynamic #1151,  0           // InvokeDynamic #10:run:()Ljava/lang/Runnable;
      33: invokevirtual #1155               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      36: ldc_w         #1159               // String @schematics
      39: invokevirtual #1161               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
      42: pop
      43: aload_1
      44: getstatic     #1165               // Field mindustry/gen/Icon.book:Larc/scene/style/TextureRegionDrawable;
      47: getstatic     #1145               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
      50: invokedynamic #1168,  0           // InvokeDynamic #11:run:()Ljava/lang/Runnable;
      55: invokevirtual #1155               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      58: ldc_w         #1169               // String @database
      61: invokevirtual #1161               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
      64: pop
      65: aload_1
      66: getstatic     #1171               // Field mindustry/gen/Icon.tree:Larc/scene/style/TextureRegionDrawable;
      69: getstatic     #1145               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
      72: invokedynamic #1174,  0           // InvokeDynamic #12:run:()Ljava/lang/Runnable;
      77: invokevirtual #1155               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      80: invokedynamic #1175,  0           // InvokeDynamic #13:get:()Larc/func/Boolp;
      85: invokevirtual #1178               // Method arc/scene/ui/layout/Cell.visible:(Larc/func/Boolp;)Larc/scene/ui/layout/Cell;
      88: ldc_w         #1182               // String @research
      91: invokevirtual #1161               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
      94: pop
      95: aload_1
      96: getstatic     #1184               // Field mindustry/gen/Icon.map:Larc/scene/style/TextureRegionDrawable;
      99: getstatic     #1145               // Field mindustry/ui/Styles.clearNonei:Larc/scene/ui/ImageButton$ImageButtonStyle;
     102: invokedynamic #1187,  0           // InvokeDynamic #14:run:()Ljava/lang/Runnable;
     107: invokevirtual #1155               // Method arc/scene/ui/layout/Table.button:(Larc/scene/style/Drawable;Larc/scene/ui/ImageButton$ImageButtonStyle;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
     110: invokedynamic #1188,  0           // InvokeDynamic #15:get:()Larc/func/Boolp;
     115: invokevirtual #1178               // Method arc/scene/ui/layout/Cell.visible:(Larc/func/Boolp;)Larc/scene/ui/layout/Cell;
     118: ldc_w         #1189               // String @planetmap
     121: invokevirtual #1161               // Method arc/scene/ui/layout/Cell.tooltip:(Ljava/lang/String;)Larc/scene/ui/layout/Cell;
     124: pop
     125: return

  void pollInputNoPlayer();
    Code:
       0: getstatic     #174                // Field arc/Core.input:Larc/Input;
       3: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
       6: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
       9: ifeq          93
      12: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
      15: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
      18: ifne          93
      21: aload_0
      22: iconst_0
      23: putfield      #1191               // Field tappedOne:Z
      26: aload_0
      27: getstatic     #174                // Field arc/Core.input:Larc/Input;
      30: invokevirtual #178                // Method arc/Input.mouseX:()I
      33: i2f
      34: getstatic     #174                // Field arc/Core.input:Larc/Input;
      37: invokevirtual #188                // Method arc/Input.mouseY:()I
      40: i2f
      41: invokevirtual #1194               // Method tileAt:(FF)Lmindustry/world/Tile;
      44: astore_1
      45: aload_0
      46: getfield      #700                // Field commandMode:Z
      49: ifeq          80
      52: aload_0
      53: iconst_1
      54: putfield      #1077               // Field commandRect:Z
      57: aload_0
      58: getstatic     #174                // Field arc/Core.input:Larc/Input;
      61: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
      64: putfield      #1197               // Field commandRectX:F
      67: aload_0
      68: getstatic     #174                // Field arc/Core.input:Larc/Input;
      71: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
      74: putfield      #1200               // Field commandRectY:F
      77: goto          93
      80: aload_1
      81: ifnull        93
      84: aload_0
      85: aload_1
      86: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      89: invokevirtual #1207               // Method tileTapped:(Lmindustry/gen/Building;)Z
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
      25: invokevirtual #1194               // Method tileAt:(FF)Lmindustry/world/Tile;
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
      62: invokestatic  #1211               // Method mindustry/core/World.toTile:(F)I
      65: istore        4
      67: getstatic     #174                // Field arc/Core.input:Larc/Input;
      70: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      73: getfield      #666                // Field arc/math/geom/Vec2.y:F
      76: invokestatic  #1211               // Method mindustry/core/World.toTile:(F)I
      79: istore        5
      81: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      84: ldc           #122                // String buildautopause
      86: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      89: ifeq          121
      92: aload_0
      93: getfield      #119                // Field isBuilding:Z
      96: ifeq          121
      99: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     102: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     105: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
     108: ifne          121
     111: aload_0
     112: iconst_0
     113: putfield      #119                // Field isBuilding:Z
     116: aload_0
     117: iconst_1
     118: putfield      #1214               // Field buildWasAutoPaused:Z
     121: aload_0
     122: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     125: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     128: ifne          187
     131: iload         4
     133: aload_0
     134: getfield      #1096               // Field schematicX:I
     137: isub
     138: istore        6
     140: iload         5
     142: aload_0
     143: getfield      #1102               // Field schematicY:I
     146: isub
     147: istore        7
     149: aload_0
     150: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     153: iload         6
     155: iload         7
     157: invokedynamic #1217,  0           // InvokeDynamic #16:get:(II)Larc/func/Cons;
     162: invokevirtual #356                // Method arc/struct/Seq.each:(Larc/func/Cons;)V
     165: aload_0
     166: dup
     167: getfield      #1096               // Field schematicX:I
     170: iload         6
     172: iadd
     173: putfield      #1096               // Field schematicX:I
     176: aload_0
     177: dup
     178: getfield      #1102               // Field schematicY:I
     181: iload         7
     183: iadd
     184: putfield      #1102               // Field schematicY:I
     187: getstatic     #174                // Field arc/Core.input:Larc/Input;
     190: getstatic     #1220               // Field mindustry/input/Binding.deselect:Larc/input/KeyBind;
     193: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     196: ifeq          250
     199: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
     202: getfield      #467                // Field mindustry/core/UI.minimapfrag:Lmindustry/ui/fragments/MinimapFragment;
     205: invokevirtual #1089               // Method mindustry/ui/fragments/MinimapFragment.shown:()Z
     208: ifne          250
     211: aload_0
     212: invokevirtual #302                // Method isPlacing:()Z
     215: ifne          250
     218: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     221: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     224: getfield      #1223               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     227: invokevirtual #1227               // Method arc/struct/Queue.isEmpty:()Z
     230: ifeq          250
     233: aload_0
     234: getfield      #700                // Field commandMode:Z
     237: ifne          250
     240: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     243: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     246: aconst_null
     247: putfield      #1230               // Field mindustry/gen/Unit.mineTile:Lmindustry/world/Tile;
     250: getstatic     #174                // Field arc/Core.input:Larc/Input;
     253: getstatic     #1234               // Field mindustry/input/Binding.clearBuilding:Larc/input/KeyBind;
     256: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     259: ifeq          280
     262: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     265: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     268: ifne          280
     271: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     274: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     277: invokevirtual #1237               // Method mindustry/gen/Unit.clearBuilding:()V
     280: getstatic     #174                // Field arc/Core.input:Larc/Input;
     283: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     286: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     289: ifne          304
     292: getstatic     #174                // Field arc/Core.input:Larc/Input;
     295: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     298: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     301: ifeq          335
     304: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     307: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
     310: ifne          335
     313: aload_0
     314: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     317: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
     320: if_acmpeq     335
     323: aload_0
     324: iload         4
     326: putfield      #35                 // Field schemX:I
     329: aload_0
     330: iload         5
     332: putfield      #38                 // Field schemY:I
     335: getstatic     #174                // Field arc/Core.input:Larc/Input;
     338: getstatic     #1234               // Field mindustry/input/Binding.clearBuilding:Larc/input/KeyBind;
     341: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     344: ifne          354
     347: aload_0
     348: invokevirtual #302                // Method isPlacing:()Z
     351: ifeq          367
     354: aload_0
     355: aconst_null
     356: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
     359: aload_0
     360: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     363: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     366: pop
     367: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     370: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
     373: ifne          540
     376: aload_0
     377: getfield      #28                 // Field selectX:I
     380: iconst_m1
     381: if_icmpne     540
     384: aload_0
     385: getfield      #32                 // Field selectY:I
     388: iconst_m1
     389: if_icmpne     540
     392: aload_0
     393: getfield      #35                 // Field schemX:I
     396: iconst_m1
     397: if_icmpeq     540
     400: aload_0
     401: getfield      #38                 // Field schemY:I
     404: iconst_m1
     405: if_icmpeq     540
     408: getstatic     #174                // Field arc/Core.input:Larc/Input;
     411: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     414: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     417: ifeq          490
     420: aload_0
     421: getstatic     #1105               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
     424: aload_0
     425: getfield      #35                 // Field schemX:I
     428: aload_0
     429: getfield      #38                 // Field schemY:I
     432: iload         4
     434: iload         5
     436: invokevirtual #1243               // Method mindustry/game/Schematics.create:(IIII)Lmindustry/game/Schematic;
     439: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
     442: aload_0
     443: aload_0
     444: getfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
     447: invokevirtual #1247               // Method useSchematic:(Lmindustry/game/Schematic;)V
     450: aload_0
     451: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     454: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     457: ifeq          465
     460: aload_0
     461: aconst_null
     462: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
     465: getstatic     #174                // Field arc/Core.input:Larc/Input;
     468: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     471: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     474: ifne          540
     477: aload_0
     478: iconst_m1
     479: putfield      #35                 // Field schemX:I
     482: aload_0
     483: iconst_m1
     484: putfield      #38                 // Field schemY:I
     487: goto          540
     490: getstatic     #174                // Field arc/Core.input:Larc/Input;
     493: getstatic     #227                // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
     496: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     499: ifeq          540
     502: aload_0
     503: aload_0
     504: getfield      #35                 // Field schemX:I
     507: aload_0
     508: getfield      #38                 // Field schemY:I
     511: iload         4
     513: iload         5
     515: invokevirtual #1251               // Method rebuildArea:(IIII)V
     518: getstatic     #174                // Field arc/Core.input:Larc/Input;
     521: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     524: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     527: ifne          540
     530: aload_0
     531: iconst_m1
     532: putfield      #35                 // Field schemX:I
     535: aload_0
     536: iconst_m1
     537: putfield      #38                 // Field schemY:I
     540: aload_0
     541: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     544: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     547: ifne          592
     550: getstatic     #174                // Field arc/Core.input:Larc/Input;
     553: getstatic     #1254               // Field mindustry/input/Binding.schematicFlipX:Larc/input/KeyBind;
     556: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     559: ifeq          571
     562: aload_0
     563: aload_0
     564: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     567: iconst_1
     568: invokevirtual #1257               // Method flipPlans:(Larc/struct/Seq;Z)V
     571: getstatic     #174                // Field arc/Core.input:Larc/Input;
     574: getstatic     #1261               // Field mindustry/input/Binding.schematicFlipY:Larc/input/KeyBind;
     577: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     580: ifeq          592
     583: aload_0
     584: aload_0
     585: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     588: iconst_0
     589: invokevirtual #1257               // Method flipPlans:(Larc/struct/Seq;Z)V
     592: aload_0
     593: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     596: ifnull        692
     599: getstatic     #174                // Field arc/Core.input:Larc/Input;
     602: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     605: getfield      #657                // Field arc/math/geom/Vec2.x:F
     608: aload_0
     609: getfield      #1264               // Field buildPlanMouseOffsetX:F
     612: fadd
     613: ldc_w         #1267               // float 8.0f
     616: fdiv
     617: invokestatic  #1268               // Method java/lang/Math.round:(F)I
     620: istore        6
     622: getstatic     #174                // Field arc/Core.input:Larc/Input;
     625: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
     628: getfield      #666                // Field arc/math/geom/Vec2.y:F
     631: aload_0
     632: getfield      #1271               // Field buildPlanMouseOffsetY:F
     635: fadd
     636: ldc_w         #1267               // float 8.0f
     639: fdiv
     640: invokestatic  #1268               // Method java/lang/Math.round:(F)I
     643: istore        7
     645: aload_0
     646: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     649: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     652: iload         6
     654: if_icmpne     669
     657: aload_0
     658: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     661: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     664: iload         7
     666: if_icmpeq     692
     669: aload_0
     670: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     673: iload         6
     675: putfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
     678: aload_0
     679: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
     682: iload         7
     684: putfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
     687: aload_0
     688: iconst_1
     689: putfield      #51                 // Field movedPlan:Z
     692: aload_0
     693: getfield      #345                // Field block:Lmindustry/world/Block;
     696: ifnull        709
     699: aload_0
     700: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     703: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
     706: if_acmpeq     717
     709: aload_0
     710: getfield      #346                // Field linePlans:Larc/struct/Seq;
     713: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     716: pop
     717: getstatic     #174                // Field arc/Core.input:Larc/Input;
     720: getstatic     #1274               // Field mindustry/input/Binding.pauseBuilding:Larc/input/KeyBind;
     723: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     726: ifeq          764
     729: aload_0
     730: aload_0
     731: getfield      #119                // Field isBuilding:Z
     734: ifne          741
     737: iconst_1
     738: goto          742
     741: iconst_0
     742: putfield      #119                // Field isBuilding:Z
     745: aload_0
     746: iconst_0
     747: putfield      #1214               // Field buildWasAutoPaused:Z
     750: aload_0
     751: getfield      #119                // Field isBuilding:Z
     754: ifeq          764
     757: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     760: iconst_0
     761: putfield      #989                // Field mindustry/gen/Player.shooting:Z
     764: aload_0
     765: invokevirtual #302                // Method isPlacing:()Z
     768: ifeq          843
     771: aload_0
     772: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     775: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
     778: if_acmpne     843
     781: iload_2
     782: aload_0
     783: getfield      #1277               // Field lastLineX:I
     786: if_icmpne     821
     789: iload_3
     790: aload_0
     791: getfield      #1280               // Field lastLineY:I
     794: if_icmpne     821
     797: getstatic     #174                // Field arc/Core.input:Larc/Input;
     800: getstatic     #998                // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
     803: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     806: ifne          821
     809: getstatic     #174                // Field arc/Core.input:Larc/Input;
     812: getstatic     #998                // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
     815: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     818: ifeq          843
     821: aload_0
     822: aload_0
     823: getfield      #28                 // Field selectX:I
     826: aload_0
     827: getfield      #32                 // Field selectY:I
     830: invokevirtual #1283               // Method updateLine:(II)V
     833: aload_0
     834: iload_2
     835: putfield      #1277               // Field lastLineX:I
     838: aload_0
     839: iload_3
     840: putfield      #1280               // Field lastLineY:I
     843: getstatic     #174                // Field arc/Core.input:Larc/Input;
     846: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
     849: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
     852: ifeq          936
     855: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     858: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
     861: ifne          936
     864: aload_0
     865: iload_2
     866: iload_3
     867: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
     870: astore        6
     872: aload         6
     874: ifnull        936
     877: aload_0
     878: getfield      #51                 // Field movedPlan:Z
     881: ifne          936
     884: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     887: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     890: getfield      #1223               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     893: aload         6
     895: iconst_1
     896: invokevirtual #1287               // Method arc/struct/Queue.indexOf:(Ljava/lang/Object;Z)I
     899: istore        7
     901: iload         7
     903: iconst_m1
     904: if_icmpeq     936
     907: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     910: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     913: getfield      #1223               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     916: iload         7
     918: invokevirtual #1291               // Method arc/struct/Queue.removeIndex:(I)Ljava/lang/Object;
     921: pop
     922: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     925: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     928: getfield      #1223               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     931: aload         6
     933: invokevirtual #1293               // Method arc/struct/Queue.addFirst:(Ljava/lang/Object;)V
     936: getstatic     #174                // Field arc/Core.input:Larc/Input;
     939: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
     942: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     945: ifeq          1408
     948: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
     951: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
     954: ifne          1408
     957: aload_0
     958: iconst_0
     959: putfield      #1191               // Field tappedOne:Z
     962: aload_0
     963: iload_2
     964: iload_3
     965: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
     968: astore        6
     970: getstatic     #174                // Field arc/Core.input:Larc/Input;
     973: getstatic     #992                // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
     976: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     979: ifeq          992
     982: aload_0
     983: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
     986: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
     989: goto          1393
     992: aload_0
     993: getfield      #101                // Field selectPlans:Larc/struct/Seq;
     996: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
     999: ifne          1018
    1002: aload_0
    1003: aload_0
    1004: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1007: invokevirtual #1297               // Method flushPlans:(Larc/struct/Seq;)V
    1010: aload_0
    1011: iconst_1
    1012: putfield      #51                 // Field movedPlan:Z
    1015: goto          1393
    1018: aload_0
    1019: invokevirtual #302                // Method isPlacing:()Z
    1022: ifeq          1067
    1025: aload_0
    1026: iload_2
    1027: putfield      #28                 // Field selectX:I
    1030: aload_0
    1031: iload_3
    1032: putfield      #32                 // Field selectY:I
    1035: aload_0
    1036: iload_2
    1037: putfield      #1277               // Field lastLineX:I
    1040: aload_0
    1041: iload_3
    1042: putfield      #1280               // Field lastLineY:I
    1045: aload_0
    1046: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    1049: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1052: aload_0
    1053: aload_0
    1054: getfield      #28                 // Field selectX:I
    1057: aload_0
    1058: getfield      #32                 // Field selectY:I
    1061: invokevirtual #1283               // Method updateLine:(II)V
    1064: goto          1393
    1067: aload         6
    1069: ifnull        1172
    1072: aload         6
    1074: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
    1077: ifne          1172
    1080: aload_0
    1081: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1084: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1087: if_acmpne     1172
    1090: aload         6
    1092: getfield      #1300               // Field mindustry/entities/units/BuildPlan.initialized:Z
    1095: ifne          1172
    1098: aload         6
    1100: getfield      #1303               // Field mindustry/entities/units/BuildPlan.progress:F
    1103: fconst_0
    1104: fcmpg
    1105: ifgt          1172
    1108: aload_0
    1109: aload         6
    1111: putfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    1114: aload_0
    1115: iconst_0
    1116: putfield      #51                 // Field movedPlan:Z
    1119: aload_0
    1120: aload_0
    1121: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    1124: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
    1127: bipush        8
    1129: imul
    1130: i2f
    1131: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1134: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1137: getfield      #657                // Field arc/math/geom/Vec2.x:F
    1140: fsub
    1141: putfield      #1264               // Field buildPlanMouseOffsetX:F
    1144: aload_0
    1145: aload_0
    1146: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    1149: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
    1152: bipush        8
    1154: imul
    1155: i2f
    1156: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1159: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1162: getfield      #666                // Field arc/math/geom/Vec2.y:F
    1165: fsub
    1166: putfield      #1271               // Field buildPlanMouseOffsetY:F
    1169: goto          1393
    1172: aload         6
    1174: ifnull        1193
    1177: aload         6
    1179: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
    1182: ifeq          1193
    1185: aload_0
    1186: iconst_1
    1187: putfield      #41                 // Field deleting:Z
    1190: goto          1393
    1193: aload_0
    1194: getfield      #700                // Field commandMode:Z
    1197: ifeq          1228
    1200: aload_0
    1201: iconst_1
    1202: putfield      #1077               // Field commandRect:Z
    1205: aload_0
    1206: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1209: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
    1212: putfield      #1197               // Field commandRectX:F
    1215: aload_0
    1216: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1219: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
    1222: putfield      #1200               // Field commandRectY:F
    1225: goto          1393
    1228: aload_0
    1229: invokevirtual #1306               // Method checkConfigTap:()Z
    1232: ifne          1374
    1235: aload_1
    1236: ifnull        1374
    1239: aload_0
    1240: aload_1
    1241: invokevirtual #1309               // Method tryRepairDerelict:(Lmindustry/world/Tile;)Z
    1244: ifne          1374
    1247: aload_0
    1248: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1251: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1254: getfield      #657                // Field arc/math/geom/Vec2.x:F
    1257: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1260: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    1263: getfield      #666                // Field arc/math/geom/Vec2.y:F
    1266: invokevirtual #1313               // Method tryTapPlayer:(FF)Z
    1269: ifne          1393
    1272: aload_0
    1273: aload_1
    1274: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    1277: invokevirtual #1207               // Method tileTapped:(Lmindustry/gen/Building;)Z
    1280: ifne          1393
    1283: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1286: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    1289: invokevirtual #1317               // Method mindustry/gen/Unit.activelyBuilding:()Z
    1292: ifne          1393
    1295: aload_0
    1296: getfield      #916                // Field droppingItem:Z
    1299: ifne          1393
    1302: aload_0
    1303: aload_1
    1304: invokevirtual #1320               // Method tryStopMine:(Lmindustry/world/Tile;)Z
    1307: ifne          1393
    1310: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
    1313: ldc_w         #1323               // String doubletapmine
    1316: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
    1319: ifeq          1344
    1322: aload_1
    1323: aload_0
    1324: getfield      #1325               // Field prevSelected:Lmindustry/world/Tile;
    1327: if_acmpne     1352
    1330: aload_0
    1331: getfield      #67                 // Field selectMillis:J
    1334: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
    1337: ldc2_w        #1328               // long 500l
    1340: lcmp
    1341: ifge          1352
    1344: aload_0
    1345: aload_1
    1346: invokevirtual #1330               // Method tryBeginMine:(Lmindustry/world/Tile;)Z
    1349: ifne          1393
    1352: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1355: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
    1358: ifne          1393
    1361: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1364: aload_0
    1365: getfield      #45                 // Field shouldShoot:Z
    1368: putfield      #989                // Field mindustry/gen/Player.shooting:Z
    1371: goto          1393
    1374: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1377: invokevirtual #220                // Method arc/scene/Scene.hasKeyboard:()Z
    1380: ifne          1393
    1383: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1386: aload_0
    1387: getfield      #45                 // Field shouldShoot:Z
    1390: putfield      #989                // Field mindustry/gen/Player.shooting:Z
    1393: aload_0
    1394: invokestatic  #873                // Method arc/util/Time.millis:()J
    1397: putfield      #67                 // Field selectMillis:J
    1400: aload_0
    1401: aload_1
    1402: putfield      #1325               // Field prevSelected:Lmindustry/world/Tile;
    1405: goto          1571
    1408: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1411: getstatic     #1220               // Field mindustry/input/Binding.deselect:Larc/input/KeyBind;
    1414: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1417: ifeq          1442
    1420: aload_0
    1421: invokevirtual #302                // Method isPlacing:()Z
    1424: ifeq          1442
    1427: aload_0
    1428: aconst_null
    1429: putfield      #345                // Field block:Lmindustry/world/Block;
    1432: aload_0
    1433: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1436: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1439: goto          1571
    1442: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1445: getstatic     #1220               // Field mindustry/input/Binding.deselect:Larc/input/KeyBind;
    1448: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1451: ifeq          1480
    1454: aload_0
    1455: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1458: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    1461: ifne          1480
    1464: aload_0
    1465: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    1468: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1471: pop
    1472: aload_0
    1473: aconst_null
    1474: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
    1477: goto          1571
    1480: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1483: getstatic     #992                // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1486: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    1489: ifeq          1571
    1492: getstatic     #149                // Field arc/Core.scene:Larc/scene/Scene;
    1495: invokevirtual #153                // Method arc/scene/Scene.hasMouse:()Z
    1498: ifne          1571
    1501: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1504: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    1507: ifeq          1571
    1510: aload_0
    1511: getfield      #700                // Field commandMode:Z
    1514: ifne          1571
    1517: aload_0
    1518: iconst_0
    1519: putfield      #41                 // Field deleting:Z
    1522: aload_0
    1523: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    1526: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1529: aload_0
    1530: aload_0
    1531: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1534: invokevirtual #178                // Method arc/Input.mouseX:()I
    1537: i2f
    1538: invokevirtual #184                // Method tileX:(F)I
    1541: putfield      #28                 // Field selectX:I
    1544: aload_0
    1545: aload_0
    1546: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1549: invokevirtual #188                // Method arc/Input.mouseY:()I
    1552: i2f
    1553: invokevirtual #191                // Method tileY:(F)I
    1556: putfield      #32                 // Field selectY:I
    1559: aload_0
    1560: iload         4
    1562: putfield      #35                 // Field schemX:I
    1565: aload_0
    1566: iload         5
    1568: putfield      #38                 // Field schemY:I
    1571: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1574: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    1577: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1580: ifeq          1646
    1583: aload_0
    1584: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1587: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    1590: if_acmpne     1646
    1593: aload_0
    1594: invokevirtual #302                // Method isPlacing:()Z
    1597: ifne          1646
    1600: aload_0
    1601: getfield      #41                 // Field deleting:Z
    1604: ifeq          1646
    1607: aload_0
    1608: iload_2
    1609: iload_3
    1610: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
    1613: astore        6
    1615: aload         6
    1617: ifnull        1643
    1620: aload         6
    1622: getfield      #308                // Field mindustry/entities/units/BuildPlan.breaking:Z
    1625: ifeq          1643
    1628: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    1631: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    1634: invokevirtual #1333               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
    1637: aload         6
    1639: invokevirtual #1336               // Method arc/struct/Queue.remove:(Ljava/lang/Object;)Z
    1642: pop
    1643: goto          1651
    1646: aload_0
    1647: iconst_0
    1648: putfield      #41                 // Field deleting:Z
    1651: aload_0
    1652: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1655: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    1658: if_acmpne     1756
    1661: aload_0
    1662: getfield      #345                // Field block:Lmindustry/world/Block;
    1665: ifnull        1756
    1668: aload_0
    1669: getfield      #1338               // Field overrideLineRotation:Z
    1672: ifne          1761
    1675: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1678: getstatic     #998                // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    1681: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1684: ifne          1761
    1687: aload_0
    1688: getfield      #28                 // Field selectX:I
    1691: iload_2
    1692: if_icmpne     1703
    1695: aload_0
    1696: getfield      #32                 // Field selectY:I
    1699: iload_3
    1700: if_icmpeq     1761
    1703: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1706: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    1709: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    1712: f2i
    1713: ifeq          1761
    1716: aload_0
    1717: aload_0
    1718: getfield      #28                 // Field selectX:I
    1721: i2f
    1722: aload_0
    1723: getfield      #32                 // Field selectY:I
    1726: i2f
    1727: iload_2
    1728: i2f
    1729: iload_3
    1730: i2f
    1731: invokestatic  #1341               // Method arc/math/Angles.angle:(FFFF)F
    1734: ldc_w         #1347               // float 45.0f
    1737: fadd
    1738: ldc_w         #1348               // float 90.0f
    1741: fdiv
    1742: f2i
    1743: iconst_4
    1744: irem
    1745: putfield      #359                // Field rotation:I
    1748: aload_0
    1749: iconst_1
    1750: putfield      #1338               // Field overrideLineRotation:Z
    1753: goto          1761
    1756: aload_0
    1757: iconst_0
    1758: putfield      #1338               // Field overrideLineRotation:Z
    1761: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1764: getstatic     #992                // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1767: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    1770: ifeq          1827
    1773: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1776: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
    1779: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1782: ifeq          1827
    1785: aload_0
    1786: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1789: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    1792: if_acmpne     1827
    1795: aload_0
    1796: getstatic     #1105               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
    1799: aload_0
    1800: getfield      #35                 // Field schemX:I
    1803: aload_0
    1804: getfield      #38                 // Field schemY:I
    1807: iload         4
    1809: iload         5
    1811: invokevirtual #1243               // Method mindustry/game/Schematics.create:(IIII)Lmindustry/game/Schematic;
    1814: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
    1817: aload_0
    1818: iconst_m1
    1819: putfield      #35                 // Field schemX:I
    1822: aload_0
    1823: iconst_m1
    1824: putfield      #38                 // Field schemY:I
    1827: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1830: getstatic     #992                // Field mindustry/input/Binding.breakBlock:Larc/input/KeyBind;
    1833: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    1836: ifne          1851
    1839: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1842: getstatic     #883                // Field mindustry/input/Binding.select:Larc/input/KeyBind;
    1845: invokevirtual #1074               // Method arc/Input.keyRelease:(Larc/input/KeyBind;)Z
    1848: ifeq          2144
    1851: aload_0
    1852: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1855: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    1858: if_acmpne     1920
    1861: aload_0
    1862: getfield      #345                // Field block:Lmindustry/world/Block;
    1865: ifnull        1920
    1868: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1871: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
    1874: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1877: ifeq          1891
    1880: aload_0
    1881: aload_0
    1882: getfield      #346                // Field linePlans:Larc/struct/Seq;
    1885: invokevirtual #1349               // Method flushPlansReverse:(Larc/struct/Seq;)V
    1888: goto          1899
    1891: aload_0
    1892: aload_0
    1893: getfield      #346                // Field linePlans:Larc/struct/Seq;
    1896: invokevirtual #1297               // Method flushPlans:(Larc/struct/Seq;)V
    1899: aload_0
    1900: getfield      #346                // Field linePlans:Larc/struct/Seq;
    1903: invokevirtual #715                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
    1906: pop
    1907: new           #1352               // class mindustry/game/EventType$LineConfirmEvent
    1910: dup
    1911: invokespecial #1354               // Method mindustry/game/EventType$LineConfirmEvent."<init>":()V
    1914: invokestatic  #1355               // Method arc/Events.fire:(Ljava/lang/Object;)V
    1917: goto          1984
    1920: aload_0
    1921: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    1924: getstatic     #198                // Field mindustry/input/PlaceMode.breaking:Lmindustry/input/PlaceMode;
    1927: if_acmpne     1984
    1930: aload_0
    1931: aload_0
    1932: getfield      #28                 // Field selectX:I
    1935: aload_0
    1936: getfield      #32                 // Field selectY:I
    1939: iload_2
    1940: iload_3
    1941: getstatic     #174                // Field arc/Core.input:Larc/Input;
    1944: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
    1947: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    1950: ifne          1958
    1953: bipush        100
    1955: goto          1961
    1958: getstatic     #213                // Field mindustry/Vars.maxSchematicSize:I
    1961: invokevirtual #1360               // Method removeSelection:(IIIII)V
    1964: aload_0
    1965: getfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
    1968: ifnull        1984
    1971: aload_0
    1972: aload_0
    1973: getfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
    1976: invokevirtual #1247               // Method useSchematic:(Lmindustry/game/Schematic;)V
    1979: aload_0
    1980: aconst_null
    1981: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
    1984: aload_0
    1985: iconst_m1
    1986: putfield      #28                 // Field selectX:I
    1989: aload_0
    1990: iconst_m1
    1991: putfield      #32                 // Field selectY:I
    1994: aload_0
    1995: aload_1
    1996: ifnonnull     2003
    1999: aconst_null
    2000: goto          2007
    2003: aload_1
    2004: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2007: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2010: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2013: getfield      #657                // Field arc/math/geom/Vec2.x:F
    2016: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2019: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2022: getfield      #666                // Field arc/math/geom/Vec2.y:F
    2025: invokevirtual #1363               // Method tryDropItems:(Lmindustry/gen/Building;FF)V
    2028: aload_0
    2029: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2032: ifnull        2137
    2035: aload_0
    2036: aload_0
    2037: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2040: getfield      #241                // Field mindustry/entities/units/BuildPlan.x:I
    2043: aload_0
    2044: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2047: getfield      #246                // Field mindustry/entities/units/BuildPlan.y:I
    2050: aload_0
    2051: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2054: getfield      #249                // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
    2057: getfield      #279                // Field mindustry/world/Block.size:I
    2060: aload_0
    2061: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2064: invokevirtual #282                // Method getPlan:(IIILmindustry/entities/units/BuildPlan;)Lmindustry/entities/units/BuildPlan;
    2067: ifnull        2088
    2070: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2073: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    2076: invokevirtual #1333               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
    2079: aload_0
    2080: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2083: iconst_1
    2084: invokevirtual #1367               // Method arc/struct/Queue.remove:(Ljava/lang/Object;Z)Z
    2087: pop
    2088: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2091: invokevirtual #1056               // Method arc/Input.ctrl:()Z
    2094: ifeq          2125
    2097: aload_0
    2098: getfield      #1370               // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
    2101: invokevirtual #1374               // Method mindustry/ui/fragments/BlockInventoryFragment.hide:()V
    2104: aload_0
    2105: getfield      #1379               // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
    2108: invokevirtual #1382               // Method mindustry/ui/fragments/BlockConfigFragment.hideConfig:()V
    2111: aload_0
    2112: getfield      #1387               // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
    2115: aload_0
    2116: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2119: invokevirtual #1391               // Method mindustry/ui/fragments/PlanConfigFragment.showConfig:(Lmindustry/entities/units/BuildPlan;)V
    2122: goto          2132
    2125: aload_0
    2126: getfield      #1387               // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
    2129: invokevirtual #1396               // Method mindustry/ui/fragments/PlanConfigFragment.hide:()V
    2132: aload_0
    2133: aconst_null
    2134: putfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2137: aload_0
    2138: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2141: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2144: aload_0
    2145: invokevirtual #302                // Method isPlacing:()Z
    2148: ifne          2168
    2151: aload_0
    2152: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2155: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    2158: if_acmpne     2168
    2161: aload_0
    2162: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2165: putfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2168: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2171: getfield      #989                // Field mindustry/gen/Player.shooting:Z
    2174: ifeq          2191
    2177: aload_0
    2178: invokevirtual #1397               // Method canShoot:()Z
    2181: ifne          2191
    2184: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2187: iconst_0
    2188: putfield      #989                // Field mindustry/gen/Player.shooting:Z
    2191: aload_0
    2192: invokevirtual #302                // Method isPlacing:()Z
    2195: ifeq          2232
    2198: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2201: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    2204: ifeq          2232
    2207: aload_0
    2208: getstatic     #1400               // Field arc/Graphics$Cursor$SystemCursor.hand:Larc/Graphics$Cursor$SystemCursor;
    2211: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2214: aload_0
    2215: aload_0
    2216: getfield      #1403               // Field selectScale:F
    2219: fconst_1
    2220: ldc_w         #1406               // float 0.2f
    2223: invokestatic  #1407               // Method arc/math/Mathf.lerpDelta:(FFF)F
    2226: putfield      #1403               // Field selectScale:F
    2229: goto          2237
    2232: aload_0
    2233: fconst_0
    2234: putfield      #1403               // Field selectScale:F
    2237: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2240: getstatic     #998                // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
    2243: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2246: ifne          2398
    2249: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2252: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2255: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2258: f2i
    2259: invokestatic  #1409               // Method java/lang/Math.abs:(I)I
    2262: ifle          2398
    2265: aload_0
    2266: aload_0
    2267: getfield      #359                // Field rotation:I
    2270: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2273: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2276: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2279: f2i
    2280: iadd
    2281: iconst_4
    2282: invokestatic  #1411               // Method arc/math/Mathf.mod:(II)I
    2285: putfield      #359                // Field rotation:I
    2288: aload_0
    2289: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2292: ifnull        2324
    2295: aload_0
    2296: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2299: aload_0
    2300: getfield      #237                // Field splan:Lmindustry/entities/units/BuildPlan;
    2303: getfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
    2306: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2309: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2312: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2315: f2i
    2316: iadd
    2317: iconst_4
    2318: invokestatic  #1411               // Method arc/math/Mathf.mod:(II)I
    2321: putfield      #253                // Field mindustry/entities/units/BuildPlan.rotation:I
    2324: aload_0
    2325: invokevirtual #302                // Method isPlacing:()Z
    2328: ifeq          2356
    2331: aload_0
    2332: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2335: getstatic     #342                // Field mindustry/input/PlaceMode.placing:Lmindustry/input/PlaceMode;
    2338: if_acmpne     2356
    2341: aload_0
    2342: aload_0
    2343: getfield      #28                 // Field selectX:I
    2346: aload_0
    2347: getfield      #32                 // Field selectY:I
    2350: invokevirtual #1283               // Method updateLine:(II)V
    2353: goto          2398
    2356: aload_0
    2357: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2360: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    2363: ifne          2398
    2366: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2369: getfield      #593                // Field mindustry/core/UI.chatfrag:Lmindustry/ui/fragments/ChatFragment;
    2372: invokevirtual #597                // Method mindustry/ui/fragments/ChatFragment.shown:()Z
    2375: ifne          2398
    2378: aload_0
    2379: aload_0
    2380: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2383: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2386: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2389: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2392: invokestatic  #1415               // Method arc/math/Mathf.sign:(F)I
    2395: invokevirtual #1418               // Method rotatePlans:(Larc/struct/Seq;I)V
    2398: aload_0
    2399: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2402: invokevirtual #178                // Method arc/Input.mouseX:()I
    2405: i2f
    2406: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2409: invokevirtual #188                // Method arc/Input.mouseY:()I
    2412: i2f
    2413: invokevirtual #1194               // Method tileAt:(FF)Lmindustry/world/Tile;
    2416: astore        6
    2418: aload_0
    2419: getstatic     #18                 // Field arc/Graphics$Cursor$SystemCursor.arrow:Larc/Graphics$Cursor$SystemCursor;
    2422: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2425: aload         6
    2427: ifnull        2919
    2430: aload         6
    2432: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2435: ifnull        2467
    2438: aload         6
    2440: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2443: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2446: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2449: invokevirtual #1422               // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
    2452: ifeq          2467
    2455: aload_0
    2456: aload         6
    2458: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2461: invokevirtual #1426               // Method mindustry/gen/Building.getCursor:()Larc/Graphics$Cursor;
    2464: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2467: aload_0
    2468: aload         6
    2470: invokevirtual #1430               // Method canRepairDerelict:(Lmindustry/world/Tile;)Z
    2473: ifeq          2507
    2476: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2479: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
    2482: ifne          2507
    2485: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2488: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
    2491: invokevirtual #1433               // Method mindustry/gen/Unit.canBuild:()Z
    2494: ifeq          2507
    2497: aload_0
    2498: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2501: getfield      #1436               // Field mindustry/core/UI.repairCursor:Larc/Graphics$Cursor;
    2504: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2507: aload_0
    2508: invokevirtual #302                // Method isPlacing:()Z
    2511: ifeq          2523
    2514: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2517: invokevirtual #339                // Method mindustry/gen/Player.isBuilder:()Z
    2520: ifne          2533
    2523: aload_0
    2524: getfield      #101                // Field selectPlans:Larc/struct/Seq;
    2527: invokevirtual #105                // Method arc/struct/Seq.isEmpty:()Z
    2530: ifne          2540
    2533: aload_0
    2534: getstatic     #1400               // Field arc/Graphics$Cursor$SystemCursor.hand:Larc/Graphics$Cursor$SystemCursor;
    2537: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2540: aload_0
    2541: invokevirtual #302                // Method isPlacing:()Z
    2544: ifne          2566
    2547: aload_0
    2548: aload         6
    2550: invokevirtual #1439               // Method canMine:(Lmindustry/world/Tile;)Z
    2553: ifeq          2566
    2556: aload_0
    2557: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2560: getfield      #1442               // Field mindustry/core/UI.drillCursor:Larc/Graphics$Cursor;
    2563: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2566: aload_0
    2567: getfield      #700                // Field commandMode:Z
    2570: ifeq          2740
    2573: aload_0
    2574: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    2577: invokevirtual #1445               // Method arc/struct/Seq.any:()Z
    2580: ifeq          2740
    2583: aload         6
    2585: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2588: ifnull        2629
    2591: aload         6
    2593: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2596: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2599: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2602: invokevirtual #1448               // Method mindustry/gen/Building.inFogTo:(Lmindustry/game/Team;)Z
    2605: ifne          2629
    2608: aload         6
    2610: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2613: getfield      #1451               // Field mindustry/gen/Building.team:Lmindustry/game/Team;
    2616: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2619: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2622: if_acmpeq     2629
    2625: iconst_1
    2626: goto          2630
    2629: iconst_0
    2630: istore        7
    2632: iload         7
    2634: ifne          2676
    2637: aload_0
    2638: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2641: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
    2644: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2647: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
    2650: invokevirtual #1453               // Method selectedEnemyUnit:(FF)Lmindustry/gen/Unit;
    2653: astore        8
    2655: aload         8
    2657: ifnull        2676
    2660: aload_0
    2661: getfield      #702                // Field selectedUnits:Larc/struct/Seq;
    2664: aload         8
    2666: invokedynamic #1457,  0           // InvokeDynamic #17:get:(Lmindustry/gen/Unit;)Larc/func/Boolf;
    2671: invokevirtual #1460               // Method arc/struct/Seq.contains:(Larc/func/Boolf;)Z
    2674: istore        7
    2676: iload         7
    2678: ifeq          2691
    2681: aload_0
    2682: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2685: getfield      #1464               // Field mindustry/core/UI.targetCursor:Larc/Graphics$Cursor;
    2688: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2691: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2694: getstatic     #1467               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
    2697: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
    2700: ifeq          2740
    2703: getstatic     #1467               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
    2706: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
    2709: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
    2712: getfield      #1470               // Field arc/input/KeyCode.type:Larc/input/KeyCode$KeyType;
    2715: getstatic     #1475               // Field arc/input/KeyCode$KeyType.mouse:Larc/input/KeyCode$KeyType;
    2718: if_acmpeq     2740
    2721: aload_0
    2722: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2725: invokevirtual #178                // Method arc/Input.mouseX:()I
    2728: i2f
    2729: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2732: invokevirtual #188                // Method arc/Input.mouseY:()I
    2735: i2f
    2736: iconst_1
    2737: invokevirtual #1480               // Method commandTap:(FFZ)V
    2740: aload_0
    2741: aload         6
    2743: getfield      #1484               // Field mindustry/world/Tile.x:S
    2746: aload         6
    2748: getfield      #1487               // Field mindustry/world/Tile.y:S
    2751: invokevirtual #305                // Method getPlan:(II)Lmindustry/entities/units/BuildPlan;
    2754: ifnull        2774
    2757: aload_0
    2758: getfield      #194                // Field mode:Lmindustry/input/PlaceMode;
    2761: getstatic     #299                // Field mindustry/input/PlaceMode.none:Lmindustry/input/PlaceMode;
    2764: if_acmpne     2774
    2767: aload_0
    2768: getstatic     #1400               // Field arc/Graphics$Cursor$SystemCursor.hand:Larc/Graphics$Cursor$SystemCursor;
    2771: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2774: aload_0
    2775: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2778: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2781: getfield      #657                // Field arc/math/geom/Vec2.x:F
    2784: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2787: invokevirtual #541                // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
    2790: getfield      #666                // Field arc/math/geom/Vec2.y:F
    2793: invokevirtual #1489               // Method canTapPlayer:(FF)Z
    2796: ifeq          2809
    2799: aload_0
    2800: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
    2803: getfield      #1492               // Field mindustry/core/UI.unloadCursor:Larc/Graphics$Cursor;
    2806: putfield      #24                 // Field cursorType:Larc/Graphics$Cursor;
    2809: aload         6
    2811: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2814: ifnull        2919
    2817: aload         6
    2819: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2822: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
    2825: invokevirtual #1495               // Method mindustry/world/Tile.interactable:(Lmindustry/game/Team;)Z
    2828: ifeq          2919
    2831: aload_0
    2832: invokevirtual #302                // Method isPlacing:()Z
    2835: ifne          2919
    2838: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2841: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2844: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2847: invokestatic  #578                // Method java/lang/Math.abs:(F)F
    2850: fconst_0
    2851: fcmpl
    2852: ifle          2919
    2855: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2858: getstatic     #1014               // Field mindustry/input/Binding.rotatePlaced:Larc/input/KeyBind;
    2861: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
    2864: ifeq          2919
    2867: aload         6
    2869: invokevirtual #314                // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
    2872: getfield      #260                // Field mindustry/world/Block.rotate:Z
    2875: ifeq          2919
    2878: aload         6
    2880: invokevirtual #314                // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
    2883: getfield      #1496               // Field mindustry/world/Block.quickRotate:Z
    2886: ifeq          2919
    2889: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
    2892: aload         6
    2894: getfield      #1203               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
    2897: getstatic     #174                // Field arc/Core.input:Larc/Input;
    2900: getstatic     #1017               // Field mindustry/input/Binding.rotate:Larc/input/KeyBind;
    2903: invokevirtual #1011               // Method arc/Input.axisTap:(Larc/input/KeyBind;)F
    2906: fconst_0
    2907: fcmpl
    2908: ifle          2915
    2911: iconst_1
    2912: goto          2916
    2915: iconst_0
    2916: invokestatic  #1499               // Method mindustry/gen/Call.rotateBlock:(Lmindustry/gen/Player;Lmindustry/gen/Building;Z)V
    2919: return

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
      20: putfield      #1191               // Field tappedOne:Z
      23: aload         4
      25: getstatic     #1503               // Field arc/input/KeyCode.mouseLeft:Larc/input/KeyCode;
      28: if_acmpne     47
      31: iload_3
      32: iconst_2
      33: if_icmplt     43
      36: aload_0
      37: invokevirtual #1506               // Method selectTypedUnits:()V
      40: goto          47
      43: aload_0
      44: invokevirtual #1509               // Method tapCommandUnit:()V
      47: aload_0
      48: fload_1
      49: fload_2
      50: iload_3
      51: aload         4
      53: invokespecial #1512               // Method mindustry/input/InputHandler.tap:(FFILarc/input/KeyCode;)Z
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
      20: getstatic     #1516               // Field arc/input/KeyCode.mouseRight:Larc/input/KeyCode;
      23: if_acmpne     32
      26: aload_0
      27: fload_1
      28: fload_2
      29: invokevirtual #1519               // Method commandTap:(FF)V
      32: aload         4
      34: getstatic     #1467               // Field mindustry/input/Binding.commandQueue:Larc/input/KeyBind;
      37: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      40: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
      43: if_acmpne     53
      46: aload_0
      47: fload_1
      48: fload_2
      49: iconst_1
      50: invokevirtual #1480               // Method commandTap:(FFZ)V
      53: aload_0
      54: fload_1
      55: fload_2
      56: iload_3
      57: aload         4
      59: invokespecial #1522               // Method mindustry/input/InputHandler.touchDown:(FFILarc/input/KeyCode;)Z
      62: ireturn

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
       1: invokespecial #1525               // Method mindustry/input/InputHandler.updateState:()V
       4: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       7: invokevirtual #986                // Method mindustry/core/GameState.isMenu:()Z
      10: ifeq          48
      13: aload_0
      14: aconst_null
      15: putfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
      18: aload_0
      19: iconst_0
      20: putfield      #916                // Field droppingItem:Z
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
       4: getfield      #1528               // Field mindustry/type/UnitType.omniMovement:Z
       7: istore_2
       8: aload_1
       9: invokevirtual #1531               // Method mindustry/gen/Unit.speed:()F
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
      36: instanceof    #1534               // class mindustry/gen/Mechc
      39: ifeq          53
      42: aload_1
      43: invokevirtual #1536               // Method mindustry/gen/Unit.isFlying:()Z
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
      88: invokevirtual #1539               // Method arc/math/geom/Vec2.sub:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
      91: fload_3
      92: invokevirtual #1543               // Method arc/math/geom/Vec2.limit:(F)Larc/math/geom/Vec2;
      95: pop
      96: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      99: aload         7
     101: ldc           #63                 // float 15.0f
     103: invokevirtual #1546               // Method mindustry/gen/Player.within:(Larc/math/geom/Position;F)Z
     106: ifeq          142
     109: aload_0
     110: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
     113: invokevirtual #605                // Method arc/math/geom/Vec2.setZero:()Larc/math/geom/Vec2;
     116: pop
     117: aload_1
     118: getfield      #1550               // Field mindustry/gen/Unit.vel:Larc/math/geom/Vec2;
     121: getstatic     #1553               // Field arc/math/geom/Vec2.ZERO:Larc/math/geom/Vec2;
     124: aload_1
     125: invokevirtual #1531               // Method mindustry/gen/Unit.speed:()F
     128: aload_1
     129: invokevirtual #1556               // Method mindustry/gen/Unit.type:()Lmindustry/type/UnitType;
     132: getfield      #1559               // Field mindustry/type/UnitType.accel:F
     135: fmul
     136: fconst_2
     137: fdiv
     138: invokevirtual #1562               // Method arc/math/geom/Vec2.approachDelta:(Larc/math/geom/Vec2;F)Larc/math/geom/Vec2;
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
     189: invokevirtual #1539               // Method arc/math/geom/Vec2.sub:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
     192: ldc_w         #1566               // float 0.04f
     195: fload_3
     196: fmul
     197: invokevirtual #615                // Method arc/math/geom/Vec2.scl:(F)Larc/math/geom/Vec2;
     200: invokevirtual #619                // Method arc/math/geom/Vec2.add:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
     203: fload_3
     204: invokevirtual #1543               // Method arc/math/geom/Vec2.limit:(F)Larc/math/geom/Vec2;
     207: pop
     208: aload_1
     209: getfield      #869                // Field mindustry/gen/Unit.x:F
     212: aload_1
     213: getfield      #870                // Field mindustry/gen/Unit.y:F
     216: invokestatic  #1567               // Method arc/math/Angles.mouseAngle:(FF)F
     219: fstore        7
     221: iload_2
     222: ifeq          263
     225: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     228: getfield      #989                // Field mindustry/gen/Player.shooting:Z
     231: ifeq          263
     234: aload_1
     235: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     238: invokevirtual #1571               // Method mindustry/type/UnitType.hasWeapons:()Z
     241: ifeq          263
     244: aload_1
     245: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     248: getfield      #1574               // Field mindustry/type/UnitType.faceTarget:Z
     251: ifeq          263
     254: iload         6
     256: ifne          263
     259: iconst_1
     260: goto          264
     263: iconst_0
     264: istore        8
     266: iload         8
     268: ifeq          280
     271: aload_1
     272: fload         7
     274: invokevirtual #1577               // Method mindustry/gen/Unit.lookAt:(F)V
     277: goto          288
     280: aload_1
     281: aload_1
     282: invokevirtual #1580               // Method mindustry/gen/Unit.prefRotation:()F
     285: invokevirtual #1577               // Method mindustry/gen/Unit.lookAt:(F)V
     288: aload_1
     289: aload_0
     290: getfield      #12                 // Field movement:Larc/math/geom/Vec2;
     293: invokevirtual #1583               // Method mindustry/gen/Unit.movePref:(Larc/math/geom/Vec2;)V
     296: aload_1
     297: getstatic     #174                // Field arc/Core.input:Larc/Input;
     300: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
     303: getstatic     #174                // Field arc/Core.input:Larc/Input;
     306: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
     309: iconst_1
     310: invokevirtual #1587               // Method mindustry/gen/Unit.aim:(FFZ)V
     313: aload_1
     314: iconst_1
     315: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     318: getfield      #989                // Field mindustry/gen/Player.shooting:Z
     321: ifeq          333
     324: iload         6
     326: ifne          333
     329: iconst_1
     330: goto          334
     333: iconst_0
     334: invokevirtual #1590               // Method mindustry/gen/Unit.controlWeapons:(ZZ)V
     337: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     340: getstatic     #174                // Field arc/Core.input:Larc/Input;
     343: getstatic     #483                // Field mindustry/input/Binding.boost:Larc/input/KeyBind;
     346: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     349: putfield      #1594               // Field mindustry/gen/Player.boosting:Z
     352: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     355: aload_1
     356: invokevirtual #1597               // Method mindustry/gen/Unit.aimX:()F
     359: putfield      #1600               // Field mindustry/gen/Player.mouseX:F
     362: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     365: aload_1
     366: invokevirtual #1602               // Method mindustry/gen/Unit.aimY:()F
     369: putfield      #1605               // Field mindustry/gen/Player.mouseY:F
     372: aload_1
     373: instanceof    #783                // class mindustry/gen/Payloadc
     376: ifeq          527
     379: getstatic     #174                // Field arc/Core.input:Larc/Input;
     382: getstatic     #1607               // Field mindustry/input/Binding.pickupCargo:Larc/input/KeyBind;
     385: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     388: ifeq          402
     391: aload_0
     392: invokevirtual #1610               // Method tryPickupPayload:()V
     395: aload_0
     396: invokestatic  #873                // Method arc/util/Time.millis:()J
     399: putfield      #1613               // Field lastPayloadKeyTapMillis:J
     402: getstatic     #174                // Field arc/Core.input:Larc/Input;
     405: getstatic     #1607               // Field mindustry/input/Binding.pickupCargo:Larc/input/KeyBind;
     408: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     411: ifeq          453
     414: aload_0
     415: getfield      #1616               // Field lastPayloadKeyHoldMillis:J
     418: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     421: ldc2_w        #1619               // long 20l
     424: lcmp
     425: ifle          453
     428: aload_0
     429: getfield      #1613               // Field lastPayloadKeyTapMillis:J
     432: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     435: ldc2_w        #1621               // long 200l
     438: lcmp
     439: ifle          453
     442: aload_0
     443: invokevirtual #1610               // Method tryPickupPayload:()V
     446: aload_0
     447: invokestatic  #873                // Method arc/util/Time.millis:()J
     450: putfield      #1616               // Field lastPayloadKeyHoldMillis:J
     453: getstatic     #174                // Field arc/Core.input:Larc/Input;
     456: getstatic     #1623               // Field mindustry/input/Binding.dropCargo:Larc/input/KeyBind;
     459: invokevirtual #444                // Method arc/Input.keyTap:(Larc/input/KeyBind;)Z
     462: ifeq          476
     465: aload_0
     466: invokevirtual #1626               // Method tryDropPayload:()V
     469: aload_0
     470: invokestatic  #873                // Method arc/util/Time.millis:()J
     473: putfield      #1613               // Field lastPayloadKeyTapMillis:J
     476: getstatic     #174                // Field arc/Core.input:Larc/Input;
     479: getstatic     #1623               // Field mindustry/input/Binding.dropCargo:Larc/input/KeyBind;
     482: invokevirtual #209                // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
     485: ifeq          527
     488: aload_0
     489: getfield      #1616               // Field lastPayloadKeyHoldMillis:J
     492: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     495: ldc2_w        #1619               // long 20l
     498: lcmp
     499: ifle          527
     502: aload_0
     503: getfield      #1613               // Field lastPayloadKeyTapMillis:J
     506: invokestatic  #863                // Method arc/util/Time.timeSinceMillis:(J)J
     509: ldc2_w        #1621               // long 200l
     512: lcmp
     513: ifle          527
     516: aload_0
     517: invokevirtual #1626               // Method tryDropPayload:()V
     520: aload_0
     521: invokestatic  #873                // Method arc/util/Time.millis:()J
     524: putfield      #1616               // Field lastPayloadKeyHoldMillis:J
     527: return

  private static boolean lambda$pollInputPlayer$25(mindustry.gen.Unit, mindustry.gen.Unit);
    Code:
       0: aload_1
       1: aload_0
       2: invokevirtual #1629               // Method mindustry/gen/Unit.canTarget:(Lmindustry/gen/Teamc;)Z
       5: ireturn

  private static void lambda$pollInputPlayer$24(int, int, mindustry.entities.units.BuildPlan);
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

  private static boolean lambda$buildPlacementUI$23();
    Code:
       0: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       3: invokevirtual #933                // Method mindustry/core/GameState.isCampaign:()Z
       6: ireturn

  private static void lambda$buildPlacementUI$22();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #936                // Field mindustry/core/UI.planet:Lmindustry/ui/dialogs/PlanetDialog;
       6: invokevirtual #1633               // Method mindustry/ui/dialogs/PlanetDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static boolean lambda$buildPlacementUI$21();
    Code:
       0: getstatic     #511                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       3: invokevirtual #933                // Method mindustry/core/GameState.isCampaign:()Z
       6: ireturn

  private static void lambda$buildPlacementUI$20();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #946                // Field mindustry/core/UI.research:Lmindustry/ui/dialogs/ResearchDialog;
       6: invokevirtual #1637               // Method mindustry/ui/dialogs/ResearchDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static void lambda$buildPlacementUI$19();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #1638               // Field mindustry/core/UI.database:Lmindustry/ui/dialogs/DatabaseDialog;
       6: invokevirtual #1642               // Method mindustry/ui/dialogs/DatabaseDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static void lambda$buildPlacementUI$18();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #955                // Field mindustry/core/UI.schematics:Lmindustry/ui/dialogs/SchematicsDialog;
       6: invokevirtual #1645               // Method mindustry/ui/dialogs/SchematicsDialog.show:()Larc/scene/ui/Dialog;
       9: pop
      10: return

  private static void lambda$update$17(java.lang.String);
    Code:
       0: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: getstatic     #174                // Field arc/Core.input:Larc/Input;
       6: invokevirtual #1036               // Method arc/Input.mouseWorldX:()F
       9: getstatic     #174                // Field arc/Core.input:Larc/Input;
      12: invokevirtual #1040               // Method arc/Input.mouseWorldY:()F
      15: aload_0
      16: invokestatic  #1646               // Method mindustry/core/UI.formatIcons:(Ljava/lang/String;)Ljava/lang/String;
      19: invokestatic  #1070               // Method mindustry/gen/Call.pingLocation:(Lmindustry/gen/Player;FFLjava/lang/String;)V
      22: return

  private void lambda$update$16(int);
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
      27: invokevirtual #1650               // Method arc/struct/Seq.addAll:([Ljava/lang/Object;)Larc/struct/Seq;
      30: pop
      31: return

  private static int lambda$update$15(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: getfield      #1653               // Field mindustry/gen/Unit.id:I
       4: ireturn

  private static boolean lambda$update$14(mindustry.gen.Building);
    Code:
       0: getstatic     #725                // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
       3: aload_0
       4: getfield      #1656               // Field mindustry/gen/Building.x:F
       7: aload_0
       8: invokevirtual #1657               // Method mindustry/gen/Building.hitSize:()F
      11: fconst_2
      12: fdiv
      13: fsub
      14: aload_0
      15: getfield      #1660               // Field mindustry/gen/Building.y:F
      18: aload_0
      19: invokevirtual #1657               // Method mindustry/gen/Building.hitSize:()F
      22: fconst_2
      23: fdiv
      24: fsub
      25: aload_0
      26: invokevirtual #1657               // Method mindustry/gen/Building.hitSize:()F
      29: aload_0
      30: invokevirtual #1657               // Method mindustry/gen/Building.hitSize:()F
      33: invokevirtual #1661               // Method arc/math/geom/Rect.overlaps:(FFFF)Z
      36: ireturn

  private static boolean lambda$update$13(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: instanceof    #783                // class mindustry/gen/Payloadc
       4: ireturn

  private static boolean lambda$update$12(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: getfield      #674                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
       4: getfield      #770                // Field mindustry/type/UnitType.controlSelectGlobal:Z
       7: ifne          14
      10: iconst_1
      11: goto          15
      14: iconst_0
      15: ireturn

  private static boolean lambda$update$11(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: invokevirtual #1665               // Method mindustry/gen/Unit.allowCommand:()Z
       4: ifeq          27
       7: aload_0
       8: invokevirtual #844                // Method mindustry/gen/Unit.isValid:()Z
      11: ifeq          27
      14: aload_0
      15: getfield      #1668               // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
      18: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      21: invokevirtual #628                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      24: if_acmpeq     31
      27: iconst_1
      28: goto          32
      31: iconst_0
      32: ireturn

  private void lambda$buildUI$10(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: aload_0
       2: invokedynamic #1669,  0           // InvokeDynamic #18:get:(Lmindustry/input/DesktopInput;)Larc/func/Boolp;
       7: invokevirtual #1672               // Method arc/scene/ui/layout/Table.visible:(Larc/func/Boolp;)Larc/scene/Element;
      10: pop
      11: aload_1
      12: invokevirtual #1675               // Method arc/scene/ui/layout/Table.bottom:()Larc/scene/ui/layout/Table;
      15: pop
      16: aload_1
      17: getstatic     #1678               // Field mindustry/ui/Styles.black6:Larc/scene/style/Drawable;
      20: aload_0
      21: invokedynamic #1682,  0           // InvokeDynamic #19:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      26: invokevirtual #1683               // Method arc/scene/ui/layout/Table.table:(Larc/scene/style/Drawable;Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      29: ldc_w         #395                // float 6.0f
      32: invokevirtual #1687               // Method arc/scene/ui/layout/Cell.margin:(F)Larc/scene/ui/layout/Cell;
      35: pop
      36: return

  private void lambda$buildUI$9(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: invokevirtual #1127               // Method arc/scene/ui/layout/Table.defaults:()Larc/scene/ui/layout/Cell;
       4: invokevirtual #1137               // Method arc/scene/ui/layout/Cell.left:()Larc/scene/ui/layout/Cell;
       7: pop
       8: aload_1
       9: invokedynamic #1689,  0           // InvokeDynamic #20:get:()Larc/func/Prov;
      14: invokevirtual #1692               // Method arc/scene/ui/layout/Table.label:(Larc/func/Prov;)Larc/scene/ui/layout/Cell;
      17: getstatic     #1696               // Field mindustry/ui/Styles.outlineLabel:Larc/scene/ui/Label$LabelStyle;
      20: invokevirtual #1700               // Method arc/scene/ui/layout/Cell.style:(Larc/scene/style/Style;)Larc/scene/ui/layout/Cell;
      23: invokedynamic #1704,  0           // InvokeDynamic #21:get:()Larc/func/Boolp;
      28: invokevirtual #1178               // Method arc/scene/ui/layout/Cell.visible:(Larc/func/Boolp;)Larc/scene/ui/layout/Cell;
      31: pop
      32: aload_1
      33: invokevirtual #1705               // Method arc/scene/ui/layout/Table.row:()Larc/scene/ui/layout/Table;
      36: pop
      37: aload_1
      38: aload_0
      39: invokedynamic #1708,  0           // InvokeDynamic #22:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      44: invokevirtual #1709               // Method arc/scene/ui/layout/Table.table:(Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      47: pop
      48: return

  private void lambda$buildUI$8(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: ldc_w         #1712               // String @schematic.add
       4: getstatic     #1714               // Field mindustry/gen/Icon.save:Larc/scene/style/TextureRegionDrawable;
       7: aload_0
       8: invokedynamic #1717,  0           // InvokeDynamic #23:run:(Lmindustry/input/DesktopInput;)Ljava/lang/Runnable;
      13: invokevirtual #1720               // Method arc/scene/ui/layout/Table.button:(Ljava/lang/String;Larc/scene/style/Drawable;Ljava/lang/Runnable;)Larc/scene/ui/layout/Cell;
      16: iconst_2
      17: invokevirtual #1723               // Method arc/scene/ui/layout/Cell.colspan:(I)Larc/scene/ui/layout/Cell;
      20: ldc_w         #1727               // float 250.0f
      23: ldc_w         #1728               // float 50.0f
      26: invokevirtual #1729               // Method arc/scene/ui/layout/Cell.size:(FF)Larc/scene/ui/layout/Cell;
      29: aload_0
      30: invokedynamic #1732,  0           // InvokeDynamic #24:get:(Lmindustry/input/DesktopInput;)Larc/func/Boolf;
      35: invokevirtual #1735               // Method arc/scene/ui/layout/Cell.disabled:(Larc/func/Boolf;)Larc/scene/ui/layout/Cell;
      38: pop
      39: return

  private boolean lambda$buildUI$7(arc.scene.ui.TextButton);
    Code:
       0: aload_0
       1: getfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
       4: ifnull        17
       7: aload_0
       8: getfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
      11: getfield      #1739               // Field mindustry/game/Schematic.file:Larc/files/Fi;
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
       0: getstatic     #1745               // Field arc/Core.bundle:Larc/util/I18NBundle;
       3: ldc_w         #1749               // String schematic.flip
       6: iconst_2
       7: anewarray     #1751               // class java/lang/Object
      10: dup
      11: iconst_0
      12: getstatic     #1254               // Field mindustry/input/Binding.schematicFlipX:Larc/input/KeyBind;
      15: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      18: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
      21: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
      24: aastore
      25: dup
      26: iconst_1
      27: getstatic     #1261               // Field mindustry/input/Binding.schematicFlipY:Larc/input/KeyBind;
      30: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      33: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
      36: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
      39: aastore
      40: invokevirtual #1757               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
      43: areturn

  private boolean lambda$buildUI$4();
    Code:
       0: getstatic     #71                 // Field mindustry/Vars.ui:Lmindustry/core/UI;
       3: getfield      #75                 // Field mindustry/core/UI.hudfrag:Lmindustry/ui/fragments/HudFragment;
       6: invokevirtual #81                 // Method mindustry/ui/fragments/HudFragment.shown:()Z
       9: ifeq          33
      12: aload_0
      13: getfield      #1239               // Field lastSchematic:Lmindustry/game/Schematic;
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
       1: getfield      #1763               // Field arc/scene/ui/layout/Table.color:Larc/graphics/Color;
       4: fconst_0
       5: putfield      #1765               // Field arc/graphics/Color.a:F
       8: aload_1
       9: aload_0
      10: aload_1
      11: invokedynamic #1768,  0           // InvokeDynamic #25:get:(Lmindustry/input/DesktopInput;Larc/scene/ui/layout/Table;)Larc/func/Boolp;
      16: invokevirtual #1672               // Method arc/scene/ui/layout/Table.visible:(Larc/func/Boolp;)Larc/scene/Element;
      19: pop
      20: aload_1
      21: invokevirtual #1675               // Method arc/scene/ui/layout/Table.bottom:()Larc/scene/ui/layout/Table;
      24: pop
      25: aload_1
      26: getstatic     #1678               // Field mindustry/ui/Styles.black6:Larc/scene/style/Drawable;
      29: aload_0
      30: invokedynamic #1771,  0           // InvokeDynamic #26:get:(Lmindustry/input/DesktopInput;)Larc/func/Cons;
      35: invokevirtual #1683               // Method arc/scene/ui/layout/Table.table:(Larc/scene/style/Drawable;Larc/func/Cons;)Larc/scene/ui/layout/Cell;
      38: ldc_w         #1772               // float 10.0f
      41: invokevirtual #1687               // Method arc/scene/ui/layout/Cell.margin:(F)Larc/scene/ui/layout/Cell;
      44: pop
      45: return

  private void lambda$buildUI$2(arc.scene.ui.layout.Table);
    Code:
       0: new           #1773               // class java/lang/StringBuilder
       3: dup
       4: invokespecial #1775               // Method java/lang/StringBuilder."<init>":()V
       7: astore_2
       8: aload_1
       9: invokevirtual #1127               // Method arc/scene/ui/layout/Table.defaults:()Larc/scene/ui/layout/Cell;
      12: invokevirtual #1137               // Method arc/scene/ui/layout/Cell.left:()Larc/scene/ui/layout/Cell;
      15: pop
      16: aload_1
      17: aload_0
      18: aload_2
      19: invokedynamic #1776,  0           // InvokeDynamic #27:get:(Lmindustry/input/DesktopInput;Ljava/lang/StringBuilder;)Larc/func/Prov;
      24: invokevirtual #1692               // Method arc/scene/ui/layout/Table.label:(Larc/func/Prov;)Larc/scene/ui/layout/Cell;
      27: getstatic     #1696               // Field mindustry/ui/Styles.outlineLabel:Larc/scene/ui/Label$LabelStyle;
      30: invokevirtual #1700               // Method arc/scene/ui/layout/Cell.style:(Larc/scene/style/Style;)Larc/scene/ui/layout/Cell;
      33: pop
      34: return

  private java.lang.CharSequence lambda$buildUI$1(java.lang.StringBuilder);
    Code:
       0: aload_0
       1: invokevirtual #1779               // Method showHint:()Z
       4: ifne          9
       7: aload_1
       8: areturn
       9: aload_1
      10: iconst_0
      11: invokevirtual #1782               // Method java/lang/StringBuilder.setLength:(I)V
      14: aload_0
      15: getfield      #119                // Field isBuilding:Z
      18: ifne          80
      21: getstatic     #87                 // Field arc/Core.settings:Larc/Settings;
      24: ldc           #122                // String buildautopause
      26: invokevirtual #95                 // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      29: ifne          80
      32: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      35: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      38: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
      41: ifne          80
      44: aload_1
      45: getstatic     #1745               // Field arc/Core.bundle:Larc/util/I18NBundle;
      48: ldc_w         #1786               // String enablebuilding
      51: iconst_1
      52: anewarray     #1751               // class java/lang/Object
      55: dup
      56: iconst_0
      57: getstatic     #1274               // Field mindustry/input/Binding.pauseBuilding:Larc/input/KeyBind;
      60: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
      63: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
      66: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
      69: aastore
      70: invokevirtual #1757               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
      73: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      76: pop
      77: goto          212
      80: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      83: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      86: invokevirtual #128                // Method mindustry/gen/Unit.isBuilding:()Z
      89: ifeq          212
      92: aload_1
      93: getstatic     #1745               // Field arc/Core.bundle:Larc/util/I18NBundle;
      96: aload_0
      97: getfield      #119                // Field isBuilding:Z
     100: ifeq          109
     103: ldc_w         #1792               // String pausebuilding
     106: goto          112
     109: ldc_w         #1794               // String resumebuilding
     112: iconst_1
     113: anewarray     #1751               // class java/lang/Object
     116: dup
     117: iconst_0
     118: getstatic     #1274               // Field mindustry/input/Binding.pauseBuilding:Larc/input/KeyBind;
     121: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     124: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
     127: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
     130: aastore
     131: invokevirtual #1757               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     134: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     137: ldc_w         #1796               // String \n
     140: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     143: getstatic     #1745               // Field arc/Core.bundle:Larc/util/I18NBundle;
     146: ldc_w         #1798               // String cancelbuilding
     149: iconst_1
     150: anewarray     #1751               // class java/lang/Object
     153: dup
     154: iconst_0
     155: getstatic     #1234               // Field mindustry/input/Binding.clearBuilding:Larc/input/KeyBind;
     158: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     161: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
     164: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
     167: aastore
     168: invokevirtual #1757               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     171: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     174: ldc_w         #1796               // String \n
     177: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     180: getstatic     #1745               // Field arc/Core.bundle:Larc/util/I18NBundle;
     183: ldc_w         #1800               // String selectschematic
     186: iconst_1
     187: anewarray     #1751               // class java/lang/Object
     190: dup
     191: iconst_0
     192: getstatic     #203                // Field mindustry/input/Binding.schematicSelect:Larc/input/KeyBind;
     195: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     198: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
     201: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
     204: aastore
     205: invokevirtual #1757               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     208: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     211: pop
     212: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     215: invokevirtual #114                // Method mindustry/gen/Player.dead:()Z
     218: ifne          285
     221: getstatic     #110                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     224: invokevirtual #124                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     227: invokevirtual #132                // Method mindustry/gen/Unit.spawnedByCore:()Z
     230: ifne          285
     233: aload_1
     234: aload_1
     235: invokevirtual #1802               // Method java/lang/StringBuilder.length:()I
     238: ifeq          247
     241: ldc_w         #1796               // String \n
     244: goto          250
     247: ldc_w         #1059               // String
     250: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     253: getstatic     #1745               // Field arc/Core.bundle:Larc/util/I18NBundle;
     256: ldc_w         #1805               // String respawn
     259: iconst_1
     260: anewarray     #1751               // class java/lang/Object
     263: dup
     264: iconst_0
     265: getstatic     #910                // Field mindustry/input/Binding.respawn:Larc/input/KeyBind;
     268: getfield      #686                // Field arc/input/KeyBind.value:Larc/input/KeyBind$Axis;
     271: getfield      #692                // Field arc/input/KeyBind$Axis.key:Larc/input/KeyCode;
     274: invokevirtual #1753               // Method arc/input/KeyCode.toString:()Ljava/lang/String;
     277: aastore
     278: invokevirtual #1757               // Method arc/util/I18NBundle.format:(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;
     281: invokevirtual #1788               // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
     284: pop
     285: aload_1
     286: areturn

  private boolean lambda$buildUI$0(arc.scene.ui.layout.Table);
    Code:
       0: aload_1
       1: getfield      #1763               // Field arc/scene/ui/layout/Table.color:Larc/graphics/Color;
       4: aload_1
       5: getfield      #1763               // Field arc/scene/ui/layout/Table.color:Larc/graphics/Color;
       8: getfield      #1765               // Field arc/graphics/Color.a:F
      11: aload_0
      12: invokevirtual #1779               // Method showHint:()Z
      15: invokestatic  #1806               // Method arc/math/Mathf.num:(Z)I
      18: i2f
      19: ldc_w         #1810               // float 0.15f
      22: invokestatic  #1407               // Method arc/math/Mathf.lerpDelta:(FFF)F
      25: dup_x1
      26: putfield      #1765               // Field arc/graphics/Color.a:F
      29: ldc_w         #1811               // float 0.001f
      32: fcmpl
      33: ifle          40
      36: iconst_1
      37: goto          41
      40: iconst_0
      41: ireturn
}
