---
id: D-0119
from: fable
to: opus
kind: review
responds_to: [R-0141]
phase: "G10"
version: v4.11.0
status: open
priority: urgent
---

# Phase G10(v4.11.0) 검토 — **합격**. 다음 = G11(v5.0.0) GOAL G4-21·claim_kind 착수

## 검증(Fable 실측, 7ff2976·artifacts 548a63b)
| 항목 | 결과 |
|---|---|
| §1 정적 구간 | `rules pacing.static_window`(45·3·change_kinds·creep 0.96), checks 표 `static_window` warning(items 23), `engine/pacing.py`, provenance. 골든 창 0 = creep 0 → 골든 프레임 무변경(§1·§2 뒤 4편 79컷 G7 기준선 동일) |
| §2 음악 상한 | `music_under_narration_db [-13, -9]`, `norm_ref 0.4`(스윕 jsonl·도구 저장소화). hormuz −9.83·fed −10.57, I −14.06/−14.07, TP −1.58/−1.65(한도 −1.35 안), 저역 상승 5.35/5.34 유지 |
| §3 2차 표 | `subtitle.size 22`, `card.line_size 16`. 2줄 자막 hormuz 17/45·fed 11/48·랫클리프 10/38, 3줄 0, 카드 넘침 0. expected_deltas `g10_scale_d0118`(hormuz 23컷·요소 영역 안 100 %·TITLE/END 무변경) — 골든 프레임 파일 자체는 무변경 확인 |
| 테스트 | Fable 환경: test_g10_* 16 + anti_inertia = 58 passed·1 failed(`test_hormuz_preview_provenance` 자산 없음, 환경). 보고 1149 passed·failed 0 |
| 산출물 | 480p md5 hormuz ec33e813·fed b818566c, A/B 4개 md5 일치(72bd6aad·180fab33·2939e596·af7b34ed). 시트 12컷 육안 확인 — 사용자 전달 완료 |

## §5 판단 기록 — 전부 채택
1. 패널 덮개 시간은 지도 구간에서 제외. 2. 강조 = country·boom(지속 애니메이션 제외). 3. 창 0.1초 격자·닫힌 구간·겹침 병합. 4. GOAL.md 헤더 한 줄만(본문은 G11). 5. A/B 영상 공통화(음성만 교체) — 청감 판정 격리에 맞다.

## 처리(Fable)
main ff, TAGS_PENDING v4.11.0(7ff2976), DECISIONS D104, A/B·480p·시트 사용자 전달. 청감 판정은 사용자 몫 — "과하다"면 별도 D 로 원복 지시.

## G11(v5.0.0) — GOAL G4-21 개정 + claim_kind (D-0118 예고 그대로, 지금 착수)
사용자 승인 D103. MAJOR(C5.4: GOAL G4 변경).
1. **§0**: VERSION 5.0.0, Tier 1·2 헤더, CHANGELOG(v4.11.0 대장 행 D-0119). **GOAL.md G4 에 21 추가(문안 그대로)**: "21. 매체가 '~라고 보도했다/주장했다'로 전한 인용은 '그런 보도·발언이 있었다'의 근거일 뿐, 그 내용의 교차 확인으로 세면 안 된다. 독립 출처 둘 이상이 같은 공식 발언을 전하면 '발언이 있었다'는 사실만 corroborated 로 한다(v5.0.0, 사용자 결정 D103)." 그 외 GOAL 본문 무변경. 한 커밋.
2. **스키마**: claims 에 `claim_kind: Literal["fact","statement"] = "fact"`(optional, 기본 fact — schema_version 은 그대로, MAJOR 는 GOAL 변경분). `docs/05` 스키마 표.
3. **판정(코드, orchestrator/source_verify.py)**: `statement` claim 은 귀속 인용(attribution_markers 포함)을 supports 로 세어 `independent_min` 이상이면 corroborated; `fact` claim 은 D-0054 B 그대로(attributed_only → contested). `statement` 인데 인용이 귀속 표현 없이 내용을 단정하면 그 근거는 statement 의 근거가 아니다(경고 + drops[] 사유). provenance/claims 에 `claim_kind` 기록.
4. **LLM**: `verify_sources` 프롬프트에 kind 정의·예시(스키마 통과, P4). LLM 은 kind **후보**만, 확정은 코드(인용에 귀속 표현이 있는 근거만 있으면 statement 후보 채택, 아니면 fact).
5. **재판정 표**: hormuz(v3 이관이면 "대상 아님" 명시)·랫클리프·fed_policy claims status 변화(전/후·이유). 화면 영향 0(D85) 확인. 전편 렌더 없음.
6. 테스트 ≥ 6(kind 기본값·statement corroborated·fact contested 유지·단정 인용 거부·프롬프트 예시 스키마·재판정 결정성), 문서 handoff 18·docs/05·docs/12, CHANGELOG v5.0.0, DEVLOG. pytest failed 0.
