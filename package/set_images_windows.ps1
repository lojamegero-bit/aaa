param(
 [Parameter(Mandatory=$true)][ValidateSet('COMPARISON','REFERENCE','DETAIL')][string]$Template,
 [Parameter(Mandatory=$true)][string]$Image1,
 [string]$Image2
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$fusion = Join-Path $env:APPDATA 'Blackmagic Design\DaVinci Resolve\Support\Fusion'
$assets = Join-Path $fusion 'ZBM_UI_SYSTEM_v1_1\Assets'
$setting = Join-Path $fusion ('Templates\Edit\Titles\ZBM UI v1.1\ZBM_'+$Template+'_v11.setting')
if (!(Test-Path $setting)) { throw 'Run install_windows.ps1 first.' }
if ($Template -eq 'COMPARISON' -and !$Image2) { throw 'COMPARISON needs -Image2 as well.' }
$files = @($Image1)
if ($Template -eq 'COMPARISON') { $files += $Image2 }
$text = [IO.File]::ReadAllText($setting)
Copy-Item $setting ($setting+'.backup.'+(Get-Date -Format 'yyyyMMdd_HHmmssfff'))
for ($i=0; $i -lt $files.Count; $i++) {
 $source = (Resolve-Path -LiteralPath $files[$i]).Path
 $id = $i+1
 $target = Join-Path $assets ('user_'+$Template+'_'+$id+'_'+[guid]::NewGuid().ToString('N')+'.png')
 $image = [Drawing.Image]::FromFile($source)
 try {
  $bitmap = New-Object Drawing.Bitmap($image.Width,$image.Height)
  try {
   $g = [Drawing.Graphics]::FromImage($bitmap)
   try { $g.DrawImageUnscaled($image,0,0) } finally { $g.Dispose() }
   $bitmap.Save($target,[Drawing.Imaging.ImageFormat]::Png)
  } finally { $bitmap.Dispose() }
 } finally { $image.Dispose() }
 $pattern = '(?s)(Image'+$id+' = Loader \{.*?Filename = ")[^"]*(")'
 $path = $target.Replace('\','/')
 $text = [regex]::Replace($text,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{param($m) $m.Groups[1].Value+$path+$m.Groups[2].Value})
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($setting,$text,$utf8)
Write-Host 'Updated defaults. Restart Resolve and place a NEW title instance.'
Write-Host 'Existing instances retain their original images. Adjust position/zoom in Inspector.'
