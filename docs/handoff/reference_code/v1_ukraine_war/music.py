"""Original procedural score (D minor), SFX, narration placement and ducking -> mix.f32 (stereo, 44.1k)."""
import numpy as np, json
from scipy.signal import oaconvolve, lfilter
import timeline as TL

SR = 44100
TOT = TL.TOTAL + 0.5
N = int(TOT * SR)
rng = np.random.default_rng(7)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)      # music bus
FX_L = np.zeros(N, np.float32); FX_R = np.zeros(N, np.float32)  # sfx bus (less ducked)


def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, x):
    i0 = int(start * SR)
    if i0 >= N:
        return
    if i0 < 0:
        x = x[-i0:]; i0 = 0
    n = min(len(x), N - i0)
    buf[i0:i0 + n] += x[:n]


# ---------------------------------------------------------------- intensity curve
def S(s): return TL.T[s]
def E(s): return TL.TE[s]


KEYS = [(0, 0.30), (S('C3_8'), 0.32), (S('C3_9'), 0.48), (S('C4_2'), 0.78), (S('C4_9'), 0.62), (S('C5_1'), 0.55),
        (S('C6_1'), 0.72), (S('C6_7'), 0.62), (S('C7_1'), 0.48), (E('C7_6'), 0.62), (S('C7_7') - 1.5, 1.0),
        (S('C7_7'), 0.5), (S('E1'), 0.42), (TOT - 6, 0.36), (TOT, 0.0)]


def inten(t):
    kt = np.array([k[0] for k in KEYS]); kv = np.array([k[1] for k in KEYS])
    return np.interp(t, kt, kv)


# ---------------------------------------------------------------- chords
CH = {
    'Dm': ([50, 53, 57, 62], 38), 'Bb': ([50, 53, 58, 62], 34), 'F': ([48, 53, 57, 60], 41),
    'C': ([48, 52, 55, 60], 36), 'Gm': ([50, 55, 58, 62], 43), 'A': ([49, 52, 57, 61], 45),
}
PROG = ['Dm', 'Bb', 'F', 'C', 'Dm', 'Bb', 'Gm', 'A']
CL = 8.0
XF = 2.5
seg_n = int((CL + XF) * SR)
ts = np.arange(seg_n, dtype=np.float32) / SR
env = np.ones(seg_n, np.float32)
fi = int(XF * SR)
env[:fi] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi))
env[-fi:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fi))

k = 0
t0 = 0.0
while t0 < TOT:
    notes, bass = CH[PROG[k % len(PROG)]]
    I = float(inten(t0 + CL / 2))
    padL = np.zeros(seg_n, np.float32); padR = np.zeros(seg_n, np.float32)
    for vi, m in enumerate(notes):
        f = mf(m)
        for n in range(1, 7):
            amp = (1.0 / n ** 1.7) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.05 * (ts + t0) + n * 1.3 + vi))
            if n > 3:
                amp = amp * (0.35 + 0.9 * I)
            ph = rng.uniform(0, 6.28)
            padL += (amp * np.sin(2 * np.pi * f * n * 0.9988 * ts + ph)).astype(np.float32)
            padR += (amp * np.sin(2 * np.pi * f * n * 1.0012 * ts + ph + 0.7)).astype(np.float32)
    fb = mf(bass)
    sub = (np.sin(2 * np.pi * fb * ts) + 0.35 * np.sin(2 * np.pi * fb * 2 * ts) + 0.12 * np.sin(2 * np.pi * fb * 3 * ts)).astype(np.float32)
    g = 0.030 * (0.55 + 0.6 * I)
    add(L, t0 - XF / 2, (padL * g + sub * 0.05 * (0.6 + 0.5 * I)) * env)
    add(R, t0 - XF / 2, (padR * g + sub * 0.05 * (0.6 + 0.5 * I)) * env)

    # ostinato pulse in tense sections
    if I > 0.5:
        step = 0.375
        arp = [notes[0] + 12, notes[2] + 12, notes[1] + 12, notes[2] + 12]
        pn = int(0.6 * SR); tp = np.arange(pn) / SR
        pe = np.exp(-tp / 0.16).astype(np.float32)
        nsteps = int(CL / step)
        for j in range(nsteps):
            tt = t0 + j * step
            m = arp[j % 4] - 12 * (j % 8 >= 4 and I < 0.7)
            f = mf(m)
            p = (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(2 * np.pi * 2 * f * tp)) * pe
            vol = 0.045 * (I - 0.45) * (1.25 if j % 4 == 0 else 0.8)
            pan = 0.35 if j % 2 else -0.35
            add(L, tt, (p * vol * (1 - pan)).astype(np.float32)); add(R, tt, (p * vol * (1 + pan)).astype(np.float32))
        # low heartbeat on beats
        if I > 0.68:
            hn = int(0.5 * SR); th = np.arange(hn) / SR
            kick = (np.sin(2 * np.pi * (48 + 40 * np.exp(-th / 0.03)) * th) * np.exp(-th / 0.12)).astype(np.float32)
            for j in range(int(CL / 0.75)):
                v = 0.10 * (I - 0.6)
                add(L, t0 + j * 0.75, kick * v); add(R, t0 + j * 0.75, kick * v)
    # bell shimmer in calm sections
    if I < 0.5:
        bn = int(3.5 * SR); tb = np.arange(bn) / SR
        for j in range(2):
            m = notes[(k + j * 2) % 4] + 24
            f = mf(m)
            b = ((np.sin(2 * np.pi * f * tb) + 0.25 * np.sin(2 * np.pi * f * 2.76 * tb)) * np.exp(-tb / 1.1)).astype(np.float32)
            tt = t0 + 1.0 + j * 4.0 + rng.uniform(-0.2, 0.2)
            pan = rng.uniform(-0.6, 0.6)
            add(L, tt, b * 0.018 * (1 - pan)); add(R, tt, b * 0.018 * (1 + pan))
    t0 += CL; k += 1

