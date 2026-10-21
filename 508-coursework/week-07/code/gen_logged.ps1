# One request at a time, 60 s apart, with the 402 retry hint honoured.
# Logs to generated/final/log2.txt so progress can be watched.

$ErrorActionPreference = 'Continue'
$root = 'G:\workspeace\dhg508-workspace\508-coursework\week-07'
$dir  = Join-Path $root 'generated\final\researched'
$log  = Join-Path $root 'generated\final\log2.txt'
New-Item -ItemType Directory -Force -Path $dir | Out-Null

function Log($m) {
    $line = "{0}  {1}" -f (Get-Date -Format 'HH:mm:ss'), $m
    Add-Content -Path $log -Value $line -Encoding utf8
    Write-Host $line
}

$tests = @(
    @{ file='wooden_stock.jpg'; seed=61; prompt='a photograph of an AK-47 rifle with a wooden stock and wooden handguard, no scope, side view, whole rifle, plain background' },
    @{ file='soviet_1950s.jpg'; seed=62; prompt='a 1950s Soviet AK-47 rifle with wooden stock, wooden handguard and curved steel magazine, side view, plain background' }
)

Log 'start'
foreach ($t in $tests) {
    $out = Join-Path $dir $t.file
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 20000)) { Log "skip $($t.file)"; continue }
    $url = "https://image.pollinations.ai/prompt/$([uri]::EscapeDataString($t.prompt))`?width=1024&height=768&seed=$($t.seed)&nologo=true"
    for ($i = 1; $i -le 6; $i++) {
        Log "get $($t.file) attempt $i"
        $code = curl.exe -sS -L --max-time 120 -o $out -w "%{http_code}" $url 2>> $log
        $len = if (Test-Path $out) { (Get-Item $out).Length } else { 0 }
        if ($code -eq '200' -and $len -gt 20000) { Log "ok $($t.file) bytes=$len"; break }
        $body = if (Test-Path $out) { Get-Content $out -Raw -ErrorAction SilentlyContinue } else { '' }
        Log "retry $($t.file) http=$code bytes=$len"
        $wait = 65
        if ($body -match 'Retry after (\d+)s') { $wait = [Math]::Max([int]$Matches[1] + 10, 40) }
        Start-Sleep -Seconds $wait
    }
    Start-Sleep -Seconds 65
}
Log 'done'
Get-ChildItem $dir -File | Select-Object Name, Length | Format-Table -AutoSize
