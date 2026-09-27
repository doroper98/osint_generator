import pickle, cairo, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from common import *

G = pickle.load(open('/home/claude/geo.pkl', 'rb'))


def polys(g):
    if g.is_empty:
        return []
    t = g.geom_type
    if t == 'Polygon':
        return [g]
    if t in ('MultiPolygon', 'GeometryCollection'):
        out = []
        for x in g.geoms:
            out += polys(x)
        return out
    return []


def lines(g):
    t = g.geom_type
    if t == 'LineString':
        return [g]
    if t in ('MultiLineString', 'GeometryCollection'):
        out = []
        for x in g.geoms:
            out += lines(x)
        return out
    return []


def path_poly(ctx, p, ppd):
    for ring in [p.exterior] + list(p.interiors):
        xy = np.array(ring.coords)
        X, Y = proj(xy[:, 0], xy[:, 1], ppd)
        ctx.move_to(X[0], Y[0])
        for x, y in zip(X[1:], Y[1:]):
            ctx.line_to(x, y)
        ctx.close_path()


def path_line(ctx, l, ppd):
    xy = np.array(l.coords)
    X, Y = proj(xy[:, 0], xy[:, 1], ppd)
    ctx.move_to(X[0], Y[0])
    for x, y in zip(X[1:], Y[1:]):
        ctx.line_to(x, y)


def surf_to_np(s):
    w, h = s.get_width(), s.get_height()
    a = np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :w]
    return a  # BGRA premultiplied


LAND_COL = {'UKR': '#1d3350', 'RUS': '#2b2227', 'BLR': '#29232a'}
DEFAULT_LAND = '#1b2029'

# --- distance-to-coast field at low res (shared)
PPD_LO = 25
wl, hl = size_at(PPD_LO)
s = cairo.ImageSurface(cairo.FORMAT_A8, wl, hl)
c = cairo.Context(s)
for p in polys(G['land'].simplify(0.02)):
    path_poly(c, p, PPD_LO)
c.fill()
mask_lo = np.ndarray((hl, s.get_stride()), np.uint8, s.get_data())[:, :wl] > 127
dist = ndimage.distance_transform_edt(~mask_lo) / PPD_LO   # degrees
t = np.clip(dist / 1.1, 0, 1) ** 0.55
coast = np.array(hexrgb('#16475e'))
deep = np.array(hexrgb('#050e18'))
sea_lo = coast[None, None] * (1 - t[..., None]) + deep[None, None] * t[..., None]
# gentle large-scale light from upper-left
yy, xx = np.mgrid[0:hl, 0:wl]
light = 1.0 + 0.18 * np.exp(-(((xx - wl * 0.55) / (wl * 0.6)) ** 2 + ((yy - hl * 0.55) / (hl * 0.6)) ** 2))
sea_lo = np.clip(sea_lo * light[..., None], 0, 1)
sea_lo_img = Image.fromarray((sea_lo * 255).astype(np.uint8))

rng = np.random.default_rng(7)
noise_lo = ndimage.gaussian_filter(rng.standard_normal((hl, wl)), 1.2)
noise_lo = noise_lo / np.abs(noise_lo).max()
noise_lo2 = ndimage.gaussian_filter(rng.standard_normal((hl * 4, wl * 4)), 1.0)
noise_lo2 = noise_lo2 / np.abs(noise_lo2).max()

MAJOR = {'Dnieper', 'Danube', 'Don', 'Volga', 'Donets', 'Dniester', 'Desna', 'Prypiat', 'Kuban'}

