"""v3『호르무즈와 한국』원고 출처 → intake/sources.json·claims.json 이관 (v3.2.0, back_and_forth D-0052 D51).

    python tools/migrate_v3_claims.py projects/hormuz_korea [projects/hormuz_ai ...]

- 소스 = credits.yaml '보도 · 자료' 6곳. 기사 4건(Reuters·Korea Herald·UPI 기고·Foreign Policy)과 국제해사기구(6.11 기준)는
  ArticleSource, 위키백과 문서는 게시일이 없어 DocumentSource. url 은 없다 — `pending_source: "원문 URL 미확보 — 매체·날짜만"`.
- claim = 문장 하나당 1개. source_ids = v3 레퍼런스(render3.py)가 **장면 단위로** 적은 매체, 근거가 없는 장면은 6곳 묶음.
  문장별 매체를 지어내지 않는다(G4).
- status = corroborated, checks = [v3_user_approved, credits.yaml] — v3 는 사용자가 사실 검증 라벨 없이 합격시킨 영상(D51).
- 원고 script.yaml 문장 sources 를 claim id 로 채운다(텍스트·발음·날짜는 그대로). 결정적 — 여러 번 돌려도 같은 결과.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.source_models import ArticleSource, Claim, ClaimsFile, DocumentSource, SourcesFile  # noqa: E402
from script.schema import Script  # noqa: E402

MIGRATED_ON = date(2026, 9, 28)
CONFIRMED_BY = "v3 사용자 합격본 이관(docs/handoff/KICKOFF_PROMPT.md §5, D-0052 D51)"
PENDING = "원문 URL 미확보 — 매체·날짜만(D-0052 D51, R-0036 종결)"
NOTE = "v3 이관 — 사용자 합격본. 근거는 크레딧 매체 단위, 문장별 대응 기록 없음"
REF = "docs/handoff/reference_code/v3_hormuz_korea/render3.py"


def _art(sid: str, pub: str, day: str, head: str, head_ko: str | None, facts: list[str], ref: str) -> ArticleSource:
    return ArticleSource(id=sid, type="article", publisher=pub, headline_original=head, headline_ko=head_ko,
                         published_at=date.fromisoformat(day), key_facts=facts, retrieved_at=MIGRATED_ON, lang="ko",
                         source_ref=f"credits.yaml 보도 · 자료 — {ref}", pending_source=PENDING, note=NOTE,
                         confirmed_by=CONFIRMED_BY, confirmed_at=datetime(2026, 9, 28, tzinfo=timezone.utc))


def sources() -> SourcesFile:
    """크레딧 6곳. 헤드라인은 미디어 레지스트리의 번역문만 있다 — 원문 제목은 미확보라고 적는다."""
    return SourcesFile(sources=[
        _art("src_art_0001", "Reuters", "2026-09-04", "Reuters 2026-09-04 기사(원문 제목 미확보 — 번역 헤드라인만)",
             "한국, 호르무즈 군사 선택지 검토… 대통령실 “결정된 것은 없다”",
             ["대통령실: 호르무즈 파병은 결정된 것이 없다", "2025년 수입 중 호르무즈 경유 비중 원유 61% · 나프타 54%(대통령실 인용 수치)"],
             "Reuters (9.4)"),
        _art("src_art_0002", "The Korea Herald", "2026-09-07", "The Korea Herald 2026-09-07 기사(원문 제목 미확보 — 번역 헤드라인만)",
             "정부, 전투 격화·반대 여론 확산에 호르무즈 파병 계획 재조정", ["정부가 호르무즈 파병 계획을 재조정했다"], "The Korea Herald (9.7)"),
        _art("src_art_0003", "UPI(기고)", "2026-09-08", "UPI 기고 2026-09-08(원문 제목 미확보)", None,
             ["파병 지지론: 호르무즈는 곧 한국의 경제 안보"], "UPI 기고 (9.8)"),
        _art("src_art_0004", "Foreign Policy", "2026-09-10", "Foreign Policy 2026-09-10 기사(원문 제목 미확보)", None,
             ["파병 반대론: 비전투 부대도 표적이 될 수 있다"], "Foreign Policy (9.10)"),
        _art("src_art_0005", "국제해사기구(IMO)", "2026-06-11", "국제해사기구 집계(6월 11일 기준, 원문 제목 미확보)", None,
             ["6월 11일까지 선박 공격 46건, 선원 사망 14명"], "국제해사기구 (6.11 기준)"),
        DocumentSource(id="src_doc_0001", type="document", issuer="위키백과", title="2026 Strait of Hormuz campaign",
                       key_facts=["2026 호르무즈 해협 전역 개요(영문 위키백과 문서)"], retrieved_at=MIGRATED_ON, lang="en",
                       note=NOTE + " · 게시일 없는 문서라 DocumentSource", confirmed_by=CONFIRMED_BY,
                       confirmed_at=datetime(2026, 9, 28, tzinfo=timezone.utc)),
    ])


ALL = ["src_art_0001", "src_art_0002", "src_art_0003", "src_art_0004", "src_art_0005", "src_doc_0001"]
# v3 render3.py 가 장면에 붙인 출처 표기(줄 번호는 REF): route 카드 "로이터 · 대통령실 인용 수치"(203), cost 카드 "국제해사기구 · 6월 11일 기준"(224),
# review 기사 카드 Reuters(259), debate 기사 카드 Korea Herald(236)·찬반 패널 UPI 기고·Foreign Policy(806~808). 나머지 장면은 근거 기록 없음 → 묶음
SCENE_SOURCES: dict[str, list[str]] = {
    "route": ["src_art_0001"], "cost": ["src_art_0005"], "review": ["src_art_0001"],
    "debate": ["src_art_0002", "src_art_0003", "src_art_0004"],
}


def _event_date(d: str) -> date | None:
    parts = d.split(".")
    return date(*map(int, parts)) if len(parts) == 3 else None


def migrate(proj: Path) -> tuple[int, int]:
    sp = proj / "script.yaml"
    script = Script.model_validate(yaml.safe_load(sp.read_text(encoding="utf-8")))
    claims: list[Claim] = []
    scenes = []
    for sc in script.scenes:
        ids = SCENE_SOURCES.get(sc.id, ALL)
        sents = []
        for s in sc.sentences:
            cid = f"clm_{len(claims) + 1:04d}"
            claims.append(Claim(claim_id=cid, text=s.text, source_ids=ids, status="corroborated",
                                checks=["v3_user_approved", "credits.yaml", f"scene_sources:{sc.id}" if sc.id in SCENE_SOURCES else "scene_sources:bundle"],
                                event_date=_event_date(s.date), notes=NOTE))
            sents.append(s.model_copy(update={"sources": [cid]}))
        scenes.append(sc.model_copy(update={"sentences": sents}))
    (proj / "intake").mkdir(exist_ok=True)
    (proj / "intake" / "sources.json").write_text(sources().model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    (proj / "intake" / "claims.json").write_text(ClaimsFile(claims=claims).model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    sp.write_text(_insert_sources(sp.read_text(encoding="utf-8"), [c.claim_id for c in claims]), encoding="utf-8")
    again = Script.model_validate(yaml.safe_load(sp.read_text(encoding="utf-8")))
    assert again == script.model_copy(update={"scenes": scenes}), "원고 이관 뒤 sources 외 변경"
    return len(sources().sources), len(claims)


def _insert_sources(text: str, ids: list[str]) -> str:
    """주석·형식을 보존하며 문장 블록 끝에 `sources: [clm_…]` 한 줄을 넣는다(이미 sources 가 있으면 교체)."""
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("sources:")]
    out: list[str] = []
    k = 0
    inside = False
    for ln in lines:
        starts = ln.startswith("  - date:") or ln.startswith("- id:")
        if starts and inside:
            out.append(f"    sources: [{ids[k]}]")
            k += 1
            inside = False
        out.append(ln)
        if ln.startswith("  - date:"):
            inside = True
    if inside:
        out.append(f"    sources: [{ids[k]}]")
        k += 1
    assert k == len(ids), (k, len(ids))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("projects", nargs="+", type=Path)
    for p in ap.parse_args(argv).projects:
        n_src, n_cl = migrate(p)
        print(f"{p}: sources {n_src} · claims {n_cl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
