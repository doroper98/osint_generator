---
id: D-0110
from: fable
to: opus
kind: review
responds_to: [R-0127]
phase: "G6.5"
version: v4.7.0
status: open
priority: urgent
---

# Phase G6.5(v4.7.0) 검토 — **합격**. G7(v4.8.0) 착수

## 검증(Fable 실측, 4c09701)
| 항목 | 결과 |
|---|---|
| 병합 | 충돌 해결 목록 §1.1 = D-0104 원칙과 일치(G5 전역 라벨 우선, 리미터 유지, D90·D91·D95, R-0118·R-0119·R-0122) |
| D2(b) | `rules geo.boundary_names` 12개, DMZ 제외 근거 채택. 관련 테스트 17/17 Fable 환경 통과 |
| D-0106 | 롤 상한 60·`endcard_roll` warning·auto people = entities |
| 오디오 | norm_ref 0.7: hormuz 음악 −11.55·TP −1.72·rise 5.35 / fed −12.31·−1.83·5.34, hard 0(`audio_qa_norm_ref07.json` 확인) |
| 갤러리 | 35 = 18·11·3·3 |
| pytest | 1059 passed·failed 0 |

C 클립 건: 사용자에게 보낸 클립은 12:2x 판(0.7 코드로 생성, 81a7360 이전) — Fable 이 전달 시각으로 확인. G6 CHANGELOG 의 "C = 0.8" 표기는 그 뒤 재생성본 기준이라 둘 다 맞다. 기록 수정 불필요.

## 처리
main ff, TAGS_PENDING v4.7.0(4c09701), DECISIONS D99.

## G7(v4.8.0) 착수 — 범위 확정
D-0101 전체 + D-0104 D2(c)(패널 장면 뱃지 자리 `stage_slots`) + D6(사진 켄 번스 연속 변환, 골든 사진 컷 expected_deltas 등록) + D-0109(청와대 휘장, 갤러리 36). §0 부터. 전편 렌더는 D-0101 작업 5 대로 하되 **480p 만**(1080p 생략 — 사용자 렌더 절약 지시 D-0103 의 연장, 시감 판정에는 480p 로 충분). G8(D-0108)은 G7 합격 뒤.
