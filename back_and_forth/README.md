<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [back-and-forth-protocol]
depends_on: [CLAUDE.md, docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, docs/handoff/DECISIONS.md]
last_review: 2026-09-27
-->

# back_and_forth — 구현 세션(Opus) ↔ 감독 세션(Fable) 교신 규칙

이 폴더는 두 에이전트가 **파일로 주고받는 교신함**이다. 사용자 지시(2026-09-27)로 만들었다.

- **Opus**(구현 책임자)는 끝낸 일을 **보고서(R)**로 남긴다.
- **Fable**(분석·감독)은 보고서를 읽고 **지침(D)**을 남긴다.
- 둘 다 **5분마다** 새 파일이 있는지 확인한다.
- 목표(§8)의 모든 Phase가 끝날 때까지 계속한다.

폴더 구성:

| 파일 | 용도 |
|---|---|
| `README.md` | 이 규칙 문서 |
| `check.py` | 감시 도구 — 미처리 상대 파일 나열, 다음 번호 계산(§5) |
| `FABLE_KICKOFF.md` | 사용자가 Fable 세션에 붙여 넣을 착수 문안 |
| `R-*.md`, `D-*.md` | 교신 파일(§2) |

폴더 이름은 공백 없이 `back_and_forth`로 했다. 셸 명령과 경로에서 따옴표 실수를 없애기 위해서다.

---

## 1. 교신 경로 = git 브랜치

두 세션은 서로 다른 컨테이너에서 돈다. 그래서 교신은 **원격 브랜치 `overhaul/v2-map-engine`의 이 폴더**로만 한다.

- 파일을 쓰면 **커밋하고 푸시**해야 상대가 본다. 로컬에만 있는 파일은 없는 것과 같다.
- 읽을 때는 **먼저 fetch/pull**한다.
- 커밋 규칙은 저장소 규칙을 그대로 따른다: 첫 줄 `vX.Y.Z: …`, X.Y.Z는 `VERSION` 파일 값(C5.3).
  교신 파일만 올리는 커밋의 요지 예: `v2.0.0: back_and_forth D-0003 — Phase 1 착수 지침`.

## 2. 파일 명명법

```
{종류}-{번호4자리}_{YYYYMMDD-HHMM}_{slug}.md
```

| 종류 | 작성자 | 뜻 |
|---|---|---|
| `R` | Opus | 보고(Report) — 작업 결과·진행·질문·막힘 |
| `D` | Fable | 지침(Directive) — 다음에 할 일, 수정 요청, 답변 |

- **번호**는 종류별로 1씩 증가한다(`R-0001`, `R-0002` …, `D-0001`, `D-0002` …). 건너뛰거나 재사용하지 않는다.
- **시각**은 UTC, 파일을 만든 시각이다.
- **slug**는 영문 소문자·숫자·하이픈 3~6단어다. 예: `phase0-complete`, `phase1-kickoff`.
- 예: `R-0001_20260927-1255_phase0-complete.md`, `D-0001_20260927-1310_phase1-go.md`.
- 번호 충돌을 막기 위해 **R은 Opus만, D는 Fable만** 만든다.

## 3. 파일 머리말 (필수)

모든 R·D 파일은 맨 위에 아래 YAML 블록을 둔다. 감시 스크립트가 이 값만 읽는다.

```yaml
---
id: R-0002                 # 파일명의 종류-번호와 같아야 한다
from: opus                 # opus | fable | user
to: fable                  # fable | opus
kind: phase_report         # §4 표
responds_to: [D-0001]      # 이 파일이 답하는 상대 파일 id. 없으면 []
phase: "1"                 # 관련 Phase (docs/handoff/19 §6 번호). 없으면 "-"
version: v2.0.1            # 작성 시점 VERSION
commit: 1a2b3c4            # 보고 대상 작업의 마지막 커밋(R 전용, D는 생략 가능)
status: done               # R: done | in_progress | blocked | question  /  D: open | superseded
priority: normal           # D 전용: urgent | normal | low
supersedes: []             # D 전용: 이 지침이 대체하는 이전 D id
---
```

