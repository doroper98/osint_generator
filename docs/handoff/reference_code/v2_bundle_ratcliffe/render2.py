import sys, json, math, pickle, time, subprocess
import numpy as np, cairo
from PIL import Image
from shapely.ops import unary_union

V = '/home/claude/v2'
P = json.load(open(f'{V}/plan.json'))
FPS = 24; W_OUT, H_OUT = 854, 480
TOTAL = P['total']; N = int(TOTAL * FPS)
SENT = {x['sid']: x for x in P['sentences']}
ORDER = [x['sid'] for x in P['sentences']]
SEC0 = P['sec_start']
SECS = [s for s in SEC0]


def S(sid, off=0.0): return SENT[sid]['t0'] + off
def E(sid, off=0.0): return SENT[sid]['t1'] + off


def SEC_END(sec):
    i = SECS.index(sec)
    return SEC0[SECS[i + 1]] - 0.3 if i + 1 < len(SECS) else TOTAL


def ym(lat): return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
def ymv(lat): return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


def clamp01(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def smooth(x): x = clamp01(x); return x * x * (3 - 2 * x)
def ease_io(x): x = clamp01(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp01(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def window(t, t0, t1, fin=0.5, fout=0.5):
    if t < t0 or t > t1: return 0.0
    return min(smooth((t - t0) / fin) if fin > 0 else 1, smooth((t1 - t) / fout) if fout > 0 else 1)


def hexc(h, a=None):
    h = h.lstrip('#'); c = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return c if a is None else c + (a,)


C = {'ru': hexc('#ff4d5e'), 'us': hexc('#5aa9ff'), 'ua': hexc('#ffd23f'), 'gold': hexc('#e2b25c'), 'teal': hexc('#56c6d8'),
     'white': (1, 1, 1), 'muted': hexc('#b0a8be'), 'green': hexc('#8fc98a'), 'amber': hexc('#ffb347'), 'ink': hexc('#0c1016'),
     'panel': hexc('#141821'), 'line': hexc('#3a4252')}

# ------------------------------------------------------------------ assets
TIERS = pickle.load(open(f'{V}/assets/tiers.pkl', 'rb'))
BASE = {}
for n, T in TIERS.items():
    for lv in T['levels']:
        im = Image.open(f'{V}/assets/base_{n}_{lv}.png').convert('RGB')
        a = np.asarray(im, np.float32); a = np.clip(a * 1.32 + 10, 0, 255).astype(np.uint8)
        BASE[(n, lv)] = Image.fromarray(a)
GEO = pickle.load(open(f'{V}/assets/geo2.pkl', 'rb'))


def to_uv(rings):
    out = []
    for r in rings:
        uv = np.stack([r[:, 0], ymv(np.clip(r[:, 1], -85, 85))], 1).astype(np.float64)
        out.append((uv, uv.min(0), uv.max(0)))
    return out


BORD = {lod: {k: to_uv(v) for k, v in GEO[lod].items()} for lod in ('coarse', 'fine')}
OLD = pickle.load(open('/home/claude/geo.pkl', 'rb'))


def geo_rings(g, tol=0.004):
    gs = g.simplify(tol, preserve_topology=True); out = []
    for p in getattr(gs, 'geoms', [gs]):
        if p.geom_type != 'Polygon': continue
        out.append(np.asarray(p.exterior.coords)[:, :2])
        for r in p.interiors: out.append(np.asarray(r.coords)[:, :2])
    return to_uv(out)


OCC = {k: geo_rings(unary_union([OLD['snap'][k], OLD['snap']['crimea']]).buffer(0)) for k in ('ds_2025-02-01', 'ds_2026-09-01')}
PCT = OLD.get('ds_pct', {})


def surf_from_pil(im):
    im = im.convert('RGBA'); a = np.asarray(im).astype(np.float32); al = a[..., 3:4] / 255
    rgb = a[..., :3] * al
    bgra = np.ascontiguousarray(np.dstack([rgb[..., 2], rgb[..., 1], rgb[..., 0], a[..., 3]]).astype(np.uint8))
    h, w = bgra.shape[:2]; buf = bytearray(bgra.tobytes())
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, w * 4)
    return (s, buf)


PORT_PIL = {p: Image.open(f'{V}/assets/portraits/{p}.png').convert('RGBA') for p in ('ratcliffe', 'naryshkin', 'bortnikov', 'trump', 'putin', 'zelensky')}
FLAG_PIL = {}
for c in ('us', 'ru', 'ua', 'ir', 'lv', 'pl', 'ro', 'de', 'eu', 'ee', 'lt'):
    FLAG_PIL[(c, '43')] = Image.open(f'{V}/assets/flags/{c}_4x3.png').convert('RGBA')
    FLAG_PIL[(c, '11')] = Image.open(f'{V}/assets/flags/{c}_1x1.png').convert('RGBA')
_SC = {}


def scaled(key, pil, w):
    w = max(8, int(round(w / 3.0) * 3)); k = (key, w)
    if k not in _SC:
        _SC[k] = surf_from_pil(pil.resize((w, max(1, int(pil.height * w / pil.width))), Image.LANCZOS))
    return _SC[k][0]


PORT_REG = json.load(open(f'{V}/assets/portrait_registry.json'))

# ------------------------------------------------------------------ fonts & text
SANS, SERIF = 'Noto Sans CJK KR', 'Noto Serif CJK KR'
FONT = {'sans': (SANS, 0), 'sansb': (SANS, 1), 'sansm': (SANS + ' Medium', 0), 'sansk': (SANS + ' Black', 0),
        'sansl': (SANS + ' Light', 0), 'serifb': (SERIF, 1), 'serif': (SERIF, 0)}


def font(ctx, name, size):
    fam, b = FONT[name]
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if b else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def tw(ctx, s, size=None, name=None):
    if size: font(ctx, name, size)
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, name='sansb', col=(1, 1, 1), a=1.0, halo=3.0, anchor='l', spacing=0.0, halo_a=0.8):
    if a <= 0.01 or not s: return 0
    font(ctx, name, size)
    w = ctx.text_extents(s).x_advance + spacing * max(0, len(s) - 1)
    if anchor == 'c': x -= w / 2
    elif anchor == 'r': x -= w
    ctx.new_path()
    if spacing:
        xx = x
        for ch in s:
            ctx.move_to(xx, y); ctx.text_path(ch); xx += ctx.text_extents(ch).x_advance + spacing
    else:
        ctx.move_to(x, y); ctx.text_path(s)
    if halo > 0:
        ctx.set_source_rgba(0.02, 0.03, 0.05, halo_a * a); ctx.set_line_width(halo); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgba(*col[:3], a); ctx.fill()
    return w


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()


def wrap(ctx, s, maxw, size, name):
    font(ctx, name, size)
    words = s.split(' '); lines = []; cur = ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if ctx.text_extents(t).x_advance > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    if cur: lines.append(cur)
    return lines


# ------------------------------------------------------------------ places
M = {m['id']: m for m in P['map']['markers']}
PL = {k: (m['lng'], m['lat']) for k, m in M.items()}
PL.update({'uk': (-1.6, 53.3), 'washington': (-77.04, 38.9), 'kyiv': (30.52, 50.45)})

# ------------------------------------------------------------------ events & camera (direction layer)
CAM, EV = [], []


def cam(t, lon, lat, w, dur=2.6): CAM.append((t, lon, ym(lat), w, dur))


def ev(typ, t0, t1, **kw):
    d = dict(type=typ, t0=t0, t1=t1); d.update(kw); EV.append(d); return d


ARCS = {(a['from_id'], a['to_id']): a for a in P['map']['arcs']}


def arc_ev(fr, to, t0, t1, grow=2.2, **kw):
    a = ARCS.get((fr, to), {})
    kind = kw.pop('kind', a.get('kind', 'flow'))
    return ev('arc', t0, t1, p0=PL[fr], p1=PL[to], kind=kind, label=kw.pop('label', a.get('label', '')), label_t=a.get('label_t', 0.5), grow=grow, **kw)


def marker_ev(mid, t0, t1, **kw):
    m = M.get(mid, {})
    d = dict(lon=PL[mid][0], lat=PL[mid][1], label=kw.pop('label', m.get('name', '')), sub=kw.pop('sub', m.get('value', '')),
             side=kw.pop('side', m.get('label_side', 'right')), hl=m.get('highlight', False))
    d.update(kw); return ev('marker', t0, t1, **d)


def badge_ev(t0, t1, x=None, y=None, lon=None, lat=None, **kw):
    return ev('badge', t0, t1, x=x, y=y, lon=lon, lat=lat, **kw)


def card(t0, t1, tag, big=None, lines=(), accent='gold', **kw):
    return ev('card', t0, t1, tag=tag, big=big, lines=list(lines), accent=accent, **kw)


def panel(kind, t0, t1, **kw): return ev('panel', t0, t1, kind=kind, **kw)


PERSON = {'ratcliffe': ('존 랫클리프', 'CIA 국장', 'us'), 'naryshkin': ('세르게이 나리시킨', '대외정보국(SVR) 국장', 'ru'),
          'bortnikov': ('알렉산드르 보르트니코프', '연방보안국(FSB) 국장', 'ru'), 'putin': ('블라디미르 푸틴', '러시아 대통령', 'ru'),
          'zelensky': ('볼로디미르 젤렌스키', '우크라이나 대통령', 'ua'), 'trump': ('도널드 트럼프', '미국 대통령', 'us')}


def person(pid, t0, t1, **kw):
    nm, role, fl = PERSON[pid]
    kw.setdefault('label', nm); kw.setdefault('role', role)
    return badge_ev(t0, t1, kind='person', pid=pid, flag=fl, **kw)


# --- intro
cam(0, -18, 46, 150, 0)
cam(S('intro_0', 0.2), 8, 48, 105, 9.0)
marker_ev('moscow', S('intro_0', 1.5), SEC0['s1'], label='모스크바', sub='')
# --- s1 flight
cam(S('s1_0', -1.0), -52, 44, 72, 3.0)
marker_ev('andrews', S('s1_0', 0.4), SEC_END('s1'))
a1 = arc_ev('andrews', 'riga', S('s1_0', 1.6), SEC_END('s3') if False else SEC_END('s1'), grow=E('s1_1', -0.6) - S('s1_0', 1.6), plane=True)
cam(S('s1_1', -0.4), 14, 53, 44, 3.6)
marker_ev('riga', S('s1_1', 0.2), SEC_END('s1'))
arc_ev('riga', 'moscow', E('s1_1', -0.9), SEC_END('s1'), grow=1.6, plane=True)
ev('boom', E('s1_1', 0.6), E('s1_1', 2.4), lon=PL['moscow'][0], lat=PL['moscow'][1])
cam(S('s1_2', -0.5), 36.5, 55.3, 11, 3.0)
marker_ev('moscow', E('s1_1', 0.4), SEC_END('s1'))
person('ratcliffe', S('s1_2', 0.2), SEC_END('s1'), lon=33.2, lat=56.4, R=32, accent='us')
card(S('s1_3', 0.1), E('s1_3', 0.6), 'CIA 국장 방러', big='2022년 이후 첫 사례', big_size=20, lines=['체류는 하루를 넘기지 않았다'])
# --- s2 three problems
cam(S('s2_0', -0.8), 40, 43, 64, 3.0)
marker_ev('moscow', S('s2_0'), SEC_END('s2'), label='모스크바', sub='')
ev('country', S('s2_1', 0.1), SEC_END('s2'), codes=['UA'], col='ua', a=0.22)
marker_ev('kyiv', S('s2_1', 0.2), SEC_END('s2'), sub='종전 협상 정체', side='left')
ev('country', S('s2_2', 0.1), SEC_END('s2'), codes=['IR'], col='ru', a=0.14)
marker_ev('hormuz', S('s2_2', 0.2), SEC_END('s2'), icon='ship', sub='2월 말부터 봉쇄')
ev('country', S('s2_3', 0.1), SEC_END('s2'), codes=['PL', 'RO', 'LT', 'LV', 'EE'], col='teal', a=0.2)
marker_ev('lublin', S('s2_3', 0.3), SEC_END('s2'), sub='')
marker_ev('tulcea', S('s2_3', 0.5), SEC_END('s2'), sub='')
arc_ev('moscow', 'lublin', S('s2_3', 0.4), SEC_END('s2'), grow=1.4, label='')
arc_ev('moscow', 'tulcea', S('s2_3', 0.7), SEC_END('s2'), grow=1.4, label='')
card(S('s2_1', 0.3), E('s2_3', 0.5), '8월의 달력', lines=['① 우크라이나 협상 — 멈춤', '② 호르무즈 해협 — 막힘', '③ 나토 동쪽 국경 — 흔들림'], accent='gold', stagger=[S('s2_1', 0.3), S('s2_2', 0.2), S('s2_3', 0.2)])
# --- s3 network (chart ch-1)
cam(SEC0['s3'] - 0.5, 37.6, 55.7, 18, 3.0)
panel('network', SEC0['s3'] - 0.2, SEC_END('s3'), chart='ch-1')
# --- s4 who was absent
cam(S('s4_0', -0.8), 34.6, 53.2, 24, 3.0)
marker_ev('moscow', S('s4_0'), SEC_END('s4'), label='모스크바', sub='')
person('putin', S('s4_0', 0.3), E('s4_1', 0.4), lon=41.6, lat=54.4, R=30, stamp='불참', accent='ru')
marker_ev('kyiv', S('s4_2', 0.1), SEC_END('s4'), sub='', side='left')
person('zelensky', S('s4_2', 0.3), SEC_END('s4'), lon=26.2, lat=51.3, R=30, role='사전 통보 받음', accent='ua')
ev('shield', S('s4_3', 0.2), SEC_END('s4'), lon=PL['moscow'][0], lat=PL['moscow'][1], r_km=260, label='월–수 타격 중단 요청')
card(S('s4_3', 0.6), E('s4_3', 0.8), '미국의 요청', big='사흘', lines=['모스크바 등 북부 도시 타격 중단'], accent='us')
# --- s5 diagnosis: DeepState real data + dot matrix (ch-2)
cam(S('s5_0', -0.8), 36.2, 48.2, 13, 3.0)
ev('occupied', S('s5_0', 0.2), S('s5_1', 0.6), key='ds_2025-02-01')
ev('occupied', S('s5_1', 0.0), E('s5_3', 0.2), key='ds_2026-09-01')
card(S('s5_0', 0.6), E('s5_0', 0.3), 'DeepState 실측', big=f"{PCT.get('ds_2025-02-01', 18.5):.1f}%", lines=['2025.2 러시아 통제 면적'], accent='ru')
panel('dots', S('s5_1', -0.1), E('s5_2', 0.4), chart='ch-2')
cam(S('s5_3', -0.6), 37.3, 55.6, 10, 2.6)
person('ratcliffe', S('s5_3', 0.1), SEC_END('s5'), lon=34.4, lat=56.4, R=30, accent='us')
person('bortnikov', S('s5_3', 0.4), SEC_END('s5'), lon=40.6, lat=56.4, R=30, accent='ru')
# --- s6 channel
cam(S('s6_0', -0.8), -18, 50, 118, 3.2)
ev('channel', S('s6_0', 0.2), E('s6_1', 0.6), p0=PL['andrews'], p1=PL['moscow'], label='정보기관 채널')
cam(S('s6_2', -0.6), 37.5, 55.6, 10, 3.0)
person('naryshkin', S('s6_2', 0.1), SEC_END('s6'), lon=34.2, lat=56.3, R=31, accent='ru')
card(S('s6_2', 0.5), E('s6_2', 0.6), '나리시킨 · 8월 27일', lines=['“특별할 것 없는', '통상적인 실무 형식”'], accent='ru', quote=True)
card(S('s6_3', 0.1), E('s6_3', 0.6), '페스코프 · 크렘린 대변인', lines=['“겁주는 이야기들은', '사실과 무관하다”'], accent='ru', quote=True)
# --- s7 NATO
cam(S('s7_0', -0.8), 22, 51.5, 30, 3.0)
ev('country', S('s7_0', 0.2), SEC_END('s7'), codes=['PL', 'RO', 'LT', 'LV', 'EE', 'DE'], col='teal', a=0.2)
card(S('s7_1', 0.2), E('s7_1', 0.6), '미 정보당국 평가', big='2026 가을 – 2029', big_size=20, lines=['나토 결속 시험 가능 시간대'], accent='teal')
marker_ev('lublin', S('s7_2', 0.1), SEC_END('s7'), icon='boom', sub='7.29 순항미사일 낙하 (약 50km)')
marker_ev('tulcea', S('s7_2', 0.5), SEC_END('s7'), icon='drone', sub='8.12–13 드론 영공 진입')
marker_ev('leipzig', S('s7_2', 0.9), SEC_END('s7'), icon='drone', sub='나토 수송 거점 드론 폐쇄')
cam(S('s7_3', -0.5), 8, 52.5, 34, 3.0)
marker_ev('uk', S('s7_3', 0.3), SEC_END('s7'), label='영국', sub='공격 계획 — 미확인', side='left', stamp='미확인', icon='none')
# --- s8 gantt
cam(SEC0['s8'] - 0.5, 30, 45, 60, 3.0)
panel('gantt', SEC0['s8'] - 0.2, SEC_END('s8'), chart='ch-3')
# --- s9 Hormuz
cam(S('s9_0', -0.8), 53.5, 29.8, 22, 3.0)
ev('country', S('s9_0', 0.1), SEC_END('s9'), codes=['IR'], col='ru', a=0.16)
marker_ev('hormuz', S('s9_0', 0.2), SEC_END('s9'), icon='ship')
badge_ev(S('s9_0', 0.4), E('s9_1', 0.2), lon=50.6, lat=32.2, kind='flag', flag='ir', label='이란', role='해협 봉쇄 유지', R=24)
cam(S('s9_1', -0.4), 47, 42, 72, 3.0)
arc_ev('moscow', 'hormuz', S('s9_1', 0.3), E('s9_2', 0.5), grow=1.8)
marker_ev('moscow', S('s9_1', 0.1), E('s9_2', 0.5), label='모스크바', sub='')
cam(S('s9_2', -0.4), 55.5, 27.5, 14, 2.8)
card(S('s9_2', 0.2), E('s9_2', 0.6), '이란 혁명수비대 · 8.26', lines=['“미국이 조건을 받아들일 때까지', '봉쇄를 유지한다”'], accent='ru', quote=True)
panel('dual_line', S('s9_3', -0.2), SEC_END('s9'), chart='ch-4')
# --- s10 versus
cam(SEC0['s10'] - 0.5, 0, 48, 90, 3.0)
panel('versus', SEC0['s10'] - 0.2, SEC_END('s10'))
# --- s11 fork
panel('fork', SEC0['s11'] - 0.2, SEC_END('s11'))
# --- s12 checklist + pull back
panel('checklist', SEC0['s12'] - 0.2, E('s12_2', 0.6))
cam(S('s12_3', -0.8), -18, 47, 130, 5.0)
arc_ev('andrews', 'riga', S('s12_3', 0.0), TOTAL, grow=1.6, glow_only=True)
arc_ev('riga', 'moscow', S('s12_3', 0.8), TOTAL, grow=1.2, glow_only=True)
marker_ev('moscow', S('s12_3', 0.4), TOTAL, label='모스크바', sub='8월 25일')
marker_ev('andrews', S('s12_3', 0.2), TOTAL, sub='')
cam(S('outro_0', -0.2), -10, 47, 140, 14.0)

# mentions (automatic from plan) -> network highlights
MENTION = [(x['t0'] + f * x['dur'], nid) for x in P['sentences'] for nid, f in x['mentions']]


# ------------------------------------------------------------------ camera build
def build_camera():
    cams = sorted(CAM, key=lambda c: c[0])
    out = np.zeros((N, 3)); cur = np.array(cams[0][1:4], float); frm = cur.copy(); k = 0; act = None
    for i in range(N):
        t = i / FPS
        while k < len(cams) and cams[k][0] <= t:
            frm = out[i - 1].copy() if i > 0 else cur.copy(); act = cams[k]; k += 1
        if act is None:
            v = cur.copy(); da = t
        else:
            t0, lo, vv, ww, dur = act
            e = ease_io((t - t0) / dur) if dur > 0 else 1.0
            wl = math.exp(math.log(frm[2]) + (math.log(ww) - math.log(frm[2])) * e)
            dist = math.hypot(lo - frm[0], vv - frm[1])
            peak = max(frm[2], ww, dist * 1.25)
            bump = (peak - max(frm[2], ww)) * math.sin(math.pi * e)
            v = np.array([frm[0] + (lo - frm[0]) * e, frm[1] + (vv - frm[1]) * e, wl + max(0, bump)]); da = t - (t0 + dur)
        if da > 0:
            v[2] *= 1 - 0.035 * (1 - math.exp(-da / 7.0))
        out[i] = v
    return out


CAMS = build_camera()
TW = TIERS['W']; TE = TIERS['E']


class View:
    def __init__(s, i):
        lon, v, w = CAMS[i]
        umin, umax = TW['lon0'], TW['lon1']; vmin, vmax = ym(TW['lat0']), ym(TW['lat1'])
        w = min(w, umax - umin - 0.01, (vmax - vmin - 0.01) * W_OUT / H_OUT)
        s.w = w; s.h = w * H_OUT / W_OUT; s.s = W_OUT / w
        s.u0 = min(max(lon - w / 2, umin), umax - w)
        s.v1 = min(max(v + s.h / 2, vmin + s.h), vmax)

    def xy(s, lon, lat): return (lon - s.u0) * s.s, (s.v1 - ym(lat)) * s.s
    def uvs(s, uv): return np.column_stack([(uv[:, 0] - s.u0) * s.s, (s.v1 - uv[:, 1]) * s.s])

    def visible(s, mn, mx, pad=0.0):
        return not (mx[0] < s.u0 - pad or mn[0] > s.u0 + s.w + pad or mx[1] < s.v1 - s.h - pad or mn[1] > s.v1 + pad)

    def base(s):
        need = W_OUT / s.w
        im = s._tier('W', need)
        inside = (s.u0 >= TE['lon0'] + 0.1 and s.u0 + s.w <= TE['lon1'] - 0.1 and s.v1 <= ym(TE['lat1']) - 0.05 and s.v1 - s.h >= ym(TE['lat0']) + 0.05)
        aE = smooth((need - 26) / 14) if inside else 0.0
        if aE > 0.01:
            im = Image.blend(im, s._tier('E', need), aE)
        return im

    def _tier(s, n, need):
        T = TIERS[n]; lvs = sorted(T['levels'])
        lv = next((l for l in lvs if l >= need * 0.95), lvs[-1])
        x0 = (s.u0 - T['lon0']) * lv; y0 = (ym(T['lat1']) - s.v1) * lv
        im = BASE[(n, lv)]
        x1 = min(x0 + s.w * lv, im.width); y1 = min(y0 + s.h * lv, im.height)
        return im.resize((W_OUT, H_OUT), Image.BILINEAR, box=(max(0.0, x0), max(0.0, y0), x1, y1))


# ------------------------------------------------------------------ map drawing
def path_rings(ctx, view, rings, min_px=1.2):
    n = 0
    for uv, mn, mx in rings:
        if not view.visible(mn, mx): continue
        if (mx - mn).max() * view.s < min_px: continue
        S_ = view.uvs(uv)
        ctx.move_to(*S_[0])
        for x, y in S_[1:]: ctx.line_to(x, y)
        ctx.close_path(); n += 1
    return n


def draw_borders(ctx, view):
    lod = 'fine' if view.w < 20 else 'coarse'
    ctx.new_path()
    for k, rings in BORD[lod].items():
        path_rings(ctx, view, rings)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(0.78, 0.83, 0.9, 0.30 if view.w < 40 else 0.22); ctx.set_line_width(0.7); ctx.stroke()


def draw_country(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.7, 0.6) * e.get('a', 0.2)
    if a <= 0.005: return
    lod = 'fine' if view.w < 20 else 'coarse'
    col = C[e['col']]
    for code in e['codes']:
        ctx.new_path()
        if not path_rings(ctx, view, BORD[lod].get(code, [])): continue
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgba(*col, a); ctx.fill_preserve()
        for wd, al in ((7, 0.07), (3.2, 0.2), (1.2, 0.9)):
            ctx.set_source_rgba(*col, al * a / e.get('a', 0.2)); ctx.set_line_width(wd); ctx.stroke_preserve()
        ctx.new_path()


def make_hatch(col, sp=7, wd=1.3, al=0.55):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, sp, sp); c = cairo.Context(s)
    c.set_source_rgba(*col, al); c.set_line_width(wd)
    c.move_to(-1, sp + 1); c.line_to(sp + 1, -1); c.move_to(-1, 1); c.line_to(1, -1); c.move_to(sp - 1, sp + 1); c.line_to(sp + 1, sp - 1); c.stroke()
    p = cairo.SurfacePattern(s); p.set_extend(cairo.EXTEND_REPEAT); return p


