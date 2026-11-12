# -*- coding: utf-8 -*-
import sys, os, math, subprocess, shutil, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from scipy.ndimage import gaussian_filter, binary_erosion
from timeline import SC, DUR, show_time, DOTS

W, H, FPS = 1280, 720, 24
NF = int(DUR * FPS)
FB = r'C:\Windows\Fonts\malgunbd.ttf'
def F(s): return ImageFont.truetype(FB, s)
def hx(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)
def sm(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def eob(t):
    t = min(1, max(0, t)); c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

PAL = {
 'intro':  dict(top='#0e1230', bot='#1c1840', acc='#ffc878', bands=['#E9C46A', '#F4A261', '#E76F51'], kw='#FFD666'),
 'value':  dict(top='#2a1410', bot='#40201a', acc='#ffbe50', bands=['#F4D35E', '#EE964B', '#F95738'], kw='#FFD666'),
 'ai':     dict(top='#06222c', bot='#0b3a44', acc='#5ae6dc', bands=['#9FE6DA', '#2A9D8F', '#1F6F78'], kw='#7EE0D0'),
 'exp':    dict(top='#2c0f22', bot='#451a35', acc='#ff96aa', bands=['#FFB5A7', '#F28482', '#E5698F'], kw='#FFAAA5'),
 'health': dict(top='#082219', bot='#103a2a', acc='#96f0a0', bands=['#B7E4C7', '#74C69D', '#40916C'], kw='#A8E6A0'),
 'outro':  dict(top='#0e1230', bot='#1c1840', acc='#ffc878', bands=['#E9C46A', '#F4A261', '#E76F51'], kw='#FFD666'),
}
for p in PAL.values():
    for k in ('top', 'bot', 'acc', 'kw'): p[k] = hx(p[k])
    p['bands'] = [hx(c) for c in p['bands']]

def pal_at(t):
    cur = 0
    for i, sc in enumerate(SC):
        if t >= sc['t0'] - 1e-9: cur = i
    P = PAL[SC[cur]['id']]
    if cur > 0:
        u = (t - SC[cur]['t0']) / 0.5
        if u < 1:
            Q = PAL[SC[cur - 1]['id']]; w = sm(0, 1, u)
            return dict(top=Q['top'] * (1 - w) + P['top'] * w, bot=Q['bot'] * (1 - w) + P['bot'] * w,
                        acc=Q['acc'] * (1 - w) + P['acc'] * w,
                        bands=[Q['bands'][i] * (1 - w) + P['bands'][i] * w for i in range(3)]), cur
    return P, cur

def blur_shadow(alpha, off, rad, op):
    sh = Image.new('RGBA', alpha.size, (8, 6, 18, 0))
    sh.putalpha(alpha.filter(ImageFilter.GaussianBlur(rad)).point(lambda v: int(v * op)))
    return ImageChops.offset(sh, off[0], off[1])

def stack(size, pieces):
    cv = Image.new('RGBA', size, (0, 0, 0, 0))
    for p in pieces:
        cv.alpha_composite(blur_shadow(p.getchannel('A'), (4, 6), 5, 0.4)); cv.alpha_composite(p)
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    out.alpha_composite(blur_shadow(cv.getchannel('A'), (8, 12), 10, 0.45)); out.alpha_composite(cv)
    return out

def piece(size, fn, color):
    im = Image.new('RGBA', size, (0, 0, 0, 0)); d = ImageDraw.Draw(im); fn(d, tuple(int(c) for c in color) + (255,)); return im

def star(cx, cy, r, n=4, k=0.3, rot=0):
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n + rot - math.pi / 2; rr = r if i % 2 == 0 else r * k
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts

def lens(cx, cy, L, Wd, ang):
    pts = []
    for i in range(41):
        s = i / 40; pts.append((s * L, Wd * math.sin(math.pi * s) ** 0.85))
    for i in range(40, -1, -1):
        s = i / 40; pts.append((s * L, -Wd * math.sin(math.pi * s) ** 0.85))
    c, sn = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * sn, cy + x * sn + y * c) for x, y in pts]

