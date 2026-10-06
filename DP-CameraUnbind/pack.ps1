# Repack DP-CameraUnbind.zip
#
# WARNING: do NOT use Compress-Archive.
#   On Windows it writes zip entry names with backslashes (scripts\main.js),
#   but arc's ZipFi only understands '/' for both nesting and extensions, so:
#     - root.child("scripts").findAll(f -> f.extEquals("js")).size == 0
#     - mod.root.child("scripts").child("main.js").isDirectory() == true
#     - the game logs: [E] No main.js found for mod camera-unbind.
#   Use ZipArchive.CreateEntry with forward slashes, as done below.
#
# Verify with the game's own arc code (see saves\_jar2\ZipProbe.java):
#   javac -encoding UTF-8 -cp <jre>\desktop.jar -d . ZipProbe.java
#   java  -cp "<jre>\desktop.jar;." ZipProbe ..\DP-CameraUnbind.zip
#   Expect: scripts.findAll(js).size = 1 and main.js isDirectory = false

param(
    [string]$ModDir,
    [string]$ZipOut,
    # 把 METHOD.md 与 tools/ 也打进去（做一个"带文档的工具包"版本，
    # 不用于安装 —— 安装版保持精简，只含游戏需要读的文件）
    [switch]$WithDocs
)

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

# Defaults computed in the body ($PSScriptRoot is safer than $MyInvocation here)
if(-not $ModDir){ $ModDir = $PSScriptRoot }
if(-not $ModDir){ $ModDir = (Get-Location).Path }
if(-not $ZipOut){ $ZipOut = Join-Path (Split-Path -Parent $ModDir) 'DP-CameraUnbind.zip' }

if(Test-Path $ZipOut){ Remove-Item $ZipOut -Force }

# entry name (always forward slashes) -- mapped to a file on disk
$names = @(
    'mod.hjson',
    'icon.png',
    'README.md',
    'scripts/main.js',
    'bundles/bundle.properties',
    'bundles/bundle_zh_CN.properties',
    'bundles/bundle_zh_TW.properties'
)

if($WithDocs){
    $names += 'METHOD.md'
    $names += 'freecam-2-line.patch'
    foreach($f in (Get-ChildItem (Join-Path $ModDir 'tools') -File | Sort-Object Name)){
        $names += 'tools/' + $f.Name
    }
}

$fs = [System.IO.File]::Open($ZipOut, [System.IO.FileMode]::CreateNew)
try{
    $arch = New-Object System.IO.Compression.ZipArchive -ArgumentList $fs, ([System.IO.Compression.ZipArchiveMode]::Create)
    try{
        foreach($name in $names){
            $src = Join-Path $ModDir ($name -replace '/', '\')
            if(-not (Test-Path $src)){ throw "missing file: $src" }
            $entry = $arch.CreateEntry($name, [System.IO.Compression.CompressionLevel]::Optimal)
            $es = $entry.Open()
            try{
                $bytes = [System.IO.File]::ReadAllBytes($src)
                $es.Write($bytes, 0, $bytes.Length)
            } finally { $es.Dispose() }
        }
    } finally { $arch.Dispose() }
} finally { $fs.Dispose() }

Write-Output "packed: $ZipOut"
$z = [System.IO.Compression.ZipFile]::OpenRead($ZipOut)
try{
    foreach($e in $z.Entries){
        $bad = ''
        if($e.FullName.Contains('\')){ $bad = '   <-- BACKSLASH, arc cannot see it' }
        Write-Output ("  [{0}]  {1} B{2}" -f $e.FullName, $e.Length, $bad)
    }
} finally { $z.Dispose() }
