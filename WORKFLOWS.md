<!--
tier: 3
last_synced_with: v4.9.0
ssot_for: [execution-procedures]
depends_on: [README.md, HANDOFF.md, docs/15_OPERATIONS_RUNBOOK.md, docs/handoff/16_ORCHESTRATOR_INTEGRATION.md]
last_review: 2026-09-30
-->

# WORKFLOWS

실제 운영 절차다. 명령 표의 요약본은 `docs/15_OPERATIONS_RUNBOOK.md` §1, 새 컨테이너 준비는 `HANDOFF.md` §4 다.
(v4.1.0 에서 v0.3.3 판을 현재 명령으로 다시 썼다 — NB29. 옛 `render-debug`·`build-audio` 등은 v2.0.0 에서 삭제됐다.)

---

## W0. 콘티 판(animatic) — 흐름·호흡을 먼저 싸게 (v4.9.0, back_and_forth D-0108, 사용자 결정 D97)

> **순서 의무 — 자막(원고) → 콘티 → (승인 후) 본영상 (v5.6.0, 사용자 결정 2026-10-04, PIPELINE-AP-015).**
> 1. 원고가 나오면 `python -m orchestrator.main gate-view {pid}` 원고 검토 자료(원고 전문·출처 표·린트)를 **사용자에게 보내 자막 점검**을 요청한다.
> 2. 사용자 승인 → `approve --gate script_approval` (승인 기록에 원고 지문 `script_sha1`).
> 3. 음성 → 연출 → 콘티 판(기록에 원고 지문). 콘티 판을 보낼 때도 원고 검토 자료를 함께 보낸다.
> 4. 게이트 ② 는 콘티 판의 원고 지문 = 승인 원고 지문일 때만 통과. 원고를 고치면 게이트 ① 부터 다시.
>
> **자산 보관 (v5.6.0, PIPELINE-AP-016)**: 초상·휘장 등 이번 영상에서 만든 자산은 콘티 판 전에
> `python tools/asset_library.py promote projects/{pid}` 로 공용 자산에 올린다(`check` = 0). 다음 영상은 공용 자산을 먼저 쓴다.

용어: **콘티 판** = animatic(animation + -matic). 1930년대 디즈니가 스토리보드를 찍어 음성과 함께 틀어 본 "Leica reel"이 원형이고,
광고·애니메이션 업계가 1970년대부터 animatic 이라 불렀다. "콘티"는 일본어 コンテ(continuity 의 축약)에서 왔다.

> **필수 단계 — 건너뛰기 금지(사용자 결정 2026-10-01, PIPELINE-AP-014).** 모든 영상 프로젝트는 게이트 ② 전에 콘티 판을 만들고
> `out/animatic.mp4` 를 **사용자에게 보내 흐름 검토를 받는다.** "검수 루프가 hard 0 이니 바로 프리뷰" 는 허용되지 않는다.
> 코드 강제: `approve --gate preview_approval` 은 현재 `plan.json` 길이와 같은 콘티 판 기록(`out/animatic_provenance.json`)이 없으면
> 거부된다(`orchestrator.project_manager.require_animatic`). 음성을 다시 만들면 콘티 판도 다시 만든다. 우회 플래그는 없다.
> 게이트 ② 기록 `shown.animatic` 에 콘티 판 경로·길이·연출 판 sha1(`animatic_run.direction_sha1`)이 남는다.

게이트 ① 원고 승인 뒤, 게이트 ② 프리뷰 전에 돈다. 연출 v1 이 나오면 콘티 판으로 흐름을 보고, 고칠 것이 있으면 연출로 되돌려 다시 돈다.

연출 전에 미디어 재료를 등록한다(v5.6.0 PIPELINE-AP-019 — 등록이 빠지면 연출 후보가 0건이라 인용·기사 조판·실사가 화면에 안 나온다):
- 기사 조판: `python tools/article_register.py projects/{pid}` → 빠진 헤드라인 번역(sources.json `headline_ko`)을 채우고 `--write`.
- 실사(사진·영상): `python tools/media_fetch.py search "<무기·장소 이름>"` 로 후보(라이선스·제한 표시)를 찾고, 피사체·라이선스·촬영 시기를
  대조해 고른 것만 레지스트리에 권리 기록과 함께 올린다(무기 이름 = rules weapon_photo.terms).
- 인용: 검증 단계가 claims `direct_quotes`(원문 따옴표 발언)를 남긴다 — 연출 입력 "인용 후보"로 자동 공급.
콘티 판을 보낼 때 `gate-view` 의 **미디어·인용 요약**(쓴 수/쓸 수 있던 수, 무기 이름의 실사 유무, 실사 출처·라이선스 목록, media_note)을 함께 보낸다 —
콘티 판에서 실사는 자리표시라 이 목록으로 확인한다. 0건이어도 막지 않는다(사용자 결정 2026-10-05) — 이유를 media_note 에 적는다.

```bash
python -m script.plan projects/{pid} --tts edge          # 러프 음성(무료·빠름). ElevenLabs 는 콘티 판 단계에서 쓰지 않는다
python -m audio.mix projects/{pid}                        # 음악·믹스는 전편과 같다(bed_bass 포함)
python -m engine.render projects/{pid} --animatic         # → out/animatic.mp4 (480p·fps 24, 5분 영상 = 4코어 3분 목표)
python -m engine.render projects/{pid} --animatic --preview auto   # (선택) prev_animatic/ 컷·시트
```

