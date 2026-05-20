<!--
tier: 2
last_synced_with: v0.2.2
ssot_for: [test-strategy]
depends_on: [../GOAL.md, 13_IMPLEMENTATION_ROADMAP.md]
last_review: 2026-05-19
-->

# 16 — Test Plan

## 1. 테스트 레이어

| 레이어 | 도구 | 범위 |
|---|---|---|
| 정적 컴파일 | `python -m py_compile` | 모든 `.py` 변경 시 |
| 단위 테스트 | `pytest` | Pydantic 모델, agent 출력 파싱, Worker base 동작 |
| 통합 테스트 | `pytest` (느림) | dummy worker subprocess, log router 동작 |
| 시스템 테스트 | 시나리오 스크립트 | 샘플 프로젝트로 Phase 0–N 일괄 실행 |
| 시각 검수 | 사람 | draft_debug / preview / final.mp4 |

## 2. Phase별 합격 기준

[docs/13_IMPLEMENTATION_ROADMAP.md](13_IMPLEMENTATION_ROADMAP.md)의 각 Phase 완료 기준이 동시에 테스트 합격 기준이다.

## 3. 회귀 테스트 항목

### Phase 1 회귀

- [ ] Command Center 진입에 5초 이내.
- [ ] dummy worker 4개 subprocess 동시 실행.
- [ ] 각 Worker 로그가 해당 Slot 패널에 1초 이내 표시.
- [ ] worker_slots.json이 슬롯 상태와 일치.
- [ ] `q`로 종료 시 모든 subprocess 종료.

### Phase 9 회귀 (Render)

- [ ] `render_mode=debug` → `draft_debug.mp4`에 DebugOverlay 좌측 상단 표시.
- [ ] `render_mode=preview` → `draft_preview.mp4`에 DebugOverlay 없음 (OCR 검증).
- [ ] `render_mode=final` → `final.mp4`에 DebugOverlay 없음 (OCR 검증).

## 4. 테스트 데이터

- `tests/fixtures/` 아래에 샘플 JSON·이미지·짧은 mp4 보관.
- 라이선스 안전한 자료만 사용.

## 5. CI (Phase 후속)

- GitHub Actions 또는 사내 CI.
- 매 PR에 `py_compile`, `pytest`, 코드 스타일 검사.
- 본 저장소는 현재 로컬 검증 위주, CI는 Phase 11 후 구축.

## 6. 테스트 작성 규칙

- 테스트 함수 이름은 `test_{condition}_{expected}` 형태.
- Pydantic 검증 실패는 명시적으로 `pytest.raises(ValidationError)` 사용.
- subprocess 테스트는 30초 timeout.
- 외부 API 호출은 mock 또는 record/replay.

## 7. Antipattern 회귀 테스트

새 Antipattern이 카탈로그에 추가되면 가능하면 같은 클래스의 회귀 테스트도 함께 작성한다. 그렇지 못한 경우 카탈로그에 `regression_test: pending` 표기.
