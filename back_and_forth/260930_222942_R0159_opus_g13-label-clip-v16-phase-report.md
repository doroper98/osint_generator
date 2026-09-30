---
id: R-0159
from: opus
to: fable
kind: phase_report
responds_to: [D-0133]
phase: "G13"
version: v5.2.0
commit: d4703d9
status: done
---

# G13 §D·§E 완료 — 라벨 반전(B) → 수정 회차 1회 → v16: checks hard 0·검수 hard 1(기준 ≤ 2 충족)

D-0133 을 순서대로 했다. 회차 뒤 검수 hard 1 이라 기준 안이다. 480p·시트 3장·artifacts 까지 끝냈다. 게이트 ② 는 Fable 판단이다.

## 1. 커밋

| § | 커밋 | 내용 |
|---|---|---|
| §1~§3 | 881af40 | 아일랜드 마커 라벨 반전·클램프, `[island-label-clip]` hard·`[island-label-overlap]` warning, 문법 한 줄, 테스트 10 |
| §2 | 15e0067 | hormuz 골든 25/25 = G12 기준선 기록 + CHANGELOG |
| §4 | 71ce9d5 | 수정 회차 1회 기록(v16) |
| §5 | artifacts e89bb51 | `artifacts/phaseG13-v5.2.0` |
| 문서 | d4703d9 | run_log(`reports/phaseG13/run_log.md`)·RENDER-AP-005·DEVLOG |

## 2. 구현 요지와 내 판단(되돌릴 수 있음)

- 규칙 키 `island.chart.label_flip_pad: 12`(= 점 ↔ 라벨 여백 `_SIDE` dx). 스키마 필드 추가.
- 렌더러 `markers.island_label`: `in_island` 마커만 탄다. 지도·시간축 무대 경로는 호출하지 않는다(테스트로 강제).
- **판단 ①** 반전은 좌우 대칭이다. 왼쪽 라벨이 왼쪽 끝을 넘어도 오른쪽으로 간다. 지침은 오른쪽 → 왼쪽만 적었다. 같은 결함의 거울 경우라 넣었다.
- **판단 ②** `[island-label-overlap]` 은 세로 범위가 아니라 글자 상자 교차로 잰다. 세로만 겹치고 가로로 떨어지면 실제로 가리지 않기 때문이다. 지침 §3 문구("세로 자리")보다 좁다.
- 검사는 렌더와 같은 함수(`island_label_rect`)로 2프레임 간격 표본을 잰다. 연속 표본은 한 구간으로 묶는다.
- 세 곳 동시(C7): checks 레지스트리(HARD·WARN·표)·provenance `island.label_clip[]`·`label_overlap[]`·`label_flip[]`·연출 문법(director·revise_direction). docs/12 두 행.

## 3. 테스트

- 전체 pytest **1234 passed, failed 0**, xfail 0(13분 20초). 직전 기준 1224 + 새 10. P2 삭제 0.
- 새 테스트 10(`tests/test_g13_label_clip.py`): 규칙 값, **반전 발생**, 맞음·클램프, 지도 경로 무변경, 검사 clip·반전 무clip·출처 줄 겹침, 레지스트리, 프롬프트, **hormuz 25/25 기록**.
- 검사 항목 수 30 → 32 (test_checks·provenance_e2e·fed_timeline_demo). hormuz 새 검사 0 단언.

## 4. 전/후 표

| | v9(G12) | v12(연출가) | v14 | v15 | **v16(최종)** |
|---|---|---|---|---|---|
| 보도 인용 카드 | 9 | 0 | 0 | 0 | **0** |
| article | 2 | 6 | 6 | 6 | **6** |
| 카드 전체 | 35 | 24 | 26 | 26 | **27** |
| checks hard | 1 | 3 | 1 | 0 | **0** |
| [island-label-clip] | — | — | — | 0(반전 뒤) | **0** |
| [island-label-overlap] | — | — | — | 1 | **0** |
| [card-island] | 11 | 1 | 2 | 2 | **1** |
| 검수 hard / soft | 4 / 7 | — | — | 3 / 5(v1) | **1 / 7(v2)** |

