import sys, os, json, math, pickle, time, subprocess, re
import numpy as np, cairo
from PIL import Image
from datetime import date

V = os.path.abspath(os.environ.get("V3_ROOT", "projects/hormuz_korea_legacy"))
P = json.load(open(f'{V}/plan.json'))
FPS = 24; W_OUT, H_OUT = 854, 480
TOTAL = P['total']; N = int(TOTAL * FPS)
SENT = {x['sid']: x for x in P['sentences']}; ORDER = [x['sid'] for x in P['sentences']]
SC0 = P['scene_start']; SCN = list(SC0)


def S(sid, off=0.0): return SENT[sid]['t0'] + off
def E(sid, off=0.0): return SENT[sid]['t1'] + off
def SC(s): return SC0[s]
def SC_END(s):
    i = SCN.index(s); return SC0[SCN[i + 1]] - 0.35 if i + 1 < len(SCN) else TOTAL
def at_word(sid, word):
    x = SENT[sid]; i = x['text'].find(word); return x['t0'] + max(0, i) / len(x['text']) * x['dur']


def ym(lat): return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
def ymv(lat): return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.clip(lat, -85, 85)) / 2)))
def clamp01(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def smooth(x): x = clamp01(x); return x * x * (3 - 2 * x)
def ease_io(x): x = clamp01(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_back(x): x = clamp01(x); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def window(t, t0, t1, fin=0.5, fout=0.5):
    if t < t0 or t > t1: return 0.0
    return min(smooth((t - t0) / fin) if fin > 0 else 1, smooth((t1 - t) / fout) if fout > 0 else 1)
def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


C = {'ru': hexc('#ff5566'), 'us': hexc('#5aa9ff'), 'gold': hexc('#e8b860'), 'teal': hexc('#5cc8da'), 'green': hexc('#8fd08a'),
     'muted': hexc('#a9b0bd'), 'amber': hexc('#ffb347'), 'white': (1, 1, 1), 'kr': hexc('#e8b860'), 'water': hexc('#7fc4ff')}

# ------------------------------------------------------------------ fonts (agents_reviewer reportage stack)
FONT = {'sans': ('IBM Plex Sans KR', 0), 'sansm': ('IBM Plex Sans KR Medium', 0), 'sansb': ('IBM Plex Sans KR SemiBold', 0),
        'sansbb': ('IBM Plex Sans KR', 1), 'disp': ('GmarketSansBold', 0), 'dispm': ('GmarketSansMedium', 0),
        'mono': ('IBM Plex Mono SemiBold', 0), 'monom': ('IBM Plex Mono Medium', 0), 'serif': ('Noto Serif CJK KR', 0), 'serifb': ('Noto Serif CJK KR', 1)}


def font(ctx, name, size):
    fam, b = FONT[name]
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if b else cairo.FONT_WEIGHT_NORMAL); ctx.set_font_size(size)


HANGUL = re.compile('[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]')


def mixed_runs(s, name):
    """IBM Plex Mono has no Hangul: split into runs, Hangul runs fall back to IBM Plex Sans KR."""
    fb = 'sans' if name == 'monom' else 'sansm'; runs = []
    for ch in s:
        f = fb if HANGUL.match(ch) else name
        if ch == ' ' and runs: f = runs[-1][1]
        if runs and runs[-1][1] == f: runs[-1][0] += ch
        else: runs.append([ch, f])
    return runs


def text(ctx, s, x, y, size, name='sansm', col=(1, 1, 1), a=1.0, halo=3.0, anchor='l', spacing=0.0, halo_a=0.8):
    if a <= 0.01 or not s: return 0
    if name in ('mono', 'monom') and HANGUL.search(s):
        runs = mixed_runs(s, name); w = sum(tw(ctx, r, size, f) for r, f in runs)
        if anchor == 'c': x -= w / 2
        elif anchor == 'r': x -= w
        for r, f in runs: x += text(ctx, r, x, y, size, f, col, a, halo, 'l', 0.0, halo_a)
        return w
    font(ctx, name, size)
    disp = name in ('disp', 'dispm') and ' ' in s
    if disp and not spacing: spacing = 0.0001
    w = tw(ctx, s, size, name) + spacing * max(0, len(s) - 1)
    if anchor == 'c': x -= w / 2
    elif anchor == 'r': x -= w
    font(ctx, name, size); ctx.new_path()
    if spacing:
        xx = x
        for ch in s:
            if ch == ' ' and name in ('disp', 'dispm'): xx += size * 0.3 + spacing; continue
            ctx.move_to(xx, y); ctx.text_path(ch); xx += ctx.text_extents(ch).x_advance + spacing
    else:
        ctx.move_to(x, y); ctx.text_path(s)
    if halo > 0:
        ctx.set_source_rgba(0.02, 0.03, 0.05, halo_a * a); ctx.set_line_width(halo); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgba(*col[:3], a); ctx.fill(); return w


def tw(ctx, s, size, name):
    if name in ('mono', 'monom') and HANGUL.search(s): return sum(tw(ctx, r, size, f) for r, f in mixed_runs(s, name))
    font(ctx, name, size)
    if name in ('disp', 'dispm') and ' ' in s: return sum(size * 0.3 if ch == ' ' else ctx.text_extents(ch).x_advance for ch in s)
    return ctx.text_extents(s).x_advance


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()


def wrap(ctx, s, maxw, size, name):
    font(ctx, name, size); words = s.split(' '); lines = []; cur = ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if ctx.text_extents(t).x_advance > maxw and cur: lines.append(cur); cur = w_
        else: cur = t
    if cur: lines.append(cur)
    return lines


# ------------------------------------------------------------------ assets
TIERS = pickle.load(open(f'{V}/assets/tiers.pkl', 'rb'))
BASE = {(n, lv): Image.open(f'{V}/assets/base_{n}_{lv}.png').convert('RGB') for n, T in TIERS.items() for lv in T['levels']}
GEO = pickle.load(open(f'{V}/assets/geo3.pkl', 'rb'))
REG = json.load(open(f'{V}/assets/rights_registry.json'))


def to_uv(rings):
    out = []
    for r in rings:
        uv = np.stack([r[:, 0], ymv(r[:, 1])], 1).astype(np.float64); out.append((uv, uv.min(0), uv.max(0)))
    return out


BORD = {lod: {k: to_uv(v) for k, v in GEO[lod].items()} for lod in ('coarse', 'fine')}
ADM = {k: [dict(name=a['name'], lx=a['lx'], ly=a['ly'], rings=to_uv(a['rings'])) for a in v] for k, v in GEO['admin1'].items()}
PLC = GEO['places']
PLC_LON = np.array([p['lon'] for p in PLC]); PLC_V = ymv(np.array([p['lat'] for p in PLC])); PLC_RANK = np.array([p['rank'] for p in PLC])
PLC_POP = np.array([p['pop'] for p in PLC]); PLC_CAP = np.array([bool(p['cap']) for p in PLC])
KO = {'KP': '북한', 'KR': '대한민국', 'IR': '이란', 'SA': '사우디아라비아', 'AE': '아랍에미리트', 'CN': '중국', 'IN': '인도', 'PK': '파키스탄',
      'OM': '오만', 'QA': '카타르', 'KW': '쿠웨이트', 'BH': '바레인', 'IQ': '이라크', 'YE': '예멘', 'JP': '일본', 'TW': '대만', 'RU': '러시아',
      'AF': '아프가니스탄', 'MM': '미얀마', 'TH': '태국', 'VN': '베트남', 'MY': '말레이시아', 'ID': '인도네시아', 'PH': '필리핀', 'LK': '스리랑카',
      'BD': '방글라데시', 'EG': '이집트', 'SO': '소말리아', 'ET': '에티오피아', 'TR': '튀르키예', 'SY': '시리아', 'JO': '요르단', 'IL': '이스라엘',
      'MN': '몽골', 'KZ': '카자흐스탄', 'TM': '투르크메니스탄', 'UZ': '우즈베키스탄', 'NP': '네팔', 'SD': '수단', 'LA': '라오스', 'KH': '캄보디아'}
SEAS = [('페르시아만', 51.2, 27.6, 0, 34), ('오만만', 58.9, 24.4, 0, 30), ('아라비아해', 63.5, 15.5, 16, 140), ('인도양', 79, -3, 40, 140),
        ('벵골만', 88.5, 14.5, 40, 140), ('남중국해', 113.5, 14.5, 40, 140), ('동해', 130.9, 38.3, 2, 40), ('서해', 124.0, 36.0, 2, 40),
        ('홍해', 38.8, 20.0, 30, 140), ('아덴만', 48.5, 12.4, 16, 140)]


def surf_from_pil(im):
    im = im.convert('RGBA'); a = np.asarray(im).astype(np.float32); al = a[..., 3:4] / 255; rgb = a[..., :3] * al
    bgra = np.ascontiguousarray(np.dstack([rgb[..., 2], rgb[..., 1], rgb[..., 0], a[..., 3]]).astype(np.uint8))
    h, w = bgra.shape[:2]; buf = bytearray(bgra.tobytes())
    return (cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, w * 4), buf)


PIL_IMG = {p: Image.open(f'{V}/assets/portraits/{p}.png').convert('RGBA') for p in ('lee_jae_myung', 'roh_moo_hyun', 'trump', 'khamenei')}
PIL_IMG['navcent'] = Image.open(f'{V}/assets/emblems/navcent.png').convert('RGBA')
for c in ('kr', 'us', 'ir', 'cn', 'in', 'de', 'gb', 'jp', 'au', 'fr', 'it', 'nl', 'ca'):
    PIL_IMG[c + '43'] = Image.open(f'{V}/assets/flags/{c}_4x3.png').convert('RGBA')
    PIL_IMG[c + '11'] = Image.open(f'{V}/assets/flags/{c}_1x1.png').convert('RGBA')
