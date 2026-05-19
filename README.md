<!--
tier: 1
last_synced_with: v0.1.2
ssot_for: [project-entry-point]
depends_on: [GOAL.md, CLAUDE.md, DOCS_GOVERNANCE.md, docs/02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-05-19
-->

# longform-briefing-pipeline

OSINT 기반 세계 이슈 롱폼 브리핑 영상 제작 시스템.

본 저장소는 단순 영상 생성기가 아닙니다. 사용자의 주제 지시 한 줄을 받아
**리서치 → 대본 → scene 설계 → 자산 수집 → TTS·BGM → Remotion 렌더 → 썸네일 → 업로드 메타데이터**
까지 자동화하는 **반복 가능·추적 가능·검수 가능** 한 파이프라인입니다.

## 핵심 원칙

1. **Orchestrator 중심.** 모든 작업은 Orchestrator가 지휘하며 Worker는 task 단위로만 동작합니다.
2. **JSON 계약 중심.** 모든 산출물은 Pydantic 모델로 검증된 JSON으로 흐릅니다.
3. **Dynamic Intake.** 주제별로 필요한 자료가 달라지므로 입력 폼을 동적으로 생성합니다.
4. **방식 B Command Center.** 단일 Textual TUI 안에 Orch CLI, Job Dashboard, Worker Slot이 모두 모입니다.
5. **Pre-production Debug Layer.** `draft_debug.mp4`에만 표시되는 디버그 오버레이로 scene 품질을 추적합니다.
6. **승인 게이트.** Intake / Source / Blueprint / Script / Scene / Draft / Thumbnail / Final 9개 Review Gate를 통과해야 합니다.

## Quick Start

```bash
# 1) Python 3.11 환경 준비
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 2) 의존성 설치
pip install -r requirements.txt

# 3) git hook 활성화 (커밋 메시지 버전 검증)
git config core.hooksPath .githooks

# 4) Command Center 실행
run_pipeline.bat                # Windows
# python -m orchestrator.main command-center --project demo
```

## 문서 진입점

| 목적 | 문서 |
|---|---|
| 무엇을 만드는지 | [GOAL.md](GOAL.md) |
| 어떤 규칙으로 만드는지 | [CLAUDE.md](CLAUDE.md) |
| 문서 거버넌스 | [DOCS_GOVERNANCE.md](DOCS_GOVERNANCE.md) |
| 시스템 아키텍처 | [docs/02_SYSTEM_ARCHITECTURE.md](docs/02_SYSTEM_ARCHITECTURE.md) |
| 데이터 스키마 | [docs/05_DATA_SCHEMA_SPEC.md](docs/05_DATA_SCHEMA_SPEC.md) |
| 단계별 구현 로드맵 | [docs/13_IMPLEMENTATION_ROADMAP.md](docs/13_IMPLEMENTATION_ROADMAP.md) |
| 운영 런북 | [docs/15_OPERATIONS_RUNBOOK.md](docs/15_OPERATIONS_RUNBOOK.md) |
| Antipattern 카탈로그 | [docs/ANTIPATTERNS/README.md](docs/ANTIPATTERNS/README.md) |

## 브랜치 / 버전 현황판 (즐겨찾기 권장)

브랜치, 커밋, PR, 각 커밋의 버전(`vX.Y.Z:` prefix)을 한눈에 보는 정적 HTML 페이지가 있습니다.
사용자 본인 전용이며, **GitHub REST API를 클라이언트에서 호출**해 매번 최신 상태를 보여줍니다.

### 호스팅: Vercel (Private 저장소 지원)

본 저장소는 Private 이므로 GitHub Pages 가 무료 플랜에서 동작하지 않습니다. 대신 Vercel 을 사용합니다.

1. [https://vercel.com/new](https://vercel.com/new) 접속 → GitHub 계정 연결.
2. `doroper98/osint_generator` 저장소 import (Private 저장소도 무료 플랜에서 사용 가능).
3. **Framework Preset**: Other / Static. **Root Directory**: `.` (기본). Build/Install command 는 비워둠.
4. Deploy. 약 1분 후 `https://<project-name>.vercel.app/` 가 발급됨.
5. 이 URL 을 즐겨찾기. 푸시할 때마다 Vercel 이 자동 재배포.

`vercel.json` 이 저장소 루트에 있어서 별다른 설정 없이 위 절차만으로 끝납니다.

### 인증: Personal Access Token (PAT)

Private 저장소이므로 페이지가 GitHub API 를 호출하려면 사용자 본인의 토큰이 필요합니다.
페이지 첫 진입 시 안내 다이얼로그가 뜨며, 입력한 토큰은 **본인 브라우저 localStorage 에만** 저장됩니다 (저장소에는 들어가지 않음).

토큰 발급: GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token

- Resource owner: 본인
- Repository access: `osint_generator` 만 선택
- Repository permissions: `Contents: Read-only`, `Metadata: Read-only`, `Pull requests: Read-only`

만료일을 길게 설정하시면 갱신 주기가 줄어듭니다.

새 브랜치를 만들면 `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 객체에 한 줄 설명을 추가하십시오.

## 현재 상태

| Phase | 상태 |
|---|---|
| 0. 프로젝트 초기화 | ✅ |
| 1. Orchestrator Command Center MVP | 🚧 진행 중 |
| 2. Project Manager / State Machine | ⬜ |
| 3. Dynamic Intake Page | ⬜ |
| 4. Task Queue / AI Delegation | ⬜ |
| 5. Source Registry / Completeness Check | ⬜ |
| 6. Research / Script / Scene | ⬜ |
| 7. Media Workers | ⬜ |
| 8. TTS / Music | ⬜ |
| 9. Remotion Rendering | ⬜ |
| 10. Thumbnail System | ⬜ |
| 11. Review Dashboard / Publish | ⬜ |

자세한 현황은 [CHANGELOG.md](CHANGELOG.md)와 [DEVLOG.md](DEVLOG.md)를 참고하십시오.
