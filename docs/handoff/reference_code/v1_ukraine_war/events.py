# -*- coding: utf-8 -*-
"""Scene events keyed to narration timing (timeline.py). Consumed by render.py."""
import pickle
from shapely.ops import unary_union
import timeline as TL

G = pickle.load(open('/home/claude/geo.pkl', 'rb'))
SN = G['snap']
PCT = G.get('ds_pct', {})


def S(sid, off=0.0):
    return TL.T[sid] + off


def E(sid, off=0.0):
    return TL.TE[sid] + off


END = TL.TOTAL
CAM, EVENTS, NOTES = [], [], []


def cam(t, lon, lat, w, dur=2.6):
    CAM.append((t, lon, lat, w, dur))


def ev(_typ, t0, t1, **kw):
    d = dict(type=_typ, t0=t0, t1=t1); d.update(kw); EVENTS.append(d)


def note(t0, t1, text):
    NOTES.append(dict(t0=t0, t1=t1, text=text))


# ------------------------------------------------------------ places (lon, lat)
PL = {
    'kyiv': (30.52, 50.45), 'kharkiv': (36.23, 49.99), 'odesa': (30.72, 46.48), 'lviv': (24.03, 49.84),
    'dnipro': (35.05, 48.46), 'zap': (35.14, 47.84), 'donetsk': (37.80, 48.02), 'luhansk': (39.31, 48.57),
    'mariupol': (37.55, 47.10), 'kherson': (32.62, 46.64), 'mykolaiv': (32.00, 46.98), 'melitopol': (35.37, 46.85),
    'sevastopol': (33.52, 44.62), 'simferopol': (34.10, 44.95), 'kerch': (36.47, 45.36), 'chernihiv': (31.29, 51.50),
    'sumy': (34.80, 50.91), 'izium': (37.26, 49.21), 'kupiansk': (37.61, 49.71), 'sloviansk': (37.61, 48.85),
    'kramatorsk': (37.56, 48.72), 'bakhmut': (38.00, 48.60), 'avdiivka': (37.75, 48.14), 'pokrovsk': (37.18, 48.28),
    'hostomel': (30.19, 50.60), 'bucha': (30.22, 50.54), 'chernobyl': (30.10, 51.39), 'hrabove': (38.64, 48.14),
    'kakhovka': (33.37, 46.78), 'robotyne': (35.84, 47.45), 'sudzha': (35.27, 51.19), 'kursk': (36.19, 51.73),
    'belgorod': (36.59, 50.60), 'rostov': (39.72, 47.24), 'novoros': (37.77, 44.72), 'moscow': (37.62, 55.75),
    'minsk': (27.56, 53.90), 'istanbul': (28.98, 41.01), 'budapest': (19.04, 47.50), 'snake': (30.20, 45.26),
    'moskva_sink': (30.93, 45.18), 'balakliia': (36.84, 49.46), 'belbek': (33.57, 44.69),
}


def u(*keys):
    gs = [SN[k] if isinstance(k, str) else k for k in keys]
    return unary_union(gs).buffer(0)


def obl(*codes):
    return unary_union([G['oblasts'][c] for c in codes]).buffer(0)


CR = SN['crimea']
PEAK = u('peak', 'crimea')
NORTH = obl('UA-32', 'UA-30', 'UA-74', 'UA-59', 'UA-18').buffer(0.02)
APR22 = PEAK.difference(NORTH).buffer(0)
DS = lambda k: u('ds_' + k, 'crimea')
C2026 = DS('2026-09-26')
DONETSK_FREE = obl('UA-14').difference(C2026).buffer(0)

# ------------------------------------------------------------ control-area track (crossfaded)
TL_START = E('C7_6', 0.8)
TL_END = S('C7_7', -0.6)
track = [
    (S('C2_7', 0.6), CR), (S('C2_10', 0.3), u('occ2014', 'crimea')), (S('C3_3', 0.5), u('sep2015', 'crimea')),
    (S('C4_7', 0.2), PEAK), (S('C4_10', 0.8), APR22), (S('C6_2', 0.3), DS('2022-10-08')),
    (S('C6_5', 0.6), DS('2022-11-15')), (S('C6_11', 0.6), DS('2024-03-01')), (S('C6_13', 0.8), DS('2025-04-28')),
    (S('C6_14', 0.6), DS('2025-12-01')), (S('C7_5', 0.6), DS('2026-03-01')),
]
# timelapse frames
tl_keys = [('2022.03 (개략)', PEAK, None), ('2022.04 (개략)', APR22, None)]
months = sorted(k[3:] for k in SN if k.startswith('ds_2') and k[3:] >= '2022-10-01' and len(k) == 13)
months = [m for m in months if m.endswith('-01')] + ['2026-09-26']
for m in months:
    tl_keys.append((m[:7].replace('-', '.'), DS(m), PCT.get('ds_' + m)))
step = (TL_END - TL_START - 1.2) / len(tl_keys)
TL_FRAMES = []
for i, (lab, g, pct) in enumerate(tl_keys):
    tt = TL_START + i * step
    track.append((tt, g)); TL_FRAMES.append((tt, lab, pct))
