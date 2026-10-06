Compiled from "Binding.java"
public class mindustry.input.Binding {
  public static final arc.input.KeyBind moveX;

  public static final arc.input.KeyBind moveY;

  public static final arc.input.KeyBind mouseMove;

  public static final arc.input.KeyBind pan;

  public static final arc.input.KeyBind boost;

  public static final arc.input.KeyBind respawn;

  public static final arc.input.KeyBind control;

  public static final arc.input.KeyBind select;

  public static final arc.input.KeyBind deselect;

  public static final arc.input.KeyBind breakBlock;

  public static final arc.input.KeyBind pickupCargo;

  public static final arc.input.KeyBind dropCargo;

  public static final arc.input.KeyBind clearBuilding;

  public static final arc.input.KeyBind pauseBuilding;

  public static final arc.input.KeyBind rotate;

  public static final arc.input.KeyBind rotatePlaced;

  public static final arc.input.KeyBind diagonalPlacement;

  public static final arc.input.KeyBind pick;

  public static final arc.input.KeyBind ping;

  public static final arc.input.KeyBind rebuildSelect;

  public static final arc.input.KeyBind schematicSelect;

  public static final arc.input.KeyBind schematicFlipX;

  public static final arc.input.KeyBind schematicFlipY;

  public static final arc.input.KeyBind schematicMenu;

  public static final arc.input.KeyBind commandMode;

  public static final arc.input.KeyBind commandQueue;

  public static final arc.input.KeyBind createControlGroup;

  public static final arc.input.KeyBind selectAllUnits;

  public static final arc.input.KeyBind selectAllUnitFactories;

  public static final arc.input.KeyBind selectAllUnitTransport;

  public static final arc.input.KeyBind selectAcrossScreen;

  public static final arc.input.KeyBind cancelOrders;

  public static final arc.input.KeyBind unitStanceHoldFire;

  public static final arc.input.KeyBind unitStancePursueTarget;

  public static final arc.input.KeyBind unitStancePatrol;

  public static final arc.input.KeyBind unitStanceRam;

  public static final arc.input.KeyBind unitStanceBoost;

  public static final arc.input.KeyBind unitStanceHoldPosition;

  public static final arc.input.KeyBind unitCommandMove;

  public static final arc.input.KeyBind unitCommandRepair;

  public static final arc.input.KeyBind unitCommandRebuild;

  public static final arc.input.KeyBind unitCommandAssist;

  public static final arc.input.KeyBind unitCommandMine;

  public static final arc.input.KeyBind unitCommandEnterPayload;

  public static final arc.input.KeyBind unitCommandLoadUnits;

  public static final arc.input.KeyBind unitCommandLoadBlocks;

  public static final arc.input.KeyBind unitCommandUnloadPayload;

  public static final arc.input.KeyBind unitCommandLoopPayload;

  public static final arc.input.KeyBind categoryPrev;

  public static final arc.input.KeyBind categoryNext;

  public static final arc.input.KeyBind blockSelectLeft;

  public static final arc.input.KeyBind blockSelectRight;

  public static final arc.input.KeyBind blockSelectUp;

  public static final arc.input.KeyBind blockSelectDown;

  public static final arc.input.KeyBind blockSelect01;

  public static final arc.input.KeyBind blockSelect02;

  public static final arc.input.KeyBind blockSelect03;

  public static final arc.input.KeyBind blockSelect04;

  public static final arc.input.KeyBind blockSelect05;

  public static final arc.input.KeyBind blockSelect06;

  public static final arc.input.KeyBind blockSelect07;

  public static final arc.input.KeyBind blockSelect08;

  public static final arc.input.KeyBind blockSelect09;

  public static final arc.input.KeyBind blockSelect10;

  public static final arc.input.KeyBind zoom;

  public static final arc.input.KeyBind detachCamera;

  public static final arc.input.KeyBind teleportCursor;

  public static final arc.input.KeyBind menu;