HATCH = make_hatch(C['ru'])


def draw_occupied(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.9, 0.9)
    if a <= 0.01: return
    ctx.new_path()
    if not path_rings(ctx, view, OCC[e['key']]): return
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgba(*hexc('#d7263d'), 0.26 * a); ctx.fill_preserve()
    ctx.save(); ctx.clip_preserve(); ctx.set_source(HATCH); ctx.paint_with_alpha(a); ctx.restore()
    ctx.set_source_rgba(*C['ru'], 0.3 * a); ctx.set_line_width(4); ctx.stroke_preserve()
    ctx.set_source_rgba(*C['ru'], 0.95 * a); ctx.set_line_width(1.4); ctx.stroke(); ctx.new_path()


def bezier(p0, p1, n=72, bulge=0.2):
    u0, v0 = p0[0], ym(p0[1]); u1, v1 = p1[0], ym(p1[1])
    mu, mv = (u0 + u1) / 2, (v0 + v1) / 2; d = math.hypot(u1 - u0, v1 - v0)
    nx, ny = -(v1 - v0) / (d + 1e-9), (u1 - u0) / (d + 1e-9)
    if ny < 0: nx, ny = -nx, -ny
    cu, cv = mu + nx * d * bulge, mv + ny * d * bulge
    tt = np.linspace(0, 1, n)[:, None]
    return (1 - tt) ** 2 * np.array([u0, v0]) + 2 * (1 - tt) * tt * np.array([cu, cv]) + tt ** 2 * np.array([u1, v1])


