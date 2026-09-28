"""오디오 리포트 CLI (v2.0.1 → v3.4.0 얇은 CLI) — 측정은 audio/qa.py 한 경로(D-0060 작업 6, 검사기 하나).

    python tools/audio_report.py <proj> [--out 경로.json]

<proj>/out/mix.f32(필수)·final.mp4(있으면 음량 측정)와 plan.json 문장으로 AudioQA 를 낸다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from audio.qa import audio_qa  # noqa: E402
from engine.project import load_plan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="오디오 리포트(audio/qa.py)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    q = audio_qa(proj / "out", load_plan(proj).sentences)
    rep = {**q.model_dump(), "issues": q.issues()}
    text = json.dumps(rep, ensure_ascii=False, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
