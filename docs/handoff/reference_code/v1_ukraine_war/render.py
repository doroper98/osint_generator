import sys, math, pickle, subprocess, time
import numpy as np, cairo
from PIL import Image
from shapely.geometry import LineString, Point
from common import *
import timeline as TL
import events as EV

G = pickle.load(open('/home/claude/geo.pkl', 'rb'))
BASE = {}
for ppd in LEVELS:
    im = Image.open(f'/home/claude/base_{ppd}.png').convert('RGB'); im.load(); BASE[ppd] = im
W0, H0 = BASE[200].size
N = int(TL.TOTAL * FPS)

SANS = 'Noto Sans CJK KR'
SERIF = 'Noto Serif CJK KR'
FONT = {  # name -> (family, weight)
    'sans': (SANS, cairo.FONT_WEIGHT_NORMAL), 'sansb': (SANS, cairo.FONT_WEIGHT_BOLD),
    'sansm': (SANS + ' Medium', cairo.FONT_WEIGHT_NORMAL), 'sansl': (SANS + ' Light', cairo.FONT_WEIGHT_NORMAL),
    'sanst': (SANS + ' Thin', cairo.FONT_WEIGHT_NORMAL), 'sansk': (SANS + ' Black', cairo.FONT_WEIGHT_NORMAL),
    'serif': (SERIF, cairo.FONT_WEIGHT_NORMAL), 'serifb': (SERIF, cairo.FONT_WEIGHT_BOLD),
}

C = {  # palette
    'ru': hexrgb('#ff3b4e'), 'ru2': hexrgb('#d7263d'), 'ua': hexrgb('#3da5ff'), 'gold': hexrgb('#f2c14e'),
    'white': (1, 1, 1), 'teal': hexrgb('#5cc3d6'), 'grey': hexrgb('#9aa6b5'), 'olive': hexrgb('#a8b86a'),
    'orange': hexrgb('#ff9f1c'), 'water': hexrgb('#38b6ff'), 'dark': hexrgb('#0a0f16'), 'yellow': hexrgb('#ffd23f'),
}


# ------------------------------------------------------------------ helpers
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def window(t, t0, t1, fin=0.6, fout=0.6):
    if t < t0 or t > t1:
        return 0.0
    a = smooth((t - t0) / fin) if fin > 0 else 1.0
    b = smooth((t1 - t) / fout) if fout > 0 else 1.0
    return min(a, b)


def P200(lon, lat):
    x, y = proj(lon, lat, 200)
    return np.stack([np.atleast_1d(x), np.atleast_1d(y)], -1)


def rings_of(g, tol):
    out = []
    if g is None or g.is_empty:
        return out
    gg = g.simplify(tol) if tol else g
    stack = [gg]
    while stack:
        h = stack.pop()
        t = h.geom_type
        if t == 'Polygon':
            for r in [h.exterior] + list(h.interiors):
                xy = np.array(r.coords)
                if len(xy) >= 3:
                    out.append(P200(xy[:, 0], xy[:, 1]))
        elif t in ('MultiPolygon', 'GeometryCollection'):
            stack += list(h.geoms)
    return out


def lines_of(g, tol=0):
    out = []
    gg = g.simplify(tol) if tol else g
    stack = [gg]
    while stack:
        h = stack.pop()
        if h.geom_type == 'LineString':
            xy = np.array(h.coords); out.append(P200(xy[:, 0], xy[:, 1]))
        elif h.geom_type in ('MultiLineString', 'GeometryCollection'):
            stack += list(h.geoms)
    return out


class Geo:
    """geometry pre-projected to level-0 px, two LODs"""
    cache = {}

    @classmethod
    def get(cls, key):
        if key not in cls.cache:
            g = G['snap'][key] if isinstance(key, str) else key
            cls.cache[key] = (rings_of(g, 0.003), rings_of(g, 0.012))
        return cls.cache[key]


def catmull(pts, n=16):
    pts = np.asarray(pts, float)
    if len(pts) < 3:
        t = np.linspace(0, 1, n)[:, None]
        return pts[0] * (1 - t) + pts[-1] * t
    P = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


# ------------------------------------------------------------------ camera
def build_camera():
    cams = sorted(EV.CAM, key=lambda c: c[0])
    lon = np.zeros(N); lat = np.zeros(N); w = np.zeros(N)
    cur = np.array(cams[0][1:4], float)
    frm = cur.copy(); k = 0; active = None; arrived = 0.0
    for i in range(N):
        t = i / FPS
        while k < len(cams) and cams[k][0] <= t:
            # start new move from current position
            frm = np.array([lon[i - 1], lat[i - 1], w[i - 1]]) if i > 0 else cur.copy()
            active = cams[k]; k += 1
        if active is None:
            v = cur.copy(); dt_arr = t
        else:
            t0, tl, ta, tw, dur = active[:5]
            e = ease_io((t - t0) / dur) if dur > 0 else 1.0
            lo = frm[0] + (tl - frm[0]) * e
            la = frm[1] + (ta - frm[1]) * e
            wl = math.exp(math.log(frm[2]) + (math.log(tw) - math.log(frm[2])) * e)
            dist = math.hypot((tl - frm[0]) * math.cos(math.radians(ta)), ta - frm[1])
            peak = max(frm[2], tw, dist * 1.35)
            bump = (peak - max(frm[2], tw)) * math.sin(math.pi * e)
            v = np.array([lo, la, wl + max(0, bump)])
            dt_arr = t - (t0 + dur)
        # slow ken-burns drift after arrival
        if dt_arr > 0:
            v[2] *= 1 - 0.035 * (1 - math.exp(-dt_arr / 7.0))
        lon[i], lat[i], w[i] = v
    return lon, lat, w


CAM_LON, CAM_LAT, CAM_W = build_camera()