def glow_line(ctx, S_, col, a, w, dash=None):
    ctx.new_path(); ctx.move_to(*S_[0])
    for x, y in S_[1:]: ctx.line_to(x, y)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash: ctx.set_dash(dash)
    for wd, al in ((w * 4.5, 0.08), (w * 2.2, 0.22), (w, 0.95)):
        ctx.set_source_rgba(*col, al * a); ctx.set_line_width(wd); ctx.stroke_preserve()
    ctx.new_path(); ctx.set_dash([])


def arrowhead(ctx, S_, col, a, size=8):
    if len(S_) < 2: return
    (x0, y0), (x1, y1) = S_[-2], S_[-1]; ang = math.atan2(y1 - y0, x1 - x0)
    ctx.new_path(); ctx.move_to(x1 + math.cos(ang) * 2, y1 + math.sin(ang) * 2)
    for s_ in (2.5, -2.5):
        ctx.line_to(x1 - math.cos(ang + s_ / 6) * size, y1 - math.sin(ang + s_ / 6) * size)
    ctx.close_path(); ctx.set_source_rgba(*col, a); ctx.fill()


def plane_glyph(ctx, x, y, ang, a, sc=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(sc, sc)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 16); g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.5 * a); g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
    ctx.set_source(g); ctx.arc(0, 0, 16, 0, 2 * math.pi); ctx.fill()
    ctx.new_path(); ctx.move_to(9, 0); ctx.line_to(1, 1.6); ctx.line_to(-2, 8); ctx.line_to(-4, 8); ctx.line_to(-2.4, 1.6)
    ctx.line_to(-7, 1.4); ctx.line_to(-9, 4); ctx.line_to(-10, 4); ctx.line_to(-9, 0); ctx.line_to(-10, -4); ctx.line_to(-9, -4)
    ctx.line_to(-7, -1.4); ctx.line_to(-2.4, -1.6); ctx.line_to(-4, -8); ctx.line_to(-2, -8); ctx.line_to(1, -1.6); ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, a); ctx.fill_preserve(); ctx.set_source_rgba(0, 0, 0, 0.5 * a); ctx.set_line_width(0.6); ctx.stroke()
    ctx.restore()


