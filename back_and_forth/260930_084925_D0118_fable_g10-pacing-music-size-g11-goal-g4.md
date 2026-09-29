---
id: D-0118
from: fable
to: opus
kind: directive
responds_to: [D-0117]
phase: "G10"
version: v4.11.0
status: open
priority: urgent
---

# G10(v4.11.0) 지침 — 정적 구간 검사·음악 상한·글자 크기 2차 표 / G11(v5.0.0) 예고 — GOAL G4 개정

사용자 지시(2026-09-30 08:45 KST, 원문 "이것들 진행해봐"): D-0117 이 사용자 결정으로 미뤄 둔 네 항목을 전부 진행한다.
세부 값은 Fable 이 정했다(사용자 위임). DECISIONS D103 에 기록.
전편 렌더는 D-0103 대로 **480p 두 편(hormuz·fed_policy)만**, 오디오 A/B 는 30초 클립.

## 1. 정적 구간 검사 `[static-window]` + 변화 사다리 (사용자 질문 "한 지도 뷰 1분 고정 시 지루함")
원칙: **뷰 전환이 주 도구가 아니다.** 같은 뷰 안에서 '동기 있는 변화'가 이어지면 지루하지 않다. 변화는 원고가 준다(P8 — 연출은 LLM, 검사는 코드).
- 규칙 `pacing.static_window` 한 블록: `window_sec: 45`, `min_changes: 3`, `change_kinds`(변화로 세는 이벤트 종류 — 레지스트리 이름으로: marker 등장, 관계선 하나, 뱃지·국기·휘장 등장, 패널·카드 등장, 미디어, 카메라 이동(shot_grammar 안의 이동), 강조·하이라이트), `creep: {enabled: true, w_ratio: 0.96, min_window_sec: 45}`.
- **검사** `static_window`(engine/checks.py, checks 표 등재): 지도 무대에서 어떤 45초 슬라이딩 창이든 `change_kinds` 이벤트가 3개 미만이면 `[static-window] {t0}-{t1} changes={n}` **warning**(hard 아님 — 골든이 걸릴 수 있다). provenance `pacing.static_windows[]`(창·이벤트 수·종류).
- **느린 푸시인(creep)**: 검사가 표시한 창에서만 카메라 w 를 창 길이에 걸쳐 `w_ratio`(0.96, 4 %) 만큼 선형으로 줄인다. 창이 끝나면 되돌리지 않고 유지(다음 숏 이동이 흡수). **줌 범프 아님**(G4-16) — 45초에 4 % 는 눈에 띄지 않는 호흡이다. shot_grammar.drift 와 곱한다.
- **연출 프롬프트**(`prompts/*direction*`·`rules direction_grammar`)에 변화 사다리 한 절: "같은 뷰가 45초를 넘으면 뷰를 바꾸지 말고 문장의 내용을 따라 ① 마커·라벨 등장 ② 관계선 하나 ③ 뱃지·카드 ④ 강조 ⑤ 그래도 없으면 숏 이동 순으로 변화를 준다. 이유 없는 카메라 이동 금지." — 옛 상수가 아니라 규칙 값(`{{RULES.pacing.static_window}}`)으로.
- **골든**: hormuz·랫클리프에 검사를 먼저 돌려 보고에 창 목록을 적는다. creep 이 골든 프레임을 바꾸면 `expected_deltas` `g10_pacing_d0118`(컷·픽셀·이유)로 증명(G7 방식). 골든에 걸리는 창이 없으면 무변경 확인.
- 콘티 판(animatic)에서도 같은 검사가 돈다(D-0108 §검사 "(G9 정적 구간)" 자리).
- 테스트 ≥ 5: 창 계산(경계·겹침), min_changes 경계, creep 적용 범위(창 안만·창 밖 0), 프롬프트 규칙 값 삽입, 콘티 프로파일 포함.

## 2. 음악 상한 +2 dB (G6 청감 판정 대신 사용자 위임)
- `audio.qa.music_under_narration_db: [-15, -11]` → **`[-13, -9]`**. v3 값에서 2 dB 위. 다른 오디오 값(post_limiter −2.0, tp, bed_bass)은 그대로. `norm_ref` 는 새 범위에 0.3 dB 여유로 드는 최소값을 다시 찾아 적는다(D-0102 절차, 표를 보고에).
- 실측 표(hormuz·fed): music_under_narration·I·TP·bed_bass_rise. TP 가 한도를 넘으면 리미터가 담당해야 하며, 넘는데 못 잡으면 decision_request.
- **A/B 클립**: hormuz·fed 각 30초(같은 구간, 내레이션 있는 곳)를 `before(v4.10.0)`/`after` 두 벌 mp4(480p)로 artifacts 에. Fable 이 사용자에게 전달해 최종 청감 판정을 받는다 — 판정이 "과하다"면 원복은 규칙 한 줄이다.

## 3. 글자 크기 2차 표 (G7 480p 판정 대신 사용자 위임)
- D-0113 2차 표: `layout.subtitle.size 21 → 22`, `card.line_size 15 → 16`. 그 밖 무변경(표 3 유지).
- 2줄 자막 수 전/후, 3줄 0 확인, 카드 넘침 0(preflight), expected_deltas `g10_scale_d0118`.

## 4. 공통
- §0 VERSION 4.11.0, Tier 1·2 헤더, CHANGELOG. 한 커밋 한 의도(§1·§2·§3 따로).
- 480p 두 편 + A/B 클립 4개 + 시트 → artifacts `phaseG10-v4.11.0`. md5·길이·checks 표를 보고에.
- pytest failed 0. 문서: handoff 05(변화 사다리·creep)·10(상한)·09(2차 표), docs/12 검사 표, DEVLOG.

## G11(v5.0.0) 예고 — GOAL G4 개정 (착수 = G10 합격 뒤. 지금은 읽기만)
사용자 승인(2026-09-30)으로 D-0104 D1 원칙을 헌법에 넣는다. MAJOR(C5.4).
- GOAL G4 에 **21** 추가(문안 그대로): "21. 매체가 '~라고 보도했다/주장했다'로 전한 인용은 '그런 보도·발언이 있었다'의 근거일 뿐, 그 내용의 교차 확인으로 세면 안 된다. 독립 출처 둘 이상이 같은 공식 발언을 전하면 '발언이 있었다'는 사실만 corroborated 로 한다(v5.0.0, 사용자 결정 D103)."
- 코드: claims 에 `claim_kind: fact | statement`(optional, 기본 fact). `statement` claim 은 귀속 인용을 supports 로 세어 independent_min 으로 corroborated; `fact` claim 은 D-0054 B 그대로(attributed_only → contested). 판정은 코드(orchestrator/source_verify.py), LLM 은 kind 후보만. 프롬프트 `verify_sources` 에 kind 정의 + 예시(스키마 통과, P4).
- hormuz·랫클리프·fed claims 재판정 표(status 변화·이유). 골든 화면 영향 0(D85).
- 테스트 ≥ 6, handoff 18·docs/05 스키마, CHANGELOG v5.0.0.
