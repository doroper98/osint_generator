"""전달 패키지 — 제목·설명·태그·썸네일 (v7.4.0, back_and_forth D-0320, 사용자 의견 UF-177).

사용자 원문: "이건 영상 줄때 매번 만들어서 주는 규칙으로 하자. 제목, 설명, 태그, 썸네일"

    python tools/deliver_package.py projects/<pid>
      → out/delivery/{title.txt, description.txt, tags.txt, thumbnail.jpg, MD5SUMS} · out/description_full.txt(원문 링크 전부)

- 원천: 프로젝트 description.yaml(title·alt_titles·summary·chapters·tags·hashtags·key_links — engine.mux.Description, 새 파일 없음 §5),
  챕터 시각 = engine.mux.chapter_time(plan), 자료·사진·음악·지도 줄 = engine.credits(이번 렌더가 실제로 쓴 권리 참조만, D-0314 교훈),
  썸네일 = tools/thumbnail.py 산출(out/thumbnail.jpg — 없으면 오류, 대신 만들지 않는다).
- 한도 = rules delivery_package(유튜브). 네 항목 중 하나라도 없거나 넘치면 오류(조용한 생략·잘림 금지, 15 P6).
- provenance: out/provenance.json 에 `delivery_package`(항목·글자 수·한도·md5).
마지막 줄에 StageResult JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SOURCES_HEADING = "자료"
KEY_LINKS_HEADING = "주요 링크"
CREDITS_SKIP = ("보도 출처",)   # 매체 요약 줄(자료)로 대신한다 — 원문 링크 전부는 description_full.txt


class DeliveryError(RuntimeError):
    """전달 패키지 네 항목 중 빠지거나 한도를 넘은 것 — 사람이 description.yaml·썸네일을 고친다(15 P6)."""


def tags_chars(tags: list[str]) -> int:
    """유튜브 태그 글자 수 — 태그 글자 + 사이 쉼표 + 띄어쓰기 있는 태그는 따옴표 2."""
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)


def outlet_summary(cited: list) -> list[str]:
    """인용 소스 → 매체별 한 덩이 '매체 (월.일·월.일)' / 자료는 '기관'(같은 기관 한 번). 순서 = 처음 나온 순, 날짜는 이른 순.
    원문 URL 이 없는 소스(프로젝트 내부 정리 파일 등)는 시청자가 찾아갈 곳이 없어 빼고, 전체 기록(description_full.txt)에는 남긴다."""
    from engine.credits import source_label  # noqa: PLC0415

    order: list[str] = []
    dates: dict[str, list[str]] = {}
    for s in [x for x in cited if x.url]:
        if s.type == "article":
            k, d = s.publisher, f"{s.published_at.month}.{s.published_at.day}"
        elif s.type == "x_post":
            k, d = source_label(s).split(" (")[0], (f"{s.posted_at.month}.{s.posted_at.day}" if s.posted_at else "")
        else:
            k, d = s.issuer, ""
        if k not in dates:
            order.append(k)
            dates[k] = []
        if d and d not in dates[k]:
            dates[k].append(d)
    def key(d: str) -> tuple[int, int]:
        m, dd = d.split(".")
        return int(m), int(dd)

    return [f"{k} ({'·'.join(sorted(dates[k], key=key))})" if dates[k] else k for k in order]


def key_links(cited: list, chosen: list[str], n: int) -> list[str]:
    """설명 주요 링크 — description.yaml key_links(소스 id 또는 URL, 이번 영상 인용 소스 안의 것만 — 감독이 고른 링크, D-0323 §5),
    비면 매체별 첫 원문 링크 n 개."""
    from engine.credits import source_label  # noqa: PLC0415

    by_key = {**{s.url: s for s in cited if s.url}, **{s.id: s for s in cited if s.url and getattr(s, "id", None)}}
    if chosen:
        bad = [u for u in chosen if u not in by_key]
        if bad:
            raise DeliveryError(f"description.yaml key_links 가 이번 영상 인용 소스(원문 URL 있는 것)에 없다: {bad}")
        if len(chosen) > n:
            raise DeliveryError(f"description.yaml key_links {len(chosen)}개 > rules delivery_package.key_links_max {n}")
        return [f"{source_label(by_key[k])} — {by_key[k].url}" for k in chosen]
    out, seen = [], set()
    for s in cited:
        k = getattr(s, "publisher", None) or getattr(s, "issuer", None)
        if s.url and k not in seen:
            seen.add(k)
            out.append(f"{source_label(s)} — {s.url}")
        if len(out) == n:
            break
    return out


def full_authors(lines: list[str], used: set[str], media: dict) -> list[str]:
    """크레딧 줄의 말줄임(엔딩 카드 폭 때문에 자른 credit_author '…')을 미디어 레지스트리 원본 author 로 되돌린다 — 설명문은 폭 제한이 없다
    (D-0323 §2). 자르는 쪽은 엔딩 카드 조판만."""
    rep: dict[str, str] = {}
    for ref in used:
        if not ref.startswith("media."):
            continue
        m = media.get(ref[len("media."):])
        cut = (getattr(m, "credit_author", None) or "").split(" · ")[0]
        if m is not None and cut.endswith("…") and m.author:
            rep[cut] = m.author
    out = []
    for ln in lines:
        for a, b in rep.items():
            ln = ln.replace(a, b)
        out.append(ln)
    return out


def build_package_description(P, d, full: bool = False) -> str:  # noqa: ANN001, N803 — engine.project.Project, engine.mux.Description
    """유튜브 설명(요약 문단·챕터·자료·주요 링크·크레딧 줄·해시태그). full = 자료 줄 대신 원문 링크 전부(기록용 description_full.txt)."""
    from engine.credits import credit_lines, description_sources  # noqa: PLC0415
    from engine.mux import chapter_time, mmss  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    DP = load_rules().delivery_package  # noqa: N806
    cited = P.R.cache.get("cited_sources") or []
    ch = [f"{mmss(chapter_time(P.plan, c.at, i == 0))} {c.label}" for i, c in enumerate(d.chapters)]
    parts: list[str] = []
    for para in d.summary_paras():
        parts += [para, ""]
    parts += ["챕터", *ch, ""]
    if full:
        parts += [SOURCES_HEADING, *description_sources(cited), ""]
    else:
        parts += [SOURCES_HEADING, " · ".join(outlet_summary(cited)), "", KEY_LINKS_HEADING, *key_links(cited, d.key_links, DP.key_links_max), ""]
    lines = credit_lines(P.R.credits, P.R.assets.rights, P.R.assets.media, P.R.cache.get("credit_refs"), cited,
                         P.R.cache.get("series_records"), P.R.cache.get("press_by_scene"))
    lines = full_authors(lines, P.R.cache.get("credit_refs") or set(), P.R.assets.media_assets)
    parts += [ln for ln in lines if not ln.startswith(CREDITS_SKIP)]
    parts += ["", " ".join(d.hashtags)]
    return "\n".join(parts).strip() + "\n"


def check_package(title: str | None, desc: str, tags: list[str], hashtags: list[str], thumb: Path) -> list[str]:
    """네 항목·한도 검사 — 문제 목록(비면 통과)."""
    from rules import load_rules  # noqa: PLC0415

    DP = load_rules().delivery_package  # noqa: N806
    T = load_rules().thumbnail  # noqa: N806
    errs = []
    if not title or not title.strip():
        errs.append("title 없음 — description.yaml title")
    elif len(title) > DP.title_max_chars:
        errs.append(f"title {len(title)}자 > {DP.title_max_chars}")
    if not desc.strip():
        errs.append("description 없음")
    elif len(desc) > DP.description_max_chars:
        errs.append(f"description {len(desc)}자 > {DP.description_max_chars} — 요약·챕터·크레딧을 줄인다")
    if not tags:
        errs.append("tags 없음 — description.yaml tags")
    elif tags_chars(tags) > DP.tags_max_chars:
        errs.append(f"tags {tags_chars(tags)}자 > {DP.tags_max_chars}")
    if len(hashtags) != DP.hashtags_count or not all(h.startswith("#") and " " not in h for h in hashtags):
        errs.append(f"hashtags {hashtags} — '#' 로 시작하는 띄어쓰기 없는 해시태그 {DP.hashtags_count}개")
    if not thumb.exists():
        errs.append(f"thumbnail 없음 — python tools/thumbnail.py 먼저 ({thumb})")
    elif thumb.stat().st_size > T.jpg_max_bytes:
        errs.append(f"thumbnail {thumb.stat().st_size} B > {T.jpg_max_bytes}")
    return errs


def make_package(proj: Path) -> dict:
    from engine.mux import load_description  # noqa: PLC0415
    from engine.project import load_project  # noqa: PLC0415

    d = load_description(proj)
    od = proj / "out"
    if d.description_text:   # v7.4.0 D-0322 — 사람이 쓴 전문(지난 영상, 렌더 준비물 없음). 원문 링크 전부 기록은 그 영상 credits·고정 댓글
        P, desc, src = None, d.description_text.strip() + "\n", "description_text"  # noqa: N806
    else:
        P = load_project(proj)  # noqa: N806 — 권리 점검을 다시 통과한 자산만 크레딧 줄에 오른다
        desc, src = build_package_description(P, d), "generated"
    thumb = od / "thumbnail.jpg"
    errs = check_package(d.title, desc, d.tags, d.hashtags, thumb)
    if errs:
        raise DeliveryError("전달 패키지 검사 실패:\n" + "\n".join(errs))
    dd = od / "delivery"
    dd.mkdir(parents=True, exist_ok=True)
    (dd / "title.txt").write_text(d.title + "\n" + "".join(f"(대안) {t}\n" for t in d.alt_titles), encoding="utf-8")
    (dd / "description.txt").write_text(desc, encoding="utf-8")
    (dd / "tags.txt").write_text(", ".join(d.tags) + "\n", encoding="utf-8")
    shutil.copyfile(thumb, dd / "thumbnail.jpg")
    if P is not None:
        (od / "description_full.txt").write_text(build_package_description(P, d, full=True), encoding="utf-8")
    names = ["title.txt", "description.txt", "tags.txt", "thumbnail.jpg"]
    md5 = {n: hashlib.md5((dd / n).read_bytes()).hexdigest() for n in names}
    (dd / "MD5SUMS").write_text("".join(f"{v}  {k}\n" for k, v in md5.items()), encoding="utf-8")
    from rules import load_rules  # noqa: PLC0415

    DP = load_rules().delivery_package  # noqa: N806
    rec = {"schema_version": 1, "items": DP.items, "title_chars": len(d.title), "alt_titles": len(d.alt_titles),
           "description_chars": len(desc), "description_source": src, "tags": len(d.tags), "tags_chars": tags_chars(d.tags), "hashtags": d.hashtags,
           "limits": {"title": DP.title_max_chars, "description": DP.description_max_chars, "tags": DP.tags_max_chars},
           "chapters": len(d.chapters), "md5": md5}
    pv = od / "provenance.json"
    if pv.exists():
        prov = json.loads(pv.read_text(encoding="utf-8"))
        prov["delivery_package"] = rec
        pv.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    from engine.credits import RightsError  # noqa: PLC0415
    from engine.project import ProjectError  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="전달 패키지(제목·설명·태그·썸네일)")
    ap.add_argument("proj", type=Path)
    a = ap.parse_args(argv)
    proj = a.proj.resolve()
    try:
        rec = make_package(proj)
        res = StageResult(ok=True, stage="delivery_package", provenance={"delivery_package": rec},
                          artifacts={"dir": str(proj / "out" / "delivery"), "description_full": str(proj / "out" / "description_full.txt")})
    except (DeliveryError, ProjectError, RightsError, KeyError, ValueError, OSError) as ex:
        res = StageResult(ok=False, stage="delivery_package", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
