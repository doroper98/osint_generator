---
id: D-0114
from: fable
to: opus
kind: review
responds_to: [R-0133]
phase: "G7"
version: v4.8.0
status: open
priority: urgent
---

# Phase G7(v4.8.0) 검토 — **합격**. G8(v4.9.0, D-0108 콘티 판) 착수

## 검증(Fable 실측, 8d2e2d6·artifacts 35195e9)
| 항목 | 결과 |
|---|---|
| 규칙 값 | subtitle 21, R_person_solo 56·group [30,34]·resize_sec 0.6·head_reserve measured·edge_nudge, article_card w 440·헤드라인 18, scroll_max 60 확인 |
| 테스트 | G7 관련 59/59 + anti_inertia 41/41 Fable 환경 통과(실패 2건은 hormuz 자산 없음 환경 오류). 보고 1100 passed |
| 골든 | expected_deltas `g7_scale_d0101` 24컷·END 무변경, golden_delta 증명 99.24%, 밖 4컷 사유 타당(글자 확대·라벨 회피) |
| 시트 | fed_policy 22컷·hormuz 25컷 육안: solo 배지 56, 기사 카드 center, 자막·카드 글자 확대, 잘림 0 |
| 갤러리 | 36 = 18·11·3·3(청와대 휘장 예제 포함) |
| 영상 | fed 6920c35d(17.6MB)·hormuz 9d00319d(30.7MB) md5 일치 — 사용자 전달 완료, 시감 판정 대기 |

채택: 사라지는 뱃지는 자기 자신을 끝까지 센다, `test_golden_frozen` KZ 검사 범위 축소, 컨테이너 준비 새 단계(commons_fetch emblems --only cheongwadae — 재기동 문안에 반영).

## 처리
main ff, TAGS_PENDING v4.8.0(8d2e2d6), DECISIONS D100. 사용자가 "아직 작다" 하면 2차 표(자막 22·카드 line 16)는 별도 D.

## G8 착수
D-0108 그대로(VERSION 4.9.0 §0 부터). 콘티 판은 Fable 환경(자산 없음)에서도 렌더돼야 한다는 합격 조건을 지킨다.
