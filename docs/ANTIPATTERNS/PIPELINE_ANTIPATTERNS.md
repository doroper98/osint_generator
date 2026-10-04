<!--
tier: 3
last_synced_with: v4.0.0
ssot_for: [pipeline-antipatterns]
depends_on: [../02_SYSTEM_ARCHITECTURE.md, ../ADDENDUM_01_ORCHESTRATOR_COMMAND_CENTER_LAYOUT.md]
last_review: 2026-05-19
-->

# Pipeline Antipatterns

본 문서는 Orchestrator·Worker·Task Queue·Log Router 관련 안티패턴 카탈로그입니다. **append-only**.

각 항목은 [README.md](README.md)의 표준 포맷을 따릅니다.

---

## PIPELINE-AP-001 — Worker가 사용자에게 직접 stdin으로 질문
- **증상**: Worker subprocess가 `input("계속하시겠습니까?")`를 호출 → TUI가 멈춤.
- **나쁜 예**: `confirm = input(...)`
- **좋은 예**: `TaskResult(status="needs_user_confirmation", warnings=["..."])` 반환.
- **자동 조치**: `workers/base_worker.py`가 stdin을 `/dev/null`로 묶어 차단. CI lint로 `input(` 패턴 검사.
- **회귀 테스트**: pending
- **발견 버전**: v0.1.0
- **상태**: active

## PIPELINE-AP-002 — Worker가 task_queue.json을 직접 갱신
- **증상**: Worker가 자기 자신의 status를 task_queue.json에 직접 쓴다 → Orchestrator의 단일 쓰기자 원칙 깨짐.
- **좋은 예**: Worker는 `task_result.json`만 작성. Orchestrator가 task_queue.json을 동기화.
- **자동 조치**: `task_queue.json`은 Orchestrator 프로세스만 쓰기. base_worker가 의도적 검증.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-003 — Worker subprocess hang 시 stale 미감지
- **증상**: 외부 API 호출이 무한 대기하면 Worker Slot이 영원히 running.
- **좋은 예**: heartbeat timeout (config: `command_center.heartbeat_timeout_sec`, 기본 60초) 후 `stale` 전환 + 재배정 옵션.
- **자동 조치**: Worker Slot Manager의 polling.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-004 — depends_on 순환 의존
- **증상**: task A가 B에 의존, B가 A에 의존 → 영원히 queued.
- **자동 조치**: `task_queue.json` 로드 시 토폴로지 정렬로 사이클 검출. 사이클이면 즉시 fail.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-005 — Log Router 패널 버퍼 무제한 증가
- **증상**: 긴 작업의 로그가 TUI 메모리를 잠식.
- **자동 조치**: `command_center.log_panel_max_lines` (기본 500)로 ring buffer.
- **회귀 테스트**: pending · **발견 버전**: v0.1.0 · **상태**: active

## PIPELINE-AP-006 — Worker Slot finalize 시 terminal 상태 잔존
- **증상**: Worker subprocess 종료 후 slot 상태를 `completed` / `failed` / `waiting_user` 로 두면, 다음 tick 에서 `_find_idle_slot()` 이 None 을 반환하여 후속 task (예: `depends_on` 가 충족된 task) 가 영영 `queued` 로 남는다.
- **나쁜 예**: finalize 시 slot.status 를 `completed`로 유지.
- **좋은 예**: finalize 직후 즉시 `idle` 로 환원. "지금 누가 일하는가" 는 `worker_slots.json`, "누가 무엇을 끝냈는가" 는 `task_queue.json` 으로 책임 분리.
- **자동 조치**: `orchestrator/worker_slot_manager.py:_finalize_slot` 에서 slot.status = `idle` 즉시 적용. 마지막 worker 정보는 stdout 로그가 보존.
- **회귀 테스트**: `tests/orchestrator/test_worker_slot_manager.py::test_chained_depends_on` (Phase 1 후속에서 추가)
- **발견 버전**: v0.1.0 (Phase 1 smoke test 중)
- **상태**: active

