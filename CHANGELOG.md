<!--
tier: 3
last_synced_with: v0.4.2
ssot_for: [release-notes]
depends_on: [README.md, GOAL.md]
last_review: 2026-05-22
-->

# CHANGELOG

본 문서는 사용자(또는 후속 개발자) 관점의 릴리즈 노트입니다.
released 항목은 **append-only**입니다.

본 저장소는 [Semantic Versioning](https://semver.org/)을 따릅니다.

---

## [Unreleased]

### Added
- 

### Changed
-

### Fixed
-

---

## [v0.5.0] — 2026-05-22

Phase 5 첫 PATCH — `SourceCollectorWorker` 도입 (codex agent 모드 첫 도메인 worker).
본 시점에 v0.4.0–v0.4.2 의 LLM-AP-003 mitigation (sandbox + scratch dir + path
가드 + side-channel known-limits) 위에서 실 호출하는 worker 가 처음 들어온다.

### Added

- **`workers/source_collector_worker.py`** — `BaseLLMWorker` 상속, `llm_backend=
  "codex"`, `llm_mode="agent"`, `allow_agent_mode=True` (LLM-AP-003 opt-in).
  `response_model=SourceCollectionPartial`. system prompt 가 SourceCollectionPartial
  / SourceEntry / RightsStatus 스키마와 codex agent sandbox 의 verified side
  channels (`%TEMP%`, `~/.codex/memories`) 접근 금지를 명시. `build_user_prompt`
  는 `01_intake/source_intake.json` 의 매칭 `UserDecision` 을 읽어 `user_note`,
  `provided_links`, `google_drive_links`, `uploaded_files` 를 `wrap_untrusted`
  로 단일 `<untrusted_source>` envelope 으로 격리. mode ∈ {ai_delegate, mixed}
  외에는 ValueError. output_path = `02_sources/partials/{task_id}.json`.
- **`orchestrator/source_collection_planner.py`** — 순수 함수 빌더. `task_id_for`,
  `needs_collection`, `build_source_collection_tasks(intake, existing_task_ids=...)`.
  `ai_delegate` / `mixed(ai_delegate_remaining=True)` 만 task 로 변환. `task_id`
  prefix `src_collect__{item_id}` 로 `_is_safe_path_segment` 통과 보장.
  `existing_task_ids` 로 idempotency.
- **`tests/test_source_collector_worker.py`** — 29 케이스 / 7 클러스터:
  system_prompt 정합 (스키마 / enum / sandbox 경계 / envelope guidance /
  `.format()` 금지), build_user_prompt (정상 매핑 / envelope injection 격리 /
  누락 / 잘못된 mode), output_path, run() 4 분기 (ok / parse_failed /
  validation_failed / subprocess_error), agent opt-in 가드 통과,
  `_build_invocation_cmd` 의 sandbox argv shape + scratch dir 부수 효과,
  task builder mode 필터 + idempotency.

### Changed

- **`VERSION`** 0.4.2 → 0.5.0 (MINOR — 새 worker 추가, C5.4).

### Verification

- `python -m py_compile` 통과 (신규 3 파일).
- `python -m unittest discover -s tests` = **129/129 통과** (기존 100 + 신규 29).
- 본 PATCH 는 commit + push 후 codex 클라우드 외부 리뷰 예정 (CLAUDE.md C10.1
  MINOR 직전 의무). 결과 흡수는 후속 v0.5.1 PATCH (v0.4.0 → v0.4.1 패턴과 동일).

### Migration / Compatibility

- 스키마 변경 없음 (`SourceCollectionPartial` 은 v0.4.0 도입). `schema_version`
  변경 없음.
- 호출하는 task / CLI / state 전이는 후속 PATCH. 본 PATCH 만으로는 worker 가
  pipeline 에 자동 합류하지 않음 — orchestrator 가 source_collection task 를
  생성하기 시작해야 활성화.

### Out of Scope (deferred)

- `task_queue.json` 영속화 + CLI 명령 (`build-source-tasks` 등) + state 전이.
- `SourceRegistryBuilder` (partial → `SourceRegistry` 합치기).
- 실 codex 프로세스를 띄우는 e2e smoke (사용자 머신에서 후속 PATCH).
- Phase 5 완료 marker.

---

## [v0.4.2] — 2026-05-22

LLM-AP-003 mitigation 의 실 효과 검증 (codex 0.130.0 Windows) 후 known-limits
및 ADDENDUM_04 §5.2.1 갱신. 코드 변경 없음, 문서만. CLAUDE.md C10.3 에 따라
codex 재리뷰 면제 (외부 검증 결과 반영 PATCH).

### Changed

- **`docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` §5.2.1 신설** — codex agent
  mode sandbox 가정의 실 검증 표. workdir 외 자동 허용 영역 (`%TEMP%`,
  `~/.codex/memories`) + junction 차단 확인 + codex 0.130.0 CLI 의 narrowing
  옵션 부재 + 버전 종속성 명시.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-003 known-limits** —
  v0.4.2 갱신. "검증된 보호" / "검증된 side channels" 두 절로 재구성. v0.4.1
  의 `_assert_no_symlinks_in_path` preflight 가 codex 0.130.0 의 OS-level
  junction 차단과 중복하지만 defense-in-depth 로 유지함을 명시.

### Verification

실 검증 시나리오 (사용자 머신, ChatGPT Plus 구독, codex-cli 0.130.0):

**Stage 1 — codex CLI 직접 호출**:
- 1a: workdir 안 write → ✅ 정상 (codex 가 `inside.txt` 생성)
- 1b-Desktop: workdir 밖 명확한 write → ✅ codex 가 sandbox 거부 명시
- 1b-multi: `C:\tmp\sibling`, `%TEMP%`, `~/.codex/memories` 각각 시도 →
  sibling 차단 ✅ / `%TEMP%` 허용 ⚠️ / memories 허용 ⚠️
- 1c-junction: `mklink /J` 로 scratch 안에 outside 가리키는 junction 깐 뒤
  via_junction.txt 작성 시도 → codex 가 OS-level 차단 ✅

**Stage 2 — Python 가드 단독** (컨테이너):
- `_is_safe_path_segment` 11 케이스 모두 기대값
- `_scratch_dir_for_task` 멱등성 / clean_scratch ephemeral / opt-out 정상
- `_build_invocation_cmd` argv 모양: codex agent 에 sandbox + scratch_cd 포함,
  claude response 에 sandbox 부재 + mkdir 부재
- `_assert_no_symlinks_in_path` POSIX symlink 검출 동작
- placeholder fail-fast + response + `{scratch_dir}` raise 모두 동작
- 사용자 prompt 본문의 JSON `{}` 는 검사 제외

**결론**: v0.4.0-v0.4.1 mitigation 은 핵심 자산 보호 (다른 worker 산출물 /
git 추적 코드 / 사용자 자료) 에 효과적. `%TEMP%` 와 `.codex/memories` 두
side channel 은 codex CLI 의 디폴트로 닫을 수 없어 known-limit 로 명시 +
prompt 측 / 운영 절차로 보강.

### Migration / Compatibility

문서 변경만. 코드/스키마 변경 없음.

---

## [v0.4.1] — 2026-05-22

v0.4.0 의 codex 1차 외부 리뷰 흡수 (Critical 2 / High 3 / Medium 3 / Low 1 / Nit 1).
sandbox + scratch dir 격리의 "의도된 가정" 들을 명시적 가드로 승격하고 회귀 테스트로
잠근다. 본 PATCH 는 CLAUDE.md C10.3 에 따라 codex 재리뷰 면제.

### Added

- **`workers/base_llm_worker.py:_is_safe_path_segment`** (module-level helper)
  — task_id 가 단일 path 세그먼트로 안전한지 검사. `/`, `\\`, `..`, `.`,
  leading `.`, 길이 > 128 거부. `Path(s).name == s` 추가 확인.
- **`workers/base_llm_worker.py:_assert_no_symlinks_in_path`** (module-level
  helper) — `path` 부터 `stop_at` 까지 위로 올라가며 symlink 검사. scratch
  경계가 symlink 인 escape 시나리오 차단.
- **`BaseLLMWorker.clean_scratch_on_start: ClassVar[bool] = True`** — scratch
  dir ephemeral 보장. 같은 task_id 재실행 시 이전 잔존물 노출 차단. 멱등
  worker (parse-on-resume) 가 잔존물 활용해야 하면 False 로 opt-out.
- **`BaseLLMWorker._build_invocation_cmd(args, full_prompt) -> list[str]`** —
  `_invoke_llm` 에서 argv 빌드 로직을 분리. subprocess 호출 없는 순수 함수라
  argv shape 회귀 테스트 가능.
- **`tests/test_base_llm_worker_sandbox.py`** — 17 메소드. path segment
  safety / scratch dir lifecycle / symlink preflight / codex-agent argv 의
  sandbox+scratch_cd 존재 / response argv 의 sandbox 부재 / placeholder
  fail-fast / response 모드 + `{scratch_dir}` raise / 사용자 prompt 본문 내
  `{...}` 허용 카테고리.

### Changed

- **`BaseLLMWorker._scratch_dir_for_task`** — (a) `_is_safe_path_segment` 로
  task_id 검증, 실패 시 `LLMSubprocessError` (LLM-AP-003 path traversal 가드).
  (b) `clean_scratch_on_start=True` 면 mkdir 전에 `shutil.rmtree`. (c) mkdir
  직후 `_assert_no_symlinks_in_path` preflight 로 scratch_root → scratch_dir
  경로상 symlink 검사.
- **`BaseLLMWorker._build_invocation_cmd`** (분리된 신규 메서드 안) —
  (a) template-driven scratch: `{scratch_dir}` 가 template 에 있을 때만
  `_scratch_dir_for_task` 호출 (mode-driven → template-driven). (b) response
  모드 template 에 `{scratch_dir}` 발견 시 `LLMSubprocessError` raise (silent
  empty-string substitution footgun 제거). (c) 치환 후 `{name}` 패턴이 cmd
  argv 에 잔존하면 fail-fast (사용자 prompt 자리는 예외 — JSON `{}` 충돌 회피).
- **`schemas/models.py:SourceCollectionPartial`** — (a) docstring "Phase 4"
  → "Phase 5" 정정 (DEVLOG/CHANGELOG/LLM-AP-003 의 표기와 일치). (b)
  `notes` → `collector_notes` rename (consumer 입장에서 출처 명확화). 본
  모델은 v0.4.0 신규로 영속 인스턴스 없어 호환성 부담 없음.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-003** — mitigation /
  regression_test / resolved / status / known-limits 절 v0.4.1 항목 추가.
  v0.4.0 의 "scratch 밖으로도 write 못 함" 단정 → "의도된 가정 하에서 …"
  로 톤다운 (known-limits 의 symlink/mount 불확실성과 균형).

### Rationale

codex 1차 리뷰가 정확히 짚은 것: v0.4.0 는 "올바른 방향" 이지만 "실 효과를
보장하는 가드" 가 빠져 있었다. v0.4.0 의 LLM-AP-003 본문이 "intent" 만 적고
"verified guarantees" 까지 적지 못한 것을 v0.4.1 에서 보강.

Critical 2 항목 (task_id traversal / symlink escape) 은 단일 가드 함수
도입으로 처리. High 3 (placeholder footgun / mode-template drift / 테스트
부재) 는 `_build_invocation_cmd` 추출 + fail-fast + 17 회귀 테스트로 처리.
Medium 3 / Low 1 / Nit 1 도 같은 PATCH 에 묶음 — 모두 같은 의도 "v0.4.0
mitigation 의 가드 승격" 하에 있음.

### Testing

- `python -m py_compile workers/base_llm_worker.py schemas/models.py
  tests/test_base_llm_worker_sandbox.py` 통과.
- `python -m unittest discover tests` — 100 케이스 통과 (기존 83 + 신규 17,
  회귀 없음).

### False positive

리뷰의 첫 번째 round (commit 9b200a8 이전 working tree 기준) 는 컨테이너의
uncommitted 변경을 사용자 머신에서 못 봐서 "구현 안 됨" 으로 정확히 짚었지만,
두 번째 round (commit 9b200a8 기준) 로 superseded. 본 PATCH 는 두 번째 round
만 흡수.

### Migration / Compatibility

- `SourceCollectionPartial.notes` → `.collector_notes` rename: 본 모델은
  v0.4.0 신규라 영속 데이터 없음. 호환성 영향 없음.
- 기존 BaseLLMWorker 하위 클래스에서 `clean_scratch_on_start` 를 명시하지
  않으면 기본 True 가 적용 — 이전엔 잔존물 보존이었지만 v0.4.1 부터는
  ephemeral. 의도적 잔존물 활용 worker 가 있으면 클래스 변수로 `False` 명시.
  현재 agent 모드 worker 가 0 개이므로 실 영향 없음.

---

## [v0.4.0] — 2026-05-22

LLM-AP-003 의 본격 sandbox/scratch dir 격리 도입 — codex agent 모드의 CLI
매핑을 안전한 형태로 변경하고, Phase 5 `source_collector_worker` 의 출력 모델
(`SourceCollectionPartial`) 을 선행 정의. 본 PATCH 는 CLI 매핑 변경 + 헬퍼
신설 + 도메인 모델 추가에 해당해 **MINOR** 증분.

### Added

- **`workers/base_llm_worker.py:BaseLLMWorker._scratch_dir_for_task`** — agent
  모드 codex CLI 의 `--cd` 대상 디렉토리. `projects/{pid}/scratch/{task_id}/`
  를 mkdir(parents=True, exist_ok=True) 로 생성하고 반환. agent 가 본 디렉토리
  밖으로 write 하지 못하도록 `--sandbox workspace-write` 와 함께 사용.
- **`schemas/models.py:SourceCollectionPartial`** — Phase 5 의
  `source_collector_worker` 단일 task 출력 모델. project_id / task_id /
  input_item_id (Optional) / collected_sources (list[SourceEntry]) / notes
  필드. 추가는 optional 모델 신설이므로 `schema_version` 1 유지 (C3 준수).

### Changed

- **`workers/base_llm_worker.py:CLI_INVOCATION`** — codex agent 엔트리에
  `--sandbox workspace-write` 추가. `--cd` 인자를 `{project_dir}` → 새
  placeholder `{scratch_dir}` 로 변경. response 모드는 영향 없음 (entry
  자체가 `--cd` / `--sandbox` 를 갖지 않음).
- **`workers/base_llm_worker.py:_invoke_llm`** — placeholder 치환 시
  `llm_mode == "agent"` 인 경우에만 `{scratch_dir}` 를
  `_scratch_dir_for_task(args)` 결과로, response 모드는 빈 문자열로 치환.
  agent 모드 templates 가 본 placeholder 를 갖지 않으면 빈 문자열로도 안전.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-003** — mitigation /
  regression_test / resolved / 상태 / 알려진 한계 절 갱신. status 는
  `resolved-partial` 유지하되 partial 의 의미가 "sandbox 매핑까지 마련,
  실 호출하는 worker 도입은 Phase 5" 로 이동.

### Rationale

LLM-AP-003 의 v0.2.5 (opt-in 가드) / v0.3.3 (envelope 헬퍼) 다음 단계.
agent 모드의 prompt injection 면적을 줄이는 세 번째 layer: OS 레벨 sandbox
+ 파일시스템 격리. Phase 5 의 `source_collector_worker` 가 들어와야 실
효과를 실증할 수 있지만, CLI 매핑과 헬퍼는 worker 보다 먼저 박혀 있어야
worker 가 일관된 sandbox 가정 위에서 동작할 수 있다.

`SourceCollectionPartial` 도 같은 맥락 — Phase 5 worker 를 짤 때 출력 모델이
schema 에 미리 있어야 한 PATCH 안에서 worker + 모델을 동시에 도입하지 않아도
된다 (작은 단위 커밋 원칙 C8.2).

### Testing

- `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
- 기존 단위 테스트 83 케이스 모두 통과 (회귀 없음).
- 새 코드 경로의 회귀 테스트는 Phase 5 의 `source_collector_worker` 도입과
  함께 추가 예정 — 본 v0.4.0 은 CLI 인자 정적 정합성과 헬퍼 mkdir 의 부수
  효과만 다루므로 단위 테스트만으로는 실 효과 검증이 제한적.

### Migration / Compatibility

- 사용자 머신의 codex CLI 가 `--sandbox` 플래그를 지원해야 한다 (rust 구현 기준
  현재 버전 대다수 지원). 미지원 codex 는 agent 모드 호출 시 unknown flag
  로 비0 종료 → `_invoke_llm` 의 H1 로깅 후 `LLMSubprocessError`. 호출자가
  분기 가능.
- 기존 agent 모드 worker 가 `{project_dir}` 안의 자료를 prompt-time 에 직접
  파일로 읽던 경우, v0.4.0 부터는 codex 가 sandbox 외부를 못 보므로 그 자료를
  `build_user_prompt` 안에서 텍스트로 inline (가급적 `wrap_untrusted` 로
  격리) 해야 한다. 현재 agent 모드를 opt-in 한 worker 는 0 개이므로 실
  마이그레이션 영향 없음.

---

## [v0.3.4] — 2026-05-22

codex 외부 리뷰 절차의 **역할 분담을 규칙으로 박음**. 트리거 시점에 AI 어시스턴트가
`review-prompt.txt` 본문을 직접 생성하고, 사용자가 codex 실행 + 결과 paste 만 수행하도록
명문화. AI 가 절차를 *안내만* 하고 사용자 요청을 기다리는 형태도 위반으로 정의.
본 PATCH 는 C10.3 (절차 자체 수정) 에 의해 codex review 면제.

### Changed

- **`CLAUDE.md` C10** — 새 §C10.0 "역할 분담 (변경 불가)" 추가. AI 어시스턴트 / 사용자
  각자의 책임을 표로 명시. "AI 어시스턴트는 본 절차를 임의로 생략하지 못한다" 를
  굵은 강조로 명문화. trigger 시점에 *안내만* 하는 행동도 위반으로 정의.
- **`CLAUDE.md` C10.2** — 절차 5 단계의 각 step 에 `(AI 어시스턴트 책임)` /
  `(사용자 책임)` / `(공동)` 태그를 부여. step 1 은 "AI 가 세 절을 모두 직접 채워서
  완성된 `review-prompt.txt` 를 전달" 로 재정의 (이전: 누가 채우는지 불명시).
- **`docs/REVIEW_PROMPT.md` §2** — 표준 프롬프트 템플릿 안내 직후에 "세 절의 변수
  채움은 AI 어시스턴트의 책임" / "AI 가 빈 칸을 사용자에게 떠넘기는 형태는 금지"
  를 인용 블록으로 추가.

### Rationale

v0.3.3 까지의 절차 문서는 codex review 가 "필수" 임을 명시하긴 했지만, 누가
프롬프트를 채우는지 / AI 가 능동적으로 절차를 시작해야 하는지가 불명확했음.
실제 사례에서 AI 어시스턴트가 MINOR 증분 직전임에도 절차를 "사용자가 직접
codex 에 paste 할 단계" 정도로만 안내하고 능동적 시작을 누락하는 일이 발생.
본 PATCH 는 이 ambiguity 를 닫음 — AI 어시스턴트의 비결정적 안내가 아니라
**의무로 박힌 행동** 으로 전환.

---

## [v0.3.3] — 2026-05-22

LLM-AP-003 후속 사전 작업. `<untrusted_source>...</untrusted_source>` envelope 헬퍼
도입 — 순수 함수 + 회귀 테스트만. Phase 4 의 `source_collector_worker` (agent 모드)
가 외부 자료를 prompt 에 넣을 때 사용 예정. 본 PATCH 는 코드 동작 변경 없음 (헬퍼
신설만, 호출하는 worker 는 아직 없음).

### Added

- **`workers/prompt_safety.py:wrap_untrusted`** — 외부 자료를 `<untrusted_source>`
  envelope 으로 안전하게 wrap 하는 순수 함수. content / source_label 안의 동일 envelope
  태그 토큰 (`<untrusted_source>` / `</untrusted_source>` + case-insensitive /
  whitespace-tolerant 변형) 을 명시적 escape 마킹으로 치환해 LLM 이 envelope 경계를
  오인하지 않게 한다. opener 의 label 속성은 `"` / newline 도 안전화. 디스크 / 네트워크
  / subprocess I/O 없음.
- **`tests/test_prompt_safety.py`** — 5 카테고리 × 13 메소드. ① 정상 wrap 형식 / 빈
  content / label 속성 / 빈 label 생략 ② close-tag injection escape ③ open-tag injection
  + 속성 달린 open-tag escape ④ case (대문자) / whitespace 변형 escape ⑤ label 안전화
  (`"` → `&quot;`, envelope 태그 escape, newline 평탄화).

### Changed

- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` — LLM-AP-003 의 mitigation / regression_test /
  resolved 항목에 envelope 헬퍼 진전 반영. status 는 여전히 `resolved-partial` —
  sandbox 매핑 / scratch dir 격리는 Phase 4 에서 완료 예정. 알려진 한계도 sentinel
  vs sandbox 의 역할 분리 명시.

### Testing

- 단위 테스트 70 → **83 케이스** (state machine 10 + prompt safety 13 추가). 모두 통과.
- `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.

---

## [v0.3.2] — 2026-05-22

SCHEMA-AP-001 (`ProjectState` 임의 점프 / self-loop) 회귀 테스트 명시. v0.2.7 카탈로그
등록 시점부터 `pending` 으로 남아있던 부채를 청산. 코드 동작 변경 없음, 테스트만 추가.

### Added

- **`tests/test_state_machine.py`** — SCHEMA-AP-001 회귀 5 카테고리 × 10 테스트 메소드.
  ① 정상 선형 (`LinearSequenceTransitions`: `LINEAR_SEQUENCE` 의 모든 인접 페어 + str
  coerce) ② 임의 점프 거부 (`ArbitraryJumpRejected`: 정·역 양방향) ③ self-loop 거부
  (`SelfLoopRejected`: 비-archived + archived) ④ ARCHIVED 어디서든 도달
  (`ArchivedReachableFromAnywhere`: `allowed_next_states` + 실 전이) ⑤ ARCHIVED 종착성
  (`ArchivedIsTerminal`: allowed 빈 집합 + 모든 외부 전이 거부).

### Changed

- `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` — SCHEMA-AP-001 의 `regression_test` 가
  `pending` → 실제 파일 경로로 갱신. 5 카테고리·10 메소드 매핑 명시. `status: active`
  의 의미를 "감지·차단·회귀 모두 마련됨" 로 보강.

### Testing

- 단위 테스트 60 → **70 케이스** (BaseLLMWorker 22 + run 통합 8 + IntakePlanner 15 +
  인테이크 flow 15 + state machine 10). 모두 통과.
- `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.

---

## [v0.3.1] — 2026-05-21

Codex 4차 리뷰 (v0.3.0, 89f56f9 검증, Phase 3 직후) 결과 일괄 흡수 —
Critical 1 / High 3 / Medium 4 / Low 1 / Nit 1. 모두 진짜로 판정, false positive 없음.
본 PATCH 는 C10.3 self-exemption (외부 리뷰 결과 흡수 PATCH) 에 해당해 추가 review 면제.

### Fixed (외부 코드 리뷰 4차 반영)

- **(C1) `{project_id}` path traversal 차단** — `web/intake_page_app.py` 의 GET/POST 가
  raw path segment 를 그대로 `project_dir(pid)` 에 전달해 `../../etc` 같은 입력으로 `projects/`
  바깥에 접근 가능했음. `orchestrator/project_manager.py` 에 공개 가드 `validate_project_id`
  를 분리 (기존 `new_project` 의 내부 검증을 추출). web 의 `_validated_pid` 가 두 endpoint
  진입점에서 강제, CLI `plan-intake` / `submit-intake` 도 동일 가드 호출. 위반 시 400 +
  `"invalid project_id"` generic 메시지 (사용자 입력 echo 안 함, 정찰 가치 축소).
- **(H1) 404 detail 의 절대경로 누출 차단** — `FileNotFoundError` 의 원본 메시지에 절대 경로
  + 후속 명령어 예시가 포함돼 그대로 HTTP detail 로 노출됐음. 이제 generic 메시지만 클라이언트에
  반환하고 절대경로는 `logger.warning(...)` 으로 서버 측에만 기록.
- **(H2) form body 크기 상한 (`MAX_FORM_BYTES=256KiB`)** — `await request.form()` 이 무제한
  입력을 받아 DoS 가능했음. submit 핸들러가 `content-length` 헤더를 미리 검사해 초과 시 413
  + `"request body too large"` 즉시 거부. 변조된 헤더는 무시하고 starlette 내부 한도가 fallback.
  운영 튜닝/테스트용으로 모듈 변수 형태 노출.
- **(H3) `plan-intake` idempotency 보강** — 이전 흐름은 매 호출마다 worker 를 재실행해
  LLM 호출 비용 + record 누적. `intake_planning` 상태에서 유효한 `01_intake/intake_plan.json`
  이 이미 있으면 worker skip 하고 `intake_pending_user` 로 전이만 진행. 손상된 plan 은 재실행.
  `--force` 옵션으로 강제 재실행. 출력에 `skipped=True/False` 명시.
- **(M1) `submit-intake` write 와 transition 순서 역전 (CLI + Web)** — 이전 흐름은
  `source_intake.json` 을 먼저 디스크에 쓰고 `transition_state` 가 실패해도 파일이 남아 잘못된
  상태에서 덮어쓰기 가능. CLI 는 tmp write → transition → atomic rename (transition 실패 시
  tmp cleanup). Web 은 state precondition 검증 → transition → write 순으로 재배열 + 사전
  current_state 검증 (intake_pending_user 아니면 409 즉시 거부, 파일 미수정).
- **(M2) `plan-intake` 가 `task_result.json` 영속화** — `worker.run()` 직접 호출 경로가
  `BaseWorker.main` 의 표준 흐름을 우회해 task_result.json 이 안 만들어졌음. C4 의 추적성 정합을
  위해 `worker.write_result(args, result)` 명시 호출. Phase 4 의 정식 task_queue 흐름 도입
  전까지의 stopgap 이지만 PR review 와 사후 분석에서 일관된 인공물 생성 보장.

### Added (회귀 테스트)

- **(M3) IntakePlannerWorker `parse_failed` / `subprocess_error` 회귀** — 기존엔 ok /
  validation_failed 두 케이스만 cover. 본 PATCH 가 4 parsed_status 분기 전부 명시 도달.
  `tests/test_intake_planner_worker.py::TestRunParseFailed` (자연어 stub → JSONDecodeError) +
  `TestRunSubprocessError` (`_invoke_llm` monkeypatch → exit_code 7 record 영속화 검증).
- **(M4) Web negative path 회귀** — `tests/test_intake_flow.py::TestWebSecurityAndNegativePaths`
  6 케이스. (a) `..` 인코딩 PID GET/POST 거부, (b) 대문자 PID 거부 (정책 정규식), (c) 없는 PID 의
  404 generic detail (절대경로 미노출), (d) MAX_FORM_BYTES 임계치 잠시 낮춰 413 확인, (e) state
  precondition 미충족 시 POST 409 + 기존 source_intake.json bytes 보존 (M1 검증), (f) plan-intake
  의 task_result.json 영속화 (M2 검증), (g) idempotent skip 회귀 (LLM stub unset 상태에서도 worker
  미호출, llm_calls/ 미생성).

### Fixed (Nit)

- **(N1) `tests/test_intake_planner_worker.py` 코멘트 정정** — "required_items 누락 →
  IntakePlan validation 통과" 는 사실과 다름 (required_items 가 `default_factory=list` 라
  누락만으로는 위반 안 됨; 실제 실패 유발은 `unknown_extra_field` 의 `extra="forbid"` 위반).
  코멘트를 정확히 다시 작성.

### Notes

- 단위 테스트 49 → **60 케이스** (BaseLLMWorker 22 + run 통합 8 + IntakePlanner 15 + 인테이크
  flow 15). 모든 추가가 회귀 테스트로 검증.
- 본 PATCH 는 `last_synced_with` 일괄 갱신을 하지 않음 — v0.2.9 의 n9ird 컨벤션 (수정한 파일의
  헤더만 갱신) 을 따름. PATCH 범위가 코드 4 파일 + 테스트 2 파일 + 본 CHANGELOG + DEVLOG +
  HANDOFF 만 수정. 다음 MINOR (v0.4.0) 에서 다시 일괄.
- **C10.3 self-exemption**: 본 PATCH 는 외부 코드 리뷰 결과 흡수 PATCH 이므로 codex review
  의무 면제 (무한 루프 방지). 다음 외부 리뷰는 v0.4.0 MINOR 직전.
- HANDOFF.md 의 "1. 지금 어디까지 와 있나" 표에 v0.3.1 행 추가.

### Codex 4차 리뷰 미반영 항목

없음. C/H/M/L/Nit 11 항목 전부 흡수.

---

## [v0.3.0] — 2026-05-21

**Phase 3 완료 — Dynamic Intake Page + IntakePlannerWorker (첫 도메인 LLM Worker).**

C5.4 의 MINOR 트리거 두 가지 (Phase 완료 + 새 Worker 추가) 가 동시에 충족됨. Phase 2 (v0.2.0) 와
동일하게 단일 MINOR 커밋으로 Phase 의 모든 변경을 묶음.

### Added
- **`workers/intake_planner_worker.py:IntakePlannerWorker`** — 본 저장소 첫 도메인 LLM
  Worker. `BaseLLMWorker` 상속, `response_model=IntakePlan`, `llm_backend="claude"` 기본
  (인스턴스 attribute 로 `"codex"` 전환 가능), `llm_mode="response"` (외부 자료 미사용,
  `allow_agent_mode` 는 False 유지 → LLM-AP-003 우회). `system_prompt` 는 IntakePlan /
  IntakePlanItem 스키마 + IntakeMode enum 전체 값 + 출력 규칙 (JSON 한 객체, 한국어 문자열,
  `extra="forbid"`) 을 LLM 에 강제. `CATEGORY_GUIDANCE` 가 GOAL.md G2 의 5 카테고리
  (지정학·전쟁/군사·경제·정보전·자연재해/지진) 별 표준 인테이크 항목 baseline 을 보유.
  `build_user_prompt` 가 ProjectManifest 의 title/category/duration/topic_summary 를
  `.replace()` 로 치환 (CLAUDE.md C2 — `.format()` 금지 준수). `output_path` 는
  `projects/{pid}/01_intake/intake_plan.json` 로 고정.
- **`web/intake_page_app.py`** — FastAPI 기반 Dynamic Intake Page. `GET /intake/{pid}`
  가 `intake_plan.json` 을 카드 형태 HTML 폼으로 렌더 (외부 템플릿 엔진 없이 인라인 문자열 +
  `html.escape` 로 XSS 방지). `POST /intake/{pid}/submit` 가 form 데이터를 `UserDecision[]` 로
  변환 → `SourceIntake` 로 영속화 + `intake_pending_user → source_collecting` 전이.
  `GET /healthz` 배포 검증용. 추가 의존성: `fastapi>=0.110`, `uvicorn>=0.27`,
  `python-multipart>=0.0.9`.
- **CLI: `plan-intake <pid> [--backend claude|codex]`** — IntakePlannerWorker 1 회 실행 +
  `created → intake_planning → intake_pending_user` 자동 전이. Phase 4 의 자동 task_queue
  도입 전 단계라 합성 `TaskQueueItem` 을 직접 만들어 `worker.run()` 호출.
- **CLI: `submit-intake <pid> --file <path>`** — 검증된 `source_intake.json` 후보를 받아
  영속화 + `intake_pending_user → source_collecting` 전이. 웹 흐름 외에 CLI 로도 결제 가능.
  project_id 불일치 / 스키마 위반 즉시 거부.
- **`tests/test_intake_planner_worker.py`** (13 케이스) — system_prompt 스키마 안내 / IntakeMode
  enum 전체 노출 / `.format()` 비사용 검증 / 5 카테고리 CATEGORY_GUIDANCE 커버리지 / build_user_prompt
  의 manifest 필드 반영 + 미등록 카테고리 폴백 / output_path 고정 / stub mode 통합 (claude + codex
  backend 양쪽 ok / IntakePlan validation_failed 도달성).
- **`tests/test_intake_flow.py`** (6 케이스) — `plan-intake` CLI end-to-end (state 진행 + plan
  파일 생성 + state_history 두 전이 모두 기록), 실패 시 `intake_planning` 에서 멈추는지,
  `submit-intake` CLI end-to-end + project_id 불일치 거부, FastAPI `TestClient` 로
  `POST /submit` end-to-end + `GET /intake/{pid}` HTML 렌더 검증. `REPO_ROOT` 를
  `orchestrator.config` / `workers.base_worker` 양쪽 모두 임시 디렉토리로 monkeypatch
  해 실제 `projects/` 를 건드리지 않음.

### Changed
- **`orchestrator/main.py`** 에 `plan-intake` / `submit-intake` 서브커맨드 추가. `_cmd_plan_intake`
  / `_cmd_submit_intake` 헬퍼 분리. `SourceIntake` import 추가, `manifest_intake_path` 헬퍼 도입.
- **`requirements.txt` / `pyproject.toml`** 에 FastAPI 의존성 3 종 추가. 기존 pydantic v2 +
  textual 등은 변경 없음.
- **`docs/03_AGENT_ARCHITECTURE.md`** Agent 카탈로그 §2 의 Dynamic Intake Planner 행을
  `agents/dynamic_intake_planner.py` → `workers/intake_planner_worker.py (BaseLLMWorker)` 로 갱신.
  Worker 카탈로그 §3 에 Intake Planner 행 추가 (Phase 3, slot 1개, LLM 호출이므로 parallelizable
  ❌ 표기 — Worker Slot Manager 가 별도 slot 으로 격리할지는 Phase 4 결정 사항).
- 모든 Tier 1·2·3 마크다운/HTML `last_synced_with: v0.2.* → v0.3.0` 일괄 갱신 (36 파일).

### Notes
- `schemas/models.py` 의 IntakePlan / IntakePlanItem / UserDecision / SourceIntake 는 Phase 0 부터
  이미 정의되어 있어 본 PATCH 에서 신규 추가 없음. schema_version 1 유지.
- LLM 호출은 `BaseLLMWorker` 의 v0.2.5 견고성 보장을 그대로 상속: parsed_status 4 상태 분리,
  output_path 컨테인먼트, agent 모드 opt-in 가드, prompt/raw/record 3-파일 영속화. IntakePlanner
  는 그 위에서 도메인 system_prompt + CATEGORY_GUIDANCE 만 책임.
- 단위 테스트 총 30 → 49 케이스 (BaseLLMWorker 22 + run 통합 8 + IntakePlannerWorker 13 + 인테이크
  flow 6). DoD 의 "30+ → 35+" 초과 충족.
- v0.2.9 의 미반영 항목 중 "SCHEMA-AP-001 회귀 테스트" 는 본 PATCH 범위 외로 분리 — Phase 3 의
  intake flow 가 정상 전이 케이스를 6 케이스 추가로 cover 하지만, 임의 점프/self-loop 차단에 대한
  명시 회귀는 별도 v0.3.x PATCH 후보.
- C10.1 (MINOR 직전 codex review 1 회 필수) 은 사용자 머신에서 실행. 본 컨테이너에는 codex CLI
  미설치. 머지/태깅 직전 사용자가 `docs/REVIEW_PROMPT.md` 절차로 1 회 실행 후 결과를 본 v0.3.0
  의 후속 PATCH (v0.3.1) 로 흡수하거나 false-positive 합의.

### 알려진 한계 (Phase 4 처리 예정)
- IntakePlannerWorker 가 직접 `task_queue.json` 을 쓰지 않고 합성 task 로 한 번 호출. Phase 4 의
  `task_queue.json` 자동 생성 흐름이 도입되면 일반 worker 처럼 task slot 배정.
- LLM-AP-003 후속 (codex `--sandbox`, scratch dir, `<untrusted_source>` envelope) 은 IntakePlanner
  가 agent 모드 미사용이라 본 Phase 미해당. Phase 4 의 `source_collector_worker` 도입 전 처리.

---

## [v0.2.9] — 2026-05-20

Codex 3차 리뷰 (단일 브랜치, HEAD 78f11bb 검증) 결과 흡수 — High 1 + Medium 1 + Low 1. 새 코드 결함 (`new` defects) 만 처리, 이전 리뷰에서 v0.2.9 후보로 분리해둔 나머지 4건 (TUI reload 분기 보강, current_state 단순화, SCHEMA-AP-001 회귀 테스트, ARCHIVED 중복) 은 Codex 가 본 차에서 모두 "OK 확인" 또는 미언급으로 분류해 별도 후속.

### Fixed (외부 코드 리뷰 3차 반영)
- **(H) `_write_manifest` 의 디렉토리 fsync 실패 신호화** — v0.2.8 의 dir fsync 가 `OSError` 를 통째로 swallow 해서 durability 보장 문구와 runtime 현실이 어긋날 수 있던 문제. `logging.getLogger(__name__).warning(...)` 로 platform·errno·메시지를 포함한 경고 emit. 실패 자체는 여전히 흡수 (rename 은 이미 visible, durability 만 약화) 하되 운영자가 사후 인지 가능. 호출 측이 logging 설정 없으면 root logger 가 stderr 로 보낸다.
- **(M) `orchestrator/main.py:_print_manifest_summary` 타입 힌트** — `# type: ignore[no-untyped-def]` 우회를 제거하고 `manifest: ProjectManifest` 명시. CLAUDE.md C2 "모든 함수 시그니처 타입 힌트 필수" 정합. `from schemas.models import ... ProjectManifest` 추가.
- **(L) `_SLUG_RE` 주석 정합화** — "영문 소문자/숫자/하이픈만 허용" → "영문 소문자·숫자·하이픈·언더스코어를 허용하며, 첫 글자는 영문 소문자 또는 숫자 (선두 `-`/`_` 차단)" 로 실제 정규식 의도와 일치. 코드 독해 혼란 제거.

### Added
- `orchestrator/project_manager.py` 모듈 레벨 `logger = logging.getLogger(__name__)`. 본 저장소 첫 표준 logging 도입.

### Notes
- smoke test 신규: `os.fsync` mock 으로 dir fsync 실패 시뮬레이션 → warning 로그에 `errno=13` / `platform=posix` 포함 검증. 기존 `Path.replace` mock cleanup 회귀 동시 통과.
- 30/30 단위 테스트 회귀 통과.
- 본 PATCH 자체는 외부 리뷰 결과 흡수 PATCH 이지만 코드 변경이 작아 (3 파일, ~30 줄) C10.3 self-exemption 미적용. 머지 전 final 검증으로 다음 codex 리뷰 1 회 추가 권장.

### Codex 3차 리뷰 미반영 항목 (의도적)
- 이전 리뷰 M ("TUI reload PermissionError 분기"): 3차 Codex 가 "분리 명확, 외곽 tick except 로 집계됨" 으로 OK 분류.
- 이전 리뷰 M ("current_state 대입 단순화"): 3차 Codex 가 "ProjectState → str 처리 적절" 로 OK.
- 이전 리뷰 M ("SCHEMA-AP-001 회귀 테스트"): 3차 Codex 도 동일 지적, 다만 본 PATCH 범위에서 분리해 Phase 3 진입 전 별도 PATCH 후보.
- 이전 리뷰 L ("ARCHIVED 중복 표현"): 3차 Codex 미언급. 코스메틱.
- 이전 리뷰 L ("CLAUDE.md C5.2 해석 충돌"): 거버넌스 논의 후보. 본 PATCH 범위 외.

---

## [v0.2.8] — 2026-05-20

Codex 2차 리뷰 (3-way 통합 검수) 의 High 2건 중 코드 측 H2 반영. H1 은 절차 이슈로 별도 처리.

### Fixed (외부 코드 리뷰 2차 반영 — codex `exec review` H2)
- **`_write_manifest` durability + 예외 안전 보강** — v0.2.7 의 atomic write 는 visibility (rename atomicity) 만 보장했고, 전원장애·강제종료 시 마지막 write 유실 가능성이 있었음. tmp write 직후 `flush()` + `os.fsync(fd)` 로 데이터의 디스크 도달을 보장하고, rename 직후 부모 디렉토리 `os.fsync(dir_fd)` (POSIX 한정, Windows 는 `O_DIRECTORY` 미지원이라 best-effort skip) 로 rename 사실까지 durable. 또한 write/replace 도중 예외 발생 시 leftover tmp 파일을 best-effort `unlink` 로 cleanup (실패해도 원본 예외만 전파).
- docstring 을 "atomic visibility" vs "durability" 로 명시적으로 분리하여 향후 reader 가 어떤 보장이 어디까지 적용되는지 명확화.

### Notes
- 본 PATCH 는 외부 리뷰 결과 흡수 PATCH 이지만 C10.3 의 자기 검증 면제는 적용 안 함 (코드 변경 있음, M/L 항목은 다음 PATCH 로 분리하기 위해 본 PATCH 만 다시 검증 가능 상태로 둠).
- 5 케이스 smoke test: 정상 happy path / `Path.replace` 실패 시 tmp cleanup 검증 / corrupt manifest → `ValidationError` / non-JSON → `JSONDecodeError`. 30/30 기존 단위 테스트 회귀 통과.
- Codex H1 (Ij1TX 원본 커밋 `ef49e49` 부재) 은 코드가 아닌 절차 이슈. Codex Cloud 에 비교 브랜치를 fetch 하도록 안내 (다음 리뷰 요청 시 `claude/start-after-handoff-Ij1TX` 명시).
- Codex M/L 항목 (TUI reload `PermissionError`/`OSError` 분기, current_state 대입 조건 단순화, SCHEMA-AP-001 회귀 테스트 추가, _SLUG_RE 주석 정합화, state_machine ARCHIVED 중복 표현, CLAUDE.md C5.2 해석 충돌) 은 다음 PATCH (v0.2.9) 또는 Phase 3 진입 전 일괄 처리 후보.

---

## [v0.2.7] — 2026-05-20

평행 브랜치 (`claude/start-after-handoff-Ij1TX`) 흡수 — SCHEMA-AP 카탈로그 + TUI 라이브 manifest 반영 + atomic write.

배경: 동일 출발점 (`v0.1.5` main) 에서 두 Claude Code 세션이 평행으로 Phase 2 를 구현. 본 브랜치 (`claude/phase-2-finalize` ← `n9ird` 베이스) 가 정본이고, Ij1TX 의 차별점 3 가지만 본 PATCH 로 가져옴.

### Added
- **`docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md`** 신설 + **SCHEMA-AP-001** 등록: `ProjectState` 임의 점프 / self-loop 전이. mitigation 칸에 `LINEAR_SEQUENCE` + `allowed_next_states` + `transition_state` 단일 진입점 + atomic write 의 4중 방어 명시.
- **TUI Job Dashboard 라이브 manifest 반영** — `orchestrator/tui_app.py:_tick_loop` 가 매 tick 마다 `load_manifest` 로 디스크 재로딩. 외부 프로세스 (`python -m orchestrator.main transition ...`) 의 상태 변경을 TUI 가 즉시 따라잡음. 변경 감지 시 Orch CLI Log 에 `state changed: A → B` 한 줄 emit.

### Changed
- **`orchestrator/project_manager.py:_write_manifest`** atomic write 화. `path.write_text` 직접 호출 → tmp 파일에 쓴 뒤 `Path.replace` 로 교체. 외부 reader (TUI 라이브 reload) 가 half-written 상태를 보는 race 차단. POSIX rename / Windows `os.replace` 모두 atomic.
- `docs/ANTIPATTERNS/README.md` SCHEMA-AP 줄을 "Phase 2부터" → "Phase 2 v0.2.7 신설, SCHEMA-AP-001~" 로 갱신.
- 모든 Tier 1·2·3 마크다운 `last_synced_with: v0.3.0 → v0.2.7` 일괄 갱신.

### Fixed
- TUI 가 외부 `transition` CLI 호출 후에도 stale state 를 표시하던 문제.
- `_write_manifest` 의 partial-write race (드물지만 atomic 미적용 시 reader 가 깨진 JSON 을 볼 수 있었음).

### Failure modes added to `_reload_manifest_state`
- `FileNotFoundError` → state=`unknown` 표시, 다음 tick 재시도.
- `JSONDecodeError` / `pydantic.ValidationError` → state=`invalid` 표시, 다음 tick 재시도. 동일 상태 진입 시에만 1 회 stderr 로그 (noise 억제).
- 모든 예외 swallow → tick loop 유지.

### Notes
- 본 PATCH 는 코드 변경이 작아 (3 파일, ~70 줄 추가) C10 self-exemption 가 아닌 정식 codex review 대상. 통합 검수 시 본 브랜치 + n9ird + Ij1TX 3-way 비교를 권장.
- 평행 브랜치 `claude/start-after-handoff-Ij1TX` 는 본 흡수 완료 후 폐기 예정.
- 단위 테스트 5 케이스 smoke (생성·atomic·전이·corrupt manifest ValidationError·non-JSON JSONDecodeError) 모두 통과.

---

## [v0.2.6] — 2026-05-20

### Added
- **CLAUDE.md C10 — 외부 코드 리뷰 (codex review) 의무화**. MINOR/MAJOR/Phase 완료 직전 codex review 1 회 실행 필수. Critical/High 흡수 후에만 버전 증분 허용. 본 절차 자체와 외부 리뷰 결과 흡수 PATCH 는 자기 검증 면제.
- **`docs/REVIEW_PROMPT.md`** 신설 (tier 2 ssot_for=codex-review-procedure). 표준 영문 프롬프트 템플릿, Windows cmd / macOS-Linux 호출 명령어, 결과 해석 가이드 (Critical/High/Medium/Low/Nit), 거짓 양성 처리 절차, 절차의 알려진 한계.
- **`HANDOFF.md`** 의 신규 세션 체크리스트에 codex review 단계 + 30 단위 테스트 통과 확인 명령 추가.

### Changed
- `HANDOFF.md` 의 "1. 지금 어디까지 와 있나" 표에 v0.2.3 / v0.2.4 / v0.2.5 / v0.2.6 행 추가, "2. 다음 작업" 절을 Phase 3 (v0.3.0 — Dynamic Intake Page + IntakePlannerWorker) 로 갱신. 알려진 antipattern 카탈로그 갱신 (LLM-AP-001/002 resolved, LLM-AP-003 resolved-partial).
- "자주 까먹는 규칙" 에 agent 모드 opt-in, codex review 의무, parsed_status 4 상태, exit_code Optional, output_path 컨테인먼트 항목 추가.

### Notes
- 본 PATCH 는 거버넌스 강화 + 다음 세션 인계 정리. 코드/스키마/테스트 변경 없음.
- C10.3 의 self-exemption 에 의해 본 PATCH 자체에는 codex review 를 돌리지 않음.

---

## [v0.2.5] — 2026-05-20

### Fixed (외부 코드 리뷰 1차 반영 — codex `exec review`)
- **(H1) 비0 종료 stdout 보존** — `LLMSubprocessError` 에 `stdout`/`stderr`/`exit_code` 첨부. CLI 가 비0 으로 종료해도 stdout 부분이 `raw.txt` 에 영속화되어 postmortem 가능.
- **(H2) Timeout stdout/exit_code 보존** — `subprocess.TimeoutExpired.stdout/stderr` 를 동일 경로로 보존. `exit_code=None` 으로 "미완료" sentinel 기록.
- **(H3) `parse_failed` 도달 가능** — `model_validate_json` 대신 `json.loads` → `model_validate(dict)` 2 단계로 분리. JSON 파싱 실패와 schema 위반이 별도 `parsed_status` 로 기록.
- **(H4) `LLMCallRecord` 항상 영속화** — `run()` 전체를 `try/finally` 로 감싸 어떤 예외 경로에서도 record/prompt/raw 3 파일이 디스크에 남음. output write 실패 시에도 record 의 `error_message` 에 기록.
- **(H5) `output_path` 컨테인먼트 검증** — `_validate_output_path` 헬퍼 추가. project_dir 밖이면 거부, `task.output_refs` 가 비어있지 않으면 그중 하나와 일치해야 함. CLAUDE.md C4 "writes only own output_refs" 의 코드 단 가드.
- **(M1) claude wrapper subtype 엄격화** — `type=="result"` 인데 `subtype != "success"` 면 `LLMSubprocessError` raise (이전 pass-through 였음 → `validation_failed` 로 흡수돼 원인 추적 어려웠음).

### Added
- **(H6 / LLM-AP-003) agent 모드 opt-in 가드** — `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False`. `llm_mode="agent"` worker 가 `allow_agent_mode=True` 를 명시 선언하지 않으면 LLM 호출 전 즉시 `TaskResult(FAILED)`. prompt injection 면적 축소의 1 단계 가드. 본격 sandbox (CLI `--sandbox`, scratch dir) 는 Phase 3+ 후속.
- **(M3) `tests/test_base_llm_worker_run.py`** 신설 — 4 `parsed_status` 케이스 (ok / parse_failed / validation_failed / subprocess_error 2 종) + agent gate + output_path 컨테인먼트 (project_dir 밖 / output_refs 불일치) 총 8 케이스. 모든 케이스에서 prompt.txt / raw.txt / record.json 3 파일 영속화 검증.
- **(M1) `tests/test_base_llm_worker.py`** 에 wrapper subtype 검증 2 케이스 추가 (`subtype=partial`, subtype 누락).

### Changed
- **(M2) `schemas/models.py:LLMCallRecord.exit_code`** `int = 0` → `Optional[int] = None`. None = "CLI 호출 이전 실패" 또는 "timeout" sentinel. schema_version 1 유지 (호환 변경).
- `LLM_ANTIPATTERNS.md` 에 **LLM-AP-003** 신규 등록 (status=`resolved-partial`).

### Notes
- 단위 테스트 총 20 → 30 케이스 (unwrap 22 + run 통합 8). 전부 통과.
- 외부 리뷰 verdict ("방향성 OK, 추적성/상태 분류 정밀화 필요") 의 모든 High/Medium 항목 반영. Low/Nit 은 모두 OK 확인 항목이라 변경 없음.
- Phase 3 의 IntakePlannerWorker 가 BaseLLMWorker 를 상속할 때 보장되는 것: (a) record 가 어떤 실패 경로에서도 남음, (b) output_path 가 project_dir 안에 강제, (c) agent 모드는 의도적 opt-in 필요, (d) 모든 4 parsed_status 가 의미적으로 구분.

---

## [v0.2.4] — 2026-05-20

### Fixed
- **LLM-AP-002 발견 즉시 해결** — `codex exec --json` 의 stdout 은 단일 JSON wrapper 가 아니라 JSONL 이벤트 스트림 (`thread.started` / `turn.started` / `item.completed` / `turn.completed`). 도메인 응답은 마지막 `item.completed` 의 `item.type=="agent_message"` 의 `text` 필드. `_unwrap_codex_response` 가 JSONL 을 순회하며 마지막 agent_message 의 text 를 추출하고, markdown fence 가 끼면 `_extract_json_block` 으로 한 번 더 벗긴다.

### Changed
- `workers/base_llm_worker.py:CLI_INVOCATION` 의 codex 매핑 보강:
  - `--skip-git-repo-check` 추가 (project_dir 이 .git 아닐 수 있음)
  - `--color never` 추가 (ANSI 코드 안전장치)
  - agent 모드는 `--cd {project_dir}` 유지
- 검증 환경: codex-cli 0.130.0 (Windows cmd). 실제 한 줄 호출 캡쳐를 fixture 로 보존.

### Added
- `tests/test_base_llm_worker.py::TestUnwrapCodexResponse` 8 케이스 — 실 캡쳐 / markdown fence / 다중 agent_message / tool_call 등 미지 item type 무시 / agent_message 없음 → `LLMSubprocessError` / 단일 JSON pass-through / non-JSONL pass-through / 빈 입력. 총 단위 테스트 13 → 20 케이스.
- `LLM_ANTIPATTERNS.md` 에 **LLM-AP-002** 신규 등록 (status=resolved, 발견 즉시 해결).

### Notes
- 알려진 한계: 다중 turn / `--output-schema` / `--output-last-message` 같은 더 견고한 codex 옵션은 도입하지 않음 (단순성 우선). Phase 3 에서 schema 강제 도입 재검토.
- 본 fix 로 v0.2.2 시점의 "codex 는 별도 후속" 항목이 해소됨. Phase 3 의 IntakePlannerWorker 가 backend 를 claude/codex 어느 쪽으로 설정해도 BaseLLMWorker 가 정상 동작.

---

## [v0.2.3] — 2026-05-20

### Fixed
- **LLM-AP-001 구조적 조치** — `BaseLLMWorker` 가 `claude -p ... --output-format json` 의 wrapper (`{type:result, subtype:success, result:"...", ...}`) 를 벗긴 뒤 `response_model.model_validate_json` 을 호출하도록 변경. wrapper `is_error=True` 면 `LLMSubprocessError` 로 변환. `result` 문자열 안의 markdown code fence (```` ```json ... ``` ````) 도 자동 제거.
- `raw.txt` 영속화는 unwrap 전 stdout 그대로 유지 → 디버깅 추적성 보존.

### Added
- `tests/__init__.py`, `tests/test_base_llm_worker.py` — 13 케이스 단위 테스트 (extract_json_block 5 / claude wrapper 7 / codex pass-through 1). `python -m unittest tests.test_base_llm_worker` 통과.
- `workers/base_llm_worker.py` 에 모듈 레벨 헬퍼: `_unwrap_claude_response`, `_unwrap_codex_response`, `_extract_json_block`. `BaseLLMWorker._unwrap_response(raw)` 가 `self.llm_backend` 로 dispatch.

### Notes
- codex CLI wrapper 는 v0.2.3 시점 미검증 → pass-through. 실제 호출 가능 환경 확보 후 별도 작업 (LLM-AP-002 후보) 으로 분리.
- LLM-AP-001 status `active` → `resolved`.

---

## [v0.2.2] — 2026-05-20

### Added
- **`workers/base_llm_worker.py:BaseLLMWorker` 코드 도입** (ADDENDUM_04 §4 의 정식 구현).
  - 클래스 변수: `llm_backend ∈ {"claude", "codex"}`, `llm_mode ∈ {"response", "agent"}`, `system_prompt`, `response_model`.
  - 추상 메서드: `build_user_prompt(args, task)`, `output_path(args, task)`.
  - `_invoke_llm` 가 backend/mode 별 `CLI_INVOCATION` 매핑으로 subprocess 호출. `FileNotFoundError` / `TimeoutExpired` / 비0 종료 모두 `LLMSubprocessError` 로 흡수.
  - `OSINT_LLM_STUB=1` + `OSINT_LLM_STUB_RESPONSE` 환경변수로 실 CLI 우회 (smoke test 전용).
  - 전 호출이 `projects/{pid}/llm_calls/{call_id}.{json,prompt.txt,raw.txt}` 3 파일로 영속화.
- `schemas/models.py` 에 `LLMCallRecord` Pydantic 모델 추가. `parsed_status ∈ {"ok", "parse_failed", "validation_failed", "subprocess_error"}`.
- `workers/dummy_llm_worker.py` 신설 (`DummyLLMResponse` 응답 모델 포함). smoke test 전용.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 의 첫 항목 **LLM-AP-001** 등록 — `claude -p ... --output-format json` 응답이 wrapper JSON (`type/subtype/result/usage/uuid` 등) 으로 감싸여 있어 그대로는 도메인 Pydantic 모델 검증 통과 안 함. 구조적 조치 v0.2.3 patch.

### Changed
- `docs/ADDENDUM_04 §4` 인트로를 "v0.2.2 코드 도입 완료" 로 갱신, §8 #1 미결 항목을 LLM-AP-001 으로 구체화.

### Notes
- smoke test 4 케이스 (정상 stub / 잘못된 JSON / 스키마 위반 / 실 claude CLI) 모두 의도대로 동작. LLMCallRecord 4건 영속화 확인.
- `BaseLLMWorker` 는 새 Worker 베이스이므로 C5.4 의 MINOR 사유 ("새 Worker 추가") 에 해당. MINOR 0.2.1 → 0.2.2.

---

## [v0.2.1] — 2026-05-19

### Added
- **Subscription LLM Bridge 패턴 정식 문서화** — 본 시스템은 LLM API 키를 사용하지 않고, 사용자가 이미 구독 중인 `claude` (Claude.ai) 와 `codex` (ChatGPT Plus/Pro) CLI 를 subprocess 로 자동 호출한다는 핵심 아키텍처 결정 정립.
- `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설. GOAL.md G4 와 동등한 강제력으로 운용. `BaseLLMWorker` 인터페이스 명세, 호출 모드 (`response` / `agent`), 백엔드 선택 가이드, 추적성 (`projects/{pid}/llm_calls/{call_id}.json`), 에러 모드 정의.
- `docs/03_AGENT_ARCHITECTURE.md` §4.5 에 `BaseLLMWorker` 계약 요약 추가. §4 베이스워커 안내문에 "LLM 호출은 `BaseLLMWorker` 상속 필수" 명시.
- `CLAUDE.md` C6 안티패턴 카테고리에 `LLM-AP-N` 추가.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 골격 신설 (항목은 Phase 3 첫 실 호출부터 누적).
- `docs/ANTIPATTERNS/README.md` 인덱스에 `LLM-AP` 행 추가.

### Notes
- 본 변경은 **G4 본문은 건드리지 않는** PATCH. ADDENDUM_04 가 G4 와 동등한 강제력을 갖도록 본문에 명시. v1.0.0 시점에 G4 #13 으로 정식 흡수 (MAJOR 증분).
- 코드 변경 없음. `BaseLLMWorker` 코드는 v0.2.2 patch 또는 Phase 3 시작 시점에 도입.

---

## [v0.2.0] — 2026-05-19

### Added
- **Phase 2 완료: Project Manager / State Machine**.
- `orchestrator/state_machine.py` 신설. `LINEAR_SEQUENCE` 가 docs/02 §4 의 24개 상태 선형 흐름을 SSOT 로 보유. `allowed_next_states` / `validate_transition` 순수 함수 제공.
- `orchestrator/project_manager.py` 신설. `project_manifest.json` 의 유일한 쓰기자. `new_project` / `resume_project` / `transition_state` 공개 API.
- `schemas/models.py` 에 `StateTransition` 모델 추가, `ProjectManifest.state_history` (append-only) 필드 추가. schema_version 은 1 유지 (optional 필드 추가).
- CLI 명령 `new-project <pid> --title ... --category ... [--duration-min] [--topic-summary]`, `resume <pid>`, `transition <pid> --to <state> [--reason]` 정식 구현.
- 전이 규칙: 선형 다음 상태 또는 `archived` 만 허용. 동일 상태 전이 / 임의 점프는 명확한 한글 메시지와 함께 `ValueError` (CLI exit=2).

### Changed
- `orchestrator/command_center.py` 가 `project_manager.load_manifest` 를 통해 manifest 를 read-only 로 로드하도록 정리. raw json 파싱 코드 제거.
- `orchestrator/main.py` 의 `new-project` / `approve` placeholder 문구 제거, 실 구현으로 교체.

---

## [v0.1.5] — 2026-05-19

### Removed
- `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에서 `test/graph-demo` 항목 삭제 (브랜치 자체가 삭제됨).
- `COMMIT_DESCRIPTIONS` 에서 `0159299` 엔트리 삭제 (해당 commit 이 도달 가능한 브랜치가 없어 dead code).

### Changed
- `test/graph-demo` 원격 브랜치 사용자 측에서 삭제 완료 (v0.1.3 그래프 분기 시각화 검증 종료).

---

## [v0.1.4] — 2026-05-19

### Added
- `docs/branches.html` 에 `COMMIT_DESCRIPTIONS` 맵 추가. 영어로 작성된 과거 커밋의 한글 설명을 SHA(앞 7자) 기준으로 override. 신규 커밋은 처음부터 한글로 작성하면 맵 갱신 불필요.
- `BRANCH_PRIORITY` + `sortBranchRefs` 헬퍼 추가. 같은 SHA 에 여러 브랜치가 가리킬 때 라벨 표시 우선순위 결정 (main → develop → release/ → feature/ → test/ → claude/ → 그 외 알파벳).
- `BRANCH_DESCRIPTIONS` 에 `test/graph-demo` 항목 추가 (임시 검증 브랜치).

### Fixed
- 같은 SHA 를 두 브랜치가 가리킬 때 `main` 라벨이 안 보이고 부차 브랜치 라벨만 보이던 문제 수정. (`sortBranchRefs` 가 main 을 항상 앞에 배치)

---

## [v0.1.3] — 2026-05-19

### Added
- `HANDOFF.md` (Tier 1) 신설. 다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 인계 문서. 현재 상태, Phase 2 후보, 체크리스트, 자주 까먹는 규칙 정리.
- `docs/branches.html` 에 `@gitgraph/js` (jsDelivr CDN) 통합. 모든 브랜치를 단일 SVG git graph 로 렌더. 브랜치가 갈라지면 자동으로 가지 그림이 나옴.
- 사이드 패널이 등록되지 않은 브랜치를 자동 감지해서 "설명 미등록" 경고 카드로 노출 (한글).

### Changed
- `docs/branches.html` 의 데이터 모델을 commit-graph 중심으로 재작성. 브랜치별 commit 을 전역 SHA 맵으로 통합, parents 필드 활용해 토폴로지 보존. 모든 브랜치 commit fetch 병렬화 (`Promise.all`).

---

## [v0.1.2] — 2026-05-19

### Added
- `docs/index.html` 추가. 루트 URL (`/`) 접근 시 `/branches.html` 로 즉시 리다이렉트 (meta-refresh + JS 양쪽).

### Fixed
- Vercel 배포에서 루트 URL 이 `404: NOT_FOUND` 를 반환하던 문제 수정. `vercel.json` 의 `rewrites` 룰이 `outputDirectory: "docs"` 와 함께 쓰일 때 안정적이지 않아 실제 `index.html` 파일로 대체.

### Changed
- `vercel.json` 에서 `rewrites` 블록 제거 (정적 `index.html` 로 충분).

---

## [v0.1.1] — 2026-05-19

### Added
- `vercel.json` 루트 추가. Vercel 로 `docs/` 정적 호스팅 (Private 저장소 호환). 푸시마다 자동 재배포.
- `docs/branches.html` 에 Personal Access Token 입력 다이얼로그 추가. 토큰은 브라우저 localStorage 에만 저장. Private 저장소 GitHub API 호출에 사용.
- README 에 Vercel 설정 절차 + PAT 발급 절차 안내.

### Changed
- GitHub default branch 가 `main` 으로 통합됨에 따라 로컬 브랜치도 `main` 으로 rename, `branches.html:BRANCH_DESCRIPTIONS` 도 갱신.
- `branches.html:loadVersion` 이 raw.githubusercontent.com 대신 `/contents/VERSION` API 를 사용하도록 변경 (Private 저장소에서도 Bearer 인증으로 동작).
- 모든 Tier 1·2·3 마크다운/HTML 의 `last_synced_with: v0.1.0 → v0.1.1` 동기화.

### Fixed
- 없음 (Phase 1 PIPELINE-AP-006 은 v0.1.0 안에서 fix 됨).

---

## [v0.1.0] — 2026-05-19

### Added
- 저장소 초기화 (Phase 0)
- Tier 1 거버넌스 문서: `README.md`, `GOAL.md`, `CLAUDE.md`, `DOCS_GOVERNANCE.md`
- Tier 3 운영 문서: `CHANGELOG.md`, `DEVLOG.md`, `WORKFLOWS.md`
- Tier 2 스펙 문서 19종 (`docs/00_~16_`, `docs/ADDENDUM_01~03`)
- Antipattern 카탈로그 골격 (`docs/ANTIPATTERNS/README.md`, `TTS_ANTIPATTERNS.md`, `PIPELINE_ANTIPATTERNS.md`)
- 프로젝트 스캐폴딩: `pyproject.toml`, `requirements.txt`, `config.yaml`, `run_pipeline.bat`, `.gitignore`, `.githooks/commit-msg`
- Pydantic 스키마 모듈 `schemas/models.py` (project_manifest, task_queue, worker_slot, task_result 등)
- **Phase 1 MVP**: Orchestrator Command Center (Textual TUI)
  - `orchestrator/command_center.py` — TUI 진입점
  - `orchestrator/tui_app.py` — Orch CLI Log + Job Dashboard + Worker Slot 4개 패널
  - `orchestrator/worker_slot_manager.py` — Worker subprocess 배정
  - `orchestrator/log_router.py` — Worker stdout/stderr 라우팅
  - `orchestrator/dashboard.py` — 작업 현황 집계
  - `orchestrator/config.py` — config.yaml 로더
  - `workers/base_worker.py` — Worker CLI 공통 베이스
  - `workers/dummy_worker.py` — Phase 1 검증용 더미 워커
- 데모 프로젝트 `projects/demo/`와 4개 dummy task가 포함된 `task_queue.json`
