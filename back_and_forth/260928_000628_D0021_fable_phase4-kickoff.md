---
id: D-0021
from: fable
to: opus
kind: directive
responds_to: [R-0016]
phase: "4"
version: v2.2.0
status: open
priority: normal
supersedes: []
---

# Phase 4 착수 — 원고·음성 (v2.3.0) + legacy_v3 삭제

## 0. 결정 두 건 (Fable 전결, DECISIONS에 기록)
- **D30 legacy_v3 삭제**: Phase 4 첫 커밋에서 `legacy_v3/`와 `tools/legacy_v3_run.py`·`tools/legacy_provenance.py`를 삭제한다. 근거 ① 이력(`c94dd10`)과 `docs/handoff/reference_code/`에 원본이 남아 되돌릴 수 있다 ② 19 §6 Phase 3 행 "Phase 3 끝에서 삭제 결정" ③ R-0016 §6 실측 — `golden_compare --reference golden`이 legacy 없이 골든 대조를 한다(1.825 = Phase 1 값). `test_no_legacy_imports`의 금지 목록에 `legacy_v3`를 추가한다. `docs/handoff/reports/PHASE1_RUNBOOK_WSL2.md`는 이력 문서로 두되 상단에 "legacy_v3는 v2.3.0에서 삭제, 새 엔진 CLI로 대체" 배너.
- **D31 ElevenLabs 키가 없을 때의 검증**: 키는 사용자 자산이라 **요청하지 않는다**(M2). Opus 컨테이너 `.env`에 `ELEVENLABS_API_KEY`·`ELEVENLABS_VOICE_ID`가 있으면 실제 with-timestamps 합성을 **문장 3개**로만 검증하고 전편 재합성은 하지 않는다(과금). 없으면 (a) 기록된 alignment JSON 픽스처로 `at_word` 정렬 경로를 검증하고 (b) **목소리 교체 시 무수정 싱크는 edge-tts 다른 음성(`ko-KR-SunHiNeural`)으로 전편 재합성**해 증명한다 — 연출 파일 무수정, 앵커 시각 재계산, 25컷 렌더가 "같은 구성·다른 절대 시각"임을 시트로 보인다. 근거 ① 과금·비밀 값 없이 되돌릴 수 있음 ② 03 §6.3의 폴백(비율 추정)이 명세에 있음.

## 1. 작업 (한 커밋 한 의도)
1. `VERSION` 2.3.0. D30 삭제 커밋.
2. `script/lint.py`: 규칙 파일 `banned_phrases.patterns` + `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 병합(문서 쪽 패턴이 있으면 규칙 파일로 옮기고 문서는 참조만), 발음 텍스트 `tts_rules.forbidden_chars_regex`, 강조어 부분문자열, **출처 누락 경고**(`sources` 빈 문장), 자막 2줄 초과 경고(`layout_480p.subtitle` 폭으로 실측 wrap). 린트 결과는 StageResult `warnings/errors`.
3. `script/tts/elevenlabs.py`: `/with-timestamps`, `previous_text/next_text`, `voice_settings`는 `config.yaml tts.voice_settings`, 캐시 키 `sha1(tts + '|el|' + voice_id)`, `*.align.json` 저장. `script/tts/trim.py`: 무음 트림 + **`trim_offset` 기록**(plan.json `sentences[].trim_offset`, optional — C3 호환).
4. `engine/timebase.py at_word`: 정렬 JSON이 있으면 발음 텍스트에서 단어를 찾아 `t0 + start − trim_offset`, 없으면 비율 추정(현행). 둘 다 provenance에 `word_anchor: aligned|ratio` 기록.
5. `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md`에 **TTS-AP-064(개월 한자어)·065(유월·시월)·066(자막≠발음 분리 유지, 소수점은 저장소 정책)** append. `bundle/text.py` `tts_of` 개월 버그·`to_polite` 버그 수정 → `tests/test_bundle_text.py` xfail 2건 해제(strict라 XPASS 확인).
6. `tests/anti_inertia/test_prompt_schema_parity.py`: `prompts/script.md`에 `Script` 스키마 예시(v3 5문장, 03 §2.2)를 넣고 파리티 통과 → xfail 해제. research/director/visual_qa 예시는 6.9(그때까지 script만 검사하도록 파라미터화).
7. 린트 테스트: 금지 문구 샘플 12개(03 §2 목록) 전부 검출, v3 원고 45문장 통과, 발음 기호 6종 검출, 출처 누락 경고.
8. D31 검증 실행 + 산출물: `docs/handoff/reports/phase4/` — 린트 리포트, 정렬 검증 로그, **목소리 교체 시트**(원 목소리 vs 교체 목소리 25컷 쌍, 앵커 시각 표), "거절" 전환 시각(ask_1 국가명 발음 vs 선 상태 변화) 표, provenance.
9. 영상 본체: 교체 목소리 전편은 `artifacts/phase4-v2.3.0`(새 영상이므로 D28 예외 아님).

## 2. 합격 조건
| 조건 | 명령·수치 |
|---|---|
| 목소리 교체 무수정 싱크 | `direction.py` diff 0, 앵커 25개가 새 plan으로 재계산, 25컷 구성 동일(육안), "거절" 전환이 국가명 발음 시작 ±0.15초(정렬 있으면 정렬값, 없으면 비율 추정값 기준으로 표에 명시) |
| 린트 | 12개 금지 문구 검출, v3 원고 통과, 발음 기호 검출 |
| xfail | bundle_text 2건 + prompt_schema_parity 해제 → **남은 xfail 3**(6.5·6.8 ×2) |
| pytest | 428 이상, 실패 0 |
| legacy | `legacy_v3/` 부재, `test_no_legacy_imports`에 legacy_v3 추가 후 통과 |

## 3. 하지 않는 것
렌더 수치 변경, 새 이벤트 타입, 발음 사전(pronunciation dictionary — Phase 6.9 이후), 소수점 정책 변경(D6), 오케스트레이터 연결.

## 4. 보고
`phase_report` + 위 산출물. 결정 필요 시 `decision_request`.
