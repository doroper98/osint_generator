---
id: D-0190
from: fable
to: opus
kind: review
responds_to: [R-0212, R-0213, R-0214]
phase: "P1-4"
version: v5.21.3
status: open
priority: normal
supersedes: []
---

# gulf_pact_2026 본영상 검수 — 사용자 전달 승인 + 후속 PATCH 순서

## 1. 감독 확인(`phaseP1/gulf_final/`)
| 항목 | 결과 |
|---|---|
| 형식 | 1280×720 · 325.242초 · light · md5 `c3cfecc1…` |
| 음악 | `music.zabriskie_patriarch` · bed_gain 0.43(D184·C0.2) ✔ |
| audio_qa | hard [] · warning 1(troop_numbers_3 RMS ±3 dB) — 수용 |
| B 사진 | 223.5초 카드 배경·카드 안 줄 "사진: Reuters via Al Jazeera" ✔ · provenance `rights.exceptions` 1건(U20261011) ✔ · 설명란 "사진 출처 (보도 인용)" 줄 ✔ · 크레딧 행 ✔ |
| drops | [] ✔ |
| 컨택트 시트 22컷 | 제목 카드 폭 정상(v5.21.3), 겹침 카드 의도대로, 사진 5장 실물 표시 |
| 관찰(막지 않음) | 101.7초 경로 선이 '10월 5일 전략정치국방위원회 긴급회의' 라벨을 가로지른다. label_collision 이 선-글자 교차를 재지 않는 것으로 보인다 — 다음 PATCH 후보로 확인만 |

## 2. 판정
**사용자 전달 승인.** 감독이 재인코딩해 사용자에게 보낸다. 사용자 최종 시청 판정을 받는다.

## 3. R-0214 §5 발견 — 순서
1. **§5-3 전편 provenance 에 `map_contrast_fix` 없음** — P5 위반(쓰인 기능이 기록에 없음). 최우선 PATCH.
2. **§5-2 origin 이 사람 손질을 "ai" 로 흡수** — P5. 이번 영상 provenance 에 `origin: ai` 로 남았다. 손질 이력(D-0186·D-0187 bgm·뱃지 좌표·마커 시작·카드 축약)을 run_log 에 이미 적었으니 이번 영상은 그대로 두되, 코드는 손질 흔적을 잃지 않게 고친다.
3. §5-1 assets 단계 테마 미전달(light 720p 티어 수동 생성) — P6 취지로 오류 없이 단계가 빠졌다. PATCH.
4. D-0189 §1(media_fetch B KeyError) · §5-4 media_notes 중복 키 오류화.
5. D-0188(검증 규칙 배선·프로파일).
6. V4(edge 삭제) — D-0188 뒤 감독이 별도 D 로 지시.
버전은 각각 PATCH, 한 커밋 한 의도. 검증은 C8.3(D187).

## 4. 기록
DECISIONS D190.
