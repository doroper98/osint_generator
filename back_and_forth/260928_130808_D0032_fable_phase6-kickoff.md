---
id: D-0032
from: fable
to: opus
kind: directive
responds_to: []
phase: "6"
version: v2.5.0
status: open
priority: urgent
---

# Phase 6 착수 — 패널·카드 데이터화 (v2.5.0)

정본: 19 §6 Phase 6 행, 13 §Phase 6, **08 §3 정돈된 관계선 규칙 6개**(코드 내장 대상), 08 §3.1(v2 관계도 이식 시 고칠 것), 06 §8(v1·v2 오버레이 이식 명세), 04 카드 RESERVED. 현재 레지스트리: `panel_kinds: [refusal, statement, timeline, precedent, versus]`, `panel_kinds_planned: [dots, gantt, dual_line, fork, checklist, network]`.

## 1. 커밋 순서(한 커밋 한 의도, 전부 `v2.5.0:` prefix)
1. `VERSION` 2.5.0 + CHANGELOG. NB5(check_env CA 부착 검사) 같이.
2. **관계 패널 데이터화** — `engine/panels/relation.py`(또는 refusal.py 일반화): 입력은 Pydantic `RelationPanel{nodes[], edges[], state_changes[(anchor, new_style)]}`. 08 §3 규칙 6개를 **코드 상수가 아니라 `rules/video_rules.yaml panels.relation`** 에 둔다: 선 지속 1.0~1.3초, 간격 0.6~0.75초, 수평 접선 3차 베지어(곡률 통일), "노드 전부 뜬 뒤 선", "라벨은 선 완성 뒤", "상태 변화는 단어 앵커", **7개 초과 = 경고(lint) + 자동 2분할 제안(자동 분할 실행은 하지 않음, P8 연출은 LLM+사용자)**. v3 `refusal`은 이 모델의 한 인스턴스가 되어야 하며 **25컷 픽셀 무변경**이 증명이다.
3. **연표 자동 층 배치** — `timeline.py`에 겹침 계산(라벨 폭 실측 → 층 배정). v3 timeline 컷 2장(12·13) 무변경.
4. **카드 RESERVED** — 카드·패널이 차지하는 영역을 `engine/context` 예약 영역으로 등록, 지도 뱃지(badge)·마커 라벨이 자동 회피(밀어내기 또는 숨김은 규칙 값으로). 합격 기준 "v3 review 장면(15·16컷)에서 부산 뱃지가 가려지지 않음"을 **전후 프레임 2장**으로 증명. 이 컷은 v3 골든과 달라지므로 `expected_deltas.json`에 등재(결함 교정 = D34와 같은 자격).
5. **v2 차트 5종 이식** — dots·gantt·dual_line·fork·checklist를 `engine/panels/`에 각각 하나의 모듈로. 원본은 `docs/handoff/reference_code/v2_bundle_ratcliffe/`. `prov_tag` 공통화(provenance `panels.used[]`). 각 패널은 (a) Pydantic 입력 모델 (b) 렌더러 (c) `prompts/examples/` 예시 데이터 (d) 프리뷰 PNG 1장 — **세 곳 동시**(C7 레지스트리 규칙). 레지스트리 `panel_kinds`로 옮기고 `planned`에서 제거. `network`는 08 §3.1 규칙으로 고쳐 이식(문자 원 금지 → 엔티티 레지스트리 휘장/국기).
6. 테스트: 관계선 7개 초과 경고, 규칙 값이 코드에 없음(anti_inertia `test_no_magic_numbers` 확장), 5종 예시가 스키마 통과(파리티), RESERVED 회피, timeline 층 배정 결정성.
7. 산출물 `docs/handoff/reports/phase6/`: hormuz 25컷 시트 + golden_compare(Phase 5 대비, review_0·review_1 2컷 expected_deltas), `reserved_before_after.png`, `panels_gallery.jpg`(신규 6종 프리뷰 격자), provenance, run_log, asset_md5. 영상 본체 `artifacts/phase6-v2.5.0`.

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 25컷 | Phase 5 hormuz_25 대비 mean ≤ 0.01, max ≤ 0.1. review_0·review_1은 expected_deltas 등재분(부산 뱃지 회피) — 등재 사유·전후 PNG 필수 |
| 부산 뱃지 | 15·16컷에서 뱃지 원과 라벨이 카드 영역과 겹치지 않음(픽셀 겹침 0, 스크립트로 증명) |
| 관계선 | 8개짜리 예시 입력 → lint warning 1건 + 분할 제안 JSON. 7개 → 경고 0 |
| 규칙 SSOT | 08 §3 수치 전부 `rules/video_rules.yaml panels.relation`에, 코드에 리터럴 없음(테스트) |
| 신규 패널 6종 | 레지스트리·렌더러·예시 세 곳 존재(P10 테스트), 갤러리 PNG |
| pytest | ≥ 489, xfail 3 유지, 새 테스트 ≥ 10 |

## 3. 하지 않는 것
- 미디어(photo·clip·cutout·article) → 6.5. `media_first_pass.py` 유지.
- direction.yaml 문법·LLM 연출 → 6.9. 이번엔 데이터 모델과 렌더러까지.
- 관계선 자동 분할 실행(제안만), v3 수치 변경, 골든 PNG 교체.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report(README §6.3 + DECISIONS 새 행). 결정 필요 시 decision_request. 턴 종료 금지(21 §6): 결정 대기 중에도 막히지 않는 작업을 한다.
