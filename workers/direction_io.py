"""연출·검수 워커 공용 입력 조립 (v3.1.0, docs/handoff/17 §5.3~5.5, back_and_forth D-0047 작업 8).

워커는 자기 몫의 입력만 본다(15 P9): 원고·타이밍·레지스트리·지오 역량·이벤트 필드(연출가), 시트·컷 정보·검사(검수자),
직전 연출·판정·검사(수정). 이전 버전 산출물·옛 템플릿을 "참고"로 넣지 않는다.
"""

from __future__ import annotations

import hashlib
import json
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel

from engine.direction import Direction, DirectionError
from engine.entities import load_entities
from engine.registry import REGISTRY, RegistryError
from script.schema import Plan

if TYPE_CHECKING:
    from schemas.genre_models import GenreProfile

SKIP_FIELDS = {"type", "t0", "t1"}


def _ann(t: object) -> str:
    s = str(t).replace("typing.", "").replace("<class '", "").replace("'>", "")
    return s.replace("engine.events.", "").replace("NoneType", "None")


def _nested(t: object, seen: set[type]) -> list[str]:
    """주석 안의 하위 모델(RelationNode 등)을 한 번씩 펼친다."""
    out: list[str] = []
    args = typing.get_args(t) or ()
    cands = [t, *args]
    for a in cands:
        if isinstance(a, type) and issubclass(a, BaseModel) and a not in seen:
            seen.add(a)
            fs = "; ".join(f"{n}{'*' if f.is_required() else ''}: {_ann(f.annotation)}" for n, f in a.model_fields.items())
            out.append(f"    · {a.__name__} = {{{fs}}}")
            for f in a.model_fields.values():
                out += _nested(f.annotation, seen)
        elif a is not t:
            out += _nested(a, seen)
    return out


def event_fields_table() -> str:
    """레지스트리의 이벤트 모델에서 필드 표를 만든다(필수 *). 코드가 정본 — 프롬프트에 손으로 적지 않는다."""
    lines: list[str] = []
    for key, entry in REGISTRY.items():
        model: type[BaseModel] = entry.model
        if key == "panel":
            continue
        fields = []
        subs: list[str] = []
        seen: set[type] = set()
        for name, f in model.model_fields.items():
            if name in SKIP_FIELDS or (key.startswith("panel:") and name == "kind"):
                continue
            note = f" ({f.description})" if f.description else ""   # v5.2.0 LLM-AP-011 — 스키마 제약(형식·상한)을 필드 표에
            fields.append(f"{name}{'*' if f.is_required() else ''}: {_ann(f.annotation)}{note}")
            subs += _nested(f.annotation, seen)
        where = " (패널 — 아래 필드는 data 아래)" if key.startswith("panel:") else ""
        lines.append(f"- {key}{where}: " + "; ".join(fields))
        lines += subs
    lines.append("- 공통: start*·end* 앵커. 사진·영상·뱃지·컷아웃·마커·카드는 place(배치 슬롯) 가능. "
                 "하위 필드의 시각(at·t0·t1·t·t_show·t_join 등 float 초)에도 숫자 대신 앵커를 쓴다")
    return "\n".join(lines)


def plan_table(plan: Plan) -> str:
    return "\n".join(f"{s.sid:<12} {s.scene:<10} {s.t0:7.2f}~{s.t1:7.2f}  {s.text}" for s in plan.sentences)


def cards_table(plan: Plan) -> str:
    """전면 카드 시각 — 카드는 장면 **안**에 들 수 있다(예: 타이틀 카드는 open 장면 안). 앵커는 {card: 종류, edge: start|end}."""
    return "\n".join(f"card:{c.kind:<6} {c.t0:7.2f}~{c.t1:7.2f}  (앵커 {{card: {c.kind}}} — 이 구간엔 지도 요소가 카드 밑에 비친다)"
                     for c in plan.cards)


