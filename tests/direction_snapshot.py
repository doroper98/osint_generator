"""합성 plan 으로 연출을 풀어 스냅샷을 만든다 (v3.1.0, D-0047 작업 3·9) — 자산·음성 없이 돈다.

`python -m tests.direction_snapshot <proj> <out.json>` 은 옛 direction.py 삭제 전에 한 번 스냅샷을 만든다.
테스트는 direction.yaml 을 같은 합성 plan 으로 풀어 이 스냅샷과 dict 단위로 비교한다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.timebase import Timebase
from script.plan import load_script
from script.schema import Plan

GAP_SEC = 0.35
SEC_PER_CHAR = 0.12


def synthetic_plan(proj: Path) -> Plan:
    sc = load_script(proj)
    rows, starts, t = [], {}, 4.0
    for scene in sc.scenes:
        starts[scene.id] = t
        for k, s in enumerate(scene.sentences):
            dur = round(len(s.text) * SEC_PER_CHAR, 3)
            rows.append(dict(sid=f"{scene.id}_{k}", scene=scene.id, date=s.date, text=s.text, tts=s.tts or s.text,
                             segments=[], mp3=f"/nonexistent/{scene.id}_{k}.mp3", npy="/nonexistent.npy", dur=dur, t0=t, t1=t + dur))
            t += dur + GAP_SEC
        t += 1.0
    return Plan.model_validate(dict(sentences=rows, cards=[dict(kind="title", t0=0.0, t1=3.5), dict(kind="end", t0=t, t1=t + 6.0)],
                                    scene_start=starts, total=t + 6.0, voice="synthetic", title=sc.title, subtitle=sc.subtitle, date=sc.date))


def snapshot(keys: list, events: list[dict], sound: dict | None, tb: Timebase) -> dict:
    from engine.registry import validate_events  # noqa: PLC0415

    ev = validate_events(events)
    by_type: dict[str, list] = {}
    for e in ev:
        by_type.setdefault(e["type"], []).append(e)
    return json.loads(json.dumps({"keys": [k.__dict__ for k in keys], "events_by_type": by_type, "sound": sound,
                                  "word_anchors": tb.word_anchors}, ensure_ascii=False, default=list))


def main(argv: list[str]) -> int:
    import importlib.util  # noqa: PLC0415

    proj, out = Path(argv[0]).resolve(), Path(argv[1])
    spec = importlib.util.spec_from_file_location("dsnap", proj / "direction.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # 옛 연출 1회 실행(스냅샷 생성용 — direction.py 삭제 전)
    tb = Timebase(synthetic_plan(proj))
    d = mod.direct(tb)
    snd = mod.sound(tb) if hasattr(mod, "sound") else None
    out.write_text(json.dumps(snapshot(d.keys, d.events, snd, tb), ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"ok {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
