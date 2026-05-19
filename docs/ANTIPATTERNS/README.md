<!--
tier: 3
last_synced_with: v0.1.4
ssot_for: [antipattern-catalog-index]
depends_on: [../../CLAUDE.md]
last_review: 2026-05-19
-->

# Antipattern Catalog

본 디렉토리는 카테고리별 안티패턴 카탈로그입니다. **append-only**입니다.

## 카테고리

| Prefix | 파일 | 도메인 |
|---|---|---|
| `TTS-AP` | [TTS_ANTIPATTERNS.md](TTS_ANTIPATTERNS.md) | TTS 발음, 억양, 운율, 자막-음성 일치 |
| `PIPELINE-AP` | [PIPELINE_ANTIPATTERNS.md](PIPELINE_ANTIPATTERNS.md) | Orchestrator, Worker, Task Queue, Log Router |
| `RIGHTS-AP` | [RIGHTS_ANTIPATTERNS.md](RIGHTS_ANTIPATTERNS.md) | 권리·라이선스 (Phase 7부터) |
| `RENDER-AP` | [RENDER_ANTIPATTERNS.md](RENDER_ANTIPATTERNS.md) | Remotion·FFmpeg·렌더 (Phase 9부터) |
| `SCHEMA-AP` | [SCHEMA_ANTIPATTERNS.md](SCHEMA_ANTIPATTERNS.md) | JSON 계약·Pydantic (Phase 2부터) |

미생성 파일은 해당 Phase 시작 시 첫 항목과 함께 생성합니다.

## 엔트리 표준 포맷

```markdown
## TTS-AP-001 — {짧은 제목}

- **증상 (symptom)**: …
- **나쁜 예 (bad)**: …
- **좋은 예 (good)**: …
- **자동 조치 (mitigation)**: …
- **회귀 테스트 (regression_test)**: `tests/...` 또는 `pending`
- **발견 버전 (discovered)**: vX.Y.Z
- **상태 (status)**: `active` / `superseded by ...` / `wontfix`
```

## 작업 흐름

1. 사고/오류 발견 → 카테고리 결정.
2. 해당 파일 끝에 새 N번 append.
3. 가능하면 같은 클래스 재발을 막는 구조적 조치 (검증기·테스트·hook).
4. `DEVLOG.md`에 한 줄 요약 + AP 번호.

## 과거 항목 수정 정책

- **과거 항목 내용 수정 금지**.
- 잘못된 항목은 `status: superseded by AP-NNN`으로 마킹만.
- 새 항목 추가로 정정.

## 인덱스 자동화 (Phase 후속)

- 각 `*_ANTIPATTERNS.md`에서 H2 `## TTS-AP-NNN` 패턴을 스캔하여 본 README 하단에 자동 목차 생성 (Phase 후속).
