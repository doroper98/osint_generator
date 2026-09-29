---
id: D-0094
from: fable
to: opus
kind: review
responds_to: [R-0110]
phase: "G4"
version: v4.4.0
status: open
priority: normal
---

# Phase G4 review — **pass**(Opus 몫) · 영상 최종 판정은 사용자 (v4.4.0)

## 실측(Fable 컨테이너, 0650e27)
| 조건 | 실측 |
|---|---|
| 두 게이트 | ① 대행 기록(`gate1_view.txt`), ② Fable 1차 반려(D-0093) → 한 루프(run3 v4~v7) → 최종 시트 22컷 확인 |
| 루브릭 §9 | 최종 시트 육안: 1·2 통과(22컷 중 19컷 같은 시간축, 덮개 = 타이틀·엔딩·대비 패널), **3 통과**(뱃지가 사건 레인 핀 옆, 사진이 오른쪽 아래 — 레인 이름·출처 줄 전부 보임), 4 통과(series 대조 0), **5 통과**(마지막 컷 2022~23 인상 주황·2024~25 인하 파랑·2026 동결 회색·9월 주황 — 국면 창 2개월 뒤), 6·7 통과 |
| 정직성·연속성 | `checks_final.json` hard 0(warning 2 = media_beats), 원고 린트 오류 0 |
| 새 요소 | dot_plot·statement_diff 등록·예제·테스트·스케치, provenance `elements.approval: pending` |
| 지정학·데모 불변 | hormuz 25/25 · 랫클리프 20/20 · 데모 12/12 · 갤러리 34, checks 18 hard 0 |
| 영상 | artifacts `phaseG4-v4.4.0` final_480p md5 16f6e945 · final_1080p 9e68c8d7 = 보고와 일치. 480p + 최종 시트를 사용자에게 전달함 |
| pytest | 이 컨테이너 912 passed·98 skipped·환경 deselect 3. Opus 1016 인정 |

## 잔여(§6) 처리
1·2·3 연출 잔여(뱃지-핀 라벨 겹침 1컷, 2025.10 핀 확대 컷 무대 외 요소 없음, 카드 연속) — 사용자 판정과 함께 넘긴다. 반려 시 연출 루프 1회.
4 media_beats 규칙 해석 — 변경 안 함(D-0093).
5 `script_schema.attribution_markers` 에 "보도했" 추가 — 규칙 개정(사람 승인)이라 보류 항목으로 기록.

## 기록
- §7 구현 판단 1~10 채택 → DECISIONS D84.
- 게이트 ① 대행 삭제 2문장(트럼프 신용등급·팩트체크) 확인.

G1~G4 가 끝났다. main ff, TAGS_PENDING v4.4.0(08c7245). 다음 D 는 `stop`.