def draw_arc(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.3, 0.6)
    if a <= 0.01: return
    if 'uv' not in e: e['uv'] = bezier(e['p0'], e['p1'], bulge=0.16 if e['kind'] == 'flow' else 0.1)
    prog = ease_io((t - e['t0']) / e['grow']) if e['grow'] > 0 else 1
    S_ = view.uvs(e['uv']); n = max(2, int(len(S_) * prog)); sub = S_[:n]
    tension = e['kind'] == 'tension'
    col = C['ru'] if tension else (C['gold'] if not e.get('glow_only') else C['gold'])
    glow_line(ctx, sub, col, a * (0.7 if e.get('glow_only') else 1), 1.8 if not tension else 1.5, dash=[5, 4] if tension else None)
    if prog < 1 and e.get('plane'):
        (x0, y0), (x1, y1) = sub[-2], sub[-1]
        plane_glyph(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a)
    elif not e.get('plane') or prog >= 1:
        if prog >= 0.98 or not e.get('plane'): arrowhead(ctx, sub, col, a)
    if e.get('label') and prog >= 0.99:
        k = int(len(S_) * e.get('label_t', 0.5)); x, y = S_[min(k, len(S_) - 1)]
        text(ctx, e['label'], x, y - 8, 10.5, 'sansb', col, a * smooth((t - e['t0'] - e['grow']) / 0.4), 3, 'c')


def draw_channel(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.6, 0.6)
    if a <= 0.01: return
    if 'uv' not in e: e['uv'] = bezier(e['p0'], e['p1'], bulge=0.18)
    S_ = view.uvs(e['uv']); prog = ease_io((t - e['t0']) / 1.8); n = max(2, int(len(S_) * prog))
    glow_line(ctx, S_[:n], C['teal'], a * 0.8, 1.4, dash=[3, 5])
    if prog >= 1:
        for k in range(6):
            f = ((t * 0.12) + k / 6) % 1.0; f2 = 1 - f if k % 2 else f
            x, y = S_[int(f2 * (len(S_) - 1))]
            g = cairo.RadialGradient(x, y, 0, x, y, 6); g.add_color_stop_rgba(0, *C['teal'], 0.95 * a); g.add_color_stop_rgba(1, *C['teal'], 0)
            ctx.set_source(g); ctx.arc(x, y, 6, 0, 2 * math.pi); ctx.fill()
        x, y = S_[len(S_) // 2]
        text(ctx, e['label'], x, y - 10, 12, 'sansb', C['teal'], a * smooth((t - e['t0'] - 1.8) / 0.5), 3, 'c')


def icon(ctx, kind, x, y, col, a, t):
    if kind == 'boom':
        for k in range(10):
            ang = k * math.pi / 5 + 0.2; r1, r2 = (9, 4) if k % 2 == 0 else (6, 3)
            ctx.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1); ctx.line_to(x + math.cos(ang + math.pi / 10) * r2, y + math.sin(ang + math.pi / 10) * r2)
        ctx.close_path(); ctx.set_source_rgba(*C['amber'], a); ctx.fill()
    elif kind == 'drone':
        ctx.set_source_rgba(*col, a); ctx.set_line_width(1.4)
        for dx, dy in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
            ctx.move_to(x, y); ctx.line_to(x + dx, y + dy); ctx.stroke(); ctx.arc(x + dx, y + dy, 2.4, 0, 2 * math.pi); ctx.stroke()
    elif kind == 'ship':
        ctx.new_path(); ctx.move_to(x - 8, y - 1); ctx.line_to(x + 8, y - 1); ctx.line_to(x + 5, y + 4); ctx.line_to(x - 5, y + 4); ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, a); ctx.fill(); ctx.rectangle(x - 2, y - 6, 4, 5); ctx.fill()
    else:
        ctx.arc(x, y, 3.2, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, a); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.set_line_width(1); ctx.stroke()


def stamp(ctx, x, y, s, a, rot=-0.18, col=None):
    col = col or C['ru']
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    font(ctx, 'sansk', 13); w = ctx.text_extents(s).x_advance
    rrect(ctx, -w / 2 - 8, -13, w + 16, 22, 3); ctx.set_source_rgba(*col, 0.9 * a); ctx.set_line_width(2); ctx.stroke()
    ctx.move_to(-w / 2, 3.5); ctx.set_source_rgba(*col, a); ctx.show_text(s); ctx.restore()


def draw_marker(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.3, 0.5)
    if a <= 0.01: return
    x, y = view.xy(e['lon'], e['lat']); lt = t - e['t0']
    if x < -80 or x > W_OUT + 80 or y < -40 or y > H_OUT + 40: return
    col = C['gold'] if e.get('hl') else C['white']
    for k in range(2):
        f = ((lt * 0.55) + k / 2) % 1.0; r = 4 + 22 * ease_out(f)
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(*col, 0.55 * (1 - f) * a); ctx.set_line_width(1.4); ctx.stroke()
    if e.get('icon', 'dot') != 'none':
        icon(ctx, e.get('icon', 'dot'), x, y, col, a * ease_out(lt / 0.3), t)
    side = e.get('side', 'right'); la = a * smooth((lt - 0.2) / 0.4)
    dx, dy, anc = {'right': (12, 4, 'l'), 'left': (-12, 4, 'r'), 'top': (0, -14, 'c'), 'bottom': (0, 20, 'c')}[side]
    text(ctx, e['label'], x + dx, y + dy, 13, 'sansb', (1, 1, 1), la, 3.2, anc)
    if e.get('sub'):
        text(ctx, e['sub'], x + dx, y + dy + 15, 10.5, 'sansm', C['gold'], la, 3, anc)
    if e.get('stamp'):
        stamp(ctx, x + dx + (40 if anc == 'l' else -40 if anc == 'r' else 0), y + dy + 36, e['stamp'], la, col=C['muted'])


def draw_boom(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.05, 0.8); x, y = view.xy(e['lon'], e['lat']); lt = t - e['t0']
    for k in range(3):
        r = 6 + 60 * ease_out((lt - k * 0.12) / 1.2)
        ctx.arc(x, y, max(r, 0.1), 0, 2 * math.pi); ctx.set_source_rgba(*C['gold'], 0.6 * a * (1 - clamp01(lt / 1.6))); ctx.set_line_width(2); ctx.stroke()