## PIPELINE-AP-007 — LLM 출력 저장 전 점검이 렌더 경로와 달라 정상 연출을 거부
- **증상**: hormuz_ai 첫 AI 연출에서 `place:` 슬롯으로 둔 뱃지가 "lon/lat 필수" 오류로 거부되고, 연출가에게 틀린 재요청이 갔다.
- **원인**: `workers/direction_io.check_direction` 이 `place` 를 버리고 모델 검증만 했다. 렌더 입력(`engine.project.load_project`)은 슬롯을 좌표로 푼 뒤 검증한다.
- **좋은 예**: 저장 전 점검 = 렌더와 **같은 함수**. `load_project(proj, direction=doc)` 로 슬롯·레지스트리·엔티티·예약영역·권리를 한 번에.
- **자동 조치**: check_direction 이 load_project 를 호출(v3.1.0).
- **회귀 테스트**: `tests/test_placement_slots.py::CheckDirectionPlaceTest`
- **발견 버전**: v3.1.0 (Phase 6.9 작업 10 실측) · **상태**: active

## PIPELINE-AP-008 — 불변 검사의 지적 표지 형식 불일치로 정당한 수정을 거부
- **증상**: 검수가 지적한 `clip:strikes`·`badge:이재명` 을 고친 연출 수정본이 "지적 없이 변경"으로 두 번 거부, 검수 루프가 0회 수정으로 멈춤.
- **원인**: 표지 `badge:이재명` 과 키 `badge|person|이재명|{앵커}` 를 부분 문자열로 비교했다. 컷 표지 `p_0136.97` 는 어떤 이벤트에도 닿지 않았다.
- **좋은 예**: 표지를 이벤트로 **해석**한다 — 타입:이름, 컷 → frames.json 활성 이벤트, 검사 id → 상세 문장 속 이름(`engine.qa.resolve_refs`).
- **교훈**: 계약 검사는 LLM 이 실제로 받는 표지 형식(프롬프트 예시)으로 단위 테스트한다. 스텁 워커 테스트만으로는 못 잡는다.
- **회귀 테스트**: `tests/test_qa_models.py` (event_ref·frame·checks id 3건)
- **발견 버전**: v3.1.0 (Phase 6.9 작업 10 실측) · **상태**: active

## PIPELINE-AP-009 — 검수 입력(frames.json)이 끝난 문장을 "진행 중"으로 적어 거짓 hard
- **증상**: taiwan_ai AI 연출(NB11)에서 엔딩 카드 컷(t=16.2)을 시각 검수가 "문장이 진행 중인데 크레딧으로 바뀌었다" order hard 2건으로 판정. 실제 문장은 9.4초에 끝났다.
- **원인**: `frames_info` 가 `cur_sentence(t)`(마지막으로 **시작한** 문장)를 sid 로 적었다. 문장이 끝난 뒤에도 sid·text 가 남는다.
- **좋은 예**: sid = 그 순간 읽는 중인 문장만. 끝난 뒤는 `after_sid`, 전면 카드는 `card`. 프롬프트에 필드 뜻을 적는다.
- **교훈**: LLM 검수의 hard 는 입력 메타데이터가 틀려도 나온다 — 판정이 흔들릴 때 입력부터 본다.
- **회귀 테스트**: `tests/test_checks.py::ChecksTest::test_frames_sid_only_while_speaking`
- **발견 버전**: v3.2.0 (Phase 6.95 NB11 실측) · **상태**: active

## PIPELINE-AP-010 — 긴 실행 중 같은 워크트리의 코드·규칙을 고쳐 실행이 반쯤 바뀐 코드를 읽음
- **증상**: Phase 10 에서 두 번. ① 480p 전편 렌더 1회차가 청크 실패로 끝났다 — 실행 중 엔진 코드를 고쳤고, 늦게 import 하는 청크 프로세스가 반쯤 바뀐 모듈을 읽었다. ② 랫클리프 AI 연출 재실행이 판 없이 멈췄다 — 실행 중 규칙(`golden`)을 옮겨, 이미 떠 있던 프로세스의 옛 스키마가 새 규칙 파일을 거부했다.
- **원인**: 청크 병렬 렌더·AI 연출 루프는 수 분~수십 분 동안 **서브프로세스를 새로 띄우며** 저장소 파일(코드·`rules/video_rules.yaml`)을 그때그때 읽는다. 같은 워크트리를 고치면 한 실행 안에서 옛 판과 새 판이 섞인다.
- **좋은 예**: 긴 실행은 고정된 워크트리에서 돌리고, 개발은 `git worktree add` 로 만든 별도 트리에서 한다. 실행 기록에 시작 커밋을 적는다.
- **교훈**: 실패가 재현되지 않으면 코드보다 먼저 "실행 중에 트리가 바뀌었나"를 본다(Phase 10 run_log §4, 단독 재실행 정상).
- **자동 조치**: 없음(운영 규칙). HANDOFF §5·docs/15 §2.3 에 규칙으로 적었다. regression_test: pending
- **발견 버전**: v3.6.0 (Phase 10 run_log §4) · **상태**: active

