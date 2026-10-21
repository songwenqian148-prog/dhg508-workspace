# Tighter control: prompt B at the same seed as prompt A (seed 11), so the seed
# is held constant and the only variable is the added researched clauses.
$ErrorActionPreference = 'Continue'
$root = 'G:\workspeace\dhg508-workspace\508-coursework\week-07'
$dir  = Join-Path $root 'generated\final\researched'
$log  = Join-Path $root 'generated\final\log3.txt'
$out  = Join-Path $dir 'seed11_short_prompt.jpg'
$prompt = 'a photograph of an AK-47 rifle with a wooden stock and wooden handguard, no scope, side view, whole rifle, plain background'
$url = "https://image.pollinations.ai/prompt/$([uri]::EscapeDataString($prompt))?width=1024&height=768&seed=11&nologo=true"

function Log($m) { $line = "{0}  {1}" -f (Get-Date -Format 'HH:mm:ss'), $m; Add-Content -Path $log -Value $line -Encoding utf8; Write-Host $line }
Log "start seed11 control"
for ($i = 1; $i -le 5; $i++) {
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 20000)) { Log "already have it"; break }
    Log "attempt $i"
    $code = curl.exe -sS -L --max-time 120 -o $out -w "%{http_code}" $url 2>> $log
    $len = if (Test-Path $out) { (Get-Item $out).Length } else { 0 }
    if ($code -eq '200' -and $len -gt 20000) { Log "ok bytes=$len"; break }
    $body = if (Test-Path $out) { Get-Content $out -Raw -ErrorAction SilentlyContinue } else { '' }
    $wait = 60
    if ($body -match 'Retry after (\d+)s') { $wait = [int]$Matches[1] + 10 }
    Log "retry http=$code bytes=$len wait=$wait"
    Start-Sleep -Seconds $wait
}
Log "done"
