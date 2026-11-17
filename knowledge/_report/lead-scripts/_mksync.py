
import io,os
ps = r'''param([switch]$What)
$src = '<scratch-dir>\kb-stage'
$dst = '<repo>\knowledge'
if (-not (Test-Path -LiteralPath $src)) { Write-Host "no src"; exit 1 }
$files = Get-ChildItem -LiteralPath $src -Recurse -File | Where-Object {
  $_.FullName -notmatch '\\__pycache__\\' -and $_.Name -notmatch '^_probe' -and $_.Extension -ne '.log'
}
$n = 0
foreach ($f in $files) {
  $rel = $f.FullName.Substring($src.Length).TrimStart('\')
  $target = Join-Path $dst $rel
  if ($What) { Write-Host "WOULD $rel"; continue }
  $dir = Split-Path -Parent $target
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Copy-Item -LiteralPath $f.FullName -Destination $target -Force
  $n++
}
Write-Host "synced $n files -> $dst"
'''
p = r'<scratch-dir>\kb-sync.ps1'
open(p,'w',encoding='utf-8-sig').write(ps)
print('written',os.path.getsize(p))
