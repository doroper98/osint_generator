"""카메라 제안 대조 사본 (v3.3.0, back_and_forth D-0056 작업 6 — `projects/hormuz_camauto`).

    python tools/camauto_copy.py projects/hormuz_korea projects/hormuz_camauto

원본 프로젝트를 복사하고, 사본 direction.yaml 의 shots 카메라·전환만 원본의 `prev/camera_suggest.json` 제안값으로
바꾼다(제안 없는 숏 — 전면 카드 뒤·장소 없음·엔딩 풀백 — 은 그대로). **원본은 읽기만 한다**(v3 direction 원본 수정 금지, D-0056 §3).
바뀐 목록은 사본 `camauto_map.json`. 제안은 옵션이다 — 이 사본은 '제안을 전부 받아들이면 어떤가'를 보는 실험이다(P8).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.camera_suggest import load_suggest  # noqa: E402
from engine.direction import load_direction_doc  # noqa: E402
from rules import load_rules  # noqa: E402
from workers.direction_io import dump_direction_yaml  # noqa: E402

COPY_SKIP = ("prev", "out", "logs", "03_tasks", "__pycache__", "llm_calls")
HEADER = "# direction.yaml — hormuz_camauto: v3 연출 사본, shots 카메라·전환만 engine.camera_suggest 제안값(v3.3.0 D-0056 작업 6).\n"


def main(argv: list[str] | None = None) -> int:
    a = argv if argv is not None else sys.argv[1:]
    src, dst = Path(a[0]).resolve(), Path(a[1]).resolve()
    cs = load_suggest(src)
    if cs is None:
        print(f"제안 없음: {src}/prev/camera_suggest.json — 먼저 python -m engine.camera_suggest {src}", file=sys.stderr)
        return 1
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*COPY_SKIP))
    doc = load_direction_doc(src / "direction.yaml")
    if len(doc.shots) != len(cs.shots):
        print(f"숏 수 불일치: direction {len(doc.shots)} · 제안 {len(cs.shots)}", file=sys.stderr)
        return 1
    lo, hi = load_rules().shot_grammar.move_dur_sec
    changes = []
    for shot, sug in zip(doc.shots, cs.shots):
        if sug.suggested is None:
            continue
        before = {"mode": shot.mode, **shot.camera.model_dump()}
        shot.camera = shot.camera.model_copy(update=sug.suggested.model_dump())
        if sug.suggested_transition is not None and sug.suggested_transition != shot.mode:
            shot.mode = sug.suggested_transition
            if shot.mode == "move":
                shot.dur = round((lo + hi) / 2, 2)
                shot.under = False
        changes.append({"t": sug.t, "scene": sug.scene, "before": before,
                        "after": {"mode": shot.mode, **shot.camera.model_dump()}, "fits": sug.fits, "note": sug.note})
    (dst / "direction.yaml").write_text(dump_direction_yaml(doc, HEADER), encoding="utf-8")
    (dst / "camauto_map.json").write_text(json.dumps({"schema_version": 1, "source": src.name,
                                                      "suggest_direction_sha1": cs.direction_sha1, "changes": changes},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{dst}: 숏 {len(changes)}/{len(doc.shots)} 제안값으로 교체")
    return 0


if __name__ == "__main__":
    sys.exit(main())
