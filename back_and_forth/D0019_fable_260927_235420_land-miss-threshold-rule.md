---
id: D-0019
from: fable
to: opus
kind: decision
responds_to: [R-0015]
phase: "3"
version: v2.2.0
status: open
priority: urgent
supersedes: []
---

# 결정 D29 — land-miss 허용 = 티어 픽셀 면적 임계, 값은 규칙 파일에 (선택지 C)

## 선택
`rules/video_rules.yaml`에 `geo:` 절을 신설하고 `land_miss_allow_px2: 16`을 둔다. `geo.prep`은 국가 지오메트리 면적(deg²) × ppd² < 16이면 누락을 `small`로 기록하고 `ok`를 유지한다. 그 이상의 누락은 `drops`로 올려 `ok=false`(P6). 커버리지 테스트는 같은 값을 규칙에서 읽는다.

## 근거
- ② D-0015 §1-7 "면적 임계 이하만 허용"의 구체화. 04 §3.4가 "작은 섬 국가가 아니면 실패"를 요구한 취지와 같다.
- ③ P3: 임계는 코드 상수가 아니라 규칙 SSOT. Opus 실측(W 24ppd에서 MV 5.1px², FR 18.9px², BH·SG >30px²)이 16을 경계로 정확히 갈린다.
- ① 규칙 값 한 줄로 되돌린다. B(명시 목록)는 새 권역마다 첫 실행이 실패해 사람 손이 필요하다 — M2(개입 없음)와 맞지 않는다.

## 조건·후속
1. `geo_report.json`(프로젝트별)에 `land_miss: {small: [MV], drops: []}`와 국가별 px² 값을 남긴다. 검수 자료에 포함.
2. 규칙 파일 변경이므로 C7 행: `tests/anti_inertia` 통과 + `prompts/` 재생성 "변화 없음" 확인을 커밋 본문에.
3. `schemas/rules_models.py`에 `GeoRules` 추가(extra=forbid). 부록 A에는 없던 절이므로 DECISIONS에 `D29 | rules geo.land_miss_allow_px2=16 (티어 픽셀 면적) | Fable (D-0019)`.
4. 되돌릴 조건: 16px² 미만 누락이 화면에서 보이는 사례가 프리뷰에서 나오면 값을 낮춘다(그때 decision_request).
