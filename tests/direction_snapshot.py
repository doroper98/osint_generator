"""합성 plan 으로 연출을 풀어 스냅샷을 만든다 (v3.1.0, D-0047 작업 3·9) — 자산·음성 없이 돈다.

스냅샷(`tests/fixtures/direction/*_old_synthetic.json`)은 옛 direction.py 삭제 전(551d48a)에 이 함수로 한 번 만들었다.
테스트는 direction.yaml 을 같은 합성 plan 으로 풀어 이 스냅샷과 dict 단위로 비교한다.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.timebase import Timebase
from script.plan import load_script
from script.schema import Plan

class SyntheticTimebase(Timebase):
    """음성 없는 합성 plan 용 테스트 대역(v5.16.0) — at_word 를 스냅샷을 만든 때와 같은 비율 추정으로 둔다.
    제품 Timebase 는 정렬 파일이 없으면 오류(D151)다. 여기는 연출 변환만 비교하므로 음성 시각을 흉내 내지 않는다."""

    def _aligned(self, x, word):  # noqa: ANN001, ANN202
        return "ratio", None, "정렬 파일 없음"


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
