"""완성 영상을 유튜브에 비공개로 올리는 파이프라인 단계 (v7.4.0, back_and_forth D-1200).

DELIVER 상태에서 `engine.mux` 다음에 돈다(orchestrator.engine_service STATE_STAGES). 단독 실행도 된다.
    python -m publish.youtube projects/<pid> --dry-run   # 메타데이터만 검증(비밀값 불필요)
    python -m publish.youtube projects/<pid>             # 실제 업로드(항상 비공개)
표준 출력 마지막 줄은 StageResult JSON(stage="upload", 16 §4)이다.

입력은 `engine.mux` 산출물이다.
    out/final.mp4        원본 화질(전달용 압축본이 아님)
    out/description.txt  첫 줄 = 제목, 빈 줄 뒤 = 설명(챕터·크레딧·출처)
    out/final.srt        자막(captions.insert)

설명이 API 한도(UTF-8 5000바이트)를 넘으면 정해진 순서로 줄이고, 줄인 내용을 기록한다(조용히 자르지 않음, 15 P6).
    1) 출처 줄의 제목 인용(“…”)을 뺀다 — 기관·매체 이름과 링크는 남는다
    2) 그래도 넘으면 뒤쪽 출처부터 링크를 빼고, 몇 건을 뺐는지 한 줄로 밝힌다
    3) 그래도 넘으면 오류
결과는 `out/youtube_upload.json`(schema_version 1). 같은 영상(md5)을 이미 올렸으면 다시 올리지 않는다.

비밀값은 환경 변수 셋만 읽는다(C9). 로그·파일에 값을 쓰지 않는다.
    YT_CLIENT_ID · YT_CLIENT_SECRET · YT_REFRESH_TOKEN
없으면 오류로 멈춘다(15 P6). 공개 범위는 항상 private — 공개 클릭은 사용자 몫이다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.config import YouTubeConfig, load_config  # noqa: E402
from schemas.engine_models import StageResult  # noqa: E402

STAGE = "upload"
SECRET_ENV: tuple[str, str, str] = ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")
TOKEN_EXPIRED_HINT = ("리프레시 토큰 만료·철회(invalid_grant). OAuth 앱이 '테스트 중'이면 7일마다 만료된다 — 앱 게시(docs/YOUTUBE_UPLOAD.md §영구 해결) 뒤에는 "
                      "철회·비밀번호 변경 때만 생긴다. OAuth Playground 에서 새 리프레시 토큰을 받아 환경의 YT_REFRESH_TOKEN 을 바꾼 뒤 새 세션에서 다시 실행")
FORBIDDEN_CHARS: tuple[str, str] = ("<", ">")   # 제목·설명에 쓰면 API 가 invalidTitle·invalidDescription 으로 거부
SOURCES_HEADING = "출처 원문"                     # engine.mux DESCRIPTION_SOURCES_HEADING 머리(설명문 섹션 찾기)
QUOTED_TITLE = re.compile(r" “[^”]*”")
URL_TAIL = re.compile(r" — https?://\S+$")
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
    contains_synthetic_media: bool
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
    video_md5: str
    title: str
    contains_synthetic_media: bool
    description_bytes: int
    description_trims: list[str] = Field(default_factory=list)   # 한도 때문에 줄인 내용(비면 원문 그대로)
    caption_id: str | None = None               # 자막을 올린 경우에만


def youtube_cfg() -> YouTubeConfig:
    cfg = load_config().youtube
    if cfg is None:
        raise UploadError("config.yaml 에 youtube: 설정이 없다")
    return cfg


def parse_description(text: str) -> tuple[str, str]:
    """description.txt → (제목, 설명). 첫 줄이 제목(engine.mux.build_description 의 headline)."""
    lines = text.strip("\n").split("\n")
    title = lines[0].strip()
    if not title:
        raise UploadError("description.txt 첫 줄(제목)이 비어 있다")
    return title, "\n".join(lines[1:]).strip("\n")


def _nbytes(s: str) -> int:
    return len(s.encode("utf-8"))


def fit_description(body: str, limit: int) -> tuple[str, list[str]]:
    """한도에 맞게 출처 섹션만 정해진 순서로 줄인다. (설명, 줄인 내용 목록). 맞출 수 없으면 오류."""
    if _nbytes(body) <= limit:
        return body, []
    paras = body.split("\n\n")
    idx = next((i for i, p in enumerate(paras) if p.startswith(SOURCES_HEADING)), None)
    if idx is None:
        raise UploadError(f"설명 {_nbytes(body)}바이트 — 한도 {limit}바이트, 줄일 출처 섹션 없음. --description-file 로 줄인 설명을 넘겨라")
    head, *lines = paras[idx].split("\n")
    trims: list[str] = []

    def joined(ls: list[str]) -> str:
        return "\n\n".join([*paras[:idx], "\n".join([head, *ls]), *paras[idx + 1:]])

    short = [QUOTED_TITLE.sub("", ln) for ln in lines]
    if short != lines:
        trims.append(f"출처 {sum(a != b for a, b in zip(short, lines))}건의 제목 인용 생략(기관·매체 이름과 링크는 유지)")
        lines = short
    if _nbytes(joined(lines)) <= limit:
        return joined(lines), trims
    linked = [i for i, ln in enumerate(lines) if URL_TAIL.search(ln)]
    for n in range(1, len(linked) + 1):
        cut = set(linked[-n:])
        ls = [URL_TAIL.sub("", ln) if i in cut else ln for i, ln in enumerate(lines)]
        ls.append(f"(설명 길이 한도로 뒤쪽 {n}건의 링크 생략 — 출처 이름은 위와 영상 엔딩 크레딧에 있음)")
        if _nbytes(joined(ls)) <= limit:
            trims.append(f"뒤쪽 출처 {n}건의 링크 생략")
            return joined(ls), trims
    raise UploadError(f"출처 링크를 모두 빼도 설명이 한도 {limit}바이트를 넘는다 — --description-file 로 줄인 설명을 넘겨라")


def validate_metadata(meta: UploadMetadata, cfg: YouTubeConfig) -> list[str]:
    """API 가 거부할 값을 업로드 전에 모두 찾는다. 빈 목록이면 통과."""
    errs: list[str] = []
    if len(meta.title) > cfg.title_max_chars:
        errs.append(f"제목 {len(meta.title)}자 — 한도 {cfg.title_max_chars}자")
    if _nbytes(meta.description) > cfg.description_max_bytes:
        errs.append(f"설명 {_nbytes(meta.description)}바이트(UTF-8) — 한도 {cfg.description_max_bytes}바이트")
    for name, val in (("제목", meta.title), ("설명", meta.description)):
        bad = [c for c in FORBIDDEN_CHARS if c in val]
        if bad:
            errs.append(f"{name}에 금지 문자 {''.join(bad)}")
    tag_len = sum(len(t) + (2 if " " in t else 0) for t in meta.tags) + max(len(meta.tags) - 1, 0)
    if tag_len > cfg.tags_max_chars:
        errs.append(f"태그 합계 {tag_len}자 — 한도 {cfg.tags_max_chars}자")
    return errs


def build_metadata(desc_text: str, tags: list[str], synthetic: bool, cfg: YouTubeConfig) -> tuple[UploadMetadata, list[str]]:
    title, body = parse_description(desc_text)
    body, trims = fit_description(body, cfg.description_max_bytes)
    meta = UploadMetadata(title=title, description=body, tags=tags, category_id=cfg.category_id,
                          default_language=cfg.default_language, privacy_status=cfg.privacy_status,
                          contains_synthetic_media=synthetic)
    return meta, trims


def read_secrets(env: dict[str, str] | None = None) -> tuple[str, str, str]:
    env = os.environ if env is None else env
    missing = [k for k in SECRET_ENV if not env.get(k)]
    if missing:
        raise UploadError(f"환경 변수 없음: {', '.join(missing)} — 클라우드 환경 설정(또는 로컬 .env)에 저장한 뒤 새 세션에서 실행")
    return env[SECRET_ENV[0]], env[SECRET_ENV[1]], env[SECRET_ENV[2]]


def _json(r: httpx.Response) -> dict:
    try:
        v = r.json()
    except ValueError:
        return {}
    return v if isinstance(v, dict) else {}


def access_token(client: httpx.Client, cfg: YouTubeConfig, secrets: tuple[str, str, str]) -> str:
    cid, csec, rtok = secrets
    r = client.post(cfg.token_url, data={"client_id": cid, "client_secret": csec, "refresh_token": rtok,
                                         "grant_type": "refresh_token"})
    if r.status_code != httpx.codes.OK:
        err = _json(r).get("error", "")
        if err == "invalid_grant":
            raise UploadError(TOKEN_EXPIRED_HINT)
        raise UploadError(f"액세스 토큰 갱신 실패 HTTP {r.status_code} error={err or '?'}")   # 응답 본문은 찍지 않는다(C9)
    return r.json()["access_token"]


def _api_error(r: httpx.Response, what: str) -> UploadError:
    e = _json(r).get("error", {})
    reasons = [x.get("reason", "") for x in e.get("errors", [])] if isinstance(e, dict) else []
    msg = e.get("message", "") if isinstance(e, dict) else str(e)
    hint = " — 하루 할당량 소진, 태평양 시간 자정 뒤 다시" if {"quotaExceeded", "uploadLimitExceeded"} & set(reasons) else ""
    return UploadError(f"{what} 실패 HTTP {r.status_code} {','.join(reasons)} {msg}{hint}".strip())


def _range_next(r: httpx.Response) -> int:
    rng = r.headers.get("range")
    return int(rng.split("-")[1]) + 1 if rng else 0


def upload_video(client: httpx.Client, cfg: YouTubeConfig, token: str, video: Path, meta: UploadMetadata,
                 sleep=time.sleep) -> str:  # noqa: ANN001 — 시험에서 대기 없애기
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
            last = ""
            try:
                r = client.put(session, content=data,
                               headers={**auth, "Content-Range": f"bytes {pos}-{pos + len(data) - 1}/{size}"})
                if r.status_code in (httpx.codes.OK, httpx.codes.CREATED):
                    return r.json()["id"]
                if r.status_code == httpx.codes.PERMANENT_REDIRECT:   # 308 Resume Incomplete
                    pos, fails = _range_next(r), 0
                    print(f"[youtube] 업로드 {pos}/{size} 바이트", file=sys.stderr, flush=True)
                    continue
                if r.status_code not in RETRY_STATUS:
                    raise _api_error(r, "영상 업로드")
                last = f"HTTP {r.status_code}"
            except httpx.TransportError as ex:
                last = type(ex).__name__
            fails += 1
            if fails >= cfg.tries:
                raise UploadError(f"영상 업로드 재시도 {cfg.tries}회 실패: {last}")
            sleep(2 ** fails)
            q = client.put(session, headers={**auth, "Content-Range": f"bytes */{size}"})   # 서버가 받은 위치 확인
            if q.status_code in (httpx.codes.OK, httpx.codes.CREATED):
                return q.json()["id"]
            pos = _range_next(q)


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


def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(MB), b""):
            h.update(block)
    return h.hexdigest()


def resolve_inputs(proj: Path, video: Path | None, desc: Path | None, srt: Path | None,
                   caption: bool) -> tuple[Path, Path, Path | None]:
    out = proj / "out"
    v = video or out / "final.mp4"
    d = desc or out / "description.txt"
    for p, what in ((v, "영상"), (d, "설명")):
        if not p.is_file():
            raise UploadError(f"{what} 파일 없음: {p} — python -m engine.mux {proj} 먼저")
    if not caption:
        return v, d, None
    s = srt or out / "final.srt"
    if not s.is_file():
        raise UploadError(f"자막 파일 없음: {s} — 자막 없이 올리려면 --no-caption")
    return v, d, s


def run(proj: Path, *, video: Path | None = None, desc: Path | None = None, srt: Path | None = None,
        caption: bool = True, tags: list[str] | None = None, synthetic: bool | None = None,
        dry_run: bool = False, transport: httpx.BaseTransport | None = None,
        env: dict[str, str] | None = None) -> StageResult:
    """업로드 단계 하나. 실패는 UploadError — main 이 StageResult(ok=False)로 바꾼다."""
    cfg = youtube_cfg()
    v, d, s = resolve_inputs(proj, video, desc, srt, caption)
    syn = cfg.contains_synthetic_media if synthetic is None else synthetic
    meta, trims = build_metadata(d.read_text(encoding="utf-8"), tags or [], syn, cfg)
    errs = validate_metadata(meta, cfg)
    if errs:
        raise UploadError("메타데이터 검증 실패: " + " · ".join(errs))
    warns = [f"설명 한도로 줄임: {t}" for t in trims]
    size, md5 = v.stat().st_size, md5_file(v)
    dest = proj / "out" / "youtube_upload.json"
    print(f"[youtube] 제목: {meta.title} · 설명 {_nbytes(meta.description)}B · 영상 {size / MB:.1f}MB · "
          f"자막 {'있음' if s else '없음'} · privacy={meta.privacy_status} · 합성 표시={syn}", file=sys.stderr)
    if dry_run:
        return StageResult(ok=True, stage=STAGE, warnings=[*warns, "dry-run — 올리지 않음"],
                           provenance={"youtube": {"dry_run": True, "description_trims": trims}})
    if dest.is_file():
        prev = UploadRecord.model_validate_json(dest.read_text(encoding="utf-8"))
        if prev.video_md5 == md5:   # 같은 영상을 두 번 올리지 않는다(advance 재실행)
            return StageResult(ok=True, stage=STAGE, artifacts={"youtube": str(dest)},
                               warnings=[f"이미 올린 영상(md5 {md5[:8]}) — {prev.url} · 다시 올리지 않음"],
                               provenance={"youtube": prev.model_dump()})
    secrets = read_secrets(env)
    with httpx.Client(timeout=cfg.timeout_sec, transport=transport) as client:
        token = access_token(client, cfg, secrets)
        vid = upload_video(client, cfg, token, v, meta)
        rec = UploadRecord(video_id=vid, url=cfg.watch_url_prefix + vid,
                           uploaded_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                           privacy_status=meta.privacy_status,
                           video_file=str(v.relative_to(proj)) if v.is_relative_to(proj) else str(v),
                           video_bytes=size, video_md5=md5, title=meta.title, contains_synthetic_media=syn,
                           description_bytes=_nbytes(meta.description), description_trims=trims)
        dest.write_text(rec.model_dump_json(indent=1), encoding="utf-8")   # 자막이 실패해도 영상 기록은 남는다
        print(f"[youtube] 영상 업로드 완료 {rec.url} (비공개)", file=sys.stderr, flush=True)
        if s is not None:
            rec.caption_id = upload_caption(client, cfg, token, vid, s)
            dest.write_text(rec.model_dump_json(indent=1), encoding="utf-8")
    return StageResult(ok=True, stage=STAGE, artifacts={"youtube": str(dest), "url": rec.url}, warnings=warns,
                       provenance={"youtube": rec.model_dump()})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="완성 영상을 유튜브에 비공개로 올린다")
    ap.add_argument("proj", type=Path, help="projects/<pid>")
    ap.add_argument("--synthetic-media", choices=("yes", "no"), help="기본 config.yaml youtube.contains_synthetic_media")
    ap.add_argument("--video", type=Path, help="기본 out/final.mp4")
    ap.add_argument("--description-file", type=Path, help="기본 out/description.txt(첫 줄 제목)")
    ap.add_argument("--srt", type=Path, help="기본 out/final.srt")
    ap.add_argument("--no-caption", action="store_true", help="자막을 올리지 않는다")
    ap.add_argument("--tags", default="", help="쉼표로 구분")
    ap.add_argument("--dry-run", action="store_true", help="메타데이터만 검증하고 올리지 않는다(비밀값 불필요)")
    a = ap.parse_args(argv)
    try:
        res = run(a.proj.resolve(), video=a.video, desc=a.description_file, srt=a.srt, caption=not a.no_caption,
                  tags=[t.strip() for t in a.tags.split(",") if t.strip()],
                  synthetic=None if a.synthetic_media is None else a.synthetic_media == "yes", dry_run=a.dry_run)
    except (UploadError, OSError, ValueError) as ex:
        res = StageResult(ok=False, stage=STAGE, errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
