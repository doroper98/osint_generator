"""승인 게이트 화면 (v3.0.0, docs/handoff/16 §5, back_and_forth D-0040 작업 6).

Command Center 게이트 패널과 `orchestrator.main gate-view` 가 같은 텍스트를 쓴다(읽기 전용).
- ① SCRIPT_APPROVAL: 장면 목록(장면명·문장 수·예상 길이), 원고 전문(자막 텍스트), 출처 표, 린트 결과, 미디어 후보 요약.
- ② PREVIEW_APPROVAL: 프리뷰 컨택트 시트 경로, 프리뷰 컷 목록, provenance 요약, 예상 러닝타임.
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
    lines += ["", *_qa_rounds(pdir, shown)]
    return "\n".join(lines), shown


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
