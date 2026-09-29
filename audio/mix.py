"""오디오 믹스 CLI (v2.1.0, mix3 분해, 10 §2~§5).

    python -m audio.mix <proj>   → <proj>/out/mix.f32 (44.1kHz 스테레오 float32)

베드 이득·덕킹·피크는 `rules/video_rules.yaml audio`(15 P3). v4.6.0(D-0097, 사용자 결정 D86): 베드는 정규화 전에
`process_bed` 저음 보강(로우 셸프·서브 옥타브 층·장면 시작 스웰, `rules audio.bed_bass`)을 거친다. 음악이 있으면
처리 전·후 베드 저역 비율을 `out/bed_stats.json` 에 남긴다(측정은 audio/qa.py 한 경로). 장면별 음악 강도·BGM 파일·추가 효과음 큐는
프로젝트 연출(`direction.yaml` 의 `sound:` 블록, v3.1.0)이 준다. 기본 효과음 규칙(sfx_policy): 타이틀 카드 휙+쿵, 장면 시작 휙.
난수 시드 3, 효과음 생성 순서도 v3 와 같다(결정성).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from scipy.signal import butter, lfilter, sosfilt

from audio.qa import bed_stats
from audio.registry import BgmError, bgm_path
from rules import load_rules
from script.schema import Plan

SR = 44100               # 코덱 상수(ffmpeg -ar) — rules audio.sample_rate 와 같아야 한다(테스트)
AU = load_rules().audio  # 수치 SSOT(D-0060 §0, 15 P3) — 값은 v3 그대로
FX = AU.sfx
REPO = Path(__file__).resolve().parent.parent


class Cue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str            # whoosh | boom | tick
    t: float
    v: float = 1.0
    dur: float | None = None   # whoosh 길이


class BgmSeg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    t: float                                   # 이 곡이 시작하는 시각(앵커 해석 뒤)


class Sound(BaseModel):
    """프로젝트 사운드 연출 — direction.yaml `sound:` 블록(앵커 해석 뒤, v3.1.0 D-0047 §0-2)."""

    model_config = ConfigDict(extra="forbid")

    bgm: str | list[BgmSeg] | None             # BGM 레지스트리 id(v3.4.0) 또는 곡 교체 목록. None = 음악 없음(F1, 명시 상태)
    intensity: list[tuple[float, float]] = Field(min_length=2)   # (초, 강도) 키프레임
    cues: list[Cue] = Field(default_factory=list)


class Sfx:
    def __init__(self, n: int, rng: np.random.Generator) -> None:
        self.fx = np.zeros(n, np.float32)
        self.n = n
        self.rng = rng

    def add(self, t: float, y: np.ndarray) -> None:
        i0 = int(t * SR)
        if i0 < 0 or i0 >= self.n:
            return
        n = min(len(y), self.n - i0)
        self.fx[i0:i0 + n] += y[:n]

    def whoosh(self, t_end: float, dur: float = FX.whoosh.dur_sec, v: float = 1.0) -> None:
        W = FX.whoosh  # noqa: N806
        n = int(dur * SR)
        ti = np.arange(n) / SR
        nz = self.rng.standard_normal(n)
        a = np.clip(ti / dur, 0, 1) ** W.shape_pow
        y = (lfilter([W.low_b], [1, W.low_a], nz) * (1 - a) * W.low_gain + (nz - lfilter([W.high_b], [1, W.high_a], nz)) * a * W.high_gain) * a
        y *= np.exp(-np.maximum(0, ti - dur + W.release_sec) / W.release_tau_sec)
        self.add(t_end - dur, (y * W.gain * v).astype(np.float32))

    def boom(self, t: float, v: float = 1.0) -> None:
        B = FX.boom  # noqa: N806
        n = int(B.dur_sec * SR)
        ti = np.arange(n) / SR
        f = B.f0_hz + B.sweep_hz * np.exp(-ti / B.sweep_tau_sec)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = (np.sin(ph) * np.exp(-ti / B.tone_tau_sec) * B.tone_gain
             + lfilter([B.noise_b], [1, B.noise_a], self.rng.standard_normal(n)) * np.exp(-ti / B.noise_tau_sec) * B.noise_gain)
        self.add(t, (y * v).astype(np.float32))

    def tick(self, t: float, v: float = 1.0) -> None:
        T = FX.tick  # noqa: N806
        n = int(T.dur_sec * SR)
        ti = np.arange(n) / SR
        self.add(t, (np.sin(2 * np.pi * T.freq_hz * ti) * np.exp(-ti / T.tau_sec) * T.gain * v).astype(np.float32))

    def cue(self, c: Cue) -> None:
        if c.kind == "whoosh":
            self.whoosh(c.t, c.dur if c.dur is not None else FX.whoosh.dur_sec, c.v)
        elif c.kind == "boom":
            self.boom(c.t, c.v)
        elif c.kind == "tick":
            self.tick(c.t, c.v)
        else:
            raise ValueError(f"모르는 효과음 종류: {c.kind!r}")


def decode_bgm(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"BGM 없음: {path} — `python tools/fetch_data.py bgm`")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def low_shelf_ba(freq_hz: float, gain_db: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """로우 셸프 biquad 계수(RBJ Audio EQ Cookbook). DC 이득 = gain_db, 고역 이득 = 0 dB. a[0] = 1 로 정규화."""
    A = 10 ** (gain_db / (2 * 20))  # noqa: N806 — 쿡북 표기(진폭 제곱근)
    w0 = 2 * np.pi * freq_hz / SR
    cs, sa = np.cos(w0), 2 * np.sqrt(A) * np.sin(w0) / (2 * q)
    b = np.array([A * ((A + 1) - (A - 1) * cs + sa), 2 * A * ((A - 1) - (A + 1) * cs), A * ((A + 1) - (A - 1) * cs - sa)])
    a = np.array([(A + 1) + (A - 1) * cs + sa, -2 * ((A - 1) + (A + 1) * cs), (A + 1) + (A - 1) * cs - sa])
    return b / a[0], a / a[0]


def envelope(x: np.ndarray) -> np.ndarray:
    """원 대역 포락선: 블록 RMS×√2(사인 진폭) → attack/release 추종(블록 단위) → 샘플로 선형 보간. 결정적."""
    S = AU.bed_bass.sub  # noqa: N806
    blk = max(1, int(S.env_block_sec * SR))
    k = -(-len(x) // blk)
    pad = np.zeros(k * blk, np.float64)
    pad[:len(x)] = x
    v = np.sqrt(np.mean(pad.reshape(k, blk) ** 2, 1) * 2)
    ca, cr = np.exp(-S.env_block_sec / S.env_attack_sec), np.exp(-S.env_block_sec / S.env_release_sec)
    env = np.empty(k)
    e = 0.0
    for i, vi in enumerate(v.tolist()):
        c = ca if vi > e else cr
        e = c * e + (1 - c) * vi
        env[i] = e
    return np.interp(np.arange(len(x)), np.arange(k) * blk + (blk - 1) / 2, env)


def swell_gain(n: int, starts: list[float]) -> np.ndarray:
    """서브 층 이득: 각 시각에서 1+depth 로 올랐다가 sec 동안 선형으로 1(겹치면 큰 값). starts 는 이미 첫 장면을 뺀 시각."""
    W = AU.bed_bass.swell  # noqa: N806
    g = np.ones(n)
    m = int(W.sec * SR)
    ramp = 1 + W.depth * (1 - np.arange(m) / m)
    for t in starts:
        i0 = int(round(t * SR))
        if i0 < 0 or i0 >= n:
            continue
        i1 = min(n, i0 + m)
        g[i0:i1] = np.maximum(g[i0:i1], ramp[:i1 - i0])
    return g


def sub_octave(mono: np.ndarray, gain: np.ndarray) -> np.ndarray:
    """곡 저음의 한 옥타브 아래: 밴드패스 → 상승 영교차마다 부호 토글(2분주 사각파) → 로우패스 → × 포락선 × gain·스웰."""
    S = AU.bed_bass.sub  # noqa: N806
    band = sosfilt(butter(S.filter_order, S.band_hz, btype="bandpass", fs=SR, output="sos"), mono)
    pos = band >= 0
    up = np.zeros(len(band), bool)
    up[1:] = pos[1:] & ~pos[:-1]
    sq = np.where(np.cumsum(up) % 2 == 1, 1.0, -1.0)
    sq = sosfilt(butter(S.filter_order, S.out_lp_hz, btype="lowpass", fs=SR, output="sos"), sq)
    return sq * envelope(band) * S.gain * gain


def process_bed(bg: np.ndarray, scene_starts: list[float]) -> np.ndarray:
    """베드 저음 보강(v4.6.0 D-0097): 로우 셸프 → 서브 옥타브 층(scene_starts 에서 스웰) 합산. 정규화 전 단계.
    scene_starts = 이 베드 시간축의 스웰 시각(호출자가 첫 장면을 뺀다)."""
    sh = AU.bed_bass.shelf
    b, a = low_shelf_ba(sh.freq_hz, sh.gain_db, sh.q)
    y = lfilter(b, a, bg.astype(np.float64), axis=0)
    sub = sub_octave(y.mean(1), swell_gain(len(y), scene_starts))
    return (y + sub[:, None]).astype(np.float32)


def bed(bg: np.ndarray, n: int, scene_starts: list[float] | None = None) -> np.ndarray:
    """루프·자르기 → (scene_starts 가 있으면 process_bed, 정규화 기준 norm_ref) → 피크 정규화. None = 저음 보강 전 베드(측정용 '처리 전')."""
    xf = int(AU.loop_xfade_sec * SR)
    while len(bg) < n:
        tail, head = bg[-xf:], bg[:xf]
        r = np.linspace(0, 1, xf)[:, None]
        bg = np.concatenate([bg[:-xf], tail * (1 - r) + head * r, bg[xf:]])
    bg = bg[:n]
    if scene_starts is None:
        return bg / (np.abs(bg).max() + AU.norm_eps)
    pre = float(np.abs(bg).max())
    bg = process_bed(bg, scene_starts)
    k = AU.bed_bass.norm_ref   # D-0102 2-C — 정규화 기준 = 처리 전 피크^(1−k) × 처리 후 피크^k
    return bg / (pre ** (1 - k) * float(np.abs(bg).max()) ** k + AU.norm_eps)


def crossfade_weights(starts: list[float], n: int) -> np.ndarray:
    """곡 k 의 가중치(곡 수 × n). 경계 t 를 가운데로 crossfade_sec 동안 앞 곡 1→0, 뒤 곡 0→1(선형, 매 샘플 합 1)."""
    w = np.zeros((len(starts), n), np.float32)
    half = AU.crossfade_sec / 2
    tt = np.arange(n) / SR
    for k in range(len(starts)):
        up = np.ones(n, np.float32) if k == 0 else np.clip((tt - (starts[k] - half)) / AU.crossfade_sec, 0, 1)
        down = np.ones(n, np.float32) if k == len(starts) - 1 else 1 - np.clip((tt - (starts[k + 1] - half)) / AU.crossfade_sec, 0, 1)
        w[k] = np.minimum(up, down)
    return w


def segment_bed(segs: list[tuple[float, np.ndarray]], n: int, scene_starts: list[float] | None = None) -> np.ndarray:
    """곡 교체 베드: 곡마다 자기 시작 − crossfade_sec/2 에서 곡 처음부터 재생(루프 포함), 교차 페이드 가중합.
    scene_starts(전체 시간축 스웰 시각)가 있으면 곡마다 자기 시간축으로 옮겨 process_bed 를 거친다."""
    starts = [t for t, _ in segs]
    for a, b in zip(starts, starts[1:]):
        if b - a < AU.crossfade_sec:
            raise ValueError(f"곡 교체 간격 {b - a:.2f}s < crossfade_sec {AU.crossfade_sec}s")
    w = crossfade_weights(starts, n)
    out = np.zeros((n, 2), np.float32)
    for k, (t, raw) in enumerate(segs):
        s0 = 0 if k == 0 else max(0, int((t - AU.crossfade_sec / 2) * SR))
        local = None if scene_starts is None else [t - s0 / SR for t in scene_starts if t * SR >= s0]
        out[s0:] += bed(raw, n - s0, local) * w[k, s0:, None]
    return out


def mix(plan: Plan, sound: Sound, bg_raw: np.ndarray | list[tuple[float, np.ndarray]] | None,
        stats: dict | None = None) -> tuple[np.ndarray, float]:
    """(N×2 float32, 정규화 전 피크). bg_raw None = 베드 없음(sound.bgm null) — 내레이션+효과음만(폴백이 아니라 명시 상태).
    stats 가 dict 이고 베드가 있으면 처리 전·후 베드 저역 비율(audio.qa.bed_stats)을 채운다(믹서가 out/bed_stats.json 에 쓴다)."""
    A = AU  # noqa: N806
    tot = plan.total + A.tail_sec
    n = int(tot * SR)
    rng = np.random.default_rng(A.seed)
    swell = list(plan.scene_start.values())[1:]   # 장면 시작 스웰(첫 장면 제외, D-0097 §3)
    if bg_raw is None:
        bg = np.zeros((n, 2), np.float32)
    elif isinstance(bg_raw, list):          # 곡 교체(작업 5) — 문자열 1곡은 bed() 한 번
        bg = segment_bed(bg_raw, n, swell)
    else:
        bg = bed(bg_raw, n, swell)
    if stats is not None and bg_raw is not None:
        before = segment_bed(bg_raw, n) if isinstance(bg_raw, list) else bed(bg_raw, n)
        stats.update(bed_stats(before, bg, swell))
    tt = np.arange(n) / SR
    K = sound.intensity  # noqa: N806
    inten = np.interp(tt, [k[0] for k in K], [k[1] for k in K]).astype(np.float32)
    vo = np.zeros(n, np.float32)
    duck = np.zeros(n, np.float32)
    for x in plan.sentences:
        a = np.load(x.npy).astype(np.float32)
        a = a / (np.abs(a).max() + A.norm_eps) * A.narration_peak
        i0 = int(x.t0 * SR)
        m = min(len(a), n - i0)
        vo[i0:i0 + m] += a[:m]
        duck[max(0, int((x.t0 - A.duck_pre_sec) * SR)):min(n, int((x.t1 + A.duck_post_sec) * SR))] = 1
    kn = int(A.duck_smooth_sec * SR)
    duck = np.convolve(duck, np.ones(kn, np.float32) / kn, mode="same")
    bed_gain = inten * (1 - A.duck_depth * duck) * A.bed_gain
    sfx = Sfx(n, rng)
    tc, ss = FX.title_card, FX.scene_start
    for c in plan.cards:  # sfx_policy: 타이틀 카드 휙+쿵
        if c.kind == "title":
            sfx.whoosh(c.t0 + tc.offset_sec, tc.whoosh_dur_sec, tc.whoosh_v)
            sfx.boom(c.t0 + tc.offset_sec, tc.boom_v)
    first = next(iter(plan.scene_start))
    for sec, t0 in plan.scene_start.items():  # sfx_policy: 장면 시작 휙(첫 장면 제외)
        if sec != first:
            sfx.whoosh(t0 - ss.lead_sec, ss.whoosh_dur_sec, ss.whoosh_v)
    for c in sound.cues:
        sfx.cue(c)
    fade = np.ones(n, np.float32)
    fi, fo = int(A.fade_in_sec * SR), int(A.fade_out_sec * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    L = (bg[:, 0] * bed_gain + sfx.fx * (1 - A.fx_duck * duck) + vo) * fade  # noqa: N806
    R = (bg[:, 1] * bed_gain + sfx.fx * (1 - A.fx_duck * duck) + vo) * fade  # noqa: N806
    pk = max(np.abs(L).max(), np.abs(R).max())
    if pk > A.master_peak:
        L /= pk / A.master_peak
        R /= pk / A.master_peak
    return np.stack([L, R], 1).astype(np.float32), float(pk)


def main(argv: list[str] | None = None) -> int:
    from engine.project import ProjectError, load_direction, load_plan  # noqa: PLC0415 — direction.yaml
    from engine.timebase import Timebase  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="audio.mix")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        plan = load_plan(proj)
        _, _, snd = load_direction(proj, Timebase(plan))
        if snd is None:
            raise ProjectError(f"{proj / 'direction.yaml'}: sound 블록이 없다")
        sound = Sound.model_validate(snd)
        if sound.bgm is None:
            src = None
        elif isinstance(sound.bgm, str):
            src = decode_bgm(bgm_path(sound.bgm))
        else:
            src = [(g.t, decode_bgm(bgm_path(g.id))) for g in sound.bgm]
        stats: dict = {}
        y, pk = mix(plan, sound, src, stats)
        (proj / "out").mkdir(exist_ok=True)
        out = proj / "out" / "mix.f32"
        y.tofile(out)
        bs = proj / "out" / "bed_stats.json"   # 음악이 있을 때만(안 돈 단계는 기록하지 않는다, P5)
        if stats:
            bs.write_text(json.dumps({**stats, "mix_samples": len(y)}, ensure_ascii=False, indent=1), encoding="utf-8")
        elif bs.exists():
            bs.unlink()
        print(f"mix ok {len(y) / SR:.1f}s peak {pk:.3f}", file=sys.stderr)
        res = StageResult(ok=True, stage="mix", artifacts={"mix": str(out), **({"bed_stats": str(bs)} if stats else {})})
    except (ProjectError, BgmError, ValueError, OSError, subprocess.CalledProcessError) as ex:
        res = StageResult(ok=False, stage="mix", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