for ppd in LEVELS:
    W, H = size_at(ppd)
    k = ppd / 100.0
    print('level', ppd, W, H, flush=True)
    base = sea_lo_img.resize((W, H), Image.BICUBIC)

    # ---- land fills
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    tol = 0.3 / ppd
    for a3, g in G['countries'].items():
        c.set_source_rgb(*hexrgb(LAND_COL.get(a3, DEFAULT_LAND)))
        for p in polys(g.simplify(tol)):
            path_poly(c, p, ppd)
        c.fill()
    # lakes / reservoirs
    c.set_source_rgb(*hexrgb('#0c2436'))
    for lg in G['lakes']:
        for p in polys(lg.simplify(tol)):
            path_poly(c, p, ppd)
        c.fill()
    s.flush()
    A = surf_to_np(s)
    N1 = Image.fromarray(((noise_lo + 1) * 127.5).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    N2 = Image.fromarray(((noise_lo2 + 1) * 127.5).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    N1 = np.asarray(N1); N2 = np.asarray(N2)
    B = np.asarray(base)
    out8 = np.empty((H, W, 3), np.uint8)
    alpha8 = np.empty((H, W), np.uint8)
    for r0 in range(0, H, 700):
        r1 = min(H, r0 + 700)
        a = A[r0:r1].astype(np.float32)
        al = a[..., 3:4] / 255.0
        tex = 1.0 + 0.10 * (N1[r0:r1].astype(np.float32) / 127.5 - 1) + 0.05 * (N2[r0:r1].astype(np.float32) / 127.5 - 1)
        o = B[r0:r1].astype(np.float32) * (1 - al) + a[..., [2, 1, 0]] * tex[..., None]
        out8[r0:r1] = np.clip(o, 0, 255).astype(np.uint8)
        alpha8[r0:r1] = A[r0:r1, :, 3]
    del A, N1, N2, B, base, s, c
    alpha = alpha8
    # ---- coast glow (outer, on water)
    m = Image.fromarray(alpha)
    rad = max(2, 7 * k)
    grow = m.filter(ImageFilter.GaussianBlur(rad))
    G8 = np.asarray(grow); M8 = alpha
    col = np.array([40, 150, 175], np.float32) * 0.55
    for r0 in range(0, H, 700):
        r1 = min(H, r0 + 700)
        glow = np.clip(G8[r0:r1].astype(np.float32) - M8[r0:r1].astype(np.float32), 0, 255) / 255.0 * 1.6
        o = out8[r0:r1].astype(np.float32) + glow[..., None] * col
        out8[r0:r1] = np.clip(o, 0, 255).astype(np.uint8)
    del grow, G8, m
    img = Image.fromarray(out8)
    del out8, alpha, alpha8

    # ---- vector details: graticule, rivers, coast line, borders, oblasts
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    # graticule
    c.set_source_rgba(1, 1, 1, 0.045)
    c.set_line_width(max(0.6, 0.9 * k))
    for lon in range(18, 47, 2):
        x, _ = proj(lon, LAT1, ppd)
        c.move_to(float(x), 0); c.line_to(float(x), H)
    for lat in range(40, 58, 2):
        _, y = proj(LON0, lat, ppd)
        c.move_to(0, float(y)); c.line_to(W, float(y))
    c.stroke()
    # rivers
    for nm, sr, g in G['rivers']:
        major = nm in MAJOR
        c.set_source_rgba(*hexrgb('#3b86ad', 0.55 if major else 0.32))
        c.set_line_width(max(0.7, (1.8 if major else 1.0) * k))
        for l in lines(g.simplify(tol)):
            path_line(c, l, ppd)
        c.stroke()
    # Ukrainian oblast borders (faint, dashed)
    if ppd >= 100:
        c.set_source_rgba(1, 1, 1, 0.13)
        c.set_line_width(0.9 * k)
        c.set_dash([4 * k, 3 * k])
        for code, g in G['oblasts'].items():
            for p in polys(g.simplify(tol)):
                path_poly(c, p, ppd)
            c.stroke()
        c.set_dash([])
    # coastline crisp
    c.set_source_rgba(*hexrgb('#5cc3d6', 0.45))
    c.set_line_width(max(0.6, 0.9 * k))
    for p in polys(G['land'].simplify(tol)):
        path_poly(c, p, ppd)
    c.stroke()
    # country borders
    c.set_source_rgba(*hexrgb('#b8c2d0', 0.42))
    c.set_line_width(max(0.7, 1.1 * k))
    for a3, g in G['countries'].items():
        for p in polys(g.simplify(tol)):
            path_poly(c, p, ppd)
        c.stroke()
    s.flush()
    ov = surf_to_np(s)
    ov_img = Image.frombuffer('RGBA', (W, H), ov[..., [2, 1, 0, 3]].copy().tobytes(), 'raw', 'RGBa', 0, 1)
    img = img.convert('RGBA')
    img.alpha_composite(ov_img)
    img = img.convert('RGB')
    img.save(f'/home/claude/base_{ppd}.png', optimize=False, compress_level=1)
    del img, ov, ov_img, s, c
print('done')
