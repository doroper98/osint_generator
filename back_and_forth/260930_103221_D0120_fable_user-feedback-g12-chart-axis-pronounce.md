---
id: D-0120
from: fable
to: opus
kind: directive
responds_to: []
phase: "G12"
version: v5.1.0
status: open
priority: normal
---

# 사용자 시청 피드백(v4.11.0 480p) → G12(v5.1.0) 예고 — 시간축 축 스케일 고정 + 발음 사전 합성 직전 적용

**착수 = G11(v5.0.0) 합격 뒤.** 지금은 읽기만. 전편 렌더 없음(사용자: "영상을 다시 만들 필요는 없고") — 프리뷰 시트·TTS 재합성 확인·pytest 로만.

## 사용자 피드백(2026-09-30, DECISIONS D105, handoff 01 기록)
1. **hormuz_korea: "100점 만점을 줄 수 있을 것 같다."** 유지.
2. **fed_policy_2026: 시간축 차트의 가로축 스케일이 계속 바뀌어 보기 불편.** 원인(Fable 실측, `direction.yaml` shots): 카메라 w(일)가 숏마다 60 → 500 → 120 → 200 → 260 → 40 → 400 → 40 → 150 → 2900 — 10번 재신축, 눈금 단위(일↔월↔년)까지 바뀐다.
3. 발음: "거부권" → [거부꿘], "연방공개시장위원회" → "연방공 개시장 위원회" 로 분절. Fable 이 사전(`assets/pronounce/pronounce_ko.json`)에 두 항목 추가 + TTS-AP-067·068 기록(커밋됨). **구조 결함**: 원고에 `tts` 가 명시되면 `bundle/to_script.py` 의 `given or tts_of(text)` 가 사전을 건너뛴다 — hormuz·fed 둘 다 tts 명시 원고라 사전만으로는 안 고쳐진다.

## 작업
### 1. 시간축 축 스케일 고정(연출 문법 + 검사, P8 — 코드가 연출을 정규화하지 않는다)
- 규칙 `stage_timeline.axis_scale`: `w_changes_per_video_max: 3`(오프닝 설정·중간 1회·엔딩 조망), `w_change_ratio_min: 1.5`(이 미만의 w 변화는 '흔들림' — 금지), `scene_fixed: true`(장면 안에서 w 변경 금지 — move 는 중심 이동(pan)만).
- checks `timeline_rescale` **hard**: 시간축 무대에서 (a) 장면 안 w 변경 (b) 영상 전체 w 변경 횟수 > max (c) 비율 < min 인 변경 → `[timeline-rescale] {at} w {a}→{b} ({이유})`. 지도 무대는 대상 아님. provenance `timeline.w_changes[]`.
- `rules direction_grammar` 한 줄 + 연출·수정 프롬프트(`{{RULES.stage_timeline.axis_scale}}`): "시간축 무대는 축 스케일을 장면 단위로 고정한다. 확대·축소는 영상당 3회 이하, 그 밖은 중심 이동(pan)만. 지도의 '문장마다 줌 금지'(G4-16)와 같은 원리."
- **fed_policy 연출 재작성은 LLM(revise_direction, W1.1 사람 루프 = Fable 검토)**: 현재 10회 → 3회 이하가 되도록 `reopen --to direction --reason "timeline-rescale"` 경로로 다시 받는다. 코드로 w 를 고치지 않는다. 결과 = 프리뷰 시트(`prev_g12/`)·checks hard 0·`[static-window]` 창 수(시간축은 지도 구간이 아니므로 0 이어야 함) 보고. 전편 렌더 없음.
- 골든(hormuz·랫클리프)은 지도 무대 → 무변경 확인. 데모(시간축)도 검사 통과해야 함 — 걸리면 데모 연출 재작성(같은 방식).
- 테스트 ≥ 5(장면 안 변경·횟수 초과·비율 미만·지도 무대 제외·프롬프트 규칙 값 삽입).

### 2. 발음 사전을 합성 직전에 항상 적용(TTS-AP-067·068 구조 조치)
- `script/plan.py` 합성 직전: 명시 `tts` 에도 `bundle.text.tts_of` 의 사전 치환(숫자 변환은 제외 — 명시 tts 는 이미 한글)을 적용. 캐시 키는 치환 뒤 텍스트로.
- `bundle/to_script.py` 의 `given or tts_of(text)` 는 그대로 두되, given 에도 사전을 거치게 한 곳으로 통일(중복 적용은 멱등이어야 함 — 테스트).
- 회귀 테스트: `tests/test_tts_pronounce.py` 에 "거부권"→"거부꿘", "연방공개시장위원회"→"연방 공개시장 위원회", 명시 tts 경로 적용, 멱등 — 4개.
- hormuz·fed 의 plan 재생성으로 해당 문장 캐시 키가 바뀌는 것(= 재합성 대상)을 보고에 적는다. 실제 재합성·전편 렌더는 하지 않는다.

### 3. 공통
- §0 VERSION 5.1.0(MINOR: 새 검사), 헤더, CHANGELOG. 한 커밋 한 의도. 문서: handoff 05(시간축 축 스케일)·03(사전 적용 시점), docs/12 검사 표, ANTIPATTERNS(상태 줄만 갱신 — 과거 항목 수정 금지), DEVLOG. pytest failed 0.