track.append((S('C7_7', -0.4), C2026))
track.sort(key=lambda x: x[0])
for i, (t0, g) in enumerate(track):
    t1 = track[i + 1][0] + 0.5 if i + 1 < len(track) else END
    fast = TL_START - 0.1 <= t0 <= TL_END
    ev('area', t0, t1, geom=g, style='ru', fade=0.3 if fast else 0.9, fade_out=0.3 if fast else 0.9)
ev('tl', TL_START - 0.3, TL_END + 0.8, frames=TL_FRAMES)
note(S('C6_2'), END, '점령지 경계: DeepState 월별 자료(2022.10~) · 그 이전은 개략')
note(S('C2_7', 0.6), S('C6_2', -0.2), '점령지 경계는 개략적 범위입니다')

# ------------------------------------------------------------ prologue
cam(0, 33.5, 46.8, 27, 0)
cam(S('P2', -0.3), 31.6, 48.6, 21, 5.0)
cam(S('P3', 0), 32.5, 47.4, 23, 6.0)

# ------------------------------------------------------------ C1 stage
cam(S('C1_1', -0.8), 31.5, 48.6, 21)
ev('marker', S('C1_1', 0.3), E('C1_2', 0.3), lon=30.52, lat=50.45, kind='star', color='gold', label='키이우', city='키이우')
ev('card', S('C1_2', 0.3), E('C1_2', 0.6), kind='stat', tag='1991', big='≈1,900', lines=['전략 핵탄두', '당시 세계 3위 규모'], accent='gold')
cam(S('C1_3', -0.8), 26.5, 48.6, 22)
ev('marker', S('C1_3', 0.4), E('C1_4', 0.4), lon=19.04, lat=47.50, kind='doc', color='gold', label='부다페스트', sub='1994 각서')
ev('card', S('C1_4', 0.2), E('C1_4', 0.6), kind='info', tag='부다페스트 각서', title='핵 포기 ↔ 안전 보장', lines=['미국 · 영국 · 러시아', '우크라이나 주권·국경 존중 약속'], accent='gold')
cam(S('C1_5', -0.8), 33.9, 44.95, 5.5, 3.2)
ev('marker', S('C1_5', 0.5), E('C1_7', 0.3), lon=33.52, lat=44.62, kind='ship', color='ru', icon_color='white', label='세바스토폴', sub='러시아 흑해함대', city='세바스토폴')
ev('card', S('C1_6', 0.3), E('C1_6', 0.5), kind='stat', tag='기지 임차', big='2042', lines=['2010년 계약 연장', '(하르키우 협정)'], accent='ru')
cam(S('C1_7', -0.6), 33.2, 43.6, 15, 3.0)
ev('movers', S('C1_7', 0.2), E('C1_7', 0.6), pts=[(33.5, 44.55), (32.4, 43.6), (30.6, 42.4), (29.1, 41.25)], n=5, speed=0.09, color='teal')
ev('line', S('C1_7', 0.2), E('C1_7', 0.6), pts=[(33.5, 44.55), (32.4, 43.6), (30.6, 42.4), (29.1, 41.25)], color='teal', width=1.4, dash=[4, 5], dash_speed=12, label='보스포루스 해협 → 지중해', label_at=(29.3, 41.55), anchor='l', label_size=11)
cam(S('C1_8', -0.8), 38.3, 48.3, 7.0, 3.0)
ev('area', S('C1_8', 0.3), E('C1_9', 0.4), geom='donlug', style='gold')
ev('particles', S('C1_8', 0.4), E('C1_9', 0.4), lon=38.3, lat=48.3, n=60, seed=5)
ev('marker', S('C1_9', 0.1), E('C1_9', 0.4), lon=37.80, lat=48.02, kind='dot', color='gold', label='도네츠크', city='도네츠크')