class View:
    def __init__(self, i):
        self.lon, self.lat, self.w = CAM_LON[i], CAM_LAT[i], CAM_W[i]
        cx, cy = proj(self.lon, self.lat, 200)
        wpx = self.w * 200; hpx = wpx * H_OUT / W_OUT
        self.bx0 = float(min(max(cx - wpx / 2, 0), W0 - wpx))
        self.by0 = float(min(max(cy - hpx / 2, 0), H0 - hpx))
        self.wpx, self.hpx = wpx, hpx
        self.s = W_OUT / wpx
        self.fine = self.w < 8.0

    def sc(self, P):
        P = np.asarray(P, float)
        return (P - (self.bx0, self.by0)) * self.s

    def geo(self, lon, lat):
        x, y = proj(lon, lat, 200)
        return (float(x) - self.bx0) * self.s, (float(y) - self.by0) * self.s

    def base(self):
        for ppd in (50, 100, 200):
            if self.w * ppd >= W_OUT * 0.98 or ppd == 200:
                break
        f = ppd / 200.0
        box = (self.bx0 * f, self.by0 * f, (self.bx0 + self.wpx) * f, (self.by0 + self.hpx) * f)
        return BASE[ppd].resize((W_OUT, H_OUT), Image.BILINEAR, box=box)


# ------------------------------------------------------------------ drawing primitives
def font(ctx, name, size):
    fam, wt = FONT[name]
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, wt)
    ctx.set_font_size(size)


def tw(ctx, s):
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, fname='sansb', color=(1, 1, 1), alpha=1.0, halo=3.0, anchor='l', halo_a=0.8, spacing=0.0):
    if alpha <= 0.01 or not s:
        return
    font(ctx, fname, size)
    width = tw(ctx, s) + spacing * max(0, len(s) - 1)
    if anchor == 'c':
        x -= width / 2
    elif anchor == 'r':
        x -= width
    ctx.new_path()
    if spacing:
        xx = x
        for ch in s:
            ctx.move_to(xx, y); ctx.text_path(ch); xx += tw(ctx, ch) + spacing
    else:
        ctx.move_to(x, y); ctx.text_path(s)
    if halo > 0:
        ctx.set_source_rgba(0.02, 0.04, 0.07, halo_a * alpha)
        ctx.set_line_width(halo); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()
    return width


def ring_path(ctx, R):
    ctx.move_to(*R[0])
    for x, y in R[1:]:
        ctx.line_to(x, y)
    ctx.close_path()


def poly_path(ctx, view, key):
    fine, coarse = Geo.get(key)
    rings = fine if view.fine else coarse
    ctx.new_path()
    n = 0
    for R in rings:
        S = view.sc(R)
        mn = S.min(0); mx = S.max(0)
        if mx[0] < -50 or mx[1] < -50 or mn[0] > W_OUT + 50 or mn[1] > H_OUT + 50:
            continue
        if (mx - mn).max() < 1.5:
            continue
        ring_path(ctx, S); n += 1
    return n


def make_hatch(col, spacing=7, width=1.3, alpha=0.55):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, spacing, spacing)
    c = cairo.Context(s)
    c.set_source_rgba(*col, alpha); c.set_line_width(width)
    c.move_to(-1, spacing + 1); c.line_to(spacing + 1, -1)
    c.move_to(-1, 1); c.line_to(1, -1)
    c.move_to(spacing - 1, spacing + 1); c.line_to(spacing + 1, spacing - 1)
    c.stroke()
    p = cairo.SurfacePattern(s); p.set_extend(cairo.EXTEND_REPEAT)
    return p


HATCH = {'ru': make_hatch(C['ru']), 'ua': make_hatch(C['ua']), 'water': make_hatch(C['water'], 6, 1.0, 0.4),
         'gold': make_hatch(C['gold'], 8, 1.0, 0.4)}
AREA_STYLE = {  # fill color, fill alpha, hatch, edge color, edge width
    'ru': (C['ru2'], 0.24, 'ru', C['ru'], 1.6),
    'ua': (C['ua'], 0.22, 'ua', C['ua'], 1.6),
    'water': (C['water'], 0.35, 'water', C['water'], 0.8),
    'gold': (C['gold'], 0.10, 'gold', C['gold'], 2.0),
    'amber': (C['orange'], 0.14, None, C['orange'], 1.8),
    'redline': (C['ru'], 0.0, None, C['ru'], 2.0),
}


def draw_area(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], e.get('fade', 0.8), e.get('fade_out', 0.8))
    if a <= 0.01:
        return
    fc, fa, hatch, ec, ew = AREA_STYLE[e.get('style', 'ru')]
    if e.get('pulse'):
        a *= 0.75 + 0.25 * math.sin((t - e['t0']) * 3.2)
    ctx.save()
    if e.get('grow'):
        glon, glat = e['grow']
        gx, gy = view.geo(glon, glat)
        r = ease_out((t - e['t0']) / e.get('grow_dur', 1.6)) * 1200
        ctx.arc(gx, gy, max(r, 0.1), 0, 2 * math.pi); ctx.clip()
    if poly_path(ctx, view, e['geom']) == 0:
        ctx.restore(); return
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    if fa > 0:
        ctx.set_source_rgba(*fc, fa * a); ctx.fill_preserve()
    if hatch:
        ctx.save(); ctx.clip_preserve(); ctx.set_source(HATCH[hatch]); ctx.paint_with_alpha(a); ctx.restore()
    if e.get('dash'):
        ctx.set_dash(e['dash'])
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*ec, 0.25 * a); ctx.set_line_width(ew * 3.2); ctx.stroke_preserve()
    ctx.set_source_rgba(*ec, 0.95 * a); ctx.set_line_width(ew); ctx.stroke()
    ctx.set_dash([])
    ctx.restore()


UA_RINGS = None


