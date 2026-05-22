<!--
tier: 2
last_synced_with: v0.3.3
ssot_for: [codex-review-procedure]
depends_on: [../CLAUDE.md]
last_review: 2026-05-20
-->

# 외부 코드 리뷰 표준 — codex `exec` Review

본 문서는 **CLAUDE.md C10** 의 codex 코드 리뷰 절차를 위한 운영 매뉴얼입니다.
"개발 완료 단계" 마다 본 절차를 실행하고 결과를 후속 PATCH 로 흡수합니다.

---

## 1. 언제 실행하나

| 트리거 | 실행 의무 |
|---|---|
| **MINOR 또는 MAJOR 증분 직전** | 필수. 리뷰 결과의 Critical/High 모두 흡수한 뒤에 증분. |
| **Phase 완료 직전** | 필수. Phase 의 DoD 체크리스트의 마지막 항목으로 codex review 포함. |
| **새 Worker 클래스 / 새 도메인 모델 도입 PATCH** | 권장. Phase 안 marker. |
| **단순 버그 fix / 문서 보강 PATCH** | 면제. (단, 같은 카테고리의 fix 가 3 회 누적되면 한 번 돌린다.) |

---

## 2. 표준 리뷰 프롬프트

본 프롬프트는 **영문 고정**입니다 (codex 의 일관된 reasoning 유지 + 한글 코드페이지 이슈 회피).
변경마다 `Versions in scope`, `Key files`, `Review priorities` 세 절만 수정해서 재사용합니다.

### 프롬프트 템플릿

```text
You are doing a code review of recent changes in this repository.

Project: longform-briefing-pipeline (osint_generator).
Branch: <current-branch>
Versions in scope: vX.Y.Z (<commit-sha>), vX.Y.Z (<commit-sha>), ...

Key files to focus on:
- <relative/path/to/file1.py> — <one-line summary of what changed>
- <relative/path/to/file2.py> — ...
- <relative/path/to/test_file.py> — ...

Review priorities (in order):
1. <highest priority topic — e.g. subprocess safety, schema invariants>
2. <next>
3. CLAUDE.md C2 compliance: type hints, Pydantic v2, .replace() only.
4. CLAUDE.md C4 compliance: BaseWorker inheritance, no user prompts, writes only own output_refs, always emits task_result.json.
5. Test coverage: are all status branches reachable from tests?
6. Traceability: are all artifacts persisted under expected paths?

Output format:
- Markdown grouped by severity: Critical / High / Medium / Low / Nit
- Each item: file:line + problem + suggested fix
- For things that look correct, one short "OK" line, no praise paragraphs
- End with a one-line verdict
```

### 작성 가이드

- `<current-branch>` 와 commit SHA 는 호출 직전 `git log --oneline` 로 확인.
- `Key files` 는 5 개 이하로 좁힌다. 너무 넓으면 리뷰가 표면적이 됨.
- `Review priorities` 의 1·2 번은 **변경의 핵심 위험**. 보안·계약 위반·데이터 손실 가능성이 있는 영역.
- 3 번 이하는 CLAUDE.md 의 일반 규칙 — 변경마다 거의 동일.
- output format 의 "no praise paragraphs" 는 codex 가 칭찬으로 페이지를 메우는 것을 막기 위함.

---

## 3. 실행 명령어

사용자 머신은 Windows cmd 가정. macOS/Linux 사용자는 4 절 참고.

### 3.1 Windows cmd

```cmd
:: 0. 콘솔을 UTF-8 로 (한 번만)
chcp 65001

:: 1. repo 로 이동
cd C:\path\to\osint_generator

:: 2. 최신 brunch + 최신 코드 확인
git checkout <branch>
git pull origin <branch>
git log --oneline -5

:: 3. 프롬프트 파일 작성 (메모장 또는 에디터)
notepad review-prompt.txt

:: 4. codex 호출 (stdin 으로 프롬프트 전달, stdout JSONL 을 파일로 저장)
type review-prompt.txt | codex exec --skip-git-repo-check --color never -C "%CD%" - > review-out.jsonl

:: 5. 결과 확인 (마지막 agent_message 의 text 가 리뷰 본문)
notepad review-out.jsonl
```