# ------------------------------------------------------------ C2 Maidan -> Crimea -> Donbas
cam(S('C2_1', -0.8), 30.7, 50.35, 4.5, 3.0)
ev('marker', S('C2_1', 0.3), E('C2_3', 0.4), lon=30.52, lat=50.45, kind='star', color='gold', label='키이우 · 마이단', city='키이우', encircle=False)
ev('particles', S('C2_2', 0.0), E('C2_3', 0.5), lon=30.52, lat=50.45, n=90, seed=2)
ev('card', S('C2_3', 0.3), E('C2_3', 0.6), kind='stat', tag='2014.02.18–20', big='100+', lines=['유혈 충돌 사망자', '우크라이나: “존엄 혁명”'], accent='ru')
cam(S('C2_4', -0.6), 34.2, 47.6, 13, 3.0)
ev('line', S('C2_4', 0.2), E('C2_4', 1.0), pts=[PL['kyiv'], PL['kharkiv'], PL['donetsk'], (34.2, 44.75)], curve=False, color='gold', width=1.8, dash=[5, 4], draw=2.6, label='야누코비치 도피 경로 (크림 경유 러시아행)', label_at=(34.6, 44.5), anchor='l', label_size=11)
cam(S('C2_5', -0.8), 34.2, 45.25, 5.2, 3.0)
ev('dots', S('C2_5', 0.3), E('C2_6', 0.5), pts=[PL['simferopol'], PL['sevastopol'], PL['belbek'], PL['kerch'], (33.37, 45.19), (35.38, 45.03)], color='ru', r=3.4, stagger=2.0)
ev('marker', S('C2_6', 0.2), E('C2_6', 0.6), lon=34.10, lat=44.95, kind='x', color='ru', label='크림 의회 장악', city='심페로폴', dy=-14)
ev('card', S('C2_7', 0.4), E('C2_7', 0.8), kind='stat', tag='2014.03.18', big='병합 선언', big_size=28, lines=['러시아, 크림반도 병합', '주민투표 3.16'], accent='ru')
ev('card', S('C2_8', 0.2), E('C2_8', 0.6), kind='versus', tag='유엔 총회 결의 68/262', left=('찬성', '100'), right=('반대', '11'), accent='ua')
cam(S('C2_9', -0.8), 38.4, 48.3, 6.5, 3.0)
ev('dots', S('C2_9', 0.3), E('C2_10', 0.5), pts=[PL['donetsk'], PL['luhansk'], PL['sloviansk'], PL['kramatorsk'], (38.51, 48.30)], color='ru', r=3.2)
ev('marker', S('C2_10', 0.1), E('C2_11', 0.3), lon=37.80, lat=48.02, kind='dot', color='ru', label='도네츠크', city='도네츠크')
ev('marker', S('C2_10', 0.4), E('C2_11', 0.3), lon=39.31, lat=48.57, kind='dot', color='ru', label='루한스크', city='루한스크')
ev('arrow', S('C2_11', 0.2), E('C2_11', 0.9), pts=[(36.9, 49.2), (37.35, 49.0), (37.55, 48.88)], color='ua', width=4.5, grow=1.3)

# ------------------------------------------------------------ C3 frozen eight years
cam(S('C3_1', -0.8), 38.5, 48.15, 4.2, 3.0)
ev('marker', S('C3_1', 0.4), E('C3_2', 0.5), lon=38.64, lat=48.14, kind='plane', color='ru', icon_color='white', label='MH17 추락', sub='2014.07.17', dy=-16, anchor='c')
ev('card', S('C3_1', 0.6), E('C3_1', 0.8), kind='stat', tag='MH17', big='298', count_to=298, lines=['탑승자 전원 사망', '암스테르담 → 쿠알라룸푸르'], accent='ru')
ev('line', S('C3_2', 0.2), E('C3_2', 0.8), pts=[(40.0, 48.2), (39.3, 48.05), (38.73, 47.97)], color='ru', width=1.6, dash=[3, 4], draw=1.4)
ev('marker', S('C3_2', 0.8), E('C3_2', 0.8), lon=38.73, lat=47.97, kind='x', color='ru', label='발사 지점(JIT)', anchor='r', dy=16)
note(S('C3_2'), E('C3_2', 0.8), '러시아는 MH17 격추 책임을 부인하고 있습니다')
cam(S('C3_3', -0.8), 31.0, 51.2, 15, 3.0)
ev('marker', S('C3_3', 0.3), E('C3_3', 0.8), lon=27.56, lat=53.90, kind='doc', color='gold', label='민스크', sub='2014 · 2015 협정', city='민스크')
cam(S('C3_4', -0.6), 38.4, 48.3, 7, 3.0)
ev('card', S('C3_4', 0.2), E('C3_4', 0.7), kind='stat', tag='2014–2021 돈바스', big='≈14,000', count_to=14000, fmt='≈{:,.0f}', lines=['분쟁 관련 사망자', '유엔 인권사무소 집계'], accent='ru')
cam(S('C3_5', -0.8), 36.55, 45.3, 3.0, 3.0)
ev('line', S('C3_5', 0.3), E('C3_7', 0.5), pts=[(36.49, 45.31), (36.57, 45.27), (36.66, 45.22), (36.74, 45.21)], color='white', width=2.4, curve=True, draw=1.6, label='크림대교 19km', label_at=(36.62, 45.36), anchor='c', label_size=12)
ev('marker', S('C3_6', 0.3), E('C3_6', 0.8), lon=36.52, lat=45.05, kind='ship', color='ua', icon_color='white', label='우크라이나 함정 3척 나포', anchor='l', sub='2018.11.25')
cam(S('C3_7', -0.6), 36.6, 46.0, 6.0, 2.6)
ev('line', S('C3_7', 0.2), E('C3_7', 0.7), pts=[(36.35, 45.40), (36.62, 45.30), (36.85, 45.18)], color='ru', width=3.0, curve=False, draw=0.8, label='아조우해 뱃길 통제', label_at=(37.0, 45.55), anchor='l', label_size=12)
cam(S('C3_8', -0.8), 33.8, 50.0, 22, 3.2)
TROOPS = [(29.2, 52.1), (27.9, 52.0), (32.3, 52.7), (35.9, 51.6), (36.7, 50.8), (38.2, 50.4), (39.6, 49.3), (39.8, 47.6), (33.9, 45.6), (35.2, 45.3)]
ev('dots', S('C3_8', 0.3), E('C3_9', 0.8), pts=TROOPS, color='ru', r=4.2, stagger=2.4)
ev('card', S('C3_9', 0.2), E('C3_9', 0.8), kind='versus', tag='2021.12', left=('러시아', '나토 동진 중단'), right=('미국', '침공 임박 경고'), accent='gold')

