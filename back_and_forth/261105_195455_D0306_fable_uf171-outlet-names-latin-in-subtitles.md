---
id: D-0306
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-171 / D528 — 화면의 매체 명칭을 라틴 표기로(NBC·CBS·AP). 발음 텍스트는 그대로. **전편 렌더 중단 → 반영 → 재시작**

## 0. 사용자 원문(2026-11-05 19:40 KST)
> "그리고 방송국 같은 명칭의 자막에는 엔비씨 가 아니라 NBC 로 표기 해줘"

## 1. 바꿀 것(화면 글자 전부 — 발음은 안 바꾼다)
| 대상 | 바꾸기 | 예 |
|---|---|---|
| script.yaml 각 문장 `text`(자막) | 엔비씨 → NBC · 씨비에스 → CBS · 에이피 → AP | "NBC 집계로는 상원이 …", "CBS 초기 출구조사에서 …", "AP 발표 전에 먼저 패배를 인정" |
| script.yaml `tts` | **그대로**(엔비씨·씨비에스·에이피) — 음성·plan.json·콘티 판 불변 | |
| direction 패널·bars `src` 출처 줄, marker sub, quote 출처, 엔딩 카드 표기 행 | "NBC 집계 · 11월 5일 오전", "확정 = AP 콜(보도 인용) 또는 NBC 결정데스크 추정" | |
| description.yaml·credits 문구 | 같은 표기 | |
- 기사 카드의 매체명은 이미 라틴(NBC News·CBS News 등) — `outlet_names` 대조(UF-130)가 자막 "NBC" 와 카드 "NBC News" 를 같은 매체로 보는지 확인(안 되면 별칭 표에 추가, 검사 hard 유지).
- 글리프: 자막 글꼴(IBM Plex Sans KR)에 라틴 대문자 있음 — `glyphs` 검사로 확인.

## 2. 절차
1. 진행 중인 720p 렌더가 있으면 **중단**(부분 산출물 버림). 표시 텍스트 수정 → `lint-script` 0 → direction 문자열 수정 → 검증 hard 0.
2. 원고 표시 텍스트만 바뀌므로 음성 재합성·콘티 판 재렌더 없음. script_sha1 이 바뀐다 — 게이트 ① 재승인은 사용자 지시(D528)로 갈음: 바뀐 sha1 을 R 과 manifest 의 다음 기록(`transition --reason` 또는 phase_report)에 적는다. 엔진이 승인 지문 불일치로 막으면(검사가 있으면) 멈추고 R 로 알린다 — 우회 금지.
3. `--preview auto` 를 다시 돌리지 않는다(글자만). 대신 원크기 3컷(act1_2 "NBC 집계" 자막·act1_10 "CBS 초기 출구조사"·엔딩 카드 표기 행)을 final 전에 뽑아 R 에.
4. 720p 전편 → audio.mix → engine.mux → final_deliver → artifacts final/ → phase_report R(D-0305 §3) + send_message.

## 3. 장치(전달 뒤, UF-171)
- script 린트: `text` 에 매체 음차(엔비씨·씨비에스·에이피·비비씨·씨엔엔 …) 금지, `tts` 에는 라틴 금지(기존) — 규칙 키 `script_vocab.outlet_display`(표기표) + 테스트. 원장 guards 갱신.