_SC = {}


def scaled(key, w):
    w = max(8, int(round(w / 3.0) * 3)); k = (key, w)
    if k not in _SC:
        pil = PIL_IMG[key]; _SC[k] = surf_from_pil(pil.resize((w, max(1, int(pil.height * w / pil.width))), Image.LANCZOS))
    return _SC[k][0]


# ------------------------------------------------------------------ media (licensed photos / video / cutouts)
MEDIA = json.load(open(f'{V}/media/media_registry.json'))
PIL_IMG['photo_hormuz'] = Image.open(f'{V}/media/hormuz_transit_720.jpg').convert('RGBA')
PIL_IMG['cut_p8'] = Image.open(f'{V}/media/p8_cut.png').convert('RGBA')
CLIP = {'strikes': np.load(f'{V}/media/strikes_480.npy', mmap_mode='r'), 'niovi': np.load(f'{V}/media/niovi_480.npy', mmap_mode='r')}
PIL_IMG['photo_rok_iraq'] = Image.open(f'{V}/media/rok_iraq_720.jpg').convert('RGBA')


# ------------------------------------------------------------------ direction layer
CAM, EV = [], []


def cam(t, lon, lat, w, dur=3.0, mode='move'): CAM.append((t, lon, ym(lat), w, dur, mode))
def ev(typ, t0, t1, **kw): d = dict(type=typ, t0=t0, t1=t1); d.update(kw); EV.append(d); return d
def dip(t): ev('dip', t - 0.5, t + 0.5); cam(t, *CUT_TARGET.pop(0), dur=0, mode='cut')


PL = {'hormuz': (56.35, 26.55), 'seoul': (126.98, 37.57), 'ulsan': (129.31, 35.54), 'busan': (129.04, 35.10), 'kharg': (50.32, 29.24),
      'aden': (46.8, 12.4), 'embassy': (126.9775, 37.5725), 'erbil': (44.01, 36.19)}
ROUTE = [(56.2, 26.45), (57.8, 24.9), (60.5, 22.6), (65.0, 18.2), (72.0, 11.0), (79.5, 5.4), (88.0, 5.6), (95.2, 5.9), (98.8, 4.6),
         (101.5, 2.6), (104.1, 1.25), (106.5, 3.8), (110.0, 9.5), (115.0, 15.5), (120.2, 20.2), (122.4, 23.8), (123.8, 28.2), (126.2, 32.2),
         (128.6, 34.5), (129.35, 35.45)]
CHEONG = [(129.04, 35.05), (126.4, 32.3), (123.9, 28.3), (122.5, 23.9), (120.3, 20.3), (115.0, 15.5), (110.0, 9.5), (106.5, 3.8), (104.1, 1.25),
          (101.5, 2.6), (98.8, 4.6), (95.2, 5.9), (88.0, 5.6), (79.5, 5.4), (70.0, 9.0), (60.0, 12.0), (52.5, 12.6), (47.2, 12.3)]

# shots ----------------------------------------------------------------
title = [c for c in P['cards'] if c['kind'] == 'title'][0]; endc = [c for c in P['cards'] if c['kind'] == 'end'][0]
CUT_TARGET = [(57.6, 25.3, 24), (88.5, 21.5, 92), (127.0, 37.45, 3.4), (88.5, 19.5, 90)]
cam(0, 127.35, 36.35, 6.4, 0, 'cut')
# open
ev('marker', S('open_0', 0.2), SC_END('open'), lon=PL['seoul'][0], lat=PL['seoul'][1], label='서울', sub='대통령실 기자회견', side='right', hl=True)
ev('badge', S('open_0', 0.6), SC_END('open'), lon=125.05, lat=37.25, kind='person', pid='lee_jae_myung', flag='kr', R=34, label='이재명', role='대한민국 대통령', accent='gold')
ev('card', S('open_1', 0.1), E('open_2', 0.6), tag='기자회견 · 9월 18일', lines=['전쟁에 개입하는 파병은 없다', '한국 선박·국민 보호는 최소한으로 계속'], accent='gold')
# title (camera cut hidden under title card)
ev('dip', title['t0'] + 2.4, title['t0'] + 3.4, under=True); cam(title['t0'] + 2.9, *CUT_TARGET.pop(0), dur=0, mode='cut')
# route
ev('marker', S('route_0', 0.1), SC_END('route'), lon=PL['hormuz'][0], lat=PL['hormuz'][1], label='호르무즈 해협', sub='가장 좁은 곳 약 39km', side='right', hl=True)
cam(S('route_1', -0.6), 88.5, 19.5, 90, 3.4)
ev('route', S('route_1', 0.6), SC_END('route'), pts=ROUTE, grow=E('route_3', -0.4) - S('route_1', 0.6), col='gold', ship=True)
ev('card', S('route_1', 0.5), E('route_2', 0.7), tag='2025년 수입 중 호르무즈 경유 비중', bigs=[('61%', '원유'), ('54%', '나프타')], accent='gold', src='로이터 · 대통령실 인용 수치')
ev('badge', E('route_3', -0.5), SC_END('route'), lon=127.0, lat=31.3, kind='flag', flag='kr', R=18, label='울산', accent='gold')
# war
cam(S('war_0', -1.2), 54.8, 27.0, 14.0, 3.4)
ev('country', S('war_0', 0.1), SC_END('war'), codes=['IR'], col='ru', a=0.07)
ev('boom', S('war_0', 1.2), S('war_0', 3.4), lon=PL['kharg'][0], lat=PL['kharg'][1])
ev('marker', S('war_0', 1.2), E('war_0', 0.5), lon=PL['kharg'][0], lat=PL['kharg'][1], label='하르그섬', sub='이란 원유 수출 거점', side='left', icon='boom')
ev('badge', S('war_1', 0.2), E('war_1', 0.8), lon=57.6, lat=29.35, kind='person', pid='khamenei', flag='ir', R=32, label='알리 하메네이', role='이란 최고지도자 (1939–2026)', accent='ru')
ev('marker', S('war_2', 0.0), SC_END('war'), lon=PL['hormuz'][0], lat=PL['hormuz'][1], label='호르무즈 해협', sub='3월 2일 IRGC 봉쇄 선언', side='right', hl=True)
ev('barrier', S('war_2', 0.3), SC_END('war'), p0=(56.28, 27.05), p1=(56.42, 26.28))
ev('route', S('war_3', 0.2), SC_END('war'), pts=[(56.9, 25.9), (58.2, 25.0), (60.4, 24.3)], grow=1.8, col='teal', ship=False, dashed=True, label='허가받은 배만 통과')
ev('badge', S('war_3', 1.6), SC_END('war'), lon=59.4, lat=23.35, kind='flag', flag='cn', R=17, label='중국', accent='teal')
ev('badge', S('war_3', 2.0), SC_END('war'), lon=60.9, lat=23.35, kind='flag', flag='in', R=17, label='인도', accent='teal')
# ask panels
ev('panel', SC('ask') - 0.2, E('ask_3', 0.5), kind='refusal')
ev('panel', S('ask_4', -0.3), SC_END('ask'), kind='statement')
# timeline panel
ev('panel', SC('timeline') - 0.2, SC_END('timeline'), kind='timeline')
# cost
cam(SC('cost') - 1.0, 52.4, 27.2, 13.5, 3.0)
ev('ships', S('cost_0', 0.2), SC_END('cost'))
ev('card', S('cost_0', 0.4), SC_END('cost') - 0.2, tag='국제해사기구 · 6월 11일 기준', lines=['선박 공격 46건', '선원 사망 14명', '발 묶인 배 약 1,000척 · 선원 2만 명'], accent='ru')
# review
dip(SC('review') - 0.55)
ev('route', S('review_0', 0.3), SC_END('review'), pts=CHEONG, grow=4.5, col='teal', ship=True, label='')
ev('marker', S('review_0', 4.6), SC_END('review'), lon=PL['aden'][0], lat=PL['aden'][1], label='아덴만', sub='청해부대 2009년~', side='bottom', hl=True)
ev('badge', S('review_0', 0.3), SC_END('review'), lon=125.6, lat=22.3, kind='flag', flag='kr', R=18, label='부산에서 출항', accent='gold')
ev('card', S('review_1', 0.0), E('review_2', 0.6), tag='거론된 선택지', lines=['해상초계기', '군수지원함'], accent='teal', src='JTBC·MBC 보도 · 대통령실 “결정된 것 없다”')
# past panel
ev('panel', SC('past') - 0.2, SC_END('past'), kind='precedent')
# debate
dip(SC('debate') - 0.55)
ev('marker', S('debate_1', 0.2), SC_END('debate'), lon=PL['embassy'][0], lat=PL['embassy'][1], label='주한 미국대사관', sub='9월 8일 파병 반대 집회', side='right', hl=True)
ev('article', S('debate_0', 0.3), E('debate_0', 1.0), pub='The Korea Herald', date='2026. 09. 07', headline='정부, 전투 격화·반대 여론 확산에 호르무즈 파병 계획 재조정', hl='재조정', sub='국방부 “항행의 자유 회복에 실질적으로 기여할 방안을 국제사회와 협의 중”', note='헤드라인 번역 · 원문 영어')
ev('panel', S('debate_2', -0.3), SC_END('debate'), kind='versus')
# decision
cam(SC('decision') - 0.8, 127.35, 36.6, 6.4, 3.2)
ev('marker', SC('decision'), SC_END('decision'), lon=PL['seoul'][0], lat=PL['seoul'][1], label='서울', sub='9월 18일 발표', side='right', hl=True)
ev('badge', S('decision_0', 0.4), SC_END('decision'), lon=125.05, lat=37.25, kind='person', pid='lee_jae_myung', flag='kr', R=34, label='이재명', role='대한민국 대통령', accent='gold')
ev('card', S('decision_0', 0.8), SC_END('decision') - 0.1, tag='이재명 대통령 · 발언 요지', lines=['“전쟁에 관여하거나 들어가는', '파병은 없다”'], accent='gold', quote=True)
# now
dip(SC('now') - 0.55)
ev('route', SC('now') - 0.2, TOTAL, pts=ROUTE, grow=0.01, col='gold', ship=False, glow_only=True)
ev('tanker_loop', SC('now'), TOTAL, pts=ROUTE)
ev('badge', S('now_0', 0.2), TOTAL, lon=61.8, lat=20.2, kind='emblem', img='navcent', R=28, label='미 해군 중부사령부', role='호위 작전', accent='us')
ev('card', S('now_0', 0.5), E('now_1', 0.4), tag='미 중부사령부 발표', bigs=[('10억 배럴', '호위 작전으로 반출된 원유')], accent='us')
ev('card', S('now_2', 0.1), E('now_2', 0.8), tag='2025년 기준', bigs=[('61%', '원유 수입의 호르무즈 경유 비중')], accent='gold')
ev('marker', SC('now'), TOTAL, lon=PL['hormuz'][0], lat=PL['hormuz'][1], label='호르무즈 해협', sub='', side='right', hl=True)
cam(S('now_3', -0.5), 90, 20, 96, 9.0)


