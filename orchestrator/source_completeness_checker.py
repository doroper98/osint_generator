"""원고 출처 완결성 — claim id 없는 주장 문장이 있으면 SCRIPT_APPROVAL 전에 차단 (v3.2.0, docs/handoff/18 §7, D-0051 작업 8, D52).

옛 역할(SourceRegistry → '부족 자료 식별' 보고서)은 D52 로 삭제됐다. 지금은 원고(script.yaml)와 `intake/claims.json` 을
대조해 게이트 ① 진입을 막는 오류만 낸다. 판정은 `script.lint` 와 같은 함수(한 규칙, 두 곳 — 15 P8):
- source-unknown: 문장 sources 가 claims.json 밖 id (claims.json 이 없으면 sources 가 있는 문장 전부)
- source-missing(오류): 숫자·날짜가 있는 문장인데 sources 가 비었다
- v5.5.0 script_grammar: disputed-claim(논쟁 주장 무귀속)·uncertain-phrase(내레이터의 미확인 결론)·flow-sparse(연결어 부족)
"""

from __future__ import annotations

from pathlib import Path

import yaml

from script.lint import lint, load_claims_for
from script.schema import Script

BLOCKING = ("source-unknown", "source-missing", "disputed-claim", "uncertain-phrase", "flow-sparse")   # v5.5.0 — 서술 규약도 승인 전에(음성 단계에서 늦게 막히지 않게)


def check_script_sources(pdir: Path) -> list[str]:
    """차단 사유 목록(빈 목록 = 통과). 원고가 없거나 깨졌으면 그 자체가 사유."""
    sp = pdir / "script.yaml"
    if not sp.exists():
        return [f"원고 없음: {sp.name}"]
    try:
        script = Script.model_validate(yaml.safe_load(sp.read_text(encoding="utf-8")))
    except (ValueError, yaml.YAMLError) as ex:
        return [f"원고 검증 실패: {ex}"]
    rep = lint(script, load_claims_for(pdir))
    return [i.line() for i in rep.errors if i.kind in BLOCKING]


__all__ = ["BLOCKING", "check_script_sources"]