def draw_ukraine_border(ctx, view, t):
    a = EV.ua_glow(t)
    if a <= 0.01:
        return
    fine, coarse = Geo.get(G['ukraine'])
    rings = fine if view.fine else coarse
    ctx.new_path()
    for R in rings:
        S = view.sc(R)
        mn = S.min(0); mx = S.max(0)
        if mx[0] < -20 or mx[1] < -20 or mn[0] > W_OUT + 20 or mn[1] > H_OUT + 20 or (mx - mn).max() < 2:
            continue
        ring_path(ctx, S)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for wd, al in ((9, 0.06), (4.5, 0.16), (1.6, 0.85)):
        ctx.set_source_rgba(*C['gold'], al * a); ctx.set_line_width(wd); ctx.stroke_preserve()
    ctx.new_path()


def pts_screen(view, pts_geo):
    P = P200(np.array([p[0] for p in pts_geo]), np.array([p[1] for p in pts_geo]))
    return view.sc(P)


def cut_polyline(S, frac):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(S, axis=0).T))]
    L = d[-1]
    if L <= 0:
        return S[:1], 0
    target = L * clamp01(frac)
    k = np.searchsorted(d, target)
    if k <= 0:
        return S[:1], L
    if k >= len(S):
        return S, L
    f = (target - d[k - 1]) / max(d[k] - d[k - 1], 1e-9)
    return np.vstack([S[:k], S[k - 1] + (S[k] - S[k - 1]) * f]), L


def draw_line(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], e.get('fade', 0.5), e.get('fade_out', 0.6))
    if a <= 0.01:
        return
    if 'smooth' not in e:
        e['smooth'] = catmull(P200(np.array([p[0] for p in e['pts']]), np.array([p[1] for p in e['pts']])), 10) \
            if e.get('curve', True) else P200(np.array([p[0] for p in e['pts']]), np.array([p[1] for p in e['pts']]))
    S = view.sc(e['smooth'])
    prog = ease_io((t - e['t0']) / e.get('draw', 1.2)) if e.get('draw', 1.2) > 0 else 1
    S, L = cut_polyline(S, prog)
    if len(S) < 2:
        return
    col = C[e.get('color', 'white')]
    wdt = e.get('width', 2.0)
    ctx.new_path(); ctx.move_to(*S[0])
    for p in S[1:]:
        ctx.line_to(*p)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if e.get('dash'):
        off = -(t * e.get('dash_speed', 0)) if e.get('dash_speed') else 0
        ctx.set_dash(e['dash'], off)
    if e.get('glow', True):
        ctx.set_source_rgba(*col, 0.18 * a); ctx.set_line_width(wdt * 4); ctx.stroke_preserve()
    ctx.set_source_rgba(*col, 0.95 * a); ctx.set_line_width(wdt); ctx.stroke()
    ctx.set_dash([])
    if e.get('travel'):  # moving highlight dots along the line
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(S, axis=0).T))]
        for k in range(e['travel']):
            f = ((t * e.get('travel_speed', 0.08)) + k / e['travel']) % 1.0
            idx = np.searchsorted(d, f * d[-1]); idx = min(max(idx, 1), len(S) - 1)
            x, y = S[idx]
            g = cairo.RadialGradient(x, y, 0, x, y, 7)
            g.add_color_stop_rgba(0, *C[e.get('travel_color', 'white')], 0.95 * a)
            g.add_color_stop_rgba(1, *C[e.get('travel_color', 'white')], 0)
            ctx.set_source(g); ctx.arc(x, y, 7, 0, 2 * math.pi); ctx.fill()
    if e.get('label'):
        lx, ly = view.geo(*e['label_at'])
        text(ctx, e['label'], lx, ly, e.get('label_size', 12), 'sansb', col, a * smooth((t - e['t0'] - 0.6) / 0.5), 3,
             e.get('anchor', 'l'))


def draw_arrow(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.25, e.get('fade_out', 0.7))
    if a <= 0.01:
        return
    if 'smooth' not in e:
        e['smooth'] = catmull(P200(np.array([p[0] for p in e['pts']]), np.array([p[1] for p in e['pts']])), 14)
    S_all = view.sc(e['smooth'])
    prog = ease_out((t - e['t0']) / e.get('grow', 1.4))
    if e.get('retract') and t > e['retract']:
        prog *= 1 - ease_io((t - e['retract']) / 1.2)
    S, L = cut_polyline(S_all, prog)
    if len(S) < 2 or L * prog < 4:
        return
    col = C[e.get('color', 'ru')]
    wb = e.get('width', 5.0)
    if e.get('dashed'):
        ctx.new_path(); ctx.move_to(*S[0])
        for p in S[1:-1]:
            ctx.line_to(*p)
        ctx.set_dash([6, 5]); ctx.set_line_width(2.2); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*col, 0.9 * a); ctx.stroke(); ctx.set_dash([])
        hl, hw = 9, 6
    else:
        hl, hw = 13 + wb, 7 + wb
    # body polygon (tapered)
    seg = np.diff(S, axis=0)
    segl = np.hypot(*seg.T); segl[segl == 0] = 1e-6
    tang = seg / segl[:, None]
    tang = np.vstack([tang, tang[-1:]])
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    d = np.r_[0, np.cumsum(segl)]
    Ltot = d[-1]
    body_end = max(Ltot - hl, 0.0)
    keep = d <= body_end
    B = S[keep]; nB = nrm[keep]; dB = d[keep]
    tip = S[-1]; dirv = tang[-1]
    base_pt = tip - dirv * hl
    nb = np.array([-dirv[1], dirv[0]])
    if not e.get('dashed'):
        wt = e.get('tail', 1.2)
        widths = wt + (wb - wt) * (dB / max(body_end, 1e-6))
        left = B + nB * widths[:, None] / 2
        right = B - nB * widths[:, None] / 2
        ctx.new_path()
        ctx.move_to(*left[0])
        for p in left[1:]:
            ctx.line_to(*p)
        ctx.line_to(*(base_pt + nb * wb / 2))
        ctx.line_to(*(base_pt + nb * hw)); ctx.line_to(*tip); ctx.line_to(*(base_pt - nb * hw))
        ctx.line_to(*(base_pt - nb * wb / 2))
        for p in right[::-1]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*col, 0.22 * a); ctx.set_line_width(7); ctx.stroke_preserve()
        ctx.set_source_rgba(*col, 0.92 * a); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.35 * a); ctx.set_line_width(0.8); ctx.stroke()
    else:
        ctx.new_path(); ctx.move_to(*(base_pt + nb * hw)); ctx.line_to(*tip); ctx.line_to(*(base_pt - nb * hw))
        ctx.close_path(); ctx.set_source_rgba(*col, 0.95 * a); ctx.fill()
    if e.get('stop') and prog >= 0.999:
        x, y = tip
        al = a * smooth((t - e['t0'] - e.get('grow', 1.4)) / 0.3)
        ctx.set_line_width(3); ctx.set_source_rgba(1, 1, 1, al)
        ctx.move_to(x - 7, y - 7); ctx.line_to(x + 7, y + 7); ctx.move_to(x + 7, y - 7); ctx.line_to(x - 7, y + 7); ctx.stroke()


