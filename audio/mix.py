"""오디오 믹스 CLI (v2.1.0, mix3 분해, 10 §2~§5).

    python -m audio.mix <proj>   → <proj>/out/mix.f32 (44.1kHz 스테레오 float32)

베드 이득·덕킹·피크는 `rules/video_rules.yaml audio`(15 P3). 장면별 음악 강도·BGM 파일·추가 효과음 큐는
프로젝트 연출(`direction.py`의 `sound(tb)`)이 준다. 기본 효과음 규칙(sfx_policy): 타이틀 카드 휙+쿵, 장면 시작 휙.
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

SR = 44100
SEED = 3
TAIL_SEC = 0.5           # plan.total 뒤 여백(v3 TOT)
LOOP_XFADE_SEC = 4.0     # BGM 반복 교차 페이드
FADE_IN_SEC = 1.2
FADE_OUT_SEC = 4.0
FX_DUCK = 0.25           # 효과음 덕킹 깊이
REPO = Path(__file__).resolve().parent.parent
BGM_DIR = REPO / "assets" / "audio" / "bgm"


class Cue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str            # whoosh | boom | tick
    t: float
    v: float = 1.0
    dur: float | None = None   # whoosh 길이


class Sound(BaseModel):
    """프로젝트 사운드 연출 — direction.py `sound(tb)`가 만든다."""

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

    def whoosh(self, t_end: float, dur: float = 1.2, v: float = 1.0) -> None:
        n = int(dur * SR)
        ti = np.arange(n) / SR
        nz = self.rng.standard_normal(n)
        a = np.clip(ti / dur, 0, 1) ** 2.2
        y = (lfilter([0.08], [1, -0.92], nz) * (1 - a) * 0.6 + (nz - lfilter([0.3], [1, -0.7], nz)) * a * 0.25) * a
        y *= np.exp(-np.maximum(0, ti - dur + 0.08) / 0.05)
        self.add(t_end - dur, (y * 0.2 * v).astype(np.float32))

    def boom(self, t: float, v: float = 1.0) -> None:
        n = int(2.6 * SR)
        ti = np.arange(n) / SR
        f = 34 + 44 * np.exp(-ti / 0.25)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.sin(ph) * np.exp(-ti / 0.8) * 0.55 + lfilter([0.02], [1, -0.98], self.rng.standard_normal(n)) * np.exp(-ti / 0.3) * 0.6
        self.add(t, (y * v).astype(np.float32))

    def tick(self, t: float, v: float = 1.0) -> None:
        n = int(0.12 * SR)
        ti = np.arange(n) / SR
        self.add(t, (np.sin(2 * np.pi * 1800 * ti) * np.exp(-ti / 0.015) * 0.18 * v).astype(np.float32))

    def cue(self, c: Cue) -> None:
        if c.kind == "whoosh":
            self.whoosh(c.t, c.dur if c.dur is not None else 1.2, c.v)
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
    xf = int(LOOP_XFADE_SEC * SR)
    while len(bg) < n:
        tail, head = bg[-xf:], bg[:xf]
        r = np.linspace(0, 1, xf)[:, None]
        bg = np.concatenate([bg[:-xf], tail * (1 - r) + head * r, bg[xf:]])
    bg = bg[:n]
    return bg / (np.abs(bg).max() + 1e-6)


def mix(plan: Plan, sound: Sound, bg_raw: np.ndarray) -> tuple[np.ndarray, float]:
    """(N×2 float32, 정규화 전 피크)."""
    A = load_rules().audio  # noqa: N806
    tot = plan.total + TAIL_SEC
    n = int(tot * SR)
    rng = np.random.default_rng(SEED)
    bg = bed(bg_raw, n)
    tt = np.arange(n) / SR
    K = sound.intensity  # noqa: N806
    inten = np.interp(tt, [k[0] for k in K], [k[1] for k in K]).astype(np.float32)
    vo = np.zeros(n, np.float32)
    duck = np.zeros(n, np.float32)
    for x in plan.sentences:
        a = np.load(x.npy).astype(np.float32)
        a = a / (np.abs(a).max() + 1e-6) * A.narration_peak
        i0 = int(x.t0 * SR)
        m = min(len(a), n - i0)
        vo[i0:i0 + m] += a[:m]
        duck[max(0, int((x.t0 - A.duck_pre_sec) * SR)):min(n, int((x.t1 + A.duck_post_sec) * SR))] = 1
    kn = int(A.duck_smooth_sec * SR)
    duck = np.convolve(duck, np.ones(kn, np.float32) / kn, mode="same")
    bed_gain = inten * (1 - A.duck_depth * duck) * A.bed_gain
    sfx = Sfx(n, rng)
    for c in plan.cards:  # sfx_policy: 타이틀 카드 휙+쿵
        if c.kind == "title":
            sfx.whoosh(c.t0 + 0.2, 1.4, 1.0)
            sfx.boom(c.t0 + 0.2, 0.6)
    first = next(iter(plan.scene_start))
    for sec, t0 in plan.scene_start.items():  # sfx_policy: 장면 시작 휙(첫 장면 제외)
        if sec != first:
            sfx.whoosh(t0 - 0.05, 0.9, 0.55)
    for c in sound.cues:
        sfx.cue(c)
    fade = np.ones(n, np.float32)
    fi, fo = int(FADE_IN_SEC * SR), int(FADE_OUT_SEC * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    L = (bg[:, 0] * bed_gain + sfx.fx * (1 - FX_DUCK * duck) + vo) * fade  # noqa: N806
    R = (bg[:, 1] * bed_gain + sfx.fx * (1 - FX_DUCK * duck) + vo) * fade  # noqa: N806
    pk = max(np.abs(L).max(), np.abs(R).max())
    if pk > A.master_peak:
        L /= pk / A.master_peak
        R /= pk / A.master_peak
    return np.stack([L, R], 1).astype(np.float32), float(pk)


def main(argv: list[str] | None = None) -> int:
    from engine.project import ProjectError, load_direction, load_plan  # noqa: PLC0415
    from engine.timebase import Timebase  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="audio.mix")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        plan = load_plan(proj)
        mod = load_direction(proj)
        if not hasattr(mod, "sound"):
            raise ProjectError(f"{proj / 'direction.py'}: sound(tb) 함수가 없다")
        sound = Sound.model_validate(mod.sound(Timebase(plan)))
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
