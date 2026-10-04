"""참조 출처 화면 표기 (v5.6.0, 사용자 결정 2026-10-04 — rules source_note).

위키백과 같은 참조 출처를 내레이션에서 "위키백과에 따르면"으로 반복해 읽지 않는다. 대신 그 출처에 근거한 문장이 읽히는 동안
화면 왼쪽 아래에 아주 작게(글자 크기 = 엔딩 카드 버전 도장과 같다) 링크만 보인다. 근거 = 원고 문장 sources → claims.json evidence →
sources.json publisher·url. 연출 파일이 아니라 원고·검증 기록에서 코드가 계산한다(P8 — 사실 텍스트는 코드 렌더).
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote

import cairo
import yaml

from engine.context import RenderCtx
from engine.fullcards import STAMP
from engine.style import C, H_OUT
from engine.typography import text
from rules import load_rules

SN = load_rules().source_note


def _short(url: str) -> str:
    u = unquote(url)
    for p in ("https://", "http://"):
        if u.startswith(p):
            u = u[len(p):]
    return u.rstrip("/")


def source_notes(proj: Path) -> dict[str, str]:
    """sid → 표기 문자열. 원고·claims·sources 중 하나라도 없으면 빈 사전(표기 없음 — 출처 기록이 없는 영상)."""
    sp, cp, srp = proj / "script.yaml", proj / "intake" / "claims.json", proj / "intake" / "sources.json"
    if not (sp.exists() and cp.exists() and srp.exists()):
        return {}
    srcs = json.loads(srp.read_text(encoding="utf-8"))
    srcs = srcs["sources"] if isinstance(srcs, dict) else srcs
    ref = {s["id"]: _short(s["url"]) for s in srcs
           if s.get("url") and any(str(s.get("publisher", "")).startswith(p) for p in SN.publishers)}
    if not ref:
        return {}
    ev = {c["claim_id"]: c.get("source_ids", []) for c in json.loads(cp.read_text(encoding="utf-8"))["claims"]}
    out: dict[str, str] = {}
    for sc in yaml.safe_load(sp.read_text(encoding="utf-8"))["scenes"]:
        for k, s in enumerate(sc["sentences"]):
            urls = list(dict.fromkeys(ref[sid] for c in s.get("sources", []) for sid in ev.get(c, []) if sid in ref))
            if urls:
                out[f"{sc['id']}_{k}"] = SN.prefix + " · ".join(urls)
    return out


def draw_source_note(ctx: cairo.Context, R: RenderCtx, t: float, notes: dict[str, str]) -> None:  # noqa: N803
    if not notes or R.tb.in_fullcard(t):
        return
    for sid, note in notes.items():
        s = R.tb.sent.get(sid)
        if s is not None and s.t0 <= t <= s.t1:
            text(ctx, note, SN.x, H_OUT - SN.y_from_bottom, STAMP.size, STAMP.font, C["muted"], SN.alpha, 0, "l", role="media_meta")
            return