# media events (photo / video / cutout / article clipping)
ev('clip', S('war_2', 0.2), S('war_2', 0.2) + 5.0, clip='niovi', x=40, y=150, w=300, mid='niovi',
   caption='이란 혁명수비대 고속정의 유조선 나포', credit='자료 영상 · 2023. 05. 03 · U.S. Navy · Public domain')
ev('photo', S('past_1', 0.6), E('past_2', 0.2), img='photo_rok_iraq', x=292, y=138, w=280, mid='rok_iraq',
   caption='이라크에 파병된 한국군 장병', credit='자료사진 · 2003 · U.S. Government · Public domain')
ev('article', S('review_0', 0.3), E('review_0', 0.9), pub='Reuters', date='2026. 09. 04', headline='한국, 호르무즈 군사 선택지 검토… 대통령실 “결정된 것은 없다”', hl='결정된 것은 없다', sub='JTBC·MBC의 ‘연내 파병 준비’ 보도 이후 나온 대통령실 설명', note='헤드라인 번역 · 원문 영어')

ev('photo', S('now_0', 1.0), E('now_1', 0.4), img='photo_hormuz', x=560, y=196, w=262, mid='hormuz_transit',
   caption='호르무즈 해협 통과 중 경계 근무를 서는 미 해군', credit='자료사진 · 2023. 05 · U.S. Navy · Public domain')
ev('clip', S('timeline_4', 0.3), S('timeline_4', 0.3) + 5.0, clip='strikes', x=207, y=112, w=440, mid='strikes',
   caption='미 중부사령부 공개 영상 · 이란 군사 목표 타격', credit='2026. 07. 07 · U.S. Central Command · Public domain')
ev('cutout', S('review_1', 0.1), E('review_2', 0.4), img='cut_p8', lon=112.0, lat=12.5, w=150, mid='p8',
   label='해상초계기 P-8A', sub='자료사진 · U.S. Navy')


# ------------------------------------------------------------------ camera
def build_camera():
    cams = sorted(CAM, key=lambda c: c[0]); out = np.zeros((N, 3)); cur = np.array(cams[0][1:4], float); frm = cur.copy(); k = 0; act = None
    for i in range(N):
        t = i / FPS
        while k < len(cams) and cams[k][0] <= t:
            act = cams[k]; k += 1
            frm = out[i - 1].copy() if i > 0 and act[5] != 'cut' else np.array(act[1:4], float)
        if act is None: v = cur.copy(); da = t
        else:
            t0, lo, vv, ww, dur, mode = act
            e = ease_io((t - t0) / dur) if dur > 0 else 1.0
            v = np.array([frm[0] + (lo - frm[0]) * e, frm[1] + (vv - frm[1]) * e, math.exp(math.log(frm[2]) + (math.log(ww) - math.log(frm[2])) * e)])
            da = t - (t0 + dur)
        if da > 0: v[2] *= 1 - 0.03 * (1 - math.exp(-da / 9.0))
        out[i] = v
    return out


CAMS = build_camera()
TW = TIERS['W']


class View:
    def __init__(s, i):
        lon, v, w = CAMS[i]
        umin, umax = TW['lon0'], TW['lon1']; vmin, vmax = ym(TW['lat0']), ym(TW['lat1'])
        w = min(w, umax - umin - 0.01, (vmax - vmin - 0.01) * W_OUT / H_OUT)
        s.w = w; s.h = w * H_OUT / W_OUT; s.s = W_OUT / w
        s.u0 = min(max(lon - w / 2, umin), umax - w); s.v1 = min(max(v + s.h / 2, vmin + s.h), vmax)

    def xy(s, lon, lat): return (lon - s.u0) * s.s, (s.v1 - ym(lat)) * s.s
    def uvs(s, uv): return np.column_stack([(uv[:, 0] - s.u0) * s.s, (s.v1 - uv[:, 1]) * s.s])
    def visible(s, mn, mx): return not (mx[0] < s.u0 or mn[0] > s.u0 + s.w or mx[1] < s.v1 - s.h or mn[1] > s.v1)

    def inside(s, T, m=0.05):
        return s.u0 >= T['lon0'] + m and s.u0 + s.w <= T['lon1'] - m and s.v1 <= ym(T['lat1']) - m and s.v1 - s.h >= ym(T['lat0']) + m

    def base(s):
        need = W_OUT / s.w; im = s._tier('W', need)
        for n in ('G', 'K'):
            if s.inside(TIERS[n]):
                a = smooth((need - 26) / 18)
                if a > 0.01: im = Image.blend(im, s._tier(n, need), a)
        return im

    def _tier(s, n, need):
        T = TIERS[n]; lvs = sorted(T['levels']); lv = next((l for l in lvs if l >= need * 0.95), lvs[-1]); im = BASE[(n, lv)]
        x0 = (s.u0 - T['lon0']) * lv; y0 = (ym(T['lat1']) - s.v1) * lv
        return im.resize((W_OUT, H_OUT), Image.BILINEAR, box=(max(0.0, x0), max(0.0, y0), min(x0 + s.w * lv, im.width), min(y0 + s.h * lv, im.height)))


# ------------------------------------------------------------------ map layers
def path_rings(ctx, view, rings, min_px=1.0):
    n = 0
    for uv, mn, mx in rings:
        if not view.visible(mn, mx) or (mx - mn).max() * view.s < min_px: continue
        S_ = view.uvs(uv); ctx.move_to(*S_[0])
        for x, y in S_[1:]: ctx.line_to(x, y)
        ctx.close_path(); n += 1
    return n


def draw_borders(ctx, view):
    lod = 'fine' if view.w < 22 else 'coarse'; ctx.new_path()
    for k, rings in BORD[lod].items(): path_rings(ctx, view, rings)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_source_rgba(0.82, 0.86, 0.92, 0.36 if view.w < 40 else 0.26); ctx.set_line_width(0.75); ctx.stroke()
    a = 0.3 * smooth((24 - view.w) / 10)
    if a > 0.01:
        ctx.set_dash([2.5, 2.5])
        for k, lst in ADM.items():
            ctx.new_path()
            for ad in lst: path_rings(ctx, view, ad['rings'], 2)
            ctx.set_source_rgba(0.8, 0.84, 0.9, a); ctx.set_line_width(0.55); ctx.stroke()
        ctx.set_dash([])


RESERVED = []