def current_version(pdir: Path) -> int | None:
    """direction.yaml 과 바이트가 같은 가장 늦은 보관본 번호. 없으면 None(사람이 고쳤거나 보관본 없음)."""
    cur = (pdir / "direction.yaml").read_bytes() if (pdir / "direction.yaml").exists() else None
    n = next_version(pdir, "direction", ".yaml") - 1
    while n >= 1:
        if (pdir / f"direction.v{n}.yaml").read_bytes() == cur:
            return n
        n -= 1
    return None


def restore_version(pdir: Path, n: int) -> None:
    """보관본 direction.v{n}.yaml 을 direction.yaml 로(판 선택 — 보관본은 그대로, D-0049 쟁점 3). 새 판을 만들지 않는다."""
    src = pdir / f"direction.v{n}.yaml"
    if not src.exists():
        raise FileNotFoundError(f"보관본 없음: {src}")
    (pdir / "direction.yaml").write_bytes(src.read_bytes())


def loop_history(pdir: Path) -> str:
    """같은 루프의 회차별 (판 → 검사·검수 → 지적 → 바꾼 것) 요약(D-0049 쟁점 2). 이전 영상·옛 템플릿이 아니라 이 루프의 자기 이력."""
    from engine.qa import QALoopRecord, QAVerdict  # noqa: PLC0415

    p = pdir / "prev" / "qa_loop.json"
    if not p.exists():
        return "(첫 수정 — 앞 회차 없음)"
    rec = QALoopRecord.model_validate_json(p.read_text(encoding="utf-8"))
    out: list[str] = []
    for r in rec.rounds:
        head = f"- direction.v{r.version}: checks hard {r.checks_hard}"
        if r.qa:
            head += f" · 검수 hard {r.qa_hard} soft {r.qa_soft}"
        out.append(head)
        if r.qa and (pdir / "prev" / r.qa).exists():
            v = QAVerdict.model_validate_json((pdir / "prev" / r.qa).read_text(encoding="utf-8"))
            out += [f"    지적 {i.severity} {i.frame} {i.fix.event_ref if i.fix else i.category}: {i.evidence[:90]}" for i in v.issues]
        if r.revision and (pdir / "prev" / r.revision).exists():
            rv = json.loads((pdir / "prev" / r.revision).read_text(encoding="utf-8"))
            out += [f"    → 바꾼 것 {c['issue_ref']}: {c['change'][:140]}" for c in rv.get("changelog", [])]
    return "\n".join(out) if out else "(첫 수정 — 앞 회차 없음)"


def entities_text(pdir: Path) -> str:
    reg = load_entities()
    flags = sorted({p.name.split("_")[0] for p in (pdir / "assets" / "flags").glob("*_1x1.png")}) if (pdir / "assets" / "flags").exists() else []
    rows = []
    for eid, e in reg.entities.items():
        d = e.__dict__ if not isinstance(e, BaseModel) else e.model_dump()
        rows.append(f"- {eid}: {d.get('kind')} · {', '.join((d.get('names') or [])[:2])} · flag {d.get('flag')}"
                    + (f" · emblem {d.get('emblem')}" if d.get("emblem") else "") + (f" · {d.get('role_default')}" if d.get("role_default") else ""))
    return "\n".join(rows) + f"\n- 국기(flag) 코드: {', '.join(flags) or '(프로젝트 국기 없음)'}"


