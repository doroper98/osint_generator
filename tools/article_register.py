"""확인된 기사 출처 → 기사 조판(article) 미디어 항목 등록 (v5.6.0, 사용자 지적 2026-10-05).

사용자 지적: "기사 내용을 조판하여 실제 기사 이미지처럼 보여주는 장면이 이번에 없었다 — 원인이 뭐지?"
원인: 기사 조판은 미디어 레지스트리(`assets/media/media_registry.json`)에 등록된 항목만 연출 후보가 되는데, 등록이 손으로 하는
별도 단계라 kaliningrad-suwalki 에서 빠졌다(PIPELINE-AP-019). 이 도구가 sources.json 의 확인된 기사로 항목을 만든다.

    python tools/article_register.py projects/<pid>            # 무엇이 등록될지·무엇이 빠졌는지(쓰지 않음)
    python tools/article_register.py projects/<pid> --write    # 레지스트리에 추가

- 대상: type article · confirmed · 참조 출처(rules source_note.publishers — 위키백과 등) 아님 · 레지스트리에 같은 url 없음.
- 조판 문구(14 §9 — 화면 캡처·로고 없음, 우리 타이포): 매체명·날짜·원문 헤드라인(headline_original)·헤드라인 번역(headline_ko)·
  부제 = 그 출처를 근거로 쓴 원고 claim 문장(검증된 한국어). 번역은 사람·에이전트가 sources.json headline_ko 에 적는다 —
  비어 있으면 등록하지 않고 "번역 필요"로 알린다(조용히 빼지 않는다, 15 P6).
- 권리 = 헤드라인 번역·요지 자체 조판(기존 기사 항목과 같은 문구). 사진은 이 도구가 다루지 않는다(권리·피사체 대조가 필요 —
  `tools/media_fetch.py search` 로 후보를 찾고 골라 등록).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

LICENSE = "헤드라인 번역·요지 자체 조판(원문 인용 15단어 미만, 기사 화면 캡처·로고 없음, 14 §9)"
SUB_MAX = 40   # 부제 글자 상한(조판 상자 한 줄)


def _mid(pid: str, sid: str) -> str:
    return f"{pid.replace('-', '_')}_{sid.replace('src_', '')}"


def _strip_site(h: str, pub: str) -> str:
    """원문 헤드라인 끝의 사이트 이름(" | Missile Threat", " - Euromaidan Press")만 뗀다 — 헤드라인 본문은 그대로(verbatim)."""
    for sep in (" | ", " - "):
        if sep in h:
            head, tail = h.rsplit(sep, 1)
            if any(w.lower() in tail.lower() for w in pub.replace("(", " ").split() if len(w) > 2):
                return head
    return h


def plan(proj: Path) -> tuple[dict[str, dict], list[str]]:
    """(등록할 항목 mid → 레지스트리 dict, 빠진 이유 줄)."""
    from engine.media_registry import registry_path  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    refs = load_rules().source_note.publishers
    reg = json.loads(registry_path().read_text(encoding="utf-8"))["assets"]
    have = {a.get("url") for a in reg.values()}
    srcs = json.loads((proj / "intake" / "sources.json").read_text(encoding="utf-8"))["sources"]
    claims = json.loads((proj / "intake" / "claims.json").read_text(encoding="utf-8"))["claims"]
    by_src: dict[str, list[str]] = {}
    for c in claims:
        for s in c["source_ids"]:
            by_src.setdefault(s, []).append(c["text"])
    out: dict[str, dict] = {}
    skipped: list[str] = []
    today = dt.date.today().isoformat()
    for s in srcs:
        if s.get("type") != "article" or not s.get("confirmed_by"):
            continue
        pub = str(s.get("publisher", ""))
        if any(pub.startswith(p) for p in refs):
            continue
        if s.get("url") in have:
            continue
        if not s.get("headline_ko"):
            skipped.append(f"{s['id']} {pub}: 헤드라인 번역(sources.json headline_ko) 없음 — 번역을 적고 다시 실행")
            continue
        if not by_src.get(s["id"]):
            skipped.append(f"{s['id']} {pub}: 이 출처를 근거로 한 claim 없음 — 영상에 쓰이지 않는 기사")
            continue
        head = _strip_site(str(s.get("headline_original", "")), pub)
        sub = by_src[s["id"]][0]
        sub = sub if len(sub) <= SUB_MAX else sub[: SUB_MAX - 1] + "…"
        date = str(s.get("published_at", ""))
        out[_mid(proj.name, s["id"])] = {
            "kind": "article", "title": f"{pub} {date} — {head}", "license": LICENSE,
            "author": pub, "credit_author": pub, "date": date, "url": s["url"], "caption": pub,
            "file_note": date.replace("-", ". "), "depicts": [sub], "is_file_photo": False,
            "verified_by": {"by": "code(tools/article_register — sources.json 확인 기록·claims 대조)", "on": today,
                            "casualty_free": True, "relevance": f"{proj.name} 원고 claim 근거 기사"},
            "rights_status": "rights_clear", "retrieved_at": str(s.get("retrieved_at", today)),
            "tool": {"name": "article_typeset", "params": {"translation": True}},
            "headline": s["headline_ko"], "sub": sub, "note": "헤드라인 번역 · 원문 영어",
            "headline_original": head or None,
        }
    return out, skipped


def main(argv: list[str] | None = None) -> int:
    from engine.media_registry import registry_path  # noqa: PLC0415
    from schemas.media_models import MediaRegistryFile  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    items, skipped = plan(a.proj.resolve())
    if a.write and items:
        p = registry_path()
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["assets"].update(items)
        MediaRegistryFile.model_validate(doc)   # 권리·필드 검증(C9) — 틀리면 쓰지 않는다
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"register": sorted(items), "skipped": skipped, "written": bool(a.write and items)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