# --------------------------------------------------------------- icons
def icon(ctx, kind, x, y, sc, col, a, t):
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc)
    if kind == 'star':
        ctx.new_path()
        for k in range(10):
            r = 8 if k % 2 == 0 else 3.4
            ang = -math.pi / 2 + k * math.pi / 5
            ctx.line_to(r * math.cos(ang), r * math.sin(ang))
        ctx.close_path(); ctx.set_source_rgba(*C['gold'], a); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.set_line_width(1); ctx.stroke()
    elif kind == 'ship':
        ctx.new_path()
        ctx.move_to(-11, -1); ctx.line_to(11, -1); ctx.line_to(7, 5); ctx.line_to(-8, 5); ctx.close_path()
        ctx.rectangle(-5, -5, 8, 4); ctx.rectangle(-1, -9, 2, 4)
        ctx.set_source_rgba(*col, a); ctx.fill()
    elif kind == 'boom':
        fl = 1 + 0.12 * math.sin(t * 22)
        for rr, cc, al in ((15 * fl, C['orange'], 0.35), (10 * fl, C['yellow'], 0.9), (4.5, (1, 1, 1), 1)):
            ctx.new_path()
            for k in range(16):
                r = rr if k % 2 == 0 else rr * 0.5
                ang = k * math.pi / 8 + 0.2
                ctx.line_to(r * math.cos(ang), r * math.sin(ang))
            ctx.close_path(); ctx.set_source_rgba(*cc, al * a); ctx.fill()
    elif kind == 'plane':
        ctx.rotate(e_ang := 0.0)
        ctx.new_path()
        ctx.move_to(10, 0); ctx.line_to(-8, -1.5); ctx.line_to(-8, 1.5); ctx.close_path()
        ctx.move_to(2, 0); ctx.line_to(-3, -9); ctx.line_to(-5, -9); ctx.line_to(-2, 0); ctx.line_to(-5, 9); ctx.line_to(-3, 9); ctx.close_path()
        ctx.move_to(-6, 0); ctx.line_to(-9, -4); ctx.line_to(-10, -4); ctx.line_to(-9, 0); ctx.line_to(-10, 4); ctx.line_to(-9, 4); ctx.close_path()
        ctx.set_source_rgba(*col, a); ctx.fill()
    elif kind == 'rad':
        ctx.set_source_rgba(*C['yellow'], a); ctx.arc(0, 0, 10, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(0.05, 0.05, 0.05, a)
        for k in range(3):
            a0 = -math.pi / 2 + k * 2 * math.pi / 3 - math.pi / 6
            ctx.move_to(0, 0); ctx.arc(0, 0, 8.5, a0, a0 + math.pi / 3); ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(*C['yellow'], a); ctx.arc(0, 0, 2.6, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(0.05, 0.05, 0.05, a); ctx.arc(0, 0, 1.6, 0, 2 * math.pi); ctx.fill()
    elif kind == 'shield':
        ctx.new_path(); ctx.move_to(0, -10); ctx.curve_to(6, -8, 9, -8, 9, -7); ctx.curve_to(9, 3, 5, 8, 0, 11)
        ctx.curve_to(-5, 8, -9, 3, -9, -7); ctx.curve_to(-9, -8, -6, -8, 0, -10); ctx.close_path()
        ctx.set_source_rgba(*C['ua'], a); ctx.fill_preserve(); ctx.set_source_rgba(*C['yellow'], a); ctx.set_line_width(1.6); ctx.stroke()
    elif kind == 'x':
        ctx.set_line_width(3); ctx.set_source_rgba(*col, a)
        ctx.move_to(-6, -6); ctx.line_to(6, 6); ctx.move_to(6, -6); ctx.line_to(-6, 6); ctx.stroke()
    elif kind == 'drone':
        ctx.new_path(); ctx.move_to(7, 0); ctx.line_to(-5, -5); ctx.line_to(-3, 0); ctx.line_to(-5, 5); ctx.close_path()
        ctx.set_source_rgba(*col, a); ctx.fill()
    elif kind == 'doc':
        ctx.set_source_rgba(1, 1, 1, a); ctx.rectangle(-6, -8, 12, 16); ctx.fill()
        ctx.set_source_rgba(0.1, 0.1, 0.1, a); ctx.set_line_width(1)
        for yy in (-4, -1, 2, 5):
            ctx.move_to(-4, yy); ctx.line_to(4, yy)
        ctx.stroke()
    elif kind == 'dam':
        ctx.set_source_rgba(*col, a); ctx.rectangle(-9, -3, 18, 6); ctx.fill()
    ctx.restore()


def draw_marker(ctx, view, t, e, suppressed):
    a = window(t, e['t0'], e['t1'], 0.3, e.get('fade_out', 0.6))
    if a <= 0.01:
        return
    if e.get('city'):
        suppressed.add(e['city'])
    x, y = view.geo(e['lon'], e['lat'])
    if x < -80 or y < -80 or x > W_OUT + 80 or y > H_OUT + 80:
        return
    col = C[e.get('color', 'ru')]
    kind = e.get('kind', 'dot')
    lt = t - e['t0']
    pop = 1.0 + 0.45 * math.exp(-lt * 7) * math.sin(lt * 18) if lt < 0.9 else 1.0
    pop *= ease_out(lt / 0.25)
    # pulse ring
    if e.get('pulse', True):
        for k in range(2):
            ph = ((lt * 0.7) + k * 0.5) % 1.0
            r = 5 + ph * 20
            ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, (1 - ph) * 0.55 * a); ctx.set_line_width(1.6); ctx.stroke()
    if e.get('encircle'):
        ctx.save(); ctx.translate(x, y); ctx.rotate(lt * 0.9)
        ctx.set_dash([5, 4]); ctx.set_line_width(2.2); ctx.set_source_rgba(*C['ru'], 0.9 * a)
        ctx.arc(0, 0, 17 * min(1, lt / 0.5) + 0.1, 0, 2 * math.pi); ctx.stroke(); ctx.set_dash([]); ctx.restore()
    if kind == 'dot':
        g = cairo.RadialGradient(x, y, 0, x, y, 12 * pop)
        g.add_color_stop_rgba(0, *col, 0.55 * a); g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g); ctx.arc(x, y, 12 * pop, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(*col, a); ctx.arc(x, y, 4.2 * pop, 0, 2 * math.pi); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, a); ctx.set_line_width(1.4); ctx.stroke()
    else:
        g = cairo.RadialGradient(x, y, 0, x, y, 18 * pop)
        g.add_color_stop_rgba(0, *col, 0.35 * a); g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g); ctx.arc(x, y, 18 * pop, 0, 2 * math.pi); ctx.fill()
        icon(ctx, kind, x, y, pop * e.get('scale', 1.0), col if kind not in ('ship',) else C[e.get('icon_color', 'white')], a, t)
    # labels
    if e.get('label'):
        la = a * smooth((lt - 0.15) / 0.4)
        anchor = e.get('anchor', 'l')
        dx = e.get('dx', 14 if anchor == 'l' else -14 if anchor == 'r' else 0)
        dy = e.get('dy', 4 if anchor in 'lr' else -16)
        lx, ly = x + dx, y + dy
        text(ctx, e['label'], lx, ly, e.get('size', 14), 'sansb', C.get(e.get('label_color', 'white')), la, 3.2, anchor)
        if e.get('sub'):
            text(ctx, e['sub'], lx, ly + 15, 11, 'sansm', C['gold'], la, 3.0, anchor)


