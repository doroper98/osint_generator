"""원고 린트 (v2.3.0, plan3 `BANNED, lint()`, 03 §2, back_and_forth D-0021 작업 2).

패턴·수치는 `rules/video_rules.yaml`에서 읽는다(15 P3). 금지 문구의 정본은 규칙 파일
`banned_phrases.patterns` 하나다 — `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-006 은 참조만 한다.

오류(하나라도 있으면 plan 실패):
- slop: AI 상투 문구(banned_phrases.patterns)
- tts-symbol: 발음 텍스트 안의 숫자·기호(tts_rules.forbidden_chars_regex, TTS-AP-021~025·058)
- emphasis-missing: 강조어가 자막에 없음(tts_rules.emphasis_must_be_substring)

경고(plan 은 진행, StageResult.warnings 로 보고):
- tts-risk: 발음 텍스트의 TTS-위험 표기(URL·파일명·버전·시각 콜론·날짜 점·화살표·범위·천단위 콤마·붙은 단위·
  슬래시·기호·로마자). 패턴은 `rules tts_risk`(v3.0.0, 옛 orchestrator/tts_lint 병합 — 16 §3, D-0040 작업 8)
- source-missing: `sources` 가 빈 문장(03 §3 "모든 수치에 출처"). **숫자·날짜가 있는 문장이면 오류**(v3.2.0 D-0051 작업 8 격상)
- attribution: unverified claim 을 인용하는데 자막에 귀속 표현(`script_schema.attribution_markers`)이 없음(18 §3-3)

오류(v3.2.0 추가):
- source-unknown: 문장 sources 가 `intake/claims.json` 밖 id(claims.json 이 없는 프로젝트면 sources 가 있는 문장 전부).
  v4.3.0 D-0088: `series:<id>` 는 데이터 레코드 참조 — 레코드 파일이 없을 때만 오류
- series-value-mismatch: series 참조 문장의 자막 N%·N%p 가 레코드 값과 다름·빈 달 값 언급·대조 불가(script/series_refs.py)
- subtitle-lines: 자막이 script_schema.subtitle_max_lines 줄을 넘음(렌더러와 같은 글꼴·폭으로 실측 wrap)

CLI (v3.0.0, 16 §4 `direction_validate` 의 6.9 전 대체 — D-0040 작업 4):
    python -m script.lint <proj>   → script.yaml 을 Script 로 로드 + 린트 + 검증 라벨 재계산·대조(D-0043),
                                     마지막 줄 StageResult JSON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

import cairo
from pydantic import BaseModel, ConfigDict

from rules import load_rules
from script.schema import Script

Severity = Literal["error", "warning"]
NUMERIC = re.compile(r"\d")   # 숫자·날짜가 있는 자막 문장


class LintIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    severity: Severity
    sid: str
    detail: str
    text: str

    def line(self) -> str:
        return f"[{self.kind}] {self.sid}: {self.detail} — {self.text}"


class LintReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[LintIssue]

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def subtitle_lines(text: str) -> int:
    """렌더러(engine/subtitles.draw_subtitle)와 같은 글꼴·크기·폭으로 wrap 한 줄 수."""
    from engine.style import SUBTITLE, SUBTITLE_WRAP_PX  # noqa: PLC0415 — 글꼴 로딩은 필요할 때만
    from engine.typography import wrap  # noqa: PLC0415

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    return len(wrap(cairo.Context(surf), text, SUBTITLE_WRAP_PX, SUBTITLE.size, "sansm"))


# ------------------------------------------------------------------ TTS-위험 표기 (옛 orchestrator/tts_lint)
def _risk_patterns() -> list[tuple[str, "re.Pattern[str]", str]]:
    return [(p.kind, re.compile(p.regex, re.IGNORECASE if p.ignore_case else 0), p.hint)
            for p in load_rules().tts_risk.patterns]


def tts_risks(text: str) -> list[tuple[str, str, str]]:
    """발음 텍스트에서 TTS-위험 표기 [(종류, 조각, 힌트)]. 같은 (종류, 조각)은 한 번,
    로마자는 더 구체적인 종류(covered_before_roman)가 덮은 구간이면 생략한다."""
    if not text:
        return []
    covered_kinds = set(load_rules().tts_risk.covered_before_roman)
    out: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    covered: list[tuple[int, int]] = []
    for kind, pattern, hint in _risk_patterns():
        for m in pattern.finditer(text):
            if kind == "roman_letters" and any(cs <= m.start() and m.end() <= ce for cs, ce in covered):
                continue
            key = (kind, m.group(0))
            if key in seen:
                continue
            seen.add(key)
            out.append((kind, m.group(0)[:60], hint))
            if kind in covered_kinds:
                covered.append(m.span())
    return out


def spoken_risks(spoken: str) -> list[tuple[str, str, str]]:
    """v5.3.0 TTS-AP-071~073 — 사전 적용 뒤 합성 문자열의 위험 표기 [(종류, 조각, 힌트)]. 패턴 = rules tts_risk.spoken_patterns."""
    out: list[tuple[str, str, str]] = []
    for p in load_rules().tts_risk.spoken_patterns:
        for m in re.finditer(p.regex, spoken, re.IGNORECASE if p.ignore_case else 0):
            if (p.kind, m.group(0)) not in {(k, s) for k, s, _ in out}:
                out.append((p.kind, m.group(0), p.hint))
    return out


# ------------------------------------------------------------------ 발음 변환 (옛 orchestrator/tts_pronounce, v0.34.10)
# 한자어 숫자 자동 변환 + JSON 음차 사전(경로 = rules pronounce.dict_path). 번들 어댑터(bundle/text)가 쓴다.
# 한 숫자의 음절은 붙여 쓴다(TTS-AP-058). 자막은 원본 유지 — 변환은 발음 텍스트만.
_ONES = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]


def _num_to_sino_under_1000(n: int) -> str:
    """1 ≤ n ≤ 999 를 한자어로. 단위는 '백십사' 처럼 단위어 우선 (자릿수 1 일 때
    `일백`/`일십` 생략).

    **한 숫자 안에서는 음절을 절대 띄우지 않는다** (TTS-AP-058) — 예전에는 prosody
    힌트라며 "백 육 십 팔" 로 띄웠으나, ElevenLabs 는 공백을 만나면 국어의 연음(자음
    동화)을 끊어 "백육십"[뱅뉵씹] 을 [배·규·씹] 으로 또박또박 읽고, 소수점 앞에서도
    반박자 쉰다. 붙여 써야 모델이 연음/운율을 자연히 적용한다."""
    if n == 0:
        return ""
    hundred, rest = divmod(n, 100)
    ten, one = divmod(rest, 10)
    parts: list[str] = []
    if hundred:
        parts.append("백" if hundred == 1 else f"{_ONES[hundred]}백")
    if ten:
        parts.append("십" if ten == 1 else f"{_ONES[ten]}십")
    if one:
        parts.append(_ONES[one])
    return "".join(parts)


def num_to_sino_kr(n: int) -> str:
    """0 ≤ n ≤ 99,999,999 를 한자어로. 99,999,999 이상은 그대로 반환(드물고
    OSINT 영상에선 만 단위 이상 거의 안 씀, 안전 폴백).

    한 숫자의 음절은 붙여서 반환 (TTS-AP-058) — 연음/운율 보존."""
    if n == 0:
        return "영"
    if n < 1000:
        return _num_to_sino_under_1000(n)
    if n < 10000:
        thousand, rest = divmod(n, 1000)
        head = "천" if thousand == 1 else f"{_ONES[thousand]}천"
        return f"{head}{_num_to_sino_under_1000(rest)}" if rest else head
    if n < 100_000_000:
        man, rest = divmod(n, 10000)
        head = f"{num_to_sino_kr(man)}만"
        return f"{head}{num_to_sino_kr(rest)}" if rest else head
    return str(n)


# 숫자 + 한글 (단위어가 바로 붙는 경우 = "80달러", "19일") 패턴. num_to_sino_kr 의 결과
# 뒤에 단위 한글이 붙으면 자연스럽게 공백 1 칸 삽입해 prosody 보정.
_NUM_THEN_HANGUL_RE = re.compile(r"(?<!\d)(\d{1,8})(?=[가-힣])")
_NUM_RE = re.compile(r"(?<!\d)(\d{1,8})(?!\d)")


def apply_dict(text: str, mapping: dict[str, str] | None = None) -> str:
    """사전 치환만(`_` 메타 제외) — apply_pronunciation 1) 단계와 합성 직전 명시 tts(`pronounce_tts`)가 같은 함수.
    v5.2.0(TTS-AP-069): 한 번 훑기 — 각 위치에서 가장 긴 key 하나만 치환하고, 치환된 글자는 다시 치환하지 않는다.
    그래서 긴 예외 항목(예: "브렌트유가" → "브렌트유가", 명사 + 조사 '가')이 짧은 항목("유가" → "유까", 油價)을 막는다."""
    keys = sorted((k for k in (mapping or {}) if not k.startswith("_") and k), key=len, reverse=True)
    if not keys:
        return text
    pat = re.compile("|".join(re.escape(k) for k in keys))
    return pat.sub(lambda m: (mapping or {})[m.group(0)], text)


def pronounce_tts(tts: str, mapping: dict[str, str] | None = None) -> str:
    """합성 직전 발음 사전(v5.1.0 back_and_forth D-0121 §D, TTS-AP-067·068 구조 조치) — 원고가 tts 를 명시해도 사전을 거친다.
    숫자 변환은 하지 않는다(명시 tts 는 이미 한글). 치환이 있었을 때만 공백을 정리한다(치환 없는 문장의 캐시 키 불변). 멱등."""
    out = apply_dict(tts, load_pronounce_dict() if mapping is None else mapping)
    return tts if out == tts else re.sub(r"\s+", " ", out).strip()


def apply_pronunciation(text: str, mapping: dict[str, str] | None = None) -> str:
    """텍스트를 narration 용 음차로 변환.

    1) `mapping` (사용자 사전) 의 key 가 text 에 있으면 value 로 치환 — 가장 우선.
    2) 남은 숫자(연속 1~8자리) 는 한자어로 자동 변환.
       2-1) 숫자 바로 뒤에 한글 단위어가 붙어있으면 (예: "80달러", "19일") 사이에
            공백 한 칸 삽입 — TTS 가 단위어 발음을 분리 적용하도록.

    단어 경계: mapping key 가 한국어이므로 `\b` 가 작동 안 함. 단순 substring 치환을
    긴 key 부터 적용해 부분 매칭 충돌 회피.
    """
    out = apply_dict(text, mapping)
    # 숫자 + 단위어 사이 공백 보정 → "팔십 달러", "십 구 일".
    out = _NUM_THEN_HANGUL_RE.sub(
        lambda m: num_to_sino_kr(int(m.group(1))) + " ", out
    )
    out = _NUM_RE.sub(lambda m: num_to_sino_kr(int(m.group(1))), out)
    return out


def pronounce_dict_path() -> Path:
    return Path(__file__).resolve().parent.parent / load_rules().pronounce.dict_path


def load_pronounce_dict(path: Path | None = None) -> dict[str, str]:
    """JSON 음차 사전. 없거나 깨지면 오류(v3.0.0 — 옛 빈 dict 조용한 폴백 제거, 15 P6). `_` 로 시작하는 키는 메타."""
    p = path or pronounce_dict_path()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: 발음 사전은 JSON 객체여야 한다")
    return {str(k): str(v) for k, v in raw.items() if isinstance(k, str) and not k.startswith("_")}


def load_claims_for(proj: Path) -> "dict | None":
    """프로젝트의 claims.json → {claim_id: status}. 없으면 None(그때 sources 가 있는 문장은 source-unknown 오류)."""
    from script.labels import CLAIMS_RELPATH, claim_statuses  # noqa: PLC0415

    p = proj / CLAIMS_RELPATH
    return claim_statuses(p) if p.exists() else None


def _series_exists(sid: str) -> bool:
    from data.series import series_dir  # noqa: PLC0415

    return (series_dir() / f"{sid}.yaml").exists()


def lint(script: Script, claims: "dict[str, str] | None" = None, *, check_sources: bool = True) -> LintReport:
    """claims = {claim_id: status}(claims.json). check_sources=False 는 출처 검사를 끈다 — 프롬프트 예시처럼
    claims.json 이 없는 원고 조각에만(파리티 테스트)."""
    r = load_rules()
    attrib = r.script_schema.attribution_markers
    banned = [re.compile(p) for p in r.banned_phrases.patterns]
    forbidden = re.compile(r.tts_rules.forbidden_chars_regex)
    max_lines = r.script_schema.subtitle_max_lines
    out: list[LintIssue] = []
    for sc in script.scenes:
        for k, s in enumerate(sc.sentences):
            sid = f"{sc.id}_{k}"

            def add(kind: str, sev: Severity, detail: str, text: str = s.text, sid: str = sid) -> None:
                out.append(LintIssue(kind=kind, severity=sev, sid=sid, detail=detail, text=text))

            for p in banned:
                if p.search(s.text):
                    add("slop", "error", p.pattern)
            say = s.tts or s.text
            hit = forbidden.search(say)
            if hit:
                add("tts-symbol", "error", repr(hit.group(0)), say)
            if r.tts_rules.emphasis_must_be_substring:
                for e in s.emphasis:
                    if e not in s.text:
                        add("emphasis-missing", "error", e)
            for kind, snippet, hint in tts_risks(say):
                add(f"tts-risk:{kind}", "warning", f"{snippet!r} → {hint}", say)
            spoken = pronounce_tts(say)   # v5.3.0 TTS-AP-071~073 — 사전 적용 뒤 실제 합성 문자열
            for kind, snippet, hint in spoken_risks(spoken):
                add(f"tts-spoken:{kind}", "warning", f"{snippet!r} → {hint}", spoken)
            if check_sources:
                if not s.sources:   # v3.2.0 — 숫자·날짜 문장은 오류(D-0029 §3 예고대로 격상), 그 밖은 경고
                    num = bool(NUMERIC.search(s.text))
                    add("source-missing", "error" if num else "warning", "sources 비어 있음" + (" (수치·날짜 문장)" if num else ""))
                from script.series_refs import check_series_sentence, is_series_ref, series_id  # noqa: PLC0415

                refs = [c for c in s.sources if is_series_ref(c)]   # v4.3.0 D-0088 — 데이터 레코드 참조(claim 아님)
                bad_refs = [c for c in refs if not _series_exists(series_id(c))]
                if bad_refs:
                    add("source-unknown", "error", f"데이터 레코드 없음 {bad_refs}(data/series)")
                elif refs:
                    for msg in check_series_sentence(s.text, s.date, refs):
                        add("series-value-mismatch", "error", msg)
                unknown = [c for c in s.sources if not is_series_ref(c) and (claims is None or c not in claims)]
                if unknown:
                    add("source-unknown", "error", f"claims.json 밖 id {unknown}" if claims is not None else
                        f"claims.json 이 없다 — sources {unknown} 를 확인할 수 없다(18 §3-6)")
                if claims is not None and any(claims.get(c) == "unverified" for c in s.sources) \
                        and not any(m in s.text for m in attrib):
                    add("attribution", "warning", "unverified claim 인용 — 귀속 표현(~라고 주장했습니다/보도했습니다, rules script_schema.attribution_markers) 없음")
            n = subtitle_lines(s.text)
            if n > max_lines:
                add("subtitle-lines", "warning", f"{n}줄 > {max_lines}")
    return LintReport(issues=out)


def main(argv: list[str] | None = None) -> int:
    import yaml  # noqa: PLC0415
    from pydantic import ValidationError  # noqa: PLC0415

    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="script.lint")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    path = args.proj.resolve() / "script.yaml"
    from script.labels import check_project_labels  # noqa: PLC0415

    try:
        script = Script.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        rep = lint(script, load_claims_for(path.parent))
        labels = check_project_labels(path.parent, script)   # 도시어가 있으면 라벨 재계산·대조(D-0043 §3)
        arts = {"script": str(path)}
        if labels is not None:
            arts["label_counts"] = json.dumps(labels.counts(), ensure_ascii=False)
        res = StageResult(ok=not rep.errors, stage="lint", artifacts=arts,
                          errors=[i.line() for i in rep.errors], warnings=[i.line() for i in rep.warnings])
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as ex:
        res = StageResult(ok=False, stage="lint", errors=[f"{path}: {ex}"])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
