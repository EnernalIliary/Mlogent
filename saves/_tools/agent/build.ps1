# NOTE: keep this file pure ASCII. PowerShell 5.1 reads .ps1 as ANSI, so non-ASCII
# text here corrupts quoting/parens and the script dies with a parse error.
#
# Produces TWO artifacts next to this script:
#   CamAgent.jar    - agent classes only (MANIFEST.MF + CamAgent*.class)
#   cam-trace.jar   - tracing classes (CameraVec2, CamProbe)
# CamAgent.class MUST NOT ship inside cam-trace.jar, and CameraVec2.class MUST NOT
# ship inside CamAgent.jar: the -javaagent jar lands on the system class path, so a
# raw CameraVec2.class there would be loaded at its own name and break the shim.
$ErrorActionPreference = 'Stop'
$JDK   = 'C:\Program Files (x86)\Android\openjdk\jdk-17.0.14\bin'
$GAME  = 'E:\Program Files (x86)\Steam\steamapps\common\Mindustry'
$JAR   = Join-Path $GAME 'jre\desktop.jar'
$DIST  = $PSScriptRoot
$SRC   = Join-Path $PSScriptRoot 'src'
$TMP   = Join-Path $env:TEMP 'camagent'
$TSRC  = Join-Path $TMP 'src'
$TOUT  = Join-Path $TMP 'out'

Write-Host "== clean =="
if (Test-Path $TMP) { Remove-Item $TMP -Recurse -Force }
New-Item -ItemType Directory -Path $TSRC -Force | Out-Null
New-Item -ItemType Directory -Path $TOUT -Force | Out-Null

# javac cannot take non-ASCII path arguments from this shell, so copy to an ASCII temp dir first
Copy-Item (Join-Path $SRC '*.java') $TSRC -Force
Write-Host ("== copied sources to " + $TSRC + " ==")

Write-Host "== 1/4 compile tracing classes =="
& "$JDK\javac.exe" -nowarn -encoding UTF-8 -cp $JAR -d $TOUT (Join-Path $TSRC 'CameraVec2.java') (Join-Path $TSRC 'CamProbe.java')
if ($LASTEXITCODE -ne 0) { throw 'javac tracing classes failed' }

Write-Host "== 2/4 compile agent =="
# -encoding UTF-8 is required: these sources contain Chinese comments/strings
& "$JDK\javac.exe" -nowarn -encoding UTF-8 -cp "$TOUT;$JAR" -d $TOUT (Join-Path $TSRC 'CamAgent.java')
if ($LASTEXITCODE -ne 0) { throw 'javac agent failed' }
if (-not (Test-Path (Join-Path $TOUT 'CamAgent.class'))) { throw 'CamAgent.class was not produced' }
Get-ChildItem $TOUT -Filter '*.class' | ForEach-Object { Write-Host ("   compiled: " + $_.Name + " (" + $_.Length + ")") }

Add-Type -AssemblyName System.IO.Compression.FileSystem

function New-JarFromFiles($zipPath, $files, $manifestPath) {
  if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
  $zip = [System.IO.Compression.ZipFile]::Open($zipPath, 'Create')
  try {
    if ($manifestPath) {
      # MANIFEST.MF must be the first entry
      $entry = $zip.CreateEntry('META-INF/MANIFEST.MF')
      $es = $entry.Open()
      $bytes = [System.IO.File]::ReadAllBytes($manifestPath)
      $es.Write($bytes, 0, $bytes.Length)
      $es.Close()
    }
    foreach ($f in $files) {
      $entry = $zip.CreateEntry($f.Name)
      $es = $entry.Open()
      $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
      $es.Write($bytes, 0, $bytes.Length)
      $es.Close()
    }
  } finally { $zip.Dispose() }
}

Write-Host "== 3/4 pack cam-trace.jar =="
$traceFiles = @(Get-ChildItem $TOUT -Filter 'CameraVec2*.class') + @(Get-ChildItem $TOUT -Filter 'CamProbe*.class')
if ($traceFiles.Count -lt 2) { throw 'tracing classes missing' }
$tracePath = Join-Path $DIST 'cam-trace.jar'
New-JarFromFiles $tracePath $traceFiles $null

Write-Host "== 4/4 pack CamAgent.jar =="
$manifest = "Premain-Class: CamAgent`r`nCan-Retransform-Classes: true`r`nCan-Redefine-Classes: true`r`n`r`n"
$mf = Join-Path $TOUT 'MANIFEST.MF'
[System.IO.File]::WriteAllText($mf, $manifest, (New-Object System.Text.ASCIIEncoding))
# every agent class, including nested ones such as CamAgent$1.class - but never the tracing classes
$agentFiles = Get-ChildItem $TOUT -Filter 'CamAgent*.class' -Recurse | Sort-Object FullName
$agentPath = Join-Path $DIST 'CamAgent.jar'
New-JarFromFiles $agentPath $agentFiles $mf

foreach ($dest in @($agentPath, $tracePath)) {
  Write-Host ""
  Write-Host ("== artifact: " + $dest + "  " + (Get-Item $dest).Length + " bytes ==")
  $z = [System.IO.Compression.ZipFile]::OpenRead($dest)
  try { foreach ($e in $z.Entries) { Write-Host ("   " + $e.FullName + "  (" + $e.Length + ")") } } finally { $z.Dispose() }
}
