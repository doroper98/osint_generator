"""완성 영상을 유튜브에 비공개로 올린다 (v7.4.0, back_and_forth D-1200).

입력은 `python -m engine.mux` 가 남긴 프로젝트 산출물이다.
    out/final.mp4        원본 화질(전달용 압축본이 아님)
    out/description.txt  첫 줄 = 제목, 빈 줄 뒤 = 설명(챕터·크레딧·출처 포함)
    out/final.srt        자막(captions.insert)

결과는 `out/youtube_upload.json`(schema_version 1)에 남는다 — video id·URL·업로드 시각·privacy.
돌지 않은 단계(자막 등)는 기록하지 않는다(15 P5).

비밀값은 환경 변수 셋만 읽는다(C9). 로그·파일에 값을 쓰지 않는다.
    YT_CLIENT_ID · YT_CLIENT_SECRET · YT_REFRESH_TOKEN
없으면 오류로 멈춘다(조용한 폴백 금지, 15 P6). 공개 범위는 항상 private — 공개 클릭은 사용자 몫이다.

    python tools/youtube_upload.py projects/<pid> --synthetic-media yes --dry-run   # 메타데이터만 검증
    python tools/youtube_upload.py projects/<pid> --synthetic-media yes             # 실제 업로드(비공개)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from orchestrator.config import YouTubeConfig, load_config  # noqa: E402

SECRET_ENV: tuple[str, str, str] = ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
TOKEN_EXPIRED_HINT = ("리프레시 토큰 만료(invalid_grant) — OAuth 앱이 '테스트 중' 상태라 7일마다 만료된다. "
                      "OAuth Playground 에서 새 리프레시 토큰을 받고(안내 2단계 d) 환경의 YT_REFRESH_TOKEN 을 바꾼 뒤(2단계 e) 새 세션에서 다시 실행")
FORBIDDEN_CHARS: tuple[str, str] = ("<", ">")   # 제목·설명에 쓰면 API 가 invalidTitle·invalidDescription 으로 거부
MB = 1024 * 1024
CHUNK_UNIT = 256 * 1024                          # 재개 가능 업로드 조각은 256 KiB 배수(API 규약)
RETRY_STATUS: frozenset[int] = frozenset({500, 502, 503, 504})


class UploadError(RuntimeError):
    """업로드 실패 — 사유를 그대로 보인다(15 P6)."""


class UploadMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    title: str = Field(min_length=1)
    description: str
    tags: list[str] = Field(default_factory=list)
    category_id: str
    default_language: str
    privacy_status: Literal["private"]
    contains_synthetic_media: bool              # AI 합성 음성 등 — 사용자가 매번 명시(기본값 없음)
    made_for_kids: bool = False

    def body(self) -> dict:
        """videos.insert 요청 본문(snippet·status)."""
        return {"snippet": {"title": self.title, "description": self.description, "tags": self.tags,
                            "categoryId": self.category_id, "defaultLanguage": self.default_language,
                            "defaultAudioLanguage": self.default_language},
                "status": {"privacyStatus": self.privacy_status, "selfDeclaredMadeForKids": self.made_for_kids,
                           "containsSyntheticMedia": self.contains_synthetic_media}}


class UploadRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    video_id: str
    url: str
    uploaded_at: str                            # UTC ISO 8601
    privacy_status: Literal["private"]
    video_file: str
    video_bytes: int
    title: str
    contains_synthetic_media: bool
    caption_id: str | None = None               # 자막을 올린 경우에만


def youtube_cfg() -> YouTubeConfig:
    cfg = load_config().youtube
    if cfg is None:
        raise UploadError("config.yaml 에 youtube: 설정이 없다")
    return cfg


def parse_description(text: str) -> tuple[str, str]:
    """description.txt → (제목, 설명). 첫 줄이 제목, 그 뒤 빈 줄 다음부터 설명(engine.mux.build_description 형식)."""
    lines = text.strip("\n").split("\n")
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip("\n")
    if not title:
        raise UploadError("description.txt 첫 줄(제목)이 비어 있다")
    return title, body


def validate_metadata(meta: UploadMetadata, cfg: YouTubeConfig) -> list[str]:
    """API 가 거부할 값을 업로드 전에 모두 찾는다. 빈 목록이면 통과. 값을 몰래 자르지 않는다(P6)."""
    errs: list[str] = []
    if len(meta.title) > cfg.title_max_chars:
        errs.append(f"제목 {len(meta.title)}자 — 한도 {cfg.title_max_chars}자")
    nbytes = len(meta.description.encode("utf-8"))
    if nbytes > cfg.description_max_bytes:
        errs.append(f"설명 {nbytes}바이트(UTF-8) — 한도 {cfg.description_max_bytes}바이트. 한글은 1자 3바이트다. "
                    "줄인 설명 파일을 --description-file 로 넘겨라")
    for name, val in (("제목", meta.title), ("설명", meta.description)):
        bad = [c for c in FORBIDDEN_CHARS if c in val]
        if bad:
            errs.append(f"{name}에 금지 문자 {''.join(bad)}")
    tag_len = sum(len(t) + (2 if " " in t else 0) for t in meta.tags) + max(len(meta.tags) - 1, 0)
    if tag_len > cfg.tags_max_chars:
        errs.append(f"태그 합계 {tag_len}자 — 한도 {cfg.tags_max_chars}자")
    return errs


def build_metadata(desc_text: str, tags: list[str], synthetic: bool, cfg: YouTubeConfig) -> UploadMetadata:
    title, body = parse_description(desc_text)
    return UploadMetadata(title=title, description=body, tags=tags, category_id=cfg.category_id,
                          default_language=cfg.default_language, privacy_status=cfg.privacy_status,
                          contains_synthetic_media=synthetic)


def read_secrets(env: dict[str, str] | None = None) -> tuple[str, str, str]:
    env = os.environ if env is None else env
    missing = [k for k in SECRET_ENV if not env.get(k)]
    if missing:
        raise UploadError(f"환경 변수 없음: {', '.join(missing)} — 클라우드 환경 설정에 저장한 뒤 새 세션에서 실행(안내 2단계 e)")
    return env[SECRET_ENV[0]], env[SECRET_ENV[1]], env[SECRET_ENV[2]]


def access_token(client: httpx.Client, cfg: YouTubeConfig, secrets: tuple[str, str, str]) -> str:
    cid, csec, rtok = secrets
    r = client.post(cfg.token_url, data={"client_id": cid, "client_secret": csec, "refresh_token": rtok,
                                         "grant_type": "refresh_token"})
    if r.status_code != httpx.codes.OK:
        err = _json(r).get("error", "")
        if err == "invalid_grant":
            raise UploadError(TOKEN_EXPIRED_HINT)
        raise UploadError(f"액세스 토큰 갱신 실패 HTTP {r.status_code} error={err or '?'}")   # 응답 본문(비밀 포함 가능)은 찍지 않는다
    return r.json()["access_token"]


def _json(r: httpx.Response) -> dict:
    try:
        v = r.json()
    except ValueError:
        return {}
    return v if isinstance(v, dict) else {}


def _api_error(r: httpx.Response, what: str) -> UploadError:
    e = _json(r).get("error", {})
    reasons = [x.get("reason", "") for x in e.get("errors", [])] if isinstance(e, dict) else []
    msg = e.get("message", "") if isinstance(e, dict) else str(e)
    hint = " — 하루 할당량 소진, 내일(태평양 시간 자정 뒤) 다시" if "quotaExceeded" in reasons or "uploadLimitExceeded" in reasons else ""
    return UploadError(f"{what} 실패 HTTP {r.status_code} {','.join(reasons)} {msg}{hint}".strip())


def _backoff(attempt: int) -> None:
    time.sleep(2 ** attempt)


def upload_video(client: httpx.Client, cfg: YouTubeConfig, token: str, video: Path, meta: UploadMetadata) -> str:
    """재개 가능 업로드(세션 시작 → 조각 PUT, 308 이면 Range 다음부터). 5xx·네트워크 오류는 cfg.tries 까지 재시도."""
    size = video.stat().st_size
    auth = {"Authorization": f"Bearer {token}"}
    r = client.post(cfg.upload_url, params={"uploadType": "resumable", "part": "snippet,status"},
                    headers={**auth, "Content-Type": "application/json; charset=UTF-8",
                             "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
                    json=meta.body())
    if r.status_code != httpx.codes.OK or "location" not in r.headers:
        raise _api_error(r, "업로드 세션 시작")
    session = r.headers["location"]
    chunk = max(cfg.chunk_mb * MB // CHUNK_UNIT, 1) * CHUNK_UNIT
    pos, fails = 0, 0
    with video.open("rb") as f:
        while True:
            f.seek(pos)
            data = f.read(chunk)
            end = pos + len(data) - 1
            try:
                r = client.put(session, content=data, headers={**auth, "Content-Range": f"bytes {pos}-{end}/{size}"})
            except httpx.TransportError as ex:
                r, err = None, ex
            if r is not None and r.status_code in (httpx.codes.OK, httpx.codes.CREATED):
                return r.json()["id"]
            if r is not None and r.status_code == httpx.codes.PERMANENT_REDIRECT:   # 308 Resume Incomplete
                rng = r.headers.get("range")
                pos = int(rng.split("-")[1]) + 1 if rng else 0
                fails = 0
                print(f"[youtube] 업로드 {pos}/{size} 바이트", flush=True)
                continue
            if r is not None and r.status_code not in RETRY_STATUS:
                raise _api_error(r, "영상 업로드")
            fails += 1
            if fails >= cfg.tries:
                raise UploadError(f"영상 업로드 재시도 {cfg.tries}회 실패: {err if r is None else r.status_code}")
            _backoff(fails)
            q = client.put(session, headers={**auth, "Content-Range": f"bytes */{size}"})   # 서버가 받은 위치 확인
            if q.status_code in (httpx.codes.OK, httpx.codes.CREATED):
                return q.json()["id"]
            rng = q.headers.get("range")
            pos = int(rng.split("-")[1]) + 1 if rng else 0


def upload_caption(client: httpx.Client, cfg: YouTubeConfig, token: str, video_id: str, srt: Path) -> str:
    """captions.insert — multipart/related(메타데이터 JSON + srt 본문)."""
    boundary = uuid.uuid4().hex
    meta = json.dumps({"snippet": {"videoId": video_id, "language": cfg.caption_language,
                                   "name": cfg.caption_name, "isDraft": False}}, ensure_ascii=False)
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
            f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode("utf-8") + srt.read_bytes() + \
        f"\r\n--{boundary}--\r\n".encode("utf-8")
    r = client.post(cfg.captions_url, params={"uploadType": "multipart", "part": "snippet"}, content=body,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/related; boundary={boundary}"})
    if r.status_code != httpx.codes.OK:
        raise _api_error(r, "자막 업로드")
    return r.json()["id"]


def resolve_inputs(proj: Path, video: Path | None, desc: Path | None, srt: Path | None) -> tuple[Path, Path, Path | None]:
    out = proj / "out"
    v = video or out / "final.mp4"
    d = desc or out / "description.txt"
    s = srt if srt is not None else out / "final.srt"
    for p, what in ((v, "영상"), (d, "설명")):
        if not p.is_file():
            raise UploadError(f"{what} 파일 없음: {p} — python -m engine.mux {proj} 먼저")
    if not s.is_file():
        raise UploadError(f"자막 파일 없음: {s} — 자막 없이 올리려면 --no-caption")
    return v, d, s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="완성 영상을 유튜브에 비공개로 올린다")
    ap.add_argument("proj", type=Path, help="projects/<pid>")
    ap.add_argument("--synthetic-media", choices=("yes", "no"), required=True,
                    help="합성·변형 미디어 표시(status.containsSyntheticMedia) — 매번 명시")
    ap.add_argument("--video", type=Path, help="기본 out/final.mp4")
    ap.add_argument("--description-file", type=Path, help="기본 out/description.txt(첫 줄 제목)")
    ap.add_argument("--srt", type=Path, help="기본 out/final.srt")
    ap.add_argument("--no-caption", action="store_true", help="자막을 올리지 않는다")
    ap.add_argument("--tags", default="", help="쉼표로 구분")
    ap.add_argument("--dry-run", action="store_true", help="메타데이터만 검증하고 올리지 않는다(비밀값 불필요)")
    a = ap.parse_args(argv)
    proj = a.proj.resolve()
    try:
        cfg = youtube_cfg()
        if a.no_caption:
            v, d, _ = resolve_inputs(proj, a.video, a.description_file, Path(os.devnull))
            s = None
        else:
            v, d, s = resolve_inputs(proj, a.video, a.description_file, a.srt)
        tags = [t.strip() for t in a.tags.split(",") if t.strip()]
        meta = build_metadata(d.read_text(encoding="utf-8"), tags, a.synthetic_media == "yes", cfg)
        errs = validate_metadata(meta, cfg)
        if errs:
            raise UploadError("메타데이터 검증 실패:\n  " + "\n  ".join(errs))
        size = v.stat().st_size
        print(f"[youtube] 제목: {meta.title}")
        print(f"[youtube] 설명 {len(meta.description.encode('utf-8'))}B · 태그 {len(tags)}개 · 영상 {size / MB:.1f}MB · "
              f"자막 {'있음' if s else '없음'} · privacy={meta.privacy_status} · 합성 표시={meta.contains_synthetic_media}")
        if a.dry_run:
            print("[youtube] dry-run 통과 — 올리지 않음")
            return 0
        secrets = read_secrets()
        dest = proj / "out" / "youtube_upload.json"
        with httpx.Client(timeout=cfg.timeout_sec) as client:
            token = access_token(client, cfg, secrets)
            vid = upload_video(client, cfg, token, v, meta)
            rec = UploadRecord(video_id=vid, url=cfg.watch_url_prefix + vid,
                               uploaded_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                               privacy_status=meta.privacy_status,
                               video_file=str(v.relative_to(proj)) if v.is_relative_to(proj) else str(v),
                               video_bytes=size, title=meta.title, contains_synthetic_media=meta.contains_synthetic_media)
            dest.write_text(rec.model_dump_json(indent=1), encoding="utf-8")   # 자막이 실패해도 영상 기록은 남는다
            print(f"[youtube] 영상 업로드 완료 {rec.url}", flush=True)
            if s:
                rec.caption_id = upload_caption(client, cfg, token, vid, s)
                dest.write_text(rec.model_dump_json(indent=1), encoding="utf-8")
        print(f"[youtube] 완료 {rec.url} (비공개) → {dest}")
        return 0
    except UploadError as ex:
        print(f"[youtube] 오류: {ex}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
