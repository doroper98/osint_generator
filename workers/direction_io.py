"""연출·검수 워커 공용 입력 조립 (v3.1.0, docs/handoff/17 §5.3~5.5, back_and_forth D-0047 작업 8).

워커는 자기 몫의 입력만 본다(15 P9): 원고·타이밍·레지스트리·지오 역량·이벤트 필드(연출가), 시트·컷 정보·검사(검수자),
직전 연출·판정·검사(수정). 이전 버전 산출물·옛 템플릿을 "참고"로 넣지 않는다.
"""

from __future__ import annotations

import json
import typing
from pathlib import Path

import yaml
from pydantic import BaseModel

from engine.direction import Direction, DirectionError
from engine.entities import load_entities
from engine.registry import REGISTRY, RegistryError
from script.schema import Plan

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
            fields.append(f"{name}{'*' if f.is_required() else ''}: {_ann(f.annotation)}")
            subs += _nested(f.annotation, seen)
        where = " (패널 — 아래 필드는 data 아래)" if key.startswith("panel:") else ""
        lines.append(f"- {key}{where}: " + "; ".join(fields))
        lines += subs
    lines.append("- 공통: start*·end* 앵커. 사진·영상·뱃지·컷아웃·마커·카드는 place(배치 슬롯) 가능. "
                 "하위 필드의 시각(at·t0·t1·t·t_show·t_join 등 float 초)에도 숫자 대신 앵커를 쓴다")
    return "\n".join(lines)


def plan_table(plan: Plan) -> str:
    return "\n".join(f"{s.sid:<12} {s.scene:<10} {s.t0:7.2f}~{s.t1:7.2f}  {s.text}" for s in plan.sentences)


def entities_text(pdir: Path) -> str:
    reg = load_entities()
    flags = sorted({p.name.split("_")[0] for p in (pdir / "assets" / "flags").glob("*_1x1.png")}) if (pdir / "assets" / "flags").exists() else []
    rows = []
    for eid, e in reg.entities.items():
        d = e.__dict__ if not isinstance(e, BaseModel) else e.model_dump()
        rows.append(f"- {eid}: {d.get('kind')} · {', '.join((d.get('names') or [])[:2])} · flag {d.get('flag')}"
                    + (f" · emblem {d.get('emblem')}" if d.get("emblem") else "") + (f" · {d.get('role_default')}" if d.get("role_default") else ""))
    return "\n".join(rows) + f"\n- 국기(flag) 코드: {', '.join(flags) or '(프로젝트 국기 없음)'}"


def media_text() -> str:
    from engine.media_registry import load_media_registry  # noqa: PLC0415

    return "\n".join(f"- {mid}: {a.kind} · {a.caption} · {a.file_note}" + (f" · 구간 {a.segment}" if a.segment else "")
                     for mid, a in load_media_registry().items())


def geo_text(pdir: Path) -> str:
    g = yaml.safe_load((pdir / "geo.yaml").read_text(encoding="utf-8"))
    tiers = "; ".join(f"{t['name']} bbox {t['bbox']}" for t in g.get("tiers", []))
    return f"국가 지오메트리 권역 bbox {g.get('bbox')}. 지형 티어(카메라 경계 = W): {tiers}. 카메라 w(화면 폭, 경도 도)는 2.5~96."


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


__all__ = ["check_direction", "dump_direction_yaml", "entities_text", "event_fields_table", "geo_text", "load_plan",
           "media_text", "next_version", "plan_table"]