def draw_shield(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.6, 0.6)
    if a <= 0.01: return
    x, y = view.xy(e['lon'], e['lat']); r = e['r_km'] / 111.0 / math.cos(math.radians(e['lat'])) * view.s * ease_out((t - e['t0']) / 1.0)
    ctx.arc(x, y, max(r, 0.1), 0, 2 * math.pi); ctx.set_source_rgba(*C['us'], 0.08 * a); ctx.fill_preserve()
    ctx.set_dash([6, 5], -t * 8); ctx.set_source_rgba(*C['us'], 0.9 * a); ctx.set_line_width(1.8); ctx.stroke(); ctx.set_dash([])
    # pause icon
    ctx.set_source_rgba(*C['us'], a); ctx.rectangle(x + r * 0.7 - 6, y - r * 0.7 - 8, 4, 14); ctx.rectangle(x + r * 0.7 + 2, y - r * 0.7 - 8, 4, 14); ctx.fill()
    text(ctx, e['label'], x + r * 0.7 + 12, y - r * 0.7 + 4, 11.5, 'sansb', C['us'], a * smooth((t - e['t0'] - 0.8) / 0.4), 3, 'l')


# ------------------------------------------------------------------ badges
def draw_flag_wave(ctx, key, cx, cy, wdt, a, t, clip=None):
    fs = scaled(key, FLAG_PIL[key], wdt); fh = fs.get_height(); fw = fs.get_width(); n = 14
    for i in range(n):
        sx = fw * i / n; sw = fw / n + 1
        dy = math.sin(t * 3.0 + i * 0.5) * wdt * 0.035
        ctx.save()
        ctx.rectangle(cx - fw / 2 + sx, cy - fh / 2 + dy - 1, sw, fh + 2); ctx.clip()
        ctx.set_source_surface(fs, cx - fw / 2, cy - fh / 2 + dy); ctx.paint_with_alpha(a)
        sh = 0.18 * (0.5 + 0.5 * math.sin(t * 3.0 + i * 0.5 + 1.2))
        ctx.set_source_rgba(0, 0, 0, sh * a); ctx.paint()
        ctx.restore()


def draw_badge_at(ctx, x, y, e, t, a):
    R = e.get('R', 30); lt = t - e['t0']
    k = ease_back(lt / 0.5)
    if k <= 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.scale(k, k)
    acc = C.get(e.get('accent', 'gold'), C['gold'])
    for r_, al in ((R + 7, 0.10), (R + 4, 0.18)):
        ctx.arc(1.5, 3, r_, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, al * a); ctx.fill()
    if e['kind'] in ('person', 'flag'):
        ctx.save(); ctx.arc(0, 0, R, 0, 2 * math.pi); ctx.clip()
        ctx.set_source_rgba(*hexc('#1d3b2e'), a); ctx.paint()
        if e['kind'] == 'person':
            draw_flag_wave(ctx, (e['flag'], '43'), R * 0.25, -R * 0.05, R * 2.3, 0.92 * a, t)
        else:
            fs = scaled((e['flag'], '11'), FLAG_PIL[(e['flag'], '11')], R * 2.1)
            ctx.set_source_surface(fs, -fs.get_width() / 2, -fs.get_height() / 2); ctx.paint_with_alpha(a)
        ctx.restore()
    else:
        ctx.arc(0, 0, R, 0, 2 * math.pi); ctx.set_source_rgba(*hexc(e.get('fill', '#243044')), a); ctx.fill()
        text(ctx, e.get('mono', ''), 0, R * 0.22, R * 0.62, 'sansk', (1, 1, 1), a, 0, 'c')
    if e['kind'] == 'person':
        ps = scaled(e['pid'], PORT_PIL[e['pid']], R * 1.72); pw, ph = ps.get_width(), ps.get_height()
        ctx.save()
        ctx.arc(0, 0, R, 0, 2 * math.pi); ctx.rectangle(-R * 0.66, -R * 2.4, R * 1.32, R * 2.4)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING); ctx.clip()
        ctx.set_source_surface(ps, -pw / 2, R - ph + R * 0.02); ctx.paint_with_alpha(a)
        ctx.restore()
    ctx.new_path(); ctx.arc(0, 0, R, 0, 2 * math.pi)
    ctx.set_source_rgba(0.03, 0.04, 0.06, a); ctx.set_line_width(3.2); ctx.stroke_preserve()
    ctx.set_source_rgba(*acc, 0.9 * a); ctx.set_line_width(1.4); ctx.stroke()
    ctx.restore()
    la = a * smooth((lt - 0.25) / 0.35)
    if e.get('label') and la > 0.01:
        font(ctx, 'sansb', 12); w = ctx.text_extents(e['label']).x_advance
        rrect(ctx, x - w / 2 - 8, y + R * k + 5, w + 16, 20, 3); ctx.set_source_rgba(0.03, 0.04, 0.06, 0.82 * la); ctx.fill()
        text(ctx, e['label'], x, y + R * k + 19.5, 12, 'sansb', (1, 1, 1), la, 0, 'c')
        if e.get('role'):
            text(ctx, e['role'], x, y + R * k + 38, 10, 'sansm', acc if e.get('accent') != 'us' else C['gold'], la, 2.6, 'c')
    if e.get('stamp') and lt > 0.9:
        stamp(ctx, x + R * 0.55, y - R * 0.2, e['stamp'], a * smooth((lt - 0.9) / 0.25), rot=-0.25)


def draw_badge(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.01, 0.45)
    if a <= 0.01: return
    x, y = (view.xy(e['lon'], e['lat']) if e.get('lon') is not None else (e['x'], e['y']))
    draw_badge_at(ctx, x, y, e, t, a)


# ------------------------------------------------------------------ cards
def draw_card(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.45, 0.45)
    if a <= 0.01: return
    slide = (1 - ease_out((t - e['t0']) / 0.55)) * 36
    lines = e['lines']; wdt = e.get('w', 250)
    font(ctx, 'sansm', 12.5)
    for s_ in lines: wdt = max(wdt, ctx.text_extents(s_).x_advance + 44)
    if e.get('big'): font(ctx, 'sansk', e.get('big_size', 30)); wdt = max(wdt, ctx.text_extents(e['big']).x_advance + 44)
    h = 40 + (e.get('big_size', 30) + 12 if e.get('big') else 0) + 19 * len(lines)
    x = W_OUT - wdt - 22 + slide; y = e.get('y', 86)
    rrect(ctx, x, y, wdt, h, 5); ctx.set_source_rgba(0.06, 0.07, 0.1, 0.84 * a); ctx.fill()
    ctx.set_source_rgba(*C[e['accent']], a); ctx.rectangle(x, y + 10, 3, h - 20); ctx.fill()
    text(ctx, e['tag'], x + 18, y + 22, 10.5, 'sansb', C[e['accent']] if e['accent'] != 'us' else C['us'], a, 0, 'l', spacing=0.6)
    yy = y + 30
    if e.get('big'):
        text(ctx, e['big'], x + 18, yy + e.get('big_size', 30) + 2, e.get('big_size', 30), 'sansk', (1, 1, 1), a, 0, 'l'); yy += e.get('big_size', 30) + 12
    st = e.get('stagger')
    for i, s_ in enumerate(lines):
        la = a * (smooth((t - st[i]) / 0.4) if st else 1)
        text(ctx, s_, x + 18, yy + 16 + 19 * i, 12.5, 'serif' if e.get('quote') else 'sansm', (0.93, 0.9, 0.88), la, 0, 'l')


# ------------------------------------------------------------------ panels
def prov_tag(ctx, chart, a, x=W_OUT - 40, y=52):
    pv = (chart or {}).get('provenance', {})
    if pv.get('verification') == 'verified' and pv.get('sources'): return
    s_ = '추정 · 출처 미기재' if not pv.get('sources') else '추정'
    font(ctx, 'sansb', 10); w = ctx.text_extents(s_).x_advance
    rrect(ctx, x - w - 14, y - 13, w + 14, 19, 3); ctx.set_source_rgba(*C['amber'], 0.9 * a); ctx.set_line_width(1); ctx.stroke()
    text(ctx, s_, x - 7, y + 1, 10, 'sansb', C['amber'], a, 0, 'r')


def panel_head(ctx, a, kicker, title):
    text(ctx, kicker, 48, 50, 10.5, 'sansb', C['gold'], a, 0, 'l', spacing=2.2)
    ctx.set_source_rgba(*C['gold'], 0.8 * a); ctx.rectangle(48, 58, 34 * a, 1.6); ctx.fill()
    text(ctx, title, 48, 88, 22, 'serifb', (1, 1, 1), a, 0, 'l')


