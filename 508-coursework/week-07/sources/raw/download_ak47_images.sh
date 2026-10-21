#!/bin/bash
# AK-47 Reference Image Collection Script (Source: Wikimedia Commons - Authoritative/CC Licensed)
# Usage: Run sequentially to avoid 429 rate limits from Wikimedia servers.
mkdir -p ak47_images
cd ak47_images || exit 1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) educational coursework reference"

# --- 1. GENERAL VIEWS / PROFILES (4 images) ---
wget -q --user-agent="$UA" -O 01_ak47_general_profile.png "https://upload.wikimedia.org/wikipedia/commons/3/37/AK-47.png" && echo "OK 01" ; sleep 5
wget -q --user-agent="$UA" -O 02_ak47_type1_vs_type2_profile.png "https://upload.wikimedia.org/wikipedia/commons/4/4e/AK-47_Type_1_and_2_%28cropped%29.png" && echo "OK 02" ; sleep 5
wget -q --user-agent="$UA" -O 03_ak47_type3_vs_aks47_profile.png "https://upload.wikimedia.org/wikipedia/commons/7/7e/AK-47_Type_3_and_AKS-47.png" && echo "OK 03" ; sleep 5
wget -q --user-agent="$UA" -O 04_ak47_high_res_museum_profile.jpg "https://upload.wikimedia.org/wikipedia/commons/2/27/Royal_Armouries_%E2%80%93_Up_Close_online_exhibition_%28AK-47%29.jpg" && echo "OK 04" ; sleep 5

# --- 2. DETAILED / COMPONENT VIEWS (5 images) ---
wget -q --user-agent="$UA" -O 05_ak47_bolt_carrier_detail.jpg "https://upload.wikimedia.org/wikipedia/commons/3/3b/AK-47_bolt_carrier_and_bolt.jpg" && echo "OK 05" ; sleep 5
wget -q --user-agent="$UA" -O 06_ak47_gas_system_diagram.png "https://upload.wikimedia.org/wikipedia/commons/7/7b/AK-47_gas_system_diagram.png" && echo "OK 06" ; sleep 5
wget -q --user-agent="$UA" -O 07_ak47_trigger_group_detail.jpg "https://upload.wikimedia.org/wikipedia/commons/f/f9/TAPCO_G2_AK-47_Trigger_Group_%26_AK_Hammer.jpg" && echo "OK 07" ; sleep 5
wget -q --user-agent="$UA" -O 08_ak47_magazine_detail.jpg "https://upload.wikimedia.org/wikipedia/commons/9/95/AK-47_magazine_closeup.jpg" && echo "OK 08" ; sleep 5
wget -q --user-agent="$UA" -O 09_ak47_receiver_detail.jpg "https://upload.wikimedia.org/wikipedia/commons/3/3b/AK-47_Type_1_Receiver.jpg" && echo "OK 09" ; sleep 5

# --- 3. DISASSEMBLED / EXPLODED VIEWS (6 images) ---
wget -q --user-agent="$UA" -O 10_ak47_cross_section_diagram.jpg "https://upload.wikimedia.org/wikipedia/commons/7/74/Typ-56-AK47-crossection-bayonet-removed.jpg" && echo "OK 10" ; sleep 5
wget -q --user-agent="$UA" -O 11_ak47_field_stripped_view.jpg "https://upload.wikimedia.org/wikipedia/commons/9/9b/AK-47_field_stripped.jpg" && echo "OK 11" ; sleep 5
wget -q --user-agent="$UA" -O 12_ak47_disassembled_parts_diagram.png "https://upload.wikimedia.org/wikipedia/commons/2/2e/AK-47_disassembly_parts_diagram.png" && echo "OK 12" ; sleep 5
wget -q --user-agent="$UA" -O 13_ak47_exploded_view.jpg "https://upload.wikimedia.org/wikipedia/commons/b/b0/AK-47_exploded_view.jpg" && echo "OK 13" ; sleep 5
wget -q --user-agent="$UA" -O 14_ak47_magazine_removed_detail.jpg "https://upload.wikimedia.org/wikipedia/commons/b/b7/AK-47_magazine_removed.jpg" && echo "OK 14" ; sleep 5
wget -q --user-agent="$UA" -O 15_ak47_parts_sheet_diagram.jpg "https://upload.wikimedia.org/wikipedia/commons/7/7c/AK-47_parts_list_and_diagram.jpg" && echo "OK 15" ; sleep 5

echo "Finished. Check files with: ls -l"
