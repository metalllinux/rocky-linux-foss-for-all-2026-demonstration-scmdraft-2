from PIL import Image
W=H=256
def fill(x,y):
    dx=x-72;dy=y-128
    if dx*dx+dy*dy<=70*70: return 2
    if 150<=x<=230 and 70<=y<=190:
        inner=(170<=x<=210) and (100<=y<=160); return 1 if inner else 2
    return 1
img=Image.new("RGB",(W,H))
px=img.load(); fg=0
for y in range(H):
    for x in range(W):
        v=fill(x,y); px[x,y]=(230,40,40) if v==2 else (30,90,30)
        if v==2: fg+=1
img.save("/home/howard/AI/demo-evidence/t0042-mask-full.png")
img.resize((W//4,H//4), Image.LANCZOS).save("/home/howard/AI/demo-evidence/t0042-mask-booth4x.png")
print("fg tiles",fg,"coverage %.3f"%(fg/(W*H)),"shape area fg=%d"%(fg))