def P_network(ctx, t, e, a):
    ch = P['charts'][e['chart']]; d = ch['data']; lt = t - e['t0']
    panel_head(ctx, a, 'STAKEHOLDERS', ch['title']); prov_tag(ctx, ch, a)
    cols = {'left': [], 'center': [], 'right': []}
    for n in d['nodes']: cols[n['col']].append(n)
    X = {'left': 150, 'center': 427, 'right': 704}; pos = {}; order = {}
    for ci, (c, ns) in enumerate([('center', cols['center']), ('left', cols['left']), ('right', cols['right'])]):
        for i, n in enumerate(ns):
            yy = 175 + (i - (len(ns) - 1) / 2) * 92 + 55
            pos[n['id']] = (X[c], yy); order[n['id']] = ci * 0.9 + i * 0.25
    ES = {'영향': (C['gold'], None, True), '연관': (C['muted'], None, False), '대립': (C['ru'], [5, 4], True), '동맹': (C['green'], None, False)}
    for k, ed in enumerate(d['edges']):
        if ed['source'] not in pos or ed['target'] not in pos: continue
        t0 = 3.2 + k * 0.18; prog = ease_io((lt - t0) / 0.8)
        if prog <= 0: continue
        (x0, y0), (x1, y1) = pos[ed['source']], pos[ed['target']]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 18 * (1 if x1 >= x0 else -1)
        pts = [((1 - s) ** 2 * x0 + 2 * (1 - s) * s * mx + s * s * x1, (1 - s) ** 2 * y0 + 2 * (1 - s) * s * my + s * s * y1) for s in np.linspace(0, prog, 24)]
        col, dash, arrow = ES.get(ed['type'], ES['연관'])
        ctx.new_path(); ctx.move_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        if dash: ctx.set_dash(dash)
        ctx.set_source_rgba(*col, 0.75 * a); ctx.set_line_width(1.4 if ed['type'] != '연관' else 1.0); ctx.stroke(); ctx.set_dash([])
        if prog > 0.95:
            px, py = pts[len(pts) // 2]
            text(ctx, ed.get('label', ''), px, py - 4, 9.5, 'sansm', col, a * 0.9, 2.4, 'c')
    hl = {nid for tt, nid in MENTION if tt - 0.2 <= t <= tt + 3.0}
    for n in d['nodes']:
        x, y = pos[n['id']]; t0 = e['t0'] + 0.5 + order[n['id']]
        if t < t0: continue
        if n.get('kind') == 'person' and n['id'] in PORT_PIL:
            be = dict(kind='person', pid=n['id'], flag=n['flag'].lower(), R=27 if not n.get('accent') else 33, t0=t0,
                      label=n['label'], role=n.get('role', ''), accent='gold' if n.get('accent') else {'US': 'us', 'RU': 'ru', 'UA': 'ua'}.get(n.get('flag'), 'gold'))
        elif n.get('flag'):
            be = dict(kind='flag', flag=n['flag'].lower(), R=24, t0=t0, label=n['label'], role=n.get('role', ''), accent='ru')
        else:
            mono = {'whitehouse': '백악관', 'cia': 'CIA', 'nato': 'NATO'}.get(n['id'], n['label'][:3])
            be = dict(kind='org', mono=mono, fill={'nato': '#1f3a6e', 'cia': '#27313f', 'whitehouse': '#2b2f3a'}.get(n['id'], '#243044'), R=24, t0=t0, label=n['label'], role=n.get('role', ''), accent='teal' if n['id'] == 'nato' else 'us')
        if n['id'] in hl:
            f = (t * 1.2) % 1.0
            ctx.arc(x, y, be['R'] + 6 + 16 * f, 0, 2 * math.pi); ctx.set_source_rgba(*C['gold'], 0.8 * (1 - f) * a); ctx.set_line_width(2); ctx.stroke()
        draw_badge_at(ctx, x, y, be, t, a)


def P_dots(ctx, t, e, a):
    ch = P['charts'][e['chart']]; lt = t - e['t0']
    panel_head(ctx, a, 'DIAGNOSIS', ch['title']); prov_tag(ctx, ch, a)
    x0, y0, sp = 250, 135, 25
    for i in range(100):
        r_, c_ = divmod(i, 10); f = smooth((lt - 0.4 - i * 0.012) / 0.3)
        if f <= 0: continue
        x, y = x0 + c_ * sp, y0 + r_ * sp
        acc = (i == 0)
        if acc:
            p = 0.6 + 0.4 * math.sin(t * 4)
            g = cairo.RadialGradient(x, y, 0, x, y, 16); g.add_color_stop_rgba(0, *C['ru'], 0.7 * p * a); g.add_color_stop_rgba(1, *C['ru'], 0)
            ctx.set_source(g); ctx.arc(x, y, 16, 0, 2 * math.pi); ctx.fill()
        ctx.arc(x, y, 7.5 * f, 0, 2 * math.pi); ctx.set_source_rgba(*(C['ru'] if acc else (0.42, 0.45, 0.52)), a); ctx.fill()
    la = a * smooth((lt - 2.0) / 0.5)
    text(ctx, '1', 540, 168, 64, 'sansk', C['ru'], la, 0, 'l'); text(ctx, '%', 582, 168, 30, 'sansk', C['ru'], la, 0, 'l')
    text(ctx, '추가로 점령한 몫', 542, 196, 14, 'sansb', (1, 1, 1), la, 0, 'l')
    text(ctx, '99% — 움직이지 않은 나머지', 542, 222, 12.5, 'sansm', C['muted'], la, 0, 'l')
    lb = a * smooth((lt - 3.2) / 0.5)
    ctx.set_source_rgba(1, 1, 1, 0.15 * lb); ctx.rectangle(542, 250, 250, 1); ctx.fill()
    text(ctx, 'DeepState 실측 교차 확인', 542, 276, 10.5, 'sansb', C['gold'], lb, 0, 'l', spacing=0.6)
    p0, p1 = PCT.get('ds_2025-02-01', 18.5), PCT.get('ds_2026-09-01', 19.3)
    text(ctx, f'{p0:.1f}% → {p1:.1f}%', 542, 306, 22, 'sansk', (1, 1, 1), lb, 0, 'l')
    text(ctx, f'러시아 통제 면적 (2025.2 → 2026.8), +{p1 - p0:.1f}%p', 542, 328, 11, 'sansm', C['muted'], lb, 0, 'l')


def P_gantt(ctx, t, e, a):
    ch = P['charts'][e['chart']]; g = P['gantt']; lt = t - e['t0']
    panel_head(ctx, a, 'TIMELINE', ch['title']); prov_tag(ctx, ch, a)
    from datetime import date
    def fx(s):
        y_, m_, d_ = map(int, s.split('-')); dd = date(y_, m_, d_); return 250 + (dd - date(2025, 1, 1)).days / (date(2030, 1, 1) - date(2025, 1, 1)).days * 560
    ctx.set_source_rgba(1, 1, 1, 0.25 * a); ctx.rectangle(250, 368, 560, 1); ctx.fill()
    for yr in range(2025, 2031):
        x = fx(f'{yr}-01-01'); ctx.rectangle(x, 364, 1, 8); ctx.fill()
        text(ctx, str(yr), x, 388, 10.5, 'sansm', C['muted'], a, 0, 'c')
    cols = [C['ru'], C['muted'], C['teal'], C['green']]
    notes = {r['label']: r.get('note', '') for r in ch['data']}
    for i, tk in enumerate(g['tasks']):
        y = 130 + i * 56; f = ease_out((lt - 0.6 - i * 0.5) / 1.1)
        if f <= 0: continue
        x0, x1 = fx(tk['start']), fx(tk['end'])
        text(ctx, tk['label'], 236, y + 15, 12.5, 'sansb', (1, 1, 1), a * clamp01(f * 2), 0, 'r')
        text(ctx, notes.get(tk['label'], ''), 236, y + 31, 9.5, 'sansm', C['muted'], a * clamp01(f * 2), 0, 'r')
        rrect(ctx, x0, y, max(2, (x1 - x0) * f), 22, 4); ctx.set_source_rgba(*cols[i % 4], 0.85 * a); ctx.fill()
    tx = fx(g['today']); tf = a * smooth((lt - 3.0) / 0.5)
    ctx.set_dash([4, 4]); ctx.set_source_rgba(*C['gold'], 0.95 * tf); ctx.set_line_width(1.4); ctx.move_to(tx, 112); ctx.line_to(tx, 372); ctx.stroke(); ctx.set_dash([])
    text(ctx, '발행일 8.29', tx, 106, 10.5, 'sansb', C['gold'], tf, 2.5, 'c')


def P_dual(ctx, t, e, a):
    ch = P['charts'][e['chart']]; d = ch['data']; lt = t - e['t0']
    panel_head(ctx, a, 'OIL · AUGUST', ch['title']); prov_tag(ctx, ch, a)
    X0, X1, Y0, Y1, lo, hi = 150, 690, 140, 360, 80, 96
    fy = lambda v: Y1 - (v - lo) / (hi - lo) * (Y1 - Y0)
    for v in range(80, 97, 4):
        ctx.set_source_rgba(1, 1, 1, 0.08 * a); ctx.rectangle(X0, fy(v), X1 - X0, 1); ctx.fill()
        text(ctx, f'${v}', X0 - 10, fy(v) + 4, 10, 'sansm', C['muted'], a, 0, 'r')
    xs = [X0 + 30, (X0 + X1) / 2, X1 - 30]
    for i, s_ in enumerate(d['left']['series']): text(ctx, s_['x'], xs[i], Y1 + 22, 11, 'sansm', C['muted'], a, 0, 'c')
    for si, (key, col) in enumerate((('left', C['gold']), ('right', C['us']))):
        ser = d[key]['series']; pts = [(xs[i], fy(p['y'])) for i, p in enumerate(ser)]
        prog = ease_io((lt - 0.6 - si * 0.5) / 1.8)
        if prog <= 0: continue
        dense = []
        for i in range(len(pts) - 1):
            for s in np.linspace(0, 1, 20, endpoint=False): dense.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * s, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * s))
        dense.append(pts[-1]); sub = dense[:max(2, int(len(dense) * prog))]
        glow_line(ctx, np.array(sub), col, a, 2.2)
        for i, p in enumerate(pts):
            if len(sub) >= i * 20 + 1:
                ctx.arc(p[0], p[1], 4, 0, 2 * math.pi); ctx.set_source_rgba(*col, a); ctx.fill()
                text(ctx, f"{ser[i]['y']:.2f}", p[0], p[1] - 10 if si == 0 else p[1] + 18, 11, 'sansb', col, a, 2.6, 'c')
        text(ctx, d[key]['label'], X1 + 12, pts[-1][1] + 4, 12, 'sansb', col, a * clamp01(prog * 3 - 2), 2.6, 'l')


