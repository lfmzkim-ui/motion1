import base64, io, json, sys
from PIL import Image, ImageFilter, ImageChops
import numpy as np

def b64(im, fmt, **kw):
    buf = io.BytesIO(); im.save(buf, fmt, **kw)
    return "data:image/%s;base64,%s" % (fmt.lower(), base64.b64encode(buf.getvalue()).decode())

def sticker(path, H=1000, r=7):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
    s = H / im.height
    im = im.resize((round(im.width * s), H), Image.LANCZOS)
    pad = r + 4
    canvas = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    canvas.paste(im, (pad, pad))
    a = canvas.getchannel("A")
    d = a.filter(ImageFilter.MaxFilter(2 * r + 1)).filter(ImageFilter.GaussianBlur(1.2))
    d = d.point(lambda v: 255 if v > 90 else 0).filter(ImageFilter.GaussianBlur(0.8))
    white = Image.new("RGBA", canvas.size, (245, 245, 242, 255)); white.putalpha(d)
    out = Image.alpha_composite(white, canvas)
    return out

def logo(path, mode, W):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).astype(float)
    mn = arr.min(axis=2)
    alpha = np.clip((255 - mn) * 1.2 - 12, 0, 255)
    red = np.clip((arr[:, :, 0] - arr[:, :, 1:].max(axis=2)) / 110.0, 0, 1)
    if mode == "white":
        red[:] = 0
    col = np.zeros(arr.shape)
    base = np.array([245, 245, 242.0]); rc = np.array([196, 24, 28.0])
    for i in range(3):
        col[:, :, i] = base[i] * (1 - red) + rc[i] * red
    rgba = np.dstack([col, alpha]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    out = out.crop(out.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox())
    s = W / out.width
    return out.resize((W, round(out.height * s)), Image.LANCZOS)

assets = {}
for i in range(1, 10):
    im = sticker("img/%d.webp" % i)
    assets["m%d" % i] = {"src": b64(im, "WEBP", quality=86, method=6), "w": im.width, "h": im.height}
L1 = logo("img/10.jpg", "color", 640); assets["logoMark"] = {"src": b64(L1, "PNG", optimize=True), "w": L1.width, "h": L1.height}
L2 = logo("img/11.jpg", "white", 1000); assets["logoWide"] = {"src": b64(L2, "PNG", optimize=True), "w": L2.width, "h": L2.height}
L3 = logo("img/11.jpg", "color", 1000); assets["logoWideColor"] = {"src": b64(L3, "PNG", optimize=True), "w": L3.width, "h": L3.height}
for k, v in assets.items(): print(k, v["w"], v["h"], len(v["src"]) // 1024, "KB")
if len(sys.argv) > 1 and sys.argv[1] == "assets": 
    for k in ("logoMark","logoWide"):
        open("preview_%s.png" % k, "wb").write(base64.b64decode(assets[k]["src"].split(",")[1]))
    sys.exit()
tpl = open("src.html", encoding="utf-8").read()
ats=[0.2,12.3,18.7,30.3,36.7,50.3,56.7,70.3,76.7,90.3,96.7,108.9]
voice=[{"at":ats[i],"b64":base64.b64encode(open("voice2/t%d.mp3"%i,"rb").read()).decode()} for i in range(12)]
html = tpl.replace("__ASSETS__", json.dumps(assets)).replace("__VOICE__", json.dumps(voice))
open("../agujjim_top5.html", "w", encoding="utf-8").write(html)
print("built", len(html) // 1024, "KB")
