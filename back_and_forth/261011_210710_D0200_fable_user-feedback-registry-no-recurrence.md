---
id: D-0200
from: fable
to: opus
kind: directive
responds_to: []
phase: "P1-6"
version: v5.21.7
status: open
priority: urgent
supersedes: []
---

# 사용자 지시 — "코멘트한 사항은 모두 기록되고 재발이 되면 안 된다" : 사용자 의견 원장 + 재발 방지 장치 강제

사용자 원문(2026-10-11): **"내가 코멘트 한사항들은 모두 기록되고 재발이 되면 안돼."**

감독이 사람용 원장 `docs/handoff/USER_FEEDBACK_LEDGER.md`(UF-01~UF-12, 원문 그대로)를 먼저 만들었다. 이 지시는 그것을 **코드가 강제하는 장치**로 만든다.
UF-02(카메라 꺾임)가 바로 "기록은 있었는데 장치가 한 트랙에만 걸려 재발한" 사례다 — 이번 장치의 설계 기준이다.

## 1. 기계 판독 원장(SSOT) — `rules/user_feedback.yaml`
- 항목: `id`(UF-NN) · `date` · `project`·`at`(시각/문장) · `quote`(사용자 원문 그대로) · `category` · `guards[]`(각각 `kind: check|test|rule`, `ref`: checks id·테스트 경로::이름·규칙 키) · `status: open|guarded|recurred` · `recurs_of`(재발이면 원래 번호) · `decision`(D 번호).
- `docs/handoff/USER_FEEDBACK_LEDGER.md` 표는 이 YAML 에서 생성하거나, 적어도 테스트로 두 파일의 번호·원문 일치를 강제한다(값 이중 관리 금지 — 하나가 정본).

## 2. 강제 장치
1. **테스트**(`tests/anti_inertia/test_user_feedback_guards.py`): 모든 항목의 guard 가 실제로 존재한다 — checks id 는 checks 레지스트리에, 테스트는 수집되는 테스트 이름으로, 규칙 키는 규칙 파일에 있다. 없는 guard = 실패.
2. **게이트**: `status: open`(장치 없음) 항목이 있으면 `approve --gate preview_approval` 이 거부된다(require_animatic 과 같은 방식, 우회 플래그 없음). 메시지에 UF 번호와 원문.
3. **저장소 전체 적용**: guard 로 쓰는 checks 는 본 엔진 기본 checks 에 등록되어 모든 프로젝트·모든 렌더 경로(콘티 판·프리뷰·전편)에서 돈다. 스케치처럼 별도 경로가 있으면 그 경로도 같은 규칙 키를 읽는다. 한 경로에만 걸린 guard 는 테스트가 실패시킨다(가능한 범위에서 — 방법을 보고).
4. **provenance**: 영상마다 `user_feedback_guards`(돈 guard id 와 결과)를 남긴다(P5).
5. **재발 처리**: 새 의견이 기존 항목과 같은 종류면 `recurs_of` 로 잇고, 원래 guard 가 왜 못 잡았는지 `docs/ANTIPATTERNS/` 에 AP 항목 + guard 보강.

## 3. 과거 의견 소급
- `docs/handoff/DECISIONS.md` 의 사용자 의견·지적·청취 판정 행(약 55행 중 의견성 항목), back_and_forth 의 `from: user` D, `docs/ANTIPATTERNS/` 의 사용자 지적 유래 항목을 훑어 UF 로 옮긴다(UF-13 부터, 날짜순 번호는 새로 매기지 않고 이어 붙임).
- 각 항목에 이미 있는 guard 를 연결하고, 없으면 `status: open` 으로 남겨 목록을 보고한다. open 을 닫는 장치는 하나씩 PATCH(P12).
- 카메라 멈칫(스케치 S 트랙 사용자 지적)은 UF-02 의 `recurs_of` 대상이 되도록 원 항목을 만든다.

## 4. 헌법
- CLAUDE.md 에 새 절(C12 "사용자 의견 원장 — 기록·재발 방지 의무")을 넣는다: 의견 수신 즉시 원장 기록, guard 없는 의견은 게이트 차단, 재발은 AP+guard 보강. 사용자 지시 원문 인용(P7 — 헌법 먼저).
- `back_and_forth/README.md`·`WORKFLOWS.md` 에 원장 기록 단계를 넣는다.

## 5. 순서
D-0199 재렌더 작업과 **같은 묶음**으로 한다. UF-01~12 의 guard 는 D-0191~0199 에서 만드는 검사들이므로, 그 검사를 만들 때 원장 guard 칸을 채운다. gulf 재렌더 전 게이트에서 UF-01~12 가 모두 `guarded` 여야 한다.
버전: 원장·게이트·테스트 = MINOR(새 Review Gate, C5.4).