def P_versus(ctx, t, e, a):
    lt = t - e['t0']
    panel_head(ctx, a, 'CONTRADICTION', '말들이 어긋나는 자리')
    L = [('트럼프 대통령', '“준일상적인 방문” · 나토 경고 부인'), ('크렘린 · 페스코프', '“겁주는 이야기는 사실무관”'), ('나리시킨', '“통상적인 실무 형식”')]
    Rr = [('WSJ · CNN · CBS', '나토 공격 말라는 경고 전달'), ('뉴욕타임스 (8.28)', '비관적 전황 평가 전달'), ('우크라인스카 프라우다', '구체적 보복 위협은 없었다')]
    for side, (title, items, col, x) in enumerate((('공식 발언 — 무게를 낮춘다', L, C['us'], 60), ('익명 취재원 보도 — 무게를 키운다', Rr, C['amber'], 450))):
        fa = a * smooth((lt - 0.4 - side * 1.2) / 0.5)
        rrect(ctx, x, 118, 344, 262, 6); ctx.set_source_rgba(0.08, 0.09, 0.13, 0.9 * fa); ctx.fill()
        ctx.set_source_rgba(*col, fa); ctx.rectangle(x, 118, 344, 3); ctx.fill()
        text(ctx, title, x + 20, 150, 14, 'sansb', col, fa, 0, 'l')
        for i, (who, what) in enumerate(items):
            ia = a * smooth((lt - 1.0 - side * 1.2 - i * 0.45) / 0.4)
            text(ctx, who, x + 20, 190 + i * 62, 11, 'sansb', C['muted'], ia, 0, 'l')
            text(ctx, what, x + 20, 212 + i * 62, 13.5, 'serifb', (1, 1, 1), ia, 0, 'l')
    if lt > 1.0:
        draw_badge_at(ctx, 360, 155, dict(kind='person', pid='trump', flag='us', R=24, t0=e['t0'] + 1.0, accent='us'), t, a)
    fb = a * smooth((lt - 6.0) / 0.6)
    text(ctx, '회담이 있었다는 사실은 누구도 부인하지 않았다', W_OUT / 2, 412, 13, 'sansb', C['gold'], fb, 3, 'c')


def P_fork(ctx, t, e, a):
    lt = t - e['t0']
    panel_head(ctx, a, 'SCENARIOS', '여기서 갈라지는 길들')
    ox, oy = 150, 250
    ctx.arc(ox, oy, 8, 0, 2 * math.pi); ctx.set_source_rgba(*C['gold'], a); ctx.fill()
    text(ctx, '8월 25일', ox, oy + 28, 12, 'sansb', C['gold'], a, 2.5, 'c')
    items = [('실무 접촉 재개', '다음 만남의 비용은 이미 낮아졌다', C['green']), ('아무 일도 없음', '메시지는 갔지만 계산은 그대로', C['muted']), ('나토 동쪽 다음 사건', '올가을 시험 시간대의 시작', C['ru'])]
    for i, (h, s_, col) in enumerate(items):
        ty = 150 + i * 100; f = ease_io((lt - 0.6 - i * 0.8) / 0.9)
        if f <= 0: continue
        pts = [(ox + (430 - ox) * s * f, oy + (ty - oy) * smooth(s * f)) for s in np.linspace(0, 1, 30)]
        glow_line(ctx, np.array(pts), col, a, 1.6)
        ca = a * smooth((lt - 1.3 - i * 0.8) / 0.4)
        rrect(ctx, 440, ty - 30, 340, 60, 5); ctx.set_source_rgba(0.08, 0.09, 0.13, 0.9 * ca); ctx.fill()
        ctx.set_source_rgba(*col, ca); ctx.rectangle(440, ty - 30, 3, 60); ctx.fill()
        text(ctx, h, 458, ty - 4, 15, 'sansb', (1, 1, 1), ca, 0, 'l'); text(ctx, s_, 458, ty + 17, 11.5, 'sansm', C['muted'], ca, 0, 'l')


def P_check(ctx, t, e, a):
    lt = t - e['t0']
    panel_head(ctx, a, 'CONFIRMED', '확인된 사실은 네 줄')
    items = ['8월 25일, 모스크바에 갔다', '나리시킨·보르트니코프를 만났다', '푸틴은 만나지 않았다', '하루 만에 돌아왔다']
    for i, s_ in enumerate(items):
        y = 150 + i * 52; f = smooth((lt - 0.6 - i * 0.7) / 0.4)
        if f <= 0: continue
        rrect(ctx, 120, y - 22, 30, 30, 5); ctx.set_source_rgba(*C['green'], 0.18 * f * a); ctx.fill()
        ck = ease_out((lt - 0.8 - i * 0.7) / 0.35)
        ctx.new_path(); ctx.move_to(127, y - 7); ctx.line_to(127 + 6 * min(1, ck * 2), y - 7 + 6 * min(1, ck * 2))
        if ck > 0.5: ctx.line_to(133 + 12 * (ck - 0.5) * 2, y + -1 - 14 * (ck - 0.5) * 2)
        ctx.set_source_rgba(*C['green'], a); ctx.set_line_width(2.6); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        text(ctx, s_, 168, y, 17, 'sansb', (1, 1, 1), f * a, 0, 'l')
    fb = a * smooth((lt - 4.2) / 0.6)
    text(ctx, '나머지는 전부 해석의 영역', 168, 372, 14, 'serif', C['muted'], fb, 0, 'l')


PANELS = {'network': P_network, 'dots': P_dots, 'gantt': P_gantt, 'dual_line': P_dual, 'versus': P_versus, 'fork': P_fork, 'checklist': P_check}


def draw_panel(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.6, 0.6)
    if a <= 0.01: return
    ctx.set_source_rgba(0.03, 0.035, 0.05, 0.78 * a); ctx.paint()
    PANELS[e['kind']](ctx, t, e, a)


# ------------------------------------------------------------------ HUD
SEC_IDX = {s['section_id']: i + 1 for i, s in enumerate([{'section_id': k} for k in P['sections']])}


def draw_hud(ctx, t):
    cur = None
    for sec in SECS:
        if SEC0[sec] - 0.4 <= t: cur = sec
    if cur not in P['sections']: return
    a = window(t, SEC0[cur] - 0.4, SEC_END(cur) + 0.2, 0.6, 0.5)
    if any(e['t0'] - 0.2 <= t <= e['t1'] for e in EV if e['type'] == 'panel'): a *= 0.0
    if a <= 0.01: return
    k = ease_out((t - SEC0[cur] + 0.4) / 0.7)
    n = SEC_IDX[cur]
    text(ctx, f'{n:02d} / {len(P["sections"]):02d}', 24 - (1 - k) * 20, 34, 11, 'sansb', C['gold'], a * k, 2.5, 'l', spacing=1.2)
    text(ctx, P['sections'][cur]['heading'], 24 - (1 - k) * 20, 58, 17, 'serifb', (1, 1, 1), a * k, 3.5, 'l')


