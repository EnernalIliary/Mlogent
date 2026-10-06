Compiled from "InputHandler.java"
public abstract class mindustry.input.InputHandler implements arc.input.InputProcessor,arc.input.GestureDetector$GestureListener {
  static arc.struct.ObjectMap<arc.math.geom.Vec2, arc.struct.Seq<mindustry.gen.Unit>> queuedCommands;

  static final float playerSelectRange;

  static final float unitSelectRadScl;

  static final arc.struct.Seq<mindustry.ai.UnitStance> stancesOut;

  static final arc.struct.IntSeq removed;

  static final arc.struct.IntSet intSet;

  static final int maxLength;

  static final arc.math.geom.Rect r1;

  static final arc.math.geom.Rect r2;

  static final arc.struct.Seq<mindustry.gen.Unit> tmpUnits;

  static final arc.struct.Seq<mindustry.gen.Building> tmpBuildings;

  static final arc.input.KeyBind[] controlGroupBindings;

  public boolean logicCutscene;

  public boolean logicHideHud;

  public arc.math.geom.Vec2 logicCamPan;

  public float logicCamSpeed;

  public float logicCutsceneZoom;

  public arc.struct.Seq<arc.func.Boolp> inputLocks;

  public arc.util.Interval controlInterval;

  public mindustry.world.Block block;

  public boolean overrideLineRotation;

  public int rotation;

  public boolean droppingItem;

  public float itemDepositCooldown;

  public arc.scene.Group uiGroup;

  public boolean isBuilding;

  public boolean buildWasAutoPaused;

  public boolean wasShooting;

  public mindustry.type.UnitType controlledType;

  public float recentRespawnTimer;

  public mindustry.game.Schematic lastSchematic;

  public arc.input.GestureDetector detector;

  public mindustry.input.InputHandler$PlaceLine line;

  public mindustry.entities.units.BuildPlan resultplan;

  public mindustry.entities.units.BuildPlan bplan;

  public arc.struct.Seq<mindustry.entities.units.BuildPlan> linePlans;

  public arc.struct.Seq<mindustry.entities.units.BuildPlan> selectPlans;

  public arc.struct.Queue<mindustry.entities.units.BuildPlan> lastPlans;

  public mindustry.gen.Unit lastUnit;

  public mindustry.gen.Unit spectating;

  public arc.struct.Seq<mindustry.gen.Unit> selectedUnits;

  public arc.struct.Seq<mindustry.gen.Building> commandBuildings;

  public boolean commandMode;

  public boolean commandRect;

  public boolean tappedOne;

  public float commandRectX;

  public float commandRectY;

  public arc.struct.IntSeq[] controlGroups;

  private arc.struct.Seq<mindustry.entities.units.BuildPlan> plansOut;

  private arc.math.geom.QuadTree<mindustry.entities.units.BuildPlan> playerPlanTree;

  private arc.math.geom.QuadTree<mindustry.entities.units.BuildPlan> selectPlanTree;

  public final mindustry.ui.fragments.BlockInventoryFragment inv;

  public final mindustry.ui.fragments.BlockConfigFragment config;

  public final mindustry.ui.fragments.PlanConfigFragment planConfig;

  private arc.scene.ui.layout.WidgetGroup group;

  private mindustry.entities.units.BuildPlan overlappingPlan;

  private mindustry.gen.Player overlappingPlayer;

  protected arc.util.Eachable<mindustry.entities.units.BuildPlan> allPlans;

  protected arc.util.Eachable<mindustry.entities.units.BuildPlan> allSelectLines;

  protected arc.util.Eachable<mindustry.entities.units.BuildPlan> allRenderPlansConfig;

  private static mindustry.entities.units.BuildPlan sameQuadPlan;

  private static final arc.func.Boolf<mindustry.entities.units.BuildPlan> sameQuadPlanFinder;

  private static mindustry.entities.units.BuildPlan vpIgnore;

  private static mindustry.world.Block vpBlock;

  private static int vpX;

  private static int vpY;

  private static final arc.func.Boolf<mindustry.entities.units.BuildPlan> vpPredicate;

  public mindustry.input.InputHandler();
    Code:
       0: aload_0
       1: invokespecial #3                  // Method java/lang/Object."<init>":()V
       4: aload_0
       5: new           #9                  // class arc/math/geom/Vec2
       8: dup
       9: invokespecial #11                 // Method arc/math/geom/Vec2."<init>":()V
      12: putfield      #12                 // Field logicCamPan:Larc/math/geom/Vec2;
      15: aload_0
      16: ldc           #18                 // float 0.1f
      18: putfield      #19                 // Field logicCamSpeed:F
      21: aload_0
      22: ldc           #23                 // float -1.0f
      24: putfield      #24                 // Field logicCutsceneZoom:F
      27: aload_0
      28: iconst_2
      29: anewarray     #27                 // class arc/func/Boolp
      32: dup
      33: iconst_0
      34: invokedynamic #29,  0             // InvokeDynamic #0:get:()Larc/func/Boolp;
      39: aastore
      40: dup
      41: iconst_1
      42: aload_0
      43: invokedynamic #33,  0             // InvokeDynamic #1:get:(Lmindustry/input/InputHandler;)Larc/func/Boolp;
      48: aastore
      49: invokestatic  #36                 // Method arc/struct/Seq.with:([Ljava/lang/Object;)Larc/struct/Seq;
      52: putfield      #42                 // Field inputLocks:Larc/struct/Seq;
      55: aload_0
      56: new           #46                 // class arc/util/Interval
      59: dup
      60: invokespecial #48                 // Method arc/util/Interval."<init>":()V
      63: putfield      #49                 // Field controlInterval:Larc/util/Interval;
      66: aload_0
      67: iconst_1
      68: putfield      #53                 // Field rotation:I
      71: aload_0
      72: iconst_1
      73: putfield      #57                 // Field isBuilding:Z
      76: aload_0
      77: iconst_0
      78: putfield      #61                 // Field buildWasAutoPaused:Z
      81: aload_0
      82: iconst_0
      83: putfield      #64                 // Field wasShooting:Z
      86: aload_0
      87: new           #67                 // class mindustry/input/InputHandler$PlaceLine
      90: dup
      91: invokespecial #69                 // Method mindustry/input/InputHandler$PlaceLine."<init>":()V
      94: putfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
      97: aload_0
      98: new           #74                 // class mindustry/entities/units/BuildPlan
     101: dup
     102: invokespecial #76                 // Method mindustry/entities/units/BuildPlan."<init>":()V
     105: putfield      #77                 // Field bplan:Lmindustry/entities/units/BuildPlan;
     108: aload_0
     109: new           #37                 // class arc/struct/Seq
     112: dup
     113: invokespecial #81                 // Method arc/struct/Seq."<init>":()V
     116: putfield      #82                 // Field linePlans:Larc/struct/Seq;
     119: aload_0
     120: new           #37                 // class arc/struct/Seq
     123: dup
     124: ldc           #74                 // class mindustry/entities/units/BuildPlan
     126: invokespecial #85                 // Method arc/struct/Seq."<init>":(Ljava/lang/Class;)V
     129: putfield      #88                 // Field selectPlans:Larc/struct/Seq;
     132: aload_0
     133: new           #91                 // class arc/struct/Queue
     136: dup
     137: invokespecial #93                 // Method arc/struct/Queue."<init>":()V
     140: putfield      #94                 // Field lastPlans:Larc/struct/Queue;
     143: aload_0
     144: new           #37                 // class arc/struct/Seq
     147: dup
     148: invokespecial #81                 // Method arc/struct/Seq."<init>":()V
     151: putfield      #98                 // Field selectedUnits:Larc/struct/Seq;
     154: aload_0
     155: new           #37                 // class arc/struct/Seq
     158: dup
     159: iconst_0
     160: invokespecial #101                // Method arc/struct/Seq."<init>":(Z)V
     163: putfield      #104                // Field commandBuildings:Larc/struct/Seq;
     166: aload_0
     167: iconst_0
     168: putfield      #107                // Field commandMode:Z
     171: aload_0
     172: iconst_0
     173: putfield      #110                // Field commandRect:Z
     176: aload_0
     177: iconst_0
     178: putfield      #113                // Field tappedOne:Z
     181: aload_0
     182: getstatic     #116                // Field controlGroupBindings:[Larc/input/KeyBind;
     185: arraylength
     186: anewarray     #120                // class arc/struct/IntSeq
     189: putfield      #122                // Field controlGroups:[Larc/struct/IntSeq;
     192: aload_0
     193: new           #37                 // class arc/struct/Seq
     196: dup
     197: ldc           #74                 // class mindustry/entities/units/BuildPlan
     199: invokespecial #85                 // Method arc/struct/Seq."<init>":(Ljava/lang/Class;)V
     202: putfield      #126                // Field plansOut:Larc/struct/Seq;
     205: aload_0
     206: new           #129                // class arc/math/geom/QuadTree
     209: dup
     210: new           #131                // class arc/math/geom/Rect
     213: dup
     214: invokespecial #133                // Method arc/math/geom/Rect."<init>":()V
     217: invokespecial #134                // Method arc/math/geom/QuadTree."<init>":(Larc/math/geom/Rect;)V
     220: putfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
     223: aload_0
     224: new           #129                // class arc/math/geom/QuadTree
     227: dup
     228: new           #131                // class arc/math/geom/Rect
     231: dup
     232: invokespecial #133                // Method arc/math/geom/Rect."<init>":()V
     235: invokespecial #134                // Method arc/math/geom/QuadTree."<init>":(Larc/math/geom/Rect;)V
     238: putfield      #141                // Field selectPlanTree:Larc/math/geom/QuadTree;
     241: aload_0
     242: new           #144                // class arc/scene/ui/layout/WidgetGroup
     245: dup
     246: invokespecial #146                // Method arc/scene/ui/layout/WidgetGroup."<init>":()V
     249: putfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     252: aload_0
     253: aconst_null
     254: putfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     257: aload_0
     258: aconst_null
     259: putfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
     262: aload_0
     263: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     266: getstatic     #158                // Field arc/scene/event/Touchable.childrenOnly:Larc/scene/event/Touchable;
     269: putfield      #164                // Field arc/scene/ui/layout/WidgetGroup.touchable:Larc/scene/event/Touchable;
     272: aload_0
     273: new           #167                // class mindustry/ui/fragments/BlockInventoryFragment
     276: dup
     277: invokespecial #169                // Method mindustry/ui/fragments/BlockInventoryFragment."<init>":()V
     280: putfield      #170                // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
     283: aload_0
     284: new           #174                // class mindustry/ui/fragments/BlockConfigFragment
     287: dup
     288: invokespecial #176                // Method mindustry/ui/fragments/BlockConfigFragment."<init>":()V
     291: putfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     294: aload_0
     295: new           #181                // class mindustry/ui/fragments/PlanConfigFragment
     298: dup
     299: invokespecial #183                // Method mindustry/ui/fragments/PlanConfigFragment."<init>":()V
     302: putfield      #184                // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
     305: aload_0
     306: invokevirtual #188                // Method createPlanLists:()V
     309: ldc           #191                // class mindustry/game/EventType$UnitDestroyEvent
     311: invokedynamic #193,  0            // InvokeDynamic #2:get:()Larc/func/Cons;
     316: invokestatic  #196                // Method arc/Events.on:(Ljava/lang/Class;Larc/func/Cons;)V
     319: ldc           #202                // class mindustry/game/EventType$WorldLoadEvent
     321: aload_0
     322: invokedynamic #204,  0            // InvokeDynamic #3:get:(Lmindustry/input/InputHandler;)Larc/func/Cons;
     327: invokestatic  #196                // Method arc/Events.on:(Ljava/lang/Class;Larc/func/Cons;)V
     330: ldc           #207                // class mindustry/game/EventType$ResetEvent
     332: aload_0
     333: invokedynamic #209,  0            // InvokeDynamic #4:get:(Lmindustry/input/InputHandler;)Larc/func/Cons;
     338: invokestatic  #196                // Method arc/Events.on:(Ljava/lang/Class;Larc/func/Cons;)V
     341: return

  protected void initQuadtrees();
    Code:
       0: aload_0
       1: new           #129                // class arc/math/geom/QuadTree
       4: dup
       5: new           #131                // class arc/math/geom/Rect
       8: dup
       9: fconst_0
      10: fconst_0
      11: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      14: invokevirtual #214                // Method mindustry/core/World.unitWidth:()I
      17: i2f
      18: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      21: invokevirtual #220                // Method mindustry/core/World.unitHeight:()I
      24: i2f
      25: invokespecial #223                // Method arc/math/geom/Rect."<init>":(FFFF)V
      28: invokespecial #134                // Method arc/math/geom/QuadTree."<init>":(Larc/math/geom/Rect;)V
      31: putfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      34: aload_0
      35: new           #129                // class arc/math/geom/QuadTree
      38: dup
      39: new           #131                // class arc/math/geom/Rect
      42: dup
      43: fconst_0
      44: fconst_0
      45: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      48: invokevirtual #214                // Method mindustry/core/World.unitWidth:()I
      51: i2f
      52: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      55: invokevirtual #220                // Method mindustry/core/World.unitHeight:()I
      58: i2f
      59: invokespecial #223                // Method arc/math/geom/Rect."<init>":(FFFF)V
      62: invokespecial #134                // Method arc/math/geom/QuadTree."<init>":(Larc/math/geom/Rect;)V
      65: putfield      #141                // Field selectPlanTree:Larc/math/geom/QuadTree;
      68: aload_0
      69: invokevirtual #188                // Method createPlanLists:()V
      72: return

  public static void transferItemEffect(mindustry.type.Item, float, float, mindustry.gen.Itemsc);
    Code:
       0: aload_3
       1: ifnonnull     5
       4: return
       5: aload_0
       6: iconst_1
       7: fload_1
       8: fload_2
       9: aload_3
      10: aconst_null
      11: invokestatic  #226                // Method createItemTransfer:(Lmindustry/type/Item;IFFLarc/math/geom/Position;Ljava/lang/Runnable;)V
      14: return

  public static void takeItems(mindustry.gen.Building, mindustry.type.Item, int, mindustry.gen.Unit);
    Code:
       0: aload_3
       1: ifnull        8
       4: aload_0
       5: ifnonnull     9
       8: return
       9: aload_0
      10: aload_1
      11: aload_3
      12: aload_1
      13: invokevirtual #230                // Method mindustry/gen/Unit.maxAccepted:(Lmindustry/type/Item;)I
      16: iload_2
      17: invokestatic  #236                // Method java/lang/Math.min:(II)I
      20: invokevirtual #242                // Method mindustry/gen/Building.removeStack:(Lmindustry/type/Item;I)I
      23: istore        4
      25: iload         4
      27: ifne          31
      30: return
      31: aload_3
      32: aload_1
      33: iload         4
      35: invokevirtual #248                // Method mindustry/gen/Unit.addItem:(Lmindustry/type/Item;I)V
      38: iconst_0
      39: istore        5
      41: iload         5
      43: iload         4
      45: iconst_3
      46: idiv
      47: iconst_1
      48: bipush        8
      50: invokestatic  #252                // Method arc/math/Mathf.clamp:(III)I
      53: if_icmpge     80
      56: iload         5
      58: i2f
      59: ldc_w         #258                // float 3.0f
      62: fmul
      63: aload_1
      64: aload_0
      65: aload_3
      66: invokedynamic #259,  0            // InvokeDynamic #5:run:(Lmindustry/type/Item;Lmindustry/gen/Building;Lmindustry/gen/Unit;)Ljava/lang/Runnable;
      71: invokestatic  #263                // Method arc/util/Time.run:(FLjava/lang/Runnable;)V
      74: iinc          5, 1
      77: goto          41
      80: return

  public static void transferItemToUnit(mindustry.type.Item, float, float, mindustry.gen.Itemsc);
    Code:
       0: aload_3
       1: ifnonnull     5
       4: return
       5: aload_0
       6: iconst_1
       7: fload_1
       8: fload_2
       9: aload_3
      10: aload_3
      11: aload_0
      12: invokedynamic #268,  0            // InvokeDynamic #6:run:(Lmindustry/gen/Itemsc;Lmindustry/type/Item;)Ljava/lang/Runnable;
      17: invokestatic  #226                // Method createItemTransfer:(Lmindustry/type/Item;IFFLarc/math/geom/Position;Ljava/lang/Runnable;)V
      20: return

  public static void setItem(mindustry.gen.Building, mindustry.type.Item, int);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
       8: ifnonnull     12
      11: return
      12: aload_0
      13: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      16: aload_1
      17: iload_2
      18: invokevirtual #275                // Method mindustry/world/modules/ItemModule.set:(Lmindustry/type/Item;I)V
      21: return

  public static void setItems(mindustry.gen.Building, mindustry.type.ItemStack[]);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
       8: ifnonnull     12
      11: return
      12: aload_1
      13: astore_2
      14: aload_2
      15: arraylength
      16: istore_3
      17: iconst_0
      18: istore        4
      20: iload         4
      22: iload_3
      23: if_icmpge     55
      26: aload_2
      27: iload         4
      29: aaload
      30: astore        5
      32: aload_0
      33: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      36: aload         5
      38: getfield      #280                // Field mindustry/type/ItemStack.item:Lmindustry/type/Item;
      41: aload         5
      43: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      46: invokevirtual #275                // Method mindustry/world/modules/ItemModule.set:(Lmindustry/type/Item;I)V
      49: iinc          4, 1
      52: goto          20
      55: return

  public static void setTileItems(mindustry.type.Item, int, int[]);
    Code:
       0: aload_2
       1: astore_3
       2: aload_3
       3: arraylength
       4: istore        4
       6: iconst_0
       7: istore        5
       9: iload         5
      11: iload         4
      13: if_icmpge     61
      16: aload_3
      17: iload         5
      19: iaload
      20: istore        6
      22: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      25: iload         6
      27: invokevirtual #289                // Method mindustry/core/World.build:(I)Lmindustry/gen/Building;
      30: astore        7
      32: aload         7
      34: ifnull        55
      37: aload         7
      39: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      42: ifnull        55
      45: aload         7
      47: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      50: aload_0
      51: iload_1
      52: invokevirtual #275                // Method mindustry/world/modules/ItemModule.set:(Lmindustry/type/Item;I)V
      55: iinc          5, 1
      58: goto          9
      61: return

  public static void clearItems(mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
       8: ifnonnull     12
      11: return
      12: aload_0
      13: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      16: invokevirtual #293                // Method mindustry/world/modules/ItemModule.clear:()V
      19: return

  public static void setLiquid(mindustry.gen.Building, mindustry.type.Liquid, float);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
       8: ifnonnull     12
      11: return
      12: aload_0
      13: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
      16: aload_1
      17: fload_2
      18: invokevirtual #300                // Method mindustry/world/modules/LiquidModule.set:(Lmindustry/type/Liquid;F)V
      21: return

  public static void setLiquids(mindustry.gen.Building, mindustry.type.LiquidStack[]);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
       8: ifnonnull     12
      11: return
      12: aload_1
      13: astore_2
      14: aload_2
      15: arraylength
      16: istore_3
      17: iconst_0
      18: istore        4
      20: iload         4
      22: iload_3
      23: if_icmpge     55
      26: aload_2
      27: iload         4
      29: aaload
      30: astore        5
      32: aload_0
      33: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
      36: aload         5
      38: getfield      #305                // Field mindustry/type/LiquidStack.liquid:Lmindustry/type/Liquid;
      41: aload         5
      43: getfield      #311                // Field mindustry/type/LiquidStack.amount:F
      46: invokevirtual #300                // Method mindustry/world/modules/LiquidModule.set:(Lmindustry/type/Liquid;F)V
      49: iinc          4, 1
      52: goto          20
      55: return

  public static void setTileLiquids(mindustry.type.Liquid, float, int[]);
    Code:
       0: aload_2
       1: astore_3
       2: aload_3
       3: arraylength
       4: istore        4
       6: iconst_0
       7: istore        5
       9: iload         5
      11: iload         4
      13: if_icmpge     61
      16: aload_3
      17: iload         5
      19: iaload
      20: istore        6
      22: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      25: iload         6
      27: invokevirtual #289                // Method mindustry/core/World.build:(I)Lmindustry/gen/Building;
      30: astore        7
      32: aload         7
      34: ifnull        55
      37: aload         7
      39: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
      42: ifnull        55
      45: aload         7
      47: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
      50: aload_0
      51: fload_1
      52: invokevirtual #300                // Method mindustry/world/modules/LiquidModule.set:(Lmindustry/type/Liquid;F)V
      55: iinc          5, 1
      58: goto          9
      61: return

  public static void clearLiquids(mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
       8: ifnonnull     12
      11: return
      12: aload_0
      13: getfield      #296                // Field mindustry/gen/Building.liquids:Lmindustry/world/modules/LiquidModule;
      16: invokevirtual #313                // Method mindustry/world/modules/LiquidModule.clear:()V
      19: return

  public static void transferItemTo(mindustry.gen.Unit, mindustry.type.Item, int, float, float, mindustry.gen.Building);
    Code:
       0: aload         5
       2: ifnull        17
       5: aload         5
       7: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      10: ifnull        17
      13: aload_1
      14: ifnonnull     18
      17: return
      18: aload_0
      19: ifnull        50
      22: aload_0
      23: invokevirtual #314                // Method mindustry/gen/Unit.item:()Lmindustry/type/Item;
      26: aload_1
      27: if_acmpne     50
      30: aload_0
      31: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      34: aload_0
      35: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      38: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      41: iload_2
      42: isub
      43: iconst_0
      44: invokestatic  #321                // Method java/lang/Math.max:(II)I
      47: putfield      #286                // Field mindustry/type/ItemStack.amount:I
      50: iconst_0
      51: istore        6
      53: iload         6
      55: iload_2
      56: iconst_3
      57: idiv
      58: iconst_1
      59: bipush        8
      61: invokestatic  #252                // Method arc/math/Mathf.clamp:(III)I
      64: if_icmpge     93
      67: iload         6
      69: iconst_3
      70: imul
      71: i2f
      72: aload_1
      73: iload_2
      74: fload_3
      75: fload         4
      77: aload         5
      79: invokedynamic #324,  0            // InvokeDynamic #7:run:(Lmindustry/type/Item;IFFLmindustry/gen/Building;)Ljava/lang/Runnable;
      84: invokestatic  #263                // Method arc/util/Time.run:(FLjava/lang/Runnable;)V
      87: iinc          6, 1
      90: goto          53
      93: iload_2
      94: ifle          105
      97: aload         5
      99: aload_1
     100: iload_2
     101: aload_0
     102: invokevirtual #327                // Method mindustry/gen/Building.handleStack:(Lmindustry/type/Item;ILmindustry/gen/Teamc;)V
     105: return

  public static void deletePlans(mindustry.gen.Player, int[]);
    Code:
       0: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       3: invokevirtual #335                // Method mindustry/net/Net.server:()Z
       6: ifeq          43
       9: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      12: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      15: aload_0
      16: getstatic     #351                // Field mindustry/net/Administration$ActionType.removePlanned:Lmindustry/net/Administration$ActionType;
      19: aload_1
      20: invokedynamic #357,  0            // InvokeDynamic #8:get:([I)Larc/func/Cons;
      25: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      28: ifne          43
      31: new           #366                // class mindustry/net/ValidateException
      34: dup
      35: aload_0
      36: ldc_w         #368                // String Player cannot remove plans.
      39: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      42: athrow
      43: aload_0
      44: ifnonnull     48
      47: return
      48: aload_0
      49: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      52: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
      55: getfield      #385                // Field mindustry/game/Teams$TeamData.plans:Larc/struct/Queue;
      58: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
      61: astore_2
      62: aload_2
      63: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      68: ifeq          153
      71: aload_2
      72: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      77: checkcast     #403                // class mindustry/game/Teams$BlockPlan
      80: astore_3
      81: aload_1
      82: astore        4
      84: aload         4
      86: arraylength
      87: istore        5
      89: iconst_0
      90: istore        6
      92: iload         6
      94: iload         5
      96: if_icmpge     150
      99: aload         4
     101: iload         6
     103: iaload
     104: istore        7
     106: aload_3
     107: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     110: iload         7
     112: invokestatic  #409                // Method arc/math/geom/Point2.x:(I)S
     115: if_icmpne     144
     118: aload_3
     119: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     122: iload         7
     124: invokestatic  #417                // Method arc/math/geom/Point2.y:(I)S
     127: if_icmpne     144
     130: aload_3
     131: iconst_1
     132: putfield      #419                // Field mindustry/game/Teams$BlockPlan.removed:Z
     135: aload_2
     136: invokeinterface #422,  1          // InterfaceMethod java/util/Iterator.remove:()V
     141: goto          62
     144: iinc          6, 1
     147: goto          92
     150: goto          62
     153: return

  public static void pingLocation(mindustry.gen.Player, float, float, java.lang.String);
    Code:
       0: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       3: invokevirtual #335                // Method mindustry/net/Net.server:()Z
       6: ifeq          45
       9: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      12: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      15: aload_0
      16: getstatic     #425                // Field mindustry/net/Administration$ActionType.pingLocation:Lmindustry/net/Administration$ActionType;
      19: fload_1
      20: fload_2
      21: aload_3
      22: invokedynamic #428,  0            // InvokeDynamic #9:get:(FFLjava/lang/String;)Larc/func/Cons;
      27: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      30: ifne          45
      33: new           #366                // class mindustry/net/ValidateException
      36: dup
      37: aload_0
      38: ldc_w         #431                // String Player was not allowed to ping a location.
      41: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      44: athrow
      45: aload_0
      46: ifnull        127
      49: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      52: ifnull        127
      55: aload_0
      56: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      59: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      62: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      65: if_acmpne     127
      68: aload_0
      69: fload_1
      70: putfield      #436                // Field mindustry/gen/Player.pingX:F
      73: aload_0
      74: fload_2
      75: putfield      #439                // Field mindustry/gen/Player.pingY:F
      78: aload_0
      79: fconst_1
      80: putfield      #442                // Field mindustry/gen/Player.pingTime:F
      83: aload_0
      84: aload_3
      85: ifnull        95
      88: aload_3
      89: invokevirtual #445                // Method java/lang/String.isEmpty:()Z
      92: ifeq          99
      95: aconst_null
      96: goto          124
      99: aload_3
     100: invokevirtual #450                // Method java/lang/String.length:()I
     103: bipush        40
     105: if_icmple     123
     108: aload_3
     109: iconst_0
     110: bipush        40
     112: invokevirtual #453                // Method java/lang/String.substring:(II)Ljava/lang/String;
     115: invokedynamic #457,  0            // InvokeDynamic #10:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
     120: goto          124
     123: aload_3
     124: putfield      #461                // Field mindustry/gen/Player.pingText:Ljava/lang/String;
     127: return

  public static void createItemTransfer(mindustry.type.Item, int, float, float, arc.math.geom.Position, java.lang.Runnable);
    Code:
       0: getstatic     #465                // Field mindustry/content/Fx.itemTransfer:Lmindustry/entities/Effect;
       3: fload_2
       4: fload_3
       5: iload_1
       6: i2f
       7: aload_0
       8: getfield      #471                // Field mindustry/type/Item.color:Larc/graphics/Color;
      11: aload         4
      13: invokevirtual #477                // Method mindustry/entities/Effect.at:(FFFLarc/graphics/Color;Ljava/lang/Object;)V
      16: aload         5
      18: ifnull        32
      21: getstatic     #465                // Field mindustry/content/Fx.itemTransfer:Lmindustry/entities/Effect;
      24: getfield      #483                // Field mindustry/entities/Effect.lifetime:F
      27: aload         5
      29: invokestatic  #263                // Method arc/util/Time.run:(FLjava/lang/Runnable;)V
      32: return

  public static void commandUnits(mindustry.gen.Player, int[], mindustry.gen.Building, mindustry.gen.Unit, arc.math.geom.Vec2, boolean, boolean);
    Code:
       0: aload_0
       1: ifnull        8
       4: aload_1
       5: ifnonnull     9
       8: return
       9: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      12: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      15: ifeq          52
      18: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      21: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      24: aload_0
      25: getstatic     #486                // Field mindustry/net/Administration$ActionType.commandUnits:Lmindustry/net/Administration$ActionType;
      28: aload_1
      29: invokedynamic #489,  0            // InvokeDynamic #11:get:([I)Larc/func/Cons;
      34: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      37: ifne          52
      40: new           #366                // class mindustry/net/ValidateException
      43: dup
      44: aload_0
      45: ldc_w         #490                // String Player cannot command units.
      48: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      51: athrow
      52: aload_2
      53: ifnonnull     60
      56: aload_3
      57: goto          61
      60: aload_2
      61: astore        7
      63: new           #9                  // class arc/math/geom/Vec2
      66: dup
      67: invokespecial #11                 // Method arc/math/geom/Vec2."<init>":()V
      70: aload         7
      72: ifnull        80
      75: aload         7
      77: goto          82
      80: aload         4
      82: invokevirtual #492                // Method arc/math/geom/Vec2.set:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
      85: astore        8
      87: getstatic     #495                // Field queuedCommands:Larc/struct/ObjectMap;
      90: aload         8
      92: invokedynamic #499,  0            // InvokeDynamic #12:get:()Larc/func/Prov;
      97: invokevirtual #502                // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;Larc/func/Prov;)Ljava/lang/Object;
     100: checkcast     #37                 // class arc/struct/Seq
     103: astore        9
     105: iconst_0
     106: istore        10
     108: aload_3
     109: ifnonnull     116
     112: aload_2
     113: ifnull        125
     116: getstatic     #507                // Field mindustry/game/EventType$Trigger.unitCommandAttack:Lmindustry/game/EventType$Trigger;
     119: invokestatic  #513                // Method arc/Events.fire:(Ljava/lang/Enum;)V
     122: goto          131
     125: getstatic     #517                // Field mindustry/game/EventType$Trigger.unitCommandPosition:Lmindustry/game/EventType$Trigger;
     128: invokestatic  #513                // Method arc/Events.fire:(Ljava/lang/Enum;)V
     131: aload_1
     132: astore        11
     134: aload         11
     136: arraylength
     137: istore        12
     139: iconst_0
     140: istore        13
     142: iload         13
     144: iload         12
     146: if_icmpge     411
     149: aload         11
     151: iload         13
     153: iaload
     154: istore        14
     156: getstatic     #520                // Field mindustry/gen/Groups.unit:Lmindustry/entities/EntityGroup;
     159: iload         14
     161: invokevirtual #526                // Method mindustry/entities/EntityGroup.getByID:(I)Lmindustry/gen/Entityc;
     164: checkcast     #231                // class mindustry/gen/Unit
     167: astore        15
     169: aload         15
     171: ifnull        405
     174: aload         15
     176: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
     179: aload_0
     180: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     183: if_acmpne     405
     186: aload         15
     188: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
     191: astore        17
     193: aload         17
     195: instanceof    #539                // class mindustry/ai/types/CommandAI
     198: ifeq          405
     201: aload         17
     203: checkcast     #539                // class mindustry/ai/types/CommandAI
     206: astore        16
     208: aload         16
     210: getfield      #541                // Field mindustry/ai/types/CommandAI.command:Lmindustry/ai/UnitCommand;
     213: ifnull        227
     216: aload         16
     218: getfield      #541                // Field mindustry/ai/types/CommandAI.command:Lmindustry/ai/UnitCommand;
     221: getfield      #545                // Field mindustry/ai/UnitCommand.switchToMove:Z
     224: ifeq          235
     227: aload         16
     229: getstatic     #550                // Field mindustry/ai/UnitCommand.moveCommand:Lmindustry/ai/UnitCommand;
     232: invokevirtual #553                // Method mindustry/ai/types/CommandAI.command:(Lmindustry/ai/UnitCommand;)V
     235: aload         7
     237: ifnull        335
     240: aload         7
     242: invokeinterface #556,  1          // InterfaceMethod mindustry/gen/Teamc.team:()Lmindustry/game/Team;
     247: aload_0
     248: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     251: if_acmpeq     335
     254: aload         7
     256: instanceof    #231                // class mindustry/gen/Unit
     259: ifeq          279
     262: aload         7
     264: checkcast     #231                // class mindustry/gen/Unit
     267: astore        17
     269: aload         15
     271: aload         17
     273: invokevirtual #559                // Method mindustry/gen/Unit.canTarget:(Lmindustry/gen/Teamc;)Z
     276: ifeq          335
     279: aload         7
     281: instanceof    #243                // class mindustry/gen/Building
     284: ifeq          298
     287: aload         15
     289: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     292: getfield      #567                // Field mindustry/type/UnitType.targetGround:Z
     295: ifeq          335
     298: iconst_1
     299: istore        10
     301: iload         5
     303: ifeq          316
     306: aload         16
     308: aload         7
     310: invokevirtual #572                // Method mindustry/ai/types/CommandAI.commandQueue:(Larc/math/geom/Position;)V
     313: goto          371
     316: aload         16
     318: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     321: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     324: pop
     325: aload         16
     327: aload         7
     329: invokevirtual #581                // Method mindustry/ai/types/CommandAI.commandTarget:(Lmindustry/gen/Teamc;)V
     332: goto          371
     335: aload         4
     337: ifnull        371
     340: iload         5
     342: ifeq          355
     345: aload         16
     347: aload         4
     349: invokevirtual #572                // Method mindustry/ai/types/CommandAI.commandQueue:(Larc/math/geom/Position;)V
     352: goto          371
     355: aload         16
     357: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     360: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     363: pop
     364: aload         16
     366: aload         4
     368: invokevirtual #585                // Method mindustry/ai/types/CommandAI.commandPosition:(Larc/math/geom/Vec2;)V
     371: aload         15
     373: aload_0
     374: invokevirtual #589                // Method mindustry/gen/Player.coloredName:()Ljava/lang/String;
     377: putfield      #593                // Field mindustry/gen/Unit.lastCommanded:Ljava/lang/String;
     380: aload         16
     382: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     385: getfield      #596                // Field arc/struct/Seq.size:I
     388: ifgt          397
     391: aload         16
     393: aconst_null
     394: putfield      #599                // Field mindustry/ai/types/CommandAI.group:Lmindustry/ai/UnitGroup;
     397: aload         9
     399: aload         15
     401: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
     404: pop
     405: iinc          13, 1
     408: goto          142
     411: iload         6
     413: ifeq          615
     416: iconst_4
     417: anewarray     #608                // class mindustry/ai/UnitGroup
     420: astore        11
     422: getstatic     #495                // Field queuedCommands:Larc/struct/ObjectMap;
     425: aload         8
     427: invokevirtual #610                // Method arc/struct/ObjectMap.remove:(Ljava/lang/Object;)Ljava/lang/Object;
     430: checkcast     #37                 // class arc/struct/Seq
     433: astore        12
     435: aload         12
     437: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     440: astore        13
     442: aload         13
     444: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     449: ifeq          566
     452: aload         13
     454: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     459: checkcast     #231                // class mindustry/gen/Unit
     462: astore        14
     464: aload         14
     466: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
     469: astore        16
     471: aload         16
     473: instanceof    #539                // class mindustry/ai/types/CommandAI
     476: ifeq          563
     479: aload         16
     481: checkcast     #539                // class mindustry/ai/types/CommandAI
     484: astore        15
     486: aload         15
     488: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     491: getfield      #596                // Field arc/struct/Seq.size:I
     494: ifne          563
     497: aload_1
     498: arraylength
     499: iconst_1
     500: if_icmple     563
     503: aload         14
     505: invokevirtual #614                // Method mindustry/gen/Unit.collisionLayer:()I
     508: istore        16
     510: iload         16
     512: iconst_m1
     513: if_icmpne     519
     516: iconst_0
     517: istore        16
     519: aload         11
     521: iload         16
     523: aaload
     524: ifnonnull     539
     527: aload         11
     529: iload         16
     531: new           #608                // class mindustry/ai/UnitGroup
     534: dup
     535: invokespecial #617                // Method mindustry/ai/UnitGroup."<init>":()V
     538: aastore
     539: aload         11
     541: iload         16
     543: aaload
     544: getfield      #618                // Field mindustry/ai/UnitGroup.units:Larc/struct/Seq;
     547: aload         14
     549: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
     552: pop
     553: aload         15
     555: aload         11
     557: iload         16
     559: aaload
     560: putfield      #599                // Field mindustry/ai/types/CommandAI.group:Lmindustry/ai/UnitGroup;
     563: goto          442
     566: iconst_0
     567: istore        13
     569: iload         13
     571: aload         11
     573: arraylength
     574: if_icmpge     615
     577: aload         11
     579: iload         13
     581: aaload
     582: astore        14
     584: aload         14
     586: ifnull        609
     589: aload         14
     591: getfield      #618                // Field mindustry/ai/UnitGroup.units:Larc/struct/Seq;
     594: getfield      #596                // Field arc/struct/Seq.size:I
     597: ifle          609
     600: aload         14
     602: aload         8
     604: iload         13
     606: invokevirtual #621                // Method mindustry/ai/UnitGroup.calculateFormation:(Larc/math/geom/Vec2;I)V
     609: iinc          13, 1
     612: goto          569
     615: aload_1
     616: arraylength
     617: ifle          660
     620: aload_0
     621: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     624: if_acmpne     660
     627: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     630: invokevirtual #629                // Method mindustry/core/GameState.isPaused:()Z
     633: ifne          660
     636: iload         10
     638: ifeq          652
     641: getstatic     #634                // Field mindustry/content/Fx.attackCommand:Lmindustry/entities/Effect;
     644: aload         7
     646: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     649: goto          660
     652: getstatic     #639                // Field mindustry/content/Fx.moveCommand:Lmindustry/entities/Effect;
     655: aload         4
     657: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     660: return

  public static void setUnitCommand(mindustry.gen.Player, int[], mindustry.ai.UnitCommand);
    Code:
       0: aload_0
       1: ifnull        12
       4: aload_1
       5: ifnull        12
       8: aload_2
       9: ifnonnull     13
      12: return
      13: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      16: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      19: ifeq          57
      22: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      25: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      28: aload_0
      29: getstatic     #486                // Field mindustry/net/Administration$ActionType.commandUnits:Lmindustry/net/Administration$ActionType;
      32: aload_1
      33: aload_2
      34: invokedynamic #641,  0            // InvokeDynamic #13:get:([ILmindustry/ai/UnitCommand;)Larc/func/Cons;
      39: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      42: ifne          57
      45: new           #366                // class mindustry/net/ValidateException
      48: dup
      49: aload_0
      50: ldc_w         #490                // String Player cannot command units.
      53: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      56: athrow
      57: aload_1
      58: astore_3
      59: aload_3
      60: arraylength
      61: istore        4
      63: iconst_0
      64: istore        5
      66: iload         5
      68: iload         4
      70: if_icmpge     292
      73: aload_3
      74: iload         5
      76: iaload
      77: istore        6
      79: getstatic     #520                // Field mindustry/gen/Groups.unit:Lmindustry/entities/EntityGroup;
      82: iload         6
      84: invokevirtual #526                // Method mindustry/entities/EntityGroup.getByID:(I)Lmindustry/gen/Entityc;
      87: checkcast     #231                // class mindustry/gen/Unit
      90: astore        7
      92: aload         7
      94: ifnull        286
      97: aload         7
      99: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
     102: aload_0
     103: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     106: if_acmpne     286
     109: aload         7
     111: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
     114: astore        9
     116: aload         9
     118: instanceof    #539                // class mindustry/ai/types/CommandAI
     121: ifeq          286
     124: aload         9
     126: checkcast     #539                // class mindustry/ai/types/CommandAI
     129: astore        8
     131: aload         7
     133: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     136: aload         7
     138: aload_2
     139: invokevirtual #644                // Method mindustry/type/UnitType.allowCommand:(Lmindustry/gen/Unit;Lmindustry/ai/UnitCommand;)Z
     142: ifeq          286
     145: aload_2
     146: getfield      #648                // Field mindustry/ai/UnitCommand.resetTarget:Z
     149: ifne          163
     152: aload         8
     154: invokevirtual #651                // Method mindustry/ai/types/CommandAI.currentCommand:()Lmindustry/ai/UnitCommand;
     157: getfield      #648                // Field mindustry/ai/UnitCommand.resetTarget:Z
     160: ifeq          167
     163: iconst_1
     164: goto          168
     167: iconst_0
     168: istore        9
     170: aload         8
     172: aload_2
     173: invokevirtual #553                // Method mindustry/ai/types/CommandAI.command:(Lmindustry/ai/UnitCommand;)V
     176: iload         9
     178: ifeq          193
     181: aload         8
     183: aconst_null
     184: putfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     187: aload         8
     189: aconst_null
     190: putfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
     193: aload         7
     195: aload_0
     196: invokevirtual #589                // Method mindustry/gen/Player.coloredName:()Ljava/lang/String;
     199: putfield      #593                // Field mindustry/gen/Unit.lastCommanded:Ljava/lang/String;
     202: getstatic     #662                // Field stancesOut:Larc/struct/Seq;
     205: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     208: pop
     209: aload         7
     211: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     214: aload         7
     216: getstatic     #662                // Field stancesOut:Larc/struct/Seq;
     219: invokevirtual #665                // Method mindustry/type/UnitType.getUnitStances:(Lmindustry/gen/Unit;Larc/struct/Seq;)V
     222: getstatic     #669                // Field mindustry/Vars.content:Lmindustry/core/ContentLoader;
     225: invokevirtual #673                // Method mindustry/core/ContentLoader.unitStances:()Larc/struct/Seq;
     228: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     231: astore        10
     233: aload         10
     235: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     240: ifeq          286
     243: aload         10
     245: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     250: checkcast     #678                // class mindustry/ai/UnitStance
     253: astore        11
     255: aload         8
     257: aload         11
     259: invokevirtual #680                // Method mindustry/ai/types/CommandAI.hasStance:(Lmindustry/ai/UnitStance;)Z
     262: ifeq          283
     265: getstatic     #662                // Field stancesOut:Larc/struct/Seq;
     268: aload         11
     270: invokevirtual #684                // Method arc/struct/Seq.contains:(Ljava/lang/Object;)Z
     273: ifne          283
     276: aload         8
     278: aload         11
     280: invokevirtual #688                // Method mindustry/ai/types/CommandAI.disableStance:(Lmindustry/ai/UnitStance;)V
     283: goto          233
     286: iinc          5, 1
     289: goto          66
     292: return

  public static void setUnitStance(mindustry.gen.Player, int[], mindustry.ai.UnitStance, boolean);
    Code:
       0: aload_0
       1: ifnull        12
       4: aload_1
       5: ifnull        12
       8: aload_2
       9: ifnonnull     13
      12: return
      13: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      16: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      19: ifeq          56
      22: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      25: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      28: aload_0
      29: getstatic     #486                // Field mindustry/net/Administration$ActionType.commandUnits:Lmindustry/net/Administration$ActionType;
      32: aload_1
      33: invokedynamic #692,  0            // InvokeDynamic #14:get:([I)Larc/func/Cons;
      38: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      41: ifne          56
      44: new           #366                // class mindustry/net/ValidateException
      47: dup
      48: aload_0
      49: ldc_w         #490                // String Player cannot command units.
      52: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      55: athrow
      56: aload_1
      57: astore        4
      59: aload         4
      61: arraylength
      62: istore        5
      64: iconst_0
      65: istore        6
      67: iload         6
      69: iload         5
      71: if_icmpge     199
      74: aload         4
      76: iload         6
      78: iaload
      79: istore        7
      81: getstatic     #520                // Field mindustry/gen/Groups.unit:Lmindustry/entities/EntityGroup;
      84: iload         7
      86: invokevirtual #526                // Method mindustry/entities/EntityGroup.getByID:(I)Lmindustry/gen/Entityc;
      89: checkcast     #231                // class mindustry/gen/Unit
      92: astore        8
      94: aload         8
      96: ifnull        193
      99: aload         8
     101: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
     104: aload_0
     105: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     108: if_acmpne     193
     111: aload         8
     113: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
     116: astore        10
     118: aload         10
     120: instanceof    #539                // class mindustry/ai/types/CommandAI
     123: ifeq          193
     126: aload         10
     128: checkcast     #539                // class mindustry/ai/types/CommandAI
     131: astore        9
     133: aload_2
     134: getstatic     #693                // Field mindustry/ai/UnitStance.stop:Lmindustry/ai/UnitStance;
     137: if_acmpne     148
     140: aload         9
     142: invokevirtual #697                // Method mindustry/ai/types/CommandAI.clearCommands:()V
     145: goto          184
     148: aload         8
     150: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     153: aload         8
     155: aload_2
     156: invokevirtual #700                // Method mindustry/type/UnitType.allowStance:(Lmindustry/gen/Unit;Lmindustry/ai/UnitStance;)Z
     159: ifeq          184
     162: aload         9
     164: aload_2
     165: aload_2
     166: getfield      #704                // Field mindustry/ai/UnitStance.toggle:Z
     169: ifeq          176
     172: iload_3
     173: ifeq          180
     176: iconst_1
     177: goto          181
     180: iconst_0
     181: invokevirtual #707                // Method mindustry/ai/types/CommandAI.setStance:(Lmindustry/ai/UnitStance;Z)V
     184: aload         8
     186: aload_0
     187: invokevirtual #589                // Method mindustry/gen/Player.coloredName:()Ljava/lang/String;
     190: putfield      #593                // Field mindustry/gen/Unit.lastCommanded:Ljava/lang/String;
     193: iinc          6, 1
     196: goto          67
     199: return

  public static void commandBuilding(mindustry.gen.Player, int[], arc.math.geom.Vec2);
    Code:
       0: aload_0
       1: ifnull        8
       4: aload_2
       5: ifnonnull     9
       8: return
       9: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      12: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      15: ifeq          52
      18: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      21: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      24: aload_0
      25: getstatic     #711                // Field mindustry/net/Administration$ActionType.commandBuilding:Lmindustry/net/Administration$ActionType;
      28: aload_1
      29: invokedynamic #714,  0            // InvokeDynamic #15:get:([I)Larc/func/Cons;
      34: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      37: ifne          52
      40: new           #366                // class mindustry/net/ValidateException
      43: dup
      44: aload_0
      45: ldc_w         #715                // String Player cannot command buildings.
      48: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      51: athrow
      52: aload_1
      53: astore_3
      54: aload_3
      55: arraylength
      56: istore        4
      58: iconst_0
      59: istore        5
      61: iload         5
      63: iload         4
      65: if_icmpge     167
      68: aload_3
      69: iload         5
      71: iaload
      72: istore        6
      74: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      77: iload         6
      79: invokevirtual #289                // Method mindustry/core/World.build:(I)Lmindustry/gen/Building;
      82: astore        7
      84: aload         7
      86: ifnull        161
      89: aload         7
      91: invokevirtual #717                // Method mindustry/gen/Building.team:()Lmindustry/game/Team;
      94: aload_0
      95: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      98: if_acmpne     161
     101: aload         7
     103: invokevirtual #718                // Method mindustry/gen/Building.isCommandable:()Z
     106: ifne          112
     109: goto          161
     112: aload         7
     114: aload_2
     115: invokevirtual #721                // Method mindustry/gen/Building.onCommand:(Larc/math/geom/Vec2;)V
     118: aload         7
     120: aload_0
     121: invokevirtual #724                // Method mindustry/gen/Building.updateLastAccess:(Lmindustry/gen/Player;)V
     124: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     127: invokevirtual #629                // Method mindustry/core/GameState.isPaused:()Z
     130: ifne          147
     133: aload_0
     134: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     137: if_acmpne     147
     140: getstatic     #639                // Field mindustry/content/Fx.moveCommand:Lmindustry/entities/Effect;
     143: aload_2
     144: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     147: new           #728                // class mindustry/game/EventType$BuildingCommandEvent
     150: dup
     151: aload_0
     152: aload         7
     154: aload_2
     155: invokespecial #730                // Method mindustry/game/EventType$BuildingCommandEvent."<init>":(Lmindustry/gen/Player;Lmindustry/gen/Building;Larc/math/geom/Vec2;)V
     158: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     161: iinc          5, 1
     164: goto          61
     167: return

  public static void requestItem(mindustry.gen.Player, mindustry.gen.Building, mindustry.type.Item, int);
    Code:
       0: aload_0
       1: ifnull        41
       4: aload_1
       5: ifnull        41
       8: aload_1
       9: aload_0
      10: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      13: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
      16: ifeq          41
      19: aload_0
      20: aload_1
      21: ldc_w         #740                // float 220.0f
      24: invokevirtual #741                // Method mindustry/gen/Player.within:(Larc/math/geom/Position;F)Z
      27: ifeq          41
      30: aload_0
      31: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      34: ifne          41
      37: iload_3
      38: ifgt          42
      41: return
      42: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      45: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      48: ifeq          98
      51: aload_0
      52: aload_1
      53: invokestatic  #748                // Method mindustry/entities/Units.canInteract:(Lmindustry/gen/Player;Lmindustry/gen/Building;)Z
      56: ifeq          86
      59: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      62: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      65: aload_0
      66: getstatic     #754                // Field mindustry/net/Administration$ActionType.withdrawItem:Lmindustry/net/Administration$ActionType;
      69: aload_1
      70: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
      73: aload_2
      74: iload_3
      75: invokedynamic #761,  0            // InvokeDynamic #16:get:(Lmindustry/type/Item;I)Larc/func/Cons;
      80: invokevirtual #764                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Lmindustry/world/Tile;Larc/func/Cons;)Z
      83: ifne          98
      86: new           #366                // class mindustry/net/ValidateException
      89: dup
      90: aload_0
      91: ldc_w         #767                // String Player cannot request items.
      94: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      97: athrow
      98: aload_1
      99: aload_2
     100: aload_0
     101: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     104: aload_2
     105: invokevirtual #230                // Method mindustry/gen/Unit.maxAccepted:(Lmindustry/type/Item;)I
     108: iload_3
     109: invokestatic  #236                // Method java/lang/Math.min:(II)I
     112: aload_0
     113: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     116: invokestatic  #772                // Method mindustry/gen/Call.takeItems:(Lmindustry/gen/Building;Lmindustry/type/Item;ILmindustry/gen/Unit;)V
     119: new           #778                // class mindustry/game/EventType$WithdrawEvent
     122: dup
     123: aload_1
     124: aload_0
     125: aload_2
     126: iload_3
     127: invokespecial #780                // Method mindustry/game/EventType$WithdrawEvent."<init>":(Lmindustry/gen/Building;Lmindustry/gen/Player;Lmindustry/type/Item;I)V
     130: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     133: return

  public static void transferInventory(mindustry.gen.Player, mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        40
       4: aload_1
       5: ifnull        40
       8: aload_0
       9: aload_1
      10: ldc_w         #740                // float 220.0f
      13: invokevirtual #741                // Method mindustry/gen/Player.within:(Larc/math/geom/Position;F)Z
      16: ifeq          40
      19: aload_1
      20: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
      23: ifnull        40
      26: aload_0
      27: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      30: ifne          40
      33: aload_1
      34: invokevirtual #783                // Method mindustry/gen/Building.allowDeposit:()Z
      37: ifne          41
      40: return
      41: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      44: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      47: ifeq          143
      50: aload_0
      51: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      54: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      57: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      60: ifle          131
      63: aload_0
      64: aload_1
      65: invokestatic  #748                // Method mindustry/entities/Units.canInteract:(Lmindustry/gen/Player;Lmindustry/gen/Building;)Z
      68: ifeq          131
      71: aload_0
      72: invokevirtual #786                // Method mindustry/gen/Player.isLocal:()Z
      75: ifne          105
      78: aload_0
      79: getfield      #789                // Field mindustry/gen/Player.itemDepositRate:Larc/util/Ratekeeper;
      82: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      85: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
      88: getfield      #797                // Field mindustry/game/Rules.itemDepositCooldown:F
      91: ldc_w         #802                // float 1000.0f
      94: fmul
      95: fconst_2
      96: fmul
      97: f2l
      98: iconst_2
      99: invokevirtual #803                // Method arc/util/Ratekeeper.allow:(JI)Z
     102: ifeq          131
     105: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
     108: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
     111: aload_0
     112: getstatic     #809                // Field mindustry/net/Administration$ActionType.depositItem:Lmindustry/net/Administration$ActionType;
     115: aload_1
     116: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
     119: aload_0
     120: invokedynamic #812,  0            // InvokeDynamic #17:get:(Lmindustry/gen/Player;)Larc/func/Cons;
     125: invokevirtual #764                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Lmindustry/world/Tile;Larc/func/Cons;)Z
     128: ifne          143
     131: new           #366                // class mindustry/net/ValidateException
     134: dup
     135: aload_0
     136: ldc_w         #815                // String Player cannot transfer an item.
     139: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
     142: athrow
     143: aload_0
     144: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     147: astore_2
     148: aload_2
     149: invokevirtual #314                // Method mindustry/gen/Unit.item:()Lmindustry/type/Item;
     152: astore_3
     153: aload_1
     154: aload_3
     155: aload_2
     156: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
     159: getfield      #286                // Field mindustry/type/ItemStack.amount:I
     162: aload_2
     163: invokevirtual #817                // Method mindustry/gen/Building.acceptStack:(Lmindustry/type/Item;ILmindustry/gen/Teamc;)I
     166: istore        4
     168: aload_2
     169: aload_3
     170: iload         4
     172: aload_2
     173: getfield      #821                // Field mindustry/gen/Unit.x:F
     176: aload_2
     177: getfield      #823                // Field mindustry/gen/Unit.y:F
     180: aload_1
     181: invokestatic  #825                // Method mindustry/gen/Call.transferItemTo:(Lmindustry/gen/Unit;Lmindustry/type/Item;IFFLmindustry/gen/Building;)V
     184: new           #829                // class mindustry/game/EventType$DepositEvent
     187: dup
     188: aload_1
     189: aload_0
     190: aload_3
     191: iload         4
     193: invokespecial #831                // Method mindustry/game/EventType$DepositEvent."<init>":(Lmindustry/gen/Building;Lmindustry/gen/Player;Lmindustry/type/Item;I)V
     196: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     199: return

  public static void removeQueueBlock(int, int, boolean);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
       6: ifne          21
       9: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      12: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      15: iload_0
      16: iload_1
      17: iload_2
      18: invokevirtual #832                // Method mindustry/gen/Unit.removeBuild:(IIZ)V
      21: return

  public static void requestUnitPayload(mindustry.gen.Player, mindustry.gen.Unit);
    Code:
       0: aload_0
       1: ifnull        25
       4: aload_0
       5: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
       8: astore_3
       9: aload_3
      10: instanceof    #836                // class mindustry/gen/Payloadc
      13: ifeq          25
      16: aload_3
      17: checkcast     #836                // class mindustry/gen/Payloadc
      20: astore_2
      21: aload_1
      22: ifnonnull     26
      25: return
      26: aload_0
      27: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      30: astore_3
      31: aload_1
      32: invokevirtual #838                // Method mindustry/gen/Unit.isAI:()Z
      35: ifeq          87
      38: aload_1
      39: invokevirtual #841                // Method mindustry/gen/Unit.isGrounded:()Z
      42: ifeq          87
      45: aload_2
      46: aload_1
      47: invokeinterface #844,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickup:(Lmindustry/gen/Unit;)Z
      52: ifeq          87
      55: aload_1
      56: aload_3
      57: aload_3
      58: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
      61: getfield      #848                // Field mindustry/type/UnitType.hitSize:F
      64: fconst_2
      65: fmul
      66: aload_1
      67: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
      70: getfield      #848                // Field mindustry/type/UnitType.hitSize:F
      73: fconst_2
      74: fmul
      75: fadd
      76: invokevirtual #851                // Method mindustry/gen/Unit.within:(Larc/math/geom/Position;F)Z
      79: ifeq          87
      82: aload_3
      83: aload_1
      84: invokestatic  #852                // Method mindustry/gen/Call.pickedUnitPayload:(Lmindustry/gen/Unit;Lmindustry/gen/Unit;)V
      87: return

  public static void requestBuildPayload(mindustry.gen.Player, mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        25
       4: aload_0
       5: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
       8: astore_3
       9: aload_3
      10: instanceof    #836                // class mindustry/gen/Payloadc
      13: ifeq          25
      16: aload_3
      17: checkcast     #836                // class mindustry/gen/Payloadc
      20: astore_2
      21: aload_1
      22: ifnonnull     26
      25: return
      26: aload_0
      27: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      30: astore_3
      31: aload_3
      32: aload_1
      33: bipush        8
      35: aload_1
      36: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
      39: getfield      #860                // Field mindustry/world/Block.size:I
      42: imul
      43: i2f
      44: ldc_w         #863                // float 1.2f
      47: fmul
      48: ldc_w         #864                // float 40.0f
      51: fadd
      52: invokevirtual #851                // Method mindustry/gen/Unit.within:(Larc/math/geom/Position;F)Z
      55: ifne          59
      58: return
      59: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      62: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      65: ifeq          106
      68: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      71: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      74: aload_0
      75: getstatic     #865                // Field mindustry/net/Administration$ActionType.pickupBlock:Lmindustry/net/Administration$ActionType;
      78: aload_1
      79: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
      82: aload_3
      83: invokedynamic #868,  0            // InvokeDynamic #18:get:(Lmindustry/gen/Unit;)Larc/func/Cons;
      88: invokevirtual #764                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Lmindustry/world/Tile;Larc/func/Cons;)Z
      91: ifne          106
      94: new           #366                // class mindustry/net/ValidateException
      97: dup
      98: aload_0
      99: ldc_w         #871                // String Player cannot pick up a block.
     102: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
     105: athrow
     106: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     109: getfield      #873                // Field mindustry/core/GameState.teams:Lmindustry/game/Teams;
     112: aload_3
     113: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
     116: aload_1
     117: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
     120: invokevirtual #878                // Method mindustry/game/Teams.canInteract:(Lmindustry/game/Team;Lmindustry/game/Team;)Z
     123: ifeq          193
     126: aload_1
     127: invokevirtual #883                // Method mindustry/gen/Building.getPayload:()Lmindustry/world/blocks/payloads/Payload;
     130: astore        4
     132: aload         4
     134: ifnull        157
     137: aload_2
     138: aload         4
     140: invokeinterface #887,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickupPayload:(Lmindustry/world/blocks/payloads/Payload;)Z
     145: ifeq          157
     148: aload_3
     149: aload_1
     150: iconst_0
     151: invokestatic  #891                // Method mindustry/gen/Call.pickedBuildPayload:(Lmindustry/gen/Unit;Lmindustry/gen/Building;Z)V
     154: goto          193
     157: aload_1
     158: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     161: getfield      #895                // Field mindustry/world/Block.buildVisibility:Lmindustry/world/meta/BuildVisibility;
     164: getstatic     #899                // Field mindustry/world/meta/BuildVisibility.hidden:Lmindustry/world/meta/BuildVisibility;
     167: if_acmpeq     193
     170: aload_1
     171: invokevirtual #904                // Method mindustry/gen/Building.canPickup:()Z
     174: ifeq          193
     177: aload_2
     178: aload_1
     179: invokeinterface #906,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickup:(Lmindustry/gen/Building;)Z
     184: ifeq          193
     187: aload_3
     188: aload_1
     189: iconst_1
     190: invokestatic  #891                // Method mindustry/gen/Call.pickedBuildPayload:(Lmindustry/gen/Unit;Lmindustry/gen/Building;Z)V
     193: return

  public static void pickedUnitPayload(mindustry.gen.Unit, mindustry.gen.Unit);
    Code:
       0: aload_1
       1: ifnull        26
       4: aload_0
       5: instanceof    #836                // class mindustry/gen/Payloadc
       8: ifeq          26
      11: aload_0
      12: checkcast     #836                // class mindustry/gen/Payloadc
      15: astore_2
      16: aload_2
      17: aload_1
      18: invokeinterface #909,  2          // InterfaceMethod mindustry/gen/Payloadc.pickup:(Lmindustry/gen/Unit;)V
      23: goto          34
      26: aload_1
      27: ifnull        34
      30: aload_1
      31: invokevirtual #913                // Method mindustry/gen/Unit.remove:()V
      34: return

  public static void pickedBuildPayload(mindustry.gen.Unit, mindustry.gen.Building, boolean);
    Code:
       0: aload_1
       1: ifnull        162
       4: aload_0
       5: instanceof    #836                // class mindustry/gen/Payloadc
       8: ifeq          162
      11: aload_0
      12: checkcast     #836                // class mindustry/gen/Payloadc
      15: astore_3
      16: iload_2
      17: ifeq          94
      20: aload_1
      21: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
      24: getfield      #895                // Field mindustry/world/Block.buildVisibility:Lmindustry/world/meta/BuildVisibility;
      27: getstatic     #899                // Field mindustry/world/meta/BuildVisibility.hidden:Lmindustry/world/meta/BuildVisibility;
      30: if_acmpeq     60
      33: aload_1
      34: invokevirtual #904                // Method mindustry/gen/Building.canPickup:()Z
      37: ifeq          60
      40: aload_3
      41: aload_1
      42: invokeinterface #906,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickup:(Lmindustry/gen/Building;)Z
      47: ifeq          60
      50: aload_3
      51: aload_1
      52: invokeinterface #914,  2          // InterfaceMethod mindustry/gen/Payloadc.pickup:(Lmindustry/gen/Building;)V
      57: goto          201
      60: getstatic     #917                // Field mindustry/gen/Sounds.payloadPickup:Larc/audio/Sound;
      63: aload_0
      64: ldc_w         #923                // float 0.9f
      67: ldc_w         #924                // float 1.1f
      70: invokestatic  #925                // Method arc/math/Mathf.random:(FF)F
      73: invokevirtual #929                // Method arc/audio/Sound.at:(Larc/math/geom/Position;F)I
      76: pop
      77: getstatic     #934                // Field mindustry/content/Fx.unitPickup:Lmindustry/entities/Effect;
      80: aload_1
      81: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
      84: aload_1
      85: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
      88: invokevirtual #937                // Method mindustry/world/Tile.remove:()V
      91: goto          201
      94: aload_1
      95: invokevirtual #883                // Method mindustry/gen/Building.getPayload:()Lmindustry/world/blocks/payloads/Payload;
      98: astore        4
     100: aload         4
     102: ifnull        159
     105: aload_3
     106: aload         4
     108: invokeinterface #887,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickupPayload:(Lmindustry/world/blocks/payloads/Payload;)Z
     113: ifeq          159
     116: aload_1
     117: invokevirtual #940                // Method mindustry/gen/Building.takePayload:()Lmindustry/world/blocks/payloads/Payload;
     120: astore        5
     122: aload         5
     124: ifnull        159
     127: getstatic     #917                // Field mindustry/gen/Sounds.payloadPickup:Larc/audio/Sound;
     130: aload_0
     131: ldc_w         #923                // float 0.9f
     134: ldc_w         #924                // float 1.1f
     137: invokestatic  #925                // Method arc/math/Mathf.random:(FF)F
     140: invokevirtual #929                // Method arc/audio/Sound.at:(Larc/math/geom/Position;F)I
     143: pop
     144: aload_3
     145: aload         5
     147: invokeinterface #943,  2          // InterfaceMethod mindustry/gen/Payloadc.addPayload:(Lmindustry/world/blocks/payloads/Payload;)V
     152: getstatic     #934                // Field mindustry/content/Fx.unitPickup:Lmindustry/entities/Effect;
     155: aload_1
     156: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     159: goto          201
     162: aload_1
     163: ifnull        201
     166: iload_2
     167: ifeq          201
     170: getstatic     #917                // Field mindustry/gen/Sounds.payloadPickup:Larc/audio/Sound;
     173: aload_0
     174: ldc_w         #923                // float 0.9f
     177: ldc_w         #924                // float 1.1f
     180: invokestatic  #925                // Method arc/math/Mathf.random:(FF)F
     183: invokevirtual #929                // Method arc/audio/Sound.at:(Larc/math/geom/Position;F)I
     186: pop
     187: getstatic     #934                // Field mindustry/content/Fx.unitPickup:Lmindustry/entities/Effect;
     190: aload_1
     191: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     194: aload_1
     195: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
     198: invokevirtual #937                // Method mindustry/world/Tile.remove:()V
     201: return

  public static void requestDropPayload(mindustry.gen.Player, float, float);
    Code:
       0: aload_0
       1: ifnull        20
       4: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       7: invokevirtual #947                // Method mindustry/net/Net.client:()Z
      10: ifne          20
      13: aload_0
      14: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      17: ifeq          21
      20: return
      21: aload_0
      22: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      25: checkcast     #836                // class mindustry/gen/Payloadc
      28: astore_3
      29: aload_3
      30: invokeinterface #950,  1          // InterfaceMethod mindustry/gen/Payloadc.payloads:()Larc/struct/Seq;
      35: invokevirtual #953                // Method arc/struct/Seq.isEmpty:()Z
      38: ifeq          42
      41: return
      42: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      45: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      48: ifeq          92
      51: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      54: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      57: aload_0
      58: getstatic     #954                // Field mindustry/net/Administration$ActionType.dropPayload:Lmindustry/net/Administration$ActionType;
      61: aload_0
      62: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      65: invokevirtual #957                // Method mindustry/gen/Unit.tileOn:()Lmindustry/world/Tile;
      68: aload_3
      69: invokedynamic #961,  0            // InvokeDynamic #19:get:(Lmindustry/gen/Payloadc;)Larc/func/Cons;
      74: invokevirtual #764                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Lmindustry/world/Tile;Larc/func/Cons;)Z
      77: ifne          92
      80: new           #366                // class mindustry/net/ValidateException
      83: dup
      84: aload_0
      85: ldc_w         #964                // String Player cannot drop a payload.
      88: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      91: athrow
      92: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
      95: fload_1
      96: fload_2
      97: invokevirtual #971                // Method arc/math/geom/Vec2.set:(FF)Larc/math/geom/Vec2;
     100: aload_3
     101: invokevirtual #974                // Method arc/math/geom/Vec2.sub:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
     104: ldc_w         #977                // float 32.0f
     107: invokevirtual #978                // Method arc/math/geom/Vec2.limit:(F)Larc/math/geom/Vec2;
     110: aload_3
     111: invokevirtual #982                // Method arc/math/geom/Vec2.add:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
     114: pop
     115: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     118: getfield      #984                // Field arc/math/geom/Vec2.x:F
     121: fstore        4
     123: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     126: getfield      #985                // Field arc/math/geom/Vec2.y:F
     129: fstore        5
     131: aload_0
     132: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     135: fload         4
     137: fload         5
     139: invokestatic  #986                // Method mindustry/gen/Call.payloadDropped:(Lmindustry/gen/Unit;FF)V
     142: return

  public static void payloadDropped(mindustry.gen.Unit, float, float);
    Code:
       0: aload_0
       1: instanceof    #836                // class mindustry/gen/Payloadc
       4: ifeq          53
       7: aload_0
       8: checkcast     #836                // class mindustry/gen/Payloadc
      11: astore_3
      12: aload_3
      13: invokeinterface #990,  1          // InterfaceMethod mindustry/gen/Payloadc.x:()F
      18: fstore        4
      20: aload_3
      21: invokeinterface #993,  1          // InterfaceMethod mindustry/gen/Payloadc.y:()F
      26: fstore        5
      28: aload_3
      29: fload_1
      30: fload_2
      31: invokeinterface #995,  3          // InterfaceMethod mindustry/gen/Payloadc.set:(FF)V
      36: aload_3
      37: invokeinterface #998,  1          // InterfaceMethod mindustry/gen/Payloadc.dropLastPayload:()Z
      42: pop
      43: aload_3
      44: fload         4
      46: fload         5
      48: invokeinterface #995,  3          // InterfaceMethod mindustry/gen/Payloadc.set:(FF)V
      53: return

  public static void unitEnteredPayload(mindustry.gen.Unit, mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        19
       4: aload_1
       5: ifnull        19
       8: aload_0
       9: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
      12: aload_1
      13: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
      16: if_acmpeq     20
      19: return
      20: aload_0
      21: invokevirtual #913                // Method mindustry/gen/Unit.remove:()V
      24: aload_0
      25: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
      28: astore_3
      29: aload_3
      30: instanceof    #539                // class mindustry/ai/types/CommandAI
      33: ifeq          62
      36: aload_3
      37: checkcast     #539                // class mindustry/ai/types/CommandAI
      40: astore_2
      41: aload_2
      42: getfield      #541                // Field mindustry/ai/types/CommandAI.command:Lmindustry/ai/UnitCommand;
      45: getstatic     #1001               // Field mindustry/ai/UnitCommand.enterPayloadCommand:Lmindustry/ai/UnitCommand;
      48: if_acmpne     62
      51: aload_2
      52: invokevirtual #697                // Method mindustry/ai/types/CommandAI.clearCommands:()V
      55: aload_2
      56: getstatic     #550                // Field mindustry/ai/UnitCommand.moveCommand:Lmindustry/ai/UnitCommand;
      59: putfield      #541                // Field mindustry/ai/types/CommandAI.command:Lmindustry/ai/UnitCommand;
      62: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      65: invokevirtual #947                // Method mindustry/net/Net.client:()Z
      68: ifeq          81
      71: getstatic     #1004               // Field mindustry/Vars.netClient:Lmindustry/core/NetClient;
      74: aload_0
      75: getfield      #1008               // Field mindustry/gen/Unit.id:I
      78: invokevirtual #1011               // Method mindustry/core/NetClient.clearRemovedEntity:(I)V
      81: new           #1017               // class mindustry/world/blocks/payloads/UnitPayload
      84: dup
      85: aload_0
      86: invokespecial #1019               // Method mindustry/world/blocks/payloads/UnitPayload."<init>":(Lmindustry/gen/Unit;)V
      89: astore_2
      90: aload_1
      91: aload_1
      92: aload_2
      93: invokevirtual #1021               // Method mindustry/gen/Building.acceptPayload:(Lmindustry/gen/Building;Lmindustry/world/blocks/payloads/Payload;)Z
      96: ifeq          112
      99: getstatic     #1025               // Field mindustry/content/Fx.unitDrop:Lmindustry/entities/Effect;
     102: aload_1
     103: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     106: aload_1
     107: aload_1
     108: aload_2
     109: invokevirtual #1028               // Method mindustry/gen/Building.handlePayload:(Lmindustry/gen/Building;Lmindustry/world/blocks/payloads/Payload;)V
     112: return

  public static void dropItem(mindustry.gen.Player, float);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
       8: ifnonnull     12
      11: return
      12: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      15: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      18: ifeq          46
      21: aload_0
      22: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      25: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      28: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      31: ifgt          46
      34: new           #366                // class mindustry/net/ValidateException
      37: dup
      38: aload_0
      39: ldc_w         #1032               // String Player cannot drop an item.
      42: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      45: athrow
      46: aload_0
      47: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      50: astore_2
      51: getstatic     #1034               // Field mindustry/content/Fx.dropItem:Lmindustry/entities/Effect;
      54: aload_2
      55: getfield      #821                // Field mindustry/gen/Unit.x:F
      58: aload_2
      59: getfield      #823                // Field mindustry/gen/Unit.y:F
      62: fload_1
      63: getstatic     #1037               // Field arc/graphics/Color.white:Larc/graphics/Color;
      66: aload_2
      67: invokevirtual #314                // Method mindustry/gen/Unit.item:()Lmindustry/type/Item;
      70: invokevirtual #477                // Method mindustry/entities/Effect.at:(FFFLarc/graphics/Color;Ljava/lang/Object;)V
      73: aload_2
      74: invokevirtual #1042               // Method mindustry/gen/Unit.clearItem:()V
      77: return

  public static void rotateBlock(mindustry.gen.Player, mindustry.gen.Building, boolean);
    Code:
       0: aload_1
       1: ifnonnull     5
       4: return
       5: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       8: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      11: ifeq          61
      14: aload_0
      15: aload_1
      16: invokestatic  #748                // Method mindustry/entities/Units.canInteract:(Lmindustry/gen/Player;Lmindustry/gen/Building;)Z
      19: ifeq          49
      22: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      25: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      28: aload_0
      29: getstatic     #1045               // Field mindustry/net/Administration$ActionType.rotate:Lmindustry/net/Administration$ActionType;
      32: aload_1
      33: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
      36: aload_1
      37: iload_2
      38: invokedynamic #1048,  0           // InvokeDynamic #20:get:(Lmindustry/gen/Building;Z)Larc/func/Cons;
      43: invokevirtual #764                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Lmindustry/world/Tile;Larc/func/Cons;)Z
      46: ifne          61
      49: new           #366                // class mindustry/net/ValidateException
      52: dup
      53: aload_0
      54: ldc_w         #1051               // String Player cannot rotate a block.
      57: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      60: athrow
      61: aload_0
      62: ifnull        70
      65: aload_1
      66: aload_0
      67: invokevirtual #724                // Method mindustry/gen/Building.updateLastAccess:(Lmindustry/gen/Player;)V
      70: aload_1
      71: getfield      #1053               // Field mindustry/gen/Building.rotation:I
      74: istore_3
      75: aload_1
      76: aload_1
      77: getfield      #1053               // Field mindustry/gen/Building.rotation:I
      80: iload_2
      81: invokestatic  #1054               // Method arc/math/Mathf.sign:(Z)I
      84: iadd
      85: iconst_4
      86: invokestatic  #1058               // Method arc/math/Mathf.mod:(II)I
      89: putfield      #1053               // Field mindustry/gen/Building.rotation:I
      92: aload_1
      93: invokevirtual #1061               // Method mindustry/gen/Building.updateProximity:()V
      96: aload_1
      97: invokevirtual #1064               // Method mindustry/gen/Building.noSleep:()V
     100: getstatic     #1067               // Field mindustry/content/Fx.rotateBlock:Lmindustry/entities/Effect;
     103: aload_1
     104: getfield      #1070               // Field mindustry/gen/Building.x:F
     107: aload_1
     108: getfield      #1071               // Field mindustry/gen/Building.y:F
     111: aload_1
     112: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     115: getfield      #860                // Field mindustry/world/Block.size:I
     118: i2f
     119: invokevirtual #1072               // Method mindustry/entities/Effect.at:(FFF)V
     122: getstatic     #1075               // Field mindustry/Vars.headless:Z
     125: ifne          144
     128: getstatic     #1078               // Field mindustry/gen/Sounds.blockRotate:Larc/audio/Sound;
     131: aload_1
     132: fconst_1
     133: ldc           #18                 // float 0.1f
     135: invokestatic  #1081               // Method arc/math/Mathf.range:(F)F
     138: fadd
     139: fconst_1
     140: invokevirtual #1085               // Method arc/audio/Sound.at:(Larc/math/geom/Position;FF)I
     143: pop
     144: new           #1088               // class mindustry/game/EventType$BuildRotateEvent
     147: dup
     148: aload_1
     149: aload_0
     150: ifnonnull     157
     153: aconst_null
     154: goto          161
     157: aload_0
     158: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     161: iload_3
     162: invokespecial #1090               // Method mindustry/game/EventType$BuildRotateEvent."<init>":(Lmindustry/gen/Building;Lmindustry/gen/Unit;I)V
     165: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     168: return

  public static void tileConfig(mindustry.gen.Player, mindustry.gen.Building, java.lang.Object);
    Code:
       0: aload_1
       1: ifnonnull     25
       4: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       7: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      10: ifeq          25
      13: new           #366                // class mindustry/net/ValidateException
      16: dup
      17: aload_0
      18: ldc_w         #1093               // String building is null
      21: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      24: athrow
      25: aload_1
      26: ifnonnull     30
      29: return
      30: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      33: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      36: ifeq          135
      39: aload_0
      40: aload_1
      41: invokestatic  #748                // Method mindustry/entities/Units.canInteract:(Lmindustry/gen/Player;Lmindustry/gen/Building;)Z
      44: ifeq          73
      47: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      50: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      53: aload_0
      54: getstatic     #1095               // Field mindustry/net/Administration$ActionType.configure:Lmindustry/net/Administration$ActionType;
      57: aload_1
      58: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
      61: aload_2
      62: invokedynamic #1098,  0           // InvokeDynamic #21:get:(Ljava/lang/Object;)Larc/func/Cons;
      67: invokevirtual #764                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Lmindustry/world/Tile;Larc/func/Cons;)Z
      70: ifne          135
      73: aload_0
      74: getfield      #1101               // Field mindustry/gen/Player.con:Lmindustry/net/NetConnection;
      77: ifnull        115
      80: new           #1105               // class mindustry/gen/TileConfigCallPacket
      83: dup
      84: invokespecial #1107               // Method mindustry/gen/TileConfigCallPacket."<init>":()V
      87: astore_3
      88: aload_3
      89: aload_0
      90: putfield      #1108               // Field mindustry/gen/TileConfigCallPacket.player:Lmindustry/gen/Player;
      93: aload_3
      94: aload_1
      95: putfield      #1109               // Field mindustry/gen/TileConfigCallPacket.build:Lmindustry/gen/Building;
      98: aload_3
      99: aload_1
     100: invokevirtual #1112               // Method mindustry/gen/Building.config:()Ljava/lang/Object;
     103: putfield      #1114               // Field mindustry/gen/TileConfigCallPacket.value:Ljava/lang/Object;
     106: aload_0
     107: getfield      #1101               // Field mindustry/gen/Player.con:Lmindustry/net/NetConnection;
     110: aload_3
     111: iconst_1
     112: invokevirtual #1118               // Method mindustry/net/NetConnection.send:(Ljava/lang/Object;Z)V
     115: aload_0
     116: invokevirtual #786                // Method mindustry/gen/Player.isLocal:()Z
     119: ifne          134
     122: new           #366                // class mindustry/net/ValidateException
     125: dup
     126: aload_0
     127: ldc_w         #1124               // String Player cannot configure a tile.
     130: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
     133: athrow
     134: return
     135: aload_0
     136: ifnull        144
     139: aload_1
     140: aload_0
     141: invokevirtual #724                // Method mindustry/gen/Building.updateLastAccess:(Lmindustry/gen/Player;)V
     144: aload_1
     145: aload_0
     146: ifnull        156
     149: aload_0
     150: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     153: ifeq          160
     156: aconst_null
     157: goto          164
     160: aload_0
     161: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     164: aload_2
     165: invokevirtual #1126               // Method mindustry/gen/Building.configured:(Lmindustry/gen/Unit;Ljava/lang/Object;)V
     168: new           #1130               // class mindustry/game/EventType$ConfigEvent
     171: dup
     172: aload_1
     173: aload_0
     174: aload_2
     175: invokespecial #1132               // Method mindustry/game/EventType$ConfigEvent."<init>":(Lmindustry/gen/Building;Lmindustry/gen/Player;Ljava/lang/Object;)V
     178: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     181: return

  public static void tileTap(mindustry.gen.Player, mindustry.world.Tile);
    Code:
       0: aload_1
       1: ifnonnull     5
       4: return
       5: new           #1135               // class mindustry/game/EventType$TapEvent
       8: dup
       9: aload_0
      10: aload_1
      11: invokespecial #1137               // Method mindustry/game/EventType$TapEvent."<init>":(Lmindustry/gen/Player;Lmindustry/world/Tile;)V
      14: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
      17: return

  public static void buildingControlSelect(mindustry.gen.Player, mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        15
       4: aload_1
       5: ifnull        15
       8: aload_0
       9: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      12: ifeq          16
      15: return
      16: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      19: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      22: ifeq          79
      25: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      28: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
      31: getfield      #1140               // Field mindustry/game/Rules.possessionAllowed:Z
      34: ifne          45
      37: aload_0
      38: invokevirtual #1143               // Method mindustry/gen/Player.bestCore:()Lmindustry/world/blocks/storage/CoreBlock$CoreBuild;
      41: aload_1
      42: if_acmpne     67
      45: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      48: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      51: aload_0
      52: getstatic     #1147               // Field mindustry/net/Administration$ActionType.buildSelect:Lmindustry/net/Administration$ActionType;
      55: aload_1
      56: invokedynamic #1150,  0           // InvokeDynamic #22:get:(Lmindustry/gen/Building;)Larc/func/Cons;
      61: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      64: ifne          79
      67: new           #366                // class mindustry/net/ValidateException
      70: dup
      71: aload_0
      72: ldc_w         #1153               // String Player cannot control a building.
      75: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      78: athrow
      79: aload_0
      80: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      83: aload_1
      84: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
      87: if_acmpne     139
      90: aload_1
      91: aload_0
      92: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      95: invokevirtual #1155               // Method mindustry/gen/Building.canControlSelect:(Lmindustry/gen/Unit;)Z
      98: ifeq          139
     101: aload_0
     102: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     105: astore_2
     106: aload_0
     107: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     110: aload_1
     111: invokestatic  #1158               // Method mindustry/gen/Call.unitBuildingControlSelect:(Lmindustry/gen/Unit;Lmindustry/gen/Building;)V
     114: aload_2
     115: getfield      #1162               // Field mindustry/gen/Unit.dead:Z
     118: ifne          139
     121: aload_2
     122: getfield      #1164               // Field mindustry/gen/Unit.spawnedByCore:Z
     125: ifeq          139
     128: aload_2
     129: invokevirtual #1167               // Method mindustry/gen/Unit.isPlayer:()Z
     132: ifne          139
     135: aload_2
     136: invokestatic  #1170               // Method mindustry/gen/Call.unitDespawn:(Lmindustry/gen/Unit;)V
     139: return

  public static void unitBuildingControlSelect(mindustry.gen.Unit, mindustry.gen.Building);
    Code:
       0: aload_0
       1: ifnull        11
       4: aload_0
       5: invokevirtual #1173               // Method mindustry/gen/Unit.dead:()Z
       8: ifeq          12
      11: return
      12: aload_0
      13: invokevirtual #1174               // Method mindustry/gen/Unit.team:()Lmindustry/game/Team;
      16: aload_1
      17: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
      20: if_acmpne     45
      23: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
      26: invokevirtual #947                // Method mindustry/net/Net.client:()Z
      29: ifne          40
      32: aload_1
      33: aload_0
      34: invokevirtual #1155               // Method mindustry/gen/Building.canControlSelect:(Lmindustry/gen/Unit;)Z
      37: ifeq          45
      40: aload_1
      41: aload_0
      42: invokevirtual #1175               // Method mindustry/gen/Building.onControlSelect:(Lmindustry/gen/Unit;)V
      45: return

  public static void unitControl(mindustry.gen.Player, mindustry.gen.Unit);
    Code:
       0: aload_0
       1: ifnonnull     5
       4: return
       5: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       8: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      11: ifeq          60
      14: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      17: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
      20: getfield      #1140               // Field mindustry/game/Rules.possessionAllowed:Z
      23: ifeq          48
      26: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      29: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      32: aload_0
      33: getstatic     #1178               // Field mindustry/net/Administration$ActionType.control:Lmindustry/net/Administration$ActionType;
      36: aload_1
      37: invokedynamic #1181,  0           // InvokeDynamic #23:get:(Lmindustry/gen/Unit;)Larc/func/Cons;
      42: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      45: ifne          60
      48: new           #366                // class mindustry/net/ValidateException
      51: dup
      52: aload_0
      53: ldc_w         #1182               // String Player cannot control a unit.
      56: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      59: athrow
      60: aload_1
      61: ifnonnull     71
      64: aload_0
      65: invokevirtual #1184               // Method mindustry/gen/Player.clearUnit:()V
      68: goto          269
      71: aload_1
      72: invokevirtual #838                // Method mindustry/gen/Unit.isAI:()Z
      75: ifeq          248
      78: aload_1
      79: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
      82: aload_0
      83: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      86: if_acmpne     248
      89: aload_1
      90: getfield      #1162               // Field mindustry/gen/Unit.dead:Z
      93: ifne          248
      96: aload_1
      97: invokevirtual #1187               // Method mindustry/gen/Unit.playerControllable:()Z
     100: ifeq          248
     103: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
     106: invokevirtual #947                // Method mindustry/net/Net.client:()Z
     109: ifeq          132
     112: aload_0
     113: invokevirtual #786                // Method mindustry/gen/Player.isLocal:()Z
     116: ifeq          132
     119: aload_0
     120: aload_0
     121: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     124: putfield      #1190               // Field mindustry/gen/Player.justSwitchFrom:Lmindustry/gen/Unit;
     127: aload_0
     128: aload_1
     129: putfield      #1194               // Field mindustry/gen/Player.justSwitchTo:Lmindustry/gen/Unit;
     132: aload_0
     133: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     136: astore_2
     137: aload_0
     138: aload_1
     139: invokevirtual #1197               // Method mindustry/gen/Player.unit:(Lmindustry/gen/Unit;)V
     142: aload_2
     143: ifnull        207
     146: aload_2
     147: getfield      #1164               // Field mindustry/gen/Unit.spawnedByCore:Z
     150: ifeq          164
     153: aload_1
     154: aload_2
     155: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     158: putfield      #1199               // Field mindustry/gen/Unit.dockedType:Lmindustry/type/UnitType;
     161: goto          189
     164: aload_2
     165: getfield      #1199               // Field mindustry/gen/Unit.dockedType:Lmindustry/type/UnitType;
     168: ifnull        189
     171: aload_2
     172: getfield      #1199               // Field mindustry/gen/Unit.dockedType:Lmindustry/type/UnitType;
     175: getfield      #1202               // Field mindustry/type/UnitType.coreUnitDock:Z
     178: ifeq          189
     181: aload_1
     182: aload_2
     183: getfield      #1199               // Field mindustry/gen/Unit.dockedType:Lmindustry/type/UnitType;
     186: putfield      #1199               // Field mindustry/gen/Unit.dockedType:Lmindustry/type/UnitType;
     189: aload_2
     190: getfield      #1164               // Field mindustry/gen/Unit.spawnedByCore:Z
     193: ifeq          207
     196: aload_2
     197: invokevirtual #1167               // Method mindustry/gen/Unit.isPlayer:()Z
     200: ifne          207
     203: aload_2
     204: invokestatic  #1170               // Method mindustry/gen/Call.unitDespawn:(Lmindustry/gen/Unit;)V
     207: getstatic     #1205               // Field mindustry/content/Fx.unitSpirit:Lmindustry/entities/Effect;
     210: getfield      #483                // Field mindustry/entities/Effect.lifetime:F
     213: aload_1
     214: invokedynamic #1208,  0           // InvokeDynamic #24:run:(Lmindustry/gen/Unit;)Ljava/lang/Runnable;
     219: invokestatic  #263                // Method arc/util/Time.run:(FLjava/lang/Runnable;)V
     222: aload_0
     223: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     226: ifne          245
     229: getstatic     #1205               // Field mindustry/content/Fx.unitSpirit:Lmindustry/entities/Effect;
     232: aload_0
     233: getfield      #1211               // Field mindustry/gen/Player.x:F
     236: aload_0
     237: getfield      #1212               // Field mindustry/gen/Player.y:F
     240: fconst_0
     241: aload_1
     242: invokevirtual #1213               // Method mindustry/entities/Effect.at:(FFFLjava/lang/Object;)V
     245: goto          269
     248: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
     251: invokevirtual #335                // Method mindustry/net/Net.server:()Z
     254: ifeq          269
     257: new           #366                // class mindustry/net/ValidateException
     260: dup
     261: aload_0
     262: ldc_w         #1216               // String Player attempted to control invalid unit.
     265: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
     268: athrow
     269: new           #1218               // class mindustry/game/EventType$UnitControlEvent
     272: dup
     273: aload_0
     274: aload_1
     275: invokespecial #1220               // Method mindustry/game/EventType$UnitControlEvent."<init>":(Lmindustry/gen/Player;Lmindustry/gen/Unit;)V
     278: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     281: return

  public static void unitClear(mindustry.gen.Player);
    Code:
       0: aload_0
       1: ifnonnull     5
       4: return
       5: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
       8: invokevirtual #335                // Method mindustry/net/Net.server:()Z
      11: ifeq          47
      14: getstatic     #341                // Field mindustry/Vars.netServer:Lmindustry/core/NetServer;
      17: getfield      #345                // Field mindustry/core/NetServer.admins:Lmindustry/net/Administration;
      20: aload_0
      21: getstatic     #1223               // Field mindustry/net/Administration$ActionType.respawn:Lmindustry/net/Administration$ActionType;
      24: invokedynamic #1226,  0           // InvokeDynamic #25:get:()Larc/func/Cons;
      29: invokevirtual #360                // Method mindustry/net/Administration.allowAction:(Lmindustry/gen/Player;Lmindustry/net/Administration$ActionType;Larc/func/Cons;)Z
      32: ifne          47
      35: new           #366                // class mindustry/net/ValidateException
      38: dup
      39: aload_0
      40: ldc_w         #1227               // String Player cannot respawn.
      43: invokespecial #370                // Method mindustry/net/ValidateException."<init>":(Lmindustry/gen/Player;Ljava/lang/String;)V
      46: athrow
      47: aload_0
      48: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      51: ifne          250
      54: aload_0
      55: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      58: getfield      #1164               // Field mindustry/gen/Unit.spawnedByCore:Z
      61: ifne          250
      64: aload_0
      65: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      68: getfield      #1199               // Field mindustry/gen/Unit.dockedType:Lmindustry/type/UnitType;
      71: astore_1
      72: aload_1
      73: ifnonnull     96
      76: aload_0
      77: invokevirtual #1143               // Method mindustry/gen/Player.bestCore:()Lmindustry/world/blocks/storage/CoreBlock$CoreBuild;
      80: astore_2
      81: aload_2
      82: ifnull        96
      85: aload_2
      86: getfield      #1229               // Field mindustry/world/blocks/storage/CoreBlock$CoreBuild.block:Lmindustry/world/Block;
      89: checkcast     #1232               // class mindustry/world/blocks/storage/CoreBlock
      92: getfield      #1234               // Field mindustry/world/blocks/storage/CoreBlock.unitType:Lmindustry/type/UnitType;
      95: astore_1
      96: aload_1
      97: ifnull        250
     100: aload_1
     101: getfield      #1202               // Field mindustry/type/UnitType.coreUnitDock:Z
     104: ifeq          250
     107: getstatic     #1237               // Field mindustry/content/Fx.spawn:Lmindustry/entities/Effect;
     110: aload_0
     111: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     114: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
     117: invokevirtual #947                // Method mindustry/net/Net.client:()Z
     120: ifne          249
     123: aload_1
     124: aload_0
     125: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     128: invokevirtual #1240               // Method mindustry/type/UnitType.create:(Lmindustry/game/Team;)Lmindustry/gen/Unit;
     131: astore_2
     132: aload_2
     133: aload_0
     134: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     137: invokevirtual #1244               // Method mindustry/gen/Unit.set:(Larc/math/geom/Position;)V
     140: aload_0
     141: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     144: invokevirtual #1246               // Method mindustry/gen/Unit.isFlying:()Z
     147: ifeq          224
     150: aload_2
     151: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     154: getfield      #1249               // Field mindustry/type/UnitType.flying:Z
     157: ifeq          224
     160: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     163: aload_0
     164: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     167: getfield      #1252               // Field mindustry/gen/Unit.rotation:F
     170: ldc_w         #1254               // float 180.0f
     173: fadd
     174: aload_0
     175: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     178: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
     181: fconst_2
     182: fdiv
     183: aload_2
     184: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
     187: fconst_2
     188: fdiv
     189: fadd
     190: invokevirtual #1256               // Method arc/math/geom/Vec2.trns:(FF)Larc/math/geom/Vec2;
     193: pop
     194: aload_2
     195: dup
     196: getfield      #821                // Field mindustry/gen/Unit.x:F
     199: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     202: getfield      #984                // Field arc/math/geom/Vec2.x:F
     205: fadd
     206: putfield      #821                // Field mindustry/gen/Unit.x:F
     209: aload_2
     210: dup
     211: getfield      #823                // Field mindustry/gen/Unit.y:F
     214: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     217: getfield      #985                // Field arc/math/geom/Vec2.y:F
     220: fadd
     221: putfield      #823                // Field mindustry/gen/Unit.y:F
     224: aload_2
     225: aload_0
     226: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     229: getfield      #1252               // Field mindustry/gen/Unit.rotation:F
     232: invokevirtual #1259               // Method mindustry/gen/Unit.rotation:(F)V
     235: aload_2
     236: aload_0
     237: invokevirtual #1262               // Method mindustry/gen/Unit.controller:(Lmindustry/entities/units/UnitController;)V
     240: aload_2
     241: iconst_1
     242: invokevirtual #1265               // Method mindustry/gen/Unit.spawnedByCore:(Z)V
     245: aload_2
     246: invokevirtual #1267               // Method mindustry/gen/Unit.add:()V
     249: return
     250: getstatic     #1237               // Field mindustry/content/Fx.spawn:Lmindustry/entities/Effect;
     253: aload_0
     254: invokevirtual #637                // Method mindustry/entities/Effect.at:(Larc/math/geom/Position;)V
     257: aload_0
     258: invokevirtual #1184               // Method mindustry/gen/Player.clearUnit:()V
     261: aload_0
     262: invokevirtual #1269               // Method mindustry/gen/Player.checkSpawn:()V
     265: aload_0
     266: ldc_w         #1272               // float 61.0f
     269: putfield      #1273               // Field mindustry/gen/Player.deathTimer:F
     272: return

  protected void createPlanLists();
    Code:
       0: aload_0
       1: new           #1276               // class mindustry/input/InputHandler$1
       4: dup
       5: aload_0
       6: aload_0
       7: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      10: iconst_1
      11: anewarray     #37                 // class arc/struct/Seq
      14: dup
      15: iconst_0
      16: aload_0
      17: getfield      #82                 // Field linePlans:Larc/struct/Seq;
      20: aastore
      21: invokespecial #1278               // Method mindustry/input/InputHandler$1."<init>":(Lmindustry/input/InputHandler;Larc/math/geom/QuadTree;[Larc/struct/Seq;)V
      24: putfield      #1281               // Field allPlans:Larc/util/Eachable;
      27: aload_0
      28: new           #1285               // class mindustry/input/InputHandler$QueryEachable
      31: dup
      32: aconst_null
      33: iconst_2
      34: anewarray     #37                 // class arc/struct/Seq
      37: dup
      38: iconst_0
      39: aload_0
      40: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
      43: aastore
      44: dup
      45: iconst_1
      46: aload_0
      47: getfield      #82                 // Field linePlans:Larc/struct/Seq;
      50: aastore
      51: invokespecial #1287               // Method mindustry/input/InputHandler$QueryEachable."<init>":(Larc/math/geom/QuadTree;[Larc/struct/Seq;)V
      54: putfield      #1290               // Field allSelectLines:Larc/util/Eachable;
      57: aload_0
      58: new           #1285               // class mindustry/input/InputHandler$QueryEachable
      61: dup
      62: aload_0
      63: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      66: iconst_1
      67: anewarray     #37                 // class arc/struct/Seq
      70: dup
      71: iconst_0
      72: aload_0
      73: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
      76: aastore
      77: invokespecial #1287               // Method mindustry/input/InputHandler$QueryEachable."<init>":(Larc/math/geom/QuadTree;[Larc/struct/Seq;)V
      80: putfield      #1293               // Field allRenderPlansConfig:Larc/util/Eachable;
      83: return

  public void updateSelectQuadtree();
    Code:
       0: aload_0
       1: getfield      #141                // Field selectPlanTree:Larc/math/geom/QuadTree;
       4: aload_0
       5: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
       8: invokevirtual #1296               // Method arc/math/geom/QuadTree.fill:(Larc/struct/Seq;)V
      11: return

  public void addLock(arc.func.Boolp);
    Code:
       0: aload_0
       1: getfield      #42                 // Field inputLocks:Larc/struct/Seq;
       4: aload_1
       5: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
       8: pop
       9: return

  public boolean locked();
    Code:
       0: aload_0
       1: getfield      #42                 // Field inputLocks:Larc/struct/Seq;
       4: invokedynamic #1300,  0           // InvokeDynamic #26:get:()Larc/func/Boolf;
       9: invokevirtual #1303               // Method arc/struct/Seq.contains:(Larc/func/Boolf;)Z
      12: ireturn

  public arc.util.Eachable<mindustry.entities.units.BuildPlan> allPlans();
    Code:
       0: aload_0
       1: getfield      #1281               // Field allPlans:Larc/util/Eachable;
       4: areturn

  public boolean isUsingSchematic();
    Code:
       0: aload_0
       1: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
       4: invokevirtual #953                // Method arc/struct/Seq.isEmpty:()Z
       7: ifne          14
      10: iconst_1
      11: goto          15
      14: iconst_0
      15: ireturn

  public void spectate(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: aload_1
       2: putfield      #1306               // Field spectating:Lmindustry/gen/Unit;
       5: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
       8: getfield      #1315               // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
      11: aload_1
      12: invokevirtual #492                // Method arc/math/geom/Vec2.set:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
      15: pop
      16: return

  public void reset();
    Code:
       0: aload_0
       1: iconst_0
       2: putfield      #1320               // Field logicCutscene:Z
       5: aload_0
       6: iconst_0
       7: putfield      #1323               // Field logicHideHud:Z
      10: aload_0
      11: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
      14: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      17: pop
      18: aload_0
      19: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      22: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      25: pop
      26: aload_0
      27: fconst_0
      28: putfield      #1326               // Field itemDepositCooldown:F
      31: aload_0
      32: getfield      #122                // Field controlGroups:[Larc/struct/IntSeq;
      35: aconst_null
      36: invokestatic  #1327               // Method java/util/Arrays.fill:([Ljava/lang/Object;Ljava/lang/Object;)V
      39: aload_0
      40: aconst_null
      41: putfield      #1332               // Field lastUnit:Lmindustry/gen/Unit;
      44: aload_0
      45: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
      48: invokevirtual #1335               // Method arc/struct/Queue.clear:()V
      51: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      54: iconst_0
      55: putfield      #1336               // Field mindustry/gen/Player.shooting:Z
      58: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      61: fconst_0
      62: putfield      #442                // Field mindustry/gen/Player.pingTime:F
      65: return

  public void getSyncedPlans(arc.struct.Seq<mindustry.entities.units.BuildPlan>);
    Code:
       0: aload_0
       1: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
       4: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
       7: astore_2
       8: aload_2
       9: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      14: ifeq          43
      17: aload_2
      18: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      23: checkcast     #74                 // class mindustry/entities/units/BuildPlan
      26: astore_3
      27: aload_3
      28: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
      31: ifne          40
      34: aload_1
      35: aload_3
      36: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
      39: pop
      40: goto          8
      43: return

  public void update();
    Code:
       0: aload_0
       1: getfield      #1306               // Field spectating:Lmindustry/gen/Unit;
       4: ifnull        38
       7: aload_0
       8: getfield      #1306               // Field spectating:Lmindustry/gen/Unit;
      11: invokevirtual #1342               // Method mindustry/gen/Unit.isValid:()Z
      14: ifeq          33
      17: aload_0
      18: getfield      #1306               // Field spectating:Lmindustry/gen/Unit;
      21: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
      24: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      27: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      30: if_acmpeq     38
      33: aload_0
      34: aconst_null
      35: putfield      #1306               // Field spectating:Lmindustry/gen/Unit;
      38: aload_0
      39: getfield      #1320               // Field logicCutscene:Z
      42: ifeq          75
      45: getstatic     #1345               // Field mindustry/Vars.renderer:Lmindustry/core/Renderer;
      48: invokevirtual #1349               // Method mindustry/core/Renderer.isCutscene:()Z
      51: ifne          75
      54: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
      57: getfield      #1315               // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
      60: aload_0
      61: getfield      #12                 // Field logicCamPan:Larc/math/geom/Vec2;
      64: aload_0
      65: getfield      #19                 // Field logicCamSpeed:F
      68: invokevirtual #1354               // Method arc/math/geom/Vec2.lerpDelta:(Larc/math/geom/Position;F)Larc/math/geom/Vec2;
      71: pop
      72: goto          81
      75: aload_0
      76: ldc           #23                 // float -1.0f
      78: putfield      #24                 // Field logicCutsceneZoom:F
      81: aload_0
      82: dup
      83: getfield      #1326               // Field itemDepositCooldown:F
      86: getstatic     #1358               // Field arc/util/Time.delta:F
      89: ldc_w         #1361               // float 60.0f
      92: fdiv
      93: fsub
      94: putfield      #1326               // Field itemDepositCooldown:F
      97: aload_0
      98: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     101: invokedynamic #1362,  0           // InvokeDynamic #27:get:()Larc/func/Boolf;
     106: invokevirtual #1363               // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
     109: pop
     110: aload_0
     111: getfield      #107                // Field commandMode:Z
     114: ifne          122
     117: aload_0
     118: iconst_0
     119: putfield      #110                // Field commandRect:Z
     122: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     125: invokevirtual #1367               // Method mindustry/gen/Player.isBuilder:()Z
     128: ifeq          295
     131: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     134: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     137: getfield      #1370               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     140: astore_1
     141: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     144: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     147: aload_0
     148: getfield      #1332               // Field lastUnit:Lmindustry/gen/Unit;
     151: if_acmpeq     208
     154: aload_1
     155: getfield      #1371               // Field arc/struct/Queue.size:I
     158: iconst_1
     159: if_icmpgt     208
     162: aload_1
     163: aload_0
     164: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     167: getfield      #1371               // Field arc/struct/Queue.size:I
     170: invokevirtual #1372               // Method arc/struct/Queue.ensureCapacity:(I)V
     173: aload_0
     174: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     177: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     180: astore_2
     181: aload_2
     182: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     187: ifeq          208
     190: aload_2
     191: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     196: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     199: astore_3
     200: aload_1
     201: aload_3
     202: invokevirtual #1375               // Method arc/struct/Queue.addLast:(Ljava/lang/Object;)V
     205: goto          181
     208: aload_0
     209: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     212: getfield      #1371               // Field arc/struct/Queue.size:I
     215: aload_1
     216: getfield      #1371               // Field arc/struct/Queue.size:I
     219: if_icmpne     253
     222: aload_0
     223: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     226: getfield      #1371               // Field arc/struct/Queue.size:I
     229: ifle          295
     232: aload_1
     233: getfield      #1371               // Field arc/struct/Queue.size:I
     236: ifle          295
     239: aload_0
     240: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     243: invokevirtual #1378               // Method arc/struct/Queue.first:()Ljava/lang/Object;
     246: aload_1
     247: invokevirtual #1378               // Method arc/struct/Queue.first:()Ljava/lang/Object;
     250: if_acmpeq     295
     253: aload_0
     254: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     257: invokevirtual #1335               // Method arc/struct/Queue.clear:()V
     260: aload_1
     261: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     264: astore_2
     265: aload_2
     266: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     271: ifeq          295
     274: aload_2
     275: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     280: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     283: astore_3
     284: aload_0
     285: getfield      #94                 // Field lastPlans:Larc/struct/Queue;
     288: aload_3
     289: invokevirtual #1375               // Method arc/struct/Queue.addLast:(Ljava/lang/Object;)V
     292: goto          265
     295: aload_0
     296: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     299: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     302: putfield      #1332               // Field lastUnit:Lmindustry/gen/Unit;
     305: aload_0
     306: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
     309: invokevirtual #1381               // Method arc/math/geom/QuadTree.clear:()V
     312: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     315: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     318: ifne          347
     321: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     324: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     327: getfield      #1370               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     330: aload_0
     331: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
     334: dup
     335: invokestatic  #1382               // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;
     338: pop
     339: invokedynamic #1387,  0           // InvokeDynamic #28:get:(Larc/math/geom/QuadTree;)Larc/func/Cons;
     344: invokevirtual #1390               // Method arc/struct/Queue.each:(Larc/func/Cons;)V
     347: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     350: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
     353: getfield      #1398               // Field mindustry/core/UI.chatfrag:Lmindustry/ui/fragments/ChatFragment;
     356: invokevirtual #1404               // Method mindustry/ui/fragments/ChatFragment.shown:()Z
     359: putfield      #1409               // Field mindustry/gen/Player.typing:Z
     362: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     365: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     368: ifeq          376
     371: aload_0
     372: iconst_0
     373: putfield      #1412               // Field droppingItem:Z
     376: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     379: invokevirtual #1367               // Method mindustry/gen/Player.isBuilder:()Z
     382: ifeq          398
     385: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     388: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     391: aload_0
     392: getfield      #57                 // Field isBuilding:Z
     395: invokevirtual #1415               // Method mindustry/gen/Unit.updateBuilding:(Z)V
     398: aload_0
     399: invokevirtual #1418               // Method locked:()Z
     402: ifeq          410
     405: aload_0
     406: aconst_null
     407: putfield      #1421               // Field block:Lmindustry/world/Block;
     410: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     413: aload_0
     414: getfield      #1421               // Field block:Lmindustry/world/Block;
     417: putfield      #1422               // Field mindustry/gen/Player.selectedBlock:Lmindustry/world/Block;
     420: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     423: aload_0
     424: getfield      #53                 // Field rotation:I
     427: putfield      #1425               // Field mindustry/gen/Player.selectedRotation:I
     430: aload_0
     431: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     434: getfield      #1336               // Field mindustry/gen/Player.shooting:Z
     437: putfield      #64                 // Field wasShooting:Z
     440: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     443: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     446: ifne          499
     449: aload_0
     450: dup
     451: getfield      #1428               // Field recentRespawnTimer:F
     454: getstatic     #1358               // Field arc/util/Time.delta:F
     457: ldc_w         #1431               // float 70.0f
     460: fdiv
     461: fsub
     462: dup_x1
     463: putfield      #1428               // Field recentRespawnTimer:F
     466: fconst_0
     467: fcmpg
     468: ifgt          499
     471: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     474: getfield      #1190               // Field mindustry/gen/Player.justSwitchFrom:Lmindustry/gen/Unit;
     477: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     480: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     483: if_acmpeq     499
     486: aload_0
     487: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     490: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     493: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     496: putfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
     499: aload_0
     500: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
     503: ifnull        592
     506: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     509: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     512: ifeq          592
     515: aload_0
     516: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
     519: getfield      #1435               // Field mindustry/type/UnitType.playerControllable:Z
     522: ifeq          592
     525: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     528: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     531: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     534: getfield      #1211               // Field mindustry/gen/Player.x:F
     537: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     540: getfield      #1212               // Field mindustry/gen/Player.y:F
     543: aload_0
     544: invokedynamic #1437,  0           // InvokeDynamic #29:get:(Lmindustry/input/InputHandler;)Larc/func/Boolf;
     549: invokestatic  #1440               // Method mindustry/entities/Units.closest:(Lmindustry/game/Team;FFLarc/func/Boolf;)Lmindustry/gen/Unit;
     552: astore_1
     553: aload_1
     554: ifnull        592
     557: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
     560: invokevirtual #947                // Method mindustry/net/Net.client:()Z
     563: ifeq          580
     566: aload_0
     567: getfield      #49                 // Field controlInterval:Larc/util/Interval;
     570: iconst_0
     571: ldc_w         #1431               // float 70.0f
     574: invokevirtual #1444               // Method arc/util/Interval.get:(IF)Z
     577: ifeq          592
     580: aload_0
     581: fconst_1
     582: putfield      #1428               // Field recentRespawnTimer:F
     585: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     588: aload_1
     589: invokestatic  #1447               // Method mindustry/gen/Call.unitControl:(Lmindustry/gen/Player;Lmindustry/gen/Unit;)V
     592: return

  public void checkUnit();
    Code:
       0: aload_0
       1: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
       4: ifnull        140
       7: aload_0
       8: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
      11: getfield      #1435               // Field mindustry/type/UnitType.playerControllable:Z
      14: ifeq          140
      17: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      20: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      23: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      26: getfield      #1211               // Field mindustry/gen/Player.x:F
      29: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      32: getfield      #1212               // Field mindustry/gen/Player.y:F
      35: aload_0
      36: invokedynamic #1450,  0           // InvokeDynamic #30:get:(Lmindustry/input/InputHandler;)Larc/func/Boolf;
      41: invokestatic  #1440               // Method mindustry/entities/Units.closest:(Lmindustry/game/Team;FFLarc/func/Boolf;)Lmindustry/gen/Unit;
      44: astore_1
      45: aload_1
      46: ifnonnull     110
      49: aload_0
      50: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
      53: getstatic     #1451               // Field mindustry/content/UnitTypes.block:Lmindustry/type/UnitType;
      56: if_acmpne     110
      59: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      62: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      65: getfield      #1211               // Field mindustry/gen/Player.x:F
      68: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      71: getfield      #1212               // Field mindustry/gen/Player.y:F
      74: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
      77: astore_3
      78: aload_3
      79: instanceof    #1459               // class mindustry/world/blocks/ControlBlock
      82: ifeq          108
      85: aload_3
      86: checkcast     #1459               // class mindustry/world/blocks/ControlBlock
      89: astore_2
      90: aload_2
      91: invokeinterface #1461,  1         // InterfaceMethod mindustry/world/blocks/ControlBlock.canControl:()Z
      96: ifeq          108
      99: aload_2
     100: invokeinterface #1464,  1         // InterfaceMethod mindustry/world/blocks/ControlBlock.unit:()Lmindustry/gen/Unit;
     105: goto          109
     108: aconst_null
     109: astore_1
     110: aload_1
     111: ifnull        140
     114: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
     117: invokevirtual #947                // Method mindustry/net/Net.client:()Z
     120: ifeq          133
     123: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     126: aload_1
     127: invokestatic  #1447               // Method mindustry/gen/Call.unitControl:(Lmindustry/gen/Player;Lmindustry/gen/Unit;)V
     130: goto          140
     133: aload_1
     134: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     137: invokevirtual #1262               // Method mindustry/gen/Unit.controller:(Lmindustry/entities/units/UnitController;)V
     140: return

  public void tryPickupPayload();
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
       6: astore_1
       7: aload_1
       8: instanceof    #836                // class mindustry/gen/Payloadc
      11: ifeq          22
      14: aload_1
      15: checkcast     #836                // class mindustry/gen/Payloadc
      18: astore_2
      19: goto          23
      22: return
      23: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      26: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      29: aload_2
      30: invokeinterface #990,  1          // InterfaceMethod mindustry/gen/Payloadc.x:()F
      35: aload_2
      36: invokeinterface #993,  1          // InterfaceMethod mindustry/gen/Payloadc.y:()F
      41: aload_1
      42: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
      45: getfield      #848                // Field mindustry/type/UnitType.hitSize:F
      48: fconst_2
      49: fmul
      50: aload_2
      51: aload_1
      52: invokedynamic #1465,  0           // InvokeDynamic #31:get:(Lmindustry/gen/Payloadc;Lmindustry/gen/Unit;)Larc/func/Boolf;
      57: invokestatic  #1468               // Method mindustry/entities/Units.closest:(Lmindustry/game/Team;FFFLarc/func/Boolf;)Lmindustry/gen/Unit;
      60: astore_3
      61: aload_3
      62: ifnull        75
      65: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      68: aload_3
      69: invokestatic  #1471               // Method mindustry/gen/Call.requestUnitPayload:(Lmindustry/gen/Player;Lmindustry/gen/Unit;)V
      72: goto          186
      75: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      78: aload_2
      79: invokeinterface #990,  1          // InterfaceMethod mindustry/gen/Payloadc.x:()F
      84: aload_2
      85: invokeinterface #993,  1          // InterfaceMethod mindustry/gen/Payloadc.y:()F
      90: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
      93: astore        4
      95: aload         4
      97: ifnonnull     101
     100: return
     101: aload         4
     103: invokevirtual #883                // Method mindustry/gen/Building.getPayload:()Lmindustry/world/blocks/payloads/Payload;
     106: astore        5
     108: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     111: getfield      #873                // Field mindustry/core/GameState.teams:Lmindustry/game/Teams;
     114: aload_1
     115: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
     118: aload         4
     120: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
     123: invokevirtual #878                // Method mindustry/game/Teams.canInteract:(Lmindustry/game/Team;Lmindustry/game/Team;)Z
     126: ifeq          186
     129: aload         5
     131: ifnull        145
     134: aload_2
     135: aload         5
     137: invokeinterface #887,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickupPayload:(Lmindustry/world/blocks/payloads/Payload;)Z
     142: ifne          178
     145: aload         4
     147: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     150: getfield      #895                // Field mindustry/world/Block.buildVisibility:Lmindustry/world/meta/BuildVisibility;
     153: getstatic     #899                // Field mindustry/world/meta/BuildVisibility.hidden:Lmindustry/world/meta/BuildVisibility;
     156: if_acmpeq     186
     159: aload         4
     161: invokevirtual #904                // Method mindustry/gen/Building.canPickup:()Z
     164: ifeq          186
     167: aload_2
     168: aload         4
     170: invokeinterface #906,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickup:(Lmindustry/gen/Building;)Z
     175: ifeq          186
     178: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     181: aload         4
     183: invokestatic  #1474               // Method mindustry/gen/Call.requestBuildPayload:(Lmindustry/gen/Player;Lmindustry/gen/Building;)V
     186: return

  public void tryDropPayload();
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
       6: astore_1
       7: aload_1
       8: instanceof    #836                // class mindustry/gen/Payloadc
      11: ifeq          28
      14: aload_1
      15: checkcast     #836                // class mindustry/gen/Payloadc
      18: astore_2
      19: aload_2
      20: invokeinterface #1478,  1         // InterfaceMethod mindustry/gen/Payloadc.canDropPayload:()Z
      25: ifne          29
      28: return
      29: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      32: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      35: getfield      #1211               // Field mindustry/gen/Player.x:F
      38: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      41: getfield      #1212               // Field mindustry/gen/Player.y:F
      44: invokestatic  #1481               // Method mindustry/gen/Call.requestDropPayload:(Lmindustry/gen/Player;FF)V
      47: return

  public float getMouseX();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: invokevirtual #1489               // Method arc/Input.mouseX:()I
       6: i2f
       7: freturn

  public float getMouseY();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: invokevirtual #1494               // Method arc/Input.mouseY:()I
       6: i2f
       7: freturn

  public void buildPlacementUI(arc.scene.ui.layout.Table);
    Code:
       0: return

  public void buildUI(arc.scene.Group);
    Code:
       0: return

  public void updateState();
    Code:
       0: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       3: invokevirtual #1497               // Method mindustry/core/GameState.isMenu:()Z
       6: ifeq          36
       9: aload_0
      10: aconst_null
      11: putfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
      14: aload_0
      15: iconst_0
      16: putfield      #1320               // Field logicCutscene:Z
      19: aload_0
      20: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
      23: invokevirtual #1500               // Method mindustry/ui/fragments/BlockConfigFragment.forceHide:()V
      26: aload_0
      27: aload_0
      28: iconst_0
      29: dup_x1
      30: putfield      #110                // Field commandRect:Z
      33: putfield      #107                // Field commandMode:Z
      36: return

  public boolean multiUnitSelect();
    Code:
       0: iconst_0
       1: ireturn

  public void selectUnitsRect();
    Code:
       0: aload_0
       1: getfield      #107                // Field commandMode:Z
       4: ifeq          163
       7: aload_0
       8: getfield      #110                // Field commandRect:Z
      11: ifeq          163
      14: aload_0
      15: getfield      #113                // Field tappedOne:Z
      18: ifne          158
      21: aload_0
      22: aload_0
      23: getfield      #1503               // Field commandRectX:F
      26: aload_0
      27: getfield      #1506               // Field commandRectY:F
      30: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      33: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      36: aload_0
      37: getfield      #1503               // Field commandRectX:F
      40: fsub
      41: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      44: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      47: aload_0
      48: getfield      #1506               // Field commandRectY:F
      51: fsub
      52: invokevirtual #1515               // Method selectedCommandUnits:(FFFF)Larc/struct/Seq;
      55: astore_1
      56: aload_0
      57: invokevirtual #1519               // Method multiUnitSelect:()Z
      60: ifeq          75
      63: aload_0
      64: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      67: aload_1
      68: invokevirtual #1522               // Method arc/struct/Seq.removeAll:(Larc/struct/Seq;)Z
      71: pop
      72: goto          83
      75: aload_0
      76: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      79: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      82: pop
      83: aload_0
      84: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
      87: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      90: pop
      91: aload_0
      92: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      95: aload_1
      96: invokevirtual #1525               // Method arc/struct/Seq.addAll:(Larc/struct/Seq;)Larc/struct/Seq;
      99: pop
     100: aload_0
     101: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
     104: invokevirtual #953                // Method arc/struct/Seq.isEmpty:()Z
     107: ifeq          152
     110: aload_0
     111: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     114: aload_0
     115: aload_0
     116: getfield      #1503               // Field commandRectX:F
     119: aload_0
     120: getfield      #1506               // Field commandRectY:F
     123: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     126: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
     129: aload_0
     130: getfield      #1503               // Field commandRectX:F
     133: fsub
     134: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     137: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
     140: aload_0
     141: getfield      #1506               // Field commandRectY:F
     144: fsub
     145: invokevirtual #1529               // Method selectedCommandBuildings:(FFFF)Larc/struct/Seq;
     148: invokevirtual #1525               // Method arc/struct/Seq.addAll:(Larc/struct/Seq;)Larc/struct/Seq;
     151: pop
     152: getstatic     #1532               // Field mindustry/game/EventType$Trigger.unitCommandChange:Lmindustry/game/EventType$Trigger;
     155: invokestatic  #513                // Method arc/Events.fire:(Ljava/lang/Enum;)V
     158: aload_0
     159: iconst_0
     160: putfield      #110                // Field commandRect:Z
     163: return

  public void selectTypedUnits();
    Code:
       0: aload_0
       1: getfield      #107                // Field commandMode:Z
       4: ifeq          94
       7: aload_0
       8: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      11: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      14: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      17: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      20: invokevirtual #1535               // Method selectedCommandUnit:(FF)Lmindustry/gen/Unit;
      23: astore_1
      24: aload_1
      25: ifnull        94
      28: aload_0
      29: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      32: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      35: pop
      36: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
      39: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      42: invokevirtual #1543               // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
      45: pop
      46: aload_0
      47: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      50: aload_0
      51: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      54: getfield      #1547               // Field arc/math/geom/Rect.x:F
      57: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      60: getfield      #1548               // Field arc/math/geom/Rect.y:F
      63: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      66: getfield      #1549               // Field arc/math/geom/Rect.width:F
      69: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      72: getfield      #1552               // Field arc/math/geom/Rect.height:F
      75: aload_1
      76: invokedynamic #1555,  0           // InvokeDynamic #32:get:(Lmindustry/gen/Unit;)Larc/func/Boolf;
      81: invokevirtual #1558               // Method selectedCommandUnits:(FFFFLarc/func/Boolf;)Larc/struct/Seq;
      84: invokevirtual #1525               // Method arc/struct/Seq.addAll:(Larc/struct/Seq;)Larc/struct/Seq;
      87: pop
      88: getstatic     #1532               // Field mindustry/game/EventType$Trigger.unitCommandChange:Lmindustry/game/EventType$Trigger;
      91: invokestatic  #513                // Method arc/Events.fire:(Ljava/lang/Enum;)V
      94: return

  public void tapCommandUnit();
    Code:
       0: aload_0
       1: getfield      #107                // Field commandMode:Z
       4: ifeq          171
       7: aload_0
       8: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      11: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      14: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      17: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      20: invokevirtual #1535               // Method selectedCommandUnit:(FF)Lmindustry/gen/Unit;
      23: astore_1
      24: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      27: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      30: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      33: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      36: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      39: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
      42: astore_2
      43: aload_1
      44: ifnull        90
      47: aload_0
      48: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      51: aload_1
      52: invokevirtual #684                // Method arc/struct/Seq.contains:(Ljava/lang/Object;)Z
      55: ifne          70
      58: aload_0
      59: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      62: aload_1
      63: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
      66: pop
      67: goto          79
      70: aload_0
      71: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      74: aload_1
      75: invokevirtual #1561               // Method arc/struct/Seq.remove:(Ljava/lang/Object;)Z
      78: pop
      79: aload_0
      80: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
      83: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      86: pop
      87: goto          165
      90: aload_0
      91: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      94: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      97: pop
      98: aload_2
      99: ifnull        157
     102: aload_2
     103: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
     106: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     109: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     112: if_acmpne     157
     115: aload_2
     116: invokevirtual #718                // Method mindustry/gen/Building.isCommandable:()Z
     119: ifeq          157
     122: aload_0
     123: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     126: aload_2
     127: invokevirtual #684                // Method arc/struct/Seq.contains:(Ljava/lang/Object;)Z
     130: ifeq          145
     133: aload_0
     134: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     137: aload_2
     138: invokevirtual #1561               // Method arc/struct/Seq.remove:(Ljava/lang/Object;)Z
     141: pop
     142: goto          165
     145: aload_0
     146: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     149: aload_2
     150: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
     153: pop
     154: goto          165
     157: aload_0
     158: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     161: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     164: pop
     165: getstatic     #1532               // Field mindustry/game/EventType$Trigger.unitCommandChange:Lmindustry/game/EventType$Trigger;
     168: invokestatic  #513                // Method arc/Events.fire:(Ljava/lang/Enum;)V
     171: return

  public void commandTap(float, float);
    Code:
       0: aload_0
       1: fload_1
       2: fload_2
       3: iconst_0
       4: invokevirtual #1563               // Method commandTap:(FFZ)V
       7: return

  public void commandTap(float, float, boolean);
    Code:
       0: aload_0
       1: getfield      #107                // Field commandMode:Z
       4: ifeq          346
       7: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      10: fload_1
      11: fload_2
      12: invokevirtual #1567               // Method arc/Input.mouseWorld:(FF)Larc/math/geom/Vec2;
      15: invokevirtual #1570               // Method arc/math/geom/Vec2.cpy:()Larc/math/geom/Vec2;
      18: astore        4
      20: aload_0
      21: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      24: getfield      #596                // Field arc/struct/Seq.size:I
      27: ifle          313
      30: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      33: aload         4
      35: getfield      #984                // Field arc/math/geom/Vec2.x:F
      38: aload         4
      40: getfield      #985                // Field arc/math/geom/Vec2.y:F
      43: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
      46: astore        5
      48: aload         5
      50: ifnull        69
      53: aload         5
      55: invokeinterface #556,  1          // InterfaceMethod mindustry/gen/Teamc.team:()Lmindustry/game/Team;
      60: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      63: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      66: if_acmpne     85
      69: aload_0
      70: aload         4
      72: getfield      #984                // Field arc/math/geom/Vec2.x:F
      75: aload         4
      77: getfield      #985                // Field arc/math/geom/Vec2.y:F
      80: invokevirtual #1574               // Method selectedEnemyUnit:(FF)Lmindustry/gen/Unit;
      83: astore        5
      85: aload_0
      86: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      89: getfield      #596                // Field arc/struct/Seq.size:I
      92: newarray       int
      94: astore        6
      96: iconst_0
      97: istore        7
      99: iload         7
     101: aload         6
     103: arraylength
     104: if_icmpge     133
     107: aload         6
     109: iload         7
     111: aload_0
     112: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
     115: iload         7
     117: invokevirtual #1577               // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     120: checkcast     #231                // class mindustry/gen/Unit
     123: getfield      #1008               // Field mindustry/gen/Unit.id:I
     126: iastore
     127: iinc          7, 1
     130: goto          99
     133: sipush        200
     136: istore        7
     138: aload         6
     140: arraylength
     141: iload         7
     143: if_icmple     259
     146: iconst_0
     147: istore        8
     149: iload         8
     151: aload         6
     153: arraylength
     154: if_icmpge     256
     157: aload         6
     159: iload         8
     161: iload         8
     163: iload         7
     165: iadd
     166: aload         6
     168: arraylength
     169: invokestatic  #236                // Method java/lang/Math.min:(II)I
     172: invokestatic  #1580               // Method java/util/Arrays.copyOfRange:([III)[I
     175: astore        9
     177: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     180: aload         9
     182: aload         5
     184: instanceof    #243                // class mindustry/gen/Building
     187: ifeq          202
     190: aload         5
     192: checkcast     #243                // class mindustry/gen/Building
     195: astore        10
     197: aload         10
     199: goto          203
     202: aconst_null
     203: aload         5
     205: instanceof    #231                // class mindustry/gen/Unit
     208: ifeq          223
     211: aload         5
     213: checkcast     #231                // class mindustry/gen/Unit
     216: astore        10
     218: aload         10
     220: goto          224
     223: aconst_null
     224: aload         4
     226: iload_3
     227: iload         8
     229: iload         7
     231: iadd
     232: aload         6
     234: arraylength
     235: if_icmplt     242
     238: iconst_1
     239: goto          243
     242: iconst_0
     243: invokestatic  #1584               // Method mindustry/gen/Call.commandUnits:(Lmindustry/gen/Player;[ILmindustry/gen/Building;Lmindustry/gen/Unit;Larc/math/geom/Vec2;ZZ)V
     246: iload         8
     248: iload         7
     250: iadd
     251: istore        8
     253: goto          149
     256: goto          313
     259: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     262: aload         6
     264: aload         5
     266: instanceof    #243                // class mindustry/gen/Building
     269: ifeq          284
     272: aload         5
     274: checkcast     #243                // class mindustry/gen/Building
     277: astore        8
     279: aload         8
     281: goto          285
     284: aconst_null
     285: aload         5
     287: instanceof    #231                // class mindustry/gen/Unit
     290: ifeq          305
     293: aload         5
     295: checkcast     #231                // class mindustry/gen/Unit
     298: astore        8
     300: aload         8
     302: goto          306
     305: aconst_null
     306: aload         4
     308: iload_3
     309: iconst_1
     310: invokestatic  #1584               // Method mindustry/gen/Call.commandUnits:(Lmindustry/gen/Player;[ILmindustry/gen/Building;Lmindustry/gen/Unit;Larc/math/geom/Vec2;ZZ)V
     313: aload_0
     314: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     317: getfield      #596                // Field arc/struct/Seq.size:I
     320: ifle          346
     323: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     326: aload_0
     327: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     330: invokedynamic #1587,  0           // InvokeDynamic #33:get:()Larc/func/Intf;
     335: invokevirtual #1590               // Method arc/struct/Seq.mapInt:(Larc/func/Intf;)Larc/struct/IntSeq;
     338: invokevirtual #1594               // Method arc/struct/IntSeq.toArray:()[I
     341: aload         4
     343: invokestatic  #1598               // Method mindustry/gen/Call.commandBuilding:(Lmindustry/gen/Player;[ILarc/math/geom/Vec2;)V
     346: return

  public void drawCommand(mindustry.gen.Unit);
    Code:
       0: aload_1
       1: getfield      #821                // Field mindustry/gen/Unit.x:F
       4: aload_1
       5: getfield      #823                // Field mindustry/gen/Unit.y:F
       8: bipush        6
      10: aload_1
      11: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
      14: fconst_1
      15: fdiv
      16: ldc_w         #1601               // float 4.0f
      19: fconst_1
      20: invokestatic  #1602               // Method arc/math/Mathf.absin:(FF)F
      23: fadd
      24: fconst_0
      25: aload_0
      26: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      29: aload_1
      30: invokevirtual #684                // Method arc/struct/Seq.contains:(Ljava/lang/Object;)Z
      33: ifeq          42
      36: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      39: goto          45
      42: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
      45: invokestatic  #1612               // Method mindustry/graphics/Drawf.poly:(FFIFFLarc/graphics/Color;)V
      48: return

  public void drawCommand(mindustry.gen.Building);
    Code:
       0: aload_1
       1: getfield      #1070               // Field mindustry/gen/Building.x:F
       4: aload_1
       5: getfield      #1071               // Field mindustry/gen/Building.y:F
       8: iconst_4
       9: aload_1
      10: invokevirtual #1618               // Method mindustry/gen/Building.hitSize:()F
      13: ldc_w         #1620               // float 1.4f
      16: fdiv
      17: ldc_w         #1621               // float 0.5f
      20: fadd
      21: ldc_w         #1601               // float 4.0f
      24: fconst_1
      25: invokestatic  #1602               // Method arc/math/Mathf.absin:(FF)F
      28: fadd
      29: fconst_0
      30: aload_0
      31: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
      34: aload_1
      35: invokevirtual #684                // Method arc/struct/Seq.contains:(Ljava/lang/Object;)Z
      38: ifeq          47
      41: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      44: goto          50
      47: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
      50: invokestatic  #1612               // Method mindustry/graphics/Drawf.poly:(FFIFFLarc/graphics/Color;)V
      53: return

  public void drawCommanded();
    Code:
       0: ldc_w         #1624               // float 85.0f
       3: aload_0
       4: invokedynamic #1625,  0           // InvokeDynamic #34:run:(Lmindustry/input/InputHandler;)Ljava/lang/Runnable;
       9: invokestatic  #1628               // Method arc/graphics/g2d/Draw.draw:(FLjava/lang/Runnable;)V
      12: ldc_w         #1633               // float 59.0f
      15: aload_0
      16: invokedynamic #1634,  0           // InvokeDynamic #35:run:(Lmindustry/input/InputHandler;)Ljava/lang/Runnable;
      21: invokestatic  #1628               // Method arc/graphics/g2d/Draw.draw:(FLjava/lang/Runnable;)V
      24: ldc_w         #1635               // float 120.0f
      27: aload_0
      28: invokedynamic #1636,  0           // InvokeDynamic #36:run:(Lmindustry/input/InputHandler;)Ljava/lang/Runnable;
      33: invokestatic  #1628               // Method arc/graphics/g2d/Draw.draw:(FLjava/lang/Runnable;)V
      36: return

  public void drawCommandedTargets();
    Code:
       0: aload_0
       1: getfield      #107                // Field commandMode:Z
       4: ifeq          105
       7: aload_0
       8: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      11: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
      14: astore_1
      15: aload_1
      16: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      21: ifeq          105
      24: aload_1
      25: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      30: checkcast     #231                // class mindustry/gen/Unit
      33: astore_2
      34: aload_2
      35: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
      38: astore        4
      40: aload         4
      42: instanceof    #539                // class mindustry/ai/types/CommandAI
      45: ifeq          102
      48: aload         4
      50: checkcast     #539                // class mindustry/ai/types/CommandAI
      53: astore_3
      54: aload_3
      55: invokevirtual #651                // Method mindustry/ai/types/CommandAI.currentCommand:()Lmindustry/ai/UnitCommand;
      58: astore        4
      60: aload_3
      61: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
      64: ifnull        102
      67: aload         4
      69: getfield      #1637               // Field mindustry/ai/UnitCommand.drawTarget:Z
      72: ifeq          102
      75: aload_3
      76: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
      79: invokeinterface #1640,  1         // InterfaceMethod mindustry/gen/Teamc.getX:()F
      84: aload_3
      85: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
      88: invokeinterface #1643,  1         // InterfaceMethod mindustry/gen/Teamc.getY:()F
      93: ldc_w         #1646               // float 6.0f
      96: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      99: invokestatic  #1647               // Method mindustry/graphics/Drawf.target:(FFFLarc/graphics/Color;)V
     102: goto          15
     105: return

  public void drawCommanded(boolean);
    Code:
       0: ldc_w         #1651               // float 6.5f
       3: fstore_2
       4: bipush        6
       6: istore_3
       7: ldc_w         #1621               // float 0.5f
      10: fstore        4
      12: aload_0
      13: getfield      #107                // Field commandMode:Z
      16: ifeq          1014
      19: aload_0
      20: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      23: invokedynamic #1652,  0           // InvokeDynamic #37:get:()Larc/func/Boolf;
      28: invokevirtual #1363               // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
      31: pop
      32: aload_0
      33: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
      36: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
      39: astore        5
      41: aload         5
      43: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      48: ifeq          873
      51: aload         5
      53: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      58: checkcast     #231                // class mindustry/gen/Unit
      61: astore        6
      63: aload         6
      65: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
      68: instanceof    #1653               // class mindustry/ai/types/LogicAI
      71: ifeq          83
      74: getstatic     #1655               // Field mindustry/game/Team.malis:Lmindustry/game/Team;
      77: getfield      #1658               // Field mindustry/game/Team.color:Larc/graphics/Color;
      80: goto          86
      83: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
      86: astore        7
      88: aconst_null
      89: astore        8
      91: aload         6
      93: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
      96: astore        10
      98: aload         10
     100: instanceof    #539                // class mindustry/ai/types/CommandAI
     103: ifeq          376
     106: aload         10
     108: checkcast     #539                // class mindustry/ai/types/CommandAI
     111: astore        9
     113: aload         9
     115: invokevirtual #651                // Method mindustry/ai/types/CommandAI.currentCommand:()Lmindustry/ai/UnitCommand;
     118: astore        10
     120: aload         9
     122: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
     125: ifnull        136
     128: aload         9
     130: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
     133: goto          141
     136: aload         9
     138: getfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     141: astore        8
     143: aload         6
     145: invokevirtual #1246               // Method mindustry/gen/Unit.isFlying:()Z
     148: ifne          162
     151: aload         6
     153: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     156: getfield      #1659               // Field mindustry/type/UnitType.allowLegStep:Z
     159: ifeq          166
     162: iconst_1
     163: goto          167
     166: iconst_0
     167: iload_1
     168: if_icmpeq     174
     171: goto          41
     174: aload         9
     176: getfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     179: ifnull        376
     182: aload         10
     184: getfield      #1637               // Field mindustry/ai/UnitCommand.drawTarget:Z
     187: ifeq          376
     190: aload         9
     192: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
     195: ifnull        206
     198: aload         9
     200: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
     203: goto          211
     206: aload         9
     208: getfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     211: astore        11
     213: aload         6
     215: aload         11
     217: aload         6
     219: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
     222: fconst_1
     223: fdiv
     224: fconst_1
     225: fadd
     226: fload_2
     227: aload         7
     229: getstatic     #1662               // Field arc/util/Tmp.c1:Larc/graphics/Color;
     232: invokevirtual #1665               // Method arc/graphics/Color.write:(Larc/graphics/Color;)Larc/graphics/Color;
     235: fload         4
     237: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     240: invokestatic  #1673               // Method mindustry/graphics/Drawf.limitLine:(Larc/math/geom/Position;Larc/math/geom/Position;FFLarc/graphics/Color;)V
     243: aload         9
     245: getfield      #658                // Field mindustry/ai/types/CommandAI.attackTarget:Lmindustry/gen/Teamc;
     248: ifnonnull     376
     251: aload         11
     253: invokeinterface #1677,  1         // InterfaceMethod arc/math/geom/Position.getX:()F
     258: aload         11
     260: invokeinterface #1680,  1         // InterfaceMethod arc/math/geom/Position.getY:()F
     265: ldc_w         #1681               // float 3.5f
     268: aload         7
     270: getstatic     #1662               // Field arc/util/Tmp.c1:Larc/graphics/Color;
     273: invokevirtual #1665               // Method arc/graphics/Color.write:(Larc/graphics/Color;)Larc/graphics/Color;
     276: fload         4
     278: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     281: invokestatic  #1682               // Method mindustry/graphics/Drawf.square:(FFFLarc/graphics/Color;)V
     284: aload         10
     286: getstatic     #1001               // Field mindustry/ai/UnitCommand.enterPayloadCommand:Lmindustry/ai/UnitCommand;
     289: if_acmpne     376
     292: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
     295: aload         11
     297: invokeinterface #1677,  1         // InterfaceMethod arc/math/geom/Position.getX:()F
     302: aload         11
     304: invokeinterface #1680,  1         // InterfaceMethod arc/math/geom/Position.getY:()F
     309: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
     312: astore        12
     314: aload         12
     316: ifnull        353
     319: aload         12
     321: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     324: getfield      #1685               // Field mindustry/world/Block.acceptsUnitPayloads:Z
     327: ifeq          353
     330: aload         12
     332: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
     335: aload         6
     337: getfield      #532                // Field mindustry/gen/Unit.team:Lmindustry/game/Team;
     340: if_acmpne     353
     343: aload         12
     345: aload         7
     347: invokestatic  #1688               // Method mindustry/graphics/Drawf.selected:(Lmindustry/gen/Building;Larc/graphics/Color;)V
     350: goto          376
     353: aload         11
     355: invokeinterface #1677,  1         // InterfaceMethod arc/math/geom/Position.getX:()F
     360: aload         11
     362: invokeinterface #1680,  1         // InterfaceMethod arc/math/geom/Position.getY:()F
     367: ldc_w         #1692               // float 7.0f
     370: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     373: invokestatic  #1693               // Method mindustry/graphics/Drawf.cross:(FFFLarc/graphics/Color;)V
     376: aload         6
     378: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
     381: fconst_1
     382: fdiv
     383: fconst_1
     384: fadd
     385: fstore        9
     387: aload         6
     389: getfield      #821                // Field mindustry/gen/Unit.x:F
     392: aload         6
     394: getfield      #823                // Field mindustry/gen/Unit.y:F
     397: iload_3
     398: fconst_0
     399: fload         9
     401: ldc_w         #1696               // float 0.8f
     404: fmul
     405: invokestatic  #1697               // Method java/lang/Math.max:(FF)F
     408: fload         9
     410: fconst_0
     411: getstatic     #1699               // Field arc/util/Tmp.c3:Larc/graphics/Color;
     414: aload         7
     416: invokevirtual #1702               // Method arc/graphics/Color.set:(Larc/graphics/Color;)Larc/graphics/Color;
     419: fconst_0
     420: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     423: getstatic     #1704               // Field arc/util/Tmp.c2:Larc/graphics/Color;
     426: aload         7
     428: invokevirtual #1702               // Method arc/graphics/Color.set:(Larc/graphics/Color;)Larc/graphics/Color;
     431: ldc_w         #1707               // float 0.7f
     434: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     437: invokestatic  #1708               // Method arc/graphics/g2d/Fill.lightInner:(FFIFFFLarc/graphics/Color;Larc/graphics/Color;)V
     440: fconst_1
     441: invokestatic  #1714               // Method arc/graphics/g2d/Lines.stroke:(F)V
     444: aload         7
     446: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
     449: aload         6
     451: getfield      #821                // Field mindustry/gen/Unit.x:F
     454: aload         6
     456: getfield      #823                // Field mindustry/gen/Unit.y:F
     459: iload_3
     460: fload         9
     462: ldc_w         #1621               // float 0.5f
     465: fadd
     466: invokestatic  #1722               // Method arc/graphics/g2d/Lines.poly:(FFIF)V
     469: invokestatic  #1725               // Method arc/graphics/g2d/Draw.reset:()V
     472: aload         8
     474: ifnonnull     481
     477: aload         6
     479: astore        8
     481: aload         6
     483: invokevirtual #535                // Method mindustry/gen/Unit.controller:()Lmindustry/entities/units/UnitController;
     486: astore        11
     488: aload         11
     490: instanceof    #539                // class mindustry/ai/types/CommandAI
     493: ifeq          870
     496: aload         11
     498: checkcast     #539                // class mindustry/ai/types/CommandAI
     501: astore        10
     503: aload         10
     505: invokevirtual #651                // Method mindustry/ai/types/CommandAI.currentCommand:()Lmindustry/ai/UnitCommand;
     508: getfield      #1637               // Field mindustry/ai/UnitCommand.drawTarget:Z
     511: ifeq          656
     514: aload         10
     516: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     519: getfield      #596                // Field arc/struct/Seq.size:I
     522: ifle          656
     525: aload         10
     527: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     530: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     533: astore        11
     535: aload         11
     537: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     542: ifeq          656
     545: aload         11
     547: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     552: checkcast     #1678               // class arc/math/geom/Position
     555: astore        12
     557: aload         8
     559: aload         12
     561: fload_2
     562: fload_2
     563: aload         7
     565: getstatic     #1662               // Field arc/util/Tmp.c1:Larc/graphics/Color;
     568: invokevirtual #1665               // Method arc/graphics/Color.write:(Larc/graphics/Color;)Larc/graphics/Color;
     571: fload         4
     573: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     576: invokestatic  #1673               // Method mindustry/graphics/Drawf.limitLine:(Larc/math/geom/Position;Larc/math/geom/Position;FFLarc/graphics/Color;)V
     579: aload         12
     581: astore        8
     583: aload         12
     585: instanceof    #9                  // class arc/math/geom/Vec2
     588: ifeq          630
     591: aload         12
     593: checkcast     #9                  // class arc/math/geom/Vec2
     596: astore        13
     598: aload         13
     600: getfield      #984                // Field arc/math/geom/Vec2.x:F
     603: aload         13
     605: getfield      #985                // Field arc/math/geom/Vec2.y:F
     608: ldc_w         #1681               // float 3.5f
     611: aload         7
     613: getstatic     #1662               // Field arc/util/Tmp.c1:Larc/graphics/Color;
     616: invokevirtual #1665               // Method arc/graphics/Color.write:(Larc/graphics/Color;)Larc/graphics/Color;
     619: fload         4
     621: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     624: invokestatic  #1682               // Method mindustry/graphics/Drawf.square:(FFFLarc/graphics/Color;)V
     627: goto          653
     630: aload         12
     632: invokeinterface #1677,  1         // InterfaceMethod arc/math/geom/Position.getX:()F
     637: aload         12
     639: invokeinterface #1680,  1         // InterfaceMethod arc/math/geom/Position.getY:()F
     644: ldc_w         #1646               // float 6.0f
     647: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     650: invokestatic  #1647               // Method mindustry/graphics/Drawf.target:(FFFLarc/graphics/Color;)V
     653: goto          535
     656: aload         10
     658: getfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     661: ifnull        870
     664: aload         10
     666: invokevirtual #651                // Method mindustry/ai/types/CommandAI.currentCommand:()Lmindustry/ai/UnitCommand;
     669: getstatic     #1728               // Field mindustry/ai/UnitCommand.loopPayloadCommand:Lmindustry/ai/UnitCommand;
     672: if_acmpne     870
     675: aload         6
     677: instanceof    #836                // class mindustry/gen/Payloadc
     680: ifeq          870
     683: aload         6
     685: checkcast     #836                // class mindustry/gen/Payloadc
     688: astore        11
     690: aload         7
     692: ldc_w         #1731               // float 0.4f
     695: ldc_w         #1732               // float 5.0f
     698: ldc_w         #1621               // float 0.5f
     701: invokestatic  #1602               // Method arc/math/Mathf.absin:(FF)F
     704: fadd
     705: invokestatic  #1733               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;F)V
     708: aload         11
     710: invokeinterface #1736,  1         // InterfaceMethod mindustry/gen/Payloadc.hasPayload:()Z
     715: ifeq          727
     718: getstatic     #1739               // Field mindustry/gen/Icon.download:Larc/scene/style/TextureRegionDrawable;
     721: invokevirtual #1745               // Method arc/scene/style/TextureRegionDrawable.getRegion:()Larc/graphics/g2d/TextureRegion;
     724: goto          733
     727: getstatic     #1751               // Field mindustry/gen/Icon.upload:Larc/scene/style/TextureRegionDrawable;
     730: invokevirtual #1745               // Method arc/scene/style/TextureRegionDrawable.getRegion:()Larc/graphics/g2d/TextureRegion;
     733: astore        12
     735: ldc_w         #1754               // float 11.0f
     738: fstore        13
     740: ldc_w         #1755               // float 8.0f
     743: fstore        14
     745: aload         12
     747: aload         10
     749: getfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     752: getfield      #984                // Field arc/math/geom/Vec2.x:F
     755: aload         10
     757: getfield      #655                // Field mindustry/ai/types/CommandAI.targetPos:Larc/math/geom/Vec2;
     760: getfield      #985                // Field arc/math/geom/Vec2.y:F
     763: fload         13
     765: fadd
     766: fload         14
     768: fload         14
     770: aload         12
     772: invokevirtual #1756               // Method arc/graphics/g2d/TextureRegion.ratio:()F
     775: fdiv
     776: invokestatic  #1761               // Method arc/graphics/g2d/Draw.rect:(Larc/graphics/g2d/TextureRegion;FFFF)V
     779: aload         10
     781: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     784: getfield      #596                // Field arc/struct/Seq.size:I
     787: ifle          867
     790: aload         11
     792: invokeinterface #1736,  1         // InterfaceMethod mindustry/gen/Payloadc.hasPayload:()Z
     797: ifne          809
     800: getstatic     #1739               // Field mindustry/gen/Icon.download:Larc/scene/style/TextureRegionDrawable;
     803: invokevirtual #1745               // Method arc/scene/style/TextureRegionDrawable.getRegion:()Larc/graphics/g2d/TextureRegion;
     806: goto          815
     809: getstatic     #1751               // Field mindustry/gen/Icon.upload:Larc/scene/style/TextureRegionDrawable;
     812: invokevirtual #1745               // Method arc/scene/style/TextureRegionDrawable.getRegion:()Larc/graphics/g2d/TextureRegion;
     815: astore        12
     817: aload         12
     819: aload         10
     821: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     824: invokevirtual #1765               // Method arc/struct/Seq.first:()Ljava/lang/Object;
     827: checkcast     #1678               // class arc/math/geom/Position
     830: invokeinterface #1677,  1         // InterfaceMethod arc/math/geom/Position.getX:()F
     835: aload         10
     837: getfield      #576                // Field mindustry/ai/types/CommandAI.commandQueue:Larc/struct/Seq;
     840: invokevirtual #1765               // Method arc/struct/Seq.first:()Ljava/lang/Object;
     843: checkcast     #1678               // class arc/math/geom/Position
     846: invokeinterface #1680,  1         // InterfaceMethod arc/math/geom/Position.getY:()F
     851: fload         13
     853: fadd
     854: fload         14
     856: fload         14
     858: aload         12
     860: invokevirtual #1756               // Method arc/graphics/g2d/TextureRegion.ratio:()F
     863: fdiv
     864: invokestatic  #1761               // Method arc/graphics/g2d/Draw.rect:(Larc/graphics/g2d/TextureRegion;FFFF)V
     867: invokestatic  #1766               // Method arc/graphics/g2d/Draw.color:()V
     870: goto          41
     873: iload_1
     874: ifeq          1014
     877: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
     880: astore        5
     882: aload_0
     883: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
     886: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     889: astore        6
     891: aload         6
     893: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     898: ifeq          1014
     901: aload         6
     903: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     908: checkcast     #243                // class mindustry/gen/Building
     911: astore        7
     913: aload         7
     915: ifnull        1011
     918: aload         7
     920: getfield      #1070               // Field mindustry/gen/Building.x:F
     923: aload         7
     925: getfield      #1071               // Field mindustry/gen/Building.y:F
     928: aload         7
     930: invokevirtual #1618               // Method mindustry/gen/Building.hitSize:()F
     933: ldc_w         #1620               // float 1.4f
     936: fdiv
     937: fconst_1
     938: fadd
     939: invokestatic  #1768               // Method mindustry/graphics/Drawf.square:(FFF)V
     942: aload         7
     944: invokevirtual #1770               // Method mindustry/gen/Building.getCommandPosition:()Larc/math/geom/Vec2;
     947: astore        8
     949: aload         8
     951: ifnull        1011
     954: aload         7
     956: aload         8
     958: aload         7
     960: invokevirtual #1618               // Method mindustry/gen/Building.hitSize:()F
     963: fconst_2
     964: fdiv
     965: fload_2
     966: aload         5
     968: getstatic     #1662               // Field arc/util/Tmp.c1:Larc/graphics/Color;
     971: invokevirtual #1665               // Method arc/graphics/Color.write:(Larc/graphics/Color;)Larc/graphics/Color;
     974: fload         4
     976: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
     979: invokestatic  #1673               // Method mindustry/graphics/Drawf.limitLine:(Larc/math/geom/Position;Larc/math/geom/Position;FFLarc/graphics/Color;)V
     982: aload         8
     984: getfield      #984                // Field arc/math/geom/Vec2.x:F
     987: aload         8
     989: getfield      #985                // Field arc/math/geom/Vec2.y:F
     992: ldc_w         #1681               // float 3.5f
     995: aload         5
     997: getstatic     #1662               // Field arc/util/Tmp.c1:Larc/graphics/Color;
    1000: invokevirtual #1665               // Method arc/graphics/Color.write:(Larc/graphics/Color;)Larc/graphics/Color;
    1003: fload         4
    1005: invokevirtual #1669               // Method arc/graphics/Color.a:(F)Larc/graphics/Color;
    1008: invokestatic  #1682               // Method mindustry/graphics/Drawf.square:(FFFLarc/graphics/Color;)V
    1011: goto          891
    1014: invokestatic  #1725               // Method arc/graphics/g2d/Draw.reset:()V
    1017: return

  public void drawUnitSelection();
    Code:
       0: aload_0
       1: getfield      #110                // Field commandRect:Z
       4: ifeq          193
       7: aload_0
       8: getfield      #107                // Field commandMode:Z
      11: ifeq          193
      14: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      17: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      20: fstore_1
      21: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      24: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      27: fstore_2
      28: aload_0
      29: aload_0
      30: getfield      #1503               // Field commandRectX:F
      33: aload_0
      34: getfield      #1506               // Field commandRectY:F
      37: fload_1
      38: aload_0
      39: getfield      #1503               // Field commandRectX:F
      42: fsub
      43: fload_2
      44: aload_0
      45: getfield      #1506               // Field commandRectY:F
      48: fsub
      49: invokevirtual #1515               // Method selectedCommandUnits:(FFFF)Larc/struct/Seq;
      52: astore_3
      53: aload_3
      54: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
      57: astore        4
      59: aload         4
      61: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      66: ifeq          90
      69: aload         4
      71: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      76: checkcast     #231                // class mindustry/gen/Unit
      79: astore        5
      81: aload_0
      82: aload         5
      84: invokevirtual #1773               // Method drawCommand:(Lmindustry/gen/Unit;)V
      87: goto          59
      90: aload_3
      91: invokevirtual #953                // Method arc/struct/Seq.isEmpty:()Z
      94: ifeq          161
      97: aload_0
      98: aload_0
      99: getfield      #1503               // Field commandRectX:F
     102: aload_0
     103: getfield      #1506               // Field commandRectY:F
     106: fload_1
     107: aload_0
     108: getfield      #1503               // Field commandRectX:F
     111: fsub
     112: fload_2
     113: aload_0
     114: getfield      #1506               // Field commandRectY:F
     117: fsub
     118: invokevirtual #1529               // Method selectedCommandBuildings:(FFFF)Larc/struct/Seq;
     121: astore        4
     123: aload         4
     125: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     128: astore        5
     130: aload         5
     132: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     137: ifeq          161
     140: aload         5
     142: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     147: checkcast     #243                // class mindustry/gen/Building
     150: astore        6
     152: aload_0
     153: aload         6
     155: invokevirtual #1776               // Method drawCommand:(Lmindustry/gen/Building;)V
     158: goto          130
     161: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
     164: ldc_w         #1778               // float 0.3f
     167: invokestatic  #1733               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;F)V
     170: aload_0
     171: getfield      #1503               // Field commandRectX:F
     174: aload_0
     175: getfield      #1506               // Field commandRectY:F
     178: fload_1
     179: aload_0
     180: getfield      #1503               // Field commandRectX:F
     183: fsub
     184: fload_2
     185: aload_0
     186: getfield      #1506               // Field commandRectY:F
     189: fsub
     190: invokestatic  #1779               // Method arc/graphics/g2d/Fill.crect:(FFFF)V
     193: aload_0
     194: getfield      #107                // Field commandMode:Z
     197: ifeq          262
     200: aload_0
     201: getfield      #110                // Field commandRect:Z
     204: ifne          262
     207: aload_0
     208: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     211: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
     214: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     217: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
     220: invokevirtual #1535               // Method selectedCommandUnit:(FF)Lmindustry/gen/Unit;
     223: astore_1
     224: aload_1
     225: ifnull        262
     228: aload_0
     229: invokevirtual #1519               // Method multiUnitSelect:()Z
     232: ifne          257
     235: aload_0
     236: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
     239: getfield      #596                // Field arc/struct/Seq.size:I
     242: iconst_1
     243: if_icmpne     257
     246: aload_0
     247: getfield      #98                 // Field selectedUnits:Larc/struct/Seq;
     250: aload_1
     251: invokevirtual #684                // Method arc/struct/Seq.contains:(Ljava/lang/Object;)Z
     254: ifne          262
     257: aload_0
     258: aload_1
     259: invokevirtual #1773               // Method drawCommand:(Lmindustry/gen/Unit;)V
     262: return

  public void drawOtherBuildPlans();
    Code:
       0: getstatic     #1782               // Field arc/util/Tmp.v3:Larc/math/geom/Vec2;
       3: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       6: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
       9: invokevirtual #1787               // Method arc/math/geom/Vec2.set:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
      12: pop
      13: aload_0
      14: aconst_null
      15: putfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
      18: aload_0
      19: aconst_null
      20: putfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
      23: getstatic     #1790               // Field mindustry/gen/Groups.player:Lmindustry/entities/EntityGroup;
      26: aload_0
      27: invokedynamic #1792,  0           // InvokeDynamic #38:get:(Lmindustry/input/InputHandler;)Larc/func/Cons;
      32: invokevirtual #1793               // Method mindustry/entities/EntityGroup.each:(Larc/func/Cons;)V
      35: aload_0
      36: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
      39: ifnull        174
      42: aload_0
      43: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
      46: invokevirtual #1794               // Method mindustry/entities/units/BuildPlan.drawx:()F
      49: aload_0
      50: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
      53: invokevirtual #1797               // Method mindustry/entities/units/BuildPlan.drawy:()F
      56: aload_0
      57: getfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
      60: getfield      #1211               // Field mindustry/gen/Player.x:F
      63: aload_0
      64: getfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
      67: getfield      #1212               // Field mindustry/gen/Player.y:F
      70: aload_0
      71: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
      74: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      77: getfield      #860                // Field mindustry/world/Block.size:I
      80: bipush        8
      82: imul
      83: i2f
      84: ldc_w         #1801               // float 0.6f
      87: fmul
      88: ldc_w         #1601               // float 4.0f
      91: fadd
      92: fconst_2
      93: aload_0
      94: getfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
      97: getfield      #1802               // Field mindustry/gen/Player.color:Larc/graphics/Color;
     100: invokestatic  #1803               // Method mindustry/graphics/Drawf.arrow:(FFFFFFLarc/graphics/Color;)V
     103: aload_0
     104: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     107: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     110: aload_0
     111: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     114: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     117: aload_0
     118: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     121: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     124: aload_0
     125: getfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
     128: getfield      #1802               // Field mindustry/gen/Player.color:Larc/graphics/Color;
     131: invokestatic  #1811               // Method mindustry/graphics/Drawf.selected:(IILmindustry/world/Block;Larc/graphics/Color;)V
     134: aload_0
     135: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     138: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     141: aload_0
     142: getfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
     145: getfield      #1814               // Field mindustry/gen/Player.name:Ljava/lang/String;
     148: aload_0
     149: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     152: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     155: aload_0
     156: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     159: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     162: aload_0
     163: getfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
     166: getfield      #1802               // Field mindustry/gen/Player.color:Larc/graphics/Color;
     169: iconst_0
     170: invokevirtual #1817               // Method mindustry/world/Block.drawPlaceText:(Ljava/lang/String;IILarc/graphics/Color;Z)F
     173: pop
     174: return

  public void drawBuildPlans();
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #1367               // Method mindustry/gen/Player.isBuilder:()Z
       6: ifne          10
       9: return
      10: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      13: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      16: astore_1
      17: aload_1
      18: invokevirtual #1821               // Method mindustry/gen/Unit.buildPlan:()Lmindustry/entities/units/BuildPlan;
      21: astore_2
      22: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
      25: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      28: invokevirtual #1543               // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
      31: pop
      32: aload_0
      33: getfield      #126                // Field plansOut:Larc/struct/Seq;
      36: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      39: pop
      40: aload_0
      41: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      44: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      47: aload_0
      48: getfield      #126                // Field plansOut:Larc/struct/Seq;
      51: invokevirtual #1825               // Method arc/math/geom/QuadTree.intersect:(Larc/math/geom/Rect;Larc/struct/Seq;)V
      54: aload_0
      55: getfield      #126                // Field plansOut:Larc/struct/Seq;
      58: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
      61: astore_3
      62: aload_3
      63: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      68: ifeq          239
      71: aload_3
      72: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      77: checkcast     #74                 // class mindustry/entities/units/BuildPlan
      80: astore        4
      82: aload         4
      84: getfield      #1829               // Field mindustry/entities/units/BuildPlan.progress:F
      87: ldc_w         #1832               // float 0.01f
      90: fcmpl
      91: ifgt          62
      94: aload_2
      95: aload         4
      97: if_acmpne     152
     100: aload         4
     102: getfield      #1833               // Field mindustry/entities/units/BuildPlan.initialized:Z
     105: ifeq          152
     108: aload_1
     109: aload         4
     111: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     114: bipush        8
     116: imul
     117: i2f
     118: aload         4
     120: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     123: bipush        8
     125: imul
     126: i2f
     127: aload_1
     128: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     131: getfield      #1836               // Field mindustry/type/UnitType.buildRange:F
     134: invokevirtual #1839               // Method mindustry/gen/Unit.within:(FFF)Z
     137: ifne          62
     140: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     143: invokevirtual #1842               // Method mindustry/core/GameState.isEditor:()Z
     146: ifeq          152
     149: goto          62
     152: aload         4
     154: fconst_1
     155: putfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
     158: aload         4
     160: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     163: ifeq          175
     166: aload_0
     167: aload         4
     169: invokevirtual #1848               // Method drawBreaking:(Lmindustry/entities/units/BuildPlan;)V
     172: goto          236
     175: aload         4
     177: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     180: aload         4
     182: aload_0
     183: getfield      #1281               // Field allPlans:Larc/util/Eachable;
     186: aload         4
     188: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     191: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     194: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     197: aload         4
     199: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     202: aload         4
     204: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     207: aload         4
     209: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
     212: invokestatic  #1853               // Method mindustry/world/Build.validPlace:(Lmindustry/world/Block;Lmindustry/game/Team;III)Z
     215: ifne          227
     218: aload_0
     219: aload         4
     221: invokevirtual #1859               // Method planMatches:(Lmindustry/entities/units/BuildPlan;)Z
     224: ifeq          231
     227: iconst_1
     228: goto          232
     231: iconst_0
     232: fconst_1
     233: invokevirtual #1863               // Method mindustry/world/Block.drawPlan:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;ZF)V
     236: goto          62
     239: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
     242: getstatic     #1867               // Field arc/util/Tmp.r3:Larc/math/geom/Rect;
     245: invokevirtual #1543               // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
     248: pop
     249: invokestatic  #1725               // Method arc/graphics/g2d/Draw.reset:()V
     252: aload_1
     253: getfield      #1370               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
     256: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     259: astore_3
     260: aload_3
     261: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     266: ifeq          433
     269: aload_3
     270: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     275: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     278: astore        4
     280: aload         4
     282: getfield      #1829               // Field mindustry/entities/units/BuildPlan.progress:F
     285: ldc_w         #1832               // float 0.01f
     288: fcmpl
     289: ifgt          260
     292: aload         4
     294: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     297: ifne          260
     300: aload_2
     301: aload         4
     303: if_acmpne     358
     306: aload         4
     308: getfield      #1833               // Field mindustry/entities/units/BuildPlan.initialized:Z
     311: ifeq          358
     314: aload_1
     315: aload         4
     317: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     320: bipush        8
     322: imul
     323: i2f
     324: aload         4
     326: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     329: bipush        8
     331: imul
     332: i2f
     333: aload_1
     334: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
     337: getfield      #1836               // Field mindustry/type/UnitType.buildRange:F
     340: invokevirtual #1839               // Method mindustry/gen/Unit.within:(FFF)Z
     343: ifne          260
     346: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     349: invokevirtual #1842               // Method mindustry/core/GameState.isEditor:()Z
     352: ifeq          358
     355: goto          260
     358: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     361: aload         4
     363: invokevirtual #1794               // Method mindustry/entities/units/BuildPlan.drawx:()F
     366: aload         4
     368: invokevirtual #1797               // Method mindustry/entities/units/BuildPlan.drawy:()F
     371: aload         4
     373: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     376: invokevirtual #1873               // Method mindustry/world/Block.planConfigClipSize:()F
     379: invokevirtual #1876               // Method arc/math/geom/Rect.setCentered:(FFF)Larc/math/geom/Rect;
     382: getstatic     #1867               // Field arc/util/Tmp.r3:Larc/math/geom/Rect;
     385: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     388: ifeq          430
     391: getstatic     #1037               // Field arc/graphics/Color.white:Larc/graphics/Color;
     394: ldc_w         #1884               // float 0.24f
     397: getstatic     #1885               // Field arc/util/Time.globalTime:F
     400: ldc_w         #1646               // float 6.0f
     403: ldc_w         #1888               // float 0.28f
     406: invokestatic  #1889               // Method arc/math/Mathf.absin:(FFF)F
     409: fadd
     410: invokestatic  #1892               // Method arc/graphics/g2d/Draw.mixcol:(Larc/graphics/Color;F)V
     413: aload         4
     415: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     418: aload         4
     420: aload_0
     421: getfield      #1293               // Field allRenderPlansConfig:Larc/util/Eachable;
     424: invokevirtual #1895               // Method mindustry/world/Block.drawPlanConfigTop:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;)V
     427: invokestatic  #1725               // Method arc/graphics/g2d/Draw.reset:()V
     430: goto          260
     433: return

  public void drawBottom();
    Code:
       0: return

  public void drawTop();
    Code:
       0: return

  public void drawOverSelect();
    Code:
       0: return

  public void drawSelected(int, int, mindustry.world.Block, arc.graphics.Color);
    Code:
       0: iload_1
       1: iload_2
       2: aload_3
       3: aload         4
       5: invokestatic  #1811               // Method mindustry/graphics/Drawf.selected:(IILmindustry/world/Block;Larc/graphics/Color;)V
       8: return

  public void drawBreaking(mindustry.entities.units.BuildPlan);
    Code:
       0: aload_1
       1: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
       4: ifeq          22
       7: aload_0
       8: aload_1
       9: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      12: aload_1
      13: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      16: invokevirtual #1899               // Method drawBreaking:(II)V
      19: goto          41
      22: aload_0
      23: aload_1
      24: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      27: aload_1
      28: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      31: aload_1
      32: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      35: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      38: invokevirtual #1902               // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
      41: return

  public void drawOverlapCheck(mindustry.world.Block, int, int, boolean);
    Code:
       0: iload         4
       2: ifne          215
       5: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
       8: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
      11: getfield      #1905               // Field mindustry/game/Rules.placeRangeCheck:Z
      14: ifeq          215
      17: aload_1
      18: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      21: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      24: iload_2
      25: iload_3
      26: invokestatic  #1908               // Method mindustry/world/Build.getEnemyOverlap:(Lmindustry/world/Block;Lmindustry/game/Team;II)Lmindustry/gen/Building;
      29: astore        5
      31: aload         5
      33: ifnull        215
      36: aload         5
      38: getfield      #1912               // Field mindustry/gen/Building.wasVisible:Z
      41: ifeq          215
      44: aload         5
      46: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      49: invokestatic  #1688               // Method mindustry/graphics/Drawf.selected:(Lmindustry/gen/Building;Larc/graphics/Color;)V
      52: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
      55: iload_2
      56: i2f
      57: iload_3
      58: i2f
      59: invokevirtual #971                // Method arc/math/geom/Vec2.set:(FF)Larc/math/geom/Vec2;
      62: ldc_w         #1755               // float 8.0f
      65: invokevirtual #1915               // Method arc/math/geom/Vec2.scl:(F)Larc/math/geom/Vec2;
      68: aload_1
      69: getfield      #1918               // Field mindustry/world/Block.offset:F
      72: aload_1
      73: getfield      #1918               // Field mindustry/world/Block.offset:F
      76: invokevirtual #1921               // Method arc/math/geom/Vec2.add:(FF)Larc/math/geom/Vec2;
      79: aload         5
      81: invokevirtual #974                // Method arc/math/geom/Vec2.sub:(Larc/math/geom/Position;)Larc/math/geom/Vec2;
      84: ldc           #23                 // float -1.0f
      86: invokevirtual #1915               // Method arc/math/geom/Vec2.scl:(F)Larc/math/geom/Vec2;
      89: invokevirtual #1923               // Method arc/math/geom/Vec2.nor:()Larc/math/geom/Vec2;
      92: pop
      93: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      96: iload_2
      97: bipush        8
      99: imul
     100: i2f
     101: aload_1
     102: getfield      #1918               // Field mindustry/world/Block.offset:F
     105: fadd
     106: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     109: getfield      #984                // Field arc/math/geom/Vec2.x:F
     112: aload_1
     113: getfield      #860                // Field mindustry/world/Block.size:I
     116: i2f
     117: fmul
     118: ldc_w         #1755               // float 8.0f
     121: fmul
     122: fconst_2
     123: fdiv
     124: fadd
     125: iload_3
     126: bipush        8
     128: imul
     129: i2f
     130: aload_1
     131: getfield      #1918               // Field mindustry/world/Block.offset:F
     134: fadd
     135: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     138: getfield      #985                // Field arc/math/geom/Vec2.y:F
     141: aload_1
     142: getfield      #860                // Field mindustry/world/Block.size:I
     145: i2f
     146: fmul
     147: ldc_w         #1755               // float 8.0f
     150: fmul
     151: fconst_2
     152: fdiv
     153: fadd
     154: aload         5
     156: getfield      #1070               // Field mindustry/gen/Building.x:F
     159: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     162: getfield      #984                // Field arc/math/geom/Vec2.x:F
     165: aload         5
     167: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     170: getfield      #860                // Field mindustry/world/Block.size:I
     173: ineg
     174: i2f
     175: fmul
     176: ldc_w         #1755               // float 8.0f
     179: fmul
     180: fconst_2
     181: fdiv
     182: fadd
     183: aload         5
     185: getfield      #1071               // Field mindustry/gen/Building.y:F
     188: getstatic     #966                // Field arc/util/Tmp.v1:Larc/math/geom/Vec2;
     191: getfield      #985                // Field arc/math/geom/Vec2.y:F
     194: aload         5
     196: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     199: getfield      #860                // Field mindustry/world/Block.size:I
     202: ineg
     203: i2f
     204: fmul
     205: ldc_w         #1755               // float 8.0f
     208: fmul
     209: fconst_2
     210: fdiv
     211: fadd
     212: invokestatic  #1926               // Method mindustry/graphics/Drawf.dashLineDst:(Larc/graphics/Color;FFFF)V
     215: return

  public boolean planMatches(mindustry.entities.units.BuildPlan);
    Code:
       0: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
       3: aload_1
       4: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
       7: aload_1
       8: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      11: invokevirtual #1930               // Method mindustry/core/World.tile:(II)Lmindustry/world/Tile;
      14: astore_2
      15: aload_2
      16: ifnull        54
      19: aload_2
      20: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      23: astore        4
      25: aload         4
      27: instanceof    #1934               // class mindustry/world/blocks/ConstructBlock$ConstructBuild
      30: ifeq          54
      33: aload         4
      35: checkcast     #1934               // class mindustry/world/blocks/ConstructBlock$ConstructBuild
      38: astore_3
      39: aload_3
      40: getfield      #1936               // Field mindustry/world/blocks/ConstructBlock$ConstructBuild.current:Lmindustry/world/Block;
      43: aload_1
      44: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      47: if_acmpne     54
      50: iconst_1
      51: goto          55
      54: iconst_0
      55: ireturn

  public void drawBreaking(int, int);
    Code:
       0: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
       3: iload_1
       4: iload_2
       5: invokevirtual #1930               // Method mindustry/core/World.tile:(II)Lmindustry/world/Tile;
       8: astore_3
       9: aload_3
      10: ifnonnull     14
      13: return
      14: aload_3
      15: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
      18: astore        4
      20: aload_0
      21: iload_1
      22: iload_2
      23: aload         4
      25: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
      28: invokevirtual #1902               // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
      31: return

  public void useSchematic(mindustry.game.Schematic);
    Code:
       0: aload_0
       1: aload_1
       2: iconst_1
       3: invokevirtual #1942               // Method useSchematic:(Lmindustry/game/Schematic;Z)V
       6: return

  public abstract void useSchematic(mindustry.game.Schematic, boolean);

  protected void showSchematicSave();
    Code:
       0: aload_0
       1: getfield      #1946               // Field lastSchematic:Lmindustry/game/Schematic;
       4: ifnonnull     8
       7: return
       8: aload_0
       9: getfield      #1946               // Field lastSchematic:Lmindustry/game/Schematic;
      12: astore_1
      13: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
      16: ldc_w         #1950               // String @schematic.add
      19: ldc_w         #1952               // String @name
      22: sipush        1000
      25: ldc_w         #1954               // String
      28: aload_1
      29: invokedynamic #1956,  0           // InvokeDynamic #39:get:(Lmindustry/game/Schematic;)Larc/func/Cons;
      34: invokevirtual #1959               // Method mindustry/core/UI.showTextInput:(Ljava/lang/String;Ljava/lang/String;ILjava/lang/String;Larc/func/Cons;)V
      37: return

  public void rotatePlans(arc.struct.Seq<mindustry.entities.units.BuildPlan>, int);
    Code:
       0: aload_0
       1: invokevirtual #1963               // Method schemOriginX:()I
       4: istore_3
       5: aload_0
       6: invokevirtual #1966               // Method schemOriginY:()I
       9: istore        4
      11: aload_1
      12: iload_2
      13: iload_3
      14: iload         4
      16: invokedynamic #1969,  0           // InvokeDynamic #40:get:(III)Larc/func/Cons;
      21: invokevirtual #1972               // Method arc/struct/Seq.each:(Larc/func/Cons;)V
      24: return

  public void flipPlans(arc.struct.Seq<mindustry.entities.units.BuildPlan>, boolean);
    Code:
       0: iload_2
       1: ifeq          11
       4: aload_0
       5: invokevirtual #1963               // Method schemOriginX:()I
       8: goto          15
      11: aload_0
      12: invokevirtual #1966               // Method schemOriginY:()I
      15: bipush        8
      17: imul
      18: istore_3
      19: aload_1
      20: iload_2
      21: iload_3
      22: invokedynamic #1973,  0           // InvokeDynamic #41:get:(ZI)Larc/func/Cons;
      27: invokevirtual #1972               // Method arc/struct/Seq.each:(Larc/func/Cons;)V
      30: return

  protected int schemOriginX();
    Code:
       0: aload_0
       1: invokevirtual #1976               // Method rawTileX:()I
       4: ireturn

  protected int schemOriginY();
    Code:
       0: aload_0
       1: invokevirtual #1979               // Method rawTileY:()I
       4: ireturn

  protected mindustry.entities.units.BuildPlan getPlan(int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iconst_1
       4: aconst_null
       5: invokevirtual #1982               // Method getPlan:(IIILmindustry/entities/units/BuildPlan;)Lmindustry/entities/units/BuildPlan;
       8: areturn

  protected mindustry.entities.units.BuildPlan getPlan(int, int, int, mindustry.entities.units.BuildPlan);
    Code:
       0: iload_3
       1: iconst_1
       2: iadd
       3: iconst_2
       4: irem
       5: bipush        8
       7: imul
       8: i2f
       9: fconst_2
      10: fdiv
      11: fstore        5
      13: getstatic     #1986               // Field r2:Larc/math/geom/Rect;
      16: bipush        8
      18: iload_3
      19: imul
      20: i2f
      21: invokevirtual #1987               // Method arc/math/geom/Rect.setSize:(F)Larc/math/geom/Rect;
      24: pop
      25: getstatic     #1986               // Field r2:Larc/math/geom/Rect;
      28: iload_1
      29: bipush        8
      31: imul
      32: i2f
      33: fload         5
      35: fadd
      36: iload_2
      37: bipush        8
      39: imul
      40: i2f
      41: fload         5
      43: fadd
      44: invokevirtual #1991               // Method arc/math/geom/Rect.setCenter:(FF)Larc/math/geom/Rect;
      47: pop
      48: aload_0
      49: aconst_null
      50: putfield      #1995               // Field resultplan:Lmindustry/entities/units/BuildPlan;
      53: aload         4
      55: invokedynamic #1998,  0           // InvokeDynamic #42:get:(Lmindustry/entities/units/BuildPlan;)Larc/func/Boolf;
      60: astore        6
      62: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      65: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      68: ifne          125
      71: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      74: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      77: invokevirtual #2001               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
      80: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
      83: astore        7
      85: aload         7
      87: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      92: ifeq          125
      95: aload         7
      97: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     102: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     105: astore        8
     107: aload         6
     109: aload         8
     111: invokeinterface #2004,  2         // InterfaceMethod arc/func/Boolf.get:(Ljava/lang/Object;)Z
     116: ifeq          122
     119: aload         8
     121: areturn
     122: goto          85
     125: aload_0
     126: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     129: aload         6
     131: invokevirtual #2008               // Method arc/struct/Seq.find:(Larc/func/Boolf;)Ljava/lang/Object;
     134: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     137: areturn

  protected void drawBreakSelection(int, int, int, int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: iload         5
       8: iconst_1
       9: invokevirtual #2012               // Method drawBreakSelection:(IIIIIZ)V
      12: return

  protected void drawBreakSelection(int, int, int, int, int, boolean);
    Code:
       0: getstatic     #2016               // Field mindustry/content/Blocks.air:Lmindustry/world/Block;
       3: iload_1
       4: iload_2
       5: iload_3
       6: iload         4
       8: iconst_0
       9: iload         5
      11: fconst_1
      12: invokestatic  #2021               // Method mindustry/input/Placement.normalizeDrawArea:(Lmindustry/world/Block;IIIIZIF)Lmindustry/input/Placement$NormalizeDrawResult;
      15: astore        7
      17: iload_1
      18: iload_2
      19: iload_3
      20: iload         4
      22: aload_0
      23: getfield      #53                 // Field rotation:I
      26: iconst_0
      27: iload         5
      29: invokestatic  #2027               // Method mindustry/input/Placement.normalizeArea:(IIIIIZI)Lmindustry/input/Placement$NormalizeResult;
      32: astore        8
      34: aload         8
      36: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
      39: istore        9
      41: iload         9
      43: aload         8
      45: getfield      #2034               // Field mindustry/input/Placement$NormalizeResult.x2:I
      48: if_icmpgt     131
      51: aload         8
      53: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
      56: istore        10
      58: iload         10
      60: aload         8
      62: getfield      #2038               // Field mindustry/input/Placement$NormalizeResult.y2:I
      65: if_icmpgt     125
      68: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      71: iload         9
      73: iload         10
      75: invokevirtual #2041               // Method mindustry/core/World.tileBuilding:(II)Lmindustry/world/Tile;
      78: astore        11
      80: aload         11
      82: ifnull        119
      85: aload_0
      86: aload         11
      88: getfield      #2044               // Field mindustry/world/Tile.x:S
      91: aload         11
      93: getfield      #2045               // Field mindustry/world/Tile.y:S
      96: invokevirtual #2046               // Method validBreak:(II)Z
      99: ifne          105
     102: goto          119
     105: aload_0
     106: aload         11
     108: getfield      #2044               // Field mindustry/world/Tile.x:S
     111: aload         11
     113: getfield      #2045               // Field mindustry/world/Tile.y:S
     116: invokevirtual #1899               // Method drawBreaking:(II)V
     119: iinc          10, 1
     122: goto          58
     125: iinc          9, 1
     128: goto          41
     131: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     134: aload         7
     136: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     139: aload         7
     141: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     144: aload         7
     146: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
     149: aload         7
     151: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     154: fsub
     155: aload         7
     157: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
     160: aload         7
     162: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     165: fsub
     166: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
     169: pop
     170: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     173: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
     176: fconst_1
     177: invokestatic  #1714               // Method arc/graphics/g2d/Lines.stroke:(F)V
     180: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     183: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     186: ifne          259
     189: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     192: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     195: invokevirtual #2001               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
     198: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     201: astore        9
     203: aload         9
     205: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     210: ifeq          259
     213: aload         9
     215: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     220: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     223: astore        10
     225: aload         10
     227: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     230: ifne          256
     233: aload         10
     235: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     238: invokevirtual #2061               // Method mindustry/entities/units/BuildPlan.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
     241: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     244: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     247: ifeq          256
     250: aload_0
     251: aload         10
     253: invokevirtual #1848               // Method drawBreaking:(Lmindustry/entities/units/BuildPlan;)V
     256: goto          203
     259: iload         6
     261: ifeq          329
     264: aload_0
     265: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     268: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     271: astore        9
     273: aload         9
     275: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     280: ifeq          329
     283: aload         9
     285: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     290: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     293: astore        10
     295: aload         10
     297: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     300: ifne          326
     303: aload         10
     305: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     308: invokevirtual #2061               // Method mindustry/entities/units/BuildPlan.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
     311: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     314: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     317: ifeq          326
     320: aload_0
     321: aload         10
     323: invokevirtual #1848               // Method drawBreaking:(Lmindustry/entities/units/BuildPlan;)V
     326: goto          273
     329: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     332: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     335: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
     338: getfield      #385                // Field mindustry/game/Teams$TeamData.plans:Larc/struct/Queue;
     341: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     344: astore        9
     346: aload         9
     348: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     353: ifeq          427
     356: aload         9
     358: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     363: checkcast     #403                // class mindustry/game/Teams$BlockPlan
     366: astore        10
     368: aload         10
     370: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     373: astore        11
     375: aload         11
     377: aload         10
     379: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     382: aload         10
     384: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     387: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     390: invokevirtual #2063               // Method mindustry/world/Block.bounds:(IILarc/math/geom/Rect;)Larc/math/geom/Rect;
     393: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     396: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     399: ifeq          424
     402: aload_0
     403: aload         10
     405: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     408: aload         10
     410: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     413: aload         10
     415: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     418: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     421: invokevirtual #1902               // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
     424: goto          346
     427: fconst_2
     428: invokestatic  #1714               // Method arc/graphics/g2d/Lines.stroke:(F)V
     431: getstatic     #2066               // Field mindustry/graphics/Pal.removeBack:Larc/graphics/Color;
     434: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
     437: aload         7
     439: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     442: aload         7
     444: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     447: fconst_1
     448: fsub
     449: aload         7
     451: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
     454: aload         7
     456: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     459: fsub
     460: aload         7
     462: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
     465: aload         7
     467: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     470: fsub
     471: invokestatic  #2069               // Method arc/graphics/g2d/Lines.rect:(FFFF)V
     474: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     477: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
     480: aload         7
     482: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     485: aload         7
     487: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     490: aload         7
     492: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
     495: aload         7
     497: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     500: fsub
     501: aload         7
     503: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
     506: aload         7
     508: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     511: fsub
     512: invokestatic  #2069               // Method arc/graphics/g2d/Lines.rect:(FFFF)V
     515: return

  protected void drawRebuildSelection(int, int, int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: iconst_0
       7: getstatic     #2071               // Field mindustry/graphics/Pal.sapBulletBack:Larc/graphics/Color;
      10: getstatic     #2074               // Field mindustry/graphics/Pal.sapBullet:Larc/graphics/Color;
      13: iconst_0
      14: invokevirtual #2077               // Method drawSelection:(IIIIILarc/graphics/Color;Larc/graphics/Color;Z)V
      17: getstatic     #2016               // Field mindustry/content/Blocks.air:Lmindustry/world/Block;
      20: iload_1
      21: iload_2
      22: iload_3
      23: iload         4
      25: iconst_0
      26: iconst_0
      27: fconst_1
      28: invokestatic  #2021               // Method mindustry/input/Placement.normalizeDrawArea:(Lmindustry/world/Block;IIIIZIF)Lmindustry/input/Placement$NormalizeDrawResult;
      31: astore        5
      33: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      36: aload         5
      38: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
      41: aload         5
      43: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
      46: aload         5
      48: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
      51: aload         5
      53: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
      56: fsub
      57: aload         5
      59: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
      62: aload         5
      64: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
      67: fsub
      68: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
      71: pop
      72: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      75: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      78: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
      81: getfield      #385                // Field mindustry/game/Teams$TeamData.plans:Larc/struct/Queue;
      84: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
      87: astore        6
      89: aload         6
      91: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      96: ifeq          170
      99: aload         6
     101: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     106: checkcast     #403                // class mindustry/game/Teams$BlockPlan
     109: astore        7
     111: aload         7
     113: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     116: astore        8
     118: aload         8
     120: aload         7
     122: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     125: aload         7
     127: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     130: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     133: invokevirtual #2063               // Method mindustry/world/Block.bounds:(IILarc/math/geom/Rect;)Larc/math/geom/Rect;
     136: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     139: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     142: ifeq          167
     145: aload_0
     146: aload         7
     148: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     151: aload         7
     153: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     156: aload         7
     158: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     161: getstatic     #2074               // Field mindustry/graphics/Pal.sapBullet:Larc/graphics/Color;
     164: invokevirtual #1902               // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
     167: goto          89
     170: iload_1
     171: iload_2
     172: iload_3
     173: iload         4
     175: aload_0
     176: getfield      #53                 // Field rotation:I
     179: iconst_0
     180: ldc_w         #2081               // int 999999999
     183: invokestatic  #2027               // Method mindustry/input/Placement.normalizeArea:(IIIIIZI)Lmindustry/input/Placement$NormalizeResult;
     186: astore        6
     188: getstatic     #2082               // Field intSet:Larc/struct/IntSet;
     191: invokevirtual #2086               // Method arc/struct/IntSet.clear:()V
     194: aload         6
     196: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
     199: istore        7
     201: iload         7
     203: aload         6
     205: getfield      #2034               // Field mindustry/input/Placement$NormalizeResult.x2:I
     208: if_icmpgt     302
     211: aload         6
     213: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
     216: istore        8
     218: iload         8
     220: aload         6
     222: getfield      #2038               // Field mindustry/input/Placement$NormalizeResult.y2:I
     225: if_icmpgt     296
     228: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
     231: iload         7
     233: iload         8
     235: invokevirtual #2041               // Method mindustry/core/World.tileBuilding:(II)Lmindustry/world/Tile;
     238: astore        9
     240: aload         9
     242: ifnull        290
     245: getstatic     #2082               // Field intSet:Larc/struct/IntSet;
     248: aload         9
     250: invokevirtual #2089               // Method mindustry/world/Tile.pos:()I
     253: invokevirtual #2092               // Method arc/struct/IntSet.add:(I)Z
     256: ifeq          290
     259: aload_0
     260: aload         9
     262: invokevirtual #2095               // Method canRepairDerelict:(Lmindustry/world/Tile;)Z
     265: ifeq          290
     268: aload_0
     269: aload         9
     271: getfield      #2044               // Field mindustry/world/Tile.x:S
     274: aload         9
     276: getfield      #2045               // Field mindustry/world/Tile.y:S
     279: aload         9
     281: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
     284: getstatic     #2074               // Field mindustry/graphics/Pal.sapBullet:Larc/graphics/Color;
     287: invokevirtual #1902               // Method drawSelected:(IILmindustry/world/Block;Larc/graphics/Color;)V
     290: iinc          8, 1
     293: goto          218
     296: iinc          7, 1
     299: goto          201
     302: return

  protected void drawBreakSelection(int, int, int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: bipush        100
       8: invokevirtual #2099               // Method drawBreakSelection:(IIIII)V
      11: return

  protected void drawSelection(int, int, int, int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: iload         5
       8: getstatic     #2102               // Field mindustry/graphics/Pal.accentBack:Larc/graphics/Color;
      11: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
      14: iconst_1
      15: invokevirtual #2077               // Method drawSelection:(IIIIILarc/graphics/Color;Larc/graphics/Color;Z)V
      18: return

  protected void drawSelection(int, int, int, int, int, arc.graphics.Color, arc.graphics.Color, boolean);
    Code:
       0: getstatic     #2016               // Field mindustry/content/Blocks.air:Lmindustry/world/Block;
       3: iload_1
       4: iload_2
       5: iload_3
       6: iload         4
       8: iconst_0
       9: iload         5
      11: fconst_1
      12: invokestatic  #2021               // Method mindustry/input/Placement.normalizeDrawArea:(Lmindustry/world/Block;IIIIZIF)Lmindustry/input/Placement$NormalizeDrawResult;
      15: astore        9
      17: fconst_2
      18: invokestatic  #1714               // Method arc/graphics/g2d/Lines.stroke:(F)V
      21: aload         6
      23: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
      26: aload         9
      28: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
      31: aload         9
      33: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
      36: fconst_1
      37: fsub
      38: aload         9
      40: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
      43: aload         9
      45: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
      48: fsub
      49: aload         9
      51: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
      54: aload         9
      56: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
      59: fsub
      60: invokestatic  #2069               // Method arc/graphics/g2d/Lines.rect:(FFFF)V
      63: aload         7
      65: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
      68: aload         9
      70: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
      73: aload         9
      75: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
      78: aload         9
      80: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
      83: aload         9
      85: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
      88: fsub
      89: aload         9
      91: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
      94: aload         9
      96: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
      99: fsub
     100: invokestatic  #2069               // Method arc/graphics/g2d/Lines.rect:(FFFF)V
     103: iload         8
     105: ifeq          325
     108: getstatic     #2105               // Field mindustry/ui/Fonts.outline:Larc/graphics/g2d/Font;
     111: astore        10
     113: aload         10
     115: aload         7
     117: invokevirtual #2111               // Method arc/graphics/g2d/Font.setColor:(Larc/graphics/Color;)V
     120: aload         10
     122: invokevirtual #2116               // Method arc/graphics/g2d/Font.usesIntegerPositions:()Z
     125: istore        11
     127: aload         10
     129: iconst_0
     130: invokevirtual #2119               // Method arc/graphics/g2d/Font.setUseIntegerPositions:(Z)V
     133: invokestatic  #2122               // Method arc/graphics/g2d/Draw.z:()F
     136: fstore        12
     138: ldc_w         #2125               // float 210.0f
     141: invokestatic  #2126               // Method arc/graphics/g2d/Draw.z:(F)V
     144: aload         10
     146: invokevirtual #2128               // Method arc/graphics/g2d/Font.getData:()Larc/graphics/g2d/Font$FontData;
     149: fconst_1
     150: getstatic     #1345               // Field mindustry/Vars.renderer:Lmindustry/core/Renderer;
     153: getfield      #2132               // Field mindustry/core/Renderer.camerascale:F
     156: fdiv
     157: invokevirtual #2135               // Method arc/graphics/g2d/Font$FontData.setScale:(F)V
     160: aload         9
     162: getfield      #2054               // Field mindustry/input/Placement$NormalizeDrawResult.x2:F
     165: aload         9
     167: getfield      #2050               // Field mindustry/input/Placement$NormalizeDrawResult.x:F
     170: fsub
     171: ldc_w         #1755               // float 8.0f
     174: fdiv
     175: f2i
     176: istore        13
     178: aload         9
     180: getfield      #2056               // Field mindustry/input/Placement$NormalizeDrawResult.y2:F
     183: aload         9
     185: getfield      #2053               // Field mindustry/input/Placement$NormalizeDrawResult.y:F
     188: fsub
     189: ldc_w         #1755               // float 8.0f
     192: fdiv
     193: f2i
     194: istore        14
     196: iload         13
     198: iload         14
     200: imul
     201: istore        15
     203: ldc_w         #1732               // float 5.0f
     206: getstatic     #1345               // Field mindustry/Vars.renderer:Lmindustry/core/Renderer;
     209: getfield      #2132               // Field mindustry/core/Renderer.camerascale:F
     212: fdiv
     213: ldc_w         #1755               // float 8.0f
     216: fmul
     217: fstore        16
     219: aload         10
     221: iload         13
     223: iload         14
     225: iload         15
     227: invokedynamic #2140,  0           // InvokeDynamic #43:makeConcatWithConstants:(III)Ljava/lang/String;
     232: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     235: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
     238: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     241: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
     244: iload_1
     245: bipush        8
     247: imul
     248: i2f
     249: fcmpl
     250: ifle          258
     253: fload         16
     255: goto          261
     258: fload         16
     260: fneg
     261: fadd
     262: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     265: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
     268: getstatic     #1485               // Field arc/Core.input:Larc/Input;
     271: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
     274: iload_2
     275: bipush        8
     277: imul
     278: i2f
     279: fcmpl
     280: ifle          288
     283: fload         16
     285: goto          291
     288: fload         16
     290: fneg
     291: fadd
     292: invokevirtual #2143               // Method arc/graphics/g2d/Font.draw:(Ljava/lang/CharSequence;FF)Larc/graphics/g2d/GlyphLayout;
     295: pop
     296: aload         10
     298: getstatic     #1037               // Field arc/graphics/Color.white:Larc/graphics/Color;
     301: invokevirtual #2111               // Method arc/graphics/g2d/Font.setColor:(Larc/graphics/Color;)V
     304: aload         10
     306: invokevirtual #2128               // Method arc/graphics/g2d/Font.getData:()Larc/graphics/g2d/Font$FontData;
     309: fconst_1
     310: invokevirtual #2135               // Method arc/graphics/g2d/Font$FontData.setScale:(F)V
     313: aload         10
     315: iload         11
     317: invokevirtual #2119               // Method arc/graphics/g2d/Font.setUseIntegerPositions:(Z)V
     320: fload         12
     322: invokestatic  #2126               // Method arc/graphics/g2d/Draw.z:(F)V
     325: return

  protected void flushSelectPlans(arc.struct.Seq<mindustry.entities.units.BuildPlan>);
    Code:
       0: aload_1
       1: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
       4: astore_2
       5: aload_2
       6: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      11: ifeq          173
      14: aload_2
      15: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      20: checkcast     #74                 // class mindustry/entities/units/BuildPlan
      23: astore_3
      24: aload_3
      25: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      28: ifnull        170
      31: aload_0
      32: aload_3
      33: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      36: aload_3
      37: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      40: aload_3
      41: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      44: aload_3
      45: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
      48: aconst_null
      49: iconst_1
      50: invokevirtual #2146               // Method validPlace:(IILmindustry/world/Block;ILmindustry/entities/units/BuildPlan;Z)Z
      53: ifeq          170
      56: aload_0
      57: aload_3
      58: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      61: aload_3
      62: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      65: aload_3
      66: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      69: getfield      #860                // Field mindustry/world/Block.size:I
      72: aconst_null
      73: invokevirtual #1982               // Method getPlan:(IIILmindustry/entities/units/BuildPlan;)Lmindustry/entities/units/BuildPlan;
      76: astore        4
      78: aload         4
      80: ifnonnull     98
      83: aload_0
      84: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
      87: aload_3
      88: invokevirtual #2149               // Method mindustry/entities/units/BuildPlan.copy:()Lmindustry/entities/units/BuildPlan;
      91: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
      94: pop
      95: goto          170
      98: aload         4
     100: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     103: ifne          170
     106: aload         4
     108: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     111: aload_3
     112: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     115: if_icmpne     170
     118: aload         4
     120: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     123: aload_3
     124: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     127: if_icmpne     170
     130: aload         4
     132: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     135: getfield      #860                // Field mindustry/world/Block.size:I
     138: aload_3
     139: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     142: getfield      #860                // Field mindustry/world/Block.size:I
     145: if_icmpne     170
     148: aload_0
     149: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     152: aload         4
     154: invokevirtual #1561               // Method arc/struct/Seq.remove:(Ljava/lang/Object;)Z
     157: pop
     158: aload_0
     159: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     162: aload_3
     163: invokevirtual #2149               // Method mindustry/entities/units/BuildPlan.copy:()Lmindustry/entities/units/BuildPlan;
     166: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
     169: pop
     170: goto          5
     173: return

  protected void flushPlansReverse(arc.struct.Seq<mindustry.entities.units.BuildPlan>);
    Code:
       0: aload_1
       1: getfield      #596                // Field arc/struct/Seq.size:I
       4: iconst_1
       5: isub
       6: istore_2
       7: iload_2
       8: iflt          94
      11: aload_1
      12: iload_2
      13: invokevirtual #1577               // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
      16: checkcast     #74                 // class mindustry/entities/units/BuildPlan
      19: astore_3
      20: aload_3
      21: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      24: ifnull        88
      27: aload_0
      28: aload_3
      29: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      32: aload_3
      33: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      36: aload_3
      37: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      40: aload_3
      41: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
      44: aconst_null
      45: iconst_1
      46: invokevirtual #2146               // Method validPlace:(IILmindustry/world/Block;ILmindustry/entities/units/BuildPlan;Z)Z
      49: ifeq          88
      52: aload_3
      53: invokevirtual #2149               // Method mindustry/entities/units/BuildPlan.copy:()Lmindustry/entities/units/BuildPlan;
      56: astore        4
      58: aload_3
      59: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      62: aload         4
      64: invokevirtual #2152               // Method mindustry/world/Block.onNewPlan:(Lmindustry/entities/units/BuildPlan;)V
      67: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      70: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      73: aload         4
      75: iconst_0
      76: invokevirtual #2155               // Method mindustry/gen/Unit.addBuild:(Lmindustry/entities/units/BuildPlan;Z)V
      79: aload_0
      80: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      83: aload         4
      85: invokevirtual #2159               // Method arc/math/geom/QuadTree.insert:(Larc/math/geom/QuadTree$QuadTreeObject;)V
      88: iinc          2, -1
      91: goto          7
      94: return

  protected void flushPlans(arc.struct.Seq<mindustry.entities.units.BuildPlan>);
    Code:
       0: aload_1
       1: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
       4: astore_2
       5: aload_2
       6: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      11: ifeq          94
      14: aload_2
      15: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      20: checkcast     #74                 // class mindustry/entities/units/BuildPlan
      23: astore_3
      24: aload_3
      25: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      28: ifnull        91
      31: aload_0
      32: aload_3
      33: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      36: aload_3
      37: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      40: aload_3
      41: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      44: aload_3
      45: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
      48: aconst_null
      49: iconst_1
      50: invokevirtual #2146               // Method validPlace:(IILmindustry/world/Block;ILmindustry/entities/units/BuildPlan;Z)Z
      53: ifeq          91
      56: aload_3
      57: invokevirtual #2149               // Method mindustry/entities/units/BuildPlan.copy:()Lmindustry/entities/units/BuildPlan;
      60: astore        4
      62: aload_3
      63: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      66: aload         4
      68: invokevirtual #2152               // Method mindustry/world/Block.onNewPlan:(Lmindustry/entities/units/BuildPlan;)V
      71: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      74: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      77: aload         4
      79: invokevirtual #2163               // Method mindustry/gen/Unit.addBuild:(Lmindustry/entities/units/BuildPlan;)V
      82: aload_0
      83: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      86: aload         4
      88: invokevirtual #2159               // Method arc/math/geom/QuadTree.insert:(Larc/math/geom/QuadTree$QuadTreeObject;)V
      91: goto          5
      94: return

  protected void drawOverPlan(mindustry.entities.units.BuildPlan);
    Code:
       0: aload_0
       1: aload_1
       2: aload_0
       3: aload_1
       4: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
       7: aload_1
       8: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      11: aload_1
      12: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      15: aload_1
      16: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
      19: invokevirtual #2165               // Method validPlace:(IILmindustry/world/Block;I)Z
      22: invokevirtual #2168               // Method drawOverPlan:(Lmindustry/entities/units/BuildPlan;Z)V
      25: return

  protected void drawOverPlan(mindustry.entities.units.BuildPlan, boolean);
    Code:
       0: invokestatic  #1725               // Method arc/graphics/g2d/Draw.reset:()V
       3: iload_2
       4: ifne          13
       7: getstatic     #2171               // Field mindustry/graphics/Pal.breakInvalid:Larc/graphics/Color;
      10: goto          16
      13: getstatic     #1037               // Field arc/graphics/Color.white:Larc/graphics/Color;
      16: iload_2
      17: ifne          26
      20: ldc_w         #1731               // float 0.4f
      23: goto          29
      26: ldc_w         #1884               // float 0.24f
      29: getstatic     #1885               // Field arc/util/Time.globalTime:F
      32: ldc_w         #1646               // float 6.0f
      35: ldc_w         #1888               // float 0.28f
      38: invokestatic  #1889               // Method arc/math/Mathf.absin:(FFF)F
      41: fadd
      42: invokestatic  #1892               // Method arc/graphics/g2d/Draw.mixcol:(Larc/graphics/Color;F)V
      45: fconst_1
      46: invokestatic  #2174               // Method arc/graphics/g2d/Draw.alpha:(F)V
      49: aload_1
      50: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      53: aload_1
      54: aload_0
      55: getfield      #1290               // Field allSelectLines:Larc/util/Eachable;
      58: invokevirtual #1895               // Method mindustry/world/Block.drawPlanConfigTop:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;)V
      61: invokestatic  #1725               // Method arc/graphics/g2d/Draw.reset:()V
      64: return

  protected void drawPlan(mindustry.entities.units.BuildPlan);
    Code:
       0: aload_0
       1: aload_1
       2: aload_1
       3: aload_0
       4: aload_1
       5: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
       8: aload_1
       9: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      12: aload_1
      13: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      16: aload_1
      17: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
      20: invokevirtual #2165               // Method validPlace:(IILmindustry/world/Block;I)Z
      23: dup_x1
      24: putfield      #2177               // Field mindustry/entities/units/BuildPlan.cachedValid:Z
      27: invokevirtual #2180               // Method drawPlan:(Lmindustry/entities/units/BuildPlan;Z)V
      30: return

  protected void drawPlan(mindustry.entities.units.BuildPlan, boolean);
    Code:
       0: aload_1
       1: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
       4: aload_1
       5: aload_0
       6: getfield      #1281               // Field allPlans:Larc/util/Eachable;
       9: iload_2
      10: invokevirtual #2182               // Method mindustry/world/Block.drawPlan:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;Z)V
      13: return

  protected void drawPlan(int, int, mindustry.world.Block, int);
    Code:
       0: aload_0
       1: getfield      #77                 // Field bplan:Lmindustry/entities/units/BuildPlan;
       4: iload_1
       5: iload_2
       6: iload         4
       8: aload_3
       9: invokevirtual #2185               // Method mindustry/entities/units/BuildPlan.set:(IIILmindustry/world/Block;)Lmindustry/entities/units/BuildPlan;
      12: pop
      13: aload_3
      14: getfield      #2188               // Field mindustry/world/Block.saveConfig:Z
      17: ifeq          31
      20: aload_0
      21: getfield      #77                 // Field bplan:Lmindustry/entities/units/BuildPlan;
      24: aload_3
      25: getfield      #2191               // Field mindustry/world/Block.lastConfig:Ljava/lang/Object;
      28: putfield      #2194               // Field mindustry/entities/units/BuildPlan.config:Ljava/lang/Object;
      31: aload_0
      32: getfield      #77                 // Field bplan:Lmindustry/entities/units/BuildPlan;
      35: fconst_1
      36: putfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
      39: aload_3
      40: aload_0
      41: getfield      #77                 // Field bplan:Lmindustry/entities/units/BuildPlan;
      44: aload_0
      45: getfield      #1281               // Field allPlans:Larc/util/Eachable;
      48: aload_0
      49: iload_1
      50: iload_2
      51: aload_3
      52: iload         4
      54: invokevirtual #2165               // Method validPlace:(IILmindustry/world/Block;I)Z
      57: invokevirtual #2182               // Method mindustry/world/Block.drawPlan:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;Z)V
      60: return

  protected void removeSelection(int, int, int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: iconst_0
       7: invokevirtual #2196               // Method removeSelection:(IIIIZ)V
      10: return

  protected void removeSelection(int, int, int, int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: iconst_0
       7: iload         5
       9: invokevirtual #2200               // Method removeSelection:(IIIIZI)V
      12: return

  protected void removeSelection(int, int, int, int, boolean);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: iload         5
       8: bipush        100
      10: invokevirtual #2200               // Method removeSelection:(IIIIZI)V
      13: return

  protected void removeSelection(int, int, int, int, boolean, int);
    Code:
       0: iload_1
       1: iload_2
       2: iload_3
       3: iload         4
       5: aload_0
       6: getfield      #53                 // Field rotation:I
       9: iconst_0
      10: iload         6
      12: invokestatic  #2027               // Method mindustry/input/Placement.normalizeArea:(IIIIIZI)Lmindustry/input/Placement$NormalizeResult;
      15: astore        7
      17: iconst_0
      18: istore        8
      20: iload         8
      22: aload         7
      24: getfield      #2034               // Field mindustry/input/Placement$NormalizeResult.x2:I
      27: aload         7
      29: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
      32: isub
      33: invokestatic  #2203               // Method java/lang/Math.abs:(I)I
      36: if_icmpgt     197
      39: iconst_0
      40: istore        9
      42: iload         9
      44: aload         7
      46: getfield      #2038               // Field mindustry/input/Placement$NormalizeResult.y2:I
      49: aload         7
      51: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
      54: isub
      55: invokestatic  #2203               // Method java/lang/Math.abs:(I)I
      58: if_icmpgt     191
      61: iload_1
      62: iload         8
      64: iload_3
      65: iload_1
      66: isub
      67: i2f
      68: invokestatic  #2207               // Method arc/math/Mathf.sign:(F)I
      71: imul
      72: iadd
      73: istore        10
      75: iload_2
      76: iload         9
      78: iload         4
      80: iload_2
      81: isub
      82: i2f
      83: invokestatic  #2207               // Method arc/math/Mathf.sign:(F)I
      86: imul
      87: iadd
      88: istore        11
      90: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      93: iload         10
      95: iload         11
      97: invokevirtual #2041               // Method mindustry/core/World.tileBuilding:(II)Lmindustry/world/Tile;
     100: astore        12
     102: aload         12
     104: ifnonnull     110
     107: goto          185
     110: iload         5
     112: ifne          126
     115: aload_0
     116: iload         10
     118: iload         11
     120: invokevirtual #2210               // Method tryBreakBlock:(II)V
     123: goto          185
     126: aload_0
     127: aload         12
     129: getfield      #2044               // Field mindustry/world/Tile.x:S
     132: aload         12
     134: getfield      #2045               // Field mindustry/world/Tile.y:S
     137: invokevirtual #2046               // Method validBreak:(II)Z
     140: ifeq          185
     143: aload_0
     144: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     147: aload         12
     149: invokedynamic #2213,  0           // InvokeDynamic #44:get:(Lmindustry/world/Tile;)Larc/func/Boolf;
     154: invokevirtual #1303               // Method arc/struct/Seq.contains:(Larc/func/Boolf;)Z
     157: ifne          185
     160: aload_0
     161: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     164: new           #74                 // class mindustry/entities/units/BuildPlan
     167: dup
     168: aload         12
     170: getfield      #2044               // Field mindustry/world/Tile.x:S
     173: aload         12
     175: getfield      #2045               // Field mindustry/world/Tile.y:S
     178: invokespecial #2216               // Method mindustry/entities/units/BuildPlan."<init>":(II)V
     181: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
     184: pop
     185: iinc          9, 1
     188: goto          42
     191: iinc          8, 1
     194: goto          20
     197: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     200: aload         7
     202: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
     205: bipush        8
     207: imul
     208: i2f
     209: aload         7
     211: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
     214: bipush        8
     216: imul
     217: i2f
     218: aload         7
     220: getfield      #2034               // Field mindustry/input/Placement$NormalizeResult.x2:I
     223: aload         7
     225: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
     228: isub
     229: bipush        8
     231: imul
     232: i2f
     233: aload         7
     235: getfield      #2038               // Field mindustry/input/Placement$NormalizeResult.y2:I
     238: aload         7
     240: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
     243: isub
     244: bipush        8
     246: imul
     247: i2f
     248: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
     251: pop
     252: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     255: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
     258: ifne          403
     261: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     264: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     267: invokevirtual #2001               // Method mindustry/gen/Unit.plans:()Larc/struct/Queue;
     270: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     273: astore        8
     275: aload         8
     277: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     282: ifeq          332
     285: aload         8
     287: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     292: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     295: astore        9
     297: aload         9
     299: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     302: ifne          329
     305: aload         9
     307: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     310: invokevirtual #2061               // Method mindustry/entities/units/BuildPlan.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
     313: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     316: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     319: ifeq          329
     322: aload         8
     324: invokeinterface #422,  1          // InterfaceMethod java/util/Iterator.remove:()V
     329: goto          275
     332: iload         5
     334: ifeq          403
     337: aload_0
     338: getfield      #88                 // Field selectPlans:Larc/struct/Seq;
     341: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
     344: astore        8
     346: aload         8
     348: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     353: ifeq          403
     356: aload         8
     358: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     363: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     366: astore        9
     368: aload         9
     370: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
     373: ifne          400
     376: aload         9
     378: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     381: invokevirtual #2061               // Method mindustry/entities/units/BuildPlan.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
     384: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     387: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     390: ifeq          400
     393: aload         8
     395: invokeinterface #422,  1          // InterfaceMethod java/util/Iterator.remove:()V
     400: goto          346
     403: getstatic     #2218               // Field removed:Larc/struct/IntSeq;
     406: invokevirtual #2221               // Method arc/struct/IntSeq.clear:()V
     409: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     412: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     415: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
     418: getfield      #385                // Field mindustry/game/Teams$TeamData.plans:Larc/struct/Queue;
     421: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
     424: astore        8
     426: aload         8
     428: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
     433: ifeq          517
     436: aload         8
     438: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     443: checkcast     #403                // class mindustry/game/Teams$BlockPlan
     446: astore        9
     448: aload         9
     450: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     453: astore        10
     455: aload         10
     457: aload         9
     459: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     462: aload         9
     464: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     467: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     470: invokevirtual #2063               // Method mindustry/world/Block.bounds:(IILarc/math/geom/Rect;)Larc/math/geom/Rect;
     473: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     476: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     479: ifeq          514
     482: getstatic     #2218               // Field removed:Larc/struct/IntSeq;
     485: aload         9
     487: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     490: aload         9
     492: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     495: invokestatic  #2222               // Method arc/math/geom/Point2.pack:(II)I
     498: invokevirtual #2225               // Method arc/struct/IntSeq.add:(I)V
     501: aload         9
     503: iconst_1
     504: putfield      #419                // Field mindustry/game/Teams$BlockPlan.removed:Z
     507: aload         8
     509: invokeinterface #422,  1          // InterfaceMethod java/util/Iterator.remove:()V
     514: goto          426
     517: getstatic     #2218               // Field removed:Larc/struct/IntSeq;
     520: getfield      #2227               // Field arc/struct/IntSeq.size:I
     523: ifle          547
     526: getstatic     #331                // Field mindustry/Vars.net:Lmindustry/net/Net;
     529: invokevirtual #2228               // Method mindustry/net/Net.active:()Z
     532: ifeq          547
     535: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     538: getstatic     #2218               // Field removed:Larc/struct/IntSeq;
     541: invokevirtual #1594               // Method arc/struct/IntSeq.toArray:()[I
     544: invokestatic  #2231               // Method mindustry/gen/Call.deletePlans:(Lmindustry/gen/Player;[I)V
     547: return

  protected void updateLine(int, int, int, int);
    Code:
       0: aload_0
       1: getfield      #82                 // Field linePlans:Larc/struct/Seq;
       4: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
       7: pop
       8: aload_0
       9: iload_1
      10: iload_2
      11: iload_3
      12: iload         4
      14: aload_0
      15: invokedynamic #2235,  0           // InvokeDynamic #45:get:(Lmindustry/input/InputHandler;)Larc/func/Cons;
      20: invokevirtual #2236               // Method iterateLine:(IIIILarc/func/Cons;)V
      23: getstatic     #2240               // Field arc/Core.settings:Larc/Settings;
      26: ldc_w         #2244               // String blockreplace
      29: invokevirtual #2246               // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      32: ifeq          59
      35: aload_0
      36: getfield      #82                 // Field linePlans:Larc/struct/Seq;
      39: aload_0
      40: invokedynamic #2252,  0           // InvokeDynamic #46:get:(Lmindustry/input/InputHandler;)Larc/func/Cons;
      45: invokevirtual #1972               // Method arc/struct/Seq.each:(Larc/func/Cons;)V
      48: aload_0
      49: getfield      #1421               // Field block:Lmindustry/world/Block;
      52: aload_0
      53: getfield      #82                 // Field linePlans:Larc/struct/Seq;
      56: invokevirtual #2253               // Method mindustry/world/Block.handlePlacementLine:(Larc/struct/Seq;)V
      59: return

  protected void updateLine(int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: aload_0
       4: aload_0
       5: invokevirtual #2256               // Method getMouseX:()F
       8: invokevirtual #2259               // Method tileX:(F)I
      11: aload_0
      12: aload_0
      13: invokevirtual #2262               // Method getMouseY:()F
      16: invokevirtual #2265               // Method tileY:(F)I
      19: invokevirtual #2268               // Method updateLine:(IIII)V
      22: return

  boolean checkConfigTap();
    Code:
       0: aload_0
       1: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
       4: invokevirtual #2272               // Method mindustry/ui/fragments/BlockConfigFragment.isShown:()Z
       7: ifeq          39
      10: aload_0
      11: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
      14: invokevirtual #2275               // Method mindustry/ui/fragments/BlockConfigFragment.getSelected:()Lmindustry/gen/Building;
      17: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      20: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      23: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      26: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      29: invokevirtual #2279               // Method mindustry/gen/Building.onConfigureTapped:(FF)Z
      32: ifeq          39
      35: iconst_1
      36: goto          40
      39: iconst_0
      40: ireturn

  boolean tileTapped(mindustry.gen.Building);
    Code:
       0: aload_0
       1: getfield      #184                // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
       4: invokevirtual #2283               // Method mindustry/ui/fragments/PlanConfigFragment.hide:()V
       7: aload_1
       8: ifnonnull     35
      11: aload_0
      12: getfield      #170                // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
      15: invokevirtual #2286               // Method mindustry/ui/fragments/BlockInventoryFragment.hide:()V
      18: aload_0
      19: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
      22: invokevirtual #2287               // Method mindustry/ui/fragments/BlockConfigFragment.hideConfig:()V
      25: aload_0
      26: getfield      #104                // Field commandBuildings:Larc/struct/Seq;
      29: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      32: pop
      33: iconst_0
      34: ireturn
      35: iconst_0
      36: istore_2
      37: iconst_0
      38: istore_3
      39: aload_1
      40: invokevirtual #718                // Method mindustry/gen/Building.isCommandable:()Z
      43: ifeq          58
      46: aload_0
      47: getfield      #107                // Field commandMode:Z
      50: ifeq          58
      53: iconst_1
      54: istore_2
      55: goto          233
      58: aload_1
      59: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
      62: getfield      #2290               // Field mindustry/world/Block.configurable:Z
      65: ifeq          178
      68: aload_1
      69: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      72: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      75: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
      78: ifeq          178
      81: iconst_1
      82: istore_2
      83: aload_0
      84: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
      87: invokevirtual #2272               // Method mindustry/ui/fragments/BlockConfigFragment.isShown:()Z
      90: ifne          103
      93: aload_1
      94: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      97: invokevirtual #2293               // Method mindustry/gen/Building.shouldShowConfigure:(Lmindustry/gen/Player;)Z
     100: ifne          137
     103: aload_0
     104: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     107: invokevirtual #2272               // Method mindustry/ui/fragments/BlockConfigFragment.isShown:()Z
     110: ifeq          233
     113: aload_0
     114: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     117: invokevirtual #2275               // Method mindustry/ui/fragments/BlockConfigFragment.getSelected:()Lmindustry/gen/Building;
     120: aload_1
     121: invokevirtual #2297               // Method mindustry/gen/Building.onConfigureBuildTapped:(Lmindustry/gen/Building;)Z
     124: ifeq          233
     127: aload_1
     128: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     131: invokevirtual #2293               // Method mindustry/gen/Building.shouldShowConfigure:(Lmindustry/gen/Player;)Z
     134: ifeq          233
     137: aload_1
     138: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     141: getfield      #2300               // Field mindustry/world/Block.configureSound:Larc/audio/Sound;
     144: aload_1
     145: getfield      #1070               // Field mindustry/gen/Building.x:F
     148: aload_1
     149: getfield      #1071               // Field mindustry/gen/Building.y:F
     152: fconst_1
     153: fconst_1
     154: getstatic     #2303               // Field mindustry/Vars.control:Lmindustry/core/Control;
     157: getfield      #2306               // Field mindustry/core/Control.sound:Lmindustry/audio/SoundControl;
     160: getfield      #2312               // Field mindustry/audio/SoundControl.uiBus:Larc/audio/AudioBus;
     163: invokevirtual #2318               // Method arc/audio/Sound.at:(FFFFLarc/audio/AudioBus;)I
     166: pop
     167: aload_0
     168: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     171: aload_1
     172: invokevirtual #2321               // Method mindustry/ui/fragments/BlockConfigFragment.showConfig:(Lmindustry/gen/Building;)V
     175: goto          233
     178: aload_0
     179: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     182: invokevirtual #2324               // Method mindustry/ui/fragments/BlockConfigFragment.hasConfigMouse:()Z
     185: ifne          233
     188: aload_0
     189: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     192: invokevirtual #2272               // Method mindustry/ui/fragments/BlockConfigFragment.isShown:()Z
     195: ifeq          221
     198: aload_0
     199: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     202: invokevirtual #2275               // Method mindustry/ui/fragments/BlockConfigFragment.getSelected:()Lmindustry/gen/Building;
     205: aload_1
     206: invokevirtual #2297               // Method mindustry/gen/Building.onConfigureBuildTapped:(Lmindustry/gen/Building;)Z
     209: ifeq          221
     212: iconst_1
     213: istore_2
     214: aload_0
     215: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     218: invokevirtual #2287               // Method mindustry/ui/fragments/BlockConfigFragment.hideConfig:()V
     221: aload_0
     222: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     225: invokevirtual #2272               // Method mindustry/ui/fragments/BlockConfigFragment.isShown:()Z
     228: ifeq          233
     231: iconst_1
     232: istore_2
     233: iload_2
     234: ifne          254
     237: aload_1
     238: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     241: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     244: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
     247: ifeq          254
     250: aload_1
     251: invokevirtual #2327               // Method mindustry/gen/Building.tapped:()V
     254: aload_1
     255: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     258: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     261: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
     264: ifeq          282
     267: aload_1
     268: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     271: getfield      #2330               // Field mindustry/world/Block.consumesTap:Z
     274: ifeq          282
     277: iconst_1
     278: istore_2
     279: goto          351
     282: aload_1
     283: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     286: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     289: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
     292: ifeq          351
     295: aload_1
     296: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     299: invokevirtual #2333               // Method mindustry/world/Block.synthetic:()Z
     302: ifeq          351
     305: iload_2
     306: ifeq          319
     309: aload_1
     310: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     313: getfield      #2336               // Field mindustry/world/Block.allowConfigInventory:Z
     316: ifeq          351
     319: aload_1
     320: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     323: getfield      #2339               // Field mindustry/world/Block.hasItems:Z
     326: ifeq          351
     329: aload_1
     330: getfield      #271                // Field mindustry/gen/Building.items:Lmindustry/world/modules/ItemModule;
     333: invokevirtual #2342               // Method mindustry/world/modules/ItemModule.total:()I
     336: ifle          351
     339: aload_0
     340: getfield      #170                // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
     343: aload_1
     344: invokevirtual #2345               // Method mindustry/ui/fragments/BlockInventoryFragment.showFor:(Lmindustry/gen/Building;)V
     347: iconst_1
     348: istore_2
     349: iconst_1
     350: istore_3
     351: iload_3
     352: ifne          362
     355: aload_0
     356: getfield      #170                // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
     359: invokevirtual #2286               // Method mindustry/ui/fragments/BlockInventoryFragment.hide:()V
     362: iload_2
     363: ireturn

  boolean tryTapPlayer(float, float);
    Code:
       0: aload_0
       1: fload_1
       2: fload_2
       3: invokevirtual #2348               // Method canTapPlayer:(FF)Z
       6: ifeq          16
       9: aload_0
      10: iconst_1
      11: putfield      #1412               // Field droppingItem:Z
      14: iconst_1
      15: ireturn
      16: iconst_0
      17: ireturn

  boolean canTapPlayer(float, float);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: fload_1
       4: fload_2
       5: getstatic     #2351               // Field playerSelectRange:F
       8: invokevirtual #2354               // Method mindustry/gen/Player.within:(FFF)Z
      11: ifeq          49
      14: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      17: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      20: ifne          49
      23: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      26: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      29: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      32: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      35: ifle          49
      38: aload_0
      39: getfield      #1421               // Field block:Lmindustry/world/Block;
      42: ifnonnull     49
      45: iconst_1
      46: goto          50
      49: iconst_0
      50: ireturn

  boolean tryBeginMine(mindustry.world.Tile);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
       6: ifne          29
       9: aload_0
      10: aload_1
      11: invokevirtual #2355               // Method canMine:(Lmindustry/world/Tile;)Z
      14: ifeq          29
      17: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      20: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      23: aload_1
      24: putfield      #2358               // Field mindustry/gen/Unit.mineTile:Lmindustry/world/Tile;
      27: iconst_1
      28: ireturn
      29: iconst_0
      30: ireturn

  boolean tryStopMine();
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
       6: ifne          33
       9: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      12: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      15: invokevirtual #2361               // Method mindustry/gen/Unit.mining:()Z
      18: ifeq          33
      21: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      24: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      27: aconst_null
      28: putfield      #2358               // Field mindustry/gen/Unit.mineTile:Lmindustry/world/Tile;
      31: iconst_1
      32: ireturn
      33: iconst_0
      34: ireturn

  boolean tryStopMine(mindustry.world.Tile);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
       6: ifne          34
       9: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      12: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      15: getfield      #2358               // Field mindustry/gen/Unit.mineTile:Lmindustry/world/Tile;
      18: aload_1
      19: if_acmpne     34
      22: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      25: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      28: aconst_null
      29: putfield      #2358               // Field mindustry/gen/Unit.mineTile:Lmindustry/world/Tile;
      32: iconst_1
      33: ireturn
      34: iconst_0
      35: ireturn

  boolean tryRepairDerelict(mindustry.world.Tile);
    Code:
       0: aload_0
       1: aload_1
       2: invokevirtual #2095               // Method canRepairDerelict:(Lmindustry/world/Tile;)Z
       5: ifeq          58
       8: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      11: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      14: new           #74                 // class mindustry/entities/units/BuildPlan
      17: dup
      18: aload_1
      19: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      22: invokevirtual #2364               // Method mindustry/gen/Building.tileX:()I
      25: aload_1
      26: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      29: invokevirtual #2366               // Method mindustry/gen/Building.tileY:()I
      32: aload_1
      33: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      36: getfield      #1053               // Field mindustry/gen/Building.rotation:I
      39: aload_1
      40: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
      43: aload_1
      44: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      47: invokevirtual #1112               // Method mindustry/gen/Building.config:()Ljava/lang/Object;
      50: invokespecial #2368               // Method mindustry/entities/units/BuildPlan."<init>":(IIILmindustry/world/Block;Ljava/lang/Object;)V
      53: invokevirtual #2163               // Method mindustry/gen/Unit.addBuild:(Lmindustry/entities/units/BuildPlan;)V
      56: iconst_1
      57: ireturn
      58: iconst_0
      59: ireturn

  boolean canRepairDerelict(mindustry.world.Tile);
    Code:
       0: aload_1
       1: ifnull        111
       4: aload_1
       5: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
       8: ifnull        111
      11: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      14: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      17: ifne          111
      20: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      23: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
      26: getfield      #2371               // Field mindustry/game/Rules.editor:Z
      29: ifne          111
      32: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      35: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      38: getstatic     #2374               // Field mindustry/game/Team.derelict:Lmindustry/game/Team;
      41: if_acmpeq     111
      44: aload_1
      45: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      48: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
      51: getstatic     #2374               // Field mindustry/game/Team.derelict:Lmindustry/game/Team;
      54: if_acmpne     111
      57: aload_1
      58: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      61: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
      64: invokevirtual #2377               // Method mindustry/world/Block.unlockedNowHost:()Z
      67: ifeq          111
      70: aload_1
      71: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
      74: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      77: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      80: aload_1
      81: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      84: invokevirtual #2364               // Method mindustry/gen/Building.tileX:()I
      87: aload_1
      88: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      91: invokevirtual #2366               // Method mindustry/gen/Building.tileY:()I
      94: aload_1
      95: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      98: getfield      #1053               // Field mindustry/gen/Building.rotation:I
     101: invokestatic  #1853               // Method mindustry/world/Build.validPlace:(Lmindustry/world/Block;Lmindustry/game/Team;III)Z
     104: ifeq          111
     107: iconst_1
     108: goto          112
     111: iconst_0
     112: ireturn

  boolean canMine(mindustry.world.Tile);
    Code:
       0: getstatic     #2380               // Field arc/Core.scene:Larc/scene/Scene;
       3: invokevirtual #2384               // Method arc/scene/Scene.hasMouse:()Z
       6: ifne          121
       9: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      12: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      15: ifne          121
      18: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      21: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      24: aload_1
      25: invokevirtual #2389               // Method mindustry/gen/Unit.validMine:(Lmindustry/world/Tile;)Z
      28: ifeq          121
      31: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      34: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      37: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      40: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      43: aload_1
      44: invokevirtual #2392               // Method mindustry/gen/Unit.getMineResult:(Lmindustry/world/Tile;)Lmindustry/type/Item;
      47: invokevirtual #2396               // Method mindustry/gen/Unit.acceptsItem:(Lmindustry/type/Item;)Z
      50: ifeq          121
      53: getstatic     #2240               // Field arc/Core.settings:Larc/Settings;
      56: ldc_w         #2400               // String doubletapmine
      59: invokevirtual #2246               // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      62: ifne          85
      65: aload_1
      66: invokevirtual #2402               // Method mindustry/world/Tile.floor:()Lmindustry/world/blocks/environment/Floor;
      69: getfield      #2406               // Field mindustry/world/blocks/environment/Floor.playerUnmineable:Z
      72: ifeq          85
      75: aload_1
      76: invokevirtual #2411               // Method mindustry/world/Tile.overlay:()Lmindustry/world/blocks/environment/Floor;
      79: getfield      #2414               // Field mindustry/world/blocks/environment/Floor.itemDrop:Lmindustry/type/Item;
      82: ifnull        121
      85: getstatic     #2240               // Field arc/Core.settings:Larc/Settings;
      88: ldc_w         #2400               // String doubletapmine
      91: invokevirtual #2246               // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      94: ifne          117
      97: aload_1
      98: invokevirtual #2411               // Method mindustry/world/Tile.overlay:()Lmindustry/world/blocks/environment/Floor;
     101: getfield      #2406               // Field mindustry/world/blocks/environment/Floor.playerUnmineable:Z
     104: ifeq          117
     107: aload_1
     108: invokevirtual #2411               // Method mindustry/world/Tile.overlay:()Lmindustry/world/blocks/environment/Floor;
     111: getfield      #2414               // Field mindustry/world/blocks/environment/Floor.itemDrop:Lmindustry/type/Item;
     114: ifnonnull     121
     117: iconst_1
     118: goto          122
     121: iconst_0
     122: ireturn

  mindustry.world.Tile tileAt(float, float);
    Code:
       0: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
       3: aload_0
       4: fload_1
       5: invokevirtual #2259               // Method tileX:(F)I
       8: aload_0
       9: fload_2
      10: invokevirtual #2265               // Method tileY:(F)I
      13: invokevirtual #1930               // Method mindustry/core/World.tile:(II)Lmindustry/world/Tile;
      16: areturn

  int rawTileX();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
       6: getfield      #984                // Field arc/math/geom/Vec2.x:F
       9: invokestatic  #2417               // Method mindustry/core/World.toTile:(F)I
      12: ireturn

  int rawTileY();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
       6: getfield      #985                // Field arc/math/geom/Vec2.y:F
       9: invokestatic  #2417               // Method mindustry/core/World.toTile:(F)I
      12: ireturn

  int tileX(float);
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: fload_1
       4: fconst_0
       5: invokevirtual #1567               // Method arc/Input.mouseWorld:(FF)Larc/math/geom/Vec2;
       8: astore_2
       9: aload_0
      10: invokevirtual #2420               // Method selectedBlock:()Z
      13: ifeq          35
      16: aload_2
      17: aload_0
      18: getfield      #1421               // Field block:Lmindustry/world/Block;
      21: getfield      #1918               // Field mindustry/world/Block.offset:F
      24: aload_0
      25: getfield      #1421               // Field block:Lmindustry/world/Block;
      28: getfield      #1918               // Field mindustry/world/Block.offset:F
      31: invokevirtual #2422               // Method arc/math/geom/Vec2.sub:(FF)Larc/math/geom/Vec2;
      34: pop
      35: aload_2
      36: getfield      #984                // Field arc/math/geom/Vec2.x:F
      39: invokestatic  #2417               // Method mindustry/core/World.toTile:(F)I
      42: ireturn

  int tileY(float);
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: fconst_0
       4: fload_1
       5: invokevirtual #1567               // Method arc/Input.mouseWorld:(FF)Larc/math/geom/Vec2;
       8: astore_2
       9: aload_0
      10: invokevirtual #2420               // Method selectedBlock:()Z
      13: ifeq          35
      16: aload_2
      17: aload_0
      18: getfield      #1421               // Field block:Lmindustry/world/Block;
      21: getfield      #1918               // Field mindustry/world/Block.offset:F
      24: aload_0
      25: getfield      #1421               // Field block:Lmindustry/world/Block;
      28: getfield      #1918               // Field mindustry/world/Block.offset:F
      31: invokevirtual #2422               // Method arc/math/geom/Vec2.sub:(FF)Larc/math/geom/Vec2;
      34: pop
      35: aload_2
      36: getfield      #985                // Field arc/math/geom/Vec2.y:F
      39: invokestatic  #2417               // Method mindustry/core/World.toTile:(F)I
      42: ireturn

  public void panCamera(arc.math.geom.Vec2);
    Code:
       0: aload_0
       1: invokevirtual #1418               // Method locked:()Z
       4: ifne          18
       7: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
      10: getfield      #1315               // Field arc/graphics/Camera.position:Larc/math/geom/Vec2;
      13: aload_1
      14: invokevirtual #1787               // Method arc/math/geom/Vec2.set:(Larc/math/geom/Vec2;)Larc/math/geom/Vec2;
      17: pop
      18: return

  public boolean selectedBlock();
    Code:
       0: aload_0
       1: invokevirtual #2424               // Method isPlacing:()Z
       4: ireturn

  public boolean isPlacing();
    Code:
       0: aload_0
       1: getfield      #1421               // Field block:Lmindustry/world/Block;
       4: ifnull        11
       7: iconst_1
       8: goto          12
      11: iconst_0
      12: ireturn

  public boolean isBreaking();
    Code:
       0: iconst_0
       1: ireturn

  public boolean isRebuildSelecting();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: getstatic     #2427               // Field mindustry/input/Binding.rebuildSelect:Larc/input/KeyBind;
       6: invokevirtual #2433               // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
       9: ireturn

  public float mouseAngle(float, float);
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: aload_0
       4: invokevirtual #2256               // Method getMouseX:()F
       7: aload_0
       8: invokevirtual #2262               // Method getMouseY:()F
      11: invokevirtual #1567               // Method arc/Input.mouseWorld:(FF)Larc/math/geom/Vec2;
      14: fload_1
      15: fload_2
      16: invokevirtual #2422               // Method arc/math/geom/Vec2.sub:(FF)Larc/math/geom/Vec2;
      19: invokevirtual #2437               // Method arc/math/geom/Vec2.angle:()F
      22: freturn

  public mindustry.gen.Unit selectedUnit();
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
       6: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       9: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      12: getfield      #984                // Field arc/math/geom/Vec2.x:F
      15: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      18: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      21: getfield      #985                // Field arc/math/geom/Vec2.y:F
      24: ldc_w         #864                // float 40.0f
      27: invokedynamic #2440,  0           // InvokeDynamic #47:get:()Larc/func/Boolf;
      32: invokestatic  #1468               // Method mindustry/entities/Units.closest:(Lmindustry/game/Team;FFFLarc/func/Boolf;)Lmindustry/gen/Unit;
      35: astore_1
      36: aload_1
      37: ifnull        74
      40: aload_1
      41: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      44: invokevirtual #2441               // Method mindustry/gen/Unit.hitbox:(Larc/math/geom/Rect;)V
      47: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      50: ldc_w         #1646               // float 6.0f
      53: invokevirtual #2444               // Method arc/math/geom/Rect.grow:(F)Larc/math/geom/Rect;
      56: pop
      57: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      60: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      63: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      66: invokevirtual #2447               // Method arc/math/geom/Rect.contains:(Larc/math/geom/Vec2;)Z
      69: ifeq          74
      72: aload_1
      73: areturn
      74: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      77: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      80: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      83: getfield      #984                // Field arc/math/geom/Vec2.x:F
      86: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      89: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      92: getfield      #985                // Field arc/math/geom/Vec2.y:F
      95: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
      98: astore_2
      99: aload_2
     100: instanceof    #1459               // class mindustry/world/blocks/ControlBlock
     103: ifeq          167
     106: aload_2
     107: checkcast     #1459               // class mindustry/world/blocks/ControlBlock
     110: astore_3
     111: aload_3
     112: invokeinterface #1461,  1         // InterfaceMethod mindustry/world/blocks/ControlBlock.canControl:()Z
     117: ifeq          167
     120: aload_2
     121: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
     124: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     127: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     130: if_acmpne     167
     133: aload_3
     134: invokeinterface #1464,  1         // InterfaceMethod mindustry/world/blocks/ControlBlock.unit:()Lmindustry/gen/Unit;
     139: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     142: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     145: if_acmpeq     167
     148: aload_3
     149: invokeinterface #1464,  1         // InterfaceMethod mindustry/world/blocks/ControlBlock.unit:()Lmindustry/gen/Unit;
     154: invokevirtual #838                // Method mindustry/gen/Unit.isAI:()Z
     157: ifeq          167
     160: aload_3
     161: invokeinterface #1464,  1         // InterfaceMethod mindustry/world/blocks/ControlBlock.unit:()Lmindustry/gen/Unit;
     166: areturn
     167: aconst_null
     168: areturn

  public mindustry.gen.Building selectedControlBuild();
    Code:
       0: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
       3: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       6: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
       9: getfield      #984                // Field arc/math/geom/Vec2.x:F
      12: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      15: invokevirtual #1785               // Method arc/Input.mouseWorld:()Larc/math/geom/Vec2;
      18: getfield      #985                // Field arc/math/geom/Vec2.y:F
      21: invokevirtual #1455               // Method mindustry/core/World.buildWorld:(FF)Lmindustry/gen/Building;
      24: astore_1
      25: aload_1
      26: ifnull        66
      29: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      32: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
      35: ifne          66
      38: aload_1
      39: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      42: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      45: invokevirtual #1155               // Method mindustry/gen/Building.canControlSelect:(Lmindustry/gen/Unit;)Z
      48: ifeq          66
      51: aload_1
      52: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
      55: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      58: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      61: if_acmpne     66
      64: aload_1
      65: areturn
      66: aconst_null
      67: areturn

  public mindustry.gen.Unit selectedCommandUnit(float, float);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
       6: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
       9: invokevirtual #2450               // Method mindustry/game/Teams$TeamData.tree:()Larc/math/geom/QuadTree;
      12: astore_3
      13: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      16: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      19: pop
      20: ldc_w         #1601               // float 4.0f
      23: fstore        4
      25: aload_3
      26: fload_1
      27: fload         4
      29: fconst_2
      30: fdiv
      31: fsub
      32: fload_2
      33: fload         4
      35: fconst_2
      36: fdiv
      37: fsub
      38: fload         4
      40: fload         4
      42: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      45: invokevirtual #2457               // Method arc/math/geom/QuadTree.intersect:(FFFFLarc/struct/Seq;)V
      48: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      51: invokedynamic #2460,  0           // InvokeDynamic #48:get:()Larc/func/Boolf;
      56: fload_1
      57: fload_2
      58: invokedynamic #2461,  0           // InvokeDynamic #49:get:(FF)Larc/func/Floatf;
      63: invokevirtual #2464               // Method arc/struct/Seq.min:(Larc/func/Boolf;Larc/func/Floatf;)Ljava/lang/Object;
      66: checkcast     #231                // class mindustry/gen/Unit
      69: areturn

  public mindustry.gen.Unit selectedEnemyUnit(float, float);
    Code:
       0: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
       3: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
       6: pop
       7: ldc_w         #1601               // float 4.0f
      10: fstore_3
      11: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      14: getfield      #873                // Field mindustry/core/GameState.teams:Lmindustry/game/Teams;
      17: getfield      #2467               // Field mindustry/game/Teams.present:Larc/struct/Seq;
      20: astore        4
      22: iconst_0
      23: istore        5
      25: iload         5
      27: aload         4
      29: getfield      #596                // Field arc/struct/Seq.size:I
      32: if_icmpge     96
      35: aload         4
      37: getfield      #2470               // Field arc/struct/Seq.items:[Ljava/lang/Object;
      40: checkcast     #2473               // class "[Lmindustry/game/Teams$TeamData;"
      43: iload         5
      45: aaload
      46: getfield      #2475               // Field mindustry/game/Teams$TeamData.team:Lmindustry/game/Team;
      49: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      52: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      55: if_acmpeq     90
      58: aload         4
      60: getfield      #2470               // Field arc/struct/Seq.items:[Ljava/lang/Object;
      63: checkcast     #2473               // class "[Lmindustry/game/Teams$TeamData;"
      66: iload         5
      68: aaload
      69: invokevirtual #2450               // Method mindustry/game/Teams$TeamData.tree:()Larc/math/geom/QuadTree;
      72: fload_1
      73: fload_3
      74: fconst_2
      75: fdiv
      76: fsub
      77: fload_2
      78: fload_3
      79: fconst_2
      80: fdiv
      81: fsub
      82: fload_3
      83: fload_3
      84: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      87: invokevirtual #2457               // Method arc/math/geom/QuadTree.intersect:(FFFFLarc/struct/Seq;)V
      90: iinc          5, 1
      93: goto          25
      96: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      99: invokedynamic #2476,  0           // InvokeDynamic #50:get:()Larc/func/Boolf;
     104: fload_1
     105: fload_2
     106: invokedynamic #2477,  0           // InvokeDynamic #51:get:(FF)Larc/func/Floatf;
     111: invokevirtual #2464               // Method arc/struct/Seq.min:(Larc/func/Boolf;Larc/func/Floatf;)Ljava/lang/Object;
     114: checkcast     #231                // class mindustry/gen/Unit
     117: areturn

  public arc.struct.Seq<mindustry.gen.Building> selectedCommandBuildings(float, float, float, float);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
       6: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
       9: getfield      #2478               // Field mindustry/game/Teams$TeamData.buildingTree:Larc/math/geom/QuadTree;
      12: astore        5
      14: getstatic     #2481               // Field tmpBuildings:Larc/struct/Seq;
      17: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      20: pop
      21: aload         5
      23: ifnonnull     30
      26: getstatic     #2481               // Field tmpBuildings:Larc/struct/Seq;
      29: areturn
      30: ldc_w         #1601               // float 4.0f
      33: fstore        6
      35: aload         5
      37: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      40: fload_1
      41: fload         6
      43: fconst_2
      44: fdiv
      45: fsub
      46: fload_2
      47: fload         6
      49: fconst_2
      50: fdiv
      51: fsub
      52: fload         6
      54: fconst_2
      55: fmul
      56: fload_3
      57: fadd
      58: fload         6
      60: fconst_2
      61: fmul
      62: fload         4
      64: fadd
      65: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
      68: invokevirtual #2484               // Method arc/math/geom/Rect.normalize:()Larc/math/geom/Rect;
      71: invokedynamic #2488,  0           // InvokeDynamic #52:get:()Larc/func/Cons;
      76: invokevirtual #2489               // Method arc/math/geom/QuadTree.intersect:(Larc/math/geom/Rect;Larc/func/Cons;)V
      79: getstatic     #2481               // Field tmpBuildings:Larc/struct/Seq;
      82: areturn

  public arc.struct.Seq<mindustry.gen.Unit> selectedCommandUnits(float, float, float, float, arc.func.Boolf<mindustry.gen.Unit>);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
       6: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
       9: invokevirtual #2450               // Method mindustry/game/Teams$TeamData.tree:()Larc/math/geom/QuadTree;
      12: astore        6
      14: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      17: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      20: pop
      21: ldc_w         #1601               // float 4.0f
      24: fstore        7
      26: aload         6
      28: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      31: fload_1
      32: fload         7
      34: fconst_2
      35: fdiv
      36: fsub
      37: fload_2
      38: fload         7
      40: fconst_2
      41: fdiv
      42: fsub
      43: fload         7
      45: fconst_2
      46: fmul
      47: fload_3
      48: fadd
      49: fload         7
      51: fconst_2
      52: fmul
      53: fload         4
      55: fadd
      56: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
      59: invokevirtual #2484               // Method arc/math/geom/Rect.normalize:()Larc/math/geom/Rect;
      62: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      65: invokevirtual #1825               // Method arc/math/geom/QuadTree.intersect:(Larc/math/geom/Rect;Larc/struct/Seq;)V
      68: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      71: aload         5
      73: invokedynamic #2492,  0           // InvokeDynamic #53:get:(Larc/func/Boolf;)Larc/func/Boolf;
      78: invokevirtual #1363               // Method arc/struct/Seq.removeAll:(Larc/func/Boolf;)Larc/struct/Seq;
      81: pop
      82: getstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      85: areturn

  public arc.struct.Seq<mindustry.gen.Unit> selectedCommandUnits(float, float, float, float);
    Code:
       0: aload_0
       1: fload_1
       2: fload_2
       3: fload_3
       4: fload         4
       6: invokedynamic #2495,  0           // InvokeDynamic #54:get:()Larc/func/Boolf;
      11: invokevirtual #1558               // Method selectedCommandUnits:(FFFFLarc/func/Boolf;)Larc/struct/Seq;
      14: areturn

  public void remove();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: aload_0
       4: invokevirtual #2496               // Method arc/Input.removeProcessor:(Larc/input/InputProcessor;)V
       7: aload_0
       8: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
      11: invokevirtual #2500               // Method arc/scene/ui/layout/WidgetGroup.remove:()Z
      14: pop
      15: getstatic     #2380               // Field arc/Core.scene:Larc/scene/Scene;
      18: ifnull        42
      21: getstatic     #2380               // Field arc/Core.scene:Larc/scene/Scene;
      24: ldc_w         #2502               // String inputTable
      27: invokevirtual #2504               // Method arc/scene/Scene.find:(Ljava/lang/String;)Larc/scene/Element;
      30: checkcast     #2507               // class arc/scene/ui/layout/Table
      33: astore_1
      34: aload_1
      35: ifnull        42
      38: aload_1
      39: invokevirtual #2509               // Method arc/scene/ui/layout/Table.clear:()V
      42: aload_0
      43: getfield      #2510               // Field detector:Larc/input/GestureDetector;
      46: ifnull        59
      49: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      52: aload_0
      53: getfield      #2510               // Field detector:Larc/input/GestureDetector;
      56: invokevirtual #2496               // Method arc/Input.removeProcessor:(Larc/input/InputProcessor;)V
      59: aload_0
      60: getfield      #2514               // Field uiGroup:Larc/scene/Group;
      63: ifnull        79
      66: aload_0
      67: getfield      #2514               // Field uiGroup:Larc/scene/Group;
      70: invokevirtual #2518               // Method arc/scene/Group.remove:()Z
      73: pop
      74: aload_0
      75: aconst_null
      76: putfield      #2514               // Field uiGroup:Larc/scene/Group;
      79: return

  public void add();
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: invokevirtual #2521               // Method arc/Input.getInputProcessors:()Larc/struct/Seq;
       6: invokedynamic #2524,  0           // InvokeDynamic #55:get:()Larc/func/Boolf;
      11: invokevirtual #2525               // Method arc/struct/Seq.remove:(Larc/func/Boolf;)Z
      14: pop
      15: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      18: aload_0
      19: new           #2527               // class arc/input/GestureDetector
      22: dup
      23: ldc_w         #2529               // float 20.0f
      26: ldc_w         #1621               // float 0.5f
      29: ldc_w         #1778               // float 0.3f
      32: ldc_w         #2530               // float 0.15f
      35: aload_0
      36: invokespecial #2531               // Method arc/input/GestureDetector."<init>":(FFFFLarc/input/GestureDetector$GestureListener;)V
      39: dup_x1
      40: putfield      #2510               // Field detector:Larc/input/GestureDetector;
      43: invokevirtual #2534               // Method arc/Input.addProcessor:(Larc/input/InputProcessor;)V
      46: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      49: aload_0
      50: invokevirtual #2534               // Method arc/Input.addProcessor:(Larc/input/InputProcessor;)V
      53: getstatic     #2380               // Field arc/Core.scene:Larc/scene/Scene;
      56: ifnull        205
      59: getstatic     #2380               // Field arc/Core.scene:Larc/scene/Scene;
      62: ldc_w         #2502               // String inputTable
      65: invokevirtual #2504               // Method arc/scene/Scene.find:(Ljava/lang/String;)Larc/scene/Element;
      68: checkcast     #2507               // class arc/scene/ui/layout/Table
      71: astore_1
      72: aload_1
      73: ifnull        85
      76: aload_1
      77: invokevirtual #2509               // Method arc/scene/ui/layout/Table.clear:()V
      80: aload_0
      81: aload_1
      82: invokevirtual #2537               // Method buildPlacementUI:(Larc/scene/ui/layout/Table;)V
      85: aload_0
      86: new           #144                // class arc/scene/ui/layout/WidgetGroup
      89: dup
      90: invokespecial #146                // Method arc/scene/ui/layout/WidgetGroup."<init>":()V
      93: putfield      #2514               // Field uiGroup:Larc/scene/Group;
      96: aload_0
      97: getfield      #2514               // Field uiGroup:Larc/scene/Group;
     100: getstatic     #158                // Field arc/scene/event/Touchable.childrenOnly:Larc/scene/event/Touchable;
     103: putfield      #2541               // Field arc/scene/Group.touchable:Larc/scene/event/Touchable;
     106: aload_0
     107: getfield      #2514               // Field uiGroup:Larc/scene/Group;
     110: iconst_1
     111: invokevirtual #2542               // Method arc/scene/Group.setFillParent:(Z)V
     114: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
     117: getfield      #2545               // Field mindustry/core/UI.hudGroup:Larc/scene/ui/layout/WidgetGroup;
     120: aload_0
     121: getfield      #2514               // Field uiGroup:Larc/scene/Group;
     124: invokevirtual #2548               // Method arc/scene/ui/layout/WidgetGroup.addChild:(Larc/scene/Element;)V
     127: aload_0
     128: getfield      #2514               // Field uiGroup:Larc/scene/Group;
     131: invokevirtual #2552               // Method arc/scene/Group.toBack:()V
     134: aload_0
     135: aload_0
     136: getfield      #2514               // Field uiGroup:Larc/scene/Group;
     139: invokevirtual #2555               // Method buildUI:(Larc/scene/Group;)V
     142: aload_0
     143: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     146: iconst_1
     147: invokevirtual #2559               // Method arc/scene/ui/layout/WidgetGroup.setFillParent:(Z)V
     150: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
     153: getfield      #2545               // Field mindustry/core/UI.hudGroup:Larc/scene/ui/layout/WidgetGroup;
     156: getstatic     #2380               // Field arc/Core.scene:Larc/scene/Scene;
     159: ldc_w         #2560               // String overlaymarker
     162: invokevirtual #2504               // Method arc/scene/Scene.find:(Ljava/lang/String;)Larc/scene/Element;
     165: aload_0
     166: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     169: invokevirtual #2562               // Method arc/scene/ui/layout/WidgetGroup.addChildBefore:(Larc/scene/Element;Larc/scene/Element;)V
     172: aload_0
     173: getfield      #170                // Field inv:Lmindustry/ui/fragments/BlockInventoryFragment;
     176: aload_0
     177: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     180: invokevirtual #2566               // Method mindustry/ui/fragments/BlockInventoryFragment.build:(Larc/scene/Group;)V
     183: aload_0
     184: getfield      #177                // Field config:Lmindustry/ui/fragments/BlockConfigFragment;
     187: aload_0
     188: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     191: invokevirtual #2568               // Method mindustry/ui/fragments/BlockConfigFragment.build:(Larc/scene/Group;)V
     194: aload_0
     195: getfield      #184                // Field planConfig:Lmindustry/ui/fragments/PlanConfigFragment;
     198: aload_0
     199: getfield      #147                // Field group:Larc/scene/ui/layout/WidgetGroup;
     202: invokevirtual #2569               // Method mindustry/ui/fragments/PlanConfigFragment.build:(Larc/scene/Group;)V
     205: aload_0
     206: invokevirtual #2570               // Method initQuadtrees:()V
     209: return

  public boolean canShoot();
    Code:
       0: aload_0
       1: getfield      #1421               // Field block:Lmindustry/world/Block;
       4: ifnonnull     80
       7: aload_0
       8: invokevirtual #2573               // Method onConfigurable:()Z
      11: ifne          80
      14: aload_0
      15: invokevirtual #2576               // Method isDroppingItem:()Z
      18: ifne          80
      21: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      24: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      27: invokevirtual #2579               // Method mindustry/gen/Unit.activelyBuilding:()Z
      30: ifne          80
      33: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      36: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      39: instanceof    #2582               // class mindustry/gen/Mechc
      42: ifeq          57
      45: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      48: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      51: invokevirtual #1246               // Method mindustry/gen/Unit.isFlying:()Z
      54: ifne          80
      57: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      60: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      63: invokevirtual #2361               // Method mindustry/gen/Unit.mining:()Z
      66: ifne          80
      69: aload_0
      70: getfield      #107                // Field commandMode:Z
      73: ifne          80
      76: iconst_1
      77: goto          81
      80: iconst_0
      81: ireturn

  public boolean onConfigurable();
    Code:
       0: iconst_0
       1: ireturn

  public boolean isDroppingItem();
    Code:
       0: aload_0
       1: getfield      #1412               // Field droppingItem:Z
       4: ireturn

  public boolean canDropItem();
    Code:
       0: aload_0
       1: getfield      #1412               // Field droppingItem:Z
       4: ifeq          30
       7: aload_0
       8: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      11: invokevirtual #1509               // Method arc/Input.mouseWorldX:()F
      14: getstatic     #1485               // Field arc/Core.input:Larc/Input;
      17: invokevirtual #1512               // Method arc/Input.mouseWorldY:()F
      20: invokevirtual #2348               // Method canTapPlayer:(FF)Z
      23: ifne          30
      26: iconst_1
      27: goto          31
      30: iconst_0
      31: ireturn

  public void tryDropItems(mindustry.gen.Building, float, float);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #745                // Method mindustry/gen/Player.dead:()Z
       6: ifeq          10
       9: return
      10: aload_0
      11: getfield      #1412               // Field droppingItem:Z
      14: ifeq          50
      17: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      20: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      23: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      26: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      29: ifle          50
      32: aload_0
      33: fload_2
      34: fload_3
      35: invokevirtual #2348               // Method canTapPlayer:(FF)Z
      38: ifne          50
      41: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      44: invokevirtual #629                // Method mindustry/core/GameState.isPaused:()Z
      47: ifeq          56
      50: aload_0
      51: iconst_0
      52: putfield      #1412               // Field droppingItem:Z
      55: return
      56: aload_0
      57: iconst_0
      58: putfield      #1412               // Field droppingItem:Z
      61: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      64: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      67: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
      70: astore        4
      72: aload_1
      73: ifnull        188
      76: aload_1
      77: aload         4
      79: getfield      #280                // Field mindustry/type/ItemStack.item:Lmindustry/type/Item;
      82: aload         4
      84: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      87: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      90: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      93: invokevirtual #817                // Method mindustry/gen/Building.acceptStack:(Lmindustry/type/Item;ILmindustry/gen/Teamc;)I
      96: ifle          188
      99: aload_1
     100: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     103: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     106: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
     109: ifeq          188
     112: aload_1
     113: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     116: getfield      #2339               // Field mindustry/world/Block.hasItems:Z
     119: ifeq          188
     122: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     125: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     128: invokevirtual #2584               // Method mindustry/gen/Unit.stack:()Lmindustry/type/ItemStack;
     131: getfield      #286                // Field mindustry/type/ItemStack.amount:I
     134: ifle          188
     137: aload_1
     138: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     141: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
     144: invokevirtual #736                // Method mindustry/gen/Building.interactable:(Lmindustry/game/Team;)Z
     147: ifeq          188
     150: aload_1
     151: invokevirtual #783                // Method mindustry/gen/Building.allowDeposit:()Z
     154: ifeq          199
     157: aload_0
     158: aload_1
     159: invokevirtual #2587               // Method canDepositItem:(Lmindustry/gen/Building;)Z
     162: ifeq          199
     165: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     168: aload_1
     169: invokestatic  #2590               // Method mindustry/gen/Call.transferInventory:(Lmindustry/gen/Player;Lmindustry/gen/Building;)V
     172: aload_0
     173: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
     176: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
     179: getfield      #797                // Field mindustry/game/Rules.itemDepositCooldown:F
     182: putfield      #1326               // Field itemDepositCooldown:F
     185: goto          199
     188: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     191: fload_2
     192: fload_3
     193: invokevirtual #2593               // Method mindustry/gen/Player.angleTo:(FF)F
     196: invokestatic  #2596               // Method mindustry/gen/Call.dropItem:(F)V
     199: return

  public boolean canDepositItem(mindustry.gen.Building);
    Code:
       0: aload_1
       1: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
       4: getfield      #2598               // Field mindustry/world/Block.depositCooldown:F
       7: fconst_0
       8: fcmpl
       9: iflt          44
      12: aload_0
      13: getfield      #1326               // Field itemDepositCooldown:F
      16: getstatic     #625                // Field mindustry/Vars.state:Lmindustry/core/GameState;
      19: getfield      #793                // Field mindustry/core/GameState.rules:Lmindustry/game/Rules;
      22: getfield      #797                // Field mindustry/game/Rules.itemDepositCooldown:F
      25: fsub
      26: aload_1
      27: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
      30: getfield      #2598               // Field mindustry/world/Block.depositCooldown:F
      33: fneg
      34: fcmpg
      35: ifgt          42
      38: iconst_1
      39: goto          43
      42: iconst_0
      43: ireturn
      44: aload_0
      45: getfield      #1326               // Field itemDepositCooldown:F
      48: fconst_0
      49: fcmpg
      50: ifgt          57
      53: iconst_1
      54: goto          58
      57: iconst_0
      58: ireturn

  public void rebuildArea(int, int, int, int);
    Code:
       0: iload_1
       1: iload_2
       2: iload_3
       3: iload         4
       5: aload_0
       6: getfield      #53                 // Field rotation:I
       9: iconst_0
      10: ldc_w         #2081               // int 999999999
      13: invokestatic  #2027               // Method mindustry/input/Placement.normalizeArea:(IIIIIZI)Lmindustry/input/Placement$NormalizeResult;
      16: astore        5
      18: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      21: aload         5
      23: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
      26: bipush        8
      28: imul
      29: i2f
      30: aload         5
      32: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
      35: bipush        8
      37: imul
      38: i2f
      39: aload         5
      41: getfield      #2034               // Field mindustry/input/Placement$NormalizeResult.x2:I
      44: aload         5
      46: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
      49: isub
      50: bipush        8
      52: imul
      53: i2f
      54: aload         5
      56: getfield      #2038               // Field mindustry/input/Placement$NormalizeResult.y2:I
      59: aload         5
      61: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
      64: isub
      65: bipush        8
      67: imul
      68: i2f
      69: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
      72: pop
      73: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      76: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      79: invokevirtual #379                // Method mindustry/game/Team.data:()Lmindustry/game/Teams$TeamData;
      82: getfield      #385                // Field mindustry/game/Teams$TeamData.plans:Larc/struct/Queue;
      85: invokevirtual #390                // Method arc/struct/Queue.iterator:()Ljava/util/Iterator;
      88: astore        6
      90: aload         6
      92: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      97: ifeq          190
     100: aload         6
     102: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     107: checkcast     #403                // class mindustry/game/Teams$BlockPlan
     110: astore        7
     112: aload         7
     114: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     117: astore        8
     119: aload         8
     121: aload         7
     123: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     126: aload         7
     128: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     131: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     134: invokevirtual #2063               // Method mindustry/world/Block.bounds:(IILarc/math/geom/Rect;)Larc/math/geom/Rect;
     137: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     140: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     143: ifeq          187
     146: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
     149: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     152: new           #74                 // class mindustry/entities/units/BuildPlan
     155: dup
     156: aload         7
     158: getfield      #405                // Field mindustry/game/Teams$BlockPlan.x:S
     161: aload         7
     163: getfield      #414                // Field mindustry/game/Teams$BlockPlan.y:S
     166: aload         7
     168: getfield      #2601               // Field mindustry/game/Teams$BlockPlan.rotation:S
     171: aload         7
     173: getfield      #2062               // Field mindustry/game/Teams$BlockPlan.block:Lmindustry/world/Block;
     176: aload         7
     178: getfield      #2603               // Field mindustry/game/Teams$BlockPlan.config:Ljava/lang/Object;
     181: invokespecial #2368               // Method mindustry/entities/units/BuildPlan."<init>":(IIILmindustry/world/Block;Ljava/lang/Object;)V
     184: invokevirtual #2163               // Method mindustry/gen/Unit.addBuild:(Lmindustry/entities/units/BuildPlan;)V
     187: goto          90
     190: getstatic     #2082               // Field intSet:Larc/struct/IntSet;
     193: invokevirtual #2086               // Method arc/struct/IntSet.clear:()V
     196: aload         5
     198: getfield      #2031               // Field mindustry/input/Placement$NormalizeResult.x:I
     201: istore        7
     203: iload         7
     205: aload         5
     207: getfield      #2034               // Field mindustry/input/Placement$NormalizeResult.x2:I
     210: if_icmpgt     288
     213: aload         5
     215: getfield      #2037               // Field mindustry/input/Placement$NormalizeResult.y:I
     218: istore        8
     220: iload         8
     222: aload         5
     224: getfield      #2038               // Field mindustry/input/Placement$NormalizeResult.y2:I
     227: if_icmpgt     282
     230: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
     233: iload         7
     235: iload         8
     237: invokevirtual #2041               // Method mindustry/core/World.tileBuilding:(II)Lmindustry/world/Tile;
     240: astore        9
     242: aload         9
     244: ifnull        276
     247: aload         9
     249: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
     252: ifnull        276
     255: getstatic     #2082               // Field intSet:Larc/struct/IntSet;
     258: aload         9
     260: invokevirtual #2089               // Method mindustry/world/Tile.pos:()I
     263: invokevirtual #2092               // Method arc/struct/IntSet.add:(I)Z
     266: ifeq          276
     269: aload_0
     270: aload         9
     272: invokevirtual #2604               // Method tryRepairDerelict:(Lmindustry/world/Tile;)Z
     275: pop
     276: iinc          8, 1
     279: goto          220
     282: iinc          7, 1
     285: goto          203
     288: return

  public void tryBreakBlock(int, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: invokevirtual #2046               // Method validBreak:(II)Z
       6: ifeq          15
       9: aload_0
      10: iload_1
      11: iload_2
      12: invokevirtual #2607               // Method breakBlock:(II)V
      15: return

  public boolean validPlace(int, int, mindustry.world.Block, int);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: aload_3
       4: iload         4
       6: aconst_null
       7: invokevirtual #2610               // Method validPlace:(IILmindustry/world/Block;ILmindustry/entities/units/BuildPlan;)Z
      10: ireturn

  public boolean validPlace(int, int, mindustry.world.Block, int, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_0
       1: iload_1
       2: iload_2
       3: aload_3
       4: iload         4
       6: aload         5
       8: iconst_0
       9: invokevirtual #2146               // Method validPlace:(IILmindustry/world/Block;ILmindustry/entities/units/BuildPlan;Z)Z
      12: ireturn

  public boolean validPlace(int, int, mindustry.world.Block, int, mindustry.entities.units.BuildPlan, boolean);
    Code:
       0: iload         6
       2: ifeq          27
       5: aload_3
       6: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       9: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      12: iload_1
      13: iload_2
      14: iload         4
      16: iconst_1
      17: iconst_1
      18: invokestatic  #2613               // Method mindustry/world/Build.validPlaceIgnoreUnits:(Lmindustry/world/Block;Lmindustry/game/Team;IIIZZ)Z
      21: ifeq          44
      24: goto          46
      27: aload_3
      28: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      31: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      34: iload_1
      35: iload_2
      36: iload         4
      38: invokestatic  #1853               // Method mindustry/world/Build.validPlace:(Lmindustry/world/Block;Lmindustry/game/Team;III)Z
      41: ifne          46
      44: iconst_0
      45: ireturn
      46: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      49: invokevirtual #1367               // Method mindustry/gen/Player.isBuilder:()Z
      52: ifeq          207
      55: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      58: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      61: getfield      #1370               // Field mindustry/gen/Unit.plans:Larc/struct/Queue;
      64: getfield      #1371               // Field arc/struct/Queue.size:I
      67: ifle          207
      70: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
      73: iload_1
      74: bipush        8
      76: imul
      77: i2f
      78: aload_3
      79: getfield      #1918               // Field mindustry/world/Block.offset:F
      82: fadd
      83: iload_2
      84: bipush        8
      86: imul
      87: i2f
      88: aload_3
      89: getfield      #1918               // Field mindustry/world/Block.offset:F
      92: fadd
      93: aload_3
      94: getfield      #860                // Field mindustry/world/Block.size:I
      97: bipush        8
      99: imul
     100: i2f
     101: invokevirtual #1876               // Method arc/math/geom/Rect.setCentered:(FFF)Larc/math/geom/Rect;
     104: pop
     105: aload_0
     106: getfield      #126                // Field plansOut:Larc/struct/Seq;
     109: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
     112: pop
     113: aload_0
     114: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
     117: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     120: aload_0
     121: getfield      #126                // Field plansOut:Larc/struct/Seq;
     124: invokevirtual #1825               // Method arc/math/geom/QuadTree.intersect:(Larc/math/geom/Rect;Larc/struct/Seq;)V
     127: aload_3
     128: getfield      #860                // Field mindustry/world/Block.size:I
     131: bipush        8
     133: imul
     134: i2f
     135: fstore        7
     137: aload         5
     139: putstatic     #2617               // Field vpIgnore:Lmindustry/entities/units/BuildPlan;
     142: aload_3
     143: putstatic     #2620               // Field vpBlock:Lmindustry/world/Block;
     146: iload_1
     147: putstatic     #2623               // Field vpX:I
     150: iload_2
     151: putstatic     #2626               // Field vpY:I
     154: aload_0
     155: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
     158: iload_1
     159: bipush        8
     161: imul
     162: i2f
     163: aload_3
     164: getfield      #1918               // Field mindustry/world/Block.offset:F
     167: fadd
     168: fload         7
     170: fconst_2
     171: fdiv
     172: fsub
     173: iload_2
     174: bipush        8
     176: imul
     177: i2f
     178: aload_3
     179: getfield      #1918               // Field mindustry/world/Block.offset:F
     182: fadd
     183: fload         7
     185: fconst_2
     186: fdiv
     187: fsub
     188: fload         7
     190: fload         7
     192: getstatic     #2629               // Field vpPredicate:Larc/func/Boolf;
     195: invokevirtual #2633               // Method arc/math/geom/QuadTree.find:(FFFFLarc/func/Boolf;)Larc/math/geom/QuadTree$QuadTreeObject;
     198: ifnonnull     205
     201: iconst_1
     202: goto          206
     205: iconst_0
     206: ireturn
     207: iconst_1
     208: ireturn

  public boolean validBreak(int, int);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
       6: iload_1
       7: iload_2
       8: invokestatic  #2636               // Method mindustry/world/Build.validBreak:(Lmindustry/game/Team;II)Z
      11: ireturn

  public void breakBlock(int, int);
    Code:
       0: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       3: invokevirtual #1367               // Method mindustry/gen/Player.isBuilder:()Z
       6: ifne          10
       9: return
      10: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      13: iload_1
      14: iload_2
      15: invokevirtual #1930               // Method mindustry/core/World.tile:(II)Lmindustry/world/Tile;
      18: astore_3
      19: aload_3
      20: ifnull        38
      23: aload_3
      24: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      27: ifnull        38
      30: aload_3
      31: getfield      #1933               // Field mindustry/world/Tile.build:Lmindustry/gen/Building;
      34: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
      37: astore_3
      38: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      41: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      44: new           #74                 // class mindustry/entities/units/BuildPlan
      47: dup
      48: aload_3
      49: getfield      #2044               // Field mindustry/world/Tile.x:S
      52: aload_3
      53: getfield      #2045               // Field mindustry/world/Tile.y:S
      56: invokespecial #2216               // Method mindustry/entities/units/BuildPlan."<init>":(II)V
      59: invokevirtual #2163               // Method mindustry/gen/Unit.addBuild:(Lmindustry/entities/units/BuildPlan;)V
      62: return

  public void drawArrow(mindustry.world.Block, int, int, int);
    Code:
       0: aload_0
       1: aload_1
       2: iload_2
       3: iload_3
       4: iload         4
       6: aload_0
       7: iload_2
       8: iload_3
       9: aload_1
      10: iload         4
      12: invokevirtual #2165               // Method validPlace:(IILmindustry/world/Block;I)Z
      15: invokevirtual #2639               // Method drawArrow:(Lmindustry/world/Block;IIIZ)V
      18: return

  public void drawArrow(mindustry.world.Block, int, int, int, boolean);
    Code:
       0: aload_1
       1: getfield      #860                // Field mindustry/world/Block.size:I
       4: iconst_2
       5: idiv
       6: bipush        8
       8: imul
       9: i2f
      10: fstore        6
      12: iload         4
      14: invokestatic  #2643               // Method arc/math/geom/Geometry.d4:(I)Larc/math/geom/Point2;
      17: getfield      #2649               // Field arc/math/geom/Point2.x:I
      20: istore        7
      22: iload         4
      24: invokestatic  #2643               // Method arc/math/geom/Geometry.d4:(I)Larc/math/geom/Point2;
      27: getfield      #2650               // Field arc/math/geom/Point2.y:I
      30: istore        8
      32: iload_2
      33: bipush        8
      35: imul
      36: i2f
      37: aload_1
      38: getfield      #1918               // Field mindustry/world/Block.offset:F
      41: fadd
      42: iload         7
      44: i2f
      45: fload         6
      47: fmul
      48: fadd
      49: fstore        9
      51: iload_3
      52: bipush        8
      54: imul
      55: i2f
      56: aload_1
      57: getfield      #1918               // Field mindustry/world/Block.offset:F
      60: fadd
      61: iload         8
      63: i2f
      64: fload         6
      66: fmul
      67: fadd
      68: fstore        10
      70: iload         5
      72: ifne          81
      75: getstatic     #2066               // Field mindustry/graphics/Pal.removeBack:Larc/graphics/Color;
      78: goto          84
      81: getstatic     #2102               // Field mindustry/graphics/Pal.accentBack:Larc/graphics/Color;
      84: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
      87: getstatic     #2651               // Field arc/Core.atlas:Larc/graphics/g2d/TextureAtlas;
      90: ldc_w         #2655               // String place-arrow
      93: invokevirtual #2657               // Method arc/graphics/g2d/TextureAtlas.find:(Ljava/lang/String;)Larc/graphics/g2d/TextureAtlas$AtlasRegion;
      96: astore        11
      98: aload         11
     100: fload         9
     102: fload         10
     104: fconst_1
     105: fsub
     106: aload         11
     108: getfield      #2662               // Field arc/graphics/g2d/TextureRegion.width:I
     111: i2f
     112: aload         11
     114: invokevirtual #2664               // Method arc/graphics/g2d/TextureRegion.scl:()F
     117: fmul
     118: aload         11
     120: getfield      #2666               // Field arc/graphics/g2d/TextureRegion.height:I
     123: i2f
     124: aload         11
     126: invokevirtual #2664               // Method arc/graphics/g2d/TextureRegion.scl:()F
     129: fmul
     130: iload         4
     132: bipush        90
     134: imul
     135: bipush        90
     137: isub
     138: i2f
     139: invokestatic  #2668               // Method arc/graphics/g2d/Draw.rect:(Larc/graphics/g2d/TextureRegion;FFFFF)V
     142: iload         5
     144: ifne          153
     147: getstatic     #1605               // Field mindustry/graphics/Pal.remove:Larc/graphics/Color;
     150: goto          156
     153: getstatic     #1609               // Field mindustry/graphics/Pal.accent:Larc/graphics/Color;
     156: invokestatic  #1719               // Method arc/graphics/g2d/Draw.color:(Larc/graphics/Color;)V
     159: aload         11
     161: fload         9
     163: fload         10
     165: aload         11
     167: getfield      #2662               // Field arc/graphics/g2d/TextureRegion.width:I
     170: i2f
     171: aload         11
     173: invokevirtual #2664               // Method arc/graphics/g2d/TextureRegion.scl:()F
     176: fmul
     177: aload         11
     179: getfield      #2666               // Field arc/graphics/g2d/TextureRegion.height:I
     182: i2f
     183: aload         11
     185: invokevirtual #2664               // Method arc/graphics/g2d/TextureRegion.scl:()F
     188: fmul
     189: iload         4
     191: bipush        90
     193: imul
     194: bipush        90
     196: isub
     197: i2f
     198: invokestatic  #2668               // Method arc/graphics/g2d/Draw.rect:(Larc/graphics/g2d/TextureRegion;FFFFF)V
     201: return

  void iterateLine(int, int, int, int, arc.func.Cons<mindustry.input.InputHandler$PlaceLine>);
    Code:
       0: getstatic     #1485               // Field arc/Core.input:Larc/Input;
       3: getstatic     #2671               // Field mindustry/input/Binding.diagonalPlacement:Larc/input/KeyBind;
       6: invokevirtual #2433               // Method arc/Input.keyDown:(Larc/input/KeyBind;)Z
       9: istore        7
      11: getstatic     #2240               // Field arc/Core.settings:Larc/Settings;
      14: ldc_w         #2674               // String swapdiagonal
      17: invokevirtual #2246               // Method arc/Settings.getBool:(Ljava/lang/String;)Z
      20: ifeq          41
      23: getstatic     #2676               // Field mindustry/Vars.mobile:Z
      26: ifeq          41
      29: iload         7
      31: ifne          38
      34: iconst_1
      35: goto          39
      38: iconst_0
      39: istore        7
      41: aload_0
      42: getfield      #1421               // Field block:Lmindustry/world/Block;
      45: ifnull        70
      48: aload_0
      49: getfield      #1421               // Field block:Lmindustry/world/Block;
      52: getfield      #2679               // Field mindustry/world/Block.swapDiagonalPlacement:Z
      55: ifeq          70
      58: iload         7
      60: ifne          67
      63: iconst_1
      64: goto          68
      67: iconst_0
      68: istore        7
      70: iconst_m1
      71: istore        8
      73: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      76: iload_1
      77: iload_2
      78: invokevirtual #2682               // Method mindustry/core/World.build:(II)Lmindustry/gen/Building;
      81: astore        9
      83: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
      86: iload_3
      87: iload         4
      89: invokevirtual #2682               // Method mindustry/core/World.build:(II)Lmindustry/gen/Building;
      92: astore        10
      94: iload         7
      96: ifeq          217
      99: aload_0
     100: getfield      #1421               // Field block:Lmindustry/world/Block;
     103: ifnull        116
     106: aload_0
     107: getfield      #1421               // Field block:Lmindustry/world/Block;
     110: getfield      #2685               // Field mindustry/world/Block.allowDiagonal:Z
     113: ifeq          217
     116: aload_0
     117: getfield      #1421               // Field block:Lmindustry/world/Block;
     120: ifnull        182
     123: aload         9
     125: instanceof    #2688               // class mindustry/world/blocks/distribution/ChainedBuilding
     128: ifeq          182
     131: aload         10
     133: instanceof    #2688               // class mindustry/world/blocks/distribution/ChainedBuilding
     136: ifeq          182
     139: aload_0
     140: getfield      #1421               // Field block:Lmindustry/world/Block;
     143: aload         10
     145: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     148: invokevirtual #2690               // Method mindustry/world/Block.canReplace:(Lmindustry/world/Block;)Z
     151: ifeq          182
     154: aload_0
     155: getfield      #1421               // Field block:Lmindustry/world/Block;
     158: aload         9
     160: getfield      #856                // Field mindustry/gen/Building.block:Lmindustry/world/Block;
     163: invokevirtual #2690               // Method mindustry/world/Block.canReplace:(Lmindustry/world/Block;)Z
     166: ifeq          182
     169: iload_1
     170: iload_2
     171: iload_3
     172: iload         4
     174: invokestatic  #2694               // Method mindustry/input/Placement.upgradeLine:(IIII)Larc/struct/Seq;
     177: astore        6
     179: goto          264
     182: aload_0
     183: getfield      #1421               // Field block:Lmindustry/world/Block;
     186: ifnull        203
     189: aload_0
     190: getfield      #1421               // Field block:Lmindustry/world/Block;
     193: getfield      #2698               // Field mindustry/world/Block.conveyorPlacement:Z
     196: ifeq          203
     199: iconst_1
     200: goto          204
     203: iconst_0
     204: iload_1
     205: iload_2
     206: iload_3
     207: iload         4
     209: invokestatic  #2701               // Method mindustry/input/Placement.pathfindLine:(ZIIII)Larc/struct/Seq;
     212: astore        6
     214: goto          264
     217: aload_0
     218: getfield      #1421               // Field block:Lmindustry/world/Block;
     221: ifnull        254
     224: aload_0
     225: getfield      #1421               // Field block:Lmindustry/world/Block;
     228: getfield      #2705               // Field mindustry/world/Block.allowRectanglePlacement:Z
     231: ifeq          254
     234: iload_1
     235: iload_2
     236: iload_3
     237: iload         4
     239: aload_0
     240: getfield      #1421               // Field block:Lmindustry/world/Block;
     243: getfield      #860                // Field mindustry/world/Block.size:I
     246: invokestatic  #2708               // Method mindustry/input/Placement.normalizeRectangle:(IIIII)Larc/struct/Seq;
     249: astore        6
     251: goto          264
     254: iload_1
     255: iload_2
     256: iload_3
     257: iload         4
     259: invokestatic  #2712               // Method mindustry/input/Placement.normalizeLine:(IIII)Larc/struct/Seq;
     262: astore        6
     264: aload         6
     266: getfield      #596                // Field arc/struct/Seq.size:I
     269: iconst_1
     270: if_icmple     327
     273: aload         10
     275: instanceof    #2688               // class mindustry/world/blocks/distribution/ChainedBuilding
     278: ifeq          327
     281: aload         6
     283: aload         6
     285: getfield      #596                // Field arc/struct/Seq.size:I
     288: iconst_2
     289: isub
     290: invokevirtual #1577               // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     293: checkcast     #410                // class arc/math/geom/Point2
     296: astore        11
     298: getstatic     #210                // Field mindustry/Vars.world:Lmindustry/core/World;
     301: aload         11
     303: getfield      #2649               // Field arc/math/geom/Point2.x:I
     306: aload         11
     308: getfield      #2650               // Field arc/math/geom/Point2.y:I
     311: invokevirtual #2682               // Method mindustry/core/World.build:(II)Lmindustry/gen/Building;
     314: instanceof    #2688               // class mindustry/world/blocks/distribution/ChainedBuilding
     317: ifne          327
     320: aload         10
     322: getfield      #1053               // Field mindustry/gen/Building.rotation:I
     325: istore        8
     327: aload_0
     328: getfield      #1421               // Field block:Lmindustry/world/Block;
     331: ifnull        349
     334: aload_0
     335: getfield      #1421               // Field block:Lmindustry/world/Block;
     338: aload         6
     340: aload_0
     341: getfield      #53                 // Field rotation:I
     344: iload         7
     346: invokevirtual #2715               // Method mindustry/world/Block.changePlacementPath:(Larc/struct/Seq;IZ)V
     349: iload_1
     350: i2f
     351: iload_2
     352: i2f
     353: iload_3
     354: i2f
     355: iload         4
     357: i2f
     358: invokestatic  #2719               // Method arc/math/Angles.angle:(FFFF)F
     361: fstore        11
     363: aload_0
     364: getfield      #53                 // Field rotation:I
     367: istore        12
     369: aload_0
     370: getfield      #2724               // Field overrideLineRotation:Z
     373: ifeq          381
     376: iload         7
     378: ifeq          414
     381: iload_1
     382: iload_3
     383: if_icmpne     399
     386: iload_2
     387: iload         4
     389: if_icmpne     399
     392: aload_0
     393: getfield      #53                 // Field rotation:I
     396: goto          412
     399: fload         11
     401: ldc_w         #2727               // float 45.0f
     404: fadd
     405: ldc_w         #2728               // float 90.0f
     408: fdiv
     409: f2i
     410: iconst_4
     411: irem
     412: istore        12
     414: getstatic     #1867               // Field arc/util/Tmp.r3:Larc/math/geom/Rect;
     417: ldc           #23                 // float -1.0f
     419: ldc           #23                 // float -1.0f
     421: fconst_0
     422: fconst_0
     423: invokevirtual #2058               // Method arc/math/geom/Rect.set:(FFFF)Larc/math/geom/Rect;
     426: pop
     427: iconst_0
     428: istore        13
     430: iload         13
     432: aload         6
     434: getfield      #596                // Field arc/struct/Seq.size:I
     437: if_icmpge     836
     440: aload         6
     442: iload         13
     444: invokevirtual #1577               // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     447: checkcast     #410                // class arc/math/geom/Point2
     450: astore        14
     452: aload_0
     453: getfield      #1421               // Field block:Lmindustry/world/Block;
     456: ifnull        525
     459: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
     462: aload_0
     463: getfield      #1421               // Field block:Lmindustry/world/Block;
     466: getfield      #860                // Field mindustry/world/Block.size:I
     469: bipush        8
     471: imul
     472: i2f
     473: invokevirtual #1987               // Method arc/math/geom/Rect.setSize:(F)Larc/math/geom/Rect;
     476: aload         14
     478: getfield      #2649               // Field arc/math/geom/Point2.x:I
     481: bipush        8
     483: imul
     484: i2f
     485: aload_0
     486: getfield      #1421               // Field block:Lmindustry/world/Block;
     489: getfield      #1918               // Field mindustry/world/Block.offset:F
     492: fadd
     493: aload         14
     495: getfield      #2650               // Field arc/math/geom/Point2.y:I
     498: bipush        8
     500: imul
     501: i2f
     502: aload_0
     503: getfield      #1421               // Field block:Lmindustry/world/Block;
     506: getfield      #1918               // Field mindustry/world/Block.offset:F
     509: fadd
     510: invokevirtual #1991               // Method arc/math/geom/Rect.setCenter:(FF)Larc/math/geom/Rect;
     513: getstatic     #1867               // Field arc/util/Tmp.r3:Larc/math/geom/Rect;
     516: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     519: ifeq          525
     522: goto          830
     525: iload         13
     527: aload         6
     529: getfield      #596                // Field arc/struct/Seq.size:I
     532: iconst_1
     533: isub
     534: if_icmpne     541
     537: aconst_null
     538: goto          553
     541: aload         6
     543: iload         13
     545: iconst_1
     546: iadd
     547: invokevirtual #1577               // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     550: checkcast     #410                // class arc/math/geom/Point2
     553: astore        15
     555: aload_0
     556: getfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
     559: aload         14
     561: getfield      #2649               // Field arc/math/geom/Point2.x:I
     564: putfield      #2729               // Field mindustry/input/InputHandler$PlaceLine.x:I
     567: aload_0
     568: getfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
     571: aload         14
     573: getfield      #2650               // Field arc/math/geom/Point2.y:I
     576: putfield      #2730               // Field mindustry/input/InputHandler$PlaceLine.y:I
     579: aload_0
     580: getfield      #2724               // Field overrideLineRotation:Z
     583: ifeq          591
     586: iload         7
     588: ifeq          736
     591: aload_0
     592: getfield      #1421               // Field block:Lmindustry/world/Block;
     595: ifnull        614
     598: aload_0
     599: getfield      #1421               // Field block:Lmindustry/world/Block;
     602: getfield      #2731               // Field mindustry/world/Block.ignoreLineRotation:Z
     605: ifeq          614
     608: getstatic     #2676               // Field mindustry/Vars.mobile:Z
     611: ifeq          736
     614: iload         12
     616: istore        16
     618: aload         15
     620: ifnull        651
     623: aload         14
     625: getfield      #2649               // Field arc/math/geom/Point2.x:I
     628: aload         14
     630: getfield      #2650               // Field arc/math/geom/Point2.y:I
     633: aload         15
     635: getfield      #2649               // Field arc/math/geom/Point2.x:I
     638: aload         15
     640: getfield      #2650               // Field arc/math/geom/Point2.y:I
     643: invokestatic  #2734               // Method mindustry/world/Tile.relativeTo:(IIII)B
     646: istore        16
     648: goto          718
     651: iload         8
     653: iconst_m1
     654: if_icmpeq     664
     657: iload         8
     659: istore        16
     661: goto          718
     664: aload_0
     665: getfield      #1421               // Field block:Lmindustry/world/Block;
     668: getfield      #2698               // Field mindustry/world/Block.conveyorPlacement:Z
     671: ifeq          718
     674: iload         13
     676: ifle          718
     679: aload         6
     681: iload         13
     683: iconst_1
     684: isub
     685: invokevirtual #1577               // Method arc/struct/Seq.get:(I)Ljava/lang/Object;
     688: checkcast     #410                // class arc/math/geom/Point2
     691: astore        17
     693: aload         17
     695: getfield      #2649               // Field arc/math/geom/Point2.x:I
     698: aload         17
     700: getfield      #2650               // Field arc/math/geom/Point2.y:I
     703: aload         14
     705: getfield      #2649               // Field arc/math/geom/Point2.x:I
     708: aload         14
     710: getfield      #2650               // Field arc/math/geom/Point2.y:I
     713: invokestatic  #2734               // Method mindustry/world/Tile.relativeTo:(IIII)B
     716: istore        16
     718: iload         16
     720: iconst_m1
     721: if_icmpeq     733
     724: aload_0
     725: getfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
     728: iload         16
     730: putfield      #2738               // Field mindustry/input/InputHandler$PlaceLine.rotation:I
     733: goto          747
     736: aload_0
     737: getfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
     740: aload_0
     741: getfield      #53                 // Field rotation:I
     744: putfield      #2738               // Field mindustry/input/InputHandler$PlaceLine.rotation:I
     747: aload_0
     748: getfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
     751: aload         15
     753: ifnonnull     760
     756: iconst_1
     757: goto          761
     760: iconst_0
     761: putfield      #2739               // Field mindustry/input/InputHandler$PlaceLine.last:Z
     764: aload         5
     766: aload_0
     767: getfield      #70                 // Field line:Lmindustry/input/InputHandler$PlaceLine;
     770: invokeinterface #2742,  2         // InterfaceMethod arc/func/Cons.get:(Ljava/lang/Object;)V
     775: getstatic     #1867               // Field arc/util/Tmp.r3:Larc/math/geom/Rect;
     778: aload_0
     779: getfield      #1421               // Field block:Lmindustry/world/Block;
     782: getfield      #860                // Field mindustry/world/Block.size:I
     785: bipush        8
     787: imul
     788: i2f
     789: invokevirtual #1987               // Method arc/math/geom/Rect.setSize:(F)Larc/math/geom/Rect;
     792: aload         14
     794: getfield      #2649               // Field arc/math/geom/Point2.x:I
     797: bipush        8
     799: imul
     800: i2f
     801: aload_0
     802: getfield      #1421               // Field block:Lmindustry/world/Block;
     805: getfield      #1918               // Field mindustry/world/Block.offset:F
     808: fadd
     809: aload         14
     811: getfield      #2650               // Field arc/math/geom/Point2.y:I
     814: bipush        8
     816: imul
     817: i2f
     818: aload_0
     819: getfield      #1421               // Field block:Lmindustry/world/Block;
     822: getfield      #1918               // Field mindustry/world/Block.offset:F
     825: fadd
     826: invokevirtual #1991               // Method arc/math/geom/Rect.setCenter:(FF)Larc/math/geom/Rect;
     829: pop
     830: iinc          13, 1
     833: goto          430
     836: return

  private static boolean lambda$static$59(mindustry.entities.units.BuildPlan);
    Code:
       0: aload_0
       1: getstatic     #2617               // Field vpIgnore:Lmindustry/entities/units/BuildPlan;
       4: if_acmpeq     51
       7: aload_0
       8: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
      11: ifne          51
      14: getstatic     #2620               // Field vpBlock:Lmindustry/world/Block;
      17: aload_0
      18: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      21: invokevirtual #2690               // Method mindustry/world/Block.canReplace:(Lmindustry/world/Block;)Z
      24: ifeq          47
      27: aload_0
      28: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      31: getstatic     #2623               // Field vpX:I
      34: if_icmpne     47
      37: aload_0
      38: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      41: getstatic     #2626               // Field vpY:I
      44: if_icmpeq     51
      47: iconst_1
      48: goto          52
      51: iconst_0
      52: ireturn

  private static boolean lambda$add$58(arc.input.InputProcessor);
    Code:
       0: aload_0
       1: instanceof    #13                 // class mindustry/input/InputHandler
       4: ifne          27
       7: aload_0
       8: instanceof    #2527               // class arc/input/GestureDetector
      11: ifeq          31
      14: aload_0
      15: checkcast     #2527               // class arc/input/GestureDetector
      18: invokevirtual #2746               // Method arc/input/GestureDetector.getListener:()Larc/input/GestureDetector$GestureListener;
      21: instanceof    #13                 // class mindustry/input/InputHandler
      24: ifeq          31
      27: iconst_1
      28: goto          32
      31: iconst_0
      32: ireturn

  private static boolean lambda$selectedCommandUnits$57(mindustry.gen.Unit);
    Code:
       0: iconst_1
       1: ireturn

  private static boolean lambda$selectedCommandUnits$56(arc.func.Boolf, mindustry.gen.Unit);
    Code:
       0: aload_1
       1: invokevirtual #2750               // Method mindustry/gen/Unit.isCommandable:()Z
       4: ifeq          17
       7: aload_0
       8: aload_1
       9: invokeinterface #2004,  2         // InterfaceMethod arc/func/Boolf.get:(Ljava/lang/Object;)Z
      14: ifne          21
      17: iconst_1
      18: goto          22
      21: iconst_0
      22: ireturn

  private static void lambda$selectedCommandBuildings$55(mindustry.gen.Building);
    Code:
       0: aload_0
       1: invokevirtual #718                // Method mindustry/gen/Building.isCommandable:()Z
       4: ifeq          15
       7: getstatic     #2481               // Field tmpBuildings:Larc/struct/Seq;
      10: aload_0
      11: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
      14: pop
      15: return

  private static float lambda$selectedEnemyUnit$54(float, float, mindustry.gen.Unit);
    Code:
       0: aload_2
       1: fload_0
       2: fload_1
       3: invokevirtual #2751               // Method mindustry/gen/Unit.dst:(FF)F
       6: aload_2
       7: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
      10: fconst_2
      11: fdiv
      12: fsub
      13: freturn

  private static boolean lambda$selectedEnemyUnit$53(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       4: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
       7: invokevirtual #2754               // Method mindustry/gen/Unit.inFogTo:(Lmindustry/game/Team;)Z
      10: ifne          17
      13: iconst_1
      14: goto          18
      17: iconst_0
      18: ireturn

  private static float lambda$selectedCommandUnit$52(float, float, mindustry.gen.Unit);
    Code:
       0: aload_2
       1: fload_0
       2: fload_1
       3: invokevirtual #2751               // Method mindustry/gen/Unit.dst:(FF)F
       6: aload_2
       7: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
      10: fconst_2
      11: fdiv
      12: fsub
      13: freturn

  private static boolean lambda$selectedCommandUnit$51(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: invokevirtual #2750               // Method mindustry/gen/Unit.isCommandable:()Z
       4: ireturn

  private static boolean lambda$selectedUnit$50(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: invokevirtual #838                // Method mindustry/gen/Unit.isAI:()Z
       4: ifeq          18
       7: aload_0
       8: invokevirtual #1187               // Method mindustry/gen/Unit.playerControllable:()Z
      11: ifeq          18
      14: iconst_1
      15: goto          19
      18: iconst_0
      19: ireturn

  private void lambda$updateLine$49(mindustry.entities.units.BuildPlan);
    Code:
       0: aload_1
       1: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
       4: aload_1
       5: aload_0
       6: getfield      #82                 // Field linePlans:Larc/struct/Seq;
       9: invokevirtual #2757               // Method mindustry/world/Block.getReplacement:(Lmindustry/entities/units/BuildPlan;Larc/struct/Seq;)Lmindustry/world/Block;
      12: astore_2
      13: aload_2
      14: invokevirtual #2761               // Method mindustry/world/Block.unlockedNow:()Z
      17: ifeq          25
      20: aload_1
      21: aload_2
      22: putfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      25: return

  private void lambda$updateLine$48(mindustry.input.InputHandler$PlaceLine);
    Code:
       0: aload_0
       1: aload_1
       2: getfield      #2738               // Field mindustry/input/InputHandler$PlaceLine.rotation:I
       5: putfield      #53                 // Field rotation:I
       8: new           #74                 // class mindustry/entities/units/BuildPlan
      11: dup
      12: aload_1
      13: getfield      #2729               // Field mindustry/input/InputHandler$PlaceLine.x:I
      16: aload_1
      17: getfield      #2730               // Field mindustry/input/InputHandler$PlaceLine.y:I
      20: aload_1
      21: getfield      #2738               // Field mindustry/input/InputHandler$PlaceLine.rotation:I
      24: aload_0
      25: getfield      #1421               // Field block:Lmindustry/world/Block;
      28: aload_0
      29: getfield      #1421               // Field block:Lmindustry/world/Block;
      32: invokevirtual #2764               // Method mindustry/world/Block.nextConfig:()Ljava/lang/Object;
      35: invokespecial #2368               // Method mindustry/entities/units/BuildPlan."<init>":(IIILmindustry/world/Block;Ljava/lang/Object;)V
      38: astore_2
      39: aload_2
      40: fconst_1
      41: putfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
      44: aload_0
      45: getfield      #82                 // Field linePlans:Larc/struct/Seq;
      48: aload_2
      49: invokevirtual #602                // Method arc/struct/Seq.add:(Ljava/lang/Object;)Larc/struct/Seq;
      52: pop
      53: return

  private static boolean lambda$removeSelection$47(mindustry.world.Tile, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_1
       1: invokevirtual #2767               // Method mindustry/entities/units/BuildPlan.tile:()Lmindustry/world/Tile;
       4: ifnull        19
       7: aload_1
       8: invokevirtual #2767               // Method mindustry/entities/units/BuildPlan.tile:()Lmindustry/world/Tile;
      11: aload_0
      12: if_acmpne     19
      15: iconst_1
      16: goto          20
      19: iconst_0
      20: ireturn

  private static boolean lambda$getPlan$46(mindustry.entities.units.BuildPlan, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_1
       1: aload_0
       2: if_acmpne     7
       5: iconst_0
       6: ireturn
       7: aload_1
       8: invokevirtual #2767               // Method mindustry/entities/units/BuildPlan.tile:()Lmindustry/world/Tile;
      11: astore_2
      12: aload_2
      13: ifnonnull     18
      16: iconst_0
      17: ireturn
      18: aload_1
      19: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
      22: ifne          77
      25: getstatic     #2769               // Field r1:Larc/math/geom/Rect;
      28: aload_1
      29: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      32: getfield      #860                // Field mindustry/world/Block.size:I
      35: bipush        8
      37: imul
      38: i2f
      39: invokevirtual #1987               // Method arc/math/geom/Rect.setSize:(F)Larc/math/geom/Rect;
      42: pop
      43: getstatic     #2769               // Field r1:Larc/math/geom/Rect;
      46: aload_2
      47: invokevirtual #2770               // Method mindustry/world/Tile.worldx:()F
      50: aload_1
      51: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      54: getfield      #1918               // Field mindustry/world/Block.offset:F
      57: fadd
      58: aload_2
      59: invokevirtual #2773               // Method mindustry/world/Tile.worldy:()F
      62: aload_1
      63: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      66: getfield      #1918               // Field mindustry/world/Block.offset:F
      69: fadd
      70: invokevirtual #1991               // Method arc/math/geom/Rect.setCenter:(FF)Larc/math/geom/Rect;
      73: pop
      74: goto          126
      77: getstatic     #2769               // Field r1:Larc/math/geom/Rect;
      80: aload_2
      81: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
      84: getfield      #860                // Field mindustry/world/Block.size:I
      87: bipush        8
      89: imul
      90: i2f
      91: invokevirtual #1987               // Method arc/math/geom/Rect.setSize:(F)Larc/math/geom/Rect;
      94: pop
      95: getstatic     #2769               // Field r1:Larc/math/geom/Rect;
      98: aload_2
      99: invokevirtual #2770               // Method mindustry/world/Tile.worldx:()F
     102: aload_2
     103: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
     106: getfield      #1918               // Field mindustry/world/Block.offset:F
     109: fadd
     110: aload_2
     111: invokevirtual #2773               // Method mindustry/world/Tile.worldy:()F
     114: aload_2
     115: invokevirtual #1939               // Method mindustry/world/Tile.block:()Lmindustry/world/Block;
     118: getfield      #1918               // Field mindustry/world/Block.offset:F
     121: fadd
     122: invokevirtual #1991               // Method arc/math/geom/Rect.setCenter:(FF)Larc/math/geom/Rect;
     125: pop
     126: getstatic     #1986               // Field r2:Larc/math/geom/Rect;
     129: getstatic     #2769               // Field r1:Larc/math/geom/Rect;
     132: invokevirtual #1880               // Method arc/math/geom/Rect.overlaps:(Larc/math/geom/Rect;)Z
     135: ireturn

  private static void lambda$flipPlans$45(boolean, int, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_2
       1: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
       4: ifeq          8
       7: return
       8: iload_0
       9: ifeq          19
      12: aload_2
      13: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      16: goto          23
      19: aload_2
      20: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      23: bipush        8
      25: imul
      26: iload_1
      27: isub
      28: i2f
      29: aload_2
      30: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      33: getfield      #1918               // Field mindustry/world/Block.offset:F
      36: fadd
      37: fneg
      38: iload_1
      39: i2f
      40: fadd
      41: fstore_3
      42: iload_0
      43: ifeq          67
      46: aload_2
      47: fload_3
      48: aload_2
      49: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      52: getfield      #1918               // Field mindustry/world/Block.offset:F
      55: fsub
      56: ldc_w         #1755               // float 8.0f
      59: fdiv
      60: f2i
      61: putfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      64: goto          85
      67: aload_2
      68: fload_3
      69: aload_2
      70: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      73: getfield      #1918               // Field mindustry/world/Block.offset:F
      76: fsub
      77: ldc_w         #1755               // float 8.0f
      80: fdiv
      81: f2i
      82: putfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      85: aload_2
      86: iload_0
      87: aload_2
      88: invokedynamic #2776,  0           // InvokeDynamic #56:get:(ZLmindustry/entities/units/BuildPlan;)Larc/func/Cons;
      93: invokevirtual #2779               // Method mindustry/entities/units/BuildPlan.pointConfig:(Larc/func/Cons;)V
      96: aload_2
      97: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     100: aload_2
     101: iload_0
     102: invokevirtual #2782               // Method mindustry/world/Block.flipRotation:(Lmindustry/entities/units/BuildPlan;Z)V
     105: return

  private static void lambda$flipPlans$44(boolean, mindustry.entities.units.BuildPlan, arc.math.geom.Point2);
    Code:
       0: iload_0
       1: ifeq          38
       4: aload_1
       5: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
       8: getfield      #860                // Field mindustry/world/Block.size:I
      11: iconst_2
      12: irem
      13: ifne          26
      16: aload_2
      17: dup
      18: getfield      #2649               // Field arc/math/geom/Point2.x:I
      21: iconst_1
      22: isub
      23: putfield      #2649               // Field arc/math/geom/Point2.x:I
      26: aload_2
      27: aload_2
      28: getfield      #2649               // Field arc/math/geom/Point2.x:I
      31: ineg
      32: putfield      #2649               // Field arc/math/geom/Point2.x:I
      35: goto          69
      38: aload_1
      39: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      42: getfield      #860                // Field mindustry/world/Block.size:I
      45: iconst_2
      46: irem
      47: ifne          60
      50: aload_2
      51: dup
      52: getfield      #2650               // Field arc/math/geom/Point2.y:I
      55: iconst_1
      56: isub
      57: putfield      #2650               // Field arc/math/geom/Point2.y:I
      60: aload_2
      61: aload_2
      62: getfield      #2650               // Field arc/math/geom/Point2.y:I
      65: ineg
      66: putfield      #2650               // Field arc/math/geom/Point2.y:I
      69: return

  private static void lambda$rotatePlans$43(int, int, int, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_3
       1: getfield      #1339               // Field mindustry/entities/units/BuildPlan.breaking:Z
       4: ifeq          8
       7: return
       8: aload_3
       9: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      12: getfield      #860                // Field mindustry/world/Block.size:I
      15: iconst_2
      16: irem
      17: ifne          26
      20: ldc_w         #2785               // float -0.5f
      23: goto          27
      26: fconst_0
      27: fstore        4
      29: aload_3
      30: fload         4
      32: iload_0
      33: invokedynamic #2786,  0           // InvokeDynamic #57:get:(FI)Larc/func/Cons;
      38: invokevirtual #2779               // Method mindustry/entities/units/BuildPlan.pointConfig:(Larc/func/Cons;)V
      41: aload_3
      42: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      45: iload_1
      46: isub
      47: bipush        8
      49: imul
      50: i2f
      51: aload_3
      52: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      55: getfield      #1918               // Field mindustry/world/Block.offset:F
      58: fadd
      59: fstore        5
      61: aload_3
      62: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      65: iload_2
      66: isub
      67: bipush        8
      69: imul
      70: i2f
      71: aload_3
      72: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      75: getfield      #1918               // Field mindustry/world/Block.offset:F
      78: fadd
      79: fstore        6
      81: fload         5
      83: fstore        7
      85: iload_0
      86: iflt          101
      89: fload         6
      91: fneg
      92: fstore        5
      94: fload         7
      96: fstore        6
      98: goto          110
     101: fload         6
     103: fstore        5
     105: fload         7
     107: fneg
     108: fstore        6
     110: aload_3
     111: fload         5
     113: aload_3
     114: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     117: getfield      #1918               // Field mindustry/world/Block.offset:F
     120: fsub
     121: invokestatic  #2417               // Method mindustry/core/World.toTile:(F)I
     124: iload_1
     125: iadd
     126: putfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
     129: aload_3
     130: fload         6
     132: aload_3
     133: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     136: getfield      #1918               // Field mindustry/world/Block.offset:F
     139: fsub
     140: invokestatic  #2417               // Method mindustry/core/World.toTile:(F)I
     143: iload_2
     144: iadd
     145: putfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
     148: aload_3
     149: aload_3
     150: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     153: aload_3
     154: getfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
     157: iload_0
     158: iadd
     159: iconst_4
     160: invokestatic  #1058               // Method arc/math/Mathf.mod:(II)I
     163: invokevirtual #2789               // Method mindustry/world/Block.planRotation:(I)I
     166: putfield      #1852               // Field mindustry/entities/units/BuildPlan.rotation:I
     169: return

  private static void lambda$rotatePlans$42(float, int, arc.math.geom.Point2);
    Code:
       0: aload_2
       1: getfield      #2649               // Field arc/math/geom/Point2.x:I
       4: i2f
       5: fload_0
       6: fadd
       7: fstore_3
       8: aload_2
       9: getfield      #2650               // Field arc/math/geom/Point2.y:I
      12: i2f
      13: fload_0
      14: fadd
      15: fstore        4
      17: fload_3
      18: fstore        5
      20: iload_1
      21: iflt          35
      24: fload         4
      26: fneg
      27: fstore_3
      28: fload         5
      30: fstore        4
      32: goto          43
      35: fload         4
      37: fstore_3
      38: fload         5
      40: fneg
      41: fstore        4
      43: aload_2
      44: fload_3
      45: fload_0
      46: fsub
      47: invokestatic  #2792               // Method arc/math/Mathf.floor:(F)I
      50: fload         4
      52: fload_0
      53: fsub
      54: invokestatic  #2792               // Method arc/math/Mathf.floor:(F)I
      57: invokevirtual #2794               // Method arc/math/geom/Point2.set:(II)Larc/math/geom/Point2;
      60: pop
      61: return

  private static void lambda$showSchematicSave$41(mindustry.game.Schematic, java.lang.String);
    Code:
       0: getstatic     #2797               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
       3: invokevirtual #2801               // Method mindustry/game/Schematics.all:()Larc/struct/Seq;
       6: aload_1
       7: invokedynamic #2806,  0           // InvokeDynamic #58:get:(Ljava/lang/String;)Larc/func/Boolf;
      12: invokevirtual #2008               // Method arc/struct/Seq.find:(Larc/func/Boolf;)Ljava/lang/Object;
      15: checkcast     #2809               // class mindustry/game/Schematic
      18: astore_2
      19: aload_2
      20: ifnull        45
      23: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
      26: ldc_w         #2811               // String @confirm
      29: ldc_w         #2813               // String @schematic.replace
      32: aload_2
      33: aload_0
      34: invokedynamic #2815,  0           // InvokeDynamic #59:run:(Lmindustry/game/Schematic;Lmindustry/game/Schematic;)Ljava/lang/Runnable;
      39: invokevirtual #2818               // Method mindustry/core/UI.showConfirm:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Runnable;)V
      42: goto          108
      45: aload_0
      46: getfield      #2822               // Field mindustry/game/Schematic.tags:Larc/struct/StringMap;
      49: ldc_w         #2826               // String name
      52: aload_1
      53: invokevirtual #2827               // Method arc/struct/StringMap.put:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
      56: pop
      57: aload_0
      58: getfield      #2822               // Field mindustry/game/Schematic.tags:Larc/struct/StringMap;
      61: ldc_w         #2833               // String description
      64: ldc_w         #1954               // String
      67: invokevirtual #2827               // Method arc/struct/StringMap.put:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
      70: pop
      71: getstatic     #2797               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
      74: aload_0
      75: invokevirtual #2835               // Method mindustry/game/Schematics.add:(Lmindustry/game/Schematic;)V
      78: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
      81: ldc_w         #2838               // String @schematic.saved
      84: invokevirtual #2840               // Method mindustry/core/UI.showInfoFade:(Ljava/lang/String;)V
      87: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
      90: getfield      #2844               // Field mindustry/core/UI.schematics:Lmindustry/ui/dialogs/SchematicsDialog;
      93: aload_0
      94: invokevirtual #2847               // Method mindustry/ui/dialogs/SchematicsDialog.showInfo:(Lmindustry/game/Schematic;)V
      97: new           #2852               // class mindustry/game/EventType$SchematicCreateEvent
     100: dup
     101: aload_0
     102: invokespecial #2854               // Method mindustry/game/EventType$SchematicCreateEvent."<init>":(Lmindustry/game/Schematic;)V
     105: invokestatic  #733                // Method arc/Events.fire:(Ljava/lang/Object;)V
     108: return

  private static void lambda$showSchematicSave$40(mindustry.game.Schematic, mindustry.game.Schematic);
    Code:
       0: getstatic     #2797               // Field mindustry/Vars.schematics:Lmindustry/game/Schematics;
       3: aload_0
       4: aload_1
       5: invokevirtual #2856               // Method mindustry/game/Schematics.overwrite:(Lmindustry/game/Schematic;Lmindustry/game/Schematic;)V
       8: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
      11: ldc_w         #2838               // String @schematic.saved
      14: invokevirtual #2840               // Method mindustry/core/UI.showInfoFade:(Ljava/lang/String;)V
      17: getstatic     #1394               // Field mindustry/Vars.ui:Lmindustry/core/UI;
      20: getfield      #2844               // Field mindustry/core/UI.schematics:Lmindustry/ui/dialogs/SchematicsDialog;
      23: aload_0
      24: invokevirtual #2847               // Method mindustry/ui/dialogs/SchematicsDialog.showInfo:(Lmindustry/game/Schematic;)V
      27: return

  private static boolean lambda$showSchematicSave$39(java.lang.String, mindustry.game.Schematic);
    Code:
       0: aload_1
       1: invokevirtual #2860               // Method mindustry/game/Schematic.name:()Ljava/lang/String;
       4: aload_0
       5: invokevirtual #2862               // Method java/lang/String.equals:(Ljava/lang/Object;)Z
       8: ireturn

  private void lambda$drawOtherBuildPlans$38(mindustry.gen.Player);
    Code:
       0: aload_1
       1: invokevirtual #2865               // Method mindustry/gen/Player.getPreviewPlans:()Larc/struct/Seq;
       4: astore_2
       5: aload_1
       6: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
       9: if_acmpeq     25
      12: aload_1
      13: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      16: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      19: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      22: if_acmpeq     31
      25: aload_2
      26: invokevirtual #578                // Method arc/struct/Seq.clear:()Larc/struct/Seq;
      29: pop
      30: return
      31: aload_1
      32: getfield      #2868               // Field mindustry/gen/Player.previewPlanTree:Larc/math/geom/QuadTree;
      35: ifnonnull     75
      38: aload_1
      39: new           #129                // class arc/math/geom/QuadTree
      42: dup
      43: aload_0
      44: getfield      #137                // Field playerPlanTree:Larc/math/geom/QuadTree;
      47: getfield      #2871               // Field arc/math/geom/QuadTree.bounds:Larc/math/geom/Rect;
      50: invokespecial #134                // Method arc/math/geom/QuadTree."<init>":(Larc/math/geom/Rect;)V
      53: putfield      #2868               // Field mindustry/gen/Player.previewPlanTree:Larc/math/geom/QuadTree;
      56: aload_1
      57: new           #1285               // class mindustry/input/InputHandler$QueryEachable
      60: dup
      61: aload_1
      62: getfield      #2868               // Field mindustry/gen/Player.previewPlanTree:Larc/math/geom/QuadTree;
      65: iconst_0
      66: anewarray     #37                 // class arc/struct/Seq
      69: invokespecial #1287               // Method mindustry/input/InputHandler$QueryEachable."<init>":(Larc/math/geom/QuadTree;[Larc/struct/Seq;)V
      72: putfield      #2873               // Field mindustry/gen/Player.planEachable:Lmindustry/input/InputHandler$QueryEachable;
      75: aload_1
      76: getfield      #2877               // Field mindustry/gen/Player.previewPlansDirty:Z
      79: ifeq          170
      82: aload_1
      83: iconst_0
      84: putfield      #2877               // Field mindustry/gen/Player.previewPlansDirty:Z
      87: aload_2
      88: invokevirtual #613                // Method arc/struct/Seq.iterator:()Ljava/util/Iterator;
      91: astore_3
      92: aload_3
      93: invokeinterface #394,  1          // InterfaceMethod java/util/Iterator.hasNext:()Z
      98: ifeq          162
     101: aload_3
     102: invokeinterface #399,  1          // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
     107: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     110: astore        4
     112: aload         4
     114: putstatic     #2880               // Field sameQuadPlan:Lmindustry/entities/units/BuildPlan;
     117: aload_1
     118: getfield      #2868               // Field mindustry/gen/Player.previewPlanTree:Larc/math/geom/QuadTree;
     121: aload         4
     123: invokevirtual #1794               // Method mindustry/entities/units/BuildPlan.drawx:()F
     126: aload         4
     128: invokevirtual #1797               // Method mindustry/entities/units/BuildPlan.drawy:()F
     131: fconst_1
     132: fconst_1
     133: getstatic     #2883               // Field sameQuadPlanFinder:Larc/func/Boolf;
     136: invokevirtual #2633               // Method arc/math/geom/QuadTree.find:(FFFFLarc/func/Boolf;)Larc/math/geom/QuadTree$QuadTreeObject;
     139: checkcast     #74                 // class mindustry/entities/units/BuildPlan
     142: astore        5
     144: aload         5
     146: ifnull        159
     149: aload         4
     151: aload         5
     153: getfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
     156: putfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
     159: goto          92
     162: aload_1
     163: getfield      #2868               // Field mindustry/gen/Player.previewPlanTree:Larc/math/geom/QuadTree;
     166: aload_2
     167: invokevirtual #1296               // Method arc/math/geom/QuadTree.fill:(Larc/struct/Seq;)V
     170: aload_1
     171: invokevirtual #1367               // Method mindustry/gen/Player.isBuilder:()Z
     174: ifeq          187
     177: aload_1
     178: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
     181: invokevirtual #1821               // Method mindustry/gen/Unit.buildPlan:()Lmindustry/entities/units/BuildPlan;
     184: goto          188
     187: aconst_null
     188: astore_3
     189: getstatic     #1309               // Field arc/Core.camera:Larc/graphics/Camera;
     192: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     195: invokevirtual #1543               // Method arc/graphics/Camera.bounds:(Larc/math/geom/Rect;)Larc/math/geom/Rect;
     198: pop
     199: aload_1
     200: getfield      #2868               // Field mindustry/gen/Player.previewPlanTree:Larc/math/geom/QuadTree;
     203: getstatic     #1539               // Field arc/util/Tmp.r1:Larc/math/geom/Rect;
     206: ldc_w         #2886               // float 16.0f
     209: invokevirtual #2444               // Method arc/math/geom/Rect.grow:(F)Larc/math/geom/Rect;
     212: aload_0
     213: aload_3
     214: aload_1
     215: invokedynamic #2887,  0           // InvokeDynamic #60:get:(Lmindustry/input/InputHandler;Lmindustry/entities/units/BuildPlan;Lmindustry/gen/Player;)Larc/func/Cons;
     220: invokevirtual #2489               // Method arc/math/geom/QuadTree.intersect:(Larc/math/geom/Rect;Larc/func/Cons;)V
     223: return

  private void lambda$drawOtherBuildPlans$37(mindustry.entities.units.BuildPlan, mindustry.gen.Player, mindustry.entities.units.BuildPlan);
    Code:
       0: aload_3
       1: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
       4: ifnull        54
       7: aload_3
       8: invokevirtual #2890               // Method mindustry/entities/units/BuildPlan.isDone:()Z
      11: ifne          54
      14: aload_1
      15: ifnull        55
      18: aload_2
      19: getfield      #1211               // Field mindustry/gen/Player.x:F
      22: aload_1
      23: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      26: i2f
      27: fcmpl
      28: ifne          55
      31: aload_2
      32: getfield      #1212               // Field mindustry/gen/Player.y:F
      35: aload_1
      36: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      39: i2f
      40: fcmpl
      41: ifne          55
      44: aload_2
      45: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      48: invokevirtual #2579               // Method mindustry/gen/Unit.activelyBuilding:()Z
      51: ifeq          55
      54: return
      55: getstatic     #1870               // Field arc/util/Tmp.r2:Larc/math/geom/Rect;
      58: aload_3
      59: invokevirtual #1794               // Method mindustry/entities/units/BuildPlan.drawx:()F
      62: aload_3
      63: invokevirtual #1797               // Method mindustry/entities/units/BuildPlan.drawy:()F
      66: aload_3
      67: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      70: getfield      #860                // Field mindustry/world/Block.size:I
      73: bipush        8
      75: imul
      76: i2f
      77: invokevirtual #1876               // Method arc/math/geom/Rect.setCentered:(FFF)Larc/math/geom/Rect;
      80: getstatic     #1782               // Field arc/util/Tmp.v3:Larc/math/geom/Vec2;
      83: invokevirtual #2447               // Method arc/math/geom/Rect.contains:(Larc/math/geom/Vec2;)Z
      86: ifeq          99
      89: aload_0
      90: aload_3
      91: putfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
      94: aload_0
      95: aload_2
      96: putfield      #154                // Field overlappingPlayer:Lmindustry/gen/Player;
      99: aload_3
     100: aload_3
     101: getfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
     104: fconst_1
     105: ldc_w         #2893               // float 0.2f
     108: invokestatic  #2894               // Method arc/math/Mathf.lerpDelta:(FFF)F
     111: putfield      #1845               // Field mindustry/entities/units/BuildPlan.animScale:F
     114: aload_3
     115: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
     118: aload_3
     119: aload_2
     120: getfield      #2873               // Field mindustry/gen/Player.planEachable:Lmindustry/input/InputHandler$QueryEachable;
     123: aload_0
     124: getfield      #151                // Field overlappingPlan:Lmindustry/entities/units/BuildPlan;
     127: aload_3
     128: if_acmpne     137
     131: ldc_w         #1707               // float 0.7f
     134: goto          140
     137: ldc_w         #2896               // float 0.25f
     140: invokevirtual #2897               // Method mindustry/world/Block.drawOtherPlayerPlan:(Lmindustry/entities/units/BuildPlan;Larc/util/Eachable;F)V
     143: return

  private static boolean lambda$static$36(mindustry.entities.units.BuildPlan);
    Code:
       0: aload_0
       1: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
       4: getstatic     #2880               // Field sameQuadPlan:Lmindustry/entities/units/BuildPlan;
       7: getfield      #1800               // Field mindustry/entities/units/BuildPlan.block:Lmindustry/world/Block;
      10: if_acmpne     43
      13: aload_0
      14: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      17: getstatic     #2880               // Field sameQuadPlan:Lmindustry/entities/units/BuildPlan;
      20: getfield      #1807               // Field mindustry/entities/units/BuildPlan.x:I
      23: if_icmpne     43
      26: aload_0
      27: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      30: getstatic     #2880               // Field sameQuadPlan:Lmindustry/entities/units/BuildPlan;
      33: getfield      #1809               // Field mindustry/entities/units/BuildPlan.y:I
      36: if_icmpne     43
      39: iconst_1
      40: goto          44
      43: iconst_0
      44: ireturn

  private static boolean lambda$drawCommanded$35(mindustry.gen.Unit);
    Code:
       0: aload_0
       1: invokevirtual #2901               // Method mindustry/gen/Unit.allowCommand:()Z
       4: ifne          11
       7: iconst_1
       8: goto          12
      11: iconst_0
      12: ireturn

  private void lambda$drawCommanded$34();
    Code:
       0: aload_0
       1: invokevirtual #2903               // Method drawCommandedTargets:()V
       4: return

  private void lambda$drawCommanded$33();
    Code:
       0: aload_0
       1: iconst_0
       2: invokevirtual #2906               // Method drawCommanded:(Z)V
       5: return

  private void lambda$drawCommanded$32();
    Code:
       0: aload_0
       1: iconst_1
       2: invokevirtual #2906               // Method drawCommanded:(Z)V
       5: return

  private static int lambda$commandTap$31(mindustry.gen.Building);
    Code:
       0: aload_0
       1: invokevirtual #2909               // Method mindustry/gen/Building.pos:()I
       4: ireturn

  private static boolean lambda$selectTypedUnits$30(mindustry.gen.Unit, mindustry.gen.Unit);
    Code:
       0: aload_1
       1: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
       4: aload_0
       5: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
       8: if_acmpne     15
      11: iconst_1
      12: goto          16
      15: iconst_0
      16: ireturn

  private static boolean lambda$tryPickupPayload$29(mindustry.gen.Payloadc, mindustry.gen.Unit, mindustry.gen.Unit);
    Code:
       0: aload_2
       1: invokevirtual #838                // Method mindustry/gen/Unit.isAI:()Z
       4: ifeq          45
       7: aload_2
       8: invokevirtual #841                // Method mindustry/gen/Unit.isGrounded:()Z
      11: ifeq          45
      14: aload_0
      15: aload_2
      16: invokeinterface #844,  2          // InterfaceMethod mindustry/gen/Payloadc.canPickup:(Lmindustry/gen/Unit;)Z
      21: ifeq          45
      24: aload_2
      25: aload_1
      26: aload_2
      27: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
      30: aload_1
      31: getfield      #1255               // Field mindustry/gen/Unit.hitSize:F
      34: fadd
      35: invokevirtual #851                // Method mindustry/gen/Unit.within:(Larc/math/geom/Position;F)Z
      38: ifeq          45
      41: iconst_1
      42: goto          46
      45: iconst_0
      46: ireturn

  private boolean lambda$checkUnit$28(mindustry.gen.Unit);
    Code:
       0: aload_1
       1: invokevirtual #1167               // Method mindustry/gen/Unit.isPlayer:()Z
       4: ifne          29
       7: aload_1
       8: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
      11: aload_0
      12: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
      15: if_acmpne     29
      18: aload_1
      19: getfield      #1162               // Field mindustry/gen/Unit.dead:Z
      22: ifne          29
      25: iconst_1
      26: goto          30
      29: iconst_0
      30: ireturn

  private boolean lambda$update$27(mindustry.gen.Unit);
    Code:
       0: aload_1
       1: invokevirtual #1167               // Method mindustry/gen/Unit.isPlayer:()Z
       4: ifne          36
       7: aload_1
       8: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
      11: aload_0
      12: getfield      #1432               // Field controlledType:Lmindustry/type/UnitType;
      15: if_acmpne     36
      18: aload_1
      19: invokevirtual #1187               // Method mindustry/gen/Unit.playerControllable:()Z
      22: ifeq          36
      25: aload_1
      26: getfield      #1162               // Field mindustry/gen/Unit.dead:Z
      29: ifne          36
      32: iconst_1
      33: goto          37
      36: iconst_0
      37: ireturn

  private static boolean lambda$update$26(mindustry.gen.Building);
    Code:
       0: aload_0
       1: invokevirtual #2910               // Method mindustry/gen/Building.isValid:()Z
       4: ifeq          27
       7: aload_0
       8: invokevirtual #718                // Method mindustry/gen/Building.isCommandable:()Z
      11: ifeq          27
      14: aload_0
      15: getfield      #877                // Field mindustry/gen/Building.team:Lmindustry/game/Team;
      18: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      21: invokevirtual #373                // Method mindustry/gen/Player.team:()Lmindustry/game/Team;
      24: if_acmpeq     31
      27: iconst_1
      28: goto          32
      31: iconst_0
      32: ireturn

  private static void lambda$unitClear$25(mindustry.net.Administration$PlayerAction);
    Code:
       0: return

  private static void lambda$unitControl$24(mindustry.gen.Unit);
    Code:
       0: getstatic     #2911               // Field mindustry/content/Fx.unitControl:Lmindustry/entities/Effect;
       3: aload_0
       4: getfield      #821                // Field mindustry/gen/Unit.x:F
       7: aload_0
       8: getfield      #823                // Field mindustry/gen/Unit.y:F
      11: fconst_0
      12: aload_0
      13: invokevirtual #1213               // Method mindustry/entities/Effect.at:(FFFLjava/lang/Object;)V
      16: return

  private static void lambda$unitControl$23(mindustry.gen.Unit, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2913               // Field mindustry/net/Administration$PlayerAction.unit:Lmindustry/gen/Unit;
       5: return

  private static void lambda$buildingControlSelect$22(mindustry.gen.Building, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: getfield      #757                // Field mindustry/gen/Building.tile:Lmindustry/world/Tile;
       5: putfield      #2917               // Field mindustry/net/Administration$PlayerAction.tile:Lmindustry/world/Tile;
       8: return

  private static void lambda$tileConfig$21(java.lang.Object, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2918               // Field mindustry/net/Administration$PlayerAction.config:Ljava/lang/Object;
       5: return

  private static void lambda$rotateBlock$20(mindustry.gen.Building, boolean, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_2
       1: aload_0
       2: getfield      #1053               // Field mindustry/gen/Building.rotation:I
       5: iload_1
       6: invokestatic  #1054               // Method arc/math/Mathf.sign:(Z)I
       9: iadd
      10: iconst_4
      11: invokestatic  #1058               // Method arc/math/Mathf.mod:(II)I
      14: putfield      #2919               // Field mindustry/net/Administration$PlayerAction.rotation:I
      17: return

  private static void lambda$requestDropPayload$19(mindustry.gen.Payloadc, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: invokeinterface #950,  1          // InterfaceMethod mindustry/gen/Payloadc.payloads:()Larc/struct/Seq;
       7: invokevirtual #2920               // Method arc/struct/Seq.peek:()Ljava/lang/Object;
      10: checkcast     #2923               // class mindustry/world/blocks/payloads/Payload
      13: putfield      #2925               // Field mindustry/net/Administration$PlayerAction.payload:Lmindustry/world/blocks/payloads/Payload;
      16: return

  private static void lambda$requestBuildPayload$18(mindustry.gen.Unit, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2913               // Field mindustry/net/Administration$PlayerAction.unit:Lmindustry/gen/Unit;
       5: return

  private static void lambda$transferInventory$17(mindustry.gen.Player, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
       5: getfield      #317                // Field mindustry/gen/Unit.stack:Lmindustry/type/ItemStack;
       8: getfield      #286                // Field mindustry/type/ItemStack.amount:I
      11: putfield      #2929               // Field mindustry/net/Administration$PlayerAction.itemAmount:I
      14: aload_1
      15: aload_0
      16: invokevirtual #769                // Method mindustry/gen/Player.unit:()Lmindustry/gen/Unit;
      19: invokevirtual #314                // Method mindustry/gen/Unit.item:()Lmindustry/type/Item;
      22: putfield      #2932               // Field mindustry/net/Administration$PlayerAction.item:Lmindustry/type/Item;
      25: return

  private static void lambda$requestItem$16(mindustry.type.Item, int, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_2
       1: aload_0
       2: putfield      #2932               // Field mindustry/net/Administration$PlayerAction.item:Lmindustry/type/Item;
       5: aload_2
       6: iload_1
       7: putfield      #2929               // Field mindustry/net/Administration$PlayerAction.itemAmount:I
      10: return

  private static void lambda$commandBuilding$15(int[], mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2933               // Field mindustry/net/Administration$PlayerAction.buildingPositions:[I
       5: return

  private static void lambda$setUnitStance$14(int[], mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2937               // Field mindustry/net/Administration$PlayerAction.unitIDs:[I
       5: return

  private static void lambda$setUnitCommand$13(int[], mindustry.ai.UnitCommand, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_2
       1: aload_0
       2: putfield      #2937               // Field mindustry/net/Administration$PlayerAction.unitIDs:[I
       5: aload_2
       6: aload_1
       7: putfield      #2940               // Field mindustry/net/Administration$PlayerAction.unitCommand:Lmindustry/ai/UnitCommand;
      10: return

  private static void lambda$commandUnits$12(int[], mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2937               // Field mindustry/net/Administration$PlayerAction.unitIDs:[I
       5: return

  private static void lambda$pingLocation$11(float, float, java.lang.String, mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_3
       1: fload_0
       2: putfield      #2943               // Field mindustry/net/Administration$PlayerAction.pingX:F
       5: aload_3
       6: fload_1
       7: putfield      #2944               // Field mindustry/net/Administration$PlayerAction.pingY:F
      10: aload_3
      11: aload_2
      12: putfield      #2945               // Field mindustry/net/Administration$PlayerAction.pingText:Ljava/lang/String;
      15: return

  private static void lambda$deletePlans$10(int[], mindustry.net.Administration$PlayerAction);
    Code:
       0: aload_1
       1: aload_0
       2: putfield      #2946               // Field mindustry/net/Administration$PlayerAction.plans:[I
       5: return

  private static void lambda$transferItemTo$9(mindustry.type.Item, int, float, float, mindustry.gen.Building);
    Code:
       0: aload_0
       1: iload_1
       2: fload_2
       3: fload_3
       4: aload         4
       6: invokedynamic #2948,  0           // InvokeDynamic #61:run:()Ljava/lang/Runnable;
      11: invokestatic  #226                // Method createItemTransfer:(Lmindustry/type/Item;IFFLarc/math/geom/Position;Ljava/lang/Runnable;)V
      14: return

  private static void lambda$transferItemTo$8();
    Code:
       0: return

  private static void lambda$transferItemToUnit$7(mindustry.gen.Itemsc, mindustry.type.Item);
    Code:
       0: aload_0
       1: aload_1
       2: invokeinterface #2951,  2         // InterfaceMethod mindustry/gen/Itemsc.addItem:(Lmindustry/type/Item;)V
       7: return

  private static void lambda$takeItems$6(mindustry.type.Item, mindustry.gen.Building, mindustry.gen.Unit);
    Code:
       0: aload_0
       1: aload_1
       2: getfield      #1070               // Field mindustry/gen/Building.x:F
       5: aload_1
       6: getfield      #1071               // Field mindustry/gen/Building.y:F
       9: aload_2
      10: invokestatic  #2956               // Method transferItemEffect:(Lmindustry/type/Item;FFLmindustry/gen/Itemsc;)V
      13: return

  private void lambda$new$5(mindustry.game.EventType$ResetEvent);
    Code:
       0: aload_0
       1: invokevirtual #2960               // Method reset:()V
       4: return

  private void lambda$new$4(mindustry.game.EventType$WorldLoadEvent);
    Code:
       0: aload_0
       1: invokevirtual #2570               // Method initQuadtrees:()V
       4: return

  private static void lambda$new$3(mindustry.game.EventType$UnitDestroyEvent);
    Code:
       0: aload_0
       1: getfield      #2961               // Field mindustry/game/EventType$UnitDestroyEvent.unit:Lmindustry/gen/Unit;
       4: ifnull        58
       7: aload_0
       8: getfield      #2961               // Field mindustry/game/EventType$UnitDestroyEvent.unit:Lmindustry/gen/Unit;
      11: invokevirtual #1167               // Method mindustry/gen/Unit.isPlayer:()Z
      14: ifeq          58
      17: aload_0
      18: getfield      #2961               // Field mindustry/game/EventType$UnitDestroyEvent.unit:Lmindustry/gen/Unit;
      21: invokevirtual #2962               // Method mindustry/gen/Unit.getPlayer:()Lmindustry/gen/Player;
      24: invokevirtual #786                // Method mindustry/gen/Player.isLocal:()Z
      27: ifeq          58
      30: aload_0
      31: getfield      #2961               // Field mindustry/game/EventType$UnitDestroyEvent.unit:Lmindustry/gen/Unit;
      34: getfield      #563                // Field mindustry/gen/Unit.type:Lmindustry/type/UnitType;
      37: getfield      #2966               // Field mindustry/type/UnitType.weapons:Larc/struct/Seq;
      40: invokedynamic #2969,  0           // InvokeDynamic #62:get:()Larc/func/Boolf;
      45: invokevirtual #1303               // Method arc/struct/Seq.contains:(Larc/func/Boolf;)Z
      48: ifeq          58
      51: getstatic     #433                // Field mindustry/Vars.player:Lmindustry/gen/Player;
      54: iconst_0
      55: putfield      #1336               // Field mindustry/gen/Player.shooting:Z
      58: return

  private static boolean lambda$new$2(mindustry.type.Weapon);
    Code:
       0: aload_0
       1: getfield      #2970               // Field mindustry/type/Weapon.bullet:Lmindustry/entities/bullet/BulletType;
       4: getfield      #2976               // Field mindustry/entities/bullet/BulletType.killShooter:Z
       7: ireturn

  private boolean lambda$new$1();
    Code:
       0: aload_0
       1: getfield      #1320               // Field logicCutscene:Z
       4: ireturn

  private static boolean lambda$new$0();
    Code:
       0: getstatic     #1345               // Field mindustry/Vars.renderer:Lmindustry/core/Renderer;
       3: invokevirtual #1349               // Method mindustry/core/Renderer.isCutscene:()Z
       6: ireturn

  static {};
    Code:
       0: new           #503                // class arc/struct/ObjectMap
       3: dup
       4: invokespecial #2981               // Method arc/struct/ObjectMap."<init>":()V
       7: putstatic     #495                // Field queuedCommands:Larc/struct/ObjectMap;
      10: getstatic     #2676               // Field mindustry/Vars.mobile:Z
      13: ifeq          22
      16: ldc_w         #2982               // float 17.0f
      19: goto          25
      22: ldc_w         #1754               // float 11.0f
      25: putstatic     #2351               // Field playerSelectRange:F
      28: new           #37                 // class arc/struct/Seq
      31: dup
      32: invokespecial #81                 // Method arc/struct/Seq."<init>":()V
      35: putstatic     #662                // Field stancesOut:Larc/struct/Seq;
      38: new           #120                // class arc/struct/IntSeq
      41: dup
      42: invokespecial #2983               // Method arc/struct/IntSeq."<init>":()V
      45: putstatic     #2218               // Field removed:Larc/struct/IntSeq;
      48: new           #2087               // class arc/struct/IntSet
      51: dup
      52: invokespecial #2984               // Method arc/struct/IntSet."<init>":()V
      55: putstatic     #2082               // Field intSet:Larc/struct/IntSet;
      58: new           #131                // class arc/math/geom/Rect
      61: dup
      62: invokespecial #133                // Method arc/math/geom/Rect."<init>":()V
      65: putstatic     #2769               // Field r1:Larc/math/geom/Rect;
      68: new           #131                // class arc/math/geom/Rect
      71: dup
      72: invokespecial #133                // Method arc/math/geom/Rect."<init>":()V
      75: putstatic     #1986               // Field r2:Larc/math/geom/Rect;
      78: new           #37                 // class arc/struct/Seq
      81: dup
      82: iconst_0
      83: invokespecial #101                // Method arc/struct/Seq."<init>":(Z)V
      86: putstatic     #2454               // Field tmpUnits:Larc/struct/Seq;
      89: new           #37                 // class arc/struct/Seq
      92: dup
      93: iconst_0
      94: invokespecial #101                // Method arc/struct/Seq."<init>":(Z)V
      97: putstatic     #2481               // Field tmpBuildings:Larc/struct/Seq;
     100: bipush        10
     102: anewarray     #2985               // class arc/input/KeyBind
     105: dup
     106: iconst_0
     107: getstatic     #2987               // Field mindustry/input/Binding.blockSelect01:Larc/input/KeyBind;
     110: aastore
     111: dup
     112: iconst_1
     113: getstatic     #2990               // Field mindustry/input/Binding.blockSelect02:Larc/input/KeyBind;
     116: aastore
     117: dup
     118: iconst_2
     119: getstatic     #2993               // Field mindustry/input/Binding.blockSelect03:Larc/input/KeyBind;
     122: aastore
     123: dup
     124: iconst_3
     125: getstatic     #2996               // Field mindustry/input/Binding.blockSelect04:Larc/input/KeyBind;
     128: aastore
     129: dup
     130: iconst_4
     131: getstatic     #2999               // Field mindustry/input/Binding.blockSelect05:Larc/input/KeyBind;
     134: aastore
     135: dup
     136: iconst_5
     137: getstatic     #3002               // Field mindustry/input/Binding.blockSelect06:Larc/input/KeyBind;
     140: aastore
     141: dup
     142: bipush        6
     144: getstatic     #3005               // Field mindustry/input/Binding.blockSelect07:Larc/input/KeyBind;
     147: aastore
     148: dup
     149: bipush        7
     151: getstatic     #3008               // Field mindustry/input/Binding.blockSelect08:Larc/input/KeyBind;
     154: aastore
     155: dup
     156: bipush        8
     158: getstatic     #3011               // Field mindustry/input/Binding.blockSelect09:Larc/input/KeyBind;
     161: aastore
     162: dup
     163: bipush        9
     165: getstatic     #3014               // Field mindustry/input/Binding.blockSelect10:Larc/input/KeyBind;
     168: aastore
     169: putstatic     #116                // Field controlGroupBindings:[Larc/input/KeyBind;
     172: invokedynamic #3017,  0           // InvokeDynamic #63:get:()Larc/func/Boolf;
     177: putstatic     #2883               // Field sameQuadPlanFinder:Larc/func/Boolf;
     180: invokedynamic #3018,  0           // InvokeDynamic #64:get:()Larc/func/Boolf;
     185: putstatic     #2629               // Field vpPredicate:Larc/func/Boolf;
     188: return
}
