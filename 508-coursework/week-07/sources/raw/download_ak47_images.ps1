# AK-47 Reference Image Collection Script (Source: Wikimedia Commons)
# Usage: powershell -ExecutionPolicy Bypass -File .\download_ak47_images.ps1

$ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) educational coursework reference"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$urls = [ordered]@{
    "01_ak47_general_view.png"              = "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f8/AK-47.png/1280px-AK-47.png"
    "02_ak47_type1_type2_comparison.png"    = "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4e/AK-47_Type_1_and_2_%28cropped%29.png/1280px-AK-47_Type_1_and_2_%28cropped%29.png"
    "03_ak47_type3_aks47_comparison.png"    = "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7e/AK-47_Type_3_and_AKS-47.png/1280px-AK-47_Type_3_and_AKS-47.png"
    "04_ak47_type1_receiver_detail.jpg"     = "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/AK-47_Type_1_Receiver.jpg/1280px-AK-47_Type_1_Receiver.jpg"
    "05_ak47_trigger_group_detail.jpg"      = "https://upload.wikimedia.org/wikipedia/commons/2/23/TAPCO_G2_AK-47_Trigger_Group_%26_AK_Hammer.jpg"
    "06_ak47_royal_armouries_detail.jpg"    = "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/1a/Royal_Armouries_-_Up_Close_online_exhibition_-_Detail_of_centrefire_automatic_rifle%2C_Kalashnikov_AK%2C_1953._PR.5428_%2853528474954%29.jpg/1280px-Royal_Armouries_-_Up_Close_online_exhibition_-_Detail_of_centrefire_automatic_rifle%2C_Kalashnikov_AK%2C_1953._PR.5428_%2853528474954%29.jpg"
    "07_ak47_cross_section_diagram.jpg"     = "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/63/Typ-56-AK47-crossection-bayonet-removed.jpg/1280px-Typ-56-AK47-crossection-bayonet-removed.jpg"
    "08_ak47_disassembled_parts.jpg"        = "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/7c/AK-disassembled.jpg/1280px-AK-disassembled.jpg"
    "10_ak47_field_stripped.jpg"            = "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/15/Gp_wasr-10_63_Field_Stripped.jpg/1280px-Gp_wasr-10_63_Field_Stripped.jpg"
    "11_ak47_converted_parts.jpg"           = "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4f/Converted_Izhmash_AK_47.JPG/1280px-Converted_Izhmash_AK_47.JPG"
    "12_ak47_repair_disassembly.jpg"        = "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/1a/Weapons_repair_121115-A-YI377-0151.jpg/1280px-Weapons_repair_121115-A-YI377-0151.jpg"
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
        Write-Host "OK $f"
    } catch {
        Write-Host "FAIL $f : $($_.Exception.Message)"
        if (Test-Path $f) { Remove-Item $f -Force }
    }
    Start-Sleep -Seconds 8
}

Write-Host "Done. Files:"
Get-ChildItem | Select-Object Name, Length
