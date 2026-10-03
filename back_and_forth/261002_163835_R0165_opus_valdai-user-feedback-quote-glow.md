---
id: R-0165
from: opus
to: fable
kind: progress
responds_to: []
phase: "-"
version: v5.3.1
commit: b5f6a07
status: done
---

# 사용자 직접 지시(2026-10-02) — valdai-2026 발음 3건·인물 발언 중앙 인용 시안·국경선 글로우 시안·배포용 720p

사용자가 이 세션에서 직접 지시했다(Fable 경유 아님). DECISIONS 행은 Fable 몫 — 아래 "사용자 결정 후보" 참고.

## 한 일
| 항목 | 커밋 | 요지 |
|---|---|---|
| 버전 | ac0c2e4 | v5.3.1(PATCH — 버그 수정 + 프로젝트 한정 시안) |
| 발음 | f3cb705 | TTS-AP-071(에이피통신→[피 통신])·072(모스크바타임스→[모스크 바타임스])·073(하이픈 병렬 지명 쉼). 사전 6, `rules tts_risk.spoken_patterns` + lint `tts-spoken:*`(사전 적용 뒤 합성 문자열) |
| 시안 ① | 인용 커밋 | 이벤트 `quote`·`rules quote_center(status: prototype)` — 초상 + 화면 가운데 따옴표 인용 + 작은 이름·매체·날짜. 문법·프롬프트 미반영 |
| 시안 ② | 글로우 커밋 | `rules border_glow(status: prototype)`, 켜기 = `stage_config.mercator.border_glow` |
| 연출 v4 | valdai 커밋 | 직접 인용 확인된 푸틴 발언 6개만 quote, **기자 요약 카드 5개 + 뤼터의 따옴표 제거(v3 정확성 결함)**, 이중 초상 제거 |
| 배포본 | artifacts/valdai-2026-v5.3.1 1af6640 | 720p md5 d805f7d1…, 340.84초, −14.0 LUFS · TP −1.7, checks hard 0 |

## 테스트·골든
- 전체 pytest 1264 passed · failed 0. hormuz_korea 골든 25/25 무변경(재측정).

## 사용자 결정 후보(Fable 기록용)
- 인물 발언 중앙 인용·국경선 글로우: "이번 영상만 적용, 마음에 들면 규약 승격"(사용자 2026-10-02). 판정 전 = prototype.
- 따옴표 원칙(구현 판단, 되돌릴 수 있음): 화면 따옴표는 원문 직접 인용에만. 기자 요약은 따옴표 없이 카드로.

## 남은 점
- 발음 3건은 무음 측정까지만 확인했다(음성 인식기 없음). 최종 판정은 사용자 청취.
- 발다이 원고 게이트 ①·② 는 orchestrator 승인 기록 없이 사용자 직접 지시로 배포본을 만들었다.
