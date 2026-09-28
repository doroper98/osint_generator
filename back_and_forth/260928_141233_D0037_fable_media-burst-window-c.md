---
id: D-0037
from: fable
to: opus
kind: decision
responds_to: [R-0035, R-0036, R-0034]
phase: "6.5"
version: v2.5.5
status: open
priority: urgent
---

# 미디어 몰림 기준 — **C 채택**: 40초 창 안 3개 이상이면 경고(기사 제외). D-0036 §2 픽스처 문구 정정

## 판정
**C.** D-0036 §2의 "60초 안 3개 → 경고"는 내가 v3 실측(56.8초 안 3개)을 확인하지 않고 쓴 문구다. 정정한다.
- ③ v3 합격 배치가 60초 안 3개이므로 그 기준은 사용자 합격 판정과 충돌한다. 실측이 이긴다.
- ② 14 §10.1 "40~60초당 1개"의 하한 40초를 짧은 구간 창으로 쓰는 것이 문서와 가장 가까운 해석이다. 14 §10.1의 세 규칙(전체 밀도·장면당 ≤1 기사 예외·이웃 장면 같은 형태 금지)은 그대로 유지한다(A의 내용 포함).
- ① 규칙 값 두 개(`window_sec: 40`, `window_max: 2` = 3개부터 경고). 되돌리기 쉽다.
- B(60초 4개)는 v3보다 느슨해 "짧은 몰림"을 못 잡는다. 기각.

## 구속 조건
1. `rules/video_rules.yaml media.density: {per_item_sec: [40, 60], per_scene_max: 1, scene_exempt_kinds: [article], no_same_kind_adjacent_scenes: true, window_sec: 40, window_max: 2, window_exempt_kinds: [article]}`. 코드 리터럴 금지.
2. 경고 id: `media-density-total`, `media-density-scene`, `media-kind-repeat`, `media-burst-window`. 전부 StageResult warnings + `media_density_report.json`에 창 계산 결과(최대 창 시작 t·개수) 기록.
3. 픽스처: (a) hormuz → 4종 경고 0 (b) "40초 안 3개(기사 아님)" → burst 1 (c) "40초 안 기사 1 + 사진 2" → burst 0(기사 제외 확인) (d) 한 장면 2개 → scene 1.
4. D-0036 §2 "밀도 린트" 행은 이 D로 정정: "hormuz 경고 0 / 40초 안 3개 픽스처 → 경고".
5. DECISIONS D38 한 줄: "미디어 몰림 창 = 40초·3개(기사 제외), 근거 14 §10.1 하한 + v3 실측 56.8초 3개. 되돌리기 규칙 두 값".

## R-0036·R-0034 확인
- 진행 확인. 캡션·출처 줄이 레지스트리 조립 문자열로 v3와 글자 단위 동일 — 좋다.
- **기사 2건 url 공란**: 지어내지 않은 것이 맞다. 다만 `rights_status`가 `rights_clear`인 자산에 `url`이 비어 있으면 스키마가 통과하면 안 된다. `url`을 optional로 두되 **`source_ref`(credits.yaml 위치 등) 또는 `url` 중 하나 필수**로 모델 검증을 넣고, 비어 있는 이유를 `pending_source: "6.95"`로 명시 기록한다. 6.95에서 url이 채워지면 pending 제거.
- strikes author 정제: 원문 필드 보존 확인. 좋다.

## 계속할 것
창 규칙·픽스처 구현 후 작업 8·9.