- 머리말 다음 본문은 한국어다. 문장은 짧게, 표는 구조가 분명할 때만 쓴다.
- **과거 파일은 고치지 않는다(append-only).** 정정은 새 파일로 하고 `supersedes`에 적는다.

## 4. 종류(kind)

| kind | 누가 | 언제 |
|---|---|---|
| `phase_report` | Opus | Phase가 끝났을 때. KICKOFF §7 다섯 항목 필수(§6) |
| `progress` | Opus | 지침 하나를 끝냈을 때, 또는 긴 작업의 중간 보고 |
| `ack` | Opus | 지침을 읽고 착수했음을 알릴 때(착수 후 5분 안) |
| `question` | Opus | 판정 기준 ①②③으로 정할 수 없는 결정이 생겼을 때 |
| `blocked` | Opus | 권한·환경·외부 요인으로 진행이 불가능할 때 |
| `directive` | Fable | 다음 작업 지시, 수정 요청 |
| `answer` | Fable | Opus의 `question`에 대한 답 |
| `review` | Fable | 보고서 검토 의견(지시 없음) |
| `stop` | Fable 또는 user | 즉시 멈춤. 현재 커밋 단위만 마무리하고 대기 |

## 5. 감시 규칙 (양쪽 공통)

### 5.1 주기
- **5분마다** 한 번 확인한다. 연속으로 빈 확인이 이어져도 주기를 늘리지 않는다.
- 작업 중이면 **커밋 단위가 끝날 때마다** 한 번 더 확인한다.

### 5.2 확인 절차

```bash
git fetch -q origin overhaul/v2-map-engine
git pull --rebase -q origin overhaul/v2-map-engine        # 로컬 미푸시 커밋만 재배치. 푸시된 이력은 절대 재작성하지 않는다
python back_and_forth/check.py --me opus                   # Opus: 미처리 D 나열 (exit 10 = 새 파일)
python back_and_forth/check.py --me fable                  # Fable: 미처리 R 나열
python back_and_forth/check.py --me opus --next-id         # 내가 쓸 다음 번호
```

- "새 파일" = 내가 아직 `responds_to`로 답하지 않은 상대 파일, 그중 `status: open`(D) 또는 모든 R.
- `check.py`는 **내 파일들의 `responds_to`를 모아** 처리 여부를 판정한다. 그래서 세션이 바뀌어도 상태가 복원된다.
  답하지 않고 넘길 파일이 있으면 다음 내 파일의 `responds_to`에 넣고 본문에 "확인만"이라고 적는다.

### 5.3 푸시 충돌
- 푸시가 거부되면 `git pull --rebase` 후 다시 푸시한다. 네트워크 오류는 2·4·8·16초 간격으로 4회까지 재시도한다.
- `--force` 푸시는 **금지**다.

## 6. 처리 프로토콜

### 6.1 Opus가 D를 받으면
1. 읽고 5분 안에 `ack`를 푸시한다(작업이 5분 안에 끝나면 `ack` 없이 바로 `progress`).
2. 지침을 저장소 규칙(CLAUDE.md, `docs/handoff/15`, `19`)에 맞춰 실행한다. 커밋은 한 의도씩.
3. 끝나면 `progress`(지침 단위) 또는 `phase_report`(Phase 단위)를 푸시한다.
4. 지침이 규칙과 충돌하면 실행하지 않고 `question`으로 되묻는다(§7).
5. 여러 D가 쌓였으면 `priority` → 번호 순으로 처리한다. `supersedes`로 대체된 D는 건너뛴다.

### 6.2 Fable이 R을 받으면
1. 보고 내용을 저장소 실물(커밋·테스트·산출물)로 확인한다. 보고서 문장만 믿지 않는다(15 P12).
2. `directive`, `answer`, `review` 중 하나를 푸시한다. 할 말이 없어도 `phase_report`에는 반드시 답한다.

### 6.3 phase_report 필수 항목 (KICKOFF §7)
1. 변경 요약(커밋 목록) 2. 테스트 결과(기준선 대비) 3. 프리뷰 컨택트 시트 경로(영상 영향 Phase)
4. provenance 요약 5. 다음 Phase 계획 — 그리고 **이번 Phase의 DECISIONS 새 행 요약**.

