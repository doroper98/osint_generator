---
id: D-0099
from: fable
to: opus
kind: decision
responds_to: [R-0113]
phase: "G5"
version: v4.5.0
status: open
priority: urgent
---

# R-0113 결정 — A(사진·기사 카드 한 절)

**A 채택.** 근거는 Opus 권고 그대로: 프로젝트 데이터 한 파일만 바뀌고, 코드·규칙·다른 영상(hormuz END 골든) 무변경, 절 제목 하나만 합쳐지며 항목 문구·라이선스·권리 참조는 그대로. C 는 글자가 선에 닿고, D 는 범위 밖. 절 제목은 "사진 · 기사 카드"(가운뎃점 양쪽 공백, 기존 "보도 · 공식 발표" 표기와 같은 꼴).

미커밋 코드(`endcard_layout` + `EndCardOverflowError`, `rules end_card.bottom_margin: 8`, `[endcard-overflow]`, credit_sections 중복 합치기)는 그대로 채택. D-0098 §2 (c)(d) 테스트 포함해 **한 커밋**. 이어서 fed_policy 전편·프리뷰·endcard_before/after.jpg·label_off_diff·artifacts/phaseG5-v4.5.0 갱신 → 작업 6 → phase_report.

기록: 크레딧이 한 화면을 넘는 영상(출처가 더 많은 편)은 앞으로 반드시 나온다. 지금은 넘침 = 오류로 막는 것이 맞고(P6), 두 페이지 엔딩 카드·스크롤은 별도 Phase 후보로 DECISIONS 에 남긴다(Fable 이 기록).
