# AK-47 Reference Image Collection - Batch 2 (Source: Wikimedia Commons)
# Usage: powershell -ExecutionPolicy Bypass -File .\download_ak47_images_batch2.ps1

$ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) educational coursework reference"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$urls = [ordered]@{
    "13_ak47_first_model_museum_view.jpg"     = "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cb/First_AK_47.jpg/1024px-First_AK_47.jpg"
    "14_ak47_athens_museum_3quarter_view.jpg" = "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a4/Soviet_automatic_rifle_AK_47_at_Athens_War_Museum_on_November_22%2C_2022.jpg/1280px-Soviet_automatic_rifle_AK_47_at_Athens_War_Museum_on_November_22%2C_2022.jpg"
    "15_ak47_type2_right_side_view.jpg"       = "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/57/AK-47_type_II_Part_DM-ST-89-01131.jpg/1280px-AK-47_type_II_Part_DM-ST-89-01131.jpg"
    "16_ak47_bolt_carrier_gas_piston.jpg"     = "https://upload.wikimedia.org/wikipedia/commons/f/fc/AK-Bolt-Carrier-Bolt-and-Gas_piston.jpg"
    "17_ak47_rear_sight_detail.jpg"           = "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/20/AK47-rear-sight.jpg/1280px-AK47-rear-sight.jpg"
    "18_ak47_type1_magazine.png"              = "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/bd/Type_1_AK-47_Magazine.png/1280px-Type_1_AK-47_Magazine.png"
    "19_ak47_aks_folding_stock.jpg"           = "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/96/AK_folding.jpg/1280px-AK_folding.jpg"
    "20_akm_muzzle_detail.jpg"                = "https://upload.wikimedia.org/wikipedia/commons/7/71/AKM_muzzle_brake.jpg"
}

function Test-Image($path) {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($path)[0..3]
        $sig = ($bytes | ForEach-Object { $_.ToString("X2") }) -join " "
        return ($sig -like "FF D8*" -or $sig -like "89 50*")
    } catch { return $false }
}

foreach ($item in $urls.GetEnumerator()) {
    $f = $item.Key
    $u = $item.Value

    if (Test-Path $f) {
        Write-Host "SKIP $f (exists)"
        continue
    }

    Write-Host "Downloading $f ..."
    try {
        Invoke-WebRequest -Uri $u -OutFile $f -UserAgent $ua -TimeoutSec 120
        if (Test-Image $f) {
            Write-Host "OK $f"
        } else {
            Write-Host "INVALID (not an image) $f - removing"
            Remove-Item $f -Force
        }
    } catch {
        Write-Host "FAIL $f : $($_.Exception.Message)"
        if (Test-Path $f) { Remove-Item $f -Force }
    }
    Start-Sleep -Seconds 10
}

Write-Host "Done. All files:"
Get-ChildItem -File | Where-Object { $_.Name -match "^\d\d_" } | Sort-Object Name | Select-Object Name, Length
