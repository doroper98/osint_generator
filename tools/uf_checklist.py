"""사용자 의견 점검표(v7.4.0 back_and_forth D-1000 S4-2 — 감독이 "표만 보고 통과"하지 못하게, LLM-AP-023).

    python tools/uf_checklist.py projects/<pid> [--src animatic|final|preview]

`rules/user_feedback.yaml` 의 의견 전부를 out/uf_checklist.md 한 표로:
- 장치가 본 엔진 검사(check)면 이번 산출의 provenance `user_feedback_guards` 결과(pass = 0건, fail = 건수, skipped, 미실행).
- 시험·규칙·코드·문서 장치만 있는 의견은 "눈 확인" 칸(빈 칸 [ ])과 볼 시각 후보를 단다 — 분류 낱말(사진·배지·지도·자막·전환·차트)로
  이 영상에서 그 종류 요소가 보이는 시각을 골라 review_sheet 칸(every 초 격자)에 맞춘다.
감독은 사용자에게 보내기 전에 이 표의 빈 칸을 모두 채운다(back_and_forth/README §6.3a). 마지막 줄 = 결과 JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.timing import stage_timer  # noqa: E402

PROV = {"animatic": "out/animatic_provenance.json", "final": "out/provenance.json", "preview": "prev/provenance.json"}
# 분류 낱말 → 이 영상에서 볼 요소 종류(볼 시각 후보). 낱말은 원장 category·원문에서 찾는다
CLASSES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "사진": (("사진", "미디어", "영상", "클립", "기사", "인용", "조판"), ("photo", "clip", "cutout", "article", "quote", "post")),
    "배지": (("뱃지", "배지", "인물", "초상", "국기", "휘장"), ("badge",)),
    "지도": (("지도", "경로", "카메라", "마커", "국경", "지명", "전황", "좌표"), ("route", "marker", "boom", "country", "ships")),
    "자막": (("자막", "원고", "글자", "문구"), ()),
    "전환": (("전환", "엔딩", "타이틀", "암전", "카드"), ("dip",)),
    "차트": (("차트", "시간축", "패널", "축", "시리즈", "그래프", "막대"), ("series", "panel", "island")),
}
EVERY = 3.0   # review_sheet 기본 칸 간격과 같은 값(칸 번호를 맞추려고)


def classes_of(text: str) -> list[str]:
    return [k for k, (words, _) in CLASSES.items() if any(w in text for w in words)]


def look_times(events: list[dict], kinds: tuple[str, ...], every: float, n: int = 4) -> list[float]:
    """그 종류 요소가 보이는 구간 가운데를 review_sheet 칸 시각(every 배수)으로 — 최대 n 개, 앞에서부터 고르게."""
    mids = sorted({round(((e["t0"] + e["t1"]) / 2) / every) * every for e in events if e.get("type") in kinds and "t0" in e and "t1" in e})
    if len(mids) <= n:
        return mids
    return [mids[round(i * (len(mids) - 1) / (n - 1))] for i in range(n)]


def build(proj: Path, src: str) -> tuple[str, dict]:
    from engine.checks import HARD  # noqa: PLC0415
    from engine.project import load_project  # noqa: PLC0415
    from rules import load_user_feedback  # noqa: PLC0415

    prov_p = proj / PROV[src]
    guards = {}
    if prov_p.exists():
        guards = {g["id"]: g["checks"] for g in json.loads(prov_p.read_text(encoding="utf-8")).get("user_feedback_guards") or []}
    P = load_project(proj, animatic=src == "animatic")  # noqa: N806
    rows, stat = [], {"auto_pass": 0, "auto_fail": 0, "eye": 0, "not_run": 0}
    for e in load_user_feedback().entries:
        checks = [g.ref for g in e.guards if g.kind == "check"]
        others = sorted({g.kind for g in e.guards if g.kind != "check"})
        ran = guards.get(e.id, {})
        if checks:
            parts = []
            for c in checks:
                v = ran.get(c)
                bad = f"**fail {v}**" if c in HARD else f"warn {v}"   # 경고 등급 검사는 실패가 아니다(검사 표 engine.checks HARD·WARN)
                parts.append(f"{c}: " + ("미실행" if v is None else "skipped" if v == "skipped" else "pass" if v == 0 else bad))
            auto = "; ".join(parts)
            if any(c in HARD and ran.get(c) not in (None, "skipped", 0) for c in checks):
                stat["auto_fail"] += 1
            elif all(ran.get(c) == 0 or (c not in HARD and isinstance(ran.get(c), int)) for c in checks):
                stat["auto_pass"] += 1
            else:
                stat["not_run"] += 1
        else:
            auto = "—"
        need_eye = not checks or any(ran.get(c) in (None, "skipped") for c in checks)
        cls = classes_of(f"{e.category} {e.quote}")
        times = sorted({t for c in cls for t in look_times(P.events, CLASSES[c][1], EVERY)})
        eye = "[ ]" if need_eye else "—"
        stat["eye"] += need_eye
        look = ", ".join(f"{t:.0f}s" for t in times[:6]) if need_eye and times else ("자막 전 구간" if need_eye and "자막" in cls else "")
        quote = e.quote.replace("\n", " ").replace("|", "/")
        rows.append(f"| {e.id} | {e.date} | {e.category} | {quote[:70]}{'…' if len(quote) > 70 else ''} | "
                    f"{', '.join(others) or '—'} | {auto} | {eye} | {'·'.join(cls) or '-'} | {look} |")
    head = (f"# 사용자 의견 점검표 — {proj.name} ({src})\n\n"
            f"provenance: `{PROV[src]}`{'' if prov_p.exists() else ' (없음 — 자동 검사 결과 미실행)'} · 의견 {len(rows)}개 · "
            f"자동 pass {stat['auto_pass']} · 자동 fail {stat['auto_fail']} · 미실행 {stat['not_run']} · 눈 확인 {stat['eye']}\n\n"
            f"볼 시각 = review_sheet `--src {src} --every {EVERY:g}` 칸 시각. 눈 확인 칸 [ ] 을 모두 [x](또는 사유)로 채운 뒤에만 사용자에게 보낸다.\n\n"
            "| UF | 날짜 | 분류 | 원문 | 다른 장치 | 자동 검사 | 눈 확인 | 분류 낱말 | 볼 시각 |\n|---|---|---|---|---|---|---|---|---|\n")
    return head + "\n".join(rows) + "\n", stat


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="사용자 의견 점검표(D-1000 S4)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--src", choices=list(PROV), default="animatic")
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    with stage_timer(proj, "review.uf_checklist", src=args.src):
        md, stat = build(proj, args.src)
        dest = proj / "out" / "uf_checklist.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(md, encoding="utf-8")
    print(json.dumps({"ok": True, "checklist": str(dest), **stat}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