사용자 흐름 검토 뒤 고칠 것이 있으면 연출을 다시 한다. 프로젝트가 아직 `direction` 상태면 연출 판(direction.vN)을 고쳐 콘티 판을 다시 돌리고,
이미 렌더 이후 상태면 `python -m orchestrator.main reopen --project {pid} --to direction --reason "콘티 판 흐름 검토: …"`(D4)로 되돌린다.
원고(자막) 내용을 고칠 때는 `reopen --to script_draft` → 게이트 ① 재승인 → 음성 → 콘티 판 순서다(v5.6.0 PIPELINE-AP-017).
흐름이 정해지면 게이트 ② 프리뷰(`--preview auto`) → 전편으로 간다.

| 콘티 판에서 | 전편과 |
|---|---|
| 자막·타이틀·엔딩 카드·날짜·마커·경로·타격 링·선박·국가 강조·시리즈·카메라·dip·음악 | 같다(자막이 호흡의 기준) |
| 카드·패널(숫자·문구·도식) | 같다 — 콘티 판에서 승인한다(v5.6.0 PIPELINE-AP-018). 패널 안 뱃지만 자리표시 |
| 뱃지(인물·국기·휘장)·사진·영상·컷아웃·기사·게시물·프리미티브 | 같은 자리·크기·타이밍의 자리표시 상자 + `[뱃지: 이름]` 같은 글자 |
| 지도 | 막지도 — 육지·바다 단색 + 국경선(`data/geo_flat/`, 자산·타일 없음), 라벨 없음 |
| 표식 | 화면 위 가운데 띠 "콘티 판 · 검토용 · 배포 금지", provenance `animatic: true`, mp4 메타데이터 표식 |
| 검사 | 콘티 프로파일 — 글리프·글자 크기·권리·미디어 해상도·차트 정직성·라벨 수는 건너뛴다(`out/animatic_checks.json` skipped) |
| 배포 | `engine.mux`(deliver)는 콘티 판을 거부한다 |

산출물: `out/animatic.mp4`, `out/animatic_checks.json`, `out/animatic_provenance.json`(`animatic_run` — 시간·조각·자리표시 수·건너뛴 검사).
전편 산출물(`out/video_noaudio.mp4`·`final.mp4`·`render.json`)과 게이트가 읽는 `prev/` 는 건드리지 않는다.
자산 없는 환경(geo.prep·미디어 받기 전)에서도 돈다 — plan.json·mix.f32 만 있으면 된다.

## W1. 새 영상 프로젝트

```bash
python -m orchestrator.main new-project {pid} --title "..." --category geopolitics --topic-summary "..." [--link URL]
python -m orchestrator.main command-center --project {pid}      # 또는 run_pipeline.bat
```

상태 흐름(`schemas/models.py ProjectState`, docs/handoff/16 §2):
`created → intake → source_verify → research → script_draft → script_approval★ → voice_timeline → assets → direction → preview_qa → preview_approval★ → render → audio_mix → deliver → done`.
★ 두 곳이 사용자 승인 게이트다. `direction` 과 `preview_approval★` 사이에 **콘티 판(W0) 사용자 흐름 검토가 필수**다 — 콘티 판 기록 없이는 게이트 ② 승인이 거부된다.

### W1.1 새 프로젝트 준비 체크리스트 (v4.7.0, back_and_forth D-0104 D3 — dmz_mine_2026 누락 M1~M5)

| 확인 | 왜 | 어떻게 |
|---|---|---|
| credits.yaml 에 음악 행 | 연출가 입력 `{music_list}` 가 크레딧 기준이라, 음악 행이 없으면 `sound.bgm: null`(무음악)로 나온다(M1) | `- music: music.<id>`(BGM 레지스트리 `assets/audio/bgm/registry.yaml`). 무음악이 의도면 그 사실을 order.yaml 에 적는다 |
| TTS 백엔드 | 이전 Phase 명령의 `--tts edge` 를 그대로 따라 하면 config 기본값(`config.yaml tts.backend_default`)과 다른 목소리가 된다(M2) | `script.plan` 전에 `backend_default` 와 키 유무를 확인하고, 다르게 쓸 때만 `--tts` 를 준다 |
| 매체명 라틴 표기 | 키릴·아랍 문자 매체명은 엔딩 크레딧 글꼴에 글리프가 없어 검사 오류가 난다(M4) | 소스 표기는 라틴(예: VZGLYAD.RU), 원 표기는 note 에 |
| 제목 길이 | 긴 제목은 타이틀 카드에서 잘린다(M3) | 첫 프리뷰 전에 타이틀 카드 한 컷(`--preview` 타이틀 시각)으로 확인, 길면 부제로 나눈다 |
| 좌표 출처 | 공개되지 않은 사건 지점을 아는 것처럼 찍으면 정확성 위반이다(M5) | 사건 지점 좌표는 출처(지명·claim 위치 수치)가 있을 때만. 없으면 marker `sub` 에 "좌표 비공개". 경계선은 `route` 로 그리지 않는다 |

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
python -m engine.render projects/{pid} --animatic [--jobs 4]      # 콘티 판 out/animatic.mp4(W0, v4.9.0)
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
