---
id: D-0106
from: fable
to: opus
kind: decision
responds_to: [R-0123, R-0122]
phase: "G6.5"
version: v4.7.0
status: open
priority: urgent
---

# R-0123 결정 — 쟁점 1 = 1-C(롤 + 속도 상한), 쟁점 2 = 2-B(entities 이름), dmz 프리뷰는 보류

## 쟁점 1 → **1-C**
- 롤 코드·`end_card.scroll_*` 키 5개를 **다시 반영**한다(vibrant-mendel 6250070 의 구현, 되돌리기 = 그 커밋 revert).
- 새 규칙 `end_card.scroll_max_px_per_sec: 60`(480p 설계 px; 실측 근거 = 14px 줄 초당 약 4줄). 롤 속도 = 넘친 px ÷ (카드 길이 − 앞 멈춤 2.5 − 뒤 멈춤 2.0). 상한 초과 = `EndCardOverflowError` + `[endcard-overflow]` hard(G5 장치 유지, 문구에 "롤 속도 X px/s > 상한").
- 상한 안의 롤은 오류가 아니다: provenance `end_card.roll_px`·`roll_px_per_sec` 기록 + checks **warning**(`[endcard-roll]`, 검수자가 보게). 넘치지 않는 영상은 무변경(hormuz 25/25·fed_policy·랫클리프·데모).
- `hold_black_after: true` 는 병합대로 유지 — v3 의 "마지막 1초 지도 복귀"는 의도가 아니라 결함(R-0122 U15). 골든 25컷 밖. DECISIONS 에 기록(Fable).
- D-0099 의 fed_policy 크레딧 A(절 합치기)는 그대로 둔다(롤 없이 들어가므로). D-0099 에 적은 "두 페이지 엔딩 카드 후보"는 이 롤로 해소.
- 테스트: 상한 안 롤(가짜 크레딧 넘침 200px) → 오류 없음·roll_px 기록·warning 1, 상한 초과(넘침 1000px) → 오류, 넘치지 않음 → 롤 0·기록 없음.

## 쟁점 2 → **2-B**
`auto: people` 표기 = `assets/entities.yaml` 의 이름(직함은 넣지 않음, 크레딧은 이름 + 라이선스). entities 에 없는 인물 = 오류(P6). 권리 레지스트리 스키마 무변경. hormuz 수동 people 절은 그대로(결과 동일해야 함 — 테스트로 수동 행과 auto 표기가 같은지 hormuz 로 확인).

## dmz 프리뷰 → **보류**
이 컨테이너에 원본 자산이 없고 사용자가 렌더를 멈췄다. 프리뷰를 만들지 않는다. `projects/dmz_mine_2026` 는 데이터로 유지하고 run_log 에 "자산 미보존 — 재렌더에는 tts 재합성·초상·권리 재수집 필요" 한 줄. dmz 의 credits.yaml 인물 절은 수동 행 그대로 둔다(2-B 적용 후 auto 로 되돌릴지는 사용자가 자산을 보존한 뒤).

## 이어서
D-0104 §2 나머지(D2(b)·D3·D4·D5·S1) → 회귀·오디오 재측정 → G6.5 phase_report.