def draw_labels(ctx, view, t, la):
    placed = list(RESERVED)

    def free(x, y, w, h):
        for (a, b, c, d) in placed:
            if x < c and x + w > a and y < d and y + h > b: return False
        return True
    # seas
    for nm, lo, la_, wmin, wmax in SEAS:
        if not (wmin <= view.w <= wmax): continue
        x, y = view.xy(lo, la_)
        if -40 < x < W_OUT + 40 and 0 < y < H_OUT:
            text(ctx, nm, x, y, 11 if view.w > 30 else 12, 'serif', hexc('#9cc8e6'), 0.62 * la, 0, 'c', spacing=2.2)
    # countries
    thr = 2 if view.w > 60 else 4 if view.w > 30 else 6 if view.w > 12 else 9
    for k, m in GEO['meta'].items():
        if m['lx'] is None or (m.get('rank') or 9) > thr: continue
        if view.w < 12 and k in ('KR',): continue
        x, y = view.xy(m['lx'], m['ly'])
        if not (30 < x < W_OUT - 30 and 60 < y < H_OUT - 70): continue
        nm = KO.get(k, m['ko']); size = 12 if view.w > 30 else 13
        w = tw(ctx, nm, size, 'sansm') + 1.8 * len(nm)
        if not free(x - w / 2, y - 12, w, 16): continue
        text(ctx, nm, x, y, size, 'sansm', (0.9, 0.92, 0.96), 0.55 * la, 2.2, 'c', spacing=1.8); placed.append((x - w / 2, y - 12, x + w / 2, y + 4))
    # admin-1 names (close zoom)
    if view.w < 8.5:
        for k in ('KR', 'KP'):
            for ad in ADM.get(k, []):
                if ad['lx'] is None: continue
                x, y = view.xy(ad['lx'], ad['ly'])
                if 20 < x < W_OUT - 20 and 60 < y < H_OUT - 70:
                    w = tw(ctx, ad['name'], 9.5, 'sans')
                    if free(x - w / 2, y - 9, w, 12):
                        text(ctx, ad['name'], x, y, 9.5, 'sans', (0.78, 0.82, 0.88), 0.42 * la, 1.8, 'c'); placed.append((x - w / 2, y - 9, x + w / 2, y + 3))
    # cities
    rk = 1 if view.w > 60 else 2 if view.w > 25 else 4 if view.w > 12 else 6 if view.w > 5 else 8
    xs = (PLC_LON - view.u0) * view.s; ys = (view.v1 - PLC_V) * view.s
    m = (xs > 12) & (xs < W_OUT - 12) & (ys > 58) & (ys < H_OUT - 72) & ((PLC_RANK <= rk) | (PLC_CAP & (PLC_RANK <= rk + 2)))
    idx = np.where(m)[0]; idx = idx[np.lexsort((-PLC_POP[idx], PLC_RANK[idx]))][:40]; n = 0
    for i in idx:
        x, y = xs[i], ys[i]; nm = PLC[i]['ko']; cap = PLC_CAP[i]; size = 11.5 if cap else 10.5
        w = tw(ctx, nm, size, 'sansb' if cap else 'sansm')
        if not free(x - 3, y - 8, w + 10, 13): continue
        ctx.arc(x, y, 2.4 if cap else 1.9, 0, 2 * math.pi); ctx.set_source_rgba(0.95, 0.96, 0.98, 0.9 * la); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.6 * la); ctx.set_line_width(0.8); ctx.stroke()
        text(ctx, nm, x + 5, y + 4, size, 'sansb' if cap else 'sansm', (0.93, 0.94, 0.97), 0.82 * la, 2.6, 'l'); placed.append((x - 3, y - 8, x + w + 7, y + 5)); n += 1
        if n >= 18: break


def draw_country(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.8, 0.6); col = C[e['col']]
    if a <= 0.01: return
    lod = 'fine' if view.w < 22 else 'coarse'
    for code in e['codes']:
        ctx.new_path()
        if not path_rings(ctx, view, BORD[lod].get(code, [])): continue
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); ctx.set_source_rgba(*col, e['a'] * a); ctx.fill_preserve()
        for wd, al in ((6, 0.07), (2.6, 0.2), (1.1, 0.85)): ctx.set_source_rgba(*col, al * a); ctx.set_line_width(wd); ctx.stroke_preserve()
        ctx.new_path()


def catmull(pts, n=10):
    P_ = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = map(np.array, P_[i - 1:i + 3])
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(np.array(P_[-2])); return np.array(out)


def route_uv(pts):
    uv = [(lo, ym(la)) for lo, la in pts]; return catmull(uv, 12)


def glow_line(ctx, S_, col, a, w, dash=None):
    ctx.new_path(); ctx.move_to(*S_[0])
    for x, y in S_[1:]: ctx.line_to(x, y)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash: ctx.set_dash(dash)
    for wd, al in ((w * 4.5, 0.08), (w * 2.2, 0.22), (w, 0.95)): ctx.set_source_rgba(*col, al * a); ctx.set_line_width(wd); ctx.stroke_preserve()
    ctx.new_path(); ctx.set_dash([])


def tanker(ctx, x, y, ang, a, sc=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(sc, sc)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 15); g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.45 * a); g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
    ctx.set_source(g); ctx.arc(0, 0, 15, 0, 2 * math.pi); ctx.fill()
    ctx.new_path(); ctx.move_to(9, 0); ctx.line_to(5, -3); ctx.line_to(-8, -3); ctx.line_to(-8, 3); ctx.line_to(5, 3); ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, a); ctx.fill_preserve(); ctx.set_source_rgba(0, 0, 0, 0.5 * a); ctx.set_line_width(0.6); ctx.stroke()
    ctx.rectangle(-7, -2, 3, 4); ctx.set_source_rgba(0.2, 0.25, 0.3, a); ctx.fill(); ctx.restore()


def draw_route(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.35, 0.6)
    if a <= 0.01: return
    if 'uv' not in e: e['uv'] = route_uv(e['pts'])
    S_ = view.uvs(e['uv']); prog = ease_io((t - e['t0']) / e['grow']) if e['grow'] > 0.05 else 1
    n = max(2, int(len(S_) * prog)); sub = S_[:n]; col = C[e['col']]
    glow_line(ctx, sub, col, a * (0.75 if e.get('glow_only') else 1), 1.9, dash=[5, 4] if e.get('dashed') else None)
    if e.get('ship') and len(sub) > 1:
        (x0, y0), (x1, y1) = sub[-2], sub[-1]; tanker(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a)
    if e.get('dashed') and prog >= 0.98:
        (x0, y0), (x1, y1) = sub[-2], sub[-1]; ang = math.atan2(y1 - y0, x1 - x0)
        ctx.new_path(); ctx.move_to(x1 + math.cos(ang) * 3, y1 + math.sin(ang) * 3)
        for s_ in (2.5, -2.5): ctx.line_to(x1 - math.cos(ang + s_ / 6) * 9, y1 - math.sin(ang + s_ / 6) * 9)
        ctx.close_path(); ctx.set_source_rgba(*col, a); ctx.fill()
    if e.get('label') and prog >= 0.99:
        x, y = S_[len(S_) // 2]; text(ctx, e['label'], x, y - 11, 11.5, 'sansb', col, a * smooth((t - e['t0'] - e['grow']) / 0.4), 3, 'c')


def draw_tanker_loop(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.6, 0.6)
    if 'uv' not in e: e['uv'] = route_uv(e['pts'])
    S_ = view.uvs(e['uv'])
    for k in range(3):
        f = ((t - e['t0']) / 26.0 + k / 3) % 1.0; i = int(f * (len(S_) - 2))
        (x0, y0), (x1, y1) = S_[i], S_[i + 1]; tanker(ctx, x1, y1, math.atan2(y1 - y0, x1 - x0), a * 0.95, 0.85)


def draw_barrier(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.4, 0.5); k = ease_out((t - e['t0']) / 0.8)
    x0, y0 = view.xy(*e['p0']); x1, y1 = view.xy(*e['p1']); xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    glow_line(ctx, np.array([[x0, y0], [xe, ye]]), C['ru'], a, 3.2)
    if k > 0.95: text(ctx, '봉쇄', (x0 + x1) / 2 - 12, (y0 + y1) / 2 + 4, 12.5, 'sansb', C['ru'], a, 3, 'r')


SHIPS = None


def draw_ships(ctx, view, t, e):
    global SHIPS
    a = window(t, e['t0'], e['t1'], 0.8, 0.6)
    if SHIPS is None:
        from shapely.geometry import Point
        from shapely.prepared import prep
        land = [prep(__import__('shapely.geometry', fromlist=['Polygon']).Polygon(r)) for k, rs in GEO['fine'].items() for r in rs if len(r) > 3]
        rng = np.random.default_rng(4); pts = []
        while len(pts) < 150:
            lo, la = rng.uniform(48.3, 56.2), rng.uniform(24.2, 29.9)
            p = Point(lo, la)
            if not any(L.contains(p) for L in land): pts.append((lo, la, rng.uniform(0, 1)))
        SHIPS = pts
    for lo, la, ph in SHIPS:
        if t < e['t0'] + ph * 1.6: continue
        x, y = view.xy(lo, la); tw_ = 0.6 + 0.4 * math.sin(t * 2 + ph * 9)
        ctx.arc(x, y, 1.7, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.82, 0.5, 0.85 * a * tw_); ctx.fill()


def icon(ctx, kind, x, y, col, a):
    if kind == 'boom':
        ctx.new_path()
        for k in range(10):
            ang = k * math.pi / 5 + 0.2; r1, r2 = (9, 4) if k % 2 == 0 else (6, 3)
            ctx.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1); ctx.line_to(x + math.cos(ang + math.pi / 10) * r2, y + math.sin(ang + math.pi / 10) * r2)
        ctx.close_path(); ctx.set_source_rgba(*C['amber'], a); ctx.fill()
    else:
        ctx.arc(x, y, 3.3, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, a); ctx.fill_preserve(); ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.set_line_width(1); ctx.stroke()


def draw_marker(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.35, 0.5)
    if a <= 0.01: return
    x, y = view.xy(e['lon'], e['lat']); lt = t - e['t0']
    if x < -80 or x > W_OUT + 80 or y < -40 or y > H_OUT + 40: return
    col = C['gold'] if e.get('hl') else C['white']
    for k in range(2):
        f = ((lt * 0.5) + k / 2) % 1.0; r = 4 + 20 * ease_out(f)
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(*col, 0.5 * (1 - f) * a); ctx.set_line_width(1.3); ctx.stroke()
    icon(ctx, e.get('icon', 'dot'), x, y, col, a * ease_out(lt / 0.3))
    side = e.get('side', 'right'); la = a * smooth((lt - 0.2) / 0.4)
    dx, dy, anc = {'right': (12, 4, 'l'), 'left': (-12, 4, 'r'), 'top': (0, -14, 'c'), 'bottom': (0, 22, 'c')}[side]
    text(ctx, e['label'], x + dx, y + dy, 13, 'sansb', (1, 1, 1), la, 3.2, anc)
    if e.get('sub'): text(ctx, e['sub'], x + dx, y + dy + 15, 10.5, 'sansm', C['gold'], la, 3, anc)
    w = tw(ctx, e['label'], 13, 'sansb') + 20
    RESERVED.append((x - 14 if anc != 'r' else x - w, y - 16, x + w if anc != 'r' else x + 14, y + 26))


