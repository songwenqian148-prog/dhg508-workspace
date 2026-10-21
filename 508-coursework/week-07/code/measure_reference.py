from PIL import Image
import numpy as np
p = r"G:\workspeace\dhg508-workspace\508-coursework\week-07\sources\raw\01_ak47_general_view.png"
im = Image.open(p).convert("RGB")
a = np.asarray(im).astype(int)
bg = a[2,2]
print("bg colour", bg)
dist = np.abs(a - bg).sum(axis=2)
mask = dist > 30
ys, xs = np.where(mask)
print("bbox x", xs.min(), xs.max(), "y", ys.min(), ys.max(), "len_px", xs.max()-xs.min()+1, "h_px", ys.max()-ys.min()+1)
x0,x1 = xs.min(), xs.max()
mm = 870.0/(x1-x0+1)
print(f"scale: {mm:.4f} mm/px")
step = max(1,(x1-x0)//36)
for x in range(x0, x1+1, step):
    col = np.where(mask[:, x])[0]
    if len(col)==0: continue
    print(f"x={x:4d} mm={(x-x0)*mm:6.1f} top={col.min():4d} bot={col.max():4d} thick_mm={(col.max()-col.min()+1)*mm:5.1f}")