IC = 560
def make_icon(sid):
    S = (IC, IC); c = IC // 2
    if sid == 'intro':
        f = F(170); tw = ImageDraw.Draw(Image.new('L', (1, 1))).textlength('2027', font=f)
        f = F(int(170 * 500 / tw))
        def outline(d, col): d.text((c, c), '2027', font=f, fill=col, anchor='mm', stroke_width=14, stroke_fill=col)
        def back(d, col): d.text((c + 7, c + 8), '2027', font=f, fill=col, anchor='mm')
        def front(d, col): d.text((c, c), '2027', font=f, fill=col, anchor='mm')
        return stack(S, [piece(S, outline, (250, 243, 227)), piece(S, back, (231, 111, 81)), piece(S, front, (244, 197, 66))])
    if sid == 'value':
        return stack(S, [
            piece(S, lambda d, col: d.ellipse([c - 176, c - 174, c + 204, c + 206], fill=col), (201, 130, 43)),
            piece(S, lambda d, col: d.ellipse([c - 190, c - 190, c + 190, c + 190], fill=col), (244, 197, 66)),
            piece(S, lambda d, col: d.ellipse([c - 148, c - 148, c + 148, c + 148], fill=col), (251, 224, 138)),
            piece(S, lambda d, col: d.text((c, c - 4), '\u20a9', font=F(210), fill=col, anchor='mm'), (228, 87, 46)),
            piece(S, lambda d, col: d.polygon(star(c + 170, c - 170, 52), fill=col), (250, 243, 227)),
            piece(S, lambda d, col: d.polygon(star(c - 190, c + 160, 30), fill=col), (231, 111, 81))])
    if sid == 'ai':
        def pins(d, col):
            for i in range(5):
                o = c - 110 + i * 55
                d.rectangle([o - 9, c - 230, o + 9, c - 150], fill=col); d.rectangle([o - 9, c + 150, o + 9, c + 230], fill=col)
                d.rectangle([c - 230, o - 9, c - 150, o + 9], fill=col); d.rectangle([c + 150, o - 9, c + 230, o + 9], fill=col)
        return stack(S, [
            piece(S, pins, (159, 230, 218)),
            piece(S, lambda d, col: d.rounded_rectangle([c - 170, c - 170, c + 170, c + 170], 40, fill=col), (42, 157, 143)),
            piece(S, lambda d, col: d.rounded_rectangle([c - 115, c - 115, c + 115, c + 115], 26, fill=col), (18, 52, 59)),
            piece(S, lambda d, col: d.text((c, c - 4), 'AI', font=F(120), fill=col, anchor='mm'), (241, 250, 238)),
            piece(S, lambda d, col: d.polygon(star(c + 190, c - 200, 50), fill=col), (255, 150, 120))])
    if sid == 'exp':
        def fork(d, col):
            x = c - 215
            d.rounded_rectangle([x - 14, c - 20, x + 14, c + 200], 12, fill=col)
            d.rounded_rectangle([x - 36, c - 150, x + 36, c - 60], 14, fill=col)
            for dx in (-32, -10, 12): d.rounded_rectangle([x + dx, c - 195, x + dx + 20, c - 80], 8, fill=col)
        def knife(d, col):
            x = c + 215
            d.rounded_rectangle([x - 14, c - 10, x + 14, c + 200], 12, fill=col)
            d.polygon([(x - 18, c - 190), (x + 28, c - 160), (x + 28, c - 20), (x - 18, c - 20)], fill=col)
        return stack(S, [
            piece(S, fork, (154, 165, 177)), piece(S, knife, (154, 165, 177)),
            piece(S, lambda d, col: d.ellipse([c - 165, c - 150, c + 165, c + 180], fill=col), (250, 243, 227)),
            piece(S, lambda d, col: d.ellipse([c - 120, c - 105, c + 120, c + 135], fill=col), (234, 223, 200)),
            piece(S, lambda d, col: d.ellipse([c - 100, c - 85, c + 100, c + 115], fill=col), (250, 243, 227)),
            piece(S, lambda d, col: d.polygon(star(c + 120, c - 130, 100), fill=col), (242, 132, 130)),
            piece(S, lambda d, col: d.polygon(star(c - 110, c - 190, 45), fill=col), (244, 197, 66))])
    if sid == 'health':
        return stack(S, [
            piece(S, lambda d, col: d.ellipse([c - 190, c - 188, c + 210, c + 212], fill=col), (27, 67, 50)),
            piece(S, lambda d, col: d.ellipse([c - 200, c - 200, c + 200, c + 200], fill=col), (45, 106, 79)),
            piece(S, lambda d, col: d.polygon(lens(c - 150, c + 120, 330, 95, -0.75), fill=col), (82, 183, 136)),
            piece(S, lambda d, col: d.polygon(lens(c - 150, c + 120, 330, 12, -0.75), fill=col), (216, 243, 220)),
            piece(S, lambda d, col: d.polygon(lens(c + 20, c + 150, 190, 55, -2.3), fill=col), (149, 213, 178)),
            piece(S, lambda d, col: d.ellipse([c + 40, c + 20, c + 170, c + 150], fill=col), (239, 71, 111)),
            piece(S, lambda d, col: d.polygon(star(c + 105, c + 24, 34, 5, 0.45), fill=col), (45, 106, 79))])
    def bars(i):
        def fn(d, col):
            h = [120, 200, 290, 400][i]; x = c - 215 + i * 115
            d.rounded_rectangle([x, c + 210 - h, x + 88, c + 210], 14, fill=col)
        return fn
    cols = [(233, 196, 106), (244, 162, 97), (231, 111, 81), (42, 157, 143)]
    pcs = [piece(S, bars(i), cols[i]) for i in range(4)]
    def arrow(d, col):
        d.line([(c - 230, c + 20), (c + 170, c - 190)], fill=col, width=30)
        d.polygon([(c + 215, c - 215), (c + 90, c - 190), (c + 170, c - 90)], fill=col)
    pcs.append(piece(S, arrow, (250, 243, 227)))
    return stack(S, pcs)

