"""씬 플랜 → `art_direction.json` (V1 시드 + V2 콘텐츠 규칙, 계획 §6.0).

**LLM 무호출.** 시드는 `fnv1a(report_id)` 에서 파생하므로 같은 번들이면 항상 같은 조판이
나온다(결정론). 리롤은 시드에 salt 를 섞어 재추첨하는 것이며, 리롤 횟수까지 기록해
"어떤 조판을 승인했는지"가 재현 가능하다.

V3(아트 디렉터 LLM)은 Phase 5 — 본 스크립트는 V1+V2 까지만 한다. 그래서 무비용이고,
프리뷰를 미리 만들어 두는 §6.0.2 자동 생성 경로에 그대로 쓸 수 있다.

사용::

    python hyperframes/shorts/build_art_direction.py
    python hyperframes/shorts/build_art_direction.py --reroll 1   # 시드 재추첨
    python hyperframes/shorts/build_art_direction.py --approve    # 승인 고정
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PLAN_JSON = HERE / "scene_plan.json"
LIB_MANIFEST = REPO_ROOT / "assets" / "library" / "library_manifest.json"
OUT_JSON = HERE / "art_direction.json"

#: 07 §4 카테고리 액센트 (섀도 색 후보). V2 가 고르고 V3 가 덮어쓸 수 있다.
ACCENTS = ["#B03A2E", "#3E6E8E", "#C9862B", "#6E2C2C", "#4A6B4E"]


def pick(seed: int, salt: int, options: list):
    """시드+salt 로 결정론 선택. `Math.random` 금지 원칙의 파이썬 쪽 대응."""
    from schemas.models import fnv1a

    return options[fnv1a(f"{seed}:{salt}") % len(options)]


def build(plan: dict, reroll: int) -> dict:
    from schemas.models import (
        BG_GRAMMARS,
        PAPER_TONES,
        ArtDirection,
        CastEntry,
        fnv1a,
    )

    report_id = plan.get("report_id", "")
    seed = fnv1a(report_id) ^ (fnv1a(f"reroll:{reroll}") if reroll else 0)

    # --- V2 콘텐츠 규칙: 배경 문법 후보 압축 -----------------------------
    # 인물이 많으면 무대/사진벽, 차트 위주면 서류 책상, 지도 있으면 종이 지도.
    has_chart = any(s.get("chart") for s in plan["scenes"])
    person_nodes = [
        n for s in plan["scenes"]
        if (s.get("chart") or {}).get("type") == "stakeholder_map"
        for n in ((s["chart"].get("data") or {}).get("nodes") or [])
        if n.get("kind") == "person"
    ]
    candidates = list(BG_GRAMMARS)
    if has_chart:
        candidates = ["file_desk", "plain_grain", "sunburst"]
    if len(person_nodes) >= 4:
        candidates = ["montage_wall", "stage_curtain", "file_desk"]

    # --- 인물 매칭 (§3.4 / §3.0.1) ---------------------------------------
    lib = json.loads(LIB_MANIFEST.read_text(encoding="utf-8"))["people"]
    by_ko = {p["name_ko"].replace(" ", ""): p["person_id"] for p in lib}

    cast: list[CastEntry] = []
    for i, n in enumerate(person_nodes):
        label = n.get("label") or ""
        cast.append(CastEntry(
            label=label,
            role=n.get("role", ""),
            person_id=by_ko.get(label.replace(" ", ""), ""),
            accent=pick(seed, 100 + i, ACCENTS),
            shadow_mode=pick(seed, 200 + i, ["offset", "outline"]),
            shadow_fill=pick(seed, 300 + i, ["solid", "hatch", "dots"]),
            # §1.5 cutout_tilt ±4°, 0.5° 단위
            tilt_deg=(fnv1a(f"{seed}:tilt:{i}") % 17 - 8) * 0.5,
        ))

    ad = ArtDirection(
        report_id=report_id,
        seed=seed,
        reroll_count=reroll,
        paper_tone=pick(seed, 1, list(PAPER_TONES)),
        bg_grammar=pick(seed, 2, candidates),
        sunburst_rotation_deg=float(fnv1a(f"{seed}:sun") % 360),
        tape_layout=fnv1a(f"{seed}:tape") % 4,
        ransom_seed=fnv1a(f"{seed}:ransom"),
        cast=cast,
        scene_ids=[s["id"] for s in plan["scenes"]],
        sentence_count=plan.get("sentence_count", 0),
        estimated_sec=plan.get("estimated_sec", 0.0),
    )
    return json.loads(ad.model_dump_json())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reroll", type=int, default=0, help="시드 재추첨 (0=원본)")
    ap.add_argument("--approve", action="store_true", help="현재 art_direction 을 승인 고정")
    ap.add_argument("--note", default="", help="--approve 시 메모")
    args = ap.parse_args()

    from schemas.models import ArtDirection

    if args.approve:
        if not OUT_JSON.exists():
            print(f"error: {OUT_JSON} 없음 — 먼저 생성하십시오.")
            return 1
        ad = ArtDirection(**json.loads(OUT_JSON.read_text(encoding="utf-8")))
        unresolved = [c.label for c in ad.missing_cast if not c.approved]
        if unresolved:
            print(f"  ! 미보유 인물 {len(unresolved)}인이 미승인 상태입니다: "
                  f"{', '.join(unresolved[:5])}{' …' if len(unresolved) > 5 else ''}")
            print("    (승인해도 렌더는 가능 — 해당 인물은 이름 태그로 대체 조판됩니다)")
        ad.approved = True
        ad.approved_note = args.note
        OUT_JSON.write_text(ad.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(f"[승인] {OUT_JSON}  seed={ad.seed} reroll={ad.reroll_count}")
        print("       이 art_direction 이 곧 렌더 입력입니다 (§6.0.1).")
        return 0

    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    data = build(plan, args.reroll)
    ad = ArtDirection(**data)

    OUT_JSON.write_text(ad.model_dump_json(indent=2) + "\n", encoding="utf-8")

    print(f"report_id  = {ad.report_id}")
    print(f"seed       = {ad.seed}  (reroll {ad.reroll_count})")
    print(f"paper_tone = {ad.paper_tone}")
    print(f"bg_grammar = {ad.bg_grammar}")
    print(f"tape/sun/ransom = {ad.tape_layout} / {ad.sunburst_rotation_deg:.0f}° / "
          f"{ad.ransom_seed}")
    print(f"cast       = {len(ad.cast)}인 (보유 "
          f"{len(ad.cast) - len(ad.missing_cast)} / 미보유 {len(ad.missing_cast)})")
    for c in ad.cast:
        mark = "O" if c.person_id else "?"
        print(f"   {mark} {c.label:18} {c.shadow_mode:7} {c.shadow_fill:5} "
              f"{c.accent}  tilt {c.tilt_deg:+.1f}°")
    print(f"\n[저장] {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