def draw_boom(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.05, 0.8); x, y = view.xy(e['lon'], e['lat']); lt = t - e['t0']
    for k in range(3):
        r = 6 + 50 * ease_out((lt - k * 0.12) / 1.2)
        ctx.arc(x, y, max(r, 0.1), 0, 2 * math.pi); ctx.set_source_rgba(*C['amber'], 0.6 * a * (1 - clamp01(lt / 1.6))); ctx.set_line_width(2); ctx.stroke()


# ------------------------------------------------------------------ media drawing
def media_frame(ctx, x, y, w, h, a):
    for d_, al in ((6, 0.10), (3, 0.18)):
        rrect(ctx, x - d_ + 2, y - d_ + 4, w + 2 * d_, h + 2 * d_, 4 + d_); ctx.set_source_rgba(0, 0, 0, al * a); ctx.fill()


def media_caption(ctx, x, y, w, cap, credit, a, tag):
    ctx.rectangle(x, y, w, 38); ctx.set_source_rgba(0.04, 0.05, 0.07, 0.9 * a); ctx.fill()
    text(ctx, cap, x + 10, y + 16, 10.5, 'sansm', (1, 1, 1), a, 0, 'l')
    text(ctx, credit, x + 10, y + 30, 7.8, 'monom', C['muted'], a * 0.95, 0, 'l')


def media_tag(ctx, x, y, s_, a):
    w = tw(ctx, s_, 7.5, 'mono') + 12
    rrect(ctx, x + 8, y + 8, w, 14, 2); ctx.set_source_rgba(0.02, 0.03, 0.05, 0.75 * a); ctx.fill()
    text(ctx, s_, x + 14, y + 18, 7.5, 'mono', C['gold'], a, 0, 'l', spacing=0.8)


def draw_photo(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.5, 0.5)
    if a <= 0.01: return
    lt = t - e['t0']; x, y, w = e['x'], e['y'] + (1 - ease_out(lt / 0.6)) * 12, e['w']; h = w * 0.625
    media_frame(ctx, x, y, w, h + 38, a)
    k = 1.0 + 0.07 * clamp01(lt / (e['t1'] - e['t0']))                     # Ken Burns
    fs = scaled(e['img'], w * k); fw, fh = fs.get_width(), fs.get_height()
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.set_source_surface(fs, x - (fw - w) * 0.35, y - (fh - h) * 0.5); ctx.paint_with_alpha(a); ctx.restore()
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + 37); ctx.set_source_rgba(1, 1, 1, 0.22 * a); ctx.set_line_width(1); ctx.stroke()
    media_tag(ctx, x, y, 'PHOTO', a); media_caption(ctx, x, y + h, w, e['caption'], e['credit'], a, 'PHOTO')


_CLIPSURF = {}


def draw_clip(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.35, 0.45)
    if a <= 0.01: return
    fr = CLIP[e['clip']]; i = min(len(fr) - 1, max(0, int((t - e['t0']) * FPS)))
    x, y, w = e['x'], e['y'], e['w']; h = w * fr.shape[1] / fr.shape[2]
    rgb = np.asarray(fr[i]); img = Image.fromarray(rgb).resize((int(w), int(h)), Image.BILINEAR).convert('RGBA')
    surf, buf = surf_from_pil(img); _CLIPSURF['last'] = buf
    media_frame(ctx, x, y, w, h + 38, a)
    ctx.set_source_surface(surf, x, y); ctx.paint_with_alpha(a)
    ctx.rectangle(x + 0.5, y + 0.5, w - 1, h + 37); ctx.set_source_rgba(1, 1, 1, 0.22 * a); ctx.set_line_width(1); ctx.stroke()
    media_tag(ctx, x, y, 'VIDEO', a); media_caption(ctx, x, y + h, w, e['caption'], e['credit'], a, 'VIDEO')


def draw_article(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.45, 0.45)
    if a <= 0.01: return
    lt = t - e['t0']; w = 300; x = W_OUT - w - 24 + (1 - ease_out(lt / 0.55)) * 30; y = 68
    hl_lines = wrap(ctx, e['headline'], w - 32, 13.5, 'serifb'); sub_lines = wrap(ctx, e['sub'], w - 32, 9.5, 'sans')
    h = 44 + len(hl_lines) * 20 + 6 + len(sub_lines) * 14 + 24
    for d_, al in ((6, 0.12), (3, 0.2)):
        rrect(ctx, x - d_ + 2, y - d_ + 4, w + 2 * d_, h + 2 * d_, 3 + d_); ctx.set_source_rgba(0, 0, 0, al * a); ctx.fill()
    rrect(ctx, x, y, w, h, 3); ctx.set_source_rgba(0.95, 0.935, 0.905, a); ctx.fill()
    ink = (0.1, 0.105, 0.12); grey = (0.38, 0.39, 0.42)
    text(ctx, e['pub'], x + 16, y + 25, 12.5, 'serifb', ink, a, 0, 'l')
    text(ctx, e['date'], x + w - 16, y + 25, 8.5, 'monom', grey, a, 0, 'r')
    ctx.set_source_rgba(*ink, 0.35 * a); ctx.rectangle(x + 16, y + 33, w - 32, 0.8); ctx.fill()
    yy = y + 54; hk = ease_io((lt - 0.8) / 0.7)
    for ln in hl_lines:
        if e.get('hl') and e['hl'] in ln and hk > 0:
            i = ln.index(e['hl']); x0 = x + 16 + tw(ctx, ln[:i], 13.5, 'serifb'); ww = tw(ctx, e['hl'], 13.5, 'serifb')
            ctx.rectangle(x0 - 2, yy - 12, (ww + 4) * hk, 16); ctx.set_source_rgba(1.0, 0.8, 0.3, 0.55 * a); ctx.fill()
        text(ctx, ln, x + 16, yy, 13.5, 'serifb', ink, a, 0, 'l'); yy += 20
    yy += 4
    for ln in sub_lines: text(ctx, ln, x + 16, yy, 9.5, 'sans', grey, a, 0, 'l'); yy += 14
    text(ctx, 'ARTICLE', x + 16, y + h - 11, 7.5, 'mono', grey, a, 0, 'l', spacing=0.8)
    text(ctx, e['note'], x + w - 16, y + h - 11, 7.8, 'sans', grey, a, 0, 'r')


