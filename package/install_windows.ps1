param([switch]$Force)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$fusion = Join-Path $env:APPDATA 'Blackmagic Design\DaVinci Resolve\Support\Fusion'
$assets = Join-Path $fusion 'ZBM_UI_SYSTEM_v1_1\Assets'
$titles = Join-Path $fusion 'Templates\Edit\Titles\ZBM UI v1.1'
if (!(Test-Path (Join-Path $PSScriptRoot 'Assets\COMPARISON_UI.png'))) { throw 'Extract the entire ZIP before running this script.' }
if ((Test-Path $titles) -and !$Force) { throw 'Already installed. To reinstall with a backup, run with -Force.' }
if (Test-Path $titles) { Copy-Item $titles ($titles+'.backup.'+(Get-Date -Format 'yyyyMMdd_HHmmssfff')) -Recurse }
New-Item -ItemType Directory -Force -Path $assets,$titles | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot 'Assets') -File | ForEach-Object { Copy-Item $_.FullName (Join-Path $assets $_.Name) -Force }
Get-ChildItem (Join-Path $PSScriptRoot 'Templates') -Filter '*.setting' | ForEach-Object {
 $s = [IO.File]::ReadAllText($_.FullName)
 $s = $s.Replace('__ZBM_ASSET_ROOT__',$assets.Replace('\','/'))
 [IO.File]::WriteAllText((Join-Path $titles $_.Name),$s,$utf8)
}
Write-Host 'Installed ZBM UI v1.1. Restart Resolve. Effects > Titles > ZBM UI v1.1.'
Write-Host 'Set Timeline FPS to match your timeline. Test all three titles before production use.'