# ------------------------------------------------------------ C4 invasion
cam(S('C4_1', -0.8), 38.3, 48.4, 7.5, 3.0)
ev('area', S('C4_1', 0.3), E('C4_1', 0.7), geom='donlug', style='amber', dash=[5, 4])
cam(S('C4_2', -0.5), 32.4, 49.0, 21, 3.0)
ev('flash', S('C4_2', 0.25), S('C4_2', 0.75), a=0.28)
ev('card', S('C4_3', 0.2), E('C4_3', 0.6), kind='info', tag='러시아가 내세운 명분', title='“특별군사작전”', lines=['나토 확장에 대한 대응', '돈바스 주민 보호 · “탈나치화”'], accent='ru')
AX = {
    'kyiv_w': [(29.9, 51.95), (30.05, 51.45), (30.18, 50.95), (30.35, 50.62)],
    'kyiv_e': [(31.55, 52.2), (31.35, 51.6), (31.05, 51.0), (30.85, 50.6)],
    'sumy': [(34.2, 51.35), (33.4, 51.2), (32.3, 50.95), (31.2, 50.65)],
    'kharkiv': [(36.62, 50.62), (36.45, 50.3), (36.3, 50.05)],
    'donbas': [(38.4, 48.0), (37.9, 47.75), (37.6, 47.2)],
    'kherson': [(33.75, 46.05), (33.2, 46.45), (32.7, 46.65), (32.1, 46.95)],
    'meli': [(34.7, 46.1), (35.3, 46.75), (36.4, 46.9), (37.4, 47.08)],
}
for k, pts in AX.items():
    ev('arrow', S('C4_4', 0.2), S('C4_10', 0.6), pts=pts, color='ru', width=5.0, grow=1.8, retract=S('C4_10', -0.2) if k in ('kyiv_w', 'kyiv_e', 'sumy') else None)
cam(S('C4_5', -0.6), 30.4, 51.0, 5.5, 3.0)
ev('marker', S('C4_5', 0.3), E('C4_5', 0.6), lon=30.10, lat=51.39, kind='rad', color='yellow', label='체르노빌', anchor='l')
ev('marker', S('C4_6', 0.2), E('C4_6', 0.8), lon=30.19, lat=50.60, kind='plane', color='ru', icon_color='white', label='호스토멜 공항', anchor='r', sub='공수부대 강하')
cam(S('C4_7', -0.6), 34.2, 50.6, 9.0, 3.0)
for p, nm in (('chernihiv', '체르니히우'), ('sumy', '수미'), ('kharkiv', '하르키우')):
    ev('marker', S('C4_7', 0.3), E('C4_7', 0.7), lon=PL[p][0], lat=PL[p][1], kind='dot', color='ru', label=nm, city=nm, encircle=True)
cam(S('C4_8', -0.6), 34.4, 46.6, 7.2, 3.0)
ev('marker', S('C4_8', 0.3), E('C4_8', 0.8), lon=32.62, lat=46.64, kind='dot', color='ru', label='헤르손', city='헤르손', sub='3.2 점령')
ev('marker', S('C4_8', 0.8), E('C4_8', 0.8), lon=35.37, lat=46.85, kind='dot', color='ru', label='멜리토폴', city='멜리토폴')
cam(S('C4_9', -0.6), 30.55, 50.5, 5.0, 2.8)
ev('marker', S('C4_9', 0.1), E('C4_10', 0.5), lon=30.52, lat=50.45, kind='shield', color='ua', label='키이우 방어', city='키이우', anchor='l')
cam(S('C4_11', -0.6), 30.3, 50.55, 2.6, 2.6)
ev('marker', S('C4_11', 0.3), E('C4_11', 0.8), lon=30.22, lat=50.54, kind='dot', color='ru', label='부차', sub='민간인 학살', anchor='l')
cam(S('C4_12', -0.8), 37.3, 47.2, 4.2, 3.0)
ev('marker', S('C4_12', 0.3), E('C4_12', 0.8), lon=37.55, lat=47.10, kind='dot', color='ru', label='마리우폴', city='마리우폴', encircle=True, sub='아조우스탈')
ev('card', S('C4_12', 0.5), E('C4_12', 0.8), kind='stat', tag='마리우폴 포위', big='86일', lines=['2022.02.24 – 05.20'], accent='ru')

