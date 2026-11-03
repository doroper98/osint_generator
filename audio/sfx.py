"""녹음 효과음 레지스트리·전투 효과음 층(v7.4.0 back_and_forth D-0627 §2·D-0628 §3·D-0629 §2, 사용자 의견 UF-258).

- `assets/audio/sfx/registry.yaml` 이 효과음 원천·권리의 SSOT 다. 파일은 `assets/audio/sfx/files/`(저장소 미추적, sha1 대조).
  녹음(recorded true)만, 라이선스는 rules `audio.battle_sfx.licenses` 안만. 없는 id·파일 없음·sha1 불일치 = 오류(P6·P10).
- 연출 `sound.cues` kind `battle`(sound·dur·dist·units) → `render_battle` 가 같은 녹음의 테이크·사본을 시간차로 겹쳐 무리 소리를 만든다.
  소리 성질은 바꾸지 않는다(걸음 → 질주·시간 늘이기 없음). 사본마다 음높이·속도는 함께 ±pitch_pct_max % 안(재표본화 한 번).
  거리감 = 저역 통과 + 지수 감쇠 잡음 잔향(rules distance). 가공 내역은 로그(믹서가 out/sfx_log.json·provenance audio.sfx 에 남긴다).
"""

from __future__ import annotations

import hashlib
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.signal import butter, fftconvolve, sosfilt

from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
SFX_DIR = REPO / "assets" / "audio" / "sfx"
REGISTRY = SFX_DIR / "registry.yaml"
FILES = SFX_DIR / "files"
PREFIX = "sfx."
SR = 44100            # audio.mix SR 과 같다(코덱 상수)
DECAY_60DB = np.log(1000)   # 잔향 길이 = −60 dB 까지(정의)


class SfxError(ValueError):
    pass


class SfxEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str
    sha1: str
    duration_sec: float = Field(gt=0)
    kind: str
    recorded: bool                       # 녹음만(AI 생성·합성 원천 금지, D-0627 §2-4)
    title: str
    author: str
    license: str
    license_basis: str                   # 원천 사이트 자체 약관·라이선스 칸 문구 인용(D-0629 §2-4)
    page_url: str
    media_url: str
    source: str
    attribution: Optional[str] = None    # CC BY = 엔딩 크레딧 문구(필수)
    notes: str = ""                      # 한계(원 사이트 없음 등)
    available: bool = True

    @model_validator(mode="after")
    def _rights(self) -> "SfxEntry":
        bs = load_rules().audio.battle_sfx
        if bs is None:
            raise ValueError("rules audio.battle_sfx 가 없다")
        if self.kind not in bs.kinds:
            raise ValueError(f"{self.file}: kind {self.kind!r} 가 rules audio.battle_sfx.kinds 밖")
        if self.license not in bs.licenses:
            raise ValueError(f"{self.file}: 라이선스 {self.license!r} 불허 — rules audio.battle_sfx.licenses {bs.licenses}(D-0627 §2-4)")
        if not self.recorded:
            raise ValueError(f"{self.file}: 녹음이 아닌 원천은 등록하지 않는다(D-0627 §2-4)")
        if self.license in bs.attribution_licenses and not self.attribution:
            raise ValueError(f"{self.file}: {self.license} 는 attribution(크레딧 문구)이 필요하다")
        return self


class SfxRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    sounds: dict[str, SfxEntry]

    @model_validator(mode="after")
    def _ids(self) -> "SfxRegistry":
        bad = [k for k in self.sounds if not k.startswith(PREFIX)]
        if bad:
            raise ValueError(f"효과음 id 는 {PREFIX} 로 시작한다: {bad}")
        return self


@lru_cache(maxsize=1)
def load_sfx_registry() -> SfxRegistry:
    return SfxRegistry.model_validate(yaml.safe_load(REGISTRY.read_text(encoding="utf-8")))


def entry(sid: str) -> SfxEntry:
    reg = load_sfx_registry().sounds
    if sid not in reg:
        raise SfxError(f"효과음 레지스트리에 없는 id: {sid}")
    return reg[sid]


def ids_for(kind: str) -> list[str]:
    return sorted(k for k, e in load_sfx_registry().sounds.items() if e.kind == kind and e.available)


def sfx_path(sid: str) -> Path:
    """파일 경로(있고 sha1 이 맞을 때만). 없으면 오류 — 조용히 빼지 않는다(P6)."""
    e = entry(sid)
    p = FILES / e.file
    if not p.exists():
        raise SfxError(f"효과음 파일 없음: {p} — registry media_url 에서 받아 sha1 대조(Still North 는 7z 안 파일, notes)")
    got = hashlib.sha1(p.read_bytes()).hexdigest()
    if got != e.sha1:
        raise SfxError(f"효과음 sha1 불일치 {sid}: {got} ≠ {e.sha1}")
    return p