def draw_dots(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.3, e.get('fade_out', 0.8))
    if a <= 0.01:
        return
    col = C[e.get('color', 'ru')]
    n = len(e['pts'])
    for k, (lon, lat) in enumerate(e['pts']):
        tk = e['t0'] + e.get('stagger', 1.5) * k / max(n, 1)
        if t < tk:
            continue
        la = a * ease_out((t - tk) / 0.25)
        x, y = view.geo(lon, lat)
        r = e.get('r', 3.0)
        if e.get('pulse', True):
            ph = ((t - tk) * 0.8 + k * 0.37) % 1.0
            ctx.new_path(); ctx.arc(x, y, r + ph * 12, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, (1 - ph) * 0.45 * la); ctx.set_line_width(1.2); ctx.stroke()
        ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*col, 0.95 * la); ctx.fill()


def draw_particles(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.3, 0.8)
    if a <= 0.01:
        return
    cx, cy = view.geo(e['lon'], e['lat'])
    rng = np.random.default_rng(e.get('seed', 3))
    n = e.get('n', 70)
    ang = rng.uniform(0, 2 * math.pi, n); rad = rng.uniform(60, 190, n); dl = rng.uniform(0, 1.4, n)
    fin = rng.uniform(4, 22, n); fa = rng.uniform(0, 2 * math.pi, n)
    for k in range(n):
        f = ease_io((t - e['t0'] - dl[k]) / 2.4)
        r = rad[k] * (1 - f) + fin[k] * f
        aa = ang[k] * (1 - f) + fa[k] * f + 0.3 * math.sin(t * 2 + k)
        x = cx + r * math.cos(aa); y = cy + r * math.sin(aa) * 0.8
        col = C['gold'] if k % 3 else C['ua']
        ctx.new_path(); ctx.arc(x, y, 1.8, 0, 2 * math.pi)
        ctx.set_source_rgba(*col, a * (0.3 + 0.7 * f)); ctx.fill()


def draw_movers(ctx, view, t, e):
    """dots moving along a path (ships)"""
    a = window(t, e['t0'], e['t1'], 0.5, 0.6)
    if a <= 0.01:
        return
    if 'smooth' not in e:
        e['smooth'] = catmull(P200(np.array([p[0] for p in e['pts']]), np.array([p[1] for p in e['pts']])), 10)
    S = view.sc(e['smooth'])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(S, axis=0).T))]
    for k in range(e.get('n', 5)):
        f = ((t - e['t0']) * e.get('speed', 0.06) + k / e.get('n', 5)) % 1.0
        idx = min(max(np.searchsorted(d, f * d[-1]), 1), len(S) - 1)
        p0, p1 = S[idx - 1], S[idx]
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        ctx.save(); ctx.translate(*p1); ctx.rotate(ang); ctx.scale(0.75, 0.75)
        ctx.new_path(); ctx.move_to(9, 0); ctx.line_to(-7, -4); ctx.line_to(-7, 4); ctx.close_path()
        ctx.set_source_rgba(*C[e.get('color', 'yellow')], 0.95 * a); ctx.fill(); ctx.restore()


def draw_glowline_pts(ctx, S, col, a, w):
    ctx.new_path(); ctx.move_to(*S[0])
    for p in S[1:]:
        ctx.line_to(*p)
    for wd, al in ((w * 5, 0.10), (w * 2.2, 0.3), (w, 1.0)):
        ctx.set_source_rgba(*col, al * a); ctx.set_line_width(wd); ctx.stroke_preserve()
    ctx.new_path()