def media_text(pdir: Path | None = None) -> str:
    """미디어 레지스트리 + (v3.2.0) 이 프로젝트에서 post 카드로 쓸 수 있는 X 게시물(사용자 확인·검증된 것만, 18 §5)."""
    from engine.media_registry import load_media_registry  # noqa: PLC0415

    reg = load_media_registry()
    own = False
    if pdir is not None:   # v4.4.0 — 주문(order.yaml)이 있는 프로젝트는 자기 자료만(15 P9): 파일이 프로젝트 media/ 에 있는 것, 기사는 소스 URL 과 같은 것
        from genres.load import load_order  # noqa: PLC0415

        if load_order(pdir) is not None:
            own = True
            from schemas.source_models import SourcesFile  # noqa: PLC0415

            spf = pdir / "intake" / "sources.json"
            urls = {s.url for s in SourcesFile.model_validate_json(spf.read_text(encoding="utf-8")).sources} if spf.exists() else set()
            reg = {mid: a for mid, a in reg.items()
                   if (a.url in urls if a.kind == "article" else bool(a.file) and (pdir / "media" / str(a.file)).exists())}
    rows = [f"- {mid}: {a.kind} · {a.caption} · {a.file_note}" + (f" · {'·'.join(a.depicts)}" if own and a.kind != "article" else "")
            + (f" · 구간 {a.segment}" if a.segment else "")
            for mid, a in reg.items()]
    sp = pdir / "intake" / "sources.json" if pdir is not None else None
    if sp is not None and sp.exists():
        from schemas.source_models import SourcesFile  # noqa: PLC0415

        posts = [s for s in SourcesFile.model_validate_json(sp.read_text(encoding="utf-8")).sources
                 if s.type == "x_post" and s.confirmed and s.verification is not None]
        if posts:
            rows.append("X 게시물 카드 — 이벤트 {type: post, src: <id>, hl?: 번역문 안 구절, quote?: bool, at?: card|panel}"
                        " (게시물 자체가 뉴스일 때만. 문구는 엔진이 소스에서 가져온다)")
            rows += [f"- {s.id}: {'개인 계정' if s.account_class == 'private' else s.account_name + ' ' + s.handle}"
                     f" · {s.account_class} · 검증 {s.verification.status} · {(s.text_ko or s.text_original)[:60]}" for s in posts]
    return "\n".join(rows)


def geo_text(pdir: Path) -> str:
    g = yaml.safe_load((pdir / "geo.yaml").read_text(encoding="utf-8"))
    tiers = "; ".join(f"{t['name']} bbox {t['bbox']}" for t in g.get("tiers", []))
    return f"국가 지오메트리 권역 bbox {g.get('bbox')}. 지형 티어(카메라 경계 = W): {tiers}. 카메라 w(화면 폭, 경도 도)는 2.5~96."


def series_records_text(pdir: Path) -> str:
    """주문(order.yaml data.series)의 데이터 레코드 요약 — 원고·연출 입력(v4.4.0 D-0090 작업 1). 값 목록은 넣지 않고
    구간·단위·기준 시점·빈 달·첫/마지막 값만(연출은 값을 쓰지 않는다, 원고는 레코드 대조 린트가 막는다)."""
    from data.series import load_series  # noqa: PLC0415
    from genres.load import load_order  # noqa: PLC0415

    order = load_order(pdir)
    if order is None or not order.data.series:
        return "(없음)"
    rows = []
    for sid in order.data.series:
        r = load_series(sid)
        if r.kind == "scatter":   # v4.4.0 — 점도표 레코드(열별 참가자 점, 중앙값은 코드 계산). dot_plot 프리미티브의 record
            cols = "; ".join(f"{c.label} {len(c.values)}명 중앙값 {c.median():g}" for c in r.columns)
            rows.append(f"- series:{r.series_id} · scatter(dot_plot 프리미티브 record 로만) · 단위 {r.unit} · 발표 {r.released} · 열 {cols} · 출처 {r.source}")
            continue
        miss = "; ".join(f"{m.date:%Y-%m} {m.note}" for m in r.missing) or "없음"
        (d0, v0), (d1, v1) = r.values[0], r.values[-1]
        rows.append(f"- series:{r.series_id} · 단위 {r.unit} · {r.transform.formula} · 구간 {d0:%Y-%m}~{d1:%Y-%m} · "
                    f"기준 시점 {r.as_of} · 첫 값 {v0:g} · 마지막 값 {v1:g} · 빈 달 {miss} · 출처 {r.source}")
    return "\n".join(rows)


