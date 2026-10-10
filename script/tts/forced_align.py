"""강제 정렬 — 합성 음성 ↔ 발음 텍스트 글자 시각 (v5.16.0, back_and_forth D-0164 §5, 사용자 결정 D151).

Supertonic 은 단어 경계를 주지 않는다. 그래서 합성 뒤 음성과 발음 텍스트를 맞춰 글자마다 시작·끝 시각을 얻는다.
- 엔진: `torchaudio.pipelines.MMS_FA`(wav2vec2 CTC, 다국어, CPU) + `uroman` 로마자화. 가중치는 config `tts.alignment`
  (`python tools/fetch_data.py mms_fa`, sha1 대조) — 로컬 파일만 연다(네트워크로 받지 않는다). 모델은 프로세스당 한 번.
- 토큰 = 어절(공백). 어절 구간을 MMS 가 찾고, 어절 안 글자 시각은 글자별 로마자 길이로 비례 분배한다.
  공백은 앞 어절 끝에 길이 0 으로 둔다(글자 수 = 발음 텍스트 글자 수).
- 어절 점수 = 토큰 확률 평균, 문장 점수 = 어절 점수 평균. 문장 점수 `rules tts_rules.forced_align.min_score` 미만,
  로마자가 빈 어절, 무음·길이 0 음성 = 오류(P6). 문턱을 어절이 아니라 문장에 거는 근거: 숫자 어절(육십일 등)은 철자 로마자와
  실제 발음이 달라 점수가 0.01 까지 떨어져도 시각은 맞다. 문장 평균은 맞는 원고·틀린 원고를 가른다(phaseV2 run_log §3).
- 발음 텍스트(숫자·기호 없음)를 그대로 넣는다. 결과 = `script.tts.align.from_forced_alignment` 공통 형식.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from orchestrator.config import load_config
from rules import load_rules
from script.tts.supertonic_assets import sha1_file

REPO = Path(__file__).resolve().parents[2]


class ForcedAlignError(ValueError):
    """강제 정렬 실패 — 무음·빈 로마자·신뢰도 미달·가중치 없음. 비율 추정으로 대신하지 않는다(P6, D151)."""


@dataclass(frozen=True)
class CharSpan:
    char: str
    start: float
    end: float
    score: float


def config():  # noqa: ANN201 — AlignmentConfig
    cfg = load_config().tts.alignment
    if cfg is None:
        raise ForcedAlignError("config.yaml tts.alignment 없음 — 강제 정렬을 쓸 수 없다")
    return cfg


def asset_dir() -> Path:
    d = Path(config().asset_dir)
    return d if d.is_absolute() else REPO / d


def require_assets() -> None:
    """가중치가 없거나 sha1 이 다르면 받는 명령을 담은 오류."""
    bad = [rel for rel, want in config().assets.items()
           if not (asset_dir() / rel).is_file() or sha1_file(asset_dir() / rel) != want]
    if bad:
        raise ForcedAlignError(f"강제 정렬 가중치 없음·불일치: {bad} ({asset_dir()}) — `python tools/fetch_data.py mms_fa` 먼저")


@lru_cache(maxsize=1)
def engine():  # noqa: ANN201 — (model, tokenizer, aligner, labels, sample_rate, uroman)
    """프로세스당 한 번 — 가중치 대조 → 로컬 파일로 모델 생성(torch.hub 캐시 경로 = asset_dir, 파일이 있으면 받지 않는다)."""
    require_assets()
    import torch  # noqa: PLC0415 — 무거운 의존성(requirements-engine.txt)
    import uroman  # noqa: PLC0415
    from torchaudio.pipelines import MMS_FA  # noqa: PLC0415

    torch.set_num_threads(config().threads)
    model = MMS_FA.get_model(dl_kwargs={"model_dir": str(asset_dir()), "progress": False})
    return model, MMS_FA.get_tokenizer(), MMS_FA.get_aligner(), frozenset(MMS_FA.get_labels(star=None)), MMS_FA.sample_rate, uroman.Uroman()


def decode(audio: Path, sr: int) -> np.ndarray:
    """mp3·wav → 단일 채널 float32 sr Hz(ffmpeg)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def romanize(s: str) -> str:
    _, _, _, labels, _, ur = engine()
    return "".join(c for c in ur.romanize_string(s).lower() if c in labels)