# ---------------------------------------------------------------- reverb on music bus
irn = int(2.8 * SR)
tir = np.arange(irn) / SR
irL = (rng.standard_normal(irn) * np.exp(-tir / 0.75)).astype(np.float32)
irR = (rng.standard_normal(irn) * np.exp(-tir / 0.75)).astype(np.float32)
irL[:int(0.02 * SR)] = 0; irR[:int(0.02 * SR)] = 0
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
wetL = oaconvolve(L, irL)[:N].astype(np.float32); wetR = oaconvolve(R, irR)[:N].astype(np.float32)
L = L * 0.75 + wetL * 0.55; R = R * 0.75 + wetR * 0.55
del wetL, wetR


# ---------------------------------------------------------------- SFX
def boom(t, v=1.0):
    n = int(3.0 * SR); tt = np.arange(n) / SR
    f = 34 + 46 * np.exp(-tt / 0.25)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-tt / 0.9)
    nz = lfilter([0.02], [1, -0.98], rng.standard_normal(n)) * np.exp(-tt / 0.35)
    y = (x * 0.55 + nz * 0.6).astype(np.float32) * v
    add(FX_L, t, y); add(FX_R, t, y)


def whoosh(t_end, dur=1.4, v=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    a = np.clip(tt / dur, 0, 1) ** 2.2
    lp = lfilter([0.08], [1, -0.92], nz)
    hp = nz - lfilter([0.3], [1, -0.7], nz)
    y = (lp * (1 - a) * 0.6 + hp * a * 0.25) * a * np.exp(-np.maximum(0, tt - dur + 0.08) / 0.05)
    y = (y * 0.22 * v).astype(np.float32)
    add(FX_L, t_end - dur, y * 0.9); add(FX_R, t_end - dur, y)


for (c0, c1, kind, key) in TL.CARDS:
    if kind in ('chapter', 'title'):
        whoosh(c0 + 0.15, 1.3, 0.9)
        boom(c0 + 0.15, 0.55 if kind == 'chapter' else 0.7)
boom(S('C4_2') + 0.25, 1.0)
boom(S('C5_3') + 2.2, 0.45)
boom(S('C6_8') + 0.3, 0.35)
boom(S('C7_6') + 2.0, 0.4)
whoosh(S('C7_7') - 0.3, 2.0, 0.8)

# ---------------------------------------------------------------- narration + ducking
DURS = json.load(open('/home/claude/tts/durs.json'))
VO = np.zeros(N, np.float32)
duck = np.zeros(N, np.float32)
for sid in TL.ORDER:
    x = np.load(f'/home/claude/tts/{sid}.npy').astype(np.float32)
    x = x / (np.abs(x).max() + 1e-6) * 0.78
    add(VO, TL.T[sid], x)
    i0 = int((TL.T[sid] - 0.25) * SR); i1 = int((TL.TE[sid] + 0.3) * SR)
    duck[max(0, i0):min(N, i1)] = 1.0
kn = int(0.35 * SR)
duck = np.convolve(duck, np.ones(kn, np.float32) / kn, mode='same')
mg = (1.0 - 0.52 * duck).astype(np.float32)
fg = (1.0 - 0.25 * duck).astype(np.float32)

# global fade in/out
fade = np.ones(N, np.float32)
fin = int(1.5 * SR); fout = int(4.0 * SR)
fade[:fin] = np.linspace(0, 1, fin); fade[-fout:] = np.linspace(1, 0, fout)

outL = (L * mg * 1.0 + FX_L * fg + VO) * fade
outR = (R * mg * 1.0 + FX_R * fg + VO) * fade
pk = max(np.abs(outL).max(), np.abs(outR).max())
print('peak', pk, 'music rms', float(np.sqrt((L ** 2).mean())), 'vo rms', float(np.sqrt((VO[VO != 0] ** 2).mean())))
if pk > 0.97:
    outL /= pk / 0.97; outR /= pk / 0.97
np.stack([outL, outR], 1).astype(np.float32).tofile('/home/claude/mix.f32')
print('seconds', N / SR)