def stage_text(pdir: Path, genre: "GenreProfile | None") -> str:
    """연출 입력 `{geo}` 자리(v4.4.0) — 주 무대가 지도면 지오 역량(바이트 동일), 시간축이면 무대 역량(레인·레코드)."""
    if genre is None or genre.stage.primary == "mercator":
        return geo_text(pdir)
    lanes = genre.stage.timeline.lanes if genre.stage.timeline is not None else []
    lane_rows = "; ".join(f"{ln.id}({ln.label}, {ln.kind})" for ln in lanes)
    island = (" — 차트는 차트 아일랜드(island 이벤트, 카메라 = stage: timeline 숏)로 띄운다" if genre.stage.primary == "backdrop" else "")
    return (f"(지도 무대 아님) 주 무대 {genre.stage.primary}{island}. 장르 프로필 기본 레인: {lane_rows}.\n"
            f"stage_config.timeline 의 start·end(YYYY-MM-DD)는 레코드 구간을 덮게 정한다. 카메라 w = 화면이 덮는 일수.\n"
            f"데이터 레코드(series 이벤트 series_id 는 이 id 만):\n{series_records_text(pdir)}{documents_text(pdir)}")


def documents_text(pdir: Path) -> str:
    """주문 data.documents 의 원문(intake 본문) — statement_diff 의 before·after 는 여기서 그대로 인용한다(코드가 대조, v4.4.0)."""
    from genres.load import load_order  # noqa: PLC0415
    from schemas.source_models import SourcesFile  # noqa: PLC0415

    order = load_order(pdir)
    spf = pdir / "intake" / "sources.json"
    if order is None or not order.data.documents or not spf.exists():
        return ""
    by_url = {s.url: s for s in SourcesFile.model_validate_json(spf.read_text(encoding="utf-8")).sources}
    rows = []
    for u in order.data.documents:
        src = by_url.get(u)
        body = pdir / "intake" / "bodies" / f"{src.id}.txt" if src is not None else None
        if body is None or not body.exists():
            continue
        text = " ".join(body.read_text(encoding="utf-8").split())
        rows.append(f"- {src.id} · {src.published_at} · {text[:1500]}")
    if not rows:
        return ""
    return ("\n원문 문서(statement_diff 의 before·after 는 아래 원문에서 연속 구절을 그대로 — 한 글자라도 다르면 렌더 전 오류):\n"
            + "\n".join(rows))


def music_list_text(pdir: Path) -> str:
    """연출가 입력 `{music_list}`(v3.4.0 D-0060 작업 3, F1): 프로젝트 credits.yaml 의 `music:` 행 id + 레지스트리 분위기 태그.
    비면 null 안내 — 음악 크레딧 없는 프로젝트에 BGM 을 넣어 권리 실패하던 것(NB11 F1)을 입력 단계에서 막는다."""
    from audio.registry import track  # noqa: PLC0415
    from engine.credits import load_credits  # noqa: PLC0415

    ids = [it.music for sec in load_credits(pdir / "credits.yaml").sections for it in sec.items if it.music]
    if not ids:
        return "(없음 — 이 프로젝트엔 음악 크레딧이 없다. sound.bgm 은 null, intensity·cues 만 쓴다)"
    rows = []
    for i in ids:
        t = track(i)
        mood = ", ".join(t.mood) if t.mood else "기록 없음"
        rows.append(f"- {i} · {t.name} — {t.author} · 길이 {t.duration_sec:.0f}초 · 분위기 {mood}" if t.duration_sec
                    else f"- {i} · {t.name} — {t.author} · 분위기 {mood}")
    return "\n".join(rows)


