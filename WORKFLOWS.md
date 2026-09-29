<!--
tier: 3
last_synced_with: v4.5.0
ssot_for: [execution-procedures]
depends_on: [README.md, HANDOFF.md, docs/15_OPERATIONS_RUNBOOK.md, docs/handoff/16_ORCHESTRATOR_INTEGRATION.md]
last_review: 2026-09-29
-->

# WORKFLOWS

실제 운영 절차다. 명령 표의 요약본은 `docs/15_OPERATIONS_RUNBOOK.md` §1, 새 컨테이너 준비는 `HANDOFF.md` §4 다.
(v4.1.0 에서 v0.3.3 판을 현재 명령으로 다시 썼다 — NB29. 옛 `render-debug`·`build-audio` 등은 v2.0.0 에서 삭제됐다.)

---

## W1. 새 영상 프로젝트

```bash
python -m orchestrator.main new-project {pid} --title "..." --category geopolitics --topic-summary "..." [--link URL]
python -m orchestrator.main command-center --project {pid}      # 또는 run_pipeline.bat
```

상태 흐름(`schemas/models.py ProjectState`, docs/handoff/16 §2):
`created → intake → source_verify → research → script_draft → script_approval★ → voice_timeline → assets → direction → preview_qa → preview_approval★ → render → audio_mix → deliver → done`.
★ 두 곳이 사용자 승인 게이트다.

## W2. 소스 접수와 원고

```bash
python -m orchestrator.main add-source {pid} --kind article --url URL --fetch     # x-text·x-capture·document 도 있다(18 §1)
python -m orchestrator.main confirm-source {pid} --id SRC_ID --by NAME           # 계정·시각 확인(18 §7)
python -m orchestrator.main submit-intake {pid}                                   # intake → source_verify
python -m orchestrator.main import-bundle {pid} --file report_bundle.json        # 번들 입력(v3.5.0)
python -m orchestrator.main lint-script {pid}                                     # 금지 문구·발음 기호·출처·검증 라벨
```

## W3. 엔진 단계 진행

```bash
python -m orchestrator.main advance --project {pid} [--jobs N]     # 현재 엔진 상태의 단계 → ok 면 다음 상태
python -m orchestrator.main gate-view --project {pid}              # 게이트 화면 텍스트
python -m orchestrator.main approve --project {pid} --gate script_approval|preview_approval --comment "..." [--version N]
python -m orchestrator.main reject  --project {pid} --gate preview_approval --to direction --comment "..."
```

게이트 기록 위치: `projects/{pid}/project_manifest.json` 의 `gate_decisions`.
Command Center 단축키: `g` advance · `a` approve · `x` reject · `c` 소스 확인 · `r` 큐 새로고침 · `s` 스냅샷 · `q` 종료.

엔진을 직접 돌릴 때(오케스트레이터는 같은 CLI 를 부른다, 15 P1):

```bash
python -m script.plan projects/{pid} --tts edge                   # 원고 → TTS → plan.json
python -m geo.prep projects/{pid} [--res 1080p]                    # 지형 티어(1080p 는 별도 티어)
python -m engine.camera_suggest projects/{pid}                     # 카메라 제안(옵션, 연출에 자동 적용 안 함)
python -m engine.render projects/{pid} --preview auto|golden       # 프리뷰 컷·시트·checks·provenance
python -m engine.render projects/{pid} --jobs 4 [--res 1080p]      # 전편 video_noaudio.mp4
```

## W4. Worker 추가

1. `workers/{name}_worker.py`, `BaseWorker` 상속(CLAUDE.md C4).
2. 프롬프트는 `prompts/*.md` 템플릿 + `rules/video_rules.yaml` 에서 만든다. 코드 상수 금지(15 P3).
3. `docs/03_AGENT_ARCHITECTURE.md` 워커 표에 한 줄.
4. `tests/` 에 워커 테스트, 프롬프트 예시 출력은 스키마 파리티 테스트(15 P4).
5. CHANGELOG `Added`.

## W5. Antipattern 기록

1. 재현 절차 확보.
2. 카테고리: `TTS-AP`·`PIPELINE-AP`·`RIGHTS-AP`·`RENDER-AP`·`SCHEMA-AP`·`LLM-AP`.
3. `docs/ANTIPATTERNS/{CAT}_ANTIPATTERNS.md` 끝에 새 번호 append(과거 항목 수정 금지).
4. 재발 방지 검증기·테스트·hook.
5. `DEVLOG.md` 한 줄 + AP 번호.

## W6. 커밋

```bash
git config core.hooksPath .githooks                # 첫 한 번
python -m py_compile $(git diff --cached --name-only | grep '\.py$')
git commit -m "v4.1.0: 요지"                         # 첫 줄 prefix = VERSION 파일(.githooks/commit-msg 가 검사)
```

버전 SSOT 는 `VERSION` 이고 `orchestrator/__init__.py:__version__` 을 같이 올린다(C5.1).

## W7. Phase 완료 체크리스트

- [ ] 지침(back_and_forth D)의 합격표 전부 충족, 증거 파일은 `docs/handoff/reports/phase*/`
- [ ] `pytest` failed 0 · xfail 0(D-0053 삭제 조정 기준선)
- [ ] 영상 영향이면 프리뷰 시트 + provenance, 무변경이면 hormuz 25컷 md5
- [ ] 새 Antipattern 기록
- [ ] CHANGELOG 버전 절, Tier 1·2 `last_synced_with`(`tests/test_docs_sync.py`)
- [ ] `phase_report` R(README §6.3 다섯 항목)
