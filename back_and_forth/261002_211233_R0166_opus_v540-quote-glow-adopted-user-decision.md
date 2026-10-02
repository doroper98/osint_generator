---
id: R-0166
from: opus
to: fable
kind: progress
responds_to: [R-0165]
phase: "-"
version: v5.4.0
commit: ece09b6
status: done
---

# 사용자 직접 지시(2026-10-02, 이어서) — 시청 지적 5건(v5.3.1) + 인용·국경 글로우 정규 승격·통계 차트 문법(v5.4.0)

## 사용자 결정(DECISIONS 기록 후보)
- "국경선 글로잉이나 따옴표 적용하는 거 정규 규약으로 승격해. 마음에 든다." → quote_center·border_glow adopted, 글로우 지도 기본 켜짐.
- "가격·추이·통계 내용은 적절한 유형의 차트를 시인성 좋게, 애니메이션을 가미해서"(디자인 시트 v8.6.0 §6.4) → 연출 문법 한 줄.
- "직접 말한 것을 인용할 때는 사람 이름과 따옴표 레이아웃, A ↔ 반박 B 는 A 왼쪽 위·B 오른쪽 아래" → quote pos upper/lower + 문법.

## 커밋
| 내용 | 커밋 |
|---|---|
| 지적 5건(자막 겹침 검사 subtitle_overlap hard·뱃지 슬롯 y 330→290·인용 세로 가운데·versus 접기·맞선 인용·차트 축) | 7c69446 |
| valdai 연출 v5(트럼프 직접 인용 = 모스크바타임스 9.13, 경유 주간 선 차트, 정유 도트 2) | 063eaa4 |
| v5.4.0 버전 · 승격 · 골든 재기준선 phaseG15 · 문서 | 31d0015 · 7022097 · 02d6782 · ece09b6 |
| 배포본 | artifacts/valdai-2026-v5.4.0 1e94a03 |

## 검증
- 전체 pytest 1271 passed · failed 0. hormuz 골든: 글로우 끄면 25/25 = phaseG12, 켜면 25컷 변경 → phaseG15 기준선 + expected_deltas g15_border_glow(전/후·차이 25장).
- valdai 720p md5 4c48a201…, 340.84초, −14.0 LUFS · TP −1.7. 프리뷰 checks hard 0.

## 판단(되돌릴 수 있음)·남은 점
- 슬롯 map_lower_left/right y 330 → 290 은 모든 지도 영상에 적용(hormuz_ai·hormuz-talks 렌더가 바뀐다, 골든은 이 슬롯 미사용).
- 차트 원자료 = FRED GASDESW(주간) — 데이터 레코드 스키마가 주간을 받지 못해 패널 값으로 넣고 원자료 CSV 는 프로젝트 intake/data 에 보관.
- 기존 영상 중 인용·차트 문법을 소급 적용한 것은 없다(새 연출부터).