# --------------------------------------------------------------- static labels
def draw_static_labels(ctx, view, t, suppressed):
    ga = EV.label_alpha(t)
    if ga <= 0.01:
        return
    w = view.w
    for L in EV.STATIC_LABELS:
        name, lon, lat, kind, minw, maxw = L[:6]
        if kind == 'city' and name in suppressed:
            continue
        fa = smooth((w - minw * 0.85) / (minw * 0.15 + 1e-6)) * smooth((maxw * 1.15 - w) / (maxw * 0.15 + 1e-6))
        a = fa * ga
        if a <= 0.02:
            continue
        x, y = view.geo(lon, lat)
        if x < -100 or x > W_OUT + 100 or y < -30 or y > H_OUT + 30:
            continue
        if kind == 'country':
            text(ctx, name, x, y, 15, 'sansb', (0.88, 0.9, 0.94), 0.42 * a, 0, 'c', spacing=4)
        elif kind == 'sea':
            text(ctx, name, x, y, 15, 'sansl', C['teal'], 0.75 * a, 0, 'c', spacing=5)
        elif kind == 'region':
            text(ctx, name, x, y, 13, 'sansb', C['gold'], 0.7 * a, 2.5, 'c', spacing=3)
        elif kind == 'city':
            anchor = L[6] if len(L) > 6 else 'l'
            ctx.new_path(); ctx.arc(x, y, 2.4, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.85 * a); ctx.fill_preserve()
            ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.set_line_width(1); ctx.stroke()
            dx = 6 if anchor == 'l' else -6 if anchor == 'r' else 0
            dy = 4 if anchor in 'lr' else (-8 if anchor == 't' else 15)
            text(ctx, name, x + dx, y + dy, 11.5, 'sansm', (0.92, 0.94, 0.97), 0.85 * a, 2.6, 'c' if anchor in 'tb' else anchor)


# --------------------------------------------------------------- UI
def rrect(ctx, x, y, w, h, r):
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def draw_card(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.45, 0.45)
    if a <= 0.01:
        return
    slide = (1 - ease_out((t - e['t0']) / 0.55)) * 40 + (1 - smooth((e['t1'] - t) / 0.45)) * 20
    kind = e.get('kind', 'stat')
    wdt = e.get('w', 262)
    x = W_OUT - wdt - 22 + slide
    y = e.get('y', 96)
    lines = e.get('lines', [])
    h = e.get('h', 0) or (64 + 17 * len(lines) + (40 if kind == 'stat' else 0))
    if kind == 'versus':
        h = e.get('h', 128)
    rrect(ctx, x, y, wdt, h, 8)
    ctx.set_source_rgba(0.03, 0.05, 0.09, 0.82 * a); ctx.fill_preserve()
    ctx.set_source_rgba(*C['gold'], 0.45 * a); ctx.set_line_width(1); ctx.stroke()
    ctx.set_source_rgba(*C[e.get('accent', 'gold')], a); ctx.rectangle(x, y + 10, 3, h - 20); ctx.fill()
    tx = x + 18
    if e.get('tag'):
        text(ctx, e['tag'], tx, y + 22, 10.5, 'sansb', C['gold'], a, 0, 'l', spacing=1.5)
    yy = y + (30 if e.get('tag') else 16)
    if kind == 'stat':
        big = e['big']
        if e.get('count_to') is not None:
            f = ease_out((t - e['t0'] - 0.2) / e.get('count_dur', 1.6))
            v = e['count_to'] * f
            big = e.get('fmt', '{:,.0f}').format(v)
        text(ctx, big, tx, yy + 36, e.get('big_size', 36), 'sansk', C.get(e.get('big_color', 'white')), a, 0, 'l')
        yy += 50
    elif kind == 'versus':
        (l1, l2), (r1, r2) = e['left'], e['right']
        cw = (wdt - 36) / 2
        text(ctx, l1, tx, yy + 14, 12, 'sansb', C['ru'], a, 0, 'l')
        text(ctx, r1, tx + cw + 10, yy + 14, 12, 'sansb', C['ua'], a, 0, 'l')
        for k, s in enumerate(l2):
            text(ctx, s, tx, yy + 36 + 17 * k, 12, 'sansm', (0.9, 0.92, 0.95), a, 0, 'l')
        for k, s in enumerate(r2):
            text(ctx, s, tx + cw + 10, yy + 36 + 17 * k, 12, 'sansm', (0.9, 0.92, 0.95), a, 0, 'l')
        ctx.set_source_rgba(1, 1, 1, 0.2 * a); ctx.move_to(tx + cw, yy + 4); ctx.line_to(tx + cw, y + h - 12); ctx.set_line_width(1); ctx.stroke()
        return
    if e.get('title'):
        text(ctx, e['title'], tx, yy + 18, 16, 'sansb', (1, 1, 1), a, 0, 'l'); yy += 26
    for k, s in enumerate(lines):
        text(ctx, s, tx, yy + 14 + 17 * k, 12, 'sansm', (0.86, 0.89, 0.93), a, 0, 'l')