### 3.2 macOS / Linux

```bash
cd ~/path/to/osint_generator
git checkout <branch>
git pull origin <branch>
git log --oneline -5

# 프롬프트 파일 작성 (에디터)
$EDITOR review-prompt.txt

# codex 호출
cat review-prompt.txt | codex exec --skip-git-repo-check --color never -C "$PWD" - > review-out.jsonl

# 결과 확인
less review-out.jsonl
```

### 3.3 .gitignore / exclude

`review-prompt.txt`, `review-out.jsonl` 은 일회용 산출물이므로 커밋하지 않습니다.

```cmd
:: 한 번만 실행 (개인 환경 전용)
echo review-prompt.txt > .git\info\exclude
echo review-out.jsonl >> .git\info\exclude
```

---

## 4. 결과 해석과 후속 조치

codex 출력은 `_unwrap_codex_response` 가 처리하는 JSONL 포맷
(`workers/base_llm_worker.py`, LLM-AP-002 참조). 사람이 읽을 때는
마지막 `{"type":"item.completed","item":{"type":"agent_message","text":"..."}}`
의 `text` 필드가 리뷰 본문.

### 4.1 심각도별 처치

| 심각도 | 처치 | 버전 영향 |
|---|---|---|
| **Critical** | 즉시 hotfix PATCH. 다른 작업 중단. | PATCH 또는 MAJOR (계약 위반 시) |
| **High** | 같은 의도의 단일 PATCH 로 일괄 흡수 (한 커밋 = "외부 리뷰 N차 반영"). | PATCH |
| **Medium** | 위와 같은 PATCH 에 묶거나, 별도 PATCH 로. | PATCH |
| **Low** | 대부분 "OK" 확인. 진짜 액션 항목이면 다음 PATCH 에 끼워넣기. | 변경 없음 또는 PATCH |
| **Nit** | 누적. 같은 영역 PATCH 작업 시 같이 처리. | 변경 없음 |

### 4.2 흡수 PATCH 의 commit 메시지 컨벤션

```
vX.Y.Z: 외부 코드 리뷰 N차 반영 ({짧은 요약})

codex CLI 리뷰의 High/Medium 항목 일괄 fix:
- H1: ...
- H2: ...
- M1: ...
```

`N차` 는 본 절차를 실행한 누적 횟수.

### 4.3 거짓 양성 (False positive)

리뷰 항목이 false positive 라고 판단되면 **반드시 사용자와 합의** 후 무시.
근거 (LLM-AP 번호, 설계 결정 위치) 를 DEVLOG 의 다음 엔트리에 명시.
codex 가 모르는 ADDENDUM/AP 가 있을 수 있으므로 우리 쪽이 맞을 가능성도 정상적으로 존재.

---

## 5. 절차의 한계

- codex 는 본 저장소의 ADDENDUM_04 / antipattern 카탈로그를 학습 데이터에 포함하지 않음.
  → 리뷰 결과가 우리 거버넌스 결정과 어긋날 수 있음. 그 때마다 우리가 판단.
- codex 의 리뷰는 정적 분석 + 일반 SE 직관. 실 실행 / 통합 테스트는 별도.
  → 본 절차는 단위/구조 검증이고, 통합 검증은 Phase 별 smoke test 가 담당.
- prompt 가 너무 길면 codex 가 핵심을 놓침. 5 파일 이하로 좁히는 게 가장 정확.

---

## 6. 관련 문서

- `CLAUDE.md` C10: 절차의 의무화 규칙
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-002: codex JSONL 출력 포맷
- `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` §5: CLI 인터페이스 가정
- `workers/base_llm_worker.py` `_unwrap_codex_response`: 같은 unwrap 로직을 우리 시스템 안에서도 사용