## PIPELINE-AP-011 — 같은 ISO 키의 국가 피처를 덮어써 나라가 바다로 그려짐(카자흐스탄)
- **증상**: 랫클리프 480p(Phase 10 v2) 모스크바 컷에서 서카자흐스탄 전역이 바다 색. hormuz W 티어(골든 25컷 포함)도 같은 결함 — KZ 는 바이코누르 조각, AU 는 애시모어·카르티에 조각만 남았다. 사용자 지적 "프랑스 때와 같은 현상".
- **원인**: `geo/prep_geometry.load_countries` 가 `G[ISO_A2_EH] = 피처` 로 넣어 **같은 키의 뒤 피처가 앞 피처를 덮어썼다**(KZ = Kazakhstan → Baykonur Cosmodrome, FR = France → Clipperton, BR·AU 부속 영토). v3 `prep3.py` 부터 있던 방식. 커버리지 검사는 G 의 대표점 한 점만 찍어 덮어쓴 작은 조각 위에서 통과했다.
- **좋은 예**: 같은 키 피처는 합집합(`unary_union`), META 는 면적이 큰 피처. 커버리지는 G 와 따로 만든 원본 합집합 영역 안의 **육지 화소 비율**로 본다(`rules geo.land_fill_min_ratio`) — 대표점 한 점이 아니라 면적.
- **교훈**: 검사기가 검사 대상(G)에서 표본을 뽑으면 G 가 틀린 경우를 못 잡는다. 기준은 조립 경로와 독립이어야 한다. 04 §3.3 의 "프랑스 버그" 도 평탄화만이 원인이 아니었을 수 있다.
- **자동 조치**: `geo.prep_tiers.fill_ratios`(면적 커버리지, 미달 = land-miss → drops), `geo_report.json` `country_area_deg2`·`fill_ratio`.
- **회귀 테스트**: `tests/test_geo_key_collision.py`(픽스처 KZ·바이코누르, 실데이터 충돌 키 전부 합집합)
- **발견 버전**: v4.1.0 (사용자 보고, back_and_forth D-0078) · **상태**: active

## PIPELINE-AP-012 — 검증 단계가 파일을 먼저 쓰고 결과 모델 검증에서 예외로 죽음(drops 있는 ok)
- **증상**: `verify-sources` 에서 근거 인용 하나만 버려져도(본문 불일치·상한 초과) CLI 가 트레이스백으로 끝났다. 그런데 `intake/claims.json`·`sources.json` 은 이미 새로 써져 있었다 — 실패인데 산출물이 남는다.
- **원인**: `orchestrator/source_verify.apply_draft` 가 파일을 쓴 뒤 `StageResult(ok=True, drops=[…])` 를 만들었다. `StageResult` 는 "drops 가 있으면 ok 일 수 없다"(15 P6)를 검증기로 막는다 → ValidationError. 테스트는 drops 없는 판정과 전부 폐기(ok=False) 판정만 다뤄 "일부 폐기" 길을 밟지 않았다. G11(v5.0.0) statement 의 단정 인용 폐기로 이 길이 흔해져 드러났다.
- **좋은 예**: 판정 → drops 가 있으면 파일을 쓰지 않고 `ok=False` + drops 사유 + 경고로 반환(재검증 1회 감수, 사용자 결정 위임 D-0122 ① A). 파일은 성공일 때만 쓴다.
- **교훈**: 결과 모델에 불변식이 있으면 그 모델을 만드는 코드의 모든 분기(특히 "부분 실패")를 테스트한다. 부작용(파일 쓰기)은 결과가 확정된 뒤에.
- **자동 조치**: `apply_draft` drops 분기(v5.0.0 G11 §3, 7cfdef6).
- **회귀 테스트**: `tests/test_g11_claim_kind.py::StatementJudgeTest::test_apply_draft_asserted_fails_with_drops_and_writes_nothing`
- **발견 버전**: v5.0.0 (G11 §3 구현 중, back_and_forth R-0143 ①) · **상태**: active