# ------------------------------------------------------------ C5 Black Sea
cam(S('C5_1', -0.8), 32.6, 44.6, 13, 3.0)
ev('arrow', S('C5_2', 0.2), E('C5_2', 0.8), pts=[(33.3, 44.5), (32.0, 44.7), (30.45, 45.18)], color='ru', width=3.5, dashed=True, grow=1.5)
ev('marker', S('C5_2', 0.8), E('C5_4', 0.5), lon=30.20, lat=45.26, kind='star', color='ru', label='즈미이니섬', sub='“뱀섬”', anchor='r')
cam(S('C5_3', -0.6), 31.3, 45.7, 5.5, 3.0)
ev('marker', S('C5_3', 0.3), E('C5_3', 0.8), lon=30.93, lat=45.18, kind='ship', color='ru', icon_color='white', label='모스크바호', sub='2022.04.14 침몰', anchor='l')
ev('marker', S('C5_3', 2.2), E('C5_3', 0.8), lon=30.93, lat=45.18, kind='boom', color='orange', pulse=True)
note(S('C5_3'), E('C5_3', 0.6), '러시아는 모스크바호 침몰 원인을 화재로 발표했습니다')
ev('marker', S('C5_4', 0.3), E('C5_4', 0.8), lon=30.20, lat=45.26, kind='shield', color='ua', label='러시아군 철수', anchor='l', dy=18)
cam(S('C5_5', -0.8), 31.2, 43.6, 14, 3.0)
ev('marker', S('C5_5', 0.3), E('C5_6', 0.5), lon=28.98, lat=41.01, kind='doc', color='gold', label='이스탄불', sub='흑해 곡물 협정', city='이스탄불', anchor='l')
GRAIN = [(30.75, 46.40), (30.9, 45.8), (31.0, 44.8), (30.5, 43.6), (29.6, 42.3), (29.1, 41.3)]
COAST = [(30.75, 46.40), (30.35, 45.75), (29.95, 45.05), (29.1, 44.3), (28.85, 43.4), (28.35, 42.3), (29.1, 41.3)]
ev('line', S('C5_6', 0.0), E('C5_7', 0.4), pts=GRAIN, color='yellow', width=1.6, dash=[4, 5], dash_speed=10, draw=1.6)
ev('movers', S('C5_6', 0.3), E('C5_6', 0.7), pts=GRAIN, n=6, speed=0.08, color='yellow')
ev('line', S('C5_7', 0.8), E('C5_8', 0.2), pts=COAST, color='ua', width=2.0, draw=1.8, label='우크라이나 자체 회랑 (2023.8~)', label_at=(27.0, 43.3), anchor='r', label_size=11)
ev('movers', S('C5_7', 1.5), E('C5_7', 0.8), pts=COAST, n=6, speed=0.08, color='ua')
cam(S('C5_8', -0.8), 35.4, 44.9, 8.5, 3.0)
ev('marker', S('C5_8', 0.2), E('C5_9', 0.5), lon=33.52, lat=44.62, kind='drone', color='ua', label='세바스토폴 피격', anchor='r', city='세바스토폴')
ev('arrow', S('C5_8', 1.0), E('C5_9', 0.5), pts=[(33.8, 44.45), (35.6, 44.3), (37.55, 44.62)], color='ru', width=3.2, dashed=True, grow=1.8)
ev('marker', S('C5_8', 2.4), E('C5_9', 0.5), lon=37.77, lat=44.72, kind='ship', color='ru', icon_color='white', label='노보로시스크', city='노보로시스크', anchor='l')
ev('card', S('C5_9', 0.1), E('C5_9', 0.7), kind='info', tag='흑해의 역전', title='해상 드론 · 미사일', lines=['흑해함대, 크림 기지에서 후퇴', '서부 흑해 항로 회복'], accent='ua')

# ------------------------------------------------------------ C6 counteroffensives & attrition
cam(S('C6_1', -0.8), 37.0, 49.4, 5.8, 3.0)
for pts in ([(36.7, 49.55), (37.15, 49.62), (37.55, 49.72)], [(36.8, 49.45), (37.05, 49.33), (37.22, 49.22)]):
    ev('arrow', S('C6_1', 0.4), E('C6_2', 0.6), pts=pts, color='ua', width=5.0, grow=1.6)