def draw_cutout(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.6, 0.5)
    if a <= 0.01: return
    lt = t - e['t0']; x, y = view.xy(e['lon'], e['lat'])
    x -= (1 - ease_out(lt / 1.2)) * 40; y += math.sin(t * 1.3) * 2.2
    fs = scaled(e['img'], e['w']); fw, fh = fs.get_width(), fs.get_height()
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.04 + 0.015 * math.sin(t * 0.9))
    ctx.set_source_rgba(0, 0, 0, 0.25 * a); ctx.save(); ctx.translate(6, 14); ctx.scale(1, 0.25); ctx.arc(0, 0, fw * 0.36, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.set_source_surface(fs, -fw / 2, -fh / 2); ctx.paint_with_alpha(a); ctx.restore()
    la = a * smooth((lt - 0.5) / 0.4)
    text(ctx, e['label'], x, y + fh / 2 + 16, 12, 'sansb', (1, 1, 1), la, 3, 'c')
    text(ctx, e['sub'], x, y + fh / 2 + 30, 8.5, 'monom', C['muted'], la, 2.4, 'c')
    RESERVED.append((x - fw / 2, y - fh / 2, x + fw / 2, y + fh / 2 + 34))


# ------------------------------------------------------------------ badges
def flag_wave(ctx, key, cx, cy, wdt, a, t):
    fs = scaled(key, wdt); fh, fw = fs.get_height(), fs.get_width(); n = 14
    for i in range(n):
        dy = math.sin(t * 2.6 + i * 0.5) * wdt * 0.032
        ctx.save(); ctx.rectangle(cx - fw / 2 + fw * i / n, cy - fh / 2 + dy - 1, fw / n + 1, fh + 2); ctx.clip()
        ctx.set_source_surface(fs, cx - fw / 2, cy - fh / 2 + dy); ctx.paint_with_alpha(a)
        ctx.set_source_rgba(0, 0, 0, 0.16 * (0.5 + 0.5 * math.sin(t * 2.6 + i * 0.5 + 1.2)) * a); ctx.paint(); ctx.restore()


def badge_at(ctx, x, y, e, t, a):
    R = e.get('R', 30); lt = t - e['t0']; k = ease_back(lt / 0.55)
    if k <= 0.01: return
    acc = C.get(e.get('accent', 'gold'), C['gold'])
    ctx.save(); ctx.translate(x, y); ctx.scale(k, k)
    for r_, al in ((R + 7, 0.1), (R + 4, 0.18)): ctx.arc(1.5, 3, r_, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, al * a); ctx.fill()
    ctx.save(); ctx.arc(0, 0, R, 0, 2 * math.pi); ctx.clip(); ctx.set_source_rgba(*hexc('#1b2a3a'), a); ctx.paint()
    if e['kind'] == 'person': flag_wave(ctx, e['flag'] + '43', R * 0.25, -R * 0.05, R * 2.3, 0.92 * a, t)
    elif e['kind'] == 'flag':
        fs = scaled(e['flag'] + '11', R * 2.1); ctx.set_source_surface(fs, -fs.get_width() / 2, -fs.get_height() / 2); ctx.paint_with_alpha(a)
    elif e['kind'] == 'emblem':
        ctx.set_source_rgba(0.96, 0.96, 0.97, a); ctx.paint()
        fs = scaled(e['img'], R * 1.96); ctx.set_source_surface(fs, -fs.get_width() / 2, -fs.get_height() / 2); ctx.paint_with_alpha(a)
    ctx.restore()
    if e['kind'] == 'person':
        ps = scaled(e['pid'], R * 1.72); pw, ph = ps.get_width(), ps.get_height()
        ctx.save(); ctx.arc(0, 0, R, 0, 2 * math.pi); ctx.rectangle(-R * 0.66, -R * 2.4, R * 1.32, R * 2.4); ctx.set_fill_rule(cairo.FILL_RULE_WINDING); ctx.clip()
        ctx.set_source_surface(ps, -pw / 2, R - ph + R * 0.02); ctx.paint_with_alpha(a); ctx.restore()
    ctx.new_path(); ctx.arc(0, 0, R, 0, 2 * math.pi); ctx.set_source_rgba(0.03, 0.04, 0.06, a); ctx.set_line_width(3.2); ctx.stroke_preserve()
    ctx.set_source_rgba(*acc, 0.92 * a); ctx.set_line_width(1.5); ctx.stroke(); ctx.restore()
    la = a * smooth((lt - 0.3) / 0.35)
    if e.get('label') and la > 0.01:
        if e.get('side') == 'right':
            text(ctx, e['label'], x + R * k + 10, y + 1, 13, 'sansb', (1, 1, 1), la, 3, 'l')
            if e.get('role'): text(ctx, e['role'], x + R * k + 10, y + 17, 10, 'sansm', acc, la, 2.6, 'l')
        else:
            w = tw(ctx, e['label'], 12, 'sansb'); rrect(ctx, x - w / 2 - 8, y + R * k + 5, w + 16, 20, 3); ctx.set_source_rgba(0.03, 0.04, 0.06, 0.84 * la); ctx.fill()
            text(ctx, e['label'], x, y + R * k + 19.5, 12, 'sansb', (1, 1, 1), la, 0, 'c')
            if e.get('role'): text(ctx, e['role'], x, y + R * k + 38, 10, 'sansm', acc, la, 2.6, 'c')
    RESERVED.append((x - R - 10, y - R * 2.2, x + R + 10, y + R + 44))


def draw_badge(ctx, view, t, e):
    a = window(t, e['t0'], e['t1'], 0.01, 0.45)
    if a <= 0.01: return
    x, y = view.xy(e['lon'], e['lat']); badge_at(ctx, x, y, e, t, a)


# ------------------------------------------------------------------ cards
def draw_card(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.45, 0.45)
    if a <= 0.01: return
    slide = (1 - ease_out((t - e['t0']) / 0.55)) * 30; lines = e.get('lines', []); acc = C[e['accent']]
    wdt = 230; font(ctx, 'sansm', 13)
    for s_ in lines: wdt = max(wdt, ctx.text_extents(s_).x_advance + 44)
    wdt = max(wdt, tw(ctx, e['tag'], 10.5, 'sansb') + 44)
    bh = 0
    if e.get('bigs'):
        bw = 0
        for big, cap in e['bigs']: bw += max(tw(ctx, big, 30, 'disp'), tw(ctx, cap, 11, 'sansm')) + 26
        wdt = max(wdt, bw + 20); bh = 62
    if e.get('src'): wdt = max(wdt, tw(ctx, e['src'], 9.5, 'sans') + 40)
    h = 42 + bh + 21 * len(lines) + (18 if e.get('src') else 0)
    x = W_OUT - wdt - 24 + slide; y = e.get('y', 70)
    rrect(ctx, x, y, wdt, h, 5); ctx.set_source_rgba(0.05, 0.06, 0.09, 0.86 * a); ctx.fill()
    ctx.set_source_rgba(*acc, a); ctx.rectangle(x, y + 10, 3, h - 20); ctx.fill()
    text(ctx, e['tag'], x + 18, y + 23, 10.5, 'sansb', acc, a, 0, 'l', spacing=0.4); yy = y + 32
    if e.get('bigs'):
        xx = x + 18
        for big, cap in e['bigs']:
            text(ctx, big, xx, yy + 32, 30, 'disp', (1, 1, 1), a, 0, 'l'); text(ctx, cap, xx, yy + 50, 11, 'sansm', C['muted'], a, 0, 'l')
            xx += max(tw(ctx, big, 30, 'disp'), tw(ctx, cap, 11, 'sansm')) + 26
        yy += bh
    for i, s_ in enumerate(lines):
        text(ctx, s_, x + 18, yy + 17 + 21 * i, 13, 'serifb' if e.get('quote') else 'sansm', (0.94, 0.92, 0.9), a, 0, 'l')
    if e.get('src'): text(ctx, e['src'], x + 18, y + h - 12, 9.5, 'sans', C['muted'], a * 0.9, 0, 'l')


# ------------------------------------------------------------------ panels
def panel_title(ctx, a, s, sub=None):
    text(ctx, s, W_OUT / 2, 74, 19, 'serifb', (1, 1, 1), a, 0, 'c')
    if sub: text(ctx, sub, W_OUT / 2, 96, 11, 'sansm', C['muted'], a, 0, 'c')


def edge_curve(x0, y0, x1, y1, prog, n=36):
    cx = (x0 + x1) / 2; pts = []
    for s in np.linspace(0, prog, n):
        pts.append(((1 - s) ** 3 * x0 + 3 * (1 - s) ** 2 * s * cx + 3 * (1 - s) * s * s * cx + s ** 3 * x1,
                    (1 - s) ** 3 * y0 + 3 * (1 - s) ** 2 * s * y0 + 3 * (1 - s) * s * s * y1 + s ** 3 * y1))
    return np.array(pts)


def P_refusal(ctx, t, e, a):
    lt = t - e['t0']; panel_title(ctx, a, '3월 15일의 요구, 다음 날의 거절')
    ux, uy = 235, 262
    badge_at(ctx, ux, uy, dict(kind='person', pid='trump', flag='us', R=36, t0=e['t0'] + 0.4, label='도널드 트럼프', role='미국 대통령', accent='us'), t, a)
    rows = [('de', '독일'), ('gb', '영국'), ('jp', '일본'), ('au', '호주'), ('kr', '한국')]
    for i, (c, nm) in enumerate(rows):
        fx, fy = 590, 138 + i * 62; t0 = e['t0'] + 1.0 + i * 0.2
        badge_at(ctx, fx, fy, dict(kind='flag', flag=c, R=19, t0=t0, label=nm, side='right', accent='gold' if c == 'kr' else 'muted'), t, a)
        et0 = 2.2 + i * 0.75; prog = ease_io((lt - et0) / 1.3)
        if prog > 0:
            tr = at_word('ask_1', nm); red = smooth((t - tr) / 0.5)
            col = tuple(C['gold'][j] * (1 - red) + C['ru'][j] * red for j in range(3))
            pts = edge_curve(ux + 40, uy, fx - 26, fy, prog)
            ctx.new_path(); ctx.move_to(*pts[0])
            for p in pts[1:]: ctx.line_to(*p)
            if red > 0.5: ctx.set_dash([4, 4])
            ctx.set_source_rgba(*col, (0.8 - 0.25 * red) * a); ctx.set_line_width(1.5); ctx.stroke(); ctx.set_dash([])
            if red > 0: text(ctx, '거절', fx + 78, fy + 5, 12, 'sansb', C['ru'], a * red, 2.4, 'l')
    if lt > 0: text(ctx, '해협 방어 참여 요구', 400, 150, 11, 'sansb', C['gold'], a * smooth((lt - 3.2) / 0.5), 2.4, 'c')
    qa = a * window(t, S('ask_2', 0.3), E('ask_2', 0.9), 0.4, 0.4)
    if qa > 0: text(ctx, '“우리가 시작한 전쟁이 아니다” — 보리스 피스토리우스 독일 국방장관', W_OUT / 2, 414, 13, 'serifb', (1, 1, 1), qa, 3, 'c')
    qb = a * window(t, S('ask_3', 0.2), E('ask_3', 1.2), 0.4, 0.4)
    if qb > 0: text(ctx, '“매우 어리석은 실수” — 트럼프 대통령', ux, uy + 92, 12.5, 'serifb', C['us'], qb, 3, 'c')


def P_statement(ctx, t, e, a):
    lt = t - e['t0']; panel_title(ctx, a, '3월 21일 공동성명', '이란의 공격 규탄 · 항행의 자유 보장 촉구')
    rows = [('gb', '영국'), ('fr', '프랑스'), ('de', '독일'), ('it', '이탈리아'), ('jp', '일본'), ('nl', '네덜란드'), ('ca', '캐나다')]
    for i, (c, nm) in enumerate(rows):
        x = 110 + i * 92; badge_at(ctx, x, 230, dict(kind='flag', flag=c, R=24, t0=e['t0'] + 0.5 + i * 0.22, label=nm, accent='muted'), t, a)
    tk = at_word('ask_4', '한국')
    badge_at(ctx, W_OUT / 2, 345, dict(kind='flag', flag='kr', R=30, t0=max(e['t0'] + 2.2, tk), label='대한민국', role='성명에 동참', accent='gold'), t, a)
    ka = a * smooth((t - max(e['t0'] + 2.2, tk)) / 0.5)
    ctx.set_source_rgba(*C['gold'], 0.5 * ka); ctx.set_line_width(1); ctx.set_dash([3, 4]); ctx.move_to(110, 292); ctx.line_to(W_OUT - 190, 292); ctx.stroke(); ctx.set_dash([])


TL_EVENTS = [('2026-02-28', '개전 · 해협 봉쇄', 'ru', -1, None), ('2026-03-15', '트럼프, 동맹에 요구', 'us', 1, None),
             ('2026-04-07', '안보리 거부권', 'ru', -2, 'timeline_1'), ('2026-04-13', '미국 해상 봉쇄', 'us', 2, 'timeline_2'),
             ('2026-06-17', '양해각서 서명', 'green', -1, 'timeline_3'), ('2026-07-08', '휴전 붕괴', 'ru', 1, 'timeline_4'),
             ('2026-08-25', '기뢰 제거 발표', 'us', -2, 'timeline_5'), ('2026-09-18', '한국, 파병 않기로', 'gold', 2, 'END')]


def P_timeline(ctx, t, e, a):
    lt = t - e['t0']; panel_title(ctx, a, '해협의 일곱 달', '2026년 2월 – 9월')
    X0, X1, Y = 80, 774, 262
    fx = lambda s: X0 + (date(*map(int, s.split('-'))) - date(2026, 2, 1)).days / (date(2026, 9, 30) - date(2026, 2, 1)).days * (X1 - X0)
    k = ease_io(lt / 1.2)
    ctx.set_source_rgba(1, 1, 1, 0.35 * a); ctx.set_line_width(1.4); ctx.move_to(X0, Y); ctx.line_to(X0 + (X1 - X0) * k, Y); ctx.stroke()
    for m in range(2, 10):
        x = fx(f'2026-{m:02d}-01')
        if x <= X0 + (X1 - X0) * k:
            ctx.rectangle(x, Y - 4, 1, 8); ctx.set_source_rgba(1, 1, 1, 0.35 * a); ctx.fill()
            text(ctx, f'{m}월', x + 3, Y + 22, 10.5, 'sansm', C['muted'], a * 0.9, 0, 'l')
    ca = a * smooth((t - S('timeline_3', 0.0)) / 0.6)
    if ca > 0:
        x0, x1 = fx('2026-04-08'), fx('2026-07-08'); ctx.rectangle(x0, Y - 7, x1 - x0, 14); ctx.set_source_rgba(*C['green'], 0.18 * ca); ctx.fill()
        text(ctx, '휴전 4.8 – 7.8', (x0 + x1) / 2, Y + 40, 10.5, 'sansm', C['green'], ca, 2, 'c')
    cur = None
    for d, lab, col, side, sid in TL_EVENTS:
        tt = e['t0'] + 0.8 if sid is None else (e['t1'] - 3.0 if sid == 'END' else S(sid, 0.1))
        f = smooth((t - tt) / 0.5)
        if f <= 0: continue
        cur = d; x = fx(d); c_ = C[col]; al = a * f * (0.55 if sid == 'END' else 1)
        L = 44 if abs(side) == 1 else 96; yy = Y - L if side < 0 else Y + L
        ctx.set_source_rgba(*c_, al * 0.8); ctx.set_line_width(1.2); ctx.move_to(x, Y); ctx.line_to(x, Y + (yy - Y) * ease_out(f)); ctx.stroke()
        ctx.arc(x, Y, 4.5, 0, 2 * math.pi); ctx.set_source_rgba(*c_, al); ctx.fill()
        mm, dd = d[5:7].lstrip('0'), d[8:].lstrip('0')
        ty = yy - 18 if side < 0 else yy + 14
        text(ctx, f'{mm}.{dd}', x, ty, 11, 'mono', c_, al, 2.4, 'c'); text(ctx, lab, x, ty + (14 if side < 0 else 15), 11.5, 'sansb', (1, 1, 1), al, 2.4, 'c')
    if cur:
        x = fx(cur); ctx.set_source_rgba(*C['gold'], 0.35 * a); ctx.set_line_width(1); ctx.set_dash([2, 3]); ctx.move_to(x, 118); ctx.line_to(x, 400); ctx.stroke(); ctx.set_dash([])


def P_precedent(ctx, t, e, a):
    panel_title(ctx, a, '한국의 해외 파견 결정', '전례와 이번 결정')
    cards = [('2004', '이라크 자이툰 부대', ['아르빌 파견', '6자회담 속 대미 관계', '국내 반대 여론'], S('past_1', 0.0), 'roh'),
             ('2009', '청해부대', ['소말리아 아덴만', '해적 대응 · 상선 보호'], S('past_3', 0.2), None),
             ('2020', '작전 구역 확대', ['호르무즈까지 확대', '지휘권은 한국군'], at_word('past_3', '호르무즈'), None),
             ('2026', '이번 결정', ['전쟁 개입 파병 없음', '최소한의 활동만'], E('past_3', -0.6), None)]
    for i, (yr, ti, lines, t0, pp) in enumerate(cards):
        f = smooth((t - t0) / 0.5)
        if f <= 0: continue
        x = 58 + i * 190; y = 150 - (1 - f) * 16; ca = a * f; col = C['gold'] if yr == '2026' else C['teal']
        rrect(ctx, x, y, 172, 212, 6); ctx.set_source_rgba(0.07, 0.08, 0.12, 0.92 * ca); ctx.fill()
        ctx.set_source_rgba(*col, ca); ctx.rectangle(x, y, 172, 3); ctx.fill()
        text(ctx, yr, x + 16, y + 42, 28, 'disp', col, ca, 0, 'l'); text(ctx, ti, x + 16, y + 68, 14, 'sansb', (1, 1, 1), ca, 0, 'l')
        for j, s_ in enumerate(lines): text(ctx, s_, x + 16, y + 96 + j * 20, 11.5, 'sansm', C['muted'], ca, 0, 'l')
        if pp == 'roh':
            badge_at(ctx, x + 136, y + 172, dict(kind='person', pid='roh_moo_hyun', flag='kr', R=24, t0=t0 + 0.3, label='', accent='teal'), t, a)
            text(ctx, '노무현 대통령', x + 16, y + 196, 10.5, 'sansb', C['teal'], ca * smooth((t - t0 - 0.6) / 0.4), 0, 'l')


def P_versus(ctx, t, e, a):
    panel_title(ctx, a, '파병을 둘러싼 두 입장')
    cols = [('지지하는 쪽', C['teal'], 60, [('호르무즈는 곧 한국의 경제 안보', S('debate_2', 0.3)), ('원유 61% · 나프타 54%가 이 해협 경유', S('debate_2', 1.6))], 'UPI 기고 · 9월 8일'),
            ('반대하는 쪽', C['amber'], 450, [('비전투 부대도 표적이 될 수 있다', S('debate_3', 0.3)), ('미국 방공 미사일 재고 감소', S('debate_4', 0.3)),
                                               ('2004년 파병 당시의 국내 갈등', S('debate_4', 1.8))], 'Foreign Policy · 9월 10일')]
    for title, col, x, items, src in cols:
        fa = a * smooth((items[0][1] - 0.4 - e['t0'] if False else (t - items[0][1] + 0.6)) / 0.5)
        if fa <= 0: continue
        rrect(ctx, x, 120, 344, 262, 6); ctx.set_source_rgba(0.07, 0.08, 0.12, 0.92 * fa); ctx.fill(); ctx.set_source_rgba(*col, fa); ctx.rectangle(x, 120, 344, 3); ctx.fill()
        text(ctx, title, x + 22, 156, 16, 'sansb', col, fa, 0, 'l')
        for i, (s_, t0) in enumerate(items):
            ia = a * smooth((t - t0) / 0.45)
            ctx.arc(x + 26, 196 + i * 50 - 5, 3, 0, 2 * math.pi); ctx.set_source_rgba(*col, ia); ctx.fill()
            text(ctx, s_, x + 38, 196 + i * 50, 13.5, 'serifb', (1, 1, 1), ia, 0, 'l')
        text(ctx, src, x + 22, 366, 10, 'sans', C['muted'], fa, 0, 'l')


PANELS = {'refusal': P_refusal, 'statement': P_statement, 'timeline': P_timeline, 'precedent': P_precedent, 'versus': P_versus}


def draw_panel(ctx, t, e):
    a = window(t, e['t0'], e['t1'], 0.6, 0.6)
    if a <= 0.01: return
    ctx.set_source_rgba(0.025, 0.03, 0.045, 0.8 * a); ctx.paint(); PANELS[e['kind']](ctx, t, e, a)


# ------------------------------------------------------------------ HUD / subtitles / cards
def cur_sentence(t):
    cur = None
    for sid in ORDER:
        if SENT[sid]['t0'] - 0.3 <= t: cur = sid
    return cur


def in_fullcard(t): return any(c['t0'] - 0.3 <= t <= c['t1'] + 0.3 for c in P['cards'])


def draw_date(ctx, t):
    sid = cur_sentence(t)
    if sid is None or in_fullcard(t): return
    d = SENT[sid]['date']; prev = None; t_ch = 0
    for s_ in ORDER:
        if SENT[s_]['t0'] - 0.3 > t: break
        if SENT[s_]['date'] != prev: prev = SENT[s_]['date']; t_ch = SENT[s_]['t0'] - 0.3
    k = smooth((t - t_ch) / 0.45); a = 0.95 * k
    txt = d.replace('.', '. ') if len(d) > 4 else d
    w = text(ctx, txt, W_OUT - 26, 40 - (1 - k) * 6, 15, 'mono', (1, 1, 1), a, 3, 'r')
    ctx.set_source_rgba(*C['gold'], 0.9 * a); ctx.rectangle(W_OUT - 26 - w * k, 48, w * k, 1.4); ctx.fill()


def draw_subtitle(ctx, t):
    for sid in ORDER:
        x = SENT[sid]
        if x['t0'] - 0.05 <= t <= x['t1'] + 0.25:
            a = min(smooth((t - x['t0'] + 0.05) / 0.18), smooth((x['t1'] + 0.25 - t) / 0.2)); size = 19
            flags = []
            for seg, f in x['segments']: flags += [f] * len(seg)
            txt = ''.join(s for s, f in x['segments']); lines = wrap(ctx, txt, 700, size, 'sansm'); base_y = 452 - (len(lines) - 1) * 26; pos = 0
            for li, ln in enumerate(lines):
                j = txt.find(ln, pos); pos = j + len(ln); font(ctx, 'sansm', size); lw = ctx.text_extents(ln).x_advance; xx = W_OUT / 2 - lw / 2; k = 0
                while k < len(ln):
                    f = flags[j + k] if j + k < len(flags) else 0; k2 = k
                    while k2 < len(ln) and (flags[j + k2] if j + k2 < len(flags) else 0) == f: k2 += 1
                    run = ln[k:k2]
                    text(ctx, run, xx, base_y + li * 26, size, 'sansb' if f else 'sansm', C['gold'] if f else (1, 1, 1), a, 5.0, 'l', halo_a=0.92)
                    font(ctx, 'sansm', size); xx += ctx.text_extents(run).x_advance; k = k2
            return


def credit_sections():
    pp = REG['people']
    lic = lambda k: pp[k]['license']
    return [
        ('보도 · 자료', [('Reuters (9.4)  ·  The Korea Herald (9.7)', ''), ('UPI 기고 (9.8)  ·  Foreign Policy (9.10)', ''),
                        ('국제해사기구 (6.11 기준)', ''), ('위키백과 “2026 Strait of Hormuz campaign”', '')]),
        ('인물 사진', [('이재명', lic('lee_jae_myung')), ('노무현', lic('roh_moo_hyun') + ' · 공공누리 제1유형'),
                      ('도널드 트럼프 · 알리 하메네이', 'osint_generator 라이브러리 가공본')]),
        ('사진 · 영상', [('혁명수비대의 유조선 나포 영상 (2023)', 'U.S. Navy · Public domain'), ('이란 군사 목표 타격 영상 (2026.7.7)', 'U.S. Central Command · Public domain'),
                       ('해상초계기 P-8A', 'U.S. Navy · Public domain'), ('이라크 파병 한국군 (2003)', 'U.S. Government · Public domain'),
                       ('호르무즈 해협 통과 미 해군 (2023)', 'U.S. Navy · Public domain')]),
        ('휘장 · 국기 · 지도', [('미 해군 중부사령부 휘장', 'Public domain'), ('국기', 'flag-icons · MIT'),
                              ('지도 · 지형', 'Natural Earth · AWS Terrain Tiles')]),
        ('음악 · 음성', [('The Life and Death of a Certain K. Zabriskie, Patriarch', 'Chris Zabriskie · CC BY 4.0'), ('내레이션', 'AI 음성 합성')]),
    ]


def credits():
    return [f"{sec}: {' / '.join(m + (' — ' + l if l else '') for m, l in items)}" for sec, items in credit_sections()]


def draw_endcard(ctx, t, c, a):
    lt = t - c['t0']
    ctx.set_source_rgba(0.018, 0.022, 0.032, 0.94 * a); ctx.paint()
    k = ease_out((lt - 0.1) / 0.9)
    text(ctx, 'SOURCES  &  CREDITS', 64, 84 - (1 - k) * 6, 8.5, 'mono', C['gold'], a * k, 0, 'l', spacing=2.4)
    text(ctx, '자료 및 출처', 64, 110 - (1 - k) * 6, 17, 'serif', (0.96, 0.95, 0.93), a * k, 0, 'l', spacing=1.0)
    ctx.set_source_rgba(*C['gold'], 0.9 * a * k); ctx.rectangle(64, 122, 36 * k, 1.1); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.08 * a * k); ctx.rectangle(64, 140, W_OUT - 128, 0.8); ctx.fill()
    cols = [(64, 158), (456, 158)]; secs = credit_sections(); place = [0, 0, 1, 0, 1]; yy = [158, 158]; n = 0
    for si, (sec, items) in enumerate(secs):
        ci = place[si]; x = cols[ci][0]; y = yy[ci]; sa = a * smooth((lt - 0.5 - si * 0.18) / 0.6)
        text(ctx, sec, x, y, 8.5, 'sansb', C['gold'], sa * 0.9, 0, 'l', spacing=1.4); y += 15
        for m, l in items:
            ia = a * smooth((lt - 0.6 - si * 0.18 - n * 0.03) / 0.6); n += 1
            text(ctx, m, x, y, 9.2, 'sans', (0.86, 0.87, 0.9), ia, 0, 'l')
            if l:
                text(ctx, l, x, y + 11, 7.8, 'monom', C['muted'], ia * 0.9, 0, 'l'); y += 23
            else:
                y += 14
        yy[ci] = y + 10
    fa = a * smooth((lt - 1.6) / 0.8)
    ctx.set_source_rgba(1, 1, 1, 0.08 * fa); ctx.rectangle(64, H_OUT - 44, W_OUT - 128, 0.8); ctx.fill()
    text(ctx, P['date'].replace('.', '. ') + ' 기준', 64, H_OUT - 26, 7.8, 'monom', C['muted'], fa, 0, 'l', spacing=0.6)
    text(ctx, '수치와 인용은 제작 시점의 공개 보도에 근거합니다', W_OUT - 64, H_OUT - 26, 7.8, 'sans', C['muted'], fa, 0, 'r')