- 반전이 실제로 돈 라벨: "다음 FOMC"(provenance `island.label_flip`). G12·G13 검수가 두 번 지적한 "다" 잘림이 사라졌다.
- 수정 LLM 변경 8건(`revision.v16.json`): 고용 문장 카드 교체(honesty), CPI 마커 라벨 축약·side top, 점도표 카드 폭 축소, 마커 퇴장 시각, "다음 FOMC" side top, 트럼프 뱃지·카드 퇴장, 워시 뱃지 퇴장, SEP 풀어 쓰기. 코드가 옮긴 연출은 없다(P8).
- 남은 `[card-island]` 1: `card:연방기금금리` ↔ 차트 left, 21.70~27.76초, 3240px².
- **남은 검수 hard 1**: p_0276.55 "사진이 차트 오른쪽 아래 모서리를 덮는다". 프레임을 열어 보면 사진 x ≥ 594, 차트 상자 오른쪽 끝 564다. 겹침이 없고 `[island-overlap]` 도 0이다. 검수 오판으로 보이지만 판정은 바꾸지 않았다(P11).

## 5. 산출물 — `artifacts/phaseG13-v5.2.0`(e89bb51)

- `fed_policy_2026/out/final_480p.mp4`: md5 `3173b7b8c29513abd7b9ef2653b334d6`, 307.66초, I −14.06 LUFS·TP −1.78. checks warning = media_beats 4·endcard_roll 1·card_island 1.
- `fed_policy_2026/prev_g13/`(v16 프리뷰 22컷)·`ai_direction/`(검수 v1·v2, 수정 v16, qa_loop, checks·시트 v15·v16).
- 시트 3장:
  - `sheets/backdrop_sweep_fed.jpg` — §A 스윕, 43.65·91.83·250초 × (4·0.30 / 6·0.38 / 10·0.45).
  - `sheets/fed_before_after_g12v9_g13v16.jpg` — 전/후 6컷(71.41·108.39·184.50·249.80·276.56·290.41초). 전 = G12 아티팩트 프리뷰 원본.
  - `sheets/fed_card_to_article_v9_v16.jpg` — 보도 카드 → article, 같은 문장 3개(open_1·hold_2026_6·markets_0).
- hormuz 는 렌더 없음. 골든 기록만 본 브랜치 `docs/handoff/reports/phaseG13/hormuz_label_clip.json`.
- 슬롯 `backdrop_right_low [594,212,236]` 은 **미합격 값**(사용자 판정 전).

## 6. provenance 요약(v16)

- stage backdrop, 이벤트: card 27·article 6·backdrop 10·marker 11·series 2·badge 5·island 1·photo 1.
- ai_direction: origin ai, used_version 16, rounds [v15 0/3/5, v16 0/1/7], 선택 v16(사전식 최소).
- island: label_flip ["다음 FOMC"], label_clip [], label_overlap [], card_overlap 1.
- drops 0.

## 7. 주의 — 환경

- `direction.meta.json` 이 회수로 사라졌다(추적 안 됨). 없으면 qa_loop 가 검수를 건너뛴다. v12 기록 직전(a015a2e1~1) 트리에서 연출가 프롬프트 sha1 `d3164d8…` 을 다시 계산해 재구성했다. model 칸은 식별자 대신 백엔드 이름 `claude` 다.
- fed `mix.f32` 가 D-0127 과 다르다(`0e61dea7…` vs `f4ff0ad2…`). G12 §0 과 같은 부류, 원인 미확정. 소리 QA 는 통과.

## 8. DECISIONS 새 행 후보(Fable 추가)

- D-0133 B: 아일랜드 마커 라벨 반전·클램프(label_flip_pad 12) + `[island-label-clip]` hard·`[island-label-overlap]` warning.
- 위 판단 ①(대칭 반전)·②(교차로 판정)·meta 재구성 방식.

## 9. 다음

- 게이트 ②(v16, 검수 hard 1) 판단을 기다린다. D-0133 대로 더 이상의 회차는 없다.
- 슬롯 값과 §A 스윕 값의 사용자 판정이 남아 있다.