def card_line(sid: str) -> tuple[str, str]:
    """엔딩 크레딧 sfx 행 (제목, 라이선스 줄) — 레지스트리에서(SSOT). CC BY 는 attribution 문구 그대로."""
    e = entry(sid)
    return e.title, e.attribution or f"{e.author} · {e.license} · {e.source}"


@lru_cache(maxsize=None)
def decode(sid: str) -> np.ndarray:
    """모노 float32 SR — 피크 1 정규화."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(sfx_path(sid)), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).copy()
    if not len(y):
        raise SfxError(f"효과음 디코드 결과가 비었다: {sid}")
    return y / (np.abs(y).max() + load_rules().audio.norm_eps)


def onsets(y: np.ndarray) -> list[int]:
    """테이크 안 부딪힘 시작 표본 위치(포락선 문턱 오르내림)."""
    O = load_rules().audio.battle_sfx.onset  # noqa: N806
    k = max(1, int(O.env_sec * SR))
    env = np.convolve(np.abs(y), np.ones(k) / k, mode="same")
    hi, lo = O.hi * env.max(), O.lo * env.max()
    out, armed, last = [], True, -int(O.gap_sec * SR)
    for i in np.flatnonzero((env > hi) | (env < lo)):
        if env[i] < lo:
            armed = True
        elif armed and i - last >= O.gap_sec * SR:
            out.append(max(0, int(i - O.pre_sec * SR)))
            armed, last = False, i
    return out


def calls(y: np.ndarray) -> list[tuple[int, int]]:
    """말 울음 파일 안 울음 구간(시작, 끝 표본) — RMS 포락선이 문턱을 넘는 덩어리, 가까운 덩어리는 이어 붙인다."""
    K = load_rules().audio.battle_sfx.call  # noqa: N806
    k = max(1, int(K.env_sec * SR))
    env = np.sqrt(np.convolve(y ** 2, np.ones(k) / k, mode="same"))
    on = np.flatnonzero(env > K.hi * env.max())
    if not len(on):
        return []
    out: list[list[int]] = [[int(on[0]), int(on[0])]]
    for i in on[1:]:
        if i - out[-1][1] <= K.merge_gap_sec * SR:
            out[-1][1] = int(i)
        else:
            out.append([int(i), int(i)])
    pre = int(K.pre_sec * SR)
    return [(max(0, a - pre), min(len(y), b + pre)) for a, b in out]


def repitch(y: np.ndarray, f: float) -> np.ndarray:
    """음높이·속도를 함께 f 배(재표본화 한 번). |f − 1| ≤ pitch_pct_max/100 은 부르는 쪽이 지킨다."""
    n = max(1, int(round(len(y) / f)))
    return np.interp(np.arange(n) * f, np.arange(len(y)), y).astype(np.float32)


def distance(y: np.ndarray, dist: str, rng: np.random.Generator) -> np.ndarray:
    D = load_rules().audio.battle_sfx.distance  # noqa: N806
    if dist not in D:
        raise SfxError(f"거리 {dist!r} 가 rules audio.battle_sfx.distance 밖({sorted(D)})")
    d = D[dist]
    z = sosfilt(butter(2, d.lowpass_hz, "low", fs=SR, output="sos"), y).astype(np.float32)
    if d.reverb_sec > 0 and d.reverb_mix > 0:
        m = int(d.reverb_sec * SR)
        ir = rng.standard_normal(m) * np.exp(-np.arange(m) / SR / (d.reverb_sec / DECAY_60DB))
        ir /= np.sqrt(np.sum(ir ** 2))
        wet = fftconvolve(z, ir)[: len(z)].astype(np.float32)
        z = (1 - d.reverb_mix) * z + d.reverb_mix * wet
    return z


def _seq(ids: list[str], n: int, rng: np.random.Generator) -> tuple[np.ndarray, list[dict]]:
    """여러 녹음을 이어 n 표본(늘이기 없음 — 짧으면 다른 녹음을 교차 페이드로 잇는다)."""
    out = np.zeros(n, np.float32)
    rec, i, xf = [], 0, int(load_rules().audio.battle_sfx.layer.seq_xfade_sec * SR)
    while i < n:
        sid = ids[int(rng.integers(len(ids)))]
        y = decode(sid)
        a = int(rng.integers(max(1, len(y) - min(len(y), n - i))))
        seg = y[a:a + (n - i) + xf].copy()
        k = min(xf, len(seg) // 2)
        if k:
            seg[:k] *= np.linspace(0, 1, k)
            seg[-k:] *= np.linspace(1, 0, k)
        m = min(len(seg), n - i)
        out[i:i + m] += seg[:m]
        rec.append({"id": sid, "from_sec": round(a / SR, 2), "len_sec": round(m / SR, 2)})
        i += max(1, m - k)
    return out, rec


def render_battle(sound: str, dur: float, dist: str, v: float, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
    """(모노 층, 가공 기록). 같은 녹음의 테이크·사본 겹치기만(D-0629 §2)."""
    bs = load_rules().audio.battle_sfx
    if bs is None:
        raise SfxError("rules audio.battle_sfx 가 없다")
    L = bs.layer  # noqa: N806
    ids = ids_for(sound)
    if not ids:
        raise SfxError(f"효과음 레지스트리에 {sound!r} 녹음이 없다 — 큐를 빼거나 원천을 등록한다(P6)")
    n = int(dur * SR)
    y = np.zeros(n, np.float32)
    pm = L.pitch_pct_max / 100   # 퍼센트 정의
    parts: list[dict] = []

    def pitch() -> float:
        return float(1 + rng.uniform(-pm, pm))

    if sound == "melee_metal":
        hits = [(sid, o) for sid in ids for o in onsets(decode(sid))]
        if not hits:
            raise SfxError("금속 부딪힘 녹음에서 부딪힘을 찾지 못했다")
        hl = int(L.melee_hit_sec * SR)
        for _ in range(max(1, int(round(dur * L.melee_hits_per_sec)))):
            sid, o = hits[int(rng.integers(len(hits)))]
            f = pitch()
            seg = repitch(decode(sid)[o:o + hl], f) * float(rng.uniform(*L.hit_gain))
            at = int(rng.integers(max(1, n - len(seg))))
            m = min(len(seg), n - at)
            y[at:at + m] += seg[:m]
            parts.append({"id": sid, "take_at_sec": round(o / SR, 3), "at_sec": round(at / SR, 2), "pitch": round(f, 4)})
    elif sound == "whinny":
        for _ in range(L.whinny_max_per_cue):
            sid = ids[int(rng.integers(len(ids)))]
            src = decode(sid)
            cs = calls(src)
            if not cs:
                raise SfxError(f"말 울음 녹음에서 울음을 찾지 못했다: {sid}")
            a, b = cs[int(rng.integers(len(cs)))]   # 울음 한 번만(D-0628 §3 — 파일에 여럿이어도)
            f = pitch()
            seg = repitch(src[a:b], f)[:n]
            at = int(rng.uniform(*L.whinny_at) * max(1, n - len(seg)))
            y[at:at + len(seg)] += seg[: n - at]
            parts.append({"id": sid, "call_sec": [round(a / SR, 2), round(b / SR, 2)], "at_sec": round(at / SR, 2), "pitch": round(f, 4)})
    else:   # gallop·crowd — 녹음을 잇고(늘이기 없음) 사본을 시간차로 겹친다
        copies = L.gallop_copies if sound == "gallop" else L.crowd_copies
        for c in range(copies):
            f = pitch()
            off = int(rng.uniform(0, L.offset_spread_sec) * SR) if c else 0
            base, rec = _seq(ids, int(np.ceil((n - off) * f)) + 1, rng)
            seg = repitch(base, f)[: n - off] * float(rng.uniform(*L.copy_gain))
            y[off:off + len(seg)] += seg
            parts.append({"copy": c, "offset_sec": round(off / SR, 2), "pitch": round(f, 4), "segments": rec})
    y = distance(y, dist, rng)
    k = min(int(bs.fade_sec * SR), n // 2)
    if k:
        y[:k] *= np.linspace(0, 1, k)
        y[n - k:] *= np.linspace(1, 0, k)
    y = (y / (np.abs(y).max() + load_rules().audio.norm_eps) * bs.peak * v).astype(np.float32)
    ps = [p["pitch"] for p in parts]
    return y, {"sound": sound, "dur_sec": round(dur, 2), "dist": dist, "v": v, "ids": sorted({p.get("id") or s["id"] for p in parts for s in (p.get("segments") or [p])}),
               "layers": len(parts), "pitch_range": [min(ps), max(ps)], "parts": parts}


__all__ = ["SfxEntry", "SfxError", "SfxRegistry", "card_line", "decode", "distance", "entry", "ids_for", "load_sfx_registry", "onsets",
           "calls", "render_battle", "repitch", "sfx_path"]
