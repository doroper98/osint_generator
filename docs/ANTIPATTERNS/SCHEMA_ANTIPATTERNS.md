<!--
tier: 3
last_synced_with: v0.3.0
ssot_for: [schema-antipatterns]
depends_on: [../../schemas/models.py, ../02_SYSTEM_ARCHITECTURE.md, ../05_DATA_SCHEMA_SPEC.md]
last_review: 2026-05-20
-->

# Schema Antipatterns

본 문서는 JSON 계약·Pydantic 모델·상태 머신 관련 안티패턴 카탈로그입니다. **append-only**.

각 항목은 [README.md](README.md) 의 표준 포맷을 따릅니다.

---

## SCHEMA-AP-001 — `ProjectState` 임의 점프 / self-loop 전이

- **증상 (symptom)**: 호출자가 `ProjectManifest.current_state` 를 직접 임의 값으로
  덮어쓰거나, 상태 머신을 우회해 `created → render_final` 같은 점프, 또는 동일
  상태 self-loop 를 수행. 결과적으로 `state_history` 가 의미를 잃고 어느 Phase 의
  산출물인지 추적 불가능해진다.
- **나쁜 예 (bad)**:
  ```python
  manifest.current_state = ProjectState.RENDER_FINAL  # 검증 없이 직접 대입
  manifest.state_history.append(...)                  # history 만 남기고 끝
  save_manifest(manifest)                             # 또는 _write_manifest 직접 호출
  ```
- **좋은 예 (good)**:
  ```python
  from orchestrator.project_manager import transition_state
  transition_state(manifest, ProjectState.INTAKE_PLANNING, reason="start intake")
  # 내부에서 state_machine.validate_transition() → LINEAR_SEQUENCE + archived 검증.
  # 표 밖이면 ValueError + "허용된 다음 상태" 동봉.
  # 동일 상태 self-loop 도 거부 ("이미 'X' 상태입니다.").
  ```
- **자동 조치 (mitigation)**:
  - `orchestrator/state_machine.py:LINEAR_SEQUENCE` + `allowed_next_states` 가 SSOT.
    각 상태에서 다음 선형 상태와 `ARCHIVED` 만 허용 (archived 는 어디서든 도달).
  - `orchestrator/project_manager.py:transition_state` 가 단일 진입점이며,
    `validate_transition` 통과 후에만 디스크 쓰기.
  - 동일 상태 self-loop 도 거부 (no-op 호출자 책임).
  - `_write_manifest` 는 atomic write (tmp → `Path.replace`) — partial write 도 차단.
- **회귀 테스트 (regression_test)**: pending (`tests/orchestrator/test_state_machine.py`
  에 ① 정상 선형 ② 점프 거부 ③ self-loop 거부 ④ ARCHIVED 어디서든 도달
  ⑤ ARCHIVED 에서 추가 전이 거부 5 케이스 추가 예정).
- **발견 버전 (discovered)**: v0.2.0 (Phase 2 구축 시 선제 카탈로그화, v0.2.7 등록).
- **상태 (status)**: active

---

> 새 패턴 발견 시 본 파일 끝에 append. 과거 항목 수정 금지.