def camera_suggest_text(pdir: Path) -> tuple[str, str | None]:
    """카메라 제안값(engine.camera_suggest, v3.3.0 D-0056 작업 5) → 연출가 입력 텍스트와 제안 파일 sha1.
    **옵션이지 강제 아님(P8)**. 제안값만 보인다 — 이전 연출의 카메라 값은 넣지 않는다(15 P9). 파일이 없으면 (없음, None)."""
    from engine.camera_suggest import SUGGEST_FILE, load_suggest  # noqa: PLC0415

    cs = load_suggest(pdir)
    if cs is None:
        return "(없음 — 제안은 기존 direction 이 있을 때 engine.camera_suggest 가 만든다)", None
    rows = []
    for s in cs.shots:
        if s.suggested is None:
            continue
        g = s.suggested
        tr = f" · 들어오는 전환 {s.suggested_transition}" if s.suggested_transition else ""
        fit = "" if s.fits else f" · 다 담기지 않음({s.note})"
        rows.append(f"- 장면 {s.scene} {s.t:.1f}~{s.t_end:.1f}초 · 장소 {', '.join(s.points)} → "
                    f"cam lon {g.lon} lat {g.lat} w {g.w}{tr}{fit}")
    sha = hashlib.sha1((pdir / "prev" / SUGGEST_FILE).read_bytes()).hexdigest()
    return ("\n".join(rows) if rows else "(제안할 숏 없음)"), sha


def bundle_materials_text(pdir: Path) -> tuple[str, str | None]:
    """번들 재료 블록(v3.5.0 D-0063 작업 4) — `intake/bundle_materials.json` 이 있을 때만. **재료일 뿐 강제 아님**(P8).
    이전 영상의 연출은 넣지 않는다(15 P9) — 이 프로젝트 번들에서 뽑은 장소·경로·패널 데이터뿐. 없으면 ("", None)."""
    from bundle.to_direction import MATERIALS_FILE, BundleMaterials  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415
    from workers.prompt_loader import load_prompt  # noqa: PLC0415

    p = pdir / "intake" / MATERIALS_FILE
    if not p.exists():
        return "", None
    raw = p.read_bytes()
    mat = BundleMaterials.model_validate_json(raw)
    body = mat.model_dump_json(indent=1, exclude={"unmatched"}, exclude_defaults=False)
    return (load_prompt("director_bundle", load_rules()).replace("{materials}", body) + "\n",
            hashlib.sha1(raw).hexdigest())


def load_plan(pdir: Path) -> Plan:
    return Plan.model_validate(json.loads((pdir / "plan.json").read_text(encoding="utf-8")))


def check_direction(doc: Direction, pdir: Path) -> None:
    """렌더 전 점검 — 렌더와 **같은 경로**(engine.project.load_project, 배치 슬롯 해석·레지스트리·엔티티·예약영역·권리).
    위반은 ValueError(워커가 오류를 붙여 1회 재요청 — 16 §3)."""
    from engine.credits import RightsError  # noqa: PLC0415
    from engine.project import ProjectError, load_project  # noqa: PLC0415

    try:
        P = load_project(pdir, doc)  # noqa: N806
    except (ProjectError, RegistryError, RightsError, DirectionError) as ex:
        raise ValueError(str(ex)) from ex
    if P.keys[0].t != 0 or P.keys[0].mode != "cut":
        raise ValueError("첫 shot 은 at 0, mode cut 이어야 한다")


def dump_direction_yaml(doc: Direction, header: str) -> str:
    raw = doc.model_dump(mode="json", exclude_defaults=False)
    return header + yaml.safe_dump(raw, allow_unicode=True, sort_keys=False, width=160)


def next_version(pdir: Path, stem: str, suffix: str) -> int:
    n = 1
    while (pdir / f"{stem}.v{n}{suffix}").exists():
        n += 1
    return n


__all__ = ["cards_table", "check_direction", "current_version", "loop_history", "restore_version", "dump_direction_yaml", "entities_text", "event_fields_table", "geo_text", "load_plan", "documents_text", "series_records_text", "stage_text",
           "media_text", "next_version", "plan_table"]
