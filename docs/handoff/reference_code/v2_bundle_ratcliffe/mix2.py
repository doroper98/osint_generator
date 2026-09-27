import json, subprocess, numpy as np
from scipy.signal import lfilter

V = '/home/claude/v2'
P = json.load(open(f'{V}/plan.json'))
SR = 44100; TOT = P['total'] + 0.5; N = int(TOT * SR)
rng = np.random.default_rng(3)
BGM = '/home/claude/og/hyperframes/briefing/assets/audio/bgm/The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3'
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', BGM, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
bg = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
print('bgm seconds', len(bg) / SR)
# loop with 4 s crossfade if needed
xf = 4 * SR
while len(bg) < N:
    tail, head = bg[-xf:], bg[:xf]
    r = np.linspace(0, 1, xf)[:, None]
    bg = np.concatenate([bg[:-xf], tail * (1 - r) + head * r, bg[xf:]])
bg = bg[:N]
bg /= (np.abs(bg).max() + 1e-6)

S = {x['sid']: x for x in P['sentences']}
C = P['sec_start']
# intensity keyframes (section-level dramaturgy)
K = [(0, 0.55), (C['s1'], 0.6), (C['s2'], 0.62), (C['s3'], 0.5), (C['s5'], 0.58), (C['s7'], 0.72), (C['s8'], 0.55),
     (C['s9'], 0.68), (C['s10'], 0.5), (C['s12'], 0.6), (C['outro'], 0.7), (TOT - 7, 0.62), (TOT, 0.0)]
tt = np.arange(N) / SR
inten = np.interp(tt, [k[0] for k in K], [k[1] for k in K]).astype(np.float32)

vo = np.zeros(N, np.float32); duck = np.zeros(N, np.float32)
for x in P['sentences']:
    a = np.load(x['npy']).astype(np.float32); a = a / (np.abs(a).max() + 1e-6) * 0.8
    i0 = int(x['t0'] * SR); n = min(len(a), N - i0); vo[i0:i0 + n] += a[:n]
    duck[max(0, int((x['t0'] - 0.25) * SR)):min(N, int((x['t1'] + 0.3) * SR))] = 1
kn = int(0.35 * SR); duck = np.convolve(duck, np.ones(kn, np.float32) / kn, mode='same')
bed_gain = inten * (1 - 0.6 * duck) * 0.33

fx = np.zeros(N, np.float32)


def add(t, y):
    i0 = int(t * SR)
    if i0 < 0 or i0 >= N: return
    n = min(len(y), N - i0); fx[i0:i0 + n] += y[:n]


def whoosh(t_end, dur=1.2, v=1.0):
    n = int(dur * SR); ti = np.arange(n) / SR; nz = rng.standard_normal(n)
    a = np.clip(ti / dur, 0, 1) ** 2.2
    y = (lfilter([0.08], [1, -0.92], nz) * (1 - a) * 0.6 + (nz - lfilter([0.3], [1, -0.7], nz)) * a * 0.25) * a
    y *= np.exp(-np.maximum(0, ti - dur + 0.08) / 0.05)
    add(t_end - dur, (y * 0.2 * v).astype(np.float32))


def boom(t, v=1.0):
    n = int(2.6 * SR); ti = np.arange(n) / SR
    f = 34 + 44 * np.exp(-ti / 0.25); ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-ti / 0.8) * 0.55 + lfilter([0.02], [1, -0.98], rng.standard_normal(n)) * np.exp(-ti / 0.3) * 0.6
    add(t, (y * v).astype(np.float32))


def tick(t, v=1.0):
    n = int(0.12 * SR); ti = np.arange(n) / SR
    add(t, (np.sin(2 * np.pi * 1800 * ti) * np.exp(-ti / 0.015) * 0.18 * v).astype(np.float32))


for c in P['cards']:
    if c['kind'] == 'title': whoosh(c['t0'] + 0.2, 1.4, 1.0); boom(c['t0'] + 0.2, 0.6)
for sec, t0 in C.items():
    if sec.startswith('s'): whoosh(t0 - 0.05, 0.9, 0.6)
boom(S['s1_1']['t1'] + 0.6, 0.55)
boom(S['s7_2']['t0'] + 0.1, 0.35)
for k in range(4): tick(C['s12'] + 0.8 + k * 0.7, 1.0)

fade = np.ones(N, np.float32); fi = int(1.2 * SR); fo = int(4 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
L = (bg[:, 0] * bed_gain + fx * (1 - 0.25 * duck) + vo) * fade
R = (bg[:, 1] * bed_gain + fx * (1 - 0.25 * duck) + vo) * fade
pk = max(np.abs(L).max(), np.abs(R).max())
if pk > 0.97: L /= pk / 0.97; R /= pk / 0.97
np.stack([L, R], 1).astype(np.float32).tofile(f'{V}/mix.f32')
print('mix ok', round(N / SR, 1), 'peak', round(float(pk), 3))