def draw_fullcards(ctx, t):
    for c in P['cards']:
        if not (c['t0'] - 0.1 <= t <= c['t1'] + 0.1): continue
        a = window(t, c['t0'], c['t1'], 0.7, 0.7); lt = t - c['t0']
        if c['kind'] == 'title':
            g = cairo.LinearGradient(0, 0, 0, H_OUT)
            for st, al in ((0, 0.86), (0.5, 0.7), (1, 0.92)): g.add_color_stop_rgba(st, 0.01, 0.015, 0.03, al * a)
            ctx.set_source(g); ctx.paint()
        if c['kind'] == 'title':
            k = ease_out(lt / 1.0)
            text(ctx, P['title'], W_OUT / 2, 232 - (1 - k) * 10, 46, 'disp', (1, 1, 1), a * smooth((lt - 0.1) / 0.6), 0, 'c')
            ctx.set_source_rgba(*C['gold'], 0.95 * a); lw = 220 * ease_io((lt - 0.5) / 0.9); ctx.rectangle(W_OUT / 2 - lw / 2, 254, lw, 1.6); ctx.fill()
            text(ctx, P['subtitle'], W_OUT / 2, 290, 18, 'serifb', (0.92, 0.9, 0.88), a * smooth((lt - 0.8) / 0.6), 0, 'c')
            text(ctx, P['date'].replace('.', '. '), W_OUT / 2, 322, 12, 'mono', C['gold'], a * smooth((lt - 1.1) / 0.6), 0, 'c')
        else:
            draw_endcard(ctx, t, c, a)


