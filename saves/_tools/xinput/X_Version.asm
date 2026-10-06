javap.exe : ����: �ļ� F:\OneDrive\����\AtomicStates\saves\_tools\xinput\X_Version.class �������� X_Version
所在位置 行:4 字符: 1
+ & $javap -p -c -cp "$t;$jar" 'X_Version' 2>&1 | Out-File (Join-Path $ ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (����: �ļ� F:\On...����� X_Version:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
Compiled from "Version.java"
public class mindustry.core.Version {
  public static java.lang.String type;

  public static java.lang.String modifier;

  public static java.lang.String commitHash;

  public static java.lang.String buildDate;

  public static int number;

  public static int build;

  public static int revision;

  public static boolean isSteam;

  public static boolean enabled;

  public mindustry.core.Version();
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Object."<init>":()V
       4: return

  public static void init();
    Code:
       0: getstatic     #7                  // Field enabled:Z
       3: ifne          7
       6: return
       7: getstatic     #13                 // Field arc/util/OS.isAndroid:Z
      10: ifne          19
      13: getstatic     #18                 // Field arc/util/OS.isIos:Z
      16: ifeq          32
      19: getstatic     #21                 // Field arc/Core.files:Larc/Files;
      22: ldc           #27                 // String version.properties
      24: invokeinterface #29,  2           // InterfaceMethod arc/Files.internal:(Ljava/lang/String;)Larc/files/Fi;
      29: goto          44
      32: new           #35                 // class arc/files/Fi
      35: dup
      36: ldc           #27                 // String version.properties
      38: getstatic     #37                 // Field arc/Files$FileType.internal:Larc/Files$FileType;
      41: invokespecial #42                 // Method arc/files/Fi."<init>":(Ljava/lang/String;Larc/Files$FileType;)V
      44: astore_0
      45: new           #45                 // class arc/struct/ObjectMap
      48: dup
      49: invokespecial #47                 // Method arc/struct/ObjectMap."<init>":()V
      52: astore_1
      53: aload_1
      54: aload_0
      55: invokevirtual #48                 // Method arc/files/Fi.reader:()Ljava/io/Reader;
      58: invokestatic  #52                 // Method arc/util/io/PropertiesUtils.load:(Larc/struct/ObjectMap;Ljava/io/Reader;)V
      61: aload_1
      62: ldc           #58                 // String type
      64: invokevirtual #60                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
      67: checkcast     #64                 // class java/lang/String
      70: putstatic     #66                 // Field type:Ljava/lang/String;
      73: aload_1
      74: ldc           #69                 // String number
      76: ldc           #71                 // String 4
      78: invokevirtual #73                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
      81: checkcast     #64                 // class java/lang/String
      84: invokestatic  #76                 // Method java/lang/Integer.parseInt:(Ljava/lang/String;)I
      87: putstatic     #82                 // Field number:I
      90: aload_1
      91: ldc           #85                 // String modifier
      93: invokevirtual #60                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
      96: checkcast     #64                 // class java/lang/String
      99: putstatic     #87                 // Field modifier:Ljava/lang/String;
     102: aload_1
     103: ldc           #89                 // String commitHash
     105: ldc           #91                 // String unknown
     107: invokevirtual #73                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
     110: checkcast     #64                 // class java/lang/String
     113: putstatic     #93                 // Field commitHash:Ljava/lang/String;
     116: aload_1
     117: ldc           #95                 // String buildDate
     119: ldc           #91                 // String unknown
     121: invokevirtual #73                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
     124: checkcast     #64                 // class java/lang/String
     127: putstatic     #97                 // Field buildDate:Ljava/lang/String;
     130: getstatic     #87                 // Field modifier:Ljava/lang/String;
     133: ldc           #99                 // String steam
     135: invokevirtual #101                // Method java/lang/String.contains:(Ljava/lang/CharSequence;)Z
     138: putstatic     #105                // Field isSteam:Z
     141: aload_1
     142: ldc           #108                // String build
     144: invokevirtual #60                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
     147: checkcast     #64                 // class java/lang/String
     150: ldc           #110                // String .
     152: invokevirtual #101                // Method java/lang/String.contains:(Ljava/lang/CharSequence;)Z
     155: ifeq          206
     158: aload_1
     159: ldc           #108                // String build
     161: invokevirtual #60                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
     164: checkcast     #64                 // class java/lang/String
     167: ldc           #112                // String \\.
     169: invokevirtual #114                // Method java/lang/String.split:(Ljava/lang/String;)[Ljava/lang/String;
     172: astore_2
     173: aload_2
     174: iconst_0
     175: aaload
     176: invokestatic  #76                 // Method java/lang/Integer.parseInt:(Ljava/lang/String;)I
     179: putstatic     #118                // Field build:I
     182: aload_2
     183: iconst_1
     184: aaload
     185: invokestatic  #76                 // Method java/lang/Integer.parseInt:(Ljava/lang/String;)I
     188: putstatic     #120                // Field revision:I
     191: goto          203
     194: astore_3
     195: aload_3
     196: invokevirtual #125                // Method java/lang/Throwable.printStackTrace:()V
     199: iconst_m1
     200: putstatic     #118                // Field build:I
     203: goto          240
     206: aload_1
     207: ldc           #108                // String build
     209: invokevirtual #60                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
     212: checkcast     #64                 // class java/lang/String
     215: invokestatic  #128                // Method arc/util/Strings.canParseInt:(Ljava/lang/String;)Z
     218: ifeq          236
     221: aload_1
     222: ldc           #108                // String build
     224: invokevirtual #60                 // Method arc/struct/ObjectMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
     227: checkcast     #64                 // class java/lang/String
     230: invokestatic  #76                 // Method java/lang/Integer.parseInt:(Ljava/lang/String;)I
     233: goto          237
     236: iconst_m1
     237: putstatic     #118                // Field build:I
     240: return
    Exception table:
       from    to  target type
         173   191   194   Class java/lang/Throwable

  public static boolean isAtLeast(java.lang.String);
    Code:
       0: getstatic     #118                // Field build:I
       3: getstatic     #120                // Field revision:I
       6: aload_0
       7: invokestatic  #134                // Method isAtLeast:(IILjava/lang/String;)Z
      10: ireturn

  public static boolean isAtLeast(int, int, java.lang.String);
    Code:
       0: iload_0
       1: ifle          15
       4: aload_2
       5: ifnull        15
       8: aload_2
       9: invokevirtual #138                // Method java/lang/String.isEmpty:()Z
      12: ifeq          17
      15: iconst_1
      16: ireturn
      17: aload_2
      18: bipush        46
      20: invokevirtual #142                // Method java/lang/String.indexOf:(I)I
      23: istore_3
      24: iload_3
      25: iconst_m1
      26: if_icmpeq     78
      29: aload_2
      30: iconst_0
      31: iload_3
      32: invokevirtual #146                // Method java/lang/String.substring:(II)Ljava/lang/String;
      35: iconst_0
      36: invokestatic  #150                // Method arc/util/Strings.parseInt:(Ljava/lang/String;I)I
      39: istore        4
      41: aload_2
      42: iload_3
      43: iconst_1
      44: iadd
      45: invokevirtual #153                // Method java/lang/String.substring:(I)Ljava/lang/String;
      48: iconst_0
      49: invokestatic  #150                // Method arc/util/Strings.parseInt:(Ljava/lang/String;I)I
      52: istore        5
      54: iload_0
      55: iload         4
      57: if_icmpgt     72
      60: iload_0
      61: iload         4
      63: if_icmpne     76
      66: iload_1
      67: iload         5
      69: if_icmplt     76
      72: iconst_1
      73: goto          77
      76: iconst_0
      77: ireturn
      78: iload_0
      79: aload_2
      80: iconst_0
      81: invokestatic  #150                // Method arc/util/Strings.parseInt:(Ljava/lang/String;I)I
      84: if_icmplt     91
      87: iconst_1
      88: goto          92
      91: iconst_0
      92: ireturn

  public static java.lang.String buildString();
    Code:
       0: getstatic     #118                // Field build:I
       3: ifge          11
       6: ldc           #156                // String custom
       8: goto          38
      11: getstatic     #118                // Field build:I
      14: getstatic     #120                // Field revision:I
      17: ifne          25
      20: ldc           #158                // String
      22: goto          33
      25: getstatic     #120                // Field revision:I
      28: invokedynamic #160,  0            // InvokeDynamic #0:makeConcatWithConstants:(I)Ljava/lang/String;
      33: invokedynamic #163,  0            // InvokeDynamic #1:makeConcatWithConstants:(ILjava/lang/String;)Ljava/lang/String;
      38: areturn

  public static java.lang.String combined();
    Code:
       0: getstatic     #118                // Field build:I
       3: iconst_m1
       4: if_icmpne     10
       7: ldc           #166                // String custom build
       9: areturn
      10: getstatic     #66                 // Field type:Ljava/lang/String;
      13: ldc           #168                // String official
      15: invokevirtual #170                // Method java/lang/String.equals:(Ljava/lang/Object;)Z
      18: ifeq          27
      21: getstatic     #87                 // Field modifier:Ljava/lang/String;
      24: goto          30
      27: getstatic     #66                 // Field type:Ljava/lang/String;
      30: getstatic     #118                // Field build:I
      33: getstatic     #120                // Field revision:I
      36: ifne          44
      39: ldc           #158                // String
      41: goto          52
      44: getstatic     #120                // Field revision:I
      47: invokedynamic #160,  0            // InvokeDynamic #0:makeConcatWithConstants:(I)Ljava/lang/String;
      52: getstatic     #93                 // Field commitHash:Ljava/lang/String;
      55: ldc           #91                 // String unknown
      57: invokevirtual #170                // Method java/lang/String.equals:(Ljava/lang/Object;)Z
      60: ifeq          68
      63: ldc           #158                // String
      65: goto          76
      68: getstatic     #93                 // Field commitHash:Ljava/lang/String;
      71: invokedynamic #174,  0            // InvokeDynamic #2:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
      76: getstatic     #177                // Field mindustryX/VarsX.version:Ljava/lang/String;
      79: invokedynamic #182,  0            // InvokeDynamic #3:makeConcatWithConstants:(Ljava/lang/String;ILjava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
      84: areturn

  static {};
    Code:
       0: ldc           #91                 // String unknown
       2: putstatic     #66                 // Field type:Ljava/lang/String;
       5: ldc           #91                 // String unknown
       7: putstatic     #87                 // Field modifier:Ljava/lang/String;
      10: ldc           #91                 // String unknown
      12: putstatic     #93                 // Field commitHash:Ljava/lang/String;
      15: ldc           #91                 // String unknown
      17: putstatic     #97                 // Field buildDate:Ljava/lang/String;
      20: iconst_0
      21: putstatic     #118                // Field build:I
      24: iconst_0
      25: putstatic     #120                // Field revision:I
      28: iconst_0
      29: putstatic     #105                // Field isSteam:Z
      32: iconst_1
      33: putstatic     #7                  // Field enabled:Z
      36: return
}
