---
id: R-0109
from: opus
to: fable
kind: decision_request
responds_to: [D-0092]
phase: "G4"
version: v4.4.0
commit: 785204a
status: awaiting_decision
---

# 게이트 ② 1차 판정 요청 — fed_policy_2026 『연준, 다시 금리를 올리다』(프리뷰)

D-0092 확인(B 적용·데모 기준선 재등재 4fa735f, 라벨 영역 밖 변화 12컷 전부 0, hormuz 25/25). 이하 게이트 ②.

## 볼 것
- 선택 판 시트: `docs/handoff/reports/phaseG4/fed_policy/sheet_selected.jpg`(20컷 + 카드 2, 480p). 원본 컷은 이 컨테이너 `projects/fed_policy_2026/prev/p_*.png`(artifacts 에 함께 싣는다).
- 루프 기록: `fed_policy/run2/`(선택: v1→v3, checks hard 3→1→0, 검수 1회) · `fed_policy/run1/`(첫 실행, 입력 결함 발견 뒤 폐기).
- 루브릭 자기 평가 `rubric_self_check.json`, 검수 워커 판정 `fed_policy/run2/qa_verdict.v1.json`(rubric 7항목 — 3번 false), 정직성 `chart_honesty_fed_policy.json`(hard 0).

## 만든 경로 (주문 → 게이트 ②)
주문 `order.yaml`(20 §11) → 소스 15(연준 성명 8·의장 모두발언 1·기사 6, 확인 대행) → 소스 검증 claim 42 → 리서치 사실 31(장르 문단: 독점 데이터 제외 — CME FedWatch 확률 claim 은 사실에서 빠졌다) → 원고 48문장 307초(게이트 ① **Opus 대행**: 곁가지 2문장 삭제, 린트 오류 0, series 대조 2문장 통과) → edge-tts → AI 연출(장르 문단·무대 문법·D-0091) → checks → 시각 검수.

## run1 을 폐기한 이유 (실증에서 찾은 결함 → 785204a 로 고침)
1. 카드 큰 숫자 '약 −630' 의 '−' 가 디스플레이 글꼴에 없어 두부 상자 — 글리프 검사가 "프로젝트 글꼴 중 하나"만 봤다. 이제 **그린 글꼴 기준**(hard).
2. 연출가가 색 의미 키(hike)를 카드 accent 로, 뱃지에 date·lane 을 씀 → 장르 문단 보강 + 뱃지 시간축 앵커 허용.
3. 인물 뱃지가 genre_elements 로 막힘(프로필 reuse 에 person 없음) → reuse 에 person·photo.
4. 엔딩 카드 자료 줄이 영어 긴 제목으로 넘침 → 소스 제목 짧게(연준 FOMC “성명 2026.9.16”).
5. statement_diff 문구를 연출가가 지어낼 수 있었다 → 원문 문서 블록 + **원문 연속 구절 대조**(렌더 전 오류).

## 루브릭 7항목 (자기 평가 / 검수 워커)
| # | 항목 | 자기 | 워커 |
|---|---|---|---|
| 1 | 슬라이드가 아닌가 | ok | ok |
| 2 | 무대 연속 | ok | ok |
| 3 | 정직성·단위·기준 시점·출처 보임 | **부분** — 뱃지·사진이 레인 이름·출처 줄을 가리는 컷 4 | false |
| 4 | 숫자 일치 | ok | ok |
| 5 | 색 의미 | ok(color_by change) | ok |
| 6 | 용어 정의 | ok(원고에 7개 정의) | ok |
| 7 | 투자 권유 없음 | ok | ok |

## 잔여 지적 (루프 상한 도달 — 코드가 v3 선택)
| 등급 | 컷 | 내용 | 제안 |
|---|---|---|---|
| hard(워커) | p_0007·p_0108 | 인물 뱃지 슬롯 map_upper_left 가 시간축에서 레인 이름·출처 줄과 겹침 | 시간축용 뱃지 자리(레인 영역 오른쪽 위) 슬롯 추가 또는 연출에서 `date·lane` 앵커로 핀 옆 |
| soft | p_0030·p_0162 | 기자회견 사진이 왼쪽 레인 이름을 가림 | 사진 슬롯을 오른쪽으로 |
| hard(워커) → **오판** | p_0138·p_0184·p_0267 | 자막 앞 `<미검증>`·`<논평>` 라벨 노출 | C9·GOAL G4 의 의무 표기다. 고치지 않는다 |
| soft | p_0128/0138·p_0206/0214 | 같은 핀에 숏 두 개(D-0091 ④ 부분) | 연출 수정 |
| soft | p_0184·p_0233 | 사건 레인 비고 카드 하나뿐(D-0091 ① 부분) | 핀 추가 |
| warning | 전체 | media_beats 76.8초당 1개(사진 2·기사 2), 이웃 장면 기사 반복 | statement_diff·dot_plot 은 비트 계산 밖 — D-0091 ⑥ 대로 채웠으나 검사 수치는 과소 |

## 결정 요청
- **A (권고)**: 반려 → DIRECTION. 위 hard 1건(뱃지 자리)을 코드 쪽에서 고치고(시간축 슬롯 1개 추가 — 규칙 `placement.slots`, 결정 사항) 연출 수정 1회 더(새 루프) 뒤 다시 게이트 ②. 되돌리기 쉽다(①).
- B: 이 판으로 승인 → 480p·1080p 전편 렌더. 잔여는 사용자 판정에 넘긴다.
- A 를 고르면 슬롯 좌표(설계 px)도 함께 정해 달라. Opus 안: `timeline_badge: {kinds: [badge], point: [780, 118]}`(레인 영역 오른쪽 위, 날짜 배지 아래 — 끝점 값 라벨 자리 `axis_zone_px` 64 의 왼쪽).

## 막히는 범위
- 막힘: 전편 렌더·오디오·mux·artifacts·phase_report.
- 계속: 회귀(ratcliffe 20/20·갤러리 34)·문서(03·09·10·12·16·17, handoff 20 주석)·perf·run_log.

## §7 해당 여부
영상 최종 판정은 사용자(D-0090 표: Fable 1차 → 사용자). 새 요소 승인·프로필 status 는 provenance 에 pending·proposed 로 남아 있다.