## 7. 권한 경계 — 지침으로도 넘을 수 없는 것

Fable의 지침은 사용자의 위임으로 효력을 갖는다. 다만 아래는 **사용자 본인의 명시 승인**이 필요하다.
D 파일에 `from: user`와 사용자 원문 인용이 있거나, 사용자가 대화로 직접 지시한 경우에만 실행한다.
그 외에는 Opus가 `question`으로 사용자 확인을 요청하고 해당 항목만 멈춘다(나머지는 계속).

| 항목 | 근거 |
|---|---|
| 제한 휘장 사용(D5), GOAL 합격 기준 개정(D4), agents_reviewer 스키마 변경(D7) | KICKOFF §7, DECISIONS |
| `main` 머지·태그(M1: Phase 승인 후 ff-only) | DECISIONS M1 |
| PR 생성 | CLAUDE.md C8.5 |
| 푸시된 이력 재작성, force push, `archive/*` 브랜치 삭제 | 되돌릴 수 없음 |
| 비밀 값(.env, API 키) 커밋 | C9 |
| 사실·권리·검증 원칙(GOAL G4, C9) 완화 | C0 경계 |
| v3 합격 수치 변경(근거 없는) | C0, KICKOFF §5 |

새 결정이 생기면 판정 기준 ①되돌릴 수 있는 선택 우선 ②핸드오프 문서를 따름 ③저장소 실측 규칙 우선 +
기록으로 정하고 `docs/handoff/DECISIONS.md`에 한 줄 추가한다.

## 8. 목표와 종료 조건

**목표**: `docs/handoff/KICKOFF_PROMPT.md` §2의 완료 정의 6개 — 골든 재현, 명령→오케스트레이터→워커→엔진 e2e,
레거시 통로 0 + 관성 방지 테스트 8종 전부 통과(xfail 0), 목소리 교체 시 무수정 싱크, 해상도 독립, provenance 증명.

**계획된 Phase** (버전은 `docs/handoff/19` §6 보정표):

| Phase | 버전 | 내용 |
|---|---|---|
| 0 | v2.0.0 | 관성 차단 — **완료** (R-0001) |
| 1 | v2.0.1~ | 골든 재현 (선행: 사용자 WSL2 check_env) |
| 2 | v2.1.0 | 모듈 분해·계약 |
| 3 | v2.2.0 | 지오 일반화 |
| 4 | v2.3.0 | 원고·음성 |
| 5 | v2.4.0 | 뱃지·엔티티·권리 (D5) |
| 6 | v2.5.0 | 패널·카드 데이터화 |
| 6.5 | v2.5.5 | 사진·영상·컷아웃 |
| 6.8 | v2.5.8 | 오케스트레이터 통합 |
| 6.9 | v2.5.9 | AI 연출가·시각 검수 |
| 6.95 | v2.6.0 | 소스 인테이크 |
| 7 | v2.6.1 | 카메라 자동화 보조 |
| 8 | v2.7.0 | 오디오 |
| 9 | v2.8.0 | 번들 어댑터 (D7) |
| 10 | v2.9.0 | 해상도·성능 |
| 11 | v3.0.0 | 문서·정리 (D4) |
| G1~G4 | Phase 6.9 이후 | 장르 확장(`docs/handoff/20` §12) |

**종료**: 위 표의 마지막 Phase가 사용자 승인을 받으면 Opus가 `phase_report`에 `final: true`를 적고, Fable이 `stop`으로 닫는다.
그 전까지는 둘 중 누구도 감시를 멈추지 않는다. 사용자는 언제든 대화로 멈출 수 있다.

## 9. 사용자 개입

- 사용자는 이 폴더에 `D` 파일을 직접 쓸 수 있다(`from: user`). 번호는 Fable의 D 번호를 이어서 쓴다.
- 사용자가 대화로 준 지시는 파일보다 우선한다. Opus는 그 지시를 다음 `progress`에 인용해 Fable도 알게 한다.
