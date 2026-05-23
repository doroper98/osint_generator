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
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from orchestrator.config import AppConfig, project_dir
from orchestrator.intake_service import IntakePlanningError, run_intake_planner
from orchestrator.project_manager import (
    load_manifest,
    new_project,
    transition_state,
    validate_project_id,
)
from schemas.models import (
    Category,
    IntakeMode,
    IntakePlan,
    IntakePlanItem,
    ProjectManifest,
    ProjectState,
    SourceIntake,
    UserDecision,
)


logger = logging.getLogger(__name__)


# v0.3.1: codex 4차 리뷰 H2 — form body 크기 상한 (DoS 방어).
# content-length 기준으로 거부. 256 KiB 면 인테이크 제출 (텍스트 메모/링크) 에 충분.
MAX_FORM_BYTES: int = 256 * 1024
# 호출자 (테스트, 운영 튜닝) 가 한도를 갱신할 수 있게 dict 가 아닌 모듈 변수.


app = FastAPI(title="OSINT Dynamic Intake Page", version="0.7.0")


# ---------------------------------------------------------------------------
# 입력 검증 (v0.3.1 C1 — path traversal 차단)
# ---------------------------------------------------------------------------


def _validated_pid(project_id: str) -> str:
    """`{project_id}` path parameter 를 정책 정규식으로 검증.

    `project_manager.validate_project_id` 와 동일 정책. 위반 시 400 응답.
    실패 메시지에 사용자 입력 자체는 노출하지 않는다 (정찰 가치 축소).
    """
    try:
        return validate_project_id(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid project_id")


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
    return RedirectResponse(url="/new")


@app.get("/new", response_class=HTMLResponse)
async def get_new_project_page() -> HTMLResponse:
    """주제 + 초기 링크 입력 폼. 제출하면 프로젝트 생성 + intake_plan 생성으로 이어진다."""
    return HTMLResponse(_render_new_project_html())


@app.post("/new")
async def create_project(request: Request):
    """주제/카테고리/길이/초기 링크를 받아 프로젝트 생성 + IntakePlanner 실행.

    성공 시 생성된 프로젝트의 동적 인테이크 페이지(`/intake/{pid}`)로 303 리다이렉트.

    - C1: project_id 정책 검증 (400).
    - H2: content-length 가 MAX_FORM_BYTES 초과면 413.
    - 중복 project_id 는 409.
    - IntakePlanner 실패는 500 (프로젝트 manifest 는 생성된 상태로 남음 — 사용자가
      backend 를 바꿔 재시도하거나 CLI `plan-intake --force` 로 이어갈 수 있음).
    """
    cl = request.headers.get("content-length")
    if cl is not None:
        try:
            cl_int = int(cl)
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid Content-Length header")
        if cl_int > MAX_FORM_BYTES:
            raise HTTPException(status_code=413, detail="request body too large")

    form = await request.form()
    project_id = (form.get("project_id") or "").strip()
    try:
        project_id = validate_project_id(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid project_id")

    title = (form.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    category_str = (form.get("category") or "").strip()
    try:
        category = Category(category_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid category")

    duration = _parse_duration(form.get("target_duration_min"))
    topic_summary = (form.get("topic_summary") or "").strip()
    initial_links = _split_lines(form.get("initial_links"))
    backend = (form.get("backend") or "claude").strip()
    if backend not in {"claude", "codex"}:
        raise HTTPException(status_code=400, detail="invalid backend")

    try:
        new_project(
            project_id=project_id,
            title=title,
            category=category,
            target_duration_min=duration,
            topic_summary=topic_summary,
            initial_links=initial_links,
        )
    except FileExistsError:
        return JSONResponse(
            status_code=409,
            content={"error": "project already exists", "project_id": project_id},
        )

    try:
        run_intake_planner(project_id, backend=backend)
    except IntakePlanningError as e:
        logger.warning("new-project planner fail — pid=%s kind=%s", project_id, e.kind)
        return JSONResponse(
            status_code=500,
            content={
                "error": "intake planning failed",
                "kind": e.kind,
                "detail": str(e),
            },
        )
    except ValueError as e:
        # 상태 전이 실패 — 보통 다른 프로세스/라우트가 동시에 상태를 바꾼 경우.
        logger.warning("new-project transition fail — pid=%s err=%s", project_id, e)
        return JSONResponse(
            status_code=409,
            content={"error": "project state changed concurrently; retry", "detail": str(e)},
        )
    except Exception:  # noqa: BLE001 — 라우트 경계: 구조화 500 보장 + traceback 로깅
        logger.exception("new-project unexpected error — pid=%s", project_id)
        return JSONResponse(
            status_code=500,
            content={"error": "internal error during intake planning"},
        )

    return RedirectResponse(url=f"/intake/{project_id}", status_code=303)


@app.get("/intake/{project_id}", response_class=HTMLResponse)
async def get_intake_page(project_id: str) -> HTMLResponse:
    project_id = _validated_pid(project_id)
    try:
        manifest = load_manifest(project_id)
        plan = _load_intake_plan(project_id)
    except FileNotFoundError as e:
        # v0.3.1 H1: 절대경로가 담긴 원본 메시지는 서버 로그에만 남기고
        # 클라이언트엔 generic 메시지만 노출.
        logger.warning("intake page 404 — pid=%s detail=%s", project_id, e)
        raise HTTPException(
            status_code=404,
            detail="intake plan not found for the requested project",
        )
    return HTMLResponse(_render_intake_html(manifest, plan))


@app.post("/intake/{project_id}/submit")
async def submit_intake(project_id: str, request: Request) -> JSONResponse:
    """form-urlencoded 제출을 받아 SourceIntake 로 영속화 + 상태 전이.

    v0.3.1 (codex 4차 리뷰 흡수):
    - C1: project_id 정책 정규식 검증.
    - H2: content-length 가 MAX_FORM_BYTES 초과면 즉시 413.
    - M1: source_intake.json 을 transition 검증을 통과한 뒤에만 영속화 (이전엔 write
          먼저 한 뒤 transition 검증 → 잘못된 상태에서도 파일 덮어쓰기 가능했음).
    """
    project_id = _validated_pid(project_id)

    cl = request.headers.get("content-length")
    if cl is not None:
        try:
            if int(cl) > MAX_FORM_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="request body too large",
                )
        except ValueError:
            # 위조된 content-length 헤더는 무시하고 진행. 실제 본문 길이 검증은
            # `request.form()` 의 starlette 내부 한도가 별도로 처리.
            pass

    try:
        manifest = load_manifest(project_id)
        plan = _load_intake_plan(project_id)
    except FileNotFoundError as e:
        logger.warning("intake submit 404 — pid=%s detail=%s", project_id, e)
        raise HTTPException(
            status_code=404,
            detail="intake plan not found for the requested project",
        )

    # v0.3.1 M1: write 전에 state precondition 검증. transition_state 와 동일한 게이트를
    # 두 번 사용하지만, 첫 번째 호출은 "쓰기 허용 여부" 만 가늠 (실제 전이는 아래에서).
    current_str = _state_str(manifest.current_state)
    if current_str != ProjectState.INTAKE_PENDING_USER.value:
        return JSONResponse(
            status_code=409,
            content={
                "error": "state precondition failed",
                "expected_state": ProjectState.INTAKE_PENDING_USER.value,
                "current_state": current_str,
            },
        )

    form = await request.form()
    decisions = _form_to_decisions(plan, form)
    intake = SourceIntake(project_id=project_id, user_decisions=decisions)

    # 상태 전이를 먼저 시도. 성공해야만 파일을 디스크에 쓴다.
    try:
        manifest = transition_state(
            manifest,
            ProjectState.SOURCE_COLLECTING,
            reason="Dynamic Intake Page 제출",
        )
    except ValueError as e:
        # 위 precondition 통과 후에도 전이가 실패한 경우 (드물지만 race 가능).
        logger.warning("intake submit transition fail — pid=%s err=%s", project_id, e)
        return JSONResponse(
            status_code=409,
            content={
                "error": "state transition failed",
                "current_state": _state_str(manifest.current_state),
            },
        )

    out_path = _source_intake_path(project_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(intake.model_dump_json(indent=2), encoding="utf-8")

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


def _parse_duration(value, default: int = 18) -> int:
    """target_duration_min form 값을 int 로. 비거나 비정상이면 default. 1~180 으로 clamp."""
    if value is None or str(value).strip() == "":
        return default
    try:
        n = int(str(value).strip())
    except ValueError:
        return default
    return max(1, min(180, n))


def _state_str(state) -> str:
    return state.value if hasattr(state, "value") else str(state)


# ---------------------------------------------------------------------------
# HTML 렌더링 (외부 템플릿 엔진 없이)
# ---------------------------------------------------------------------------


def _render_new_project_html() -> str:
    """주제 + 초기 링크 입력 폼 HTML. 외부 템플릿 엔진 없이 인라인."""
    options = "\n".join(
        "    <option value=\"" + html.escape(c.value) + "\">" + html.escape(c.value) + "</option>"
        for c in Category
    )
    return (
        "<!doctype html>\n"
        "<html lang=\"ko\"><head><meta charset=\"utf-8\">\n"
        "<title>새 영상 프로젝트</title>\n"
        "<style>\n"
        "body{font-family:system-ui,sans-serif;background:#f4f4f7;color:#222;margin:0;padding:24px;}\n"
        ".wrap{max-width:680px;margin:0 auto;}\n"
        "h1{font-size:1.4rem;margin:0 0 4px 0;}\n"
        ".sub{color:#555;font-size:0.9rem;margin-bottom:20px;}\n"
        ".card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:20px;}\n"
        "label{display:block;font-weight:600;font-size:0.9rem;margin:14px 0 4px 0;}\n"
        ".hint{font-weight:400;color:#777;font-size:0.8rem;}\n"
        "input,select,textarea{width:100%;font-family:inherit;font-size:0.95rem;padding:8px;"
        "border:1px solid #ccc;border-radius:4px;box-sizing:border-box;}\n"
        "textarea{resize:vertical;}\n"
        ".row{display:grid;grid-template-columns:2fr 1fr;gap:12px;}\n"
        ".footer{margin-top:20px;text-align:right;}\n"
        ".footer button{background:#1565c0;color:#fff;border:0;border-radius:6px;"
        "padding:10px 20px;font-size:1rem;cursor:pointer;}\n"
        ".footer button:hover{background:#0d3f78;}\n"
        "</style></head><body>\n"
        "<div class=\"wrap\">\n"
        "<h1>새 영상 프로젝트</h1>\n"
        "<div class=\"sub\">주제와 사전 확보 자료를 입력하면 Orchestrator 가 인테이크 계획을 생성합니다.</div>\n"
        "<form method=\"POST\" action=\"/new\" class=\"card\">\n"
        "  <div class=\"row\">\n"
        "    <div><label>project_id <span class=\"hint\">(영문 소문자/숫자/하이픈/언더스코어)</span>"
        "<input name=\"project_id\" required pattern=\"[a-z0-9_-]+\" placeholder=\"kursk_2026\"></label></div>\n"
        "    <div><label>목표 길이(분)<input name=\"target_duration_min\" type=\"number\" min=\"1\" max=\"180\" value=\"18\"></label></div>\n"
        "  </div>\n"
        "  <label>제목 (주제)<input name=\"title\" required placeholder=\"쿠르스크 전선 교착 — OSINT 종합 브리핑\"></label>\n"
        "  <label>카테고리<select name=\"category\" required>\n"
        + options + "\n"
        "  </select></label>\n"
        "  <label>주제 요약 <span class=\"hint\">(선택)</span>"
        "<textarea name=\"topic_summary\" rows=\"2\" placeholder=\"한두 문장으로 영상의 초점을 적어 주세요.\"></textarea></label>\n"
        "  <label>사전 확보 자료 링크 <span class=\"hint\">(선택, 한 줄에 하나 — 분석 리포트·기사·영상 등)</span>"
        "<textarea name=\"initial_links\" rows=\"4\" placeholder=\"https://...\"></textarea></label>\n"
        "  <label>LLM backend<select name=\"backend\">\n"
        "    <option value=\"claude\">claude</option>\n"
        "    <option value=\"codex\">codex</option>\n"
        "  </select></label>\n"
        "  <div class=\"footer\"><button type=\"submit\">인테이크 계획 생성</button></div>\n"
        "</form>\n"
        "</div></body></html>\n"
    )


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

    # v0.3.1 L1: parser 가 처리하는 모든 UserDecision 필드 (gdrive, uploaded_files,
    # ai_delegate_remaining) 를 form 에도 노출. parser ↔ UI contract 일치.
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
        "  <textarea name=\"google_drive_links__" + iid + "\" rows=\"2\" placeholder=\"Google Drive 링크 (한 줄에 하나)\"></textarea>\n"
        "  <textarea name=\"uploaded_files__" + iid + "\" rows=\"2\" placeholder=\"업로드 파일 경로 (한 줄에 하나, 향후 multipart 도입 전 placeholder)\"></textarea>\n"
        "</div>\n"
        "<div class=\"modes\"><label><input type=\"checkbox\" name=\"ai_delegate_remaining__" + iid + "\" value=\"1\"> 사용자가 일부 제공하고 나머지는 AI 위임</label></div>\n"
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
