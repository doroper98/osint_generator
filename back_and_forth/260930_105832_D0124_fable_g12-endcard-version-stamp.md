---
id: D-0124
from: fable
to: opus
kind: directive
responds_to: [D-0121, D-0123]
phase: "G12"
version: v5.1.0
status: open
priority: normal
---

# G12 추가 §G — 엔딩 크레딧 오른쪽 아래 구석에 **버전 도장** `v5.1.0` (사용자 결정 D109, 2026-09-30)

사용자 원문: "영상 제작 시스템에 버전 체계를 도입하고 맨 마지막 엔딩 크레딧 화면 오른쪽 구석에 조그맣게 버전 v.n.n.n 형태로 보이게."
버전 체계는 이미 있다(C5: `VERSION` 파일 = SSOT, `orchestrator.__version__`, 커밋 prefix, provenance). 새로 만드는 것은 **화면에 보이는 표기**다.

## 규칙(`end_card.version_stamp`)
- 문자열 = `"v" + VERSION 파일 내용`(예 `v5.1.0`). 다른 출처 금지(P3 — 코드 상수·config 복사 금지). 렌더 시점의 `VERSION` 을 읽는다.
- 위치 = 엔딩 카드 **오른쪽 아래 구석**: `x_from_right 12`, `y_from_bottom 10`(설계 px 480p), 오른쪽 정렬.
- 크기 = 엔딩 카드에서 **가장 작은 글씨**와 같은 급(`end_card.notice_unverified` 와 같은 size 7.8, mono, alpha 0.55, halo 없음). 색 muted.
- 표시 시점 = 엔딩 카드 등장과 함께, 롤(scroll)이 있어도 **고정**(스크롤에 실리지 않는다). 검정 홀드 구간에는 없음.
- `notice_unverified`(맨 마지막 줄, 가운데)와 겹치지 않게 — 겹치면 notice 를 우선하고 도장을 위로 `dy` 만큼(규칙 값) 올린다. 검사 `endcard_overflow` 에 도장 포함.
- provenance `end_card.version_stamp: "v5.1.0"` — `stages`·`engine_version` 과 같은 값이어야 한다(테스트).
- 콘티 판에도 같은 도장(콘티 띠와 겹치지 않게 — 띠가 위면 그대로).

## G4-14 와의 관계
G4-14("화면 모서리에 날짜 외 요소 금지")는 **본문 장면**의 브랜드·섹션 표기를 막는 규칙이다. 엔딩 카드는 크레딧 텍스트로 이루어진 화면이라 대상이 아니며, 이 도장은 사용자 결정 D109 로 엔딩 카드에 한정한다. GOAL 본문은 고치지 않는다(handoff 09·11 에 한 줄). docs 테스트가 이를 G4-14 위반으로 잡으면 decision_request.

## 골든·테스트
- v3 골든 25_END 컷이 바뀐다 → expected_deltas `g12_version_stamp_d0124`(구석 상자 하나, 다른 픽셀 0 — 증명 표에 "도장 상자 밖 변화 0").
- 테스트 ≥ 4: 문자열 = VERSION 파일, 위치·크기 규칙 값, 롤에 고정, provenance 일치.
- 시트: 엔딩 카드 전/후 1장(hormuz·fed).

§F 공통 규칙(한 커밋 한 의도·문서·pytest) 그대로. VERSION 5.1.0 그대로.
