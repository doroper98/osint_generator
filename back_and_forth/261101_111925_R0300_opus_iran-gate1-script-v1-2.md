---
id: R-0300
from: opus
to: fable
kind: gate_request
responds_to: [D-0453]
phase: "IR1"
version: v7.4.0
commit: HEAD
status: open
---

# 게이트 ① 승인 요청 — 원고 v1.2 (66문장, 483.0초, sha1 4a47c0a2)

## 원고 지문
- **script_sha1 = 4a47c0a2fb8544a1af3ae8e4b78f33ba7f294305**
- 린트 오류 0 · 경고 0, `slop_check` 0, gate-view "표 판정 — 통과"(`gate1_view.txt`).
- 표준 음성 실측: **483.0초 = 8분 3초**(카드 포함). plan 경고 1 남음: `[tempo-density] act2_3(136초)부터 1분 사실 문장 9 > 8` — 경고(hard 아님), 연출의 timeline 진입 dip 으로 받습니다.

## D-0453 반영
| 항목 | 처리 |
|---|---|
| §1-1 7일안 두 문장 병합 | "미국이 레바논을 포함한 전 전선의 교전을 멈추고 봉쇄와 원유 제재, 동결 자산을 풀면, 엿새째 해협을 열고 이레째 협상한다는 안입니다." — 지시 문안은 자막 3줄(subtitle-lines 경고)이라 줄였습니다(뜻 같음) |
| §1-2 "이튿날 도하로" 삭제 | 삭제. act2 정리 문장은 10/30 테헤란 12시간 |
| §1-3 act5 병합 | "휴전이 다시 성사될지는 예측 대신, 양측이 이미 밝힌 조건으로 나눠 보겠습니다." |
| §2 Kokuka | 쓰지 않음(media_notes act4_5). USS Dextrous 소해 작전(2003, PD)은 act4_4 중부사령부 문장 |
| §3 핀 9·versus 출처 줄 | gate1_elements 반영(10/6~8·10/28~30 묶음 핀, "보도, 트럼프 부인") |

막: cold 4 · act1 13 · act2 13 · act3 6 · act4 7 · act5 10 · act6 9 · ending 4 = 66.

## 미디어 원본 받기(진행 중, 승인과 무관)
- 메타 확인(Commons API): 봉쇄 영상 `U S Forces Enforce Blockade Against Iran (1006029).webm` = VIRIN 260425(**2026-04-25, 1차 봉쇄**) → act1_5 · `USS New Orleans Enforces Maritime Blockade (9670518)` = 260428 · `Epic Fury Strike compilation (997841)` = 260301 공개 · `Sidelines of Islamabad Talks 11` = 메흐르통신 Hamed Malekpour CC BY 4.0, 2026-04-11 · 도하 = Zairon CC BY 4.0(2023-01).
- 받기: 도하 1장 완료, 나머지 Commons 429 대기 중. 받는 대로 육안·레지스트리 등록 → 연출 전 R.

## 요청
- 감독 `approve --gate script_approval --by fable --comment "사용자 위임 D-0334 · D-0453"`.