def draw_date_badge(ctx, t):
    info = EV.current_sentence(t)
    if info is None:
        return
    sid, a = info
    if a <= 0.01:
        return
    s = TL.SENT[sid]
    ch = s['chapter']
    num, title, yrs = TL.CHAPTER_INFO[ch]
    if num:
        text(ctx, f'제{int(num)}장 · {title.split(" — ")[0]}', 24, 34, 11.5, 'sansb', C['gold'], 0.95 * a, 2.5, 'l', spacing=1)
    if s['date']:
        # animate on change
        ch_t = EV.date_changed_at(t)
        k = ease_out((t - ch_t) / 0.45)
        text(ctx, s['date'], 23, 64 + (1 - k) * 8, 28, 'sansk', (1, 1, 1), a * k, 3.5, 'l')
    # timeline
    yv = s['year']
    if yv is None:
        return
    x0, x1, y0 = 596, 830, 34
    ctx.set_line_width(1.2); ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.move_to(x0, y0); ctx.line_to(x1, y0); ctx.stroke()
    for yr in range(2014, 2027):
        xx = x0 + (yr - 2014) / 12 * (x1 - x0)
        big = yr in (2014, 2018, 2022, 2026)
        ctx.move_to(xx, y0 - (4 if big else 2)); ctx.line_to(xx, y0 + (4 if big else 2))
        ctx.set_source_rgba(1, 1, 1, (0.6 if big else 0.3) * a); ctx.stroke()
        if big:
            text(ctx, str(yr), xx, y0 + 17, 10, 'sansm', (0.85, 0.88, 0.92), 0.8 * a, 0, 'c')
    yshow = EV.smooth_year(t)
    pre = yshow < 2013.9
    xx = x0 + (min(max(yshow, 2014), 2026.9) - 2014) / 12 * (x1 - x0)
    if pre:
        text(ctx, f'◀ {int(yshow)}', x0 - 6, y0 + 4, 10.5, 'sansb', C['gold'], a, 0, 'r')
    else:
        ctx.set_source_rgba(*C['gold'], 0.9 * a); ctx.set_line_width(2.4)
        ctx.move_to(x0, y0); ctx.line_to(xx, y0); ctx.stroke()
        g = cairo.RadialGradient(xx, y0, 0, xx, y0, 10)
        g.add_color_stop_rgba(0, *C['gold'], 0.9 * a); g.add_color_stop_rgba(1, *C['gold'], 0)
        ctx.set_source(g); ctx.arc(xx, y0, 10, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgba(1, 1, 1, a); ctx.arc(xx, y0, 3, 0, 2 * math.pi); ctx.fill()


def wrap(ctx, s, maxw):
    if tw(ctx, s) <= maxw:
        return [s]
    words = s.split(' ')
    best, bi = 1e9, 1
    for i in range(1, len(words)):
        a = ' '.join(words[:i]); b = ' '.join(words[i:])
        d = abs(tw(ctx, a) - tw(ctx, b))
        if d < best and max(tw(ctx, a), tw(ctx, b)) <= maxw:
            best, bi = d, i
    return [' '.join(words[:bi]), ' '.join(words[bi:])]


def draw_subtitle(ctx, t):
    for sid in TL.ORDER:
        if TL.T[sid] - 0.05 <= t <= TL.TE[sid] + 0.25:
            a = min(smooth((t - TL.T[sid] + 0.05) / 0.18), smooth((TL.TE[sid] + 0.25 - t) / 0.2))
            font(ctx, 'sansm', 19)
            ls = wrap(ctx, TL.SENT[sid]['text'], 700)
            base_y = 452 - (len(ls) - 1) * 26
            for k, s in enumerate(ls):
                text(ctx, s, W_OUT / 2, base_y + k * 26, 19, 'sansm', (1, 1, 1), a, 4.5, 'c', halo_a=0.9)
            return


def draw_fullcards(ctx, t):
    for (t0, t1, kind, key) in TL.CARDS:
        if not (t0 - 0.1 <= t <= t1 + 0.1):
            continue
        a = window(t, t0, t1, 0.55, 0.65)
        lt = t - t0
        if kind in ('chapter', 'title', 'end'):
            g = cairo.LinearGradient(0, 0, 0, H_OUT)
            g.add_color_stop_rgba(0, 0.01, 0.02, 0.04, 0.78 * a)
            g.add_color_stop_rgba(0.5, 0.01, 0.02, 0.04, 0.62 * a)
            g.add_color_stop_rgba(1, 0.01, 0.02, 0.04, 0.85 * a)
            ctx.set_source(g); ctx.paint()
        if kind == 'chapter':
            num, title, yrs = TL.CHAPTER_INFO[key]
            k = ease_out(lt / 0.9)
            text(ctx, num, W_OUT / 2, 190 - (1 - k) * 12, 64, 'sanst', C['gold'], a * k, 0, 'c', spacing=4)
            lw = 170 * ease_io((lt - 0.2) / 0.9)
            ctx.set_source_rgba(*C['gold'], 0.8 * a); ctx.set_line_width(1.2)
            ctx.move_to(W_OUT / 2 - lw, 214); ctx.line_to(W_OUT / 2 + lw, 214); ctx.stroke()
            k2 = ease_out((lt - 0.35) / 0.9)
            text(ctx, title, W_OUT / 2, 262 + (1 - k2) * 10, 32, 'serifb', (1, 1, 1), a * k2, 0, 'c')
            k3 = ease_out((lt - 0.6) / 0.9)
            text(ctx, yrs, W_OUT / 2, 296, 14, 'sansl', (0.8, 0.84, 0.9), a * k3, 0, 'c', spacing=4)
        elif kind == 'title':
            k = ease_out(lt / 1.2)
            text(ctx, '흑해를 둘러싼 12년', W_OUT / 2, 170, 16, 'sansl', C['gold'], a * k, 0, 'c', spacing=8)
            k2 = ease_out((lt - 0.3) / 1.2)
            text(ctx, '우크라이나 전쟁', W_OUT / 2, 244 + (1 - k2) * 14, 58, 'serifb', (1, 1, 1), a * k2, 0, 'c', spacing=3)
            lw = 210 * ease_io((lt - 0.6) / 1.2)
            ctx.set_source_rgba(*C['gold'], 0.8 * a); ctx.set_line_width(1.2)
            ctx.move_to(W_OUT / 2 - lw, 272); ctx.line_to(W_OUT / 2 + lw, 272); ctx.stroke()
            k3 = ease_out((lt - 1.0) / 1.2)
            text(ctx, '발단과 전개, 그리고 현재  ·  2014 – 2026', W_OUT / 2, 304, 15, 'sansm', (0.85, 0.88, 0.93), a * k3, 0, 'c', spacing=1)
        elif kind == 'end':
            k = ease_out(lt / 1.0)
            text(ctx, '자료 및 참고', W_OUT / 2, 120, 14, 'sansb', C['gold'], a * k, 0, 'c', spacing=6)
            rows = EV.END_LINES
            for i, r in enumerate(rows):
                kk = ease_out((lt - 0.2 - i * 0.12) / 0.8)
                text(ctx, r, W_OUT / 2, 158 + i * 24, 13, 'sansm', (0.88, 0.9, 0.94), a * kk, 0, 'c')


def build_vignette():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    c = cairo.Context(s)
    g = cairo.RadialGradient(W_OUT / 2, H_OUT / 2, H_OUT * 0.35, W_OUT / 2, H_OUT / 2, W_OUT * 0.72)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.62)
    c.set_source(g); c.paint()
    g = cairo.LinearGradient(0, H_OUT - 110, 0, H_OUT)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    c.set_source(g); c.rectangle(0, H_OUT - 110, W_OUT, 110); c.fill()
    g = cairo.LinearGradient(0, 0, 0, 90)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.45); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    c.set_source(g); c.rectangle(0, 0, W_OUT, 90); c.fill()
    return s