def draw_brand(ctx, t):
    a = smooth((t - 1.0) / 1.0) * (1 - smooth((t - (TOTAL - 11)) / 1.0))
    text(ctx, '◆ OSINT BRIEFING', W_OUT - 24, 30, 9.5, 'sansb', C['gold'], 0.85 * a, 2, 'r', spacing=1.5)
    text(ctx, P['report']['date'].replace('-', '.'), W_OUT - 24, 44, 9.5, 'sansm', C['muted'], 0.8 * a, 2, 'r')


def draw_subtitle(ctx, t):
    for sid in ORDER:
        x = SENT[sid]
        if x['t0'] - 0.05 <= t <= x['t1'] + 0.25:
            a = min(smooth((t - x['t0'] + 0.05) / 0.18), smooth((x['t1'] + 0.25 - t) / 0.2))
            size = 18.5
            flags = []
            for seg, f in x['segments']: flags += [f] * len(seg)
            txt = ''.join(s for s, f in x['segments'])
            lines = wrap(ctx, txt, 700, size, 'sansm')
            base_y = 452 - (len(lines) - 1) * 25; pos = 0
            for li, ln in enumerate(lines):
                j = txt.find(ln, pos); pos = j + len(ln)
                font(ctx, 'sansm', size); lw = ctx.text_extents(ln).x_advance; xx = W_OUT / 2 - lw / 2
                k = 0
                while k < len(ln):
                    f = flags[j + k] if j + k < len(flags) else 0; k2 = k
                    while k2 < len(ln) and (flags[j + k2] if j + k2 < len(flags) else 0) == f: k2 += 1
                    run = ln[k:k2]
                    text(ctx, run, xx, base_y + li * 25, size, 'sansb' if f else 'sansm', C['gold'] if f else (1, 1, 1), a, 4.2, 'l', halo_a=0.9)
                    font(ctx, 'sansm', size); xx += ctx.text_extents(run).x_advance
                    k = k2
            return


CREDITS = None


def credits_lines():
    import re as _re
    pm = json.load(open('/home/claude/og/assets/library/workshop/references/photo_manifest.json'))['people']
    out = []
    for pid in ('ratcliffe', 'naryshkin', 'bortnikov', 'trump', 'putin', 'zelensky'):
        r = PORT_REG[pid]; lic = r['license']
        who = pm.get(pid, {}).get('artist', '') if r['src'] == 'repo_library' else r.get('credit', '')
        who = _re.sub(r'<[^>]+>', '', who or '').strip()
        who = 'Public domain' if 'ublic domain' in lic else (who[:34] + '…' if len(who) > 35 else who) or 'Wikimedia Commons'
        tag = ' (라이브러리 가공본)' if r['src'] == 'repo_library' else ''
        out.append(f"{PERSON[pid][0]} 사진{tag}: {lic} · {who}" if 'ublic' not in lic else f"{PERSON[pid][0]} 사진{tag}: Public domain")
    out += ['국기: flag-icons (MIT) · 지도: Natural Earth · 지형: AWS Terrain Tiles',
            '점령지 경계: DeepState · 음악: Chris Zabriskie (CC BY 4.0)',
            '원자료: agents_reviewer 리포트 번들 · 차트 수치는 번들 기준 추정치',
            f"내레이션: AI 음성 합성 ({'ElevenLabs' if 'eleven' in P['voice'] else 'edge-tts'})"]
    return out


def draw_cards_full(ctx, t):
    for c in P['cards']:
        if not (c['t0'] - 0.1 <= t <= c['t1'] + 0.1): continue
        a = window(t, c['t0'], c['t1'], 0.6, 0.7); lt = t - c['t0']
        g = cairo.LinearGradient(0, 0, 0, H_OUT)
        g.add_color_stop_rgba(0, 0.01, 0.02, 0.04, 0.8 * a); g.add_color_stop_rgba(0.55, 0.01, 0.02, 0.04, 0.6 * a); g.add_color_stop_rgba(1, 0.01, 0.02, 0.04, 0.88 * a)
        ctx.set_source(g); ctx.paint()
        if c['kind'] == 'title':
            k = ease_out(lt / 1.0)
            text(ctx, 'OSINT BRIEFING  ·  ' + P['report']['date'].replace('-', '.'), W_OUT / 2, 150, 11, 'sansb', C['gold'], a * k, 0, 'c', spacing=2.5)
            lines = wrap(ctx, P['report']['headline'], 520, 30, 'serifb')
            for i, ln in enumerate(lines):
                text(ctx, ln, W_OUT / 2, 212 + i * 44 - (1 - k) * 10, 30, 'serifb', (1, 1, 1), a * smooth((lt - 0.2 - i * 0.2) / 0.6), 0, 'c')
            yb = 212 + len(lines) * 44
            ctx.set_source_rgba(*C['gold'], 0.9 * a); lw = 200 * ease_io((lt - 0.6) / 0.9); ctx.rectangle(W_OUT / 2 - lw / 2, yb - 16, lw, 1.5); ctx.fill()
            for i, ln in enumerate(wrap(ctx, P['report']['deck'], 600, 13.5, 'sansm')):
                text(ctx, ln, W_OUT / 2, yb + 14 + i * 21, 13.5, 'sansm', (0.85, 0.84, 0.86), a * smooth((lt - 1.0) / 0.6), 0, 'c')
        else:
            text(ctx, '자료 및 출처', W_OUT / 2, 110, 20, 'serifb', (1, 1, 1), a, 0, 'c')
            for i, r in enumerate(credits_lines()):
                text(ctx, r, W_OUT / 2, 150 + i * 23, 11.5, 'sansm', (0.86, 0.87, 0.9), a * smooth((lt - 0.3 - i * 0.1) / 0.6), 0, 'c')


def build_vignette():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT); c = cairo.Context(s)
    g = cairo.RadialGradient(W_OUT / 2, H_OUT / 2, H_OUT * 0.35, W_OUT / 2, H_OUT / 2, W_OUT * 0.72)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.62); c.set_source(g); c.paint()
    g = cairo.LinearGradient(0, H_OUT - 110, 0, H_OUT); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    c.set_source(g); c.rectangle(0, H_OUT - 110, W_OUT, 110); c.fill()
    g = cairo.LinearGradient(0, 0, 0, 90); g.add_color_stop_rgba(0, 0, 0, 0, 0.5); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    c.set_source(g); c.rectangle(0, 0, W_OUT, 90); c.fill()
    return s


VIG = build_vignette()
MAPDRAW = {'country': draw_country, 'occupied': draw_occupied, 'arc': draw_arc, 'channel': draw_channel, 'shield': draw_shield,
           'boom': draw_boom, 'marker': draw_marker, 'badge': draw_badge}
LAYER = ['country', 'occupied', 'channel', 'shield', 'arc', 'boom', 'marker', 'badge']


def render_frame(i):
    t = i / FPS; view = View(i)
    im = view.base(); buf = bytearray(im.tobytes('raw', 'BGRX'))
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W_OUT, H_OUT, W_OUT * 4)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    act = [e for e in EV if e['t0'] - 0.05 <= t <= e['t1'] + 0.05]
    draw_borders(ctx, view)
    for L in LAYER:
        for e in act:
            if e['type'] == L: MAPDRAW[L](ctx, view, t, e)
    ctx.set_source_surface(VIG, 0, 0); ctx.paint()
    for e in act:
        if e['type'] == 'panel': draw_panel(ctx, t, e)
    for e in act:
        if e['type'] == 'card': draw_card(ctx, t, e)
    draw_hud(ctx, t); draw_brand(ctx, t)
    draw_cards_full(ctx, t)
    draw_subtitle(ctx, t)
    fa = 1 - min(smooth(t / 1.2), smooth((TOTAL - t) / 1.6))
    if fa > 0.001: ctx.set_source_rgba(0, 0, 0, fa); ctx.paint()
    surf.flush(); return surf, buf


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        for tt in [float(x) for x in sys.argv[2].split(',')]:
            s, b = render_frame(min(N - 1, int(tt * FPS))); s.write_to_png(f'{V}/prev/p_{tt:07.2f}.png')
        sys.exit(0)
    st = int(sys.argv[1]) if len(sys.argv) > 1 else 0; en = int(sys.argv[2]) if len(sys.argv) > 2 else N
    out = sys.argv[3] if len(sys.argv) > 3 else f'{V}/video_noaudio.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W_OUT}x{H_OUT}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'faster', '-crf', '19', '-pix_fmt', 'yuv420p', '-g', '48', out], stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(st, en):
        s, b = render_frame(i); ff.stdin.write(b)
        if (i - st) % 480 == 0: print(f'frame {i}/{en} {time.time() - t0:.0f}s', flush=True)
    ff.stdin.close(); ff.wait(); print('done', round(time.time() - t0))
