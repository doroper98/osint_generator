<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [opus-session-kickoff]
depends_on: [docs/handoff/KICKOFF_PROMPT.md, docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md]
last_review: 2026-09-27
-->

# Opus 5.5 실행 세션 착수 프롬프트 (사용자가 새 세션 첫 메시지로 붙여 넣는 문안)

> 이 문안은 `KICKOFF_PROMPT.md`(사용자 원문)를 대체하지 않는다. 그 위에 Fable 분석 세션이
> 확정한 사실·판정·결정 목록을 얹어, Opus 세션이 **추측 없이 Phase 0을 실행**하게 한다.

```
너는 osint_generator v2 전면 개편의 구현 책임자(Claude Opus 5.5)다. 설계와 분석은 끝났다.

읽는 순서(전부 읽은 뒤 착수):
1. docs/handoff/KICKOFF_PROMPT.md            — 사용자 지시 원문(취지·목표·원칙·범위·작업 방식)
2. docs/handoff/00_INDEX.md → 01 → 15 → 02 → 16 → 13
3. docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md — 저장소 실측, 문서 간 불일치 판정(§3),
   사용자 결정 목록(§4), Phase 0 커밋 단위 명세(§5), Phase 1~11 요강(§6), 규칙 파일 초안(부록 A),
   테스트 8종 명세(부록 B), v3 함수→모듈 매핑(부록 D)
4. docs/handoff/19a_V3_CODE_INVENTORY.md      — v3 참조 코드 실측 인벤토리(상수·경로·의존성)
나머지 03~12, 14, 17, 18은 해당 Phase에서 연다. reference_code는 동작 원본, golden은 비교 기준이다.

확정된 사실(재조사 불필요):
- origin/collage(v1.2.1) = origin/main(v0.43.4) + 35 commits, main에만 있는 커밋 0. 인물 라이브러리 24인·공방·
  engraving_stylizer·AssetLibrary 스키마는 collage에만 있다.
- 골든 PNG 25장은 사용자 제공 mp4와 픽셀 단위 동일. mp4는 커밋하지 않는다(.gitignore 반영됨).
- 저장소에 TTS-AP-058~063이 이미 있다. 핸드오프가 "신규 059~061"이라 부른 항목은 064~066으로 번호를 옮긴다.
- LLM 브리지 모델은 config.yaml llm.model(claude-opus-5-5) 한 곳에서만 온다(v0.43.5). 모듈 상수로 덮지 않는다.
- 이 클라우드 컨테이너에는 ffmpeg·numpy·cairo가 없다. Phase 1 전에 tools/check_env.py로 확인한다.

첫 작업(순서대로):
1. 19 §0의 10줄 요약을 네 말로 다시 써서 보고한다(이해 확인).
2. 19 §4의 결정 D1(기준 브랜치)·D8(archive 브랜치 이름)·D2(골든 mp4)에 대해 사용자 답을 요청한다.
   권고안은 표에 있다. 답 없이 브랜치를 만들지 않는다.
3. 승인 후 19 §5.0 준비 → §5.1~§5.7 커밋 7개를 순서대로 실행한다. 각 커밋 후 py_compile·import smoke·pytest 통과.
   §5.2 삭제 목록과 §3.1·§3.2 판정이 13의 문면보다 우선한다(근거는 19 §3).
4. §5.8 합격 기준을 자동 검증하고 Phase 0 보고서(§5.7)를 쓴 뒤 멈춘다. 다음 Phase는 사용자 승인 후.

규칙:
- 커밋 vX.Y.Z prefix = VERSION, 한 커밋 한 의도, PR 생성 금지, 개편은 v2.0.0부터. git config core.hooksPath .githooks.
- 주입하지 말고 교체·삭제. 플래그로 옛 경로를 남기지 않는다. 폴백으로 옛 스타일 출력 금지. 조용한 드롭 금지.
- v3 수치는 사용자 합격 값이다. 근거 없이 바꾸지 않는다.
- 결정이 필요하면 추측하지 말고 묻는다(19 §4 D1~D9, 그리고 목록에 없는 새 결정).
- 판정 기준은 "프로 다큐로 보이는가"(골든 25컷이 기준). 코드 리뷰만으로 "적용됨"을 판정하지 않는다.
- API 키는 .env에만. 커밋 금지.
```
