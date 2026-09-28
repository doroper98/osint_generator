"""오디오 믹스 CLI (v2.1.0, mix3 분해, 10 §2~§5).

    python -m audio.mix <proj>   → <proj>/out/mix.f32 (44.1kHz 스테레오 float32)

베드 이득·덕킹·피크는 `rules/video_rules.yaml audio`(15 P3). 장면별 음악 강도·BGM 파일·추가 효과음 큐는
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
from scipy.signal import lfilter

from rules import load_rules
from script.schema import Plan

SR = 44100               # 코덱 상수(ffmpeg -ar) — rules audio.sample_rate 와 같아야 한다(테스트)
AU = load_rules().audio  # 수치 SSOT(D-0060 §0, 15 P3) — 값은 v3 그대로
FX = AU.sfx
REPO = Path(__file__).resolve().parent.parent
BGM_DIR = REPO / "assets" / "audio" / "bgm"


class Cue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str            # whoosh | boom | tick
    t: float
    v: float = 1.0
    dur: float | None = None   # whoosh 길이


class Sound(BaseModel):
    """프로젝트 사운드 연출 — direction.yaml `sound:` 블록(앵커 해석 뒤, v3.1.0 D-0047 §0-2)."""

    model_config = ConfigDict(extra="forbid")

    bgm: str                                   # assets/audio/bgm/ 안 파일명
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


def bed(bg: np.ndarray, n: int) -> np.ndarray:
    xf = int(AU.loop_xfade_sec * SR)
    while len(bg) < n:
        tail, head = bg[-xf:], bg[:xf]
        r = np.linspace(0, 1, xf)[:, None]
        bg = np.concatenate([bg[:-xf], tail * (1 - r) + head * r, bg[xf:]])
    bg = bg[:n]
    return bg / (np.abs(bg).max() + AU.norm_eps)


def mix(plan: Plan, sound: Sound, bg_raw: np.ndarray) -> tuple[np.ndarray, float]:
    """(N×2 float32, 정규화 전 피크)."""
    A = AU  # noqa: N806
    tot = plan.total + A.tail_sec
    n = int(tot * SR)
    rng = np.random.default_rng(A.seed)
    bg = bed(bg_raw, n)
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
        y, pk = mix(plan, sound, decode_bgm(BGM_DIR / sound.bgm))
        (proj / "out").mkdir(exist_ok=True)
        out = proj / "out" / "mix.f32"
        y.tofile(out)
        print(f"mix ok {len(y) / SR:.1f}s peak {pk:.3f}", file=sys.stderr)
        res = StageResult(ok=True, stage="mix", artifacts={"mix": str(out)})
    except (ProjectError, ValueError, OSError, subprocess.CalledProcessError) as ex:
        res = StageResult(ok=False, stage="mix", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
