<!--
tier: 2
last_synced_with: v5.13.0
ssot_for: [dynamic-intake-page]
depends_on: [02_SYSTEM_ARCHITECTURE.md, 05_DATA_SCHEMA_SPEC.md]
last_review: 2026-09-29
-->

# 04 — Dynamic Intake Page Spec

## 1. 정의

Dynamic Intake Page는 **고정 폼이 아니라**, Orchestrator가 주제를 분석해 만든 `intake_plan.json`을 기반으로 **그때마다 렌더링되는 동적 입력 페이지**다.

진입은 두 단계다:
1. **프로젝트 생성 화면 (`GET/POST /new`, v0.7.0)** — 주제/카테고리/길이/**초기 자료 링크**를 입력. 제출하면 `new_project` + `IntakePlanner` 가 실행되고 `/intake/{pid}` 로 리다이렉트.
2. **동적 인테이크 페이지 (`GET /intake/{pid}`)** — 생성된 `intake_plan.json` 을 안내 카드로 보여 주고, 소스 넣기 폼(`POST /intake/{pid}/source`)·사용자 확인(`/confirm`)·제출(`/submit`)을 받는다. 저장 위치는 `intake/sources.json`(v3.2.0, handoff 18 §7 — 옛 `source_intake.json` 삭제).

## 2. 책임

| 역할 | 책임 |
|---|---|
| Web App (`GET/POST /new`) | 주제 + 초기 링크 입력 → `new_project` + planner 실행 → `/intake/{pid}` 리다이렉트 |
| Dynamic Intake Planner Agent | 주제(+초기 링크) 분석 → `intake_plan.json` 생성 |
| Web App (`web/intake_page_app.py`) | `intake_plan.json` 읽어 폼 렌더 |
| 사용자 | 각 항목 모드 선택 + 자료 업로드 |
| Web App | 소스 한 건씩 `intake/sources.json`에 기록(`orchestrator.source_intake`), 확인·제출은 `intake_service.submit_sources` 호출만 |

> **공유 오케스트레이션**: `new-project` 후의 planner 실행은 CLI(`plan-intake`)와 Web(`POST /new`)이 `orchestrator/intake_service.py:run_intake_planner` 를 공유한다 (전이 순서·idempotency 단일 출처).

## 3. 항목 모드

사용자가 각 항목별로 선택하는 모드:

| 모드 | 의미 |
|---|---|
| `direct_provide` | 사용자가 텍스트로 직접 제공 |
| `link_provide` | 사용자가 URL 제공 |
| `gdrive_provide` | Google Drive 링크 제공 |
| `file_upload` | 파일 직접 업로드 |
| `ai_delegate` | AI Delegation (Worker가 알아서) |
| `mixed` | 사용자 일부 제공 + AI Delegation |
| `skip` | 항목 생략 |
| `must_use` | 반드시 사용 (`priority=must_use`로 승격) |
| `reference_only` | 참고만 사용 (영상 노출 금지) |

## 4. Planner 카테고리별 항목 예시

### 4.1 전쟁/군사

- 핵심 사건 영상 (X/TG 링크)
- 위치 좌표 / 지명
- 공식 발표 (정부·국방부)
- OSINT 분석가 트윗
- 과거 유사 사례
- 위성 사진
- 무기 체계명

### 4.2 자연재해 / 지진

- 진앙·규모·진원 깊이
- 발생 시각 (UTC + 현지)
- 출처 (USGS / JMA / CWA / CENC / KMA)
- 여진 추이
- 쓰나미 경보 유무
- 인근 도시
- 판 경계 / 해구
- 현장 영상 / CCTV
- 피해 사진
- 과거 유사 지진

### 4.3 경제 / 금융 / 산업

- 핵심 지표 (유가, 환율, 금리, 운임)
- 시계열 데이터 출처
- 산업 보고서
- 관련 기업
- 정책 발표

### 4.4 음모론 / 정보전 (해외 한정)

- 원 주장 출처 (누가 처음 퍼뜨렸는가)
- 확산 경로 (어느 플랫폼에서 어떻게)
- 반박 자료
- 검증 / 미검증 상태
- 미검증 라벨 필요 항목

## 5. `intake_plan.json` 항목 필드

[docs/05_DATA_SCHEMA_SPEC.md](05_DATA_SCHEMA_SPEC.md)의 `IntakePlanItem` 모델을 SSOT로 사용합니다.

## 6. UI 가이드

- 항목별 카드 형태
- 각 카드 헤더: 라벨 + priority 배지
- 각 카드 본문: 설명 + why_needed + risk_notice
- 각 카드 푸터: 모드 라디오 + 업로드 영역
- 페이지 하단: `영상 생성 착수` 버튼 (모든 필수 항목 모드 선택 시 활성화)

상세 UI 디자인은 Phase 3에서 와이어프레임으로 확정.

## 7. 제출 흐름 (v3.2.0)

1. 사용자가 소스를 넣는다(기사 URL·기사 본문·X 텍스트·X 캡처·파일). x.com 은 열지 않는다.
2. 소스마다 계정·시각이 맞는지 사용자가 확인한다(미확인 소스가 있으면 제출 409).
3. `POST /intake/{pid}/submit` → `intake → source_verify` 전이. 이후 검증 워커 초안 → 코드 판정 → `intake/claims.json`.
4. (v1 이력) `source_intake.json` 작성 → `source_collecting` 전이 → task_queue 배정 흐름은 v3.2.0 에서 삭제됐다.

## 8. 예외 처리

- 필수 항목인데 모드가 `skip`이면 → 경고 후 사용자 재확인.
- 모든 항목이 `ai_delegate`라면 → 경고 (사용자 자료 부재).
- 업로드 파일 용량 초과 → Worker 단계로 미루지 않고 즉시 거부.