def build_vignette():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT); c = cairo.Context(s)
    g = cairo.RadialGradient(W_OUT / 2, H_OUT / 2, H_OUT * 0.36, W_OUT / 2, H_OUT / 2, W_OUT * 0.72); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    c.set_source(g); c.paint()
    g = cairo.LinearGradient(0, H_OUT - 110, 0, H_OUT); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55); c.set_source(g); c.rectangle(0, H_OUT - 110, W_OUT, 110); c.fill()
    g = cairo.LinearGradient(0, 0, 0, 80); g.add_color_stop_rgba(0, 0, 0, 0, 0.4); g.add_color_stop_rgba(1, 0, 0, 0, 0); c.set_source(g); c.rectangle(0, 0, W_OUT, 80); c.fill()
    return s


VIG = build_vignette()
MAPDRAW = {'country': draw_country, 'route': draw_route, 'tanker_loop': draw_tanker_loop, 'barrier': draw_barrier, 'ships': draw_ships,
           'boom': draw_boom, 'marker': draw_marker, 'badge': draw_badge, 'cutout': draw_cutout}
LAYER = ['country', 'ships', 'route', 'tanker_loop', 'barrier', 'boom', 'cutout', 'marker', 'badge']


def render_frame(i):
    t = i / FPS; view = View(i); RESERVED.clear()
    im = view.base(); buf = bytearray(im.tobytes('raw', 'BGRX'))
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W_OUT, H_OUT, W_OUT * 4); ctx = cairo.Context(surf)
    act = [e for e in EV if e['t0'] - 0.05 <= t <= e['t1'] + 0.05]
    panel_a = max([window(t, e['t0'], e['t1'], 0.6, 0.6) for e in act if e['type'] == 'panel'] + [0])
    draw_borders(ctx, view)
    for L in LAYER:
        for e in act:
            if e['type'] == L: MAPDRAW[L](ctx, view, t, e)
    if panel_a < 0.99: draw_labels(ctx, view, t, 1 - panel_a)
    for e in act:
        if e['type'] == 'dip' and e.get('under'):
            d = math.sin(math.pi * clamp01((t - e['t0']) / (e['t1'] - e['t0']))); ctx.set_source_rgba(0, 0, 0, 0.93 * d); ctx.paint()
    for e in act:
        if e['type'] == 'panel': draw_panel(ctx, t, e)
    for e in act:
        if e['type'] == 'photo': draw_photo(ctx, t, e)
        elif e['type'] == 'clip': draw_clip(ctx, t, e)
    for e in act:
        if e['type'] == 'card': draw_card(ctx, t, e)
        elif e['type'] == 'article': draw_article(ctx, t, e)
    draw_date(ctx, t); draw_fullcards(ctx, t); draw_subtitle(ctx, t)
    for e in act:
        if e['type'] == 'dip' and not e.get('under'):
            d = math.sin(math.pi * clamp01((t - e['t0']) / (e['t1'] - e['t0']))); ctx.set_source_rgba(0, 0, 0, 0.93 * d); ctx.paint()
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