def align_sentence(audio: Path, pron_text: str) -> list[CharSpan]:
    """발음 텍스트 글자마다 (시작, 끝, 점수). 시각은 음성 파일 처음 기준(초). 실패 = ForcedAlignError."""
    import torch  # noqa: PLC0415

    model, tok, aligner, _, sr, _ = engine()
    words = pron_text.split()
    if not words:
        raise ForcedAlignError("발음 텍스트가 비었다")
    roms = [romanize(w) for w in words]
    empty = [w for w, r in zip(words, roms) if not r]
    if empty:
        raise ForcedAlignError(f"로마자로 바꿀 수 없는 어절 {empty}: {pron_text!r}")
    x = decode(audio, sr)
    if x.size == 0 or float(np.abs(x).max()) < 1e-3:
        raise ForcedAlignError(f"무음·길이 0 음성: {audio}")
    wav = torch.from_numpy(x).unsqueeze(0)
    with torch.inference_mode():
        emission, _ = model(wav)
    try:
        spans = aligner(emission[0], tok(roms))
    except Exception as ex:  # noqa: BLE001 — 토큰이 프레임보다 많은 경우 등
        raise ForcedAlignError(f"정렬 실패({type(ex).__name__}: {ex}): {audio}") from ex
    ratio = wav.size(1) / emission.size(1) / sr
    min_score = load_rules().tts_rules.forced_align.min_score
    out: list[CharSpan] = []
    pos = 0
    for wi, (w, sp) in enumerate(zip(words, spans)):
        i = pron_text.index(w, pos)
        out += [CharSpan(c, out[-1].end if out else 0.0, out[-1].end if out else 0.0, 1.0) for c in pron_text[pos:i]]   # 공백
        t0, t1 = sp[0].start * ratio, sp[-1].end * ratio
        score = float(sum(t.score for t in sp) / len(sp))
        weights = [max(len(romanize(c)), 0) for c in w]
        total = sum(weights) or len(w)
        acc = 0
        for c, wt in zip(w, weights if sum(weights) else [1] * len(w)):
            a = t0 + (t1 - t0) * acc / total
            acc += wt
            out.append(CharSpan(c, a, t0 + (t1 - t0) * acc / total, score))
        pos = i + len(w)
        if wi == len(words) - 1:
            out += [CharSpan(c, out[-1].end, out[-1].end, 1.0) for c in pron_text[pos:]]
    mean = sentence_score(out, pron_text)
    if mean < min_score:
        raise ForcedAlignError(f"정렬 신뢰도 문장 평균 {mean:.3f} < min_score {min_score} — 원고·음성 불일치 의심: {audio}")
    return out


def word_starts(spans: list[CharSpan], pron_text: str) -> list[float]:
    """어절 첫 글자 시작 시각(게이트·provenance 용)."""
    starts, pos = [], 0
    for w in pron_text.split():
        i = pron_text.index(w, pos)
        starts.append(spans[i].start)
        pos = i + len(w)
    return starts


def sentence_score(spans: list[CharSpan], pron_text: str) -> float:
    """문장 점수 = 어절 점수(어절 첫 글자에 실린 값) 평균."""
    scores, pos = [], 0
    for w in pron_text.split():
        i = pron_text.index(w, pos)
        scores.append(spans[i].score)
        pos = i + len(w)
    return float(sum(scores) / len(scores))


def align_file(audio: Path, pron_text: str) -> dict:
    """정렬 → `{mp3}.align.json` 공통 형식 + score_mean·elapsed_ms(plan row·provenance 용). 실패 = ForcedAlignError."""
    from script.tts.align import from_forced_alignment  # noqa: PLC0415

    t = time.perf_counter()
    spans = align_sentence(audio, pron_text)
    al = from_forced_alignment(pron_text, spans)
    al["score_mean"] = round(sentence_score(spans, pron_text), 4)
    al["elapsed_ms"] = round((time.perf_counter() - t) * 1000)
    return al
