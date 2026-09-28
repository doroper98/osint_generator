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

## 2. 파일 명명법 (사용자 지시 2026-09-28 재개정 — 시각 우선, ls 정렬 = 대화 순서)

```
{yymmdd}_{hhmmss}_{종류}{번호4자리}_{작성자}_{slug}.md
```

| 종류 | 작성자 | 뜻 |
|---|---|---|
| `R` | `opus` | 보고(Report) — 작업 결과·진행·질문·막힘·결정 요청 |
| `D` | `fable` (또는 `user`) | 지침(Directive)·결정·답변·검토 |

- **시각이 맨 앞**이다. **KST(UTC+9)** `yymmdd_hhmmss`, 파일을 만든 시각(사용자 지시 2026-09-28 — UTC 표기 금지). 그래서 `ls` 한 번에 R과 D가 주고받은 순서로 섞여 보인다.
  (2026-09-27 체계 `{종류}{번호}_{작성자}_{시각}_{slug}`는 종류별로 묶여 대화 순서가 끊겼다 → 재개정.)
- 종류 뒤에 번호, 그 뒤에 작성자. 모델 버전은 쓰지 않는다(`opus`, `fable`, `user`).
- **번호**는 종류별로 1씩 증가(`R0001`, `D0001` …). 건너뛰거나 재사용하지 않는다. 머리말 `id`는 종전대로 `R-0001` 형식.
- **slug**는 영문 소문자·숫자·하이픈 3~6단어.
- 예: `260928_012218_R0020_opus_word-anchor-edge-boundary.md`, `260928_012815_D0026_fable_edge-word-boundary-align.md`.
- 다음 파일 이름은 `python back_and_forth/check.py --me opus --next-name {slug}`로 만든다(틀리지 않는다).
  출력은 파일 이름만이다. **`back_and_forth/` 아래에** 만든다.
- 이전 체계의 파일은 **이름만** 바꿨다(내용 무수정, 번호 보존, UTC 시각은 +9시간으로 KST 환산). `check.py`는 새 이름만 인식한다.
- 번호 충돌을 막기 위해 **R은 Opus만, D는 Fable(사용자)만** 만든다.

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
status: done               # R: done | in_progress | blocked | question | awaiting_decision  /  D: open | superseded
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
| `decision_request` | Opus | **결정이 필요할 때 항상**(§6.4). Opus는 혼자 결정하지 않는다 |
| `question` | Opus | 지침의 뜻이 불분명하거나 규칙과 충돌할 때 |
| `blocked` | Opus | 권한·환경·외부 요인으로 진행이 불가능할 때 |
| `directive` | Fable | 다음 작업 지시, 수정 요청 |
| `decision` | Fable 또는 user | `decision_request`에 대한 결정(§6.4) |
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
2. `directive`, `decision`, `answer`, `review` 중 하나를 푸시한다. 할 말이 없어도 `phase_report`에는 반드시 답한다.
3. `decision_request`는 다른 R보다 먼저 처리한다. Opus의 일부 작업이 그 결정을 기다리고 있기 때문이다.

### 6.3 phase_report 필수 항목 (KICKOFF §7)
1. 변경 요약(커밋 목록) 2. 테스트 결과(기준선 대비) 3. 프리뷰 컨택트 시트 경로(영상 영향 Phase)
4. provenance 요약 5. 다음 Phase 계획 — 그리고 **이번 Phase의 DECISIONS 새 행 요약**.

### 6.4 결정 위임 — 결정은 Fable이 내린다 (사용자 지시 2026-09-27)

**결정의 범위**: `docs/handoff/DECISIONS.md`에 한 줄로 남을 만한 것 전부다.
- 핸드오프 문서와 저장소 실측이 충돌할 때, 문서 간 불일치, 명세에 없는 설계 선택
- 명세에서 벗어나는 구현(범위 축소·확대, 순서 변경, 대체 방법)
- 수치·임계값·기본값 선택, 도구·라이브러리 선택, 테스트 합격 기준 해석

**결정이 아닌 것**(Opus가 그대로 진행): 명세가 이미 정한 것을 그대로 옮기는 구현 세부(변수명, 파일 내부 구성,
명세 범위 안의 리팩터링), 저장소 규칙이 이미 답을 정한 것(커밋 형식, 테스트 실행 등).

**Opus 절차**
1. 결정이 필요해지면 그 자리에서 혼자 정하지 않고 `decision_request` R을 푸시한다.
2. 본문 필수 항목:
   - **쟁점** — 무엇을 정해야 하나(한두 문장)
   - **선택지** — 최소 2개. 각 선택지의 결과·위험·되돌리는 방법
   - **Opus 권고** — 판정 기준 ①되돌릴 수 있는 선택 우선 ②핸드오프 문서를 따름 ③저장소 실측 규칙 우선+기록 에 따른 권고와 근거
   - **근거 자료** — 문서 절·파일 경로·커밋·실측 결과
   - **막히는 범위** — 이 결정을 기다리는 작업과, 기다리지 않고 계속할 수 있는 작업
   - **§7 해당 여부** — 사용자 고유 결정이면 명시
