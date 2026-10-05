"""승인 게이트 화면 (v3.0.0, docs/handoff/16 §5, back_and_forth D-0040 작업 6).

Command Center 게이트 패널과 `orchestrator.main gate-view` 가 같은 텍스트를 쓴다(읽기 전용).
- ① SCRIPT_APPROVAL: 장면 목록(장면명·문장 수·예상 길이), 원고 전문(자막 텍스트), 출처 표, 린트 결과, 미디어 후보 요약.
- ② PREVIEW_APPROVAL: 프리뷰 컨택트 시트 경로, 프리뷰 컷 목록, provenance 요약, 예상 러닝타임.
- (v3.2.0) INTAKE·SOURCE_VERIFY 소스 확인 화면(`source_view`, 18 §7): 소스별 계정·시각·확인 여부·검증 status, claims 요약.
린트는 엔진 CLI(`script.lint`)를 engine_service 로 불러 얻는다(15 P1). 파일은 읽기만 한다.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import yaml

from orchestrator import engine_service
from schemas.models import ProjectState
from script.labels import check_project_labels
from script.media_suggest import suggest_media
from script.schema import Plan, Script

# 예상 길이 추정(plan.json 이 아직 없을 때): 한국어 발화 분당 글자 수(prompts/script.md 가정과 같음)
CHARS_PER_MIN: int = 320


def _script(pdir: Path) -> Script:
    return Script.model_validate(yaml.safe_load((pdir / "script.yaml").read_text(encoding="utf-8")))


def _plan(pdir: Path) -> Plan | None:
    p = pdir / "plan.json"
    return Plan.model_validate_json(p.read_text(encoding="utf-8")) if p.exists() else None


def script_gate_view(pdir: Path, runner: Callable = subprocess.run) -> tuple[str, dict[str, str]]:
    """게이트 ① 텍스트와 '보인 것' 요약(GateDecision.shown)."""
    sc = _script(pdir)
    plan = _plan(pdir)
    durs: dict[str, float] = {}
    if plan is not None:
        for s in plan.sentences:
            durs[s.scene] = durs.get(s.scene, 0.0) + s.dur
    lines = [f"[게이트 ① 원고 승인] {sc.title} — {sc.subtitle} ({sc.date})", "", "장면 목록"]
    total = 0.0
    for scene in sc.scenes:
        est = durs.get(scene.id) or sum(len(s.tts or s.text) for s in scene.sentences) / CHARS_PER_MIN * 60
        total += est
        lines.append(f"  {scene.id:<10} 문장 {len(scene.sentences):>2}  예상 {est:6.1f}초")
    lines.append(f"  합계 {sum(len(s.sentences) for s in sc.scenes)}문장 · 예상 {total:.1f}초"
                 + (" (plan.json 실측)" if plan else f" (글자 수 추정 {CHARS_PER_MIN}자/분)"))
    try:   # 검증 라벨 — 코드가 도시어 status 로 계산(D-0043). 불일치는 화면에 오류로
        labels = check_project_labels(pdir, sc)
        label_note = "" if labels is not None else " (도시어 없음 — 라벨 계산 안 함)"
    except ValueError as e:
        labels, label_note = None, f" — 라벨 오류: {e}"
    lines += ["", "원고 전문(자막) · [검증 라벨]" + label_note]
    src_rows: list[str] = []
    media_rows: list[str] = []
    for scene in sc.scenes:
        for k, s in enumerate(scene.sentences):
            sid = f"{scene.id}_{k}"
            lab = labels.labels[sid].label if labels is not None else None
            lines.append(f"  {sid:<12} {s.text}" + (f"  [{lab}]" if lab else ""))
            src_rows.append(f"  {sid:<12} {', '.join(s.sources) if s.sources else '(출처 없음)'}")
            if s.media is not None:
                ref = s.media.asset_id or f"검색어 {s.media.query!r}"
                media_rows.append(f"  {sid:<12} {s.media.kind} · {ref}" + (f" · '{s.media.at}'" if s.media.at else ""))
    lines += ["", "출처 표", *src_rows]
    from orchestrator.bundle_service import import_view_lines  # noqa: PLC0415 — v3.5.0 번들 출처(D-0064 쟁점 2)
    bl = import_view_lines(pdir)
    if bl:
        lines += ["", *bl]
    lint = engine_service.run_stage(pdir, "direction_validate", runner=runner)
    lines += ["", f"린트 — 오류 {len(lint.errors)} · 경고 {len(lint.warnings)}"]
    lines += [f"  오류 {e}" for e in lint.errors] + [f"  경고 {w}" for w in lint.warnings[:20]]
    if len(lint.warnings) > 20:
        lines.append(f"  … 경고 {len(lint.warnings) - 20}건 더")
    lines += ["", f"미디어 후보 — 원고 media 필드 {len(media_rows)}건", *media_rows]
    if plan is not None:   # 트리거 제안(14 §10.2, 제안만 — P8)
        sug = suggest_media(plan)
        lines.append(f"  트리거 제안 {len(sug)}건: " + ", ".join(f"{m.sid}({m.kind}·{m.trigger})" for m in sug[:12])
                     + (" …" if len(sug) > 12 else ""))
    else:
        lines.append("  트리거 제안 — plan.json 이 생기면(voice_timeline 뒤) 표시")
    if labels is not None:
        lines += ["", "검증 라벨 집계 " + json.dumps(labels.counts(), ensure_ascii=False)]
    shown = {"script": str(pdir / "script.yaml"), "lint_errors": str(len(lint.errors)),
             "lint_warnings": str(len(lint.warnings)), "est_sec": f"{total:.1f}"}
    return "\n".join(lines), shown


def preview_gate_view(pdir: Path) -> tuple[str, dict[str, str]]:
    """게이트 ② 텍스트와 '보인 것' 요약."""
    prev = pdir / "prev"
    sheet = prev / "sheet.jpg"
    cuts = sorted(prev.glob("p_*.png")) if prev.exists() else []
    lines = ["[게이트 ② 프리뷰 승인]", "",
             f"컨택트 시트  {sheet if sheet.exists() else '(없음 — preview 단계 먼저)'}",
             f"프리뷰 컷    {len(cuts)}장" + (f"  {cuts[0].name} … {cuts[-1].name}" if cuts else "")]
    plan = _plan(pdir)
    if plan is not None:
        m, s = divmod(plan.total, 60)
        lines.append(f"예상 러닝타임 {int(m)}분 {s:04.1f}초 ({plan.total:.3f}초, 목소리 {plan.voice})")
    pp = prev / "provenance.json"
    shown = {"sheet": str(sheet), "cuts": str(len(cuts))}
    if pp.exists():
        prov = json.loads(pp.read_text(encoding="utf-8"))
        fu = prov.get("features_used", {})
        lines += ["", "provenance 요약 (prev/provenance.json)",
                  f"  stages      {json.dumps(prov.get('stages', {}), ensure_ascii=False)}",
                  f"  카메라 이동 {fu.get('camera_moves')} · dip {fu.get('dips')} · 뱃지 {fu.get('badges')} · 카드 {fu.get('cards')}",
                  f"  패널        {', '.join(fu.get('panels', []))}",
                  f"  미디어      {json.dumps(fu.get('media', {}), ensure_ascii=False)}",
                  f"  drops       {len(prov.get('drops', []))}건 · 연출 경고 {len(prov.get('lint_warnings', []))}건",
                  f"  rules_hash  {str(prov.get('rules_hash', ''))[:12]}"]
        shown.update({"provenance": str(pp), "drops": str(len(prov.get("drops", [])))})
    else:
        lines += ["", "provenance 요약 (없음 — preview 단계가 prev/provenance.json 을 쓴다)"]
    lines += ["", *media_summary(pdir, shown), "", *_camera_table(pdir, shown), "", *_qa_rounds(pdir, shown)]
    return "\n".join(lines), shown


def media_summary(pdir: Path, shown: dict[str, str] | None = None) -> list[str]:
    """v5.6.0(사용자 결정 2026-10-05 "없으면 없는 거지 막을 필요는 없다" — 막지 않고 보이게, PIPELINE-AP-019) —
    인용·기사 조판·실사(사진·영상·컷아웃) 쓴 수 / 쓸 수 있던 수, 무기 이름 문장의 실사 유무, 연출이 적은 이유(media_note)."""
    import re  # noqa: PLC0415

    import yaml  # noqa: PLC0415

    from rules import load_rules  # noqa: PLC0415
    from workers.direction_io import media_text, quote_candidates  # noqa: PLC0415

    dp = pdir / "direction.yaml"
    if not dp.exists():
        return ["미디어·인용 요약 — direction.yaml 없음"]
    doc = yaml.safe_load(dp.read_text(encoding="utf-8")) or {}
    evs = doc.get("events", [])
    used = {k: sum(1 for e in evs if e.get("type") in kinds) for k, kinds in
            {"quote": ("quote",), "article": ("article",), "real": ("photo", "clip", "cutout")}.items()}
    reg = media_text(pdir)
    avail = {"article": len(re.findall(r"^- [^:]+: article ", reg, re.M)),
             "real": len(re.findall(r"^- [^:]+: (photo|video|cutout) ", reg, re.M))}
    qc = quote_candidates(pdir)
    quoted = " ".join(str(e) for e in evs if e.get("type") == "quote")
    unused = sorted({q["claim_id"] for q in qc if q["original"][:12] not in quoted})
    out = ["미디어·인용 요약 (막지 않는다 — 보고 판단)",
           f"  인용(따옴표)   {used['quote']}건 사용 · 원문 따옴표 후보 {len(qc)}건" + (f" — 안 쓴 후보 {', '.join(unused)}" if unused and len(qc) else ""),
           f"  기사 조판      {used['article']}건 사용 · 등록 {avail['article']}건" + ("  (tools/article_register.py 로 등록)" if not avail["article"] else ""),
           f"  실사(사진·영상) {used['real']}건 사용 · 등록 {avail['real']}건" + ("  (tools/media_fetch.py search 로 후보)" if not avail["real"] else "")]
    reals = [e for e in evs if e.get("type") in ("photo", "clip", "cutout") and e.get("mid")]
    if reals:   # 실사는 콘티 판에서 자리표시라 여기서 출처·권리를 본다(사용자 확인용 목록)
        from engine.media_registry import load_media_registry  # noqa: PLC0415

        mr = load_media_registry()
        out += [f"    {e['type']:<6} {e['mid']} · {mr[e['mid']].caption} · {mr[e['mid']].file_note} · {mr[e['mid']].license[:40]} · {mr[e['mid']].url or ''}"
                for e in reals if e["mid"] in mr]
    sp = pdir / "script.yaml"
    if sp.exists():
        terms = load_rules().weapon_photo.terms
        hits = sorted({w for sc in (yaml.safe_load(sp.read_text(encoding="utf-8")) or {}).get("scenes", [])
                       for s in sc.get("sentences", []) for w in terms if w in s.get("text", "")})
        if hits:
            out.append(f"  무기 이름       {', '.join(hits)} — 실사 {'있음' if used['real'] else '없음'}")
    if doc.get("media_note"):
        out.append(f"  연출 메모       {doc['media_note']}")
    elif not (used["quote"] and used["article"] and used["real"]):
        out.append("  연출 메모       (없음 — 0건인 항목의 이유를 direction.yaml media_note 에 적는다)")
    if shown is not None:
        shown.update({"media_used": f"quote {used['quote']} · article {used['article']} · real {used['real']}",
                      "quote_candidates": str(len(qc))})
    return out


def _camera_table(pdir: Path, shown: dict[str, str]) -> list[str]:
    """카메라 "제안 vs 현재" 표(v3.3.0 D-0056 작업 5) — 제안은 옵션, 자동 적용하지 않는다(P8). 판단은 사람·연출가."""
    from engine.camera_suggest import load_suggest  # noqa: PLC0415

    cs = load_suggest(pdir)
    if cs is None:
        return ["카메라 제안 — 없음(engine camera_suggest 단계가 prev/camera_suggest.json 을 쓴다)"]
    out = ["카메라 제안 vs 현재 (prev/camera_suggest.json — 참고용, 자동 적용 없음)",
           "  시각     장면        현재 lon/lat/w (전환)        제안 lon/lat/w (전환)        현재 담김 제안 담김"]
    for s in cs.shots:
        c = s.current
        cur = f"{c.lon:7.2f} {c.lat:6.2f} {c.w:5.1f} ({s.current_mode})"
        if s.suggested is None:
            out.append(f"  {s.t:7.1f}  {s.scene:<10}  {cur:<28}  — {s.note}")
            continue
        g = s.suggested
        sug = f"{g.lon:7.2f} {g.lat:6.2f} {g.w:5.1f} ({s.suggested_transition or '-'})"
        cf = "-" if s.current_fits is None else ("예" if s.current_fits else "아니오")
        out.append(f"  {s.t:7.1f}  {s.scene:<10}  {cur:<28}  {sug:<28}  {cf:<8} {'예' if s.fits else '아니오 ' + s.note}")
    out.append(f"  숏 규칙(현재) 경고 {len(cs.shot_issues_current)}건" + "".join(f"\n    {i}" for i in cs.shot_issues_current))
    shown.update({"camera_suggest": str(sum(s.suggested is not None for s in cs.shots))})
    return out


def _qa_rounds(pdir: Path, shown: dict[str, str]) -> list[str]:
    """AI 연출 판 목록(D-0049 쟁점 3) — 사람은 다른 판을 골라 승인할 수 있다(approve --version N → chosen_version)."""
    from engine.qa import QALoopRecord, QAVerdict  # noqa: PLC0415

    p = pdir / "prev" / "qa_loop.json"
    if not p.exists():
        return ["AI 검수 — 기록 없음(사람 연출이면 검수 루프를 돌지 않는다)"]
    rec = QALoopRecord.model_validate_json(p.read_text(encoding="utf-8"))
    sel = rec.selected.version if rec.selected else None
    out = [f"AI 연출 판 목록 — {len(rec.rounds)}판" + (f", 선택 v{sel} ({rec.selected.by}: {rec.selected.reason})" if rec.selected else "")]
    for r in rec.rounds:
        qa = f"검수 hard {r.qa_hard} soft {r.qa_soft}" if r.qa else "검수 없음(검사 hard 잔존)"
        out.append(f"  {'*' if r.version == sel else ' '} v{r.version}  checks hard {r.checks_hard} · {qa} · 시트 prev/{r.sheet}")
    pick = next((r for r in rec.rounds if r.version == sel), None)
    if pick is not None and pick.qa and (pdir / "prev" / pick.qa).exists():
        v = QAVerdict.model_validate_json((pdir / "prev" / pick.qa).read_text(encoding="utf-8"))
        out.append(f"  선택 판 잔여 이슈 {len(v.issues)}건")
        out += [f"    {i.severity:<4} {i.frame} {i.fix.event_ref if i.fix else i.category} — {i.evidence[:80]}" for i in v.issues]
    shown.update({"qa_rounds": str(len(rec.rounds)), "qa_selected": str(sel)})
    return out


def gate_view(pdir: Path, state: ProjectState | str, runner: Callable = subprocess.run) -> tuple[str, dict[str, str]]:
    st = state if isinstance(state, ProjectState) else ProjectState(state)
    if st == ProjectState.SCRIPT_APPROVAL:
        return script_gate_view(pdir, runner)
    if st == ProjectState.PREVIEW_APPROVAL:
        return preview_gate_view(pdir)
    raise ValueError(f"'{st.value}' 는 승인 게이트가 아니다")


__all__ = ["gate_view", "preview_gate_view", "script_gate_view"]


def source_view(pdir: Path) -> str:
    """소스 확인 화면(v3.2.0, 18 §7) — 사용자 확인 필드가 빈 소스를 앞에. Command Center 'c' 로 확인한다."""
    from orchestrator.source_intake import load_sources  # noqa: PLC0415
    from orchestrator.source_verify import load_claims  # noqa: PLC0415

    f = load_sources(pdir)
    if not f.sources:
        return "소스 없음 — CLI add-source 또는 웹 /intake/{pid} 에서 넣는다(기사 URL·본문·X 텍스트·X 캡처·파일)"
    rows = []
    for s in sorted(f.sources, key=lambda x: (x.confirmed, x.id)):
        if s.type == "x_post":
            who = f"{s.account_name} {s.handle} [{s.account_class}] · {s.posted_at or '시각 미상'}"
            body = (s.text_ko or s.text_original)[:60]
        elif s.type == "article":
            who, body = f"{s.publisher} · {s.published_at}", s.headline_ko or s.headline_original
        else:
            who, body = f"{s.issuer} · {s.published_at or '-'}", s.title
        conf = f"확인 {s.confirmed_by}" if s.confirmed else "미확인 — c 로 확인"
        ver = s.verification.status if s.verification else "-"
        rows.append(f"{s.id:14} {conf:16} 검증 {ver:12} {who}\n{'':14} {body}")
    from orchestrator.bundle_service import import_view_lines  # noqa: PLC0415

    out = [f"소스 {len(f.sources)}건 · 미확인 {sum(not s.confirmed for s in f.sources)}건", *rows, *import_view_lines(pdir)]
    claims = load_claims(pdir)
    if claims is not None:
        st = {k: sum(c.status == k for c in claims.claims) for k in ("verified", "corroborated", "unverified", "disputed")}
        out.append(f"claims {len(claims.claims)}개 · {st}")
    return "\n".join(out)

