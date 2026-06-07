"""CompositionPlan 사실 가드 (순수 결정론 — LLM 없음).

codex/claude 가 낸 연출 플랜의 **텍스트**에 번들에 없는 숫자(사실)가 섞이면 `<미검증>`
으로 표시한다. 차트 데이터·축·값은 codex 가 애초에 만지지 못하므로(플랜은 연출만 담는다)
여기서는 헤드라인·자막·카운트업 같은 텍스트만 번들 사실과 대조한다.

경계(CLAUDE.md C9/C0): 사용자 결정 = "번들 외 텍스트 허용 + 미검증 라벨". 따라서
- 숫자가 아닌 표현/연결어 추가 → 자유 허용(라벨 안 붙임).
- 번들에 없는 **숫자**(파생·과장·환각) → 해당 텍스트에 `<미검증>` 라벨 강제.
라벨 적용(문자열 prepend)은 소비 단계(build_composed_scenes)에서 unverified 플래그를 보고 한다.
"""

from __future__ import annotations

import json
import re

from schemas.models import (
    CompositionPlan,
    PlanFactFinding,
    PlanValidationReport,
    ReportBundle,
)

# 숫자 토큰: 정수/소수. 천단위 콤마는 비교 전에 제거한다.
_NUM = re.compile(r"\d+(?:\.\d+)?")


def _bundle_numbers(bundle: ReportBundle) -> set[str]:
    """번들 전체를 JSON 으로 덤프해 등장하는 모든 숫자 토큰 집합(allowed set).

    소수의 정수부도 함께 허용한다(번들 "21.7" → "21" 도 OK). 반올림/축약 표기를 통과시키되
    완전 날조(999, 5000 등 번들에 흔적조차 없는 숫자)는 여전히 걸린다 — 사용자 '허용+라벨' 결정.
    """
    raw = json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False)
    raw = raw.replace(",", "")  # "7,383.74" 류 천단위 콤마 제거 후 추출
    nums = set(_NUM.findall(raw))
    return nums | {n.split(".")[0] for n in nums}


def _unverified_numbers(text: str | None, allowed: set[str]) -> list[str]:
    """text 안에서 allowed 에 없는 숫자 토큰을 돌려준다(번들 미존재 = 미검증 후보)."""
    if not text:
        return []
    bad: list[str] = []
    for tok in _NUM.findall(text.replace(",", "")):
        if tok in allowed:
            continue
        # 소수 → 정수부 일치도 허용 (예: 번들 "21.7" 있고 플랜이 "21" 만 써도 OK).
        if "." in tok and tok.split(".")[0] in allowed:
            continue
        bad.append(tok)
    return bad


def validate_and_label_plan(
    plan: CompositionPlan, bundle: ReportBundle
) -> tuple[CompositionPlan, PlanValidationReport]:
    """플랜의 텍스트를 번들 숫자와 대조 → 미검증 플래그를 채운 새 플랜 + 리포트 반환.

    플랜을 폐기(reject)하지는 않는다(사용자 '허용' 결정). 대신 unverified 표식만 단다.
    """
    allowed = _bundle_numbers(bundle)
    findings: list[PlanFactFinding] = []

    new_scenes = []
    for sc in plan.scenes:
        uf = list(sc.unverified_fields)
        for field in ("headline", "countup_value", "narration"):
            bad = _unverified_numbers(getattr(sc, field), allowed)
            if bad:
                if field not in uf:
                    uf.append(field)
                for b in bad:
                    findings.append(PlanFactFinding(
                        where=f"scene:{sc.scene_id}.{field}", token=b,
                        action="labeled_unverified",
                    ))
        new_scenes.append(sc.model_copy(update={"unverified_fields": uf}))

    new_caps = []
    for cap in plan.captions:
        bad = _unverified_numbers(cap.text, allowed)
        unv = bool(cap.unverified or bad)
        for b in bad:
            findings.append(PlanFactFinding(
                where=f"caption:{cap.scene_ref}.{cap.order}", token=b,
                action="labeled_unverified",
            ))
        new_caps.append(cap.model_copy(update={"unverified": unv}))

    for b in _unverified_numbers(plan.title, allowed):
        findings.append(PlanFactFinding(where="title", token=b, action="labeled_unverified"))

    sanitized = plan.model_copy(update={"scenes": new_scenes, "captions": new_caps})
    report = PlanValidationReport(
        plan_engine=plan.plan_engine, findings=findings, rejected=False,
    )
    return sanitized, report
