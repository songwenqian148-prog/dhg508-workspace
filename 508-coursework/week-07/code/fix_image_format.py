import pathlib, json
from PIL import Image
root = pathlib.Path(r"G:\workspeace\dhg508-workspace\508-coursework\week-07")
for p in sorted((root/"generated").rglob("seed*.png")):
    with Image.open(p) as im:
        print(p.name, im.format, im.size, p.stat().st_size)
        if im.format != "PNG":
            im.convert("RGB").save(p, "PNG")
            print("  converted to real PNG", p.stat().st_size)
