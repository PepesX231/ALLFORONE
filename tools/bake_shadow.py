"""Bake the soft drop shadow (and optional golden glow) into cast cutouts so the page needs no CSS filter
(filters on moving/animated images are the most expensive thing to draw on phones).
usage: python3 tools/bake_shadow.py src.webp dst.webp [glow]"""
import sys
from PIL import Image, ImageFilter, ImageChops
src, dst = sys.argv[1], sys.argv[2]; glow = len(sys.argv) > 3
im = Image.open(src).convert('RGBA'); w, h = im.size
pad = int(h * .08); W, H = w + pad * 2, h + pad * 2
a = Image.new('L', (W, H), 0); a.paste(im.getchannel('A'), (pad, pad))
out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
def layer(color, blur, dy, op):
    m = a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    m = ImageChops.offset(m, 0, dy)
    c = Image.new('RGBA', (W, H), color); c.putalpha(m); return c
if glow:
    out.alpha_composite(layer((255, 214, 130, 255), h * .035, 0, .95))
    out.alpha_composite(layer((255, 246, 208, 255), h * .006, 0, 1))
out.alpha_composite(layer((12, 18, 44, 255), h * .018, int(h * .02), .42))
out.alpha_composite(im, (pad, pad))
out.save(dst, quality=86, method=6); print(dst, out.size)
