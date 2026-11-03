"""고정 격자 조각 캐시 — 부분 재렌더(v7.4.0 back_and_forth D-1000 S2, 사용자 UF-300 "거의 이틀이 걸려").

조각 경계 = config engine.render.chunk_sec 의 고정 격자(t=0 정렬). jobs 는 작업자 수일 뿐 경계와 무관하다 — 그래서 문장 하나를 고친 뒤
바뀌지 않은 조각은 `out/chunks/<판>/<idx>_<키>.mp4` 를 그대로 쓴다.

조각 키 = sha1(전역 키 + 조각 입력 조각 + 탐침 서명)
- 전역 키: 판(animatic·catalog·final)·출력 프로파일(해상도·fps·crf·preset)·인코더 인자·렌더 코드(engine·schemas·rules·geo·script·genres 의
  .py 내용)·rules_hash·config.yaml·프로젝트 자산 목록(경로·크기·mtime)·영상 길이(전체 페이드). 엔진 코드가 바뀌면 전부 무효(보수적, 커밋 안 한 수정 포함).
- 조각 입력: 조각 창 ± margin 에 걸치는 이벤트(dict 전체)·그 프레임들의 카메라 값·창에 걸치는 문장·카드.
- 탐침 서명: 조각 안 {probe_step_sec 간격} ∪ {조각 안 이벤트 시작·끝 ±1프레임} 프레임을 **출력 해상도 그대로** 그린 바이트의 sha1.
  (D-1000 은 probe_scale 0.25 축소 렌더를 제안했으나 지형 래스터가 프로파일별 자산(assets/res_<프로파일>)이라 축소 장치에서 그릴 수 없다 —
  구현 전결: 전체 해상도 탐침. 캐시 후보가 없는 조각은 렌더하면서 같은 프레임에서 서명을 떠서 추가 비용 0, 후보가 있을 때만 탐침을 먼저 그린다.)
조용한 재사용 금지(P6): 키가 정확히 같을 때만 재사용하고, 조각마다 reused|rendered·시간을 render.json 에 남긴다.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from engine.project import Project

REPO = Path(__file__).resolve().parent.parent
CODE_DIRS = ("engine", "schemas", "rules", "geo", "script", "genres")
EVENT_PAD_SEC = 0.05   # render_frame act 창(t0 − 0.05 ≤ t ≤ t1 + 0.05)과 같은 값


def render_cfg():  # noqa: ANN201 — orchestrator.config.RenderConfig
    from orchestrator.config import load_config  # noqa: PLC0415

    rc = load_config().engine.render
    missing = [k for k in ("chunk_sec", "probe_step_sec") if getattr(rc, k) is None]
    if missing:
        raise ValueError(f"config.yaml engine.render.{'·'.join(missing)} 없음 — 조각 캐시 설정(D-1000 S2)")
    return rc


def chunk_frames(fps: int) -> int:
    return max(1, round(render_cfg().chunk_sec * fps))


def grid_ranges(n_frames: int, step: int) -> list[tuple[int, int]]:
    """고정 격자 [(시작, 끝)] — t=0 정렬, 마지막 조각만 짧다."""
    return [(s, min(n_frames, s + step)) for s in range(0, n_frames, step)]


def _jsonable(o: Any) -> Any:  # noqa: ANN401
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, (set, frozenset)):
        return sorted(map(str, o))
    if hasattr(o, "model_dump"):
        return o.model_dump()
    return f"<{type(o).__name__}>"


def _sha(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def code_hash() -> str:
    """렌더 코드 내용 해시(커밋하지 않은 수정 포함) + 규칙·설정 파일."""
    h = hashlib.sha1()
    for d in CODE_DIRS:
        for f in sorted((REPO / d).rglob("*.py")):
            h.update(str(f.relative_to(REPO)).encode())
            h.update(f.read_bytes())
    for f in sorted((REPO / "rules").glob("*.yaml")) + [REPO / "config.yaml"]:
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def assets_manifest(proj: Path) -> str:
    """프로젝트·저장소 자산 목록(경로·크기·mtime_ns) — 사진·지형·글꼴을 바꾸면 전부 무효."""
    h = hashlib.sha1()
    roots = [proj / "assets", proj / "media", proj / "portraits", REPO / "assets"]
    for r in roots:
        if not r.exists():
            continue
        for f in sorted(r.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and "out" not in f.relative_to(r).parts[:1]:
                st = f.stat()
                h.update(f"{f.relative_to(REPO) if f.is_relative_to(REPO) else f}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    return h.hexdigest()


FC_PROPS: tuple[str, ...] = ("antialias", "hinting", "hintstyle", "rgba", "lcdfilter")   # 글자 화소를 정하는 fontconfig 렌더 속성(RENDER-AP-032)
_FONT_ENV: dict[str, str] = {}   # 프로세스당 한 번(설정 파일 경로 → 지문). 시험은 비우고 다시 잰다


def conf_chain(conf: Path, seen: "set[Path] | None" = None) -> list[tuple[str, bytes]]:
    """fonts.conf 와 그 include 체인(파일·디렉터리 안 *.conf 정렬) → [(경로, 내용)]. 없는 include 는 건너뛴다(fontconfig 와 같음)."""
    import re  # noqa: PLC0415

    seen = set() if seen is None else seen
    conf = conf.expanduser().resolve()
    if conf in seen or not conf.exists():
        return []
    seen.add(conf)
    if conf.is_dir():
        return [x for f in sorted(conf.glob("*.conf")) for x in conf_chain(f, seen)]
    body = conf.read_bytes()
    out = [(str(conf), body)]
    for m in re.finditer(rb"<include[^>]*>([^<]+)</include>", body):
        inc = Path(m.group(1).decode().strip()).expanduser()
        out += conf_chain(inc if inc.is_absolute() else conf.parent / inc, seen)
    return out


def fc_props(family: str, bold: bool, env: "dict[str, str] | None" = None) -> dict[str, str]:
    """fc-match -v 로 실제 적용되는 렌더 속성과 고른 파일 — 엔진 글꼴 패밀리 하나."""
    import re  # noqa: PLC0415
    import subprocess  # noqa: PLC0415

    pat = f"{family}:weight=bold" if bold else family
    out = subprocess.run(["fc-match", "-v", pat], capture_output=True, text=True, env=env, check=True, timeout=60).stdout
    got = {k: (m.group(1).strip() if (m := re.search(rf"^\s*{k}:\s*(.+)$", out, re.M)) else "") for k in (*FC_PROPS, "file")}
    return got


def file_md5(path: str) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()  # noqa: S324 — 내용 지문(보안 용도 아님)


def font_env_fingerprint(conf: "Path | None" = None) -> str:
    """글꼴 환경 지문(v7.4.0 D-1005, RENDER-AP-032 후속) — 탐침 프레임에 글자가 없는 조각도 글꼴 설정이 바뀌면 무효가 되게.
    (a) 실제 쓰는 fonts.conf(FONTCONFIG_FILE) 내용 + include 체인, (b) engine.style 글꼴 패밀리마다 fc-match 렌더 속성,
    (c) 그 패밀리들이 고른 글꼴 파일 md5. 설정 파일 경로마다 프로세스당 한 번만 잰다."""
    from engine.style import FONT  # noqa: PLC0415 — import 가 fontenv.ensure(표준 FONTCONFIG_FILE)를 먼저 부른다

    path = Path(conf or os.environ.get("FONTCONFIG_FILE") or "/etc/fonts/fonts.conf")
    k = str(path)
    if k not in _FONT_ENV:
        env = {**os.environ, "FONTCONFIG_FILE": str(path)}
        h = hashlib.sha1()
        for p_, body in conf_chain(path):
            h.update(p_.encode() + b"\0" + body + b"\0")
        files: dict[str, str] = {}
        for name in sorted(FONT):
            fam, bold = FONT[name]
            pr = fc_props(fam, bool(bold), env)
            h.update(json.dumps([name, {x: pr[x] for x in FC_PROPS}], sort_keys=True).encode())
            if pr["file"]:
                files[pr["file"].split('"')[1] if '"' in pr["file"] else pr["file"]] = ""
        for f in sorted(files):
            h.update(f"{f}|{file_md5(f) if Path(f).exists() else 'missing'}".encode())
        _FONT_ENV[k] = h.hexdigest()
    return _FONT_ENV[k]


def global_key(P: "Project", kind: str, encoder: list[str]) -> str:  # noqa: N803
    rec = {"kind": kind, "profile": P.R.out.record(), "encoder": encoder, "code": code_hash(), "assets": assets_manifest(P.root),
           "total": round(P.plan.total, 6), "n_frames": P.n_frames, "fontenv": font_env_fingerprint()}
    return _sha(json.dumps(rec, sort_keys=True, default=_jsonable).encode())


def event_window(ev: dict) -> tuple[float, float]:
    """이벤트가 화면에 그려질 수 있는 창 — render_frame act(±0.05) + backdrop crossfade 꼬리. 시각이 없는 이벤트 = 전 구간."""
    from engine.style import BACKDROP  # noqa: PLC0415

    tail = BACKDROP.crossfade_sec if ev.get("type") == "backdrop" else 0.0
    return ev.get("t0", -1e9) - EVENT_PAD_SEC, ev.get("t1", 1e9) + EVENT_PAD_SEC + tail


def slice_key(P: "Project", s: int, e: int, fps: int) -> str:  # noqa: N803
    """조각 입력 — 조각 창에 그려질 수 있는 이벤트(event_window)·창에 걸치는 문장(± 0.1초)·카드, 그 프레임의 카메라.
    창 밖 이벤트가 이 조각 그림에 주는 영향(전역 배치 등)은 탐침 서명이 잡는다."""
    a, b = s / fps, (e - 1) / fps   # 조각의 첫·마지막 프레임 시각
    evs = [ev for ev in P.events if event_window(ev)[0] <= b and event_window(ev)[1] >= a]
    a, b = a - EVENT_PAD_SEC, b + EVENT_PAD_SEC
    sents = [x for x in P.plan.sentences if x.t0 <= b and x.t1 >= a]
    align = {x.sid: P.R.tb.alignment(x.sid) for x in sents}   # 자막 단어 시각(.align.json)
    cards = [c.model_dump() for c in P.plan.cards if c.t0 <= b and c.t1 >= a]
    cams = np.ascontiguousarray(np.asarray(P.cams[s:e]))
    body = json.dumps({"events": evs, "sentences": [x.model_dump() for x in sents], "align": align, "cards": cards},
                      sort_keys=True, default=_jsonable).encode()
    return _sha(body + cams.tobytes())


def probe_frames(P: "Project", s: int, e: int, fps: int) -> list[int]:  # noqa: N803
    """탐침 프레임 — 조각 안 probe_step_sec 간격 + 조각 안 이벤트 시작·끝 ±1프레임(정렬·중복 없음)."""
    step = max(1, round(render_cfg().probe_step_sec * fps))
    fr = set(range(s, e, step))
    for ev in P.events:
        for k in ("t0", "t1"):
            t = ev.get(k)
            if isinstance(t, (int, float)):
                f = int(t * fps)
                fr.update(x for x in (f - 1, f, f + 1) if s <= x < e)
    return sorted(fr)


def chunk_key(gkey: str, skey: str, probe_sig: str) -> str:
    return _sha(f"{gkey}|{skey}|{probe_sig}".encode())


def probe_signature(P: "Project", frames: list[int]) -> str:  # noqa: N803
    """탐침 프레임을 그려 바이트 sha1 을 잇는다(렌더 전 탐침 — 캐시 후보가 있을 때만). 대비 보정 기록은 건드리지 않는다."""
    from engine import typography  # noqa: PLC0415
    from engine.render import render_frame  # noqa: PLC0415

    saved = dict(typography.CONTRAST_FIXED)
    h = hashlib.sha1()
    try:
        for i in frames:
            _, buf = render_frame(P, i)
            h.update(hashlib.sha1(buf).digest())
    finally:
        typography.CONTRAST_FIXED.clear()
        typography.CONTRAST_FIXED.update(saved)
    return h.hexdigest()


SIDECARS = (".contrast_fix.json", ".catalog.json")


def cache_path(cdir: Path, idx: int, key: str) -> Path:
    return cdir / f"{idx:04d}_{key[:20]}.mp4"


def candidates(cdir: Path, idx: int) -> list[Path]:
    return sorted(cdir.glob(f"{idx:04d}_*.mp4"))


def prune(cdir: Path, idx: int, keep: Path) -> None:
    """같은 조각 번호의 옛 키 파일 정리(캐시 크기 = 한 벌)."""
    for p in candidates(cdir, idx):
        if p != keep:
            for f in [p, *(p.with_suffix(x) for x in SIDECARS)]:
                f.unlink(missing_ok=True)


def claim(qdir: Path, idx: int) -> bool:
    """작업자 사이 조각 하나 차지(O_EXCL — 먼저 만든 쪽만). 큐 = 파일 체계."""
    try:
        os.close(os.open(qdir / f"{idx:04d}.claim", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def run_worker(P: "Project", plan_path: Path, worker: int) -> None:  # noqa: N803
    """작업자 하나 — 큐(plan.json)의 조각을 차례로 차지해 재사용하거나 그린다. 결과 = qdir/<idx>.json."""
    from engine.render import render_chunk  # noqa: PLC0415
    from engine.style import FPS  # noqa: PLC0415

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    qdir, cdir = Path(plan["qdir"]), Path(plan["cdir"])
    chunks = plan["chunks"]
    order = chunks[worker::plan["workers"]] + [c for k, c in enumerate(chunks) if k % plan["workers"] != worker]
    # 조각 입력 키는 그리기 전에 한꺼번에 — 렌더러가 이벤트 dict 에 붙이는 지연 캐시(curve·press_surf 등)가 키에 섞이지 않게
    skeys = {c["idx"]: slice_key(P, c["s"], c["e"], FPS) for c in chunks}
    for c in order:
        idx = c["idx"]
        if not claim(qdir, idx):
            continue
        s, e = c["s"], c["e"]
        t0 = time.perf_counter()
        skey = skeys[idx]
        frames = probe_frames(P, s, e, FPS)
        cands = [] if plan["no_cache"] else candidates(cdir, idx)
        status, probe_sec, path = "rendered", 0.0, None
        if cands:
            tp = time.perf_counter()
            key = chunk_key(plan["gkey"], skey, probe_signature(P, frames))
            probe_sec = time.perf_counter() - tp
            hit = cache_path(cdir, idx, key)
            if hit.exists() and all(hit.with_suffix(x).exists() for x in plan["sidecars"]):
                status, path = "reused", hit
        if path is None:
            tmp = cdir / f"{idx:04d}.w{worker}.tmp.mp4"
            sig = render_chunk(P, s, e, tmp, probe=frames)
            key = chunk_key(plan["gkey"], skey, sig)
            path = cache_path(cdir, idx, key)
            for x in plan["sidecars"]:
                os.replace(tmp.with_suffix(x), path.with_suffix(x))
            os.replace(tmp, path)
        prune(cdir, idx, path)
        (qdir / f"{idx:04d}.json").write_text(json.dumps({"idx": idx, "s": s, "e": e, "status": status, "key": key[:20],
                                                          "path": str(path), "sec": round(time.perf_counter() - t0, 3),
                                                          "probe_sec": round(probe_sec, 3), "probe_frames": len(frames),
                                                          "worker": worker}), encoding="utf-8")
