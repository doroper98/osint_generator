<!--
tier: 1
last_synced_with: v5.5.1
ssot_for: [project-entry-point]
depends_on: [GOAL.md, CLAUDE.md, DOCS_GOVERNANCE.md, docs/02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-09-29
-->

# longform-briefing-pipeline

OSINT 기반 세계 이슈 롱폼 브리핑 영상 제작 시스템.

본 저장소는 단순 영상 생성기가 아닙니다. 사용자의 주제 지시 한 줄을 받아
**리서치 → 원고 → 음성 타임라인 → 자산 → AI 연출 → 시각 검수 → 지도 중심 다큐 엔진(engine/) 렌더 → 오디오 → 전달**
까지 자동화하는 **반복 가능·추적 가능·검수 가능** 한 파이프라인입니다.

## 핵심 원칙

1. **Orchestrator 중심.** 상태 머신이 프로젝트를 CREATED→DONE 으로 진행하고, LLM 워커와 엔진 CLI 는 서브프로세스로만 부릅니다.
2. **JSON·YAML 계약 중심.** 모든 산출물은 `schema_version` 을 갖고 Pydantic 모델로 검증됩니다.
3. **소스 인테이크와 인용 대조.** 기사·X 게시물을 사람이 넣고 확인하면, 주장의 검증 status 는 코드가 인용 대조로 정합니다.
4. **영상미 우선, 정확성 위에서.** 기준 작품은 v3『호르무즈와 한국』(`docs/handoff/golden/`)이고, 수치는 `rules/video_rules.yaml` 한 곳에 있습니다.
5. **관성 방지.** 옛 경로는 삭제로 끝내고, 폴백으로 옛 스타일 영상을 내보내지 않습니다(`docs/handoff/15`, `tests/anti_inertia/`).
6. **승인 게이트 2개.** 원고(SCRIPT_APPROVAL)와 프리뷰(PREVIEW_APPROVAL). 그 사이는 결정적 검사와 AI 시각 검수가 채웁니다.

## Quick Start

```bash
# 1) Python 3.11 환경 준비
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 2) 의존성 설치 (엔진 포함) + 시스템 ffmpeg·fontconfig
pip install -r requirements.txt -r requirements-engine.txt
python tools/fetch_data.py fonts ne tiles flags bgm   # 글꼴·지도·지형·국기·음악

# 3) git hook 활성화 (커밋 메시지 버전 검증)
git config core.hooksPath .githooks

# 4) Command Center 실행
run_pipeline.bat                # Windows
# python -m orchestrator.main command-center --project demo
```

## 문서 진입점

| 목적 | 문서 |
|---|---|
| **v2 개편 인계 문서 (영상 기준 정본)** | [docs/handoff/00_INDEX.md](docs/handoff/00_INDEX.md) |
| 무엇을 만드는지 | [GOAL.md](GOAL.md) |
| 어떤 규칙으로 만드는지 | [CLAUDE.md](CLAUDE.md) |
| 문서 거버넌스 | [DOCS_GOVERNANCE.md](DOCS_GOVERNANCE.md) |
| 시스템 아키텍처 | [docs/02_SYSTEM_ARCHITECTURE.md](docs/02_SYSTEM_ARCHITECTURE.md) |
| 데이터 스키마 | [docs/05_DATA_SCHEMA_SPEC.md](docs/05_DATA_SCHEMA_SPEC.md) |
| 단계별 구현 로드맵 | [docs/13_IMPLEMENTATION_ROADMAP.md](docs/13_IMPLEMENTATION_ROADMAP.md) |
| 운영 런북 | [docs/15_OPERATIONS_RUNBOOK.md](docs/15_OPERATIONS_RUNBOOK.md) |
| 영상·오디오·지도·렌더 안내도 | [docs/07](docs/07_VIDEO_STYLE_GUIDE.md) · [08](docs/08_AUDIO_AND_TTS_SPEC.md) · [09](docs/09_MAP_AND_GEO_SPEC.md) · [10](docs/10_RENDERING_PIPELINE_SPEC.md) |
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

## 현재 상태 (v5.3.0)

| 구간 | 상태 |
|---|---|
| v2 개편 Phase 0~10 (v2.0.0~v3.6.0) | 합격 — 골든 재현·모듈 분해·지오·원고/음성·권리·패널·미디어·오케스트레이터·AI 연출·소스 인테이크·카메라·오디오·번들·1080p |
| Phase 11 문서·정리·GOAL G3 개정 (v4.0.0) | 완료(D-0075) |
| G1 무대 추상화 (v4.1.0) | 완료(D-0080) |
| G2 장르 프로필·새 요소 파이프라인 (v4.2.0) | 완료(D-0083) |
| G3 시간축 무대·데이터 레코드·차트 정직성 검사 (v4.3.0) | 완료(D-0089) |
| G4 첫 비지정학 영상 (v4.4.0) | 완료(D-0094), 영상 최종 판정은 사용자 |
| G5 검증 라벨 엔딩 카드 한 줄 (v4.5.0) | 완료(D-0100) |
| G6 배경음악 저음 보강 (v4.6.0) | 완료(D-0105) |
| G6.5 dmz_mine 브랜치 병합 (v4.7.0) | 완료(D-0110) |
| G7 요소 크기 (v4.8.0) | 완료(D-0114) |
| G8 콘티 판 루틴 (v4.9.0) | 완료(D-0116) |
| G9 정비 — 지명 사전·브리지 stdin·귀속 표현 (v4.10.0) | 완료(D-0117) |
| G10 정적 구간 검사·음악 상한·글자 크기 2차 표 (v4.11.0) | 완료(D-0119) |
| G11 GOAL G4-21·claim_kind fact/statement (v5.0.0) | 완료(D-0125) |
| G12 backdrop 무대·아일랜드·축 스케일·기사 프레스 v2·버전 도장 (v5.1.0) | 완료(D-0127·D-0128) |
| G13 배경 가독·주 아일랜드 상시·보도 인용 = 기사·card-island (v5.2.0) | 완료(D-0134) |
| G14 겹침 카드(cascade) 채택 (v5.3.0) | 진행 중 |
| 썸네일 시스템, 텔레그램 인테이크, 유튜브 업로드 | v2 파이프라인에 없음 — 별도 계획 |

Phase 표와 버전은 [docs/13_IMPLEMENTATION_ROADMAP.md](docs/13_IMPLEMENTATION_ROADMAP.md), 변경 내역은 [CHANGELOG.md](CHANGELOG.md), 합격 커밋은 [docs/handoff/TAGS_PENDING.md](docs/handoff/TAGS_PENDING.md).