3. 결정을 기다리는 동안 **막히지 않는 작업은 계속**한다. 결정이 필요한 부분은 구현하지 않는다
   (권고안으로 먼저 만들어 두는 것도 금지 — 되돌리기 비용이 결정을 기울인다).
4. `decision` D를 받으면 그대로 따르고, `DECISIONS.md`에 한 줄 추가한다.
   결정자 칸은 `Fable (back_and_forth D-000N)` 또는 `사용자 (D-000N)`.
5. 모든 막힌 작업이 결정을 기다리면 R의 `status: awaiting_decision`으로 알린다.

**Fable 절차**
1. 선택지·근거를 저장소 실물로 확인한 뒤 `decision` D를 쓴다. 필수 항목: **선택**, **근거**(판정 기준 번호),
   **조건·후속**(검증 방법, 되돌릴 조건).
2. 선택지가 부족하면 새 선택지를 제시해 결정해도 된다. 정보가 부족하면 `answer`로 추가 조사를 요청한다.
3. **§7 항목은 Fable이 결정하지 않는다.** 사용자에게 직접 묻고, 답을 받으면 원문을 인용해 `decision` D(`from: user`)로 남긴다.

### 6.5 Phase 전환과 main 머지 (사용자 지시 2026-09-27 — 개입 없이 끝까지)

- Phase가 끝나면 Opus는 `phase_report`를 쓰고 Fable의 `review`를 기다린다. 스스로 넘어가지 않는다.
- **Fable의 `review` verdict `pass`가 곧 Phase 승인이다.** 사용자 승인은 따로 받지 않는다.
- pass 직후 **Fable이 main을 fast-forward한다**: `git push origin overhaul/v2-map-engine:main` (ff만, 실패하면 멈추고 원인을 D에 기록). 그다음 다음 Phase 착수 `directive`를 낸다.
- **태그는 두 세션 모두 원격 푸시가 막혀 있다(403).** 대신 `docs/handoff/TAGS_PENDING.md`에 `버전 → 커밋`을 한 줄씩 append한다. 사용자가 원할 때 PC에서 한꺼번에 올리면 되고, 올리지 않아도 진행에 영향이 없다.
- 사용자가 대화나 `from: user` D로 Phase를 멈추거나 되돌리면 그 지시가 우선한다.

## 7. 금지 항목과 Fable 전결 (사용자 지시 2026-09-27)

사용자 원문: "내 결정 없이 끝까지 너(fable)랑 구현자(opus)가 의논해 가며 진행하라는게 내 의도였어."
따라서 **사용자에게 묻는 항목은 없다.** 아래 두 표만 남는다.

**7.1 누구도 하지 않는 것 (지침으로도 금지)**

| 항목 | 근거 |
|---|---|
| PR 생성 | CLAUDE.md C8.5 |
| 푸시된 이력 재작성, force push, `archive/*`·`artifacts/*` 브랜치 삭제 | 되돌릴 수 없음 |
| 비밀 값(.env, API 키) 커밋 | C9 |
| 사실·권리·검증 원칙(GOAL G4, C9) 완화 | C0 경계 |
| 사용자 외부 계정·서비스 조작(agents_reviewer 저장소 수정, 유튜브·텔레그램) | 범위 밖(KICKOFF §3) |

**7.2 Fable이 전결하는 것 (옛 "사용자 고유 결정")**

| 항목 | 기본 원칙 |
|---|---|
| D5 제한 휘장 | 위키미디어 `Restrictions`(insignia·trademarked·personality)가 있으면 **쓰지 않고 국기로 대체**, 레지스트리에 사유 기록. 예외 없음 |
| D7 agents_reviewer 스키마 | 저장소 밖이라 **제안 문서만** 작성(`docs/handoff/reports/`), 반영은 하지 않음 |
| D4 GOAL G3 개정 | 결정 완료(D-0005), Phase 11 반영 |
| v3 합격 수치 변경 | **유지가 기본.** 바꾸려면 골든 25컷 회귀 + 근거 + 되돌리는 방법을 `decision_request`로, Fable이 결정·기록 |
| main 머지·태그 | §6.5 |

새 결정은 §6.4대로 Fable이 내린다. Opus는 판정 기준 ①②③으로 **권고**만 하고, 결정이 오면 `DECISIONS.md`에 기록한다.

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

**종료**: 위 표의 마지막 Phase가 Fable `review` pass를 받으면 Opus가 `phase_report`에 `final: true`를 적고, Fable이 `stop`으로 닫은 뒤 사용자에게 최종 보고한다.
그 전까지는 둘 중 누구도 감시를 멈추지 않는다. 사용자는 언제든 대화로 멈출 수 있다.

## 9. 사용자 개입

- 사용자는 이 폴더에 `D` 파일을 직접 쓸 수 있다(`from: user`). 번호는 Fable의 D 번호를 이어서 쓴다.
- 사용자가 대화로 준 지시는 파일보다 우선한다. Opus는 그 지시를 다음 `progress`에 인용해 Fable도 알게 한다.
