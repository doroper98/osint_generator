"""norm_ref 스윕 — 베드 정규화 기준(rules audio.bed_bass.norm_ref)만 바꿔 믹스를 메모리에서 만들고 음악 레벨을 잰다.

D-0102 절차(v4.6.0 G6)의 도구판(v4.11.0 back_and_forth D-0118 §2). 프로젝트 out/ 에 쓰지 않는다(임시 폴더의 mix.f32 → audio.qa.audio_qa).
한 줄 = 한 값의 JSON(jsonl). 규칙 값 선택 = 모든 프로젝트의 music_under_narration_db 가 범위 안 0.3 dB 여유로 드는 최소값.

    python tools/norm_ref_sweep.py projects/hormuz_korea hormuz 0.7 0.6 0.5 0.4 0.3 >> sweep.jsonl
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import audio.mix as M  # noqa: E402
from audio.qa import audio_qa  # noqa: E402
from engine.project import load_direction, load_plan  # noqa: E402
from engine.timebase import Timebase  # noqa: E402


def main(argv: list[str]) -> int:
    proj, tag, vals = Path(argv[0]).resolve(), argv[1], [float(v) for v in argv[2:]]
    plan = load_plan(proj)
    _, _, snd = load_direction(proj, Timebase(plan))
    sound = M.Sound.model_validate(snd)
    if sound.bgm is None:
        raise SystemExit("음악 없는 프로젝트 — norm_ref 가 쓰이지 않는다")
    src = (M.decode_bgm(M.bgm_path(sound.bgm)) if isinstance(sound.bgm, str)
           else [(g.t, M.decode_bgm(M.bgm_path(g.id))) for g in sound.bgm])
    for v in vals:
        M.AU.bed_bass.norm_ref = v   # 이 프로세스 안에서만(규칙 파일은 그대로)
        stats: dict = {}
        y, _ = M.mix(plan, sound, src, stats)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mix.f32").write_bytes(y.tobytes())
            (Path(d) / "bed_stats.json").write_text(json.dumps({**stats, "mix_samples": len(y)}), encoding="utf-8")
            q = audio_qa(Path(d), plan.sentences)
        print(json.dumps({"project": tag, "norm_ref": v, "music_under_narration_db": q.music_under_narration_db,
                          "mix_peak": q.mix_peak, "bed_bass_rise_db": q.bed_bass_rise_db, "bed_bass_ratio_db": q.bed_bass_ratio_db,
                          "narration_rms_db": q.narration_rms_db}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
