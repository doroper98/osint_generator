<!--
tier: 1
last_synced_with: v5.12.0
ssot_for: [session-handoff]
depends_on: [CLAUDE.md, GOAL.md, VERSION, docs/13_IMPLEMENTATION_ROADMAP.md, docs/handoff/KICKOFF_PROMPT.md, docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, back_and_forth/README.md]
last_review: 2026-09-29
-->

# HANDOFF — 다음 세션 AI 인계 문서

다음 Claude Code 세션이 **가장 먼저 읽는 문서**다. 현재 상태의 거울이며 append-only가 아니다.
과거는 `DEVLOG.md`·`CHANGELOG.md`, Phase 계획은 `docs/13_IMPLEMENTATION_ROADMAP.md`가 SSOT다.

---

## 1. 지금 어디인가 (v5.3.0)

- **작업 브랜치: `overhaul/v2-map-engine`.** Phase 합격(Fable review pass) 뒤 Fable이 main을 fast-forward한다. PR 생성 금지(C8.5).
- **완료**: v2 개편 Phase 0~11·G1~G13(v2.0.0~v5.2.0). 합격 커밋은 `docs/handoff/TAGS_PENDING.md`.
- **진행**: G14 — 겹침 카드(cascade) 채택: 지도 고정 구간의 사건 경과를 겹침 카드 하나로(v5.3.0, back_and_forth D-0139, 사용자 결정 D116·판정 D117).
- **다음**: G4 사용자 판정("슬라이드가 아니라 다큐", `docs/handoff/20` §12). 합격 기준은 `GOAL.md` G3(17개, 항목별 검증 방법).

## 2. 일하는 방식 — back_and_forth

구현 세션(Opus)과 감독 세션(Fable)은 `back_and_forth/`에 파일로 교신한다. 규칙은 `back_and_forth/README.md`.

- Opus는 R(보고), Fable은 D(지침·결정)를 쓴다. 파일 이름은 `python back_and_forth/check.py --me opus --next-name {slug}`.
- 새 D 확인: `git pull --rebase origin overhaul/v2-map-engine && python back_and_forth/check.py --me opus`.
- **결정은 혼자 내리지 않는다.** `decision_request` R을 올리고 막히지 않는 작업을 계속한다(CLAUDE.md C11 말미).
- 세션 생존·재기동은 `docs/handoff/21_SESSION_LIVENESS_AND_RECOVERY.md`. 크론·sleep 루프를 만들지 않는다. Fable이 poke로 깨운다.
- 결정 기록 `docs/handoff/DECISIONS.md`는 Fable이 행을 추가한다.

## 3. 먼저 읽을 것

1. `CLAUDE.md`(C0 영상미·C11 관성 방지) → `GOAL.md`(G3·G4) → `docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md`.
2. 착수 원문 `docs/handoff/KICKOFF_PROMPT.md`, 실행 계획 `docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md`.
3. 영상 기준 정본 `docs/handoff/`(00_INDEX 읽는 순서), 수치 SSOT `rules/video_rules.yaml`, 설정 SSOT `config.yaml`.
4. 안내도: `docs/07`(영상)·`08`(오디오)·`09`(지도)·`10`(렌더)·`12`(QA)·`03`(워커)·`05`(스키마).

## 4. 새 컨테이너 준비

최신 절차는 가장 최근 Phase의 `docs/handoff/reports/phase*/run_log.md` §0이다. 요약:

- `git config core.hooksPath .githooks`, `pip install -r requirements.txt -r requirements-engine.txt`, `apt-get install ffmpeg fontconfig fonts-noto-cjk`.
- edge-tts가 프록시 CA를 쓰도록 certifi 번들에 `/root/.ccr/ca-bundle.crt`를 덧붙인다.
- 자산 복원: `artifacts/phase7-v3.3.0`의 `shared/` → hormuz `tts/`·`plan.json`·`media/`(`fetch_data media`는 돌리지 않는다 — Commons 429).
- `python tools/fetch_data.py fonts ne tiles flags bgm` → `commons people` → legacy 자산 복사 → `python -m geo.prep projects/hormuz_korea [--res 1080p]`.
- 1080p 를 렌더하면 클립도: `python tools/media_fetch.py projects/hormuz_korea --res 1080p --no-sheets`(복원한 webm 에서, md5 는 `reports/phase11/nb28_media.json`).
- 기준선: `pytest`(failed 0·xfail 0), `python -m engine.render projects/hormuz_korea --preview golden`(25컷).

## 5. 자주 까먹는 규칙

- **콘티 판(W0)은 필수.** 연출 판 → `audio.mix` → `engine.render --animatic` → 사용자에게 `out/animatic.mp4` 전달·흐름 검토 → 그 뒤 프리뷰·게이트 ②. 없으면 게이트 ② 승인이 코드에서 거부된다(PIPELINE-AP-014).
- 커밋 첫 줄 `vX.Y.Z: 요지` = `VERSION`. 한 커밋 한 의도. 푸시 거부 시 `pull --rebase` 후 재시도, force 금지.
- 모델 식별자를 산출물·커밋·문서에 넣지 않는다. `.env`·API 키 커밋 금지.
- 긴 실행(전편 렌더·AI 연출) 중에는 그 워크트리의 코드·규칙을 바꾸지 않는다(PIPELINE-AP-010).
- 결과는 영상(프리뷰 시트·provenance)으로 확인한다. 코드 리뷰만으로 "적용됨" 판정 금지(15 P12).
- 문서는 수치를 복사하지 않고 `rules:키`·`config:키`로 가리킨다(`tests/test_docs_sync.py`).

## 6. 이 문서의 갱신 규칙

- Phase가 시작·끝날 때 §1을 고친다. 버전이 오르면 `last_synced_with`도 고친다(`tests/test_docs_sync.py`).
- 지난 내용은 지운다. 이력은 `DEVLOG.md`·`CHANGELOG.md`·git이 보존한다. (쇼츠 콜라주 인계문·v0.3.3 인계문은 v4.0.0에서 제거 — git 이력과 `archive/hyperframes-briefing`.)