  public static final arc.input.KeyBind fullscreen;

  public static final arc.input.KeyBind pause;

  public static final arc.input.KeyBind skipWave;

  public static final arc.input.KeyBind minimap;

  public static final arc.input.KeyBind research;

  public static final arc.input.KeyBind planetMap;

  public static final arc.input.KeyBind blockInfo;

  public static final arc.input.KeyBind toggleMenus;

  public static final arc.input.KeyBind screenshot;

  public static final arc.input.KeyBind togglePowerLines;

  public static final arc.input.KeyBind toggleBlockStatus;

  public static final arc.input.KeyBind playerList;

  public static final arc.input.KeyBind chat;

  public static final arc.input.KeyBind chatHistoryPrev;

  public static final arc.input.KeyBind chatHistoryNext;

  public static final arc.input.KeyBind chatScroll;

  public static final arc.input.KeyBind chatMode;

  public static final arc.input.KeyBind console;

  public static final arc.input.KeyBind debugHitboxes;

  public static final arc.input.KeyBind performanceMetrics;

  public mindustry.input.Binding();
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Object."<init>":()V
       4: return

  public static void init();
    Code:
       0: return

  static {};
    Code:
       0: ldc           #7                  // String move_x
       2: new           #9                  // class arc/input/KeyBind$Axis
       5: dup
       6: getstatic     #11                 // Field arc/input/KeyCode.a:Larc/input/KeyCode;
       9: getstatic     #17                 // Field arc/input/KeyCode.d:Larc/input/KeyCode;
      12: invokespecial #20                 // Method arc/input/KeyBind$Axis."<init>":(Larc/input/KeyCode;Larc/input/KeyCode;)V
      15: ldc           #23                 // String general
      17: invokestatic  #25                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;Ljava/lang/String;)Larc/input/KeyBind;
      20: putstatic     #31                 // Field moveX:Larc/input/KeyBind;
      23: ldc           #37                 // String move_y
      25: new           #9                  // class arc/input/KeyBind$Axis
      28: dup
      29: getstatic     #39                 // Field arc/input/KeyCode.s:Larc/input/KeyCode;
      32: getstatic     #42                 // Field arc/input/KeyCode.w:Larc/input/KeyCode;
      35: invokespecial #20                 // Method arc/input/KeyBind$Axis."<init>":(Larc/input/KeyCode;Larc/input/KeyCode;)V
      38: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
      41: putstatic     #48                 // Field moveY:Larc/input/KeyBind;
      44: ldc           #51                 // String mouse_move
      46: getstatic     #53                 // Field arc/input/KeyCode.mouseBack:Larc/input/KeyCode;
      49: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
      52: putstatic     #56                 // Field mouseMove:Larc/input/KeyBind;
      55: ldc           #59                 // String pan
      57: getstatic     #61                 // Field arc/input/KeyCode.mouseForward:Larc/input/KeyCode;
      60: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
      63: putstatic     #64                 // Field pan:Larc/input/KeyBind;
      66: ldc           #66                 // String boost
      68: getstatic     #68                 // Field arc/input/KeyCode.shiftLeft:Larc/input/KeyCode;
      71: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
      74: putstatic     #71                 // Field boost:Larc/input/KeyBind;
      77: ldc           #73                 // String respawn
      79: getstatic     #75                 // Field arc/input/KeyCode.v:Larc/input/KeyCode;
      82: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
      85: putstatic     #78                 // Field respawn:Larc/input/KeyBind;
      88: ldc           #80                 // String control
      90: getstatic     #82                 // Field arc/input/KeyCode.controlLeft:Larc/input/KeyCode;
      93: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
      96: putstatic     #85                 // Field control:Larc/input/KeyBind;
      99: ldc           #87                 // String select
     101: getstatic     #89                 // Field arc/input/KeyCode.mouseLeft:Larc/input/KeyCode;
     104: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     107: putstatic     #92                 // Field select:Larc/input/KeyBind;
     110: ldc           #94                 // String deselect
     112: getstatic     #96                 // Field arc/input/KeyCode.mouseRight:Larc/input/KeyCode;
     115: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     118: putstatic     #99                 // Field deselect:Larc/input/KeyBind;
     121: ldc           #101                // String break_block
     123: getstatic     #96                 // Field arc/input/KeyCode.mouseRight:Larc/input/KeyCode;
     126: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     129: putstatic     #103                // Field breakBlock:Larc/input/KeyBind;
     132: ldc           #106                // String pickupCargo
     134: getstatic     #108                // Field arc/input/KeyCode.leftBracket:Larc/input/KeyCode;
     137: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     140: putstatic     #111                // Field pickupCargo:Larc/input/KeyBind;
     143: ldc           #113                // String dropCargo
     145: getstatic     #115                // Field arc/input/KeyCode.rightBracket:Larc/input/KeyCode;
     148: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     151: putstatic     #118                // Field dropCargo:Larc/input/KeyBind;
     154: ldc           #120                // String clear_building
     156: getstatic     #122                // Field arc/input/KeyCode.q:Larc/input/KeyCode;
     159: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     162: putstatic     #125                // Field clearBuilding:Larc/input/KeyBind;
     165: ldc           #128                // String pause_building
     167: getstatic     #130                // Field arc/input/KeyCode.e:Larc/input/KeyCode;
     170: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     173: putstatic     #133                // Field pauseBuilding:Larc/input/KeyBind;
     176: ldc           #136                // String rotate
     178: new           #9                  // class arc/input/KeyBind$Axis
     181: dup
     182: getstatic     #138                // Field arc/input/KeyCode.scroll:Larc/input/KeyCode;
     185: invokespecial #141                // Method arc/input/KeyBind$Axis."<init>":(Larc/input/KeyCode;)V
     188: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     191: putstatic     #144                // Field rotate:Larc/input/KeyBind;
     194: ldc           #146                // String rotateplaced
     196: getstatic     #148                // Field arc/input/KeyCode.r:Larc/input/KeyCode;
     199: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     202: putstatic     #151                // Field rotatePlaced:Larc/input/KeyBind;
     205: ldc           #154                // String diagonal_placement
     207: getstatic     #82                 // Field arc/input/KeyCode.controlLeft:Larc/input/KeyCode;
     210: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     213: putstatic     #156                // Field diagonalPlacement:Larc/input/KeyBind;
     216: ldc           #159                // String pick
     218: getstatic     #161                // Field arc/input/KeyCode.mouseMiddle:Larc/input/KeyCode;
     221: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     224: putstatic     #164                // Field pick:Larc/input/KeyBind;
     227: ldc           #166                // String ping
     229: getstatic     #168                // Field arc/input/KeyCode.p:Larc/input/KeyCode;
     232: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     235: putstatic     #171                // Field ping:Larc/input/KeyBind;
     238: ldc           #173                // String rebuild_select
     240: getstatic     #175                // Field arc/input/KeyCode.b:Larc/input/KeyCode;
     243: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     246: putstatic     #178                // Field rebuildSelect:Larc/input/KeyBind;
     249: ldc           #181                // String schematic_select
     251: getstatic     #183                // Field arc/input/KeyCode.f:Larc/input/KeyCode;
     254: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     257: putstatic     #186                // Field schematicSelect:Larc/input/KeyBind;
     260: ldc           #189                // String schematic_flip_x
     262: getstatic     #191                // Field arc/input/KeyCode.z:Larc/input/KeyCode;
     265: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     268: putstatic     #194                // Field schematicFlipX:Larc/input/KeyBind;
     271: ldc           #197                // String schematic_flip_y
     273: getstatic     #199                // Field arc/input/KeyCode.x:Larc/input/KeyCode;
     276: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     279: putstatic     #202                // Field schematicFlipY:Larc/input/KeyBind;
     282: ldc           #205                // String schematic_menu
     284: getstatic     #207                // Field arc/input/KeyCode.t:Larc/input/KeyCode;
     287: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     290: putstatic     #210                // Field schematicMenu:Larc/input/KeyBind;
     293: ldc           #213                // String command_mode
     295: getstatic     #68                 // Field arc/input/KeyCode.shiftLeft:Larc/input/KeyCode;
     298: ldc           #215                // String command
     300: invokestatic  #25                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;Ljava/lang/String;)Larc/input/KeyBind;
     303: putstatic     #217                // Field commandMode:Larc/input/KeyBind;
     306: ldc           #220                // String command_queue
     308: getstatic     #161                // Field arc/input/KeyCode.mouseMiddle:Larc/input/KeyCode;
     311: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     314: putstatic     #222                // Field commandQueue:Larc/input/KeyBind;
     317: ldc           #225                // String create_control_group
     319: getstatic     #82                 // Field arc/input/KeyCode.controlLeft:Larc/input/KeyCode;
     322: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     325: putstatic     #227                // Field createControlGroup:Larc/input/KeyBind;
     328: ldc           #230                // String select_all_units
     330: getstatic     #232                // Field arc/input/KeyCode.g:Larc/input/KeyCode;
     333: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     336: putstatic     #235                // Field selectAllUnits:Larc/input/KeyBind;
     339: ldc           #238                // String select_all_unit_factories
     341: getstatic     #240                // Field arc/input/KeyCode.h:Larc/input/KeyCode;
     344: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     347: putstatic     #243                // Field selectAllUnitFactories:Larc/input/KeyBind;
     350: ldc           #246                // String select_all_unit_transport
     352: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     355: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     358: putstatic     #251                // Field selectAllUnitTransport:Larc/input/KeyBind;
     361: ldc           #254                // String select_across_screen
     363: getstatic     #256                // Field arc/input/KeyCode.altLeft:Larc/input/KeyCode;
     366: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     369: putstatic     #259                // Field selectAcrossScreen:Larc/input/KeyBind;
     372: ldc_w         #262                // String cancel_orders
     375: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     378: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     381: putstatic     #264                // Field cancelOrders:Larc/input/KeyBind;
     384: ldc_w         #267                // String unit_stance_hold_fire
     387: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     390: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     393: putstatic     #269                // Field unitStanceHoldFire:Larc/input/KeyBind;
     396: ldc_w         #272                // String unit_stance_pursue_target
     399: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     402: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     405: putstatic     #274                // Field unitStancePursueTarget:Larc/input/KeyBind;
     408: ldc_w         #277                // String unit_stance_patrol
     411: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     414: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     417: putstatic     #279                // Field unitStancePatrol:Larc/input/KeyBind;
     420: ldc_w         #282                // String unit_stance_ram
     423: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     426: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     429: putstatic     #284                // Field unitStanceRam:Larc/input/KeyBind;
     432: ldc_w         #287                // String unit_stance_boost
     435: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     438: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     441: putstatic     #289                // Field unitStanceBoost:Larc/input/KeyBind;
     444: ldc_w         #292                // String unit_stance_hold_position
     447: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     450: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     453: putstatic     #294                // Field unitStanceHoldPosition:Larc/input/KeyBind;
     456: ldc_w         #297                // String unit_command_move
     459: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     462: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     465: putstatic     #299                // Field unitCommandMove:Larc/input/KeyBind;
     468: ldc_w         #302                // String unit_command_repair
     471: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     474: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     477: putstatic     #304                // Field unitCommandRepair:Larc/input/KeyBind;
     480: ldc_w         #307                // String unit_command_rebuild
     483: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     486: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     489: putstatic     #309                // Field unitCommandRebuild:Larc/input/KeyBind;
     492: ldc_w         #312                // String unit_command_assist
     495: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     498: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     501: putstatic     #314                // Field unitCommandAssist:Larc/input/KeyBind;
     504: ldc_w         #317                // String unit_command_mine
     507: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     510: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     513: putstatic     #319                // Field unitCommandMine:Larc/input/KeyBind;
     516: ldc_w         #322                // String unit_command_enter_payload
     519: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     522: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     525: putstatic     #324                // Field unitCommandEnterPayload:Larc/input/KeyBind;
     528: ldc_w         #327                // String unit_command_load_units
     531: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     534: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     537: putstatic     #329                // Field unitCommandLoadUnits:Larc/input/KeyBind;
     540: ldc_w         #332                // String unit_command_load_blocks
     543: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     546: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     549: putstatic     #334                // Field unitCommandLoadBlocks:Larc/input/KeyBind;
     552: ldc_w         #337                // String unit_command_unload_payload
     555: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     558: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     561: putstatic     #339                // Field unitCommandUnloadPayload:Larc/input/KeyBind;
     564: ldc_w         #342                // String unit_command_loop_payload
     567: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     570: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     573: putstatic     #344                // Field unitCommandLoopPayload:Larc/input/KeyBind;
     576: ldc_w         #347                // String category_prev
     579: getstatic     #349                // Field arc/input/KeyCode.comma:Larc/input/KeyCode;
     582: ldc_w         #352                // String blocks
     585: invokestatic  #25                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;Ljava/lang/String;)Larc/input/KeyBind;
     588: putstatic     #354                // Field categoryPrev:Larc/input/KeyBind;
     591: ldc_w         #357                // String category_next
     594: getstatic     #359                // Field arc/input/KeyCode.period:Larc/input/KeyCode;
     597: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     600: putstatic     #362                // Field categoryNext:Larc/input/KeyBind;
     603: ldc_w         #365                // String block_select_left
     606: getstatic     #367                // Field arc/input/KeyCode.left:Larc/input/KeyCode;
     609: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     612: putstatic     #370                // Field blockSelectLeft:Larc/input/KeyBind;
     615: ldc_w         #373                // String block_select_right
     618: getstatic     #375                // Field arc/input/KeyCode.right:Larc/input/KeyCode;
     621: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     624: putstatic     #378                // Field blockSelectRight:Larc/input/KeyBind;
     627: ldc_w         #381                // String block_select_up
     630: getstatic     #383                // Field arc/input/KeyCode.up:Larc/input/KeyCode;
     633: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     636: putstatic     #386                // Field blockSelectUp:Larc/input/KeyBind;
     639: ldc_w         #389                // String block_select_down
     642: getstatic     #391                // Field arc/input/KeyCode.down:Larc/input/KeyCode;
     645: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     648: putstatic     #394                // Field blockSelectDown:Larc/input/KeyBind;
     651: ldc_w         #397                // String block_select_01
     654: getstatic     #399                // Field arc/input/KeyCode.num1:Larc/input/KeyCode;
     657: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     660: putstatic     #402                // Field blockSelect01:Larc/input/KeyBind;
     663: ldc_w         #405                // String block_select_02
     666: getstatic     #407                // Field arc/input/KeyCode.num2:Larc/input/KeyCode;
     669: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     672: putstatic     #410                // Field blockSelect02:Larc/input/KeyBind;
     675: ldc_w         #413                // String block_select_03
     678: getstatic     #415                // Field arc/input/KeyCode.num3:Larc/input/KeyCode;
     681: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     684: putstatic     #418                // Field blockSelect03:Larc/input/KeyBind;
     687: ldc_w         #421                // String block_select_04
     690: getstatic     #423                // Field arc/input/KeyCode.num4:Larc/input/KeyCode;
     693: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     696: putstatic     #426                // Field blockSelect04:Larc/input/KeyBind;
     699: ldc_w         #429                // String block_select_05
     702: getstatic     #431                // Field arc/input/KeyCode.num5:Larc/input/KeyCode;
     705: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     708: putstatic     #434                // Field blockSelect05:Larc/input/KeyBind;
     711: ldc_w         #437                // String block_select_06
     714: getstatic     #439                // Field arc/input/KeyCode.num6:Larc/input/KeyCode;
     717: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     720: putstatic     #442                // Field blockSelect06:Larc/input/KeyBind;
     723: ldc_w         #445                // String block_select_07
     726: getstatic     #447                // Field arc/input/KeyCode.num7:Larc/input/KeyCode;
     729: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     732: putstatic     #450                // Field blockSelect07:Larc/input/KeyBind;
     735: ldc_w         #453                // String block_select_08
     738: getstatic     #455                // Field arc/input/KeyCode.num8:Larc/input/KeyCode;
     741: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     744: putstatic     #458                // Field blockSelect08:Larc/input/KeyBind;
     747: ldc_w         #461                // String block_select_09
     750: getstatic     #463                // Field arc/input/KeyCode.num9:Larc/input/KeyCode;
     753: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     756: putstatic     #466                // Field blockSelect09:Larc/input/KeyBind;
     759: ldc_w         #469                // String block_select_10
     762: getstatic     #471                // Field arc/input/KeyCode.num0:Larc/input/KeyCode;
     765: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     768: putstatic     #474                // Field blockSelect10:Larc/input/KeyBind;
     771: ldc_w         #477                // String zoom
     774: new           #9                  // class arc/input/KeyBind$Axis
     777: dup
     778: getstatic     #138                // Field arc/input/KeyCode.scroll:Larc/input/KeyCode;
     781: invokespecial #141                // Method arc/input/KeyBind$Axis."<init>":(Larc/input/KeyCode;)V
     784: ldc_w         #479                // String view
     787: invokestatic  #25                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;Ljava/lang/String;)Larc/input/KeyBind;
     790: putstatic     #481                // Field zoom:Larc/input/KeyBind;
     793: ldc_w         #483                // String detach_camera
     796: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     799: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     802: putstatic     #485                // Field detachCamera:Larc/input/KeyBind;
     805: ldc_w         #488                // String teleport_cursor
     808: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     811: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     814: putstatic     #490                // Field teleportCursor:Larc/input/KeyBind;
     817: ldc_w         #493                // String menu
     820: getstatic     #495                // Field mindustry/Vars.android:Z
     823: ifeq          832
     826: getstatic     #501                // Field arc/input/KeyCode.back:Larc/input/KeyCode;
     829: goto          835
     832: getstatic     #504                // Field arc/input/KeyCode.escape:Larc/input/KeyCode;
     835: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     838: putstatic     #507                // Field menu:Larc/input/KeyBind;
     841: ldc_w         #509                // String fullscreen
     844: getstatic     #511                // Field arc/input/KeyCode.f11:Larc/input/KeyCode;
     847: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     850: putstatic     #514                // Field fullscreen:Larc/input/KeyBind;
     853: ldc_w         #516                // String pause
     856: getstatic     #518                // Field arc/input/KeyCode.space:Larc/input/KeyCode;
     859: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     862: putstatic     #521                // Field pause:Larc/input/KeyBind;
     865: ldc_w         #523                // String skip_wave
     868: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
     871: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     874: putstatic     #525                // Field skipWave:Larc/input/KeyBind;
     877: ldc_w         #528                // String minimap
     880: getstatic     #530                // Field arc/input/KeyCode.m:Larc/input/KeyCode;
     883: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     886: putstatic     #533                // Field minimap:Larc/input/KeyBind;
     889: ldc_w         #535                // String research
     892: getstatic     #537                // Field arc/input/KeyCode.j:Larc/input/KeyCode;
     895: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     898: putstatic     #540                // Field research:Larc/input/KeyBind;
     901: ldc_w         #542                // String planet_map
     904: getstatic     #544                // Field arc/input/KeyCode.n:Larc/input/KeyCode;
     907: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     910: putstatic     #547                // Field planetMap:Larc/input/KeyBind;
     913: ldc_w         #550                // String block_info
     916: getstatic     #552                // Field arc/input/KeyCode.f1:Larc/input/KeyCode;
     919: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     922: putstatic     #555                // Field blockInfo:Larc/input/KeyBind;
     925: ldc_w         #558                // String toggle_menus
     928: getstatic     #560                // Field arc/input/KeyCode.c:Larc/input/KeyCode;
     931: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     934: putstatic     #563                // Field toggleMenus:Larc/input/KeyBind;
     937: ldc_w         #566                // String screenshot
     940: getstatic     #568                // Field arc/input/KeyCode.f12:Larc/input/KeyCode;
     943: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     946: putstatic     #571                // Field screenshot:Larc/input/KeyBind;
     949: ldc_w         #573                // String toggle_power_lines
     952: getstatic     #575                // Field arc/input/KeyCode.f5:Larc/input/KeyCode;
     955: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     958: putstatic     #578                // Field togglePowerLines:Larc/input/KeyBind;
     961: ldc_w         #581                // String toggle_block_status
     964: getstatic     #583                // Field arc/input/KeyCode.f6:Larc/input/KeyCode;
     967: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     970: putstatic     #586                // Field toggleBlockStatus:Larc/input/KeyBind;
     973: ldc_w         #589                // String player_list
     976: getstatic     #591                // Field arc/input/KeyCode.tab:Larc/input/KeyCode;
     979: ldc_w         #594                // String multiplayer
     982: invokestatic  #25                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;Ljava/lang/String;)Larc/input/KeyBind;
     985: putstatic     #596                // Field playerList:Larc/input/KeyBind;
     988: ldc_w         #599                // String chat
     991: getstatic     #601                // Field arc/input/KeyCode.enter:Larc/input/KeyCode;
     994: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
     997: putstatic     #604                // Field chat:Larc/input/KeyBind;
    1000: ldc_w         #606                // String chat_history_prev
    1003: getstatic     #383                // Field arc/input/KeyCode.up:Larc/input/KeyCode;
    1006: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1009: putstatic     #608                // Field chatHistoryPrev:Larc/input/KeyBind;
    1012: ldc_w         #611                // String chat_history_next
    1015: getstatic     #391                // Field arc/input/KeyCode.down:Larc/input/KeyCode;
    1018: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1021: putstatic     #613                // Field chatHistoryNext:Larc/input/KeyBind;
    1024: ldc_w         #616                // String chat_scroll
    1027: new           #9                  // class arc/input/KeyBind$Axis
    1030: dup
    1031: getstatic     #138                // Field arc/input/KeyCode.scroll:Larc/input/KeyCode;
    1034: invokespecial #141                // Method arc/input/KeyBind$Axis."<init>":(Larc/input/KeyCode;)V
    1037: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1040: putstatic     #618                // Field chatScroll:Larc/input/KeyBind;
    1043: ldc_w         #621                // String chat_mode
    1046: getstatic     #591                // Field arc/input/KeyCode.tab:Larc/input/KeyCode;
    1049: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1052: putstatic     #623                // Field chatMode:Larc/input/KeyBind;
    1055: ldc_w         #626                // String console
    1058: getstatic     #628                // Field arc/input/KeyCode.f8:Larc/input/KeyCode;
    1061: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1064: putstatic     #631                // Field console:Larc/input/KeyBind;
    1067: ldc_w         #633                // String debug_hitboxes
    1070: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
    1073: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1076: putstatic     #635                // Field debugHitboxes:Larc/input/KeyBind;
    1079: ldc_w         #638                // String performance_metrics
    1082: getstatic     #248                // Field arc/input/KeyCode.unset:Larc/input/KeyCode;
    1085: invokestatic  #45                 // Method arc/input/KeyBind.add:(Ljava/lang/String;Larc/input/KeyBind$KeybindValue;)Larc/input/KeyBind;
    1088: putstatic     #640                // Field performanceMetrics:Larc/input/KeyBind;
    1091: return
}