## PIPELINE-AP-013 — 검사가 라벨용 date 를 시간축 앵커로 오판해 AI 연출가를 3회 거부
- **증상**: fed_policy AI 재연출(G12 §E)에서 연출가 1~3회가 모두 "backdrop 무대의 시간축 이벤트가 차트 아일랜드 구간 밖" 오류로 거부됐다. 거부된 이벤트는 statement_diff 프리미티브였다 — 시간축에 앉지 않는 요소다.
- **원인**: `check_islands`(engine/project.py)가 이벤트에 `date` 필드만 있으면 시간축 앵커로 보았다. statement_diff 의 `date` 는 "기준 날짜" 라벨이고 `lane` 이 없다. 앵커 판정 기준을 필드 하나로 잡아 다른 뜻의 같은 이름 필드를 구별하지 못했다.
- **좋은 예**: 시간축 앵커 = `date`·`lane` 쌍. lane 없는 date 는 라벨로 본다. 연출가 거부 사유가 같은 모양으로 반복되면 LLM 보다 검사를 먼저 의심하고, llm_calls 원문과 오류 문장을 대조한다.
- **교훈**: 검사기의 오판은 LLM 재시도 비용으로 나타난다. 거부가 3회 연속이면 검사기 결함부터 본다.
- **자동 조치**: `check_islands` 앵커 판정 = date·lane 쌍(v5.1.0 G12 보정 ①, 65eda77), rules `stage_backdrop.grammar` 2줄.
- **회귀 테스트**: `tests/test_g12_island.py::WiringTest::test_timeline_events_only_inside_island`(statement_diff 라벨 date 통과·lane 있는 badge 오류)
- **발견 버전**: v5.1.0 (G12 §E fed 재연출, back_and_forth R-0148 §4·D-0127 §6) · **상태**: active

## PIPELINE-AP-014 — 콘티 판(W0)을 건너뛰고 검수 루프에서 바로 프리뷰 게이트로 감
- **증상**: hormuz-talks-2026(v5.2.0) 제작에서 연출 v1~v7 과 AI 검수 루프를 돌리는 동안 콘티 판을 한 번도 만들지 않았다. 사용자가 "콘티 짜는 것도 만들어 두지 않았었나?" 로 지적한 뒤에야 렌더했다.
- **원인**: 콘티 판은 상태가 아니라 `direction` 안의 사람 루프(handoff 16 §7)라서 `advance` 가 부르지 않고, 게이트 ② 도 확인하지 않았다. 문서(WORKFLOWS W0)에만 있는 단계는 세션이 놓치면 그대로 빠진다(15 패턴 A — 만들었지만 연결되지 않음).
- **좋은 예**: 연출 판 → `audio.mix` → `engine.render --animatic` → `out/animatic.mp4` 를 사용자에게 보내 흐름 검토 → 프리뷰 → 게이트 ②.
- **교훈**: 사람 검토 단계도 코드가 선행 조건으로 확인하지 않으면 "선택 사항" 이 된다. 문서 규칙은 게이트 검사로 받친다.
- **자동 조치**: `orchestrator.project_manager.require_animatic` — 게이트 ② 승인 전에 `out/animatic_provenance.json`(animatic_run 있음, total_sec = plan.json total ± 0.05초) 확인, 없으면 `AnimaticMissingError`(우회 플래그 없음, 사용자 결정 2026-10-01). 게이트 기록 `shown.animatic`. `engine.render --animatic` provenance 에 `animatic_run.direction_sha1`.
- **회귀 테스트**: `tests/test_gates_pipeline.py::AnimaticGateTest`(없음·미완료·옛 음성 거부, 맞으면 승인·기록)
- **발견 버전**: v5.2.0 (사용자 지적 2026-10-01) · **상태**: active

---

