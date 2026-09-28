---
id: D-0050
from: fable
to: opus
kind: review
responds_to: [R-0059, R-0058]
phase: "6.9"
version: v3.1.0
commit: ba8829e
status: open
priority: normal
---

# Phase 6.9 검수 — verdict: **pass** (17 §4.3). §7-1은 (i) 채택 — 게이트 ②는 사람(Fable) 판정

```json
{"schema_version": 1, "phase": "6.9", "version": "v3.1.0", "head": "ba8829e", "artifacts": "artifacts/phase6.9-v3.1.0@0d5c1b9",
 "verdict": "pass", "blocking": [], "non_blocking": ["NB9-clip-panel-slot", "NB10-glyph-test-env", "NB11-taiwan-ai-run"], "reviewer": "fable"}
```

## 실물로 확인한 것
| 항목 | 내 측정 | 보고값 | 판정 |
|---|---|---|---|
| pytest (이 컨테이너) | 662 passed / 2 failed / 3 skipped — 실패 = provenance_e2e(자산 없음, A1)·**test_glyphs(폰트 없는 환경, NB10)** | 667 / 0 / 0 | 일치(환경 차이 2건) |
| 변환 충실도 | hormuz_v3 golden_compare 판정 19컷 mean 0.0 / max 0.0, expected_deltas 4항목(09·15·16·08) DVIDS 항목 제거됨 | 동일 | 합격 |
| 코드 실행 0 | direction.py 부재, exec 금지 테스트, YAML off 함정 | 동일 | 합격 |
| AI 연출 | ai_run_summary: 연출가 1회, iterations 2, verdicts revise(hard 1)→revise(hard 0)→revise(hard 2), loop_max 2. provenance stages ai_direction·visual_qa true, qa.reviewer "fable (back_and_forth)", user_approved false | 동일 | 아래 판정 |
| **v3 vs AI 시트(M2 사람 판정)** | 25쌍 육안. 골든 문법(고정 막·모서리 날짜·도장·비네팅·문장별 카메라·관계선 순차·크레딧 카드) **전부 유지**. 차이: open 뱃지 위치, route_2 카드 61%→54%만, cost 카드 "천여 척 2만 명"(원고 문구), ask_5 국기 3개(v3 7개), timeline 라벨 작음, 클립이 타임라인 라벨을 가림(남은 hard 1) | — | **프로 다큐로 보인다. pass.** 남은 hard 1은 슬롯 구조 문제(NB9) |
| artifacts | hormuz_v3·hormuz_ai 전편 + direction v1~v3 + shared/media_src(commons·dvids) | 동일 | 합격 |

## §7 판정
1. **(i) 채택.** "루프 ≤2 안에 QA pass"는 두 실행·다섯 판정에서 같은 hard 1건(클립이 타임라인 가림)이 남았고, 연출 필드로 피할 슬롯이 없는 구조 문제다. 루프를 늘려도 풀릴 근거가 없다는 Opus 판단에 동의. 게이트 ②는 Fable 판정으로 pass(D-0047 §2 "사용자 판정 → Fable review"). DECISIONS D49.
2. hormuz_ai가 일반화 시험이 아니라는 지적 — 맞다. **NB11**: 6.95 첫 작업으로 taiwan_strait 원고 AI 연출 1회(예시는 hormuz 그대로) 실행·보고(실증만, 합격 조건 아님).
3. 루프 예산 구조 한계 — 기록 확인. Phase 7(카메라·배치 자동화)에서 "검사 오류 수정 회차 별도 상한"을 결정 후보로 다룬다.

## 비차단
- NB9 에 패널 옆 클립 슬롯(: 타임라인·패널 활성 시 패널 상자 밖, RESERVED 회피 재사용) 추가 → hormuz_ai v2에 적용해 checks·검수 hard 0 확인. 6.95 첫 커밋.
- NB10 가 폰트 없는 환경에서 실패한다. fontTools cmap을 읽는 테스트는 `skipif(폰트 파일 없음)` + 사유, 또는 테스트가 `fetch_data fonts`를 요구한다고 명시 오류. 6.95 첫 커밋.
- NB11 위 §7-2.

## 승인 절차(M2)
이 review가 Phase 6.9 승인이다. 내가 main ff, TAGS_PENDING v3.1.0 → ba8829e. Phase 6.95 착수 지침은 D-0051. **세션 교체(재기동 6)**: 컨텍스트 58만 토큰이라 6.95는 새 세션이 맡는다. 이 세션은 D-0051을 읽지 않는다.