ev('marker', S('C6_2', 0.2), E('C6_2', 0.8), lon=37.26, lat=49.21, kind='dot', color='ua', label='이지움', anchor='r')
ev('marker', S('C6_2', 0.5), E('C6_2', 0.8), lon=37.61, lat=49.71, kind='dot', color='ua', label='쿠피안스크', anchor='l')
cam(S('C6_3', -0.8), 35.6, 47.6, 12, 3.0)
ev('area', S('C6_3', 0.3), E('C6_4', 0.6), geom='annex4', style='redline', dash=[6, 4])
ev('card', S('C6_4', 0.2), E('C6_4', 0.8), kind='stat', tag='유엔 총회 2022.10.12', big='143', count_to=143, lines=['병합 규탄 결의 찬성국'], accent='ua')
cam(S('C6_5', -0.8), 33.0, 46.85, 5.5, 3.0)
ev('arrow', S('C6_5', 0.2), E('C6_5', 0.6), pts=[(33.4, 47.35), (33.0, 47.0), (32.68, 46.72)], color='ua', width=5.0, grow=1.5)
ev('marker', S('C6_5', 1.2), E('C6_6', 0.5), lon=32.62, lat=46.64, kind='shield', color='ua', label='헤르손 탈환', city='헤르손', anchor='r')
if 'DNIPRO' in G.get('lines', {}):
    dn = G['lines']['DNIPRO']
    import numpy as _np
    if hasattr(dn, 'coords'):
        pts = [tuple(c[:2]) for c in dn.coords]
    elif hasattr(dn, 'geoms'):
        pts = [tuple(c[:2]) for c in max(dn.geoms, key=lambda x: x.length).coords]
    else:
        arr = _np.asarray(dn[0] if _np.ndim(dn[0]) > 1 or (len(dn) and hasattr(dn[0][0], '__len__')) else dn, float)
        pts = [tuple(p[:2]) for p in arr]
    ev('line', S('C6_6', 0.0), E('C6_6', 0.7), pts=pts, color='water', width=2.2, curve=False, draw=1.6, label='드니프로강 전선', label_at=(33.6, 46.95), anchor='l', label_size=12)
cam(S('C6_7', -0.6), 37.2, 48.1, 9.0, 3.0)
ev('dots', S('C6_7', 0.2), E('C6_7', 0.6), pts=[(38.0, 48.6), (37.75, 48.14), (37.6, 47.8), (36.6, 47.5), (35.8, 47.4), (38.1, 49.1), (37.9, 49.6)], color='orange', r=2.8, stagger=1.8)
cam(S('C6_8', -0.6), 37.95, 48.55, 3.8, 2.8)
ev('marker', S('C6_8', 0.3), E('C6_8', 0.8), lon=38.00, lat=48.60, kind='boom', color='ru', label='바흐무트', sub='2023.05 함락', anchor='l')
cam(S('C6_9', -0.8), 33.0, 46.7, 4.6, 3.0)
ev('marker', S('C6_9', 0.2), E('C6_9', 0.8), lon=33.37, lat=46.78, kind='dam', color='water', label='카호우카 댐', anchor='l')
ev('area', S('C6_9', 0.8), E('C6_9', 1.6), geom='flood', style='water', grow=(33.37, 46.78), grow_dur=2.5)
note(S('C6_9'), E('C6_9', 0.6), '댐 파괴 책임을 두고 양측은 서로를 지목했습니다')
cam(S('C6_10', -0.6), 35.9, 47.45, 4.8, 3.0)
ev('arrow', S('C6_10', 0.3), E('C6_10', 0.8), pts=[(35.75, 47.75), (35.82, 47.58), (35.84, 47.47)], color='ua', width=5.0, grow=1.6, stop=True)
ev('marker', S('C6_10', 1.4), E('C6_10', 0.8), lon=35.84, lat=47.45, kind='dot', color='ua', label='로보티네', anchor='l')
cam(S('C6_11', -0.6), 37.55, 48.2, 4.6, 3.0)
ev('marker', S('C6_11', 0.3), E('C6_11', 0.8), lon=37.75, lat=48.14, kind='dot', color='ru', label='아우디이우카', anchor='l', sub='2024.02 함락')
cam(S('C6_12', -0.8), 35.4, 51.05, 4.6, 3.0)
ev('arrow', S('C6_12', 0.3), E('C6_12', 0.8), pts=[(35.05, 50.85), (35.2, 51.02), (35.3, 51.2)], color='ua', width=5.0, grow=1.4)
try:
    from shapely.geometry import Point as _Pt
    from shapely import affinity as _aff
    _rus = G['countries']['RUS']
    KURSK = _aff.scale(_Pt(35.28, 51.2).buffer(1, 64), 0.36, 0.21).intersection(_rus).buffer(0)
    if KURSK.is_empty or KURSK.area < 0.02:
        raise ValueError
except Exception:
    KURSK = SN['kursk'].buffer(0.04).buffer(-0.04)
ev('area', S('C6_12', 1.2), E('C6_13', 0.4), geom=KURSK, style='ua')
ev('marker', S('C6_12', 1.0), E('C6_12', 0.8), lon=35.27, lat=51.19, kind='dot', color='ua', label='수자', anchor='l', sub='쿠르스크주')
note(S('C6_12'), E('C6_13', 0.4), '쿠르스크 진격 범위는 개략입니다')
ev('card', S('C6_13', 0.3), E('C6_13', 0.7), kind='info', tag='2024.11 – 2025.04', title='북한군 투입', lines=['러시아, 쿠르스크 반격', '2025.4 “탈환 완료” 발표'], accent='ru')
cam(S('C6_14', -0.6), 37.2, 48.3, 5.0, 3.0)
ev('marker', S('C6_14', 0.3), E('C6_14', 0.8), lon=37.18, lat=48.28, kind='dot', color='ru', label='포크로우스크', anchor='r', city='포크로우스크')