VIG = build_vignette()


def draw_note(ctx, t):
    for e in EV.NOTES:
        a = window(t, e['t0'], e['t1'], 0.5, 0.5)
        if a > 0.01:
            text(ctx, e['text'], 16, 470, 9.5, 'sansm', (0.75, 0.8, 0.86), 0.85 * a, 2, 'l')



def draw_tl(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.5, 0.6)
    if a <= 0.01:
        return
    fr = e['frames']; cur = fr[0]; k = 0
    for i, f in enumerate(fr):
        if f[0] <= t:
            cur = f; k = i
    g = cairo.LinearGradient(0, 330, 0, H_OUT)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.6 * a)
    ctx.set_source(g); ctx.rectangle(0, 330, W_OUT, H_OUT - 330); ctx.fill()
    text(ctx, '전선의 변화', W_OUT / 2, 36, 12, 'sansb', C['gold'], a, 2.5, 'c', spacing=3)
    text(ctx, cur[1], W_OUT / 2, 412, 34, 'sansk', (1, 1, 1), a, 4, 'c')
    if cur[2] is not None:
        text(ctx, f'러시아 통제  {cur[2]:.1f}%', W_OUT / 2, 440, 15, 'sansb', C['ru'], a, 3, 'c')
    x0, x1, y = 227, 627, 458
    ctx.set_line_width(2); ctx.set_source_rgba(1, 1, 1, 0.25 * a); ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke()
    f = (k + min(1, (t - cur[0]) / max(1e-3, (fr[min(k + 1, len(fr) - 1)][0] - cur[0]) or 1))) / len(fr)
    ctx.set_source_rgba(*C['gold'], 0.9 * a); ctx.move_to(x0, y); ctx.line_to(x0 + (x1 - x0) * min(f, 1), y); ctx.stroke()
    text(ctx, '2022', x0 - 8, y + 4, 10, 'sansm', (0.85, 0.88, 0.92), 0.8 * a, 0, 'r')
    text(ctx, '2026', x1 + 8, y + 4, 10, 'sansm', (0.85, 0.88, 0.92), 0.8 * a, 0, 'l')

DRAW = {'area': None, 'line': draw_line, 'arrow': draw_arrow, 'dots': draw_dots, 'particles': draw_particles,
        'movers': draw_movers}


def render_frame(i):
    t = i / FPS
    view = View(i)
    im = view.base()
    buf = bytearray(im.tobytes('raw', 'BGRX'))
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W_OUT, H_OUT, W_OUT * 4)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    act = [e for e in EV.EVENTS if e['t0'] - 0.05 <= t <= e['t1'] + 0.05]
    for e in act:
        if e['type'] == 'area':
            draw_area(ctx, view, t, e)
    draw_ukraine_border(ctx, view, t)
    for z in ('line', 'arrow', 'dots', 'movers', 'particles'):
        for e in act:
            if e['type'] == z:
                DRAW[z](ctx, view, t, e)
    suppressed = set()
    mk = [e for e in act if e['type'] == 'marker']
    for e in mk:
        if e.get('city'):
            suppressed.add(e['city'])
    draw_static_labels(ctx, view, t, suppressed)
    for e in mk:
        draw_marker(ctx, view, t, e, suppressed)
    for e in act:
        if e['type'] == 'flash':
            a = window(t, e['t0'], e['t1'], 0.05, e['t1'] - e['t0'] - 0.05)
            ctx.set_source_rgba(1, 0.95, 0.9, e.get('a', 0.5) * a); ctx.paint()
    ctx.set_source_surface(VIG, 0, 0); ctx.paint()
    for e in act:
        if e['type'] == 'card':
            draw_card(ctx, t, e)
    draw_note(ctx, t)
    for e in act:
        if e['type'] == 'tl':
            draw_tl(ctx, t, e)
    draw_date_badge(ctx, t)
    draw_fullcards(ctx, t)
    draw_subtitle(ctx, t)
    # global fade
    fa = 1 - min(smooth(t / 1.4), smooth((TL.TOTAL - t) / 1.6))
    if fa > 0.001:
        ctx.set_source_rgba(0, 0, 0, fa); ctx.paint()
    surf.flush()
    return surf, buf


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        times = [float(x) for x in sys.argv[2].split(',')]
        for tt in times:
            s, b = render_frame(int(tt * FPS))
            s.write_to_png(f'/home/claude/prev/p_{tt:07.2f}.png')
        sys.exit(0)
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else N
    out = sys.argv[3] if len(sys.argv) > 3 else '/home/claude/video_noaudio.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W_OUT}x{H_OUT}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'faster', '-crf', '19',
                           '-pix_fmt', 'yuv420p', '-g', '48', out], stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(start, end):
        s, b = render_frame(i)
        ff.stdin.write(b)
        if (i - start) % 240 == 0:
            el = time.time() - t0
            print(f'frame {i}/{end}  {el:.0f}s  {(i - start + 1) / max(el, 1e-3):.1f} fps', flush=True)
    ff.stdin.close(); ff.wait()
    print('done', time.time() - t0)
