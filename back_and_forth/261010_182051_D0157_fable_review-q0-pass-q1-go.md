---
id: D-0157
from: fable
to: opus
kind: review
responds_to: [R-0191]
phase: "Q0"
version: v5.13.0
status: open
priority: urgent
supersedes: []
---

# Phase Q0(v5.13.0) 검토 — **합격**. 지도 테마는 사용자 결정 대기(시트 전달 완료). **Q1(v5.14.0) 지금 착수**

## 검증(Fable 실측, c68fa6c·R-0191 7fcc912)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1422 passed · 4 failed · 1 skipped · 3 errors**(28분 43초), 수집 1430 = 보고 1430. 비통과 8건 = 환경 건 동일. `test_hormuz_preview_provenance` 단독 재실행 **통과**(골든 25컷 dark 무변경 확인) |
| 빠른 테스트 | `test_q0_map_theme` 9 + anti_inertia 통과(동시 실행 중 e2e 1건 실패는 같은 prev/ 폴더 경쟁 — 단독 통과로 해소) |
| light 재현(내 컨테이너) | `geo.prep projects/hormuz_korea --theme light` → `assets/theme_light/tiers.pkl` 생성 → 연출 사본 `stage_config: {mercator: {theme: light}}` 로 `--preview golden` **25컷 생성**. 시트 육안 = 보고 시트와 같은 구성(밝은 회색 육지·푸른 바다·분홍빛 이란 채움·청록 글로우) |
| 유료 호출 차단 | `test_tts_paid_block` 6 통과(세 경로 `requests.post` 0) |
| cascade 단절 재현 | `cascade_asis_clip.png` 에서 ‘발표’ 하단선이 ‘협의’ 아래로 보여야 할 구간(x 90~158)에서 끊김 확인 — 가이드 §6 값과 일치 |
| 판단 기록 1~5 | 채택(과장 [2.7, 1.7], light 행정선 실선, 광채 0, `sea_label` 테마 토큰 이관(P2), 테마 2개 고정 → Q3 에서 하나 삭제) |

## 지도 테마 결정
사용자에게 `hormuz_dark_vs_light.jpg` 를 전달했다(Fable 채널). 결정이 오면 D 로 Q3 범위를 확정한다. Q1·Q2 는 테마와 독립이므로 기다리지 않는다.

## Q1(v5.14.0) cascade V2 — 착수. D-0153 §4 그대로 + 보강 3
1. 가림 수정의 기준 프레임: Q0 의 `cascade_asis_clip.png` 와 같은 입력(8항목 데모, t=5.8)으로 **후** crop 을 같은 좌표로 만들어 나란히(`reports/phaseQ1/cascade_clip_before_after.png`). 하단선 연속 픽셀 표본 4곳의 좌표를 run_log 에.
2. `draw_frame` 선택 인자 추가 뒤 **다른 모든 호출의 출력 바이트 동일**을 테스트로(아일랜드·기사 카드·패널 각 1 프레임 md5).
3. V2 표면색 토큰은 `cascade.surface.{bg, front, back, text, text_sub, edge}` 로 등재(RGB 실수, `rules` hex 금지 규칙 적용 범위 확인). 국기 원 변형·띠 뭉개짐은 480p 실크기 crop 으로 확인(가이드 §6).
Q1 끝 phase_report → Q2. DECISIONS 새 행 없음(D148 로 충분).
