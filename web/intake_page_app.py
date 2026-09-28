"""Dynamic Intake Page — `intake_plan.json` 을 사용자에게 보여주고 결정을 받는 웹 폼.

docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md 의 정식 구현 첫 단계 (Phase 3, v0.3.0).

엔드포인트
---------
- GET  /healthz                : 헬스체크 (배포 검증용, JSON 응답)
- GET  /intake/{pid}           : 인테이크 계획(안내) + 소스 넣기 폼 + 소스 목록·사용자 확인 (v3.2.0, 18 §7)
- POST /intake/{pid}/source    : 소스 한 건(기사 URL·기사 본문·X 텍스트·X 캡처·파일) → intake/sources.json
- POST /intake/{pid}/confirm   : 소스 사용자 확인(계정·시각)
- POST /intake/{pid}/submit    : 확인된 소스로 `intake → source_verify` 전이(미확인이 있으면 409)

설계 원칙
--------
- **Pydantic 모델만 사용**. 도메인 데이터는 `IntakePlan` / `schemas.source_models` 로만 다룬다 (CLAUDE.md C2).
  소스 기록·확인·제출은 `orchestrator.source_intake`·`intake_service.submit_sources` 를 호출만 한다.
  x.com 은 열지 않는다(18 §1) — X 는 텍스트 붙여넣기나 캡처로 받는다.
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

from orchestrator import source_intake as si
from orchestrator.config import AppConfig, project_dir
from orchestrator.intake_service import IntakePlanningError, SubmitSourcesError, run_intake_planner, submit_sources
from orchestrator.project_manager import (
    load_manifest,
    new_project,
    validate_project_id,
)
from schemas.models import (
    Category,
    IntakePlan,
    IntakePlanItem,
    ProjectManifest,
    ProjectState,
)
from schemas.source_models import SourcesFile


logger = logging.getLogger(__name__)


# v0.3.1: codex 4차 리뷰 H2 — form body 크기 상한 (DoS 방어).
# content-length 기준으로 거부. 256 KiB 면 인테이크 제출 (텍스트 메모/링크) 에 충분.
MAX_FORM_BYTES: int = 256 * 1024
# v3.2.0: X 캡처·자료 파일 업로드(multipart) 상한 — 소스 넣기 라우트만
MAX_UPLOAD_BYTES: int = 8 * 1024 * 1024
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


def _load_page(project_id: str) -> tuple[ProjectManifest, IntakePlan]:
    try:
        return load_manifest(project_id), _load_intake_plan(project_id)
    except FileNotFoundError as e:
        # v0.3.1 H1: 절대경로가 담긴 원본 메시지는 서버 로그에만 남기고 클라이언트엔 generic 메시지만.
        logger.warning("intake page 404 — pid=%s detail=%s", project_id, e)
        raise HTTPException(status_code=404, detail="intake plan not found for the requested project")


def _check_length(request: Request, limit: int) -> None:
    cl = request.headers.get("content-length")
    if cl is None:
        return
    try:
        n = int(cl)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid Content-Length header")
    if n > limit:
        raise HTTPException(status_code=413, detail="request body too large")


def _require_intake(manifest: ProjectManifest) -> Optional[JSONResponse]:
    cur = _state_str(manifest.current_state)
    if cur != ProjectState.INTAKE.value:
        return JSONResponse(status_code=409, content={"error": "state precondition failed",
                                                      "expected_state": ProjectState.INTAKE.value, "current_state": cur})
    return None


@app.get("/intake/{project_id}", response_class=HTMLResponse)
async def get_intake_page(project_id: str) -> HTMLResponse:
    project_id = _validated_pid(project_id)
    manifest, plan = _load_page(project_id)
    try:
        sources = si.load_sources(project_dir(project_id))
    except ValueError:
        logger.warning("intake page — sources.json 손상 pid=%s", project_id)
        raise HTTPException(status_code=500, detail="sources.json is corrupt")
    return HTMLResponse(_render_intake_html(manifest, plan, sources))


def _field(form, key: str) -> str:  # noqa: ANN001
    v = form.get(key)
    return v.strip() if isinstance(v, str) else ""


async def _upload_to_tmp(upload, suffixes: tuple[str, ...]) -> Path:  # noqa: ANN001 — starlette UploadFile
    import tempfile  # noqa: PLC0415

    name = getattr(upload, "filename", "") or ""
    suf = Path(name).suffix.lower()
    if suf not in suffixes:
        raise ValueError(f"파일 형식은 {', '.join(suffixes)} 만")
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("파일이 너무 크다")
    tmp = Path(tempfile.mkdtemp(prefix="intake_")) / f"upload{suf}"
    tmp.write_bytes(data)
    return tmp


@app.post("/intake/{project_id}/source")
async def add_source(project_id: str, request: Request):
    """소스 한 건 넣기(18 §1). kind = article_url | article_text | x_text | x_capture | file. 성공하면 페이지로 303."""
    from datetime import date, datetime  # noqa: PLC0415

    project_id = _validated_pid(project_id)
    _check_length(request, MAX_UPLOAD_BYTES)
    manifest, _plan = _load_page(project_id)
    bad = _require_intake(manifest)
    if bad is not None:
        return bad
    pdir = project_dir(project_id)
    form = await request.form()
    kind = _field(form, "kind")
    note = _field(form, "note")
    try:
        if kind == "x_text":
            posted = _field(form, "posted_at")
            si.add_x_text(pdir, account_name=_field(form, "account_name"), handle=_field(form, "handle"),
                          text=_field(form, "text"), text_ko=_field(form, "text_ko") or None, lang=_field(form, "lang") or "en",
                          posted_at=datetime.fromisoformat(posted) if posted else None, url=_field(form, "url") or None, note=note)
        elif kind == "x_capture":
            img = form.get("image")
            if img is None or isinstance(img, str):
                raise ValueError("캡처 이미지가 없다")
            tmp = await _upload_to_tmp(img, (".png", ".jpg", ".jpeg"))
            sid = si.stage_capture(pdir, tmp)
            rec, errs = si.read_capture(pdir, sid, note=note, backend=_field(form, "backend") or "claude")
            if rec is None:
                return JSONResponse(status_code=502, content={"error": "capture read failed", "detail": errs[:3]})
        elif kind in ("article_url", "article_text"):
            url = _field(form, "url") or None
            body, head, pub, day = _field(form, "body"), _field(form, "headline"), _field(form, "publisher"), _field(form, "published_at")
            if kind == "article_url":
                if not url:
                    raise ValueError("기사 URL 이 없다")
                got = si.fetch_article(url)
                body, head = body or got["body"], head or got["title"]
                pub, day = pub or got["publisher"], day or got["published_at"]
            if not (body and head and pub and day):
                raise ValueError("기사는 본문·제목·매체·게시일이 필요하다(가져오지 못한 칸은 직접 적는다)")
            facts = _split_lines(form.get("facts"))
            si.add_article(pdir, publisher=pub, headline=head, headline_ko=_field(form, "headline_ko") or None,
                           published_at=date.fromisoformat(day), body=body, url=url, key_facts=facts or None,
                           lang=_field(form, "lang") or "ko", note=note)
        elif kind == "file":
            up = form.get("file")
            if up is None or isinstance(up, str):
                raise ValueError("파일이 없다")
            tmp = await _upload_to_tmp(up, (".txt", ".md", ".pdf", ".csv", ".json"))
            body = tmp.read_text(encoding="utf-8", errors="replace") if tmp.suffix in (".txt", ".md", ".csv", ".json") else ""
            facts = _split_lines(form.get("facts"))
            if not body and not facts:
                raise ValueError("텍스트가 아닌 파일은 요지(한 줄에 하나)를 적는다")
            day = _field(form, "published_at")
            si.add_document(pdir, issuer=_field(form, "issuer"), title=_field(form, "title"), body=body or "\n".join(facts),
                            key_facts=facts or None, published_at=date.fromisoformat(day) if day else None,
                            url=_field(form, "url") or None, file=tmp, lang=_field(form, "lang") or "ko", note=note)
        else:
            raise ValueError("알 수 없는 소스 유형")
    except (si.SourceIntakeError, ValueError, OSError) as e:
        return JSONResponse(status_code=400, content={"error": "invalid source", "detail": str(e)[:300]})
    return RedirectResponse(url=f"/intake/{project_id}", status_code=303)


@app.post("/intake/{project_id}/confirm")
async def confirm_source(project_id: str, request: Request):
    """사용자 확인(18 §7) — 계정·시각이 맞는지 본 사람. 게시 시각을 고칠 수 있다."""
    from datetime import datetime  # noqa: PLC0415

    project_id = _validated_pid(project_id)
    _check_length(request, MAX_FORM_BYTES)
    manifest, _plan = _load_page(project_id)
    bad = _require_intake(manifest)
    if bad is not None:
        return bad
    form = await request.form()
    by = _field(form, "by")
    if not by:
        return JSONResponse(status_code=400, content={"error": "confirmer (by) is required"})
    posted = _field(form, "posted_at")
    klass = _field(form, "account_class") or None
    try:
        si.confirm(project_dir(project_id), _field(form, "source_id"), by,
                   posted_at=datetime.fromisoformat(posted) if posted else None, account_class=klass)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": "confirm failed", "detail": str(e)[:300]})
    return RedirectResponse(url=f"/intake/{project_id}", status_code=303)


@app.post("/intake/{project_id}/submit")
async def submit_intake(project_id: str, request: Request) -> JSONResponse:
    """확인된 소스로 intake → source_verify. 소스 없음·미확인은 409(18 §7). 파일을 새로 쓰지 않는다(sources.json 이 SSOT)."""
    project_id = _validated_pid(project_id)
    _check_length(request, MAX_FORM_BYTES)
    _load_page(project_id)
    try:
        manifest = submit_sources(project_id, reason="Dynamic Intake Page 제출")
    except SubmitSourcesError as e:
        return JSONResponse(status_code=409, content={"error": str(e), "kind": e.kind, "pending": e.errors})
    except ValueError as e:
        logger.warning("intake submit transition fail — pid=%s err=%s", project_id, e)
        return JSONResponse(status_code=409, content={"error": "state transition failed"})
    return JSONResponse(content={"current_state": _state_str(manifest.current_state),
                                 "sources": si.summary(project_dir(project_id))})


def _split_lines(value) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for line in str(value).splitlines():
        line = line.strip()
        if line:
            parts.append(line)
    return parts


def _parse_duration(value, default: int = 18) -> int:
    """target_duration_min form 값을 int 로. 비거나 비정상이면 default. 3~20 분으로 clamp.

    지원 길이 범위는 3~20 분 (ProjectManifest/IntakePlan 의 ge=3/le=20 과 일치).
    """
    if value is None or str(value).strip() == "":
        return default
    try:
        n = int(str(value).strip())
    except ValueError:
        return default
    return max(3, min(20, n))


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
        "    <div><label>목표 길이(분) <span class=\"hint\">(3~20)</span><input name=\"target_duration_min\" type=\"number\" min=\"3\" max=\"20\" value=\"18\"></label></div>\n"
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


_CSS = (
    "body{font-family:system-ui,sans-serif;background:#f4f4f7;color:#222;margin:0;padding:16px;}\n"
    ".wrap{max-width:860px;margin:0 auto;}\n"
    "h1{margin:0 0 8px 0;font-size:1.3rem;}h2{font-size:1.05rem;margin:18px 0 8px 0;}\n"
    ".meta{color:#555;font-size:0.85rem;margin-bottom:12px;}\n"
    ".assessment{background:#fff8e1;border-left:4px solid #f0b400;padding:10px 14px;border-radius:6px;margin-bottom:16px;}\n"
    ".card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px 14px;margin-bottom:10px;}\n"
    ".card h3{margin:0 0 4px 0;font-size:0.95rem;}\n"
    ".desc{color:#444;font-size:0.9rem;margin:4px 0;}.why{color:#1565c0;font-size:0.85rem;}.risk{color:#c62828;font-size:0.85rem;}\n"
    "label{display:block;font-size:0.85rem;font-weight:600;margin:8px 0 2px 0;}\n"
    "input,select,textarea{width:100%;font-family:inherit;font-size:0.9rem;padding:6px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;}\n"
    ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;}\n"
    "table{width:100%;border-collapse:collapse;background:#fff;font-size:0.85rem;}\n"
    "td,th{border-bottom:1px solid #eee;padding:6px;text-align:left;vertical-align:top;}\n"
    ".ok{color:#2e7d32;font-weight:600;}.no{color:#c62828;font-weight:600;}\n"
    ".official{background:#e0f2f1;border:1px solid #26a69a;border-radius:8px;padding:0 6px;font-size:0.75rem;}\n"
    "button{background:#1565c0;color:#fff;border:0;border-radius:6px;padding:8px 14px;font-size:0.95rem;cursor:pointer;margin-top:8px;}\n"
    "button.small{padding:4px 8px;font-size:0.8rem;}\n"
)


def _render_intake_html(manifest: ProjectManifest, plan: IntakePlan, sources: SourcesFile) -> str:
    """인테이크 계획(무엇을 더 모을지 안내) + 소스 넣기 폼 + 소스 목록·확인 + 제출(v3.2.0, 18 §7)."""
    title = html.escape(manifest.title)
    pid = html.escape(manifest.project_id)
    state = html.escape(_state_str(manifest.current_state))
    assessment = html.escape(plan.orchestrator_assessment or "(orchestrator 평가 없음)")
    guide = "\n".join(_render_item_card(item) for item in plan.required_items) or "<div class=\"desc\">(안내 항목 없음)</div>"
    pending = sum(not s.confirmed for s in sources.sources)
    return (
        "<!doctype html>\n<html lang=\"ko\"><head><meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<title>Intake — " + title + "</title>\n<style>\n" + _CSS + "</style></head><body><div class=\"wrap\">\n"
        "<h1>" + title + "</h1>\n"
        "<div class=\"meta\">project_id=" + pid + " &middot; current_state=" + state
        + " &middot; target_duration_min=" + str(manifest.target_duration_min) + "</div>\n"
        "<div class=\"assessment\"><strong>Orchestrator 평가:</strong> " + assessment + "</div>\n"
        "<h2>모을 자료 안내</h2>\n" + guide + "\n"
        "<h2>소스 넣기</h2>\n" + _render_add_form(pid) + "\n"
        "<h2>소스 목록 (" + str(len(sources.sources)) + "건 · 확인 대기 " + str(pending) + "건)</h2>\n"
        + _render_sources_table(pid, sources) + "\n"
        "<form method=\"POST\" action=\"/intake/" + pid + "/submit\">"
        "<button type=\"submit\">확인된 소스로 검증 단계 시작</button></form>\n"
        "</div></body></html>\n"
    )


def _render_add_form(pid: str) -> str:
    """소스 유형 선택(기사 URL·기사 본문·X 텍스트·X 캡처·파일) + 메모. X 는 링크만으로 받지 않는다(18 §1)."""
    return (
        "<form method=\"POST\" action=\"/intake/" + pid + "/source\" enctype=\"multipart/form-data\" class=\"card\">\n"
        "<label>소스 유형<select name=\"kind\">"
        "<option value=\"article_url\">기사 URL (가져오기)</option>"
        "<option value=\"article_text\">기사 본문 붙여넣기</option>"
        "<option value=\"x_text\">X 게시물 텍스트</option>"
        "<option value=\"x_capture\">X 게시물 캡처</option>"
        "<option value=\"file\">공문·자료 파일</option></select></label>\n"
        "<div class=\"grid\">"
        "<label>URL<input name=\"url\" placeholder=\"https://… (X 링크는 열지 않는다 — 텍스트·캡처로)\"></label>"
        "<label>매체<input name=\"publisher\"></label>"
        "<label>기사 제목(원문)<input name=\"headline\"></label>"
        "<label>제목 번역<input name=\"headline_ko\"></label>"
        "<label>게시일 (YYYY-MM-DD)<input name=\"published_at\"></label>"
        "<label>X 표시 이름<input name=\"account_name\"></label>"
        "<label>X 핸들<input name=\"handle\" placeholder=\"@...\"></label>"
        "<label>X 게시 시각 (ISO)<input name=\"posted_at\" placeholder=\"2026-09-20T14:05\"></label>"
        "<label>언어 코드<input name=\"lang\" placeholder=\"en / ko\"></label>"
        "<label>발행 기관(자료)<input name=\"issuer\"></label>"
        "<label>자료 제목<input name=\"title\"></label>"
        "</div>\n"
        "<label>본문 (기사 본문 · X 본문)<textarea name=\"body\" rows=\"4\"></textarea></label>\n"
        "<label>X 본문 (X 텍스트)<textarea name=\"text\" rows=\"3\"></textarea></label>\n"
        "<label>X 번역<textarea name=\"text_ko\" rows=\"2\"></textarea></label>\n"
        "<label>요지 (한 줄에 하나 — 원문 장문 복제 금지)<textarea name=\"facts\" rows=\"3\"></textarea></label>\n"
        "<div class=\"grid\"><label>X 캡처 이미지<input type=\"file\" name=\"image\" accept=\".png,.jpg,.jpeg\"></label>"
        "<label>자료 파일<input type=\"file\" name=\"file\"></label></div>\n"
        "<label>메모<input name=\"note\"></label>\n"
        "<button type=\"submit\">소스 추가</button>\n</form>"
    )


def _render_sources_table(pid: str, sources: SourcesFile) -> str:
    if not sources.sources:
        return "<div class=\"card desc\">아직 소스가 없다.</div>"
    rows = []
    for s in sources.sources:
        sid = html.escape(s.id)
        if s.type == "x_post":
            who = html.escape(f"{s.account_name} {s.handle}") + (" <span class=\"official\">공식 계정</span>"
                                                               if s.account_class.startswith("official") else
                                                               " <span class=\"desc\">(" + html.escape(s.account_class) + ")</span>")
            what = html.escape((s.text_ko or s.text_original)[:160])
            when = html.escape(str(s.posted_at or "시각 미상"))
        elif s.type == "article":
            who, what, when = html.escape(s.publisher), html.escape(s.headline_ko or s.headline_original), html.escape(str(s.published_at))
        else:
            who, what, when = html.escape(s.issuer), html.escape(s.title), html.escape(str(s.published_at or "-"))
        if s.confirmed:
            conf = "<span class=\"ok\">확인 · " + html.escape(s.confirmed_by or "") + "</span>"
        else:
            conf = ("<form method=\"POST\" action=\"/intake/" + pid + "/confirm\">"
                    "<input type=\"hidden\" name=\"source_id\" value=\"" + sid + "\">"
                    "<input name=\"by\" placeholder=\"확인한 사람\" required>"
                    + ("<input name=\"posted_at\" placeholder=\"게시 시각 고침(ISO)\">"
                       "<select name=\"account_class\"><option value=\"\">계정 분류(목록 밖)</option>"
                       "<option value=\"journalist\">기자</option><option value=\"public_figure\">공인</option>"
                       "<option value=\"private\">개인</option><option value=\"unknown\">모름</option></select>"
                       if s.type == "x_post" else "")
                    + "<button class=\"small\" type=\"submit\">계정·시각 확인</button></form>"
                    "<span class=\"no\">미확인</span>")
        rows.append("<tr><td>" + sid + "<br>" + html.escape(s.type) + "</td><td>" + who + "<br>" + when + "</td><td>" + what
                    + "</td><td>" + conf + "</td></tr>")
    return "<table><tr><th>id</th><th>출처·시각</th><th>내용</th><th>사용자 확인</th></tr>" + "".join(rows) + "</table>"


def _render_item_card(item: IntakePlanItem) -> str:
    """인테이크 계획 항목 — 무엇을 더 모으면 좋은지 안내만(v3.2.0, IntakePlanner 는 안내 역할, D52)."""
    risk = ("<div class=\"risk\"><strong>리스크 안내:</strong> " + html.escape(item.risk_notice) + "</div>") if item.risk_notice else ""
    return ("<div class=\"card\" id=\"card-" + html.escape(item.item_id) + "\"><h3>" + html.escape(item.label)
            + " <span class=\"desc\">(" + html.escape(_state_str(item.priority)) + ")</span></h3>"
            "<div class=\"desc\">" + html.escape(item.description) + "</div>"
            "<div class=\"why\"><strong>필요한 이유:</strong> " + html.escape(item.why_needed) + "</div>" + risk + "</div>")


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
