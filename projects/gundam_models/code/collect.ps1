# Copy the renders and exports out of the coursework workspace into this project.
#
# Blender cannot write here directly: the session sandbox only allows writes
# inside the coursework workspace, so build_*.py write to
# 508-coursework/week-07/artifacts/gundam/ and this script brings them across.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File code/collect.ps1

$ErrorActionPreference = 'Stop'
$project = 'G:\workspeace\dhg508-workspace\projects\gundam_models'
$source  = 'G:\workspeace\dhg508-workspace\508-coursework\week-07\artifacts\gundam'

if (-not (Test-Path $source)) { throw "nothing to collect: $source does not exist" }

$rendersOut = Join-Path $project 'generated\renders'
$modelOut   = Join-Path $project 'model'
New-Item -ItemType Directory -Force -Path $rendersOut, $modelOut | Out-Null

$renders = Get-ChildItem (Join-Path $source 'renders') -Filter *.png -File -ErrorAction SilentlyContinue
foreach ($file in $renders) {
    Copy-Item $file.FullName -Destination (Join-Path $rendersOut $file.Name) -Force
}
Write-Host "renders copied: $($renders.Count)"

$models = Get-ChildItem (Join-Path $source 'model') -File -ErrorAction SilentlyContinue
foreach ($file in $models) {
    Copy-Item $file.FullName -Destination (Join-Path $modelOut $file.Name) -Force
}
Write-Host "model files copied: $($models.Count)"

Get-ChildItem $rendersOut -File | Select-Object Name, Length | Format-Table -AutoSize
Get-ChildItem $modelOut -File | Select-Object Name, Length | Format-Table -AutoSize
