"""Dynamic Intake Page — `intake_plan.json` 을 사용자에게 보여주고 결정을 받는 웹 폼.

docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md 의 정식 구현 첫 단계 (Phase 3, v0.3.0).

엔드포인트
---------
- GET  /healthz                : 헬스체크 (배포 검증용, JSON 응답)
- GET  /intake/{pid}           : intake_plan.json 을 카드 형태 HTML 로 렌더
- POST /intake/{pid}/submit    : 사용자 결정 (모드/메모/링크) 을 SourceIntake 로
                                 영속화하고 `intake_pending_user → source_collecting`
                                 상태 전이

설계 원칙
--------
- **Pydantic 모델만 사용**. 도메인 데이터는 `IntakePlan` / `SourceIntake` /
  `UserDecision` 으로만 다루며 raw dict 사용 금지 (CLAUDE.md C2).
- **상태 전이는 project_manager 가 유일한 진입점**. 본 모듈은 직접 manifest 를
  쓰지 않고 `transition_state` 를 호출만 함.
- **HTML 은 외부 템플릿 엔진 없이 인라인 문자열**. Jinja 등 추가 의존성 회피.
  CSS 도 인라인 (Phase 3 의 와이어프레임 수준).
- HTML 출력의 사용자/manifest 유래 문자열은 `html.escape` 로 escape 해 XSS 방지.

실행
----
    uvicorn web.intake_page_app:app --host 127.0.0.1 --port 8765 --reload

또는 본 모듈의 `run_server()` 헬퍼:

    python -m web.intake_page_app --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.project_manager import load_manifest, transition_state
from schemas.models import (
    IntakeMode,
    IntakePlan,
    IntakePlanItem,
    ProjectManifest,
    ProjectState,
    SourceIntake,
    UserDecision,
)


app = FastAPI(title="OSINT Dynamic Intake Page", version="0.3.0")


# ---------------------------------------------------------------------------
# 경로 헬퍼
# ---------------------------------------------------------------------------


def _intake_plan_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return project_dir(project_id, cfg) / "01_intake" / "intake_plan.json"


def _source_intake_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return project_dir(project_id, cfg) / "01_intake" / "source_intake.json"


def _load_intake_plan(project_id: str, cfg: Optional[AppConfig] = None) -> IntakePlan:
    path = _intake_plan_path(project_id, cfg)
    if not path.exists():
        raise FileNotFoundError(
            f"intake_plan.json 이 없습니다: {path}. "
            f"먼저 `python -m orchestrator.main plan-intake {project_id}` 를 실행하십시오."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return IntakePlan.model_validate(raw)


# ---------------------------------------------------------------------------
# 라우트
# ---------------------------------------------------------------------------


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "intake_page", "version": app.version}


@app.get("/")
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/healthz")


@app.get("/intake/{project_id}", response_class=HTMLResponse)
async def get_intake_page(project_id: str) -> HTMLResponse:
    try:
        manifest = load_manifest(project_id)
        plan = _load_intake_plan(project_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return HTMLResponse(_render_intake_html(manifest, plan))


@app.post("/intake/{project_id}/submit")
async def submit_intake(project_id: str, request: Request) -> JSONResponse:
    """form-urlencoded 제출을 받아 SourceIntake 로 영속화 + 상태 전이."""
    try:
        manifest = load_manifest(project_id)
        plan = _load_intake_plan(project_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    form = await request.form()
    decisions = _form_to_decisions(plan, form)
    intake = SourceIntake(project_id=project_id, user_decisions=decisions)

    out_path = _source_intake_path(project_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(intake.model_dump_json(indent=2), encoding="utf-8")

    # 상태 전이: intake_pending_user → source_collecting
    # 이미 다른 상태이면 transition_state 가 ValueError. 사용자에게 그대로 노출.
    try:
        manifest = transition_state(
            manifest,
            ProjectState.SOURCE_COLLECTING,
            reason="Dynamic Intake Page 제출",
        )
    except ValueError as e:
        # source_intake.json 은 이미 저장됐으므로 잃지 않는다. 상태 전이 실패는 응답에 명시.
        return JSONResponse(
            status_code=409,
            content={
                "saved": str(out_path),
                "state_transition_error": str(e),
                "current_state": _state_str(manifest.current_state),
            },
        )

    return JSONResponse(
        content={
            "saved": str(out_path),
            "current_state": _state_str(manifest.current_state),
            "decisions": len(decisions),
        }
    )


# ---------------------------------------------------------------------------
# Form → UserDecision[] 변환
# ---------------------------------------------------------------------------


def _form_to_decisions(plan: IntakePlan, form) -> list[UserDecision]:
    """form 데이터를 plan 의 항목 순서에 맞춰 `UserDecision[]` 으로 변환.

    필드 컨벤션 (각 IntakePlanItem 당):
    - `mode__{item_id}`              : IntakeMode 문자열 (필수)
    - `user_note__{item_id}`         : 자유 메모
    - `provided_links__{item_id}`    : 줄바꿈 또는 공백 구분 URL 목록
    - `google_drive_links__{item_id}`: 동일
    - `uploaded_files__{item_id}`    : (Phase 3 에선 multipart 미구현, 향후 확장)
    - `ai_delegate_remaining__{item_id}`: "1" / "true" / "on" 이면 True

    알 수 없는 필드는 무시. mode 가 누락된 항목은 default_mode 로 fallback.
    """
    decisions: list[UserDecision] = []
    for item in plan.required_items:
        iid = item.item_id
        mode_str = (form.get(f"mode__{iid}") or "").strip()
        if mode_str:
            try:
                mode = IntakeMode(mode_str)
            except ValueError:
                # 알 수 없는 enum 값이면 default_mode 로 fallback
                mode = _coerce_mode(item.default_mode)
        else:
            mode = _coerce_mode(item.default_mode)

        decision = UserDecision(
            item_id=iid,
            mode=mode,
            user_note=(form.get(f"user_note__{iid}") or "").strip(),
            provided_links=_split_lines(form.get(f"provided_links__{iid}")),
            google_drive_links=_split_lines(form.get(f"google_drive_links__{iid}")),
            uploaded_files=_split_lines(form.get(f"uploaded_files__{iid}")),
            ai_delegate_remaining=_truthy(form.get(f"ai_delegate_remaining__{iid}")),
        )
        decisions.append(decision)
    return decisions


def _coerce_mode(value) -> IntakeMode:
    if isinstance(value, IntakeMode):
        return value
    try:
        return IntakeMode(str(value))
    except ValueError:
        return IntakeMode.AI_DELEGATE


def _split_lines(value) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for line in str(value).splitlines():
        line = line.strip()
        if line:
            parts.append(line)
    return parts


def _truthy(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "on", "yes"}


def _state_str(state) -> str:
    return state.value if hasattr(state, "value") else str(state)


# ---------------------------------------------------------------------------
# HTML 렌더링 (외부 템플릿 엔진 없이)
# ---------------------------------------------------------------------------


def _render_intake_html(manifest: ProjectManifest, plan: IntakePlan) -> str:
    cards = "\n".join(_render_item_card(item) for item in plan.required_items)
    title = html.escape(manifest.title)
    pid = html.escape(manifest.project_id)
    cat = html.escape(_state_str(manifest.category))
    state = html.escape(_state_str(manifest.current_state))
    assessment = html.escape(plan.orchestrator_assessment or "(orchestrator 평가 없음)")
    duration = manifest.target_duration_min

    return (
        "<!doctype html>\n"
        "<html lang=\"ko\"><head><meta charset=\"utf-8\">\n"
        "<title>Intake — " + title + "</title>\n"
        "<style>\n"
        "body{font-family:system-ui,sans-serif;background:#f4f4f7;color:#222;margin:0;padding:24px;}\n"
        "h1{margin:0 0 8px 0;font-size:1.4rem;}\n"
        ".meta{color:#555;font-size:0.9rem;margin-bottom:16px;}\n"
        ".assessment{background:#fff8e1;border-left:4px solid #f0b400;padding:12px 16px;border-radius:6px;margin-bottom:24px;}\n"
        ".card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:16px;}\n"
        ".card h2{margin:0 0 4px 0;font-size:1.05rem;}\n"
        ".badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.75rem;margin-left:8px;vertical-align:middle;}\n"
        ".badge-must_use{background:#c62828;color:#fff;}\n"
        ".badge-high{background:#ef6c00;color:#fff;}\n"
        ".badge-normal{background:#1565c0;color:#fff;}\n"
        ".badge-low{background:#616161;color:#fff;}\n"
        ".desc{color:#444;margin:6px 0;}\n"
        ".why{color:#1565c0;font-size:0.9rem;margin:4px 0;}\n"
        ".risk{color:#c62828;font-size:0.85rem;margin:4px 0;}\n"
        ".modes{margin-top:10px;}\n"
        ".modes label{display:inline-block;margin-right:12px;font-size:0.9rem;}\n"
        ".extras{margin-top:8px;display:grid;grid-template-columns:repeat(2,1fr);gap:8px;}\n"
        ".extras textarea,.extras input{width:100%;font-family:inherit;font-size:0.85rem;padding:6px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;}\n"
        ".footer{margin-top:24px;text-align:right;}\n"
        ".footer button{background:#1565c0;color:#fff;border:0;border-radius:6px;padding:10px 18px;font-size:1rem;cursor:pointer;}\n"
        ".footer button:hover{background:#0d3f78;}\n"
        "</style></head><body>\n"
        "<h1>" + title + " <span class=\"badge badge-normal\">" + cat + "</span></h1>\n"
        "<div class=\"meta\">project_id=" + pid + " &middot; current_state=" + state
        + " &middot; target_duration_min=" + str(duration) + "</div>\n"
        "<div class=\"assessment\"><strong>Orchestrator 평가:</strong> " + assessment + "</div>\n"
        "<form method=\"POST\" action=\"/intake/" + pid + "/submit\">\n"
        + cards + "\n"
        "<div class=\"footer\"><button type=\"submit\">영상 생성 착수</button></div>\n"
        "</form>\n"
        "</body></html>\n"
    )


def _render_item_card(item: IntakePlanItem) -> str:
    iid = html.escape(item.item_id)
    label = html.escape(item.label)
    desc = html.escape(item.description)
    why = html.escape(item.why_needed)
    priority = _state_str(item.priority)
    badge = "badge-" + priority
    default_mode = _state_str(item.default_mode)

    risk_html = ""
    if item.risk_notice:
        risk_html = (
            "<div class=\"risk\"><strong>리스크 안내:</strong> "
            + html.escape(item.risk_notice) + "</div>\n"
        )

    # user_options 이 비어 있으면 IntakeMode 전체 + default_mode 만 표시.
    options = item.user_options or [item.default_mode]
    if item.default_mode not in options:
        options = [item.default_mode, *options]
    seen: set[str] = set()
    radios = []
    for mode in options:
        mode_str = _state_str(mode)
        if mode_str in seen:
            continue
        seen.add(mode_str)
        checked = " checked" if mode_str == default_mode else ""
        radios.append(
            "<label><input type=\"radio\" name=\"mode__" + iid
            + "\" value=\"" + html.escape(mode_str) + "\"" + checked + "> "
            + html.escape(mode_str) + "</label>"
        )

    return (
        "<div class=\"card\" id=\"card-" + iid + "\">\n"
        "<h2>" + label + " <span class=\"badge " + badge + "\">" + priority + "</span></h2>\n"
        "<div class=\"desc\">" + desc + "</div>\n"
        "<div class=\"why\"><strong>필요한 이유:</strong> " + why + "</div>\n"
        + risk_html
        + "<div class=\"modes\">" + " ".join(radios) + "</div>\n"
        "<div class=\"extras\">\n"
        "  <textarea name=\"user_note__" + iid + "\" rows=\"2\" placeholder=\"메모\"></textarea>\n"
        "  <textarea name=\"provided_links__" + iid + "\" rows=\"2\" placeholder=\"링크 (한 줄에 하나)\"></textarea>\n"
        "</div>\n"
        "</div>"
    )


# ---------------------------------------------------------------------------
# 실행 진입점 (개발 편의용)
# ---------------------------------------------------------------------------


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """uvicorn 으로 서버 기동. 운영에서는 직접 `uvicorn ...` 호출 권장."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


def _parse_argv(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="web.intake_page_app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args(argv)


if __name__ == "__main__":
    ns = _parse_argv()
    run_server(host=ns.host, port=ns.port)
