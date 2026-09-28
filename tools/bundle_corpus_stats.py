"""번들 코퍼스 실측(v3.5.0, back_and_forth D-0063 작업 7) — agents_reviewer 스키마 개선안(12 §6)의 근거 수치.

    python tools/bundle_corpus_stats.py json samples --out docs/handoff/reports/phase9/corpus_stats.json

각 필드가 없어서 어댑터가 무엇을 못 했는지를 센다: 문장 날짜 부재(timeline 대응 외), narration_tts 빈 비율,
엔티티 id 조인 실패(unmatched), 문장별 entity_refs 부재(별칭 폴백 의존), 섹션 map_ref 부재, 출처 게시일·제목 부재,
claims 비어 있음, 논쟁 양측 출처 부재, 패널 렌더러 없는 차트 종류, 금지 문구 걸린 문장.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bundle.entities import join_entities  # noqa: E402
from bundle.load import corpus_files, load_report_bundle  # noqa: E402
from bundle.to_script import build_draft  # noqa: E402
from bundle.to_sources import parse_citation  # noqa: E402
from engine.entities import load_entities  # noqa: E402
from rules import load_rules  # noqa: E402


def stats(roots: list[Path]) -> dict:
    reg = load_entities()
    panels = set(load_rules().bundle.chart_panels)
    c: Counter = Counter()
    chart_types: Counter = Counter()
    rw_patterns: Counter = Counter()
    for f in corpus_files(roots):
        b = load_report_bundle(f)
        c["bundles"] += 1
        c["sections"] += len(b.sections)
        c["sections_map_ref"] += sum(1 for s in b.sections if s.map_ref)
        c["bundles_with_map"] += bool(b.map and b.map.markers)
        c["markers"] += len(b.map.markers) if b.map else 0
        c["bundles_with_timeline"] += bool(b.timeline and b.timeline.points)
        c["claims_bundles_nonempty"] += bool(b.claims)
        c["contradictions"] += len(b.contradictions)
        c["sources"] += len(b.sources)
        for s in b.sources:
            cit = parse_citation(s)
            c["sources_url"] += bool(cit.url)
            c["sources_pubdate"] += cit.published_at is not None
            c["sources_title"] += bool(cit.title)
            c["sources_publisher"] += bool(cit.publisher)
        for ch in b.charts:
            chart_types[ch.type] += 1
            c["charts"] += 1
            c["charts_panel_renderer"] += ch.type in panels
            c["charts_inferred"] += ch.provenance.verification != "confirmed"
            c["charts_no_source"] += not ch.provenance.sources
        join = join_entities(b, reg)
        nodes = [e for e in join.entities if e.origin == "node"]
        c["nodes"] += len(nodes)
        c["nodes_joined"] += sum(1 for e in nodes if e.entity_id)
        c["nodes_no_flag_no_join"] += sum(1 for e in nodes if not e.entity_id and not e.flag)
        try:
            sc, n = build_draft(b, join, reg)
        except ValueError:
            c["bundles_no_narration"] += 1
            continue
        c["drafts"] += 1
        c["draft_scenes_ne_sections"] += n.scenes != n.sections
        c["draft_scenes"] += n.scenes
        c["sentences"] += len(n.tts)
        c["tts_from_bundle"] += sum(1 for t in n.tts if t.source == "bundle")
        c["tts_rule_issue"] += sum(1 for t in n.tts if t.issue)
        c["dates_timeline"] += sum(v == "timeline" for v in n.date_sources.values())
        c["sentences_with_mention"] += len(n.mentions)
        c["rewrite_required"] += len(n.rewrite_required)
        for m in n.rewrite_required:
            rw_patterns.update(m.patterns)
    return {"schema_version": 1, "counts": dict(sorted(c.items())), "chart_types": dict(chart_types.most_common()),
            "rewrite_patterns": dict(rw_patterns.most_common())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="번들 코퍼스 실측(D7 근거)")
    ap.add_argument("roots", nargs="+", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    rep = stats(a.roots)
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