# ------------------------------------------------------------ C7 negotiations & now
cam(S('C7_1', -0.8), 32.8, 48.8, 22, 3.0)
ev('card', S('C7_1', 0.2), E('C7_1', 0.6), kind='info', tag='2025', title='종전 협상 본격화', lines=['미국 트럼프 행정부 중재'], accent='gold')
ev('marker', S('C7_2', 0.1), E('C7_2', 0.8), lon=28.98, lat=41.01, kind='doc', color='gold', label='이스탄불', sub='2025.5 직접 회담', city='이스탄불', anchor='l')
ev('card', S('C7_2', 0.4), E('C7_2', 0.8), kind='info', tag='2025.08.15', title='알래스카 정상회담', lines=['트럼프 – 푸틴', '합의 없이 종료'], accent='gold')
ev('card', S('C7_3', 0.2), E('C7_3', 0.6), kind='info', tag='2026.01–02', title='3자 회담 (UAE · 스위스)', lines=['미국 · 우크라이나 · 러시아', '돌파구 없음'], accent='gold')
cam(S('C7_4', -0.8), 37.6, 48.45, 6.0, 3.0)
ev('area', S('C7_4', 0.6), E('C7_4', 0.8), geom=DONETSK_FREE, style='amber', pulse=True)
ev('marker', S('C7_4', 1.0), E('C7_4', 0.8), lon=37.56, lat=48.72, kind='dot', color='orange', label='크라마토르스크', anchor='l', sub='러시아 요구 지역')
cam(S('C7_5', -0.8), 36.2, 47.85, 5.2, 3.0)
ev('arrow', S('C7_5', 0.4), E('C7_5', 0.8), pts=[(35.9, 48.1), (36.1, 47.95), (36.3, 47.82)], color='ua', width=5.0, grow=1.6)
cam(S('C7_6', -0.8), 35.4, 45.6, 9.0, 3.0)
for src in ((31.0, 46.9), (33.5, 47.6), (35.2, 47.9)):
    ev('arrow', S('C7_6', 0.4), E('C7_6', 0.5), pts=[src, ((src[0] + 37.7) / 2, (src[1] + 44.8) / 2 + 0.3), (37.7, 44.78)], color='ua', width=2.6, dashed=True, grow=2.0)
ev('marker', S('C7_6', 2.0), E('C7_6', 0.6), lon=37.77, lat=44.72, kind='boom', color='orange', label='노보로시스크', city='노보로시스크', anchor='l', sub='정유·수출 시설')
# timelapse camera
cam(TL_START - 0.6, 34.6, 48.1, 14.0, 2.4)
cam(S('C7_7', -0.4), 33.0, 48.4, 20.0, 3.0)
ev('card', S('C7_7', 0.3), E('C7_7', 0.9), kind='stat', tag='2026.09 · DeepState', big='%.1f%%' % PCT.get('ds_2026-09-26', 19.3), lines=['러시아 통제 면적', '크림반도 포함, 우크라이나 대비'], accent='ru')
ev('card', S('C7_8', 0.2), E('C7_8', 0.7), kind='stat', tag='유엔 확인 · 2026.08', big='16,874', count_to=16874, lines=['우크라이나 민간인 사망자', '실제는 더 많을 수 있음'], accent='ru')
ev('card', S('C7_9', 0.2), E('C7_9', 0.8), kind='info', tag='2026.09', title='협상 재개 움직임', lines=['미국 특사단 양국 방문', '10월 UAE 3자 회담 추진'], accent='gold')

# ------------------------------------------------------------ epilogue
cam(S('E1', -0.6), 34.2, 46.2, 14.0, 4.0)
cam(S('E3', -0.4), 33.4, 47.2, 25.0, 9.0)

