<!--
tier: 2
last_synced_with: v5.5.0
ssot_for: [test-strategy]
depends_on: [../GOAL.md, 13_IMPLEMENTATION_ROADMAP.md]
last_review: 2026-09-29
-->

# 16 — Test Plan

## 1. 테스트 레이어

| 레이어 | 도구 | 범위 |
|---|---|---|
| 정적 컴파일 | `python -m py_compile` | 모든 `.py` 변경 시 |
| 단위 테스트 | `pytest` | Pydantic 모델, agent 출력 파싱, Worker base 동작 |
| 통합 테스트 | `pytest` (느림) | dummy worker subprocess, log router 동작 |
| 시스템 테스트 | 시나리오 스크립트 | 샘플 프로젝트로 Phase 0–N 일괄 실행 |
| 결정적 검사 | `engine/checks.py` → `prev/checks.json` | 프리뷰 18항목(hard 0 이 게이트 ② 전제) |
| 골든 회귀 | `tools/golden_compare.py`, `tools/res_compare.py` | hormuz 25컷 MAD(480p 무변경 = 0), 1080p 축소 비교 |
| 관성 방지 | `tests/anti_inertia/` | 15 P1~P12(레거시 경로·폴백·코드 연출·매직 넘버·레지스트리·provenance) |
| 문서 동기화 | `tests/test_goal_g3.py`, `tests/test_docs_sync.py` | G3 검증 방법 실재, 헤더 버전·규칙 키 인용·폐기 배너·삭제 경로 링크 |
| 시각 검수 | 사람(게이트 ②) + AI 시각 검수 | `prev/sheet.jpg`·프리뷰 컷·전편 mp4 |

## 2. Phase별 합격 기준

v2 합격 기준은 [GOAL.md](../GOAL.md) G3(17개, 항목별 검증 방법)이다. Phase 합격표는 back_and_forth 지침(D)과 [13](13_IMPLEMENTATION_ROADMAP.md)이다.
테스트 기준선은 **삭제 조정 기준선**이다(D-0053): passed ≥ (직전 기준 − P2로 삭제한 옛 테스트 수) + 새 테스트 요구치, failed 0·xfail 0.
글꼴·지형 티어가 없는 환경의 테스트는 사유 있는 skip이다(`tests/conftest.py` NB16, `tests/_fonts.py` NB27).

## 3. 회귀 테스트 항목

### 영상 회귀 (매 Phase)

- [ ] hormuz `--preview golden` 25컷 MAD 0(렌더 코드를 바꾸지 않은 Phase) 또는 근거 있는 차이표.
- [ ] 480p 전편 `video_noaudio.mp4` md5 무변경(렌더 무변경 Phase).
- [ ] `prev/checks.json` hard 0, provenance drops 0.
- [ ] 시간축 데모 12컷 md5 = 최신 등재 기준선(v4.4.0 `reports/phaseG4/demo_frames.json`, 글자 토큰 변경 D-0092).
- [ ] 장르 프롬프트 층: 기본 장르 프롬프트 바이트 동일, 장르 예시 출력 = 스키마(`tests/test_genre_prompts.py`, 파리티).

v1 회귀 항목(Command Center 슬롯·Remotion render_mode·DebugOverlay OCR)은 폐기됐다(G3-legacy).

## 4. 테스트 데이터

- `tests/fixtures/` 아래에 샘플 JSON·이미지·짧은 mp4 보관.
- 라이선스 안전한 자료만 사용.

## 5. CI (Phase 후속)

- GitHub Actions 또는 사내 CI.
- 매 PR에 `py_compile`, `pytest`, 코드 스타일 검사.
- 본 저장소는 현재 로컬 검증 위주다. CI 구축은 G1~G4 이후 과제로 남는다.

## 6. 테스트 작성 규칙

- 테스트 함수 이름은 `test_{condition}_{expected}` 형태.
- Pydantic 검증 실패는 명시적으로 `pytest.raises(ValidationError)` 사용.
- subprocess 테스트는 30초 timeout.
- 외부 API 호출은 mock 또는 record/replay.

## 7. Antipattern 회귀 테스트

새 Antipattern이 카탈로그에 추가되면 가능하면 같은 클래스의 회귀 테스트도 함께 작성한다. 그렇지 못한 경우 카탈로그에 `regression_test: pending` 표기.
