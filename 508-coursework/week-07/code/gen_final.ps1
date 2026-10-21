# Generate the final Week 7 comparison images through curl, one request at a
# time, because the free tier allows 1 image per 45 s per IP and the service
# answers 402 with a "Retry after Ns" hint when that is exceeded.
#
# Writes generated/final/<role>/seed<seed>.jpg and appends every step to
# generated/final/log.txt so progress can be watched while it runs.

$ErrorActionPreference = 'Continue'
$root = 'G:\workspeace\dhg508-workspace\508-coursework\week-07'
$out  = Join-Path $root 'generated\final'
$log  = Join-Path $out 'log.txt'
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format 'HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding utf8
    Write-Host $line
}

$jobs = @(
    @{ role='baseline';   seed=41; prompt='a photograph of an AK-47 rifle, side view, whole rifle, plain background' },
    @{ role='researched'; seed=11; prompt='full side view photograph of a 1953 Soviet AK-47 rifle, wooden buttstock, wooden handguards, brown wooden pistol grip, curved black steel magazine, no scope, plain white studio background, one complete rifle, nothing cropped' },
    @{ role='researched'; seed=23; prompt='1950s Soviet Kalashnikov rifle product photograph, full length side view, wood stock and wooden handguard, curved black magazine, tall front sight, white background' },
    @{ role='researched'; seed=37; prompt='vintage 1950s Soviet assault rifle with wooden stock, wooden handguards and a curved steel magazine, side view, white seamless background, museum catalogue photograph, whole rifle in frame' }
)

Log "start"

foreach ($job in $jobs) {
    $dir = Join-Path $out $job.role
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $file = Join-Path $dir ("seed{0}.jpg" -f $job.seed)
    if ((Test-Path $file) -and ((Get-Item $file).Length -gt 20000)) { Log "skip $($job.role)/$($job.seed) (exists)"; continue }

    $encoded = [uri]::EscapeDataString($job.prompt)
    $url = "https://image.pollinations.ai/prompt/$encoded`?width=1024&height=768&seed=$($job.seed)&nologo=true"

    for ($attempt = 1; $attempt -le 6; $attempt++) {
        Log "get $($job.role)/$($job.seed) attempt $attempt"
        $code = curl.exe -sS -L --max-time 180 -o $file -w "%{http_code}" $url 2>> $log
        $size = if (Test-Path $file) { (Get-Item $file).Length } else { 0 }
        if ($code -eq '200' -and $size -gt 20000) { Log "ok  $($job.role)/$($job.seed) bytes=$size"; break }
        $body = if (Test-Path $file) { Get-Content $file -Raw -ErrorAction SilentlyContinue } else { '' }
        Log "retry $($job.role)/$($job.seed) http=$code bytes=$size body=$($body.Substring(0, [Math]::Min(120, $body.Length)))"
        $wait = 50
        if ($body -match 'Retry after (\d+)s') { $wait = [int]$Matches[1] + 5 }
        Start-Sleep -Seconds $wait
    }
    Start-Sleep -Seconds 12
}

Log "done"
Get-ChildItem $out -Recurse -File | Select-Object FullName, Length | Format-Table -AutoSize