# ------------------------------------------------------------ static labels (name, lon, lat, kind, minw, maxw[, anchor])
STATIC_LABELS = [
    ('러시아', 39.5, 52.6, 'country', 7, 40), ('벨라루스', 28.0, 53.2, 'country', 7, 40), ('폴란드', 20.8, 51.8, 'country', 9, 40),
    ('루마니아', 24.8, 45.9, 'country', 9, 40), ('몰도바', 28.5, 47.3, 'country', 7, 16), ('튀르키예', 33.5, 40.4, 'country', 9, 40),
    ('불가리아', 25.3, 42.7, 'country', 9, 40), ('조지아', 43.6, 42.3, 'country', 9, 40), ('우크라이나', 31.2, 49.4, 'region', 12, 40),
    ('흑 해', 34.0, 43.3, 'sea', 5, 40), ('아조우해', 36.7, 46.25, 'sea', 2.5, 14), ('크림반도', 34.2, 45.45, 'region', 2.5, 11),
    ('돈바스', 38.9, 48.4, 'region', 4, 14),
    ('키이우', 30.52, 50.45, 'city', 0, 40, 'l'), ('하르키우', 36.23, 49.99, 'city', 0, 30, 'l'), ('오데사', 30.72, 46.48, 'city', 0, 30, 'l'),
    ('리비우', 24.03, 49.84, 'city', 0, 30, 'l'), ('드니프로', 35.05, 48.46, 'city', 0, 30, 'l'), ('도네츠크', 37.80, 48.02, 'city', 0, 30, 'b'),
    ('세바스토폴', 33.52, 44.62, 'city', 0, 30, 'r'), ('모스크바', 37.62, 55.75, 'city', 0, 40, 'l'), ('민스크', 27.56, 53.90, 'city', 0, 40, 'l'),
    ('이스탄불', 28.98, 41.01, 'city', 0, 40, 'r'), ('자포리자', 35.14, 47.84, 'city', 0, 14, 'l'), ('루한스크', 39.31, 48.57, 'city', 0, 14, 'l'),
    ('마리우폴', 37.55, 47.10, 'city', 0, 14, 'l'), ('헤르손', 32.62, 46.64, 'city', 0, 14, 'r'), ('미콜라이우', 32.00, 46.98, 'city', 0, 12, 't'),
    ('멜리토폴', 35.37, 46.85, 'city', 0, 12, 'b'), ('심페로폴', 34.10, 44.95, 'city', 0, 12, 'l'), ('케르치', 36.47, 45.36, 'city', 0, 10, 'l'),
    ('노보로시스크', 37.77, 44.72, 'city', 0, 16, 'l'), ('로스토프나도누', 39.72, 47.24, 'city', 0, 14, 'l'), ('수미', 34.80, 50.91, 'city', 0, 14, 'l'),
    ('체르니히우', 31.29, 51.50, 'city', 0, 14, 'l'), ('크라마토르스크', 37.56, 48.72, 'city', 0, 8, 'l'), ('슬로뱐스크', 37.61, 48.85, 'city', 0, 8, 'l'),
    ('바흐무트', 38.00, 48.60, 'city', 0, 7, 'r'), ('포크로우스크', 37.18, 48.28, 'city', 0, 7, 'r'), ('벨고로드', 36.59, 50.60, 'city', 0, 10, 'l'),
    ('쿠르스크', 36.19, 51.73, 'city', 0, 10, 'l'), ('콘스탄차', 28.65, 44.17, 'city', 0, 16, 'r'),
]

# ------------------------------------------------------------ time helpers
CARD_WIN = [(c[0], c[1]) for c in TL.CARDS]


def _card_cover(t):
    m = 0.0
    for t0, t1 in CARD_WIN:
        if t0 - 0.6 <= t <= t1 + 0.6:
            m = max(m, min(1.0, (t - t0 + 0.6) / 0.6, (t1 + 0.6 - t) / 0.6))
    return max(0.0, min(1.0, m))


def label_alpha(t):
    a = 1.0 - 0.85 * _card_cover(t)
    if TL_START <= t <= TL_END:
        a *= 0.7
    return a


def ua_glow(t):
    if t < TL.T['P2'] - 0.5:
        return 0.35
    if t < TL.T['P2'] + 2.0:
        return 0.35 + 0.55 * (t - TL.T['P2'] + 0.5) / 2.5
    return 0.9 if t < TL.T['C1_1'] else 0.65


def current_sentence(t):
    cur = None
    for sid in TL.ORDER:
        if TL.T[sid] - 0.3 <= t:
            cur = sid
        else:
            break
    if cur is None:
        return None
    a = 1.0 - _card_cover(t)
    if TL.TE['C7_6'] + 0.8 < t < TL.T['C7_7'] - 0.4:
        a = 0.0
    if TL.SENT[cur]['chapter'] in ('P',):
        a = 0.0
    return cur, max(0.0, a)


_DCHG = []
_prev = None
for _sid in TL.ORDER:
    d = TL.SENT[_sid]['date']
    if d != _prev:
        _DCHG.append(TL.T[_sid] - 0.3); _prev = d


def date_changed_at(t):
    last = 0.0
    for x in _DCHG:
        if x <= t:
            last = x
    return last


_YR = [(TL.T[s], TL.SENT[s]['year']) for s in TL.ORDER if TL.SENT[s]['year'] is not None]


def smooth_year(t):
    if t <= _YR[0][0]:
        return _YR[0][1]
    prev_t, prev_y = _YR[0]
    for tt, yy in _YR[1:]:
        if tt > t:
            break
        prev_t, prev_y, last_y = tt, yy, prev_y
    # find year before prev
    idx = [x[0] for x in _YR].index(prev_t)
    y0 = _YR[idx - 1][1] if idx > 0 else prev_y
    f = min(1.0, (t - prev_t) / 1.2)
    f = f * f * (3 - 2 * f)
    return y0 + (prev_y - y0) * f

END_LINES = [
    '지도: Natural Earth · 지형: AWS Terrain Tiles (Mapzen)',
    '점령지 경계: DeepState 월별 자료(2022.10–2026.9) · 그 이전은 개략',
    '자료: 유엔 · 영국 하원 도서관 · Russia Matters · ISW 등',
    '크림반도는 국제적으로 인정된 우크라이나 영토로 표시했습니다',
    '내레이션: AI 음성 합성 · 음악: 자체 제작',
    '2026년 9월 26일 기준',
]