def bubble_img(w, h, side, fill, back):
    M, T = 28, 26
    size = (w + 2 * M, h + 2 * M + T)
    r = min(34, h // 2)
    bk = Image.new('RGBA', size, (0, 0, 0, 0)); ImageDraw.Draw(bk).rounded_rectangle([M + 8, M + 9, M + w + 8, M + h + 9], r, fill=tuple(int(x) for x in back) + (255,))
    fr = Image.new('RGBA', size, (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
    col = tuple(int(x) for x in fill) + (255,)
    d.rounded_rectangle([M, M, M + w, M + h], r, fill=col)
    if side == 'L': d.polygon([(M + 26, M + h - 4), (M + 10, M + h + T), (M + 70, M + h - 4)], fill=col)
    else: d.polygon([(M + w - 26, M + h - 4), (M + w - 10, M + h + T), (M + w - 70, M + h - 4)], fill=col)
    return stack(size, [bk, fr]), M

BOT_BACK = np.array([238, 108, 77]); USER_BACK = np.array([42, 157, 143])
CREAM = np.array([251, 245, 234]); MUST = np.array([244, 196, 80])
GAP, BOTTOM = 22, 585
XL, XR = 80, 800
_dm = ImageDraw.Draw(Image.new('L', (1, 1)))

def build_msgs():
    msgs = []
    for sc in SC:
        P = PAL[sc['id']]
        for m in sc['msgs']:
            kw = m['kind'] == 'kw'
            f = F(46 if kw else 38); lines = m['text'].split('\n'); lh = int(f.size * 1.35)
            tw = max(_dm.textlength(l, font=f) for l in lines)
            w = int(max(tw + 70, 150)); h = int(len(lines) * lh + 44)
            fill = P['kw'] if kw else (MUST if m['side'] == 'R' else CREAM)
            back = USER_BACK if m['side'] == 'R' else (P['bands'][1] if kw else BOT_BACK)
            img, M = bubble_img(w, h, m['side'], fill, back)
            msgs.append(dict(side=m['side'], lines=lines, f=f, lh=lh, w=w, h=h, img=img, M=M,
                             tstart=sc['t0'] + m['t'], tshow=show_time(sc, m)))
    dots, dM = bubble_img(130, 70, 'L', CREAM, BOT_BACK)
    return msgs, dots, dM

def build_bands():
    BH = 200; y0 = H - BH; x = np.arange(W); y = np.arange(BH)[:, None]
    layers = []
    specs = [(110, 16, 2, 0.4, 7, 5, 1.3), (146, 14, 3, 1.9, 6, 7, 2.4), (182, 12, 2, 3.3, 5, 4, 0.7)]
    for base, a1, k1, ph1, a2, k2, ph2 in specs:
        e = base + a1 * np.sin(2 * np.pi * k1 * x / W + ph1) + a2 * np.sin(2 * np.pi * k2 * x / W + ph2)
        A = np.clip(y - e[None, :] + 0.5, 0, 1).astype(np.float32)
        S = gaussian_filter(np.roll(A, -7, axis=0), 7) * 0.55
        layers.append((A, S.astype(np.float32)))
    return y0, layers

def build_targets():
    pts = {}
    for sc in SC:
        a = np.array(make_icon(sc['id']).getchannel('A')) > 128
        edge = a & ~binary_erosion(a, iterations=3)
        ys, xs = np.nonzero(edge); ey = np.stack([xs, ys], 1)
        ys, xs = np.nonzero(a); iy = np.stack([xs, ys], 1)
        r = np.random.default_rng(1)
        sel = np.concatenate([ey[r.integers(0, len(ey), 1500)], iy[r.integers(0, len(iy), 500)]])
        pts[sc['id']] = sel.astype(np.float32) + np.array([1000 - IC // 2, 300 - IC // 2], np.float32)
    return pts

def sim_particles():
    N = 2800; r = np.random.default_rng(11)
    pos = r.uniform([0, 0], [W, H], (N, 2)).astype(np.float32); vel = np.zeros((N, 2), np.float32)
    bound = np.zeros(N, bool); bound[:2000] = True
    tg = build_targets(); out = np.zeros((NF, N, 2), np.float32)
    cur = -1; tgt = pos.copy()
    for fi in range(NF):
        t = fi / FPS
        si = max(i for i, sc in enumerate(SC) if sc['t0'] <= t + 1e-6)
        sc = SC[si]
        if si != cur:
            cur = si; P = tg[sc['id']]; tgt = P[r.integers(0, len(P), N)] + r.normal(0, 4, (N, 2)).astype(np.float32)
        u = t - sc['t0']; d = sc['t1'] - sc['t0']
        w = sm(0.1, 1.1, u) * (1 - sm(d - 0.7, d - 0.1, u))
        x, y = pos[:, 0], pos[:, 1]
        th = 1.6 * (np.sin(x * 0.0032 + t * 0.3) + np.cos(y * 0.004 - t * 0.23) + np.sin((x + y) * 0.002 + t * 0.17))
        flow = np.stack([np.cos(th), np.sin(th)], 1)
        kk = np.where(bound, 0.016 * w, 0.0)[:, None]
        vel += (tgt - pos) * kk + flow * (0.32 * (1 - 0.75 * w * bound))[:, None]
        vel *= 0.9; pos += vel
        pos[:, 0] %= W; pos[:, 1] %= H
        out[fi] = pos
    return out

class R:
    def __init__(self, traj):
        self.traj = traj; self.msgs, self.dots, self.dM = build_msgs()
        self.y0, self.layers = build_bands()
        self.icons = {sc['id']: make_icon(sc['id']) for sc in SC}
        self.tags = {}
        for sc in SC:
            f = F(30); tw = int(_dm.textlength(sc['tag'], font=f)) + 56
            im = Image.new('RGBA', (tw + 40, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.rounded_rectangle([20, 20, 20 + tw, 70], 14, fill=(250, 243, 227, 255))
            d.text((20 + tw // 2, 45), sc['tag'], font=f, fill=(28, 30, 52), anchor='mm')
            self.tags[sc['id']] = stack(im.size, [im]).rotate(2.5, resample=Image.BICUBIC, expand=True)
        self.grad = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        yy, xx = np.mgrid[0:H, 0:W]
        self.vig = (1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2).astype(np.float32)[..., None]
        self.grain = np.random.default_rng(5).normal(0, 2.2, (H, W, 1)).astype(np.float32)

    def particles(self, fi, pal, pulse):
        hw, hh = W // 2, H // 2; acc = np.zeros(hw * hh, np.float32)
        for k in range(6):
            j = max(0, fi - k); p = self.traj[j]
            ix = np.clip((p[:, 0] / 2).astype(int), 0, hw - 1); iy = np.clip((p[:, 1] / 2).astype(int), 0, hh - 1)
            acc += np.bincount(iy * hw + ix, minlength=hw * hh).astype(np.float32) * (0.72 ** k)
        acc = acc.reshape(hh, hw)
        core = gaussian_filter(acc, 0.8); glow = gaussian_filter(acc, 4.0) * 2.2
        v = (core * 0.9 + glow) * (1 + 0.5 * pulse)
        v = (1 - np.exp(-v * 1.1)).astype(np.float32)
        big = np.array(Image.fromarray(v).resize((W, H), Image.BILINEAR))[..., None]
        return big * (pal['acc'][None, None, :] * 0.85 + 70)

    def frame(self, fi):
        t = fi / FPS; pal, si = pal_at(t); sc = SC[si]
        pulse = 0
        for m in self.msgs:
            dt = t - m['tshow']
            if 0 <= dt < 0.5: pulse = max(pulse, math.exp(-dt * 7))
        bg = (pal['top'][None, None] * (1 - self.grad) + pal['bot'][None, None] * self.grad).astype(np.float32) * self.vig
        fr = (bg + self.particles(fi, pal, pulse)).astype(np.float32)
        reg = fr[self.y0:]
        for i, (A, S) in enumerate(self.layers):
            dx = int((t * (22 + 14 * i)) * (1 if i % 2 == 0 else -1))
            A2 = np.roll(A, dx, 1); S2 = np.roll(S, dx, 1)
            reg *= (1 - S2[..., None]); reg[:] = reg * (1 - A2[..., None]) + pal['bands'][i][None, None] * A2[..., None]
        im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))
        d0, d1 = sc['t0'], sc['t1']
        s = eob((t - d0) / 0.55) * ((1 - sm(d1 - 0.3, d1, t)) if si < len(SC) - 1 else 1)
        if s > 0.02:
            ic = self.icons[sc['id']]; sz = max(2, int(IC * s))
            ic2 = ic.resize((sz, sz), Image.BILINEAR) if sz != IC else ic
            ic2 = ic2.rotate(3 * math.sin(t * 1.1), resample=Image.BILINEAR)
            im.paste(ic2, (1000 - sz // 2, int(300 - sz // 2 + 8 * math.sin(t * 2))), ic2)
        tg = self.tags[sc['id']]; e = eob((t - d0) / 0.45)
        im.paste(tg, (60, int(24 - (1 - e) * 90)), tg)
        for i, m in enumerate(self.msgs):
            if t < m['tstart']: continue
            push = 0
            for j in range(i + 1, len(self.msgs)):
                mj = self.msgs[j]
                if t >= mj['tstart']: push += (mj['h'] + GAP) * sm(0, 1, (t - mj['tstart']) / 0.4)
            e = sm(0, 1, (t - m['tstart']) / 0.35)
            yb = BOTTOM - push + (1 - e) * 30
            ytop = yb - m['h']
            al = min(1, max(0, (ytop - 70) / 100)) * e
            if al <= 0.01: continue
            x = XL if m['side'] == 'L' else XR - m['w']
            typing = m['side'] == 'L' and t < m['tshow']
            if typing:
                img = self.dots.copy(); dd = ImageDraw.Draw(img); M = self.dM; hh = 70
                for k in range(3):
                    dy = -7 * max(0, math.sin(t * 9 - k * 0.9))
                    cx = M + 34 + k * 30
                    dd.ellipse([cx - 8, M + 35 + dy - 8, cx + 8, M + 35 + dy + 8], fill=(90, 92, 120, 255))
            else:
                pop = eob((t - m['tshow']) / 0.3); img = m['img'].copy(); M = m['M']; hh = m['h']
                dd = ImageDraw.Draw(img)
                n = sum(len(l) for l in m['lines'])
                shown = int(n * min(1, (t - m['tshow']) / 0.9)) if m['side'] == 'L' else n
                cnt = 0
                for li, l in enumerate(m['lines']):
                    k = max(0, min(len(l), shown - cnt)); cnt += len(l)
                    if k: dd.text((M + 35, M + 22 + li * m['lh']), l[:k], font=m['f'], fill=(28, 30, 52, 255))
                if pop < 0.999:
                    img = img.resize((max(2, int(img.width * (0.8 + 0.2 * pop))), max(2, int(img.height * (0.8 + 0.2 * pop)))), Image.BILINEAR)
            pos = (x - M, int(yb - hh - M))
            if al < 0.99:
                img.putalpha(img.getchannel('A').point(lambda v: int(v * al)))
            im.paste(img, pos, img)
        for s2 in SC[1:]:
            u = (t - (s2['t0'] - 0.35)) / 0.7
            if 0 <= u <= 1:
                ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(ov)
                for col, delay, wd in [(PAL[s2['id']]['bands'][2], 0.0, 0.5), (PAL[s2['id']]['bands'][0], 0.08, 0.42)]:
                    p = sm(0, 1, (u - delay) / (1 - 0.08)); cx = -0.5 * W + p * 2.0 * W
                    poly = [(cx - wd * W / 2 + 160, 0), (cx + wd * W / 2 + 160, 0), (cx + wd * W / 2 - 160, H), (cx - wd * W / 2 - 160, H)]
                    dd.polygon([(px - 10, py + 12) for px, py in poly], fill=(8, 6, 18, 90))
                    dd.polygon(poly, fill=tuple(int(c) for c in col) + (255,))
                im.paste(ov, (0, 0), ov)
        a = np.asarray(im).astype(np.float32)
        a += np.roll(self.grain, (fi * 7 % H, fi * 13 % W), (0, 1))
        a *= min(1, t / 0.3) * min(1, (DUR - t) / 0.4)
        return np.clip(a, 0, 255).astype(np.uint8)

def find_ff():
    p = shutil.which('ffmpeg')
    if p: return p
    c = glob.glob(os.path.expanduser(r'~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\ffmpeg.exe'), recursive=True)
    return c[0]

def work(args):
    a, b, traj_path, out = args
    r = R(np.load(traj_path))
    p = subprocess.Popen([find_ff(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(a, b): p.stdin.write(r.frame(fi).tobytes())
    p.stdin.close(); p.wait(); return out

if __name__ == '__main__':
    import multiprocessing as mp
    if len(sys.argv) > 1 and sys.argv[1] == 'still':
        np.save('traj.npy', sim_particles()); r = R(np.load('traj.npy'))
        for s in sys.argv[2:]: Image.fromarray(r.frame(int(float(s) * FPS))).save(f'still_{s}.png')
        sys.exit()
    np.save('traj.npy', sim_particles())
    n = max(2, min(os.cpu_count() or 4, 8)); edges = np.linspace(0, NF, n + 1).astype(int)
    jobs = [(int(edges[i]), int(edges[i + 1]), 'traj.npy', f'chunk{i}.mp4') for i in range(n)]
    with mp.Pool(n) as pool: outs = pool.map(work, jobs)
    open('list.txt', 'w').write(''.join(f"file '{o}'\n" for o in outs))
    subprocess.run([find_ff(), '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-i', 'final_audio.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '../외식트렌드2027_30초.mp4'])
    print('done')