## PIPELINE-AP-015 — 원고(자막) 검토 없이 콘티 판부터 만들어 보냄
- **증상**: kaliningrad-suwalki(v5.5.1) — 원고를 내가 다듬은 뒤 게이트 ① 승인 없이 음성·연출·콘티 판을 만들어 보냈다. 사용자 결정(2026-10-04): "콘티판 제작과 더불어서 자막(대본)에 대한 점검도 요청 — 자막 → 콘티 → (승인 후) 본영상".
- **원인**: 게이트 ① 은 상태 전이로만 있었고, 엔진 CLI(`script.plan`·`engine.render --animatic`)를 직접 부르면 건너뛸 수 있었다. 게이트 ② 는 콘티 판 존재·음성 길이만 봤지, 그 콘티 판이 승인된 원고로 만들어졌는지 보지 않았다.
- **좋은 예**: 원고 → `gate-view` 자료를 사용자에게 보내 자막 점검 → `approve --gate script_approval`(원고 지문 기록) → 음성 → 연출 → 콘티 판(원고 지문 기록) → 사용자 흐름 검토 → 프리뷰 → 게이트 ② → 본편.
- **자동 조치**: 게이트 ① 승인 `shown.script_sha1`, 콘티 판 `animatic_run.script_sha1`, `require_animatic(pdir, approved_sha1)` 이 대조 — 승인 기록 없음·지문 다름 = 게이트 ② 거부(우회 플래그 없음).
- **회귀 테스트**: `tests/test_gates_pipeline.py::AnimaticGateTest::test_script_changed_after_approval_blocks_gate2`
- **발견 버전**: v5.5.1 (사용자 지적 2026-10-04) · **상태**: active

## PIPELINE-AP-016 — 제작한 자산(초상·휘장)을 프로젝트 폴더에만 두어 다음 영상에서 다시 만듦
- **증상**: kaliningrad-suwalki 에서 나토 휘장·인물 초상 5인을 만들었지만 프로젝트 `assets/`(.gitignore)에만 있었다. 다른 영상·새 세션에서는 다시 받고 다시 가공해야 했다(위키미디어 429 로 수십 분).
- **원인**: 공용 자산 자리(`assets/library`)는 사전 구축 24인만 있었고, 프로젝트에서 만든 자산을 올리는 단계가 없었다.
- **좋은 예**: 자산을 만든 뒤 `python tools/asset_library.py promote projects/{pid}` — 초상은 라이브러리(권리 기록 동반), 휘장은 `assets/emblems/files`. 다음 영상은 라이브러리·공용 파일을 먼저 쓴다.
- **자동 조치**: `tools/asset_library.py check`(승격 안 된 자산 = exit 1), `commons_fetch emblems` 가 공용 파일 우선. 권리 기록 없는 자산은 승격하지 않는다(C9).
- **회귀 테스트**: `tests/test_asset_library.py`
- **발견 버전**: v5.5.1 (사용자 지시 2026-10-04) · **상태**: active

---

> 새 패턴 발견 시 본 파일 끝에 append. 과거 항목 수정 금지.

## PIPELINE-AP-017 — 본편을 본 뒤 원고 내용을 보강할 길이 없음(reopen 은 연출로만)

- **증상(실제 현상)**: kaliningrad-suwalki 본편(v5.6.0, 2026-10-04) 사용자 지적 — "독일의 영유권이 있던 적도 없는데 갑자기 영유권 포기 이야기가 나온다, 독일 이야기가 추가돼야". 원고가 1255년(튜턴 기사단)에서 1945년(소련군 장악)으로 건너뛰어 약 700년간 독일 도시였다는 사실이 빠졌다. 원고 2문장을 더하려 했는데 `reopen` 은 렌더 이후 → direction 만 허용해 게이트 ① 로 돌아갈 수 없었다.
- **원리**: v4.7.0 D-0104 D4 의 reopen 은 "연출 다시"만 상정했다. 게이트 ② 반려는 내용 문제로 script_draft 에 갈 수 있는데, 렌더 뒤에는 같은 길이 없었다 — 원고를 손으로 고치고 게이트 ① 을 건너뛰는 우회만 남는다(PIPELINE-AP-015 위반 유도).
- **원칙**: 렌더 뒤 내용 보강도 자막 → 콘티 → 본편 순서를 그대로 탄다. 연표의 결과(1990 영유권 포기)를 말하려면 그 전제(독일 도시였던 시기)를 먼저 말한다.
- **자동 조치**: `REOPENS` 에 script_draft 추가(`reopen --to script_draft`) → transition script_approval → 게이트 ① 재승인(새 원고 지문) → 음성 → 콘티 판(지문 대조, `require_animatic`) → 게이트 ②. 테스트 `test_g65_merge.test_reopen_rules`.
- **발견 버전**: v5.6.0 · **상태**: active
