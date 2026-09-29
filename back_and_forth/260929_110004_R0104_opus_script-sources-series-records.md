---
id: R-0104
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G3"
version: v4.3.0
commit: 32697e0
status: in_progress
---

# 결정 요청 — 원고 문장의 출처로 데이터 레코드를 가리키는 방법(작업 6)

## 쟁점
실증 원고(`projects/fed_timeline_demo/script.yaml`, 10문장)는 두 레코드의 값·날짜만 말한다.
`script.lint` 는 수치·날짜 문장의 `sources` 가 비면 **오류**다(v3.2.0 D-0051). `sources` 는 `intake/claims.json` 의 claim id 만 받는다.
claim 은 기사·게시물 인용 대조(D50·D53)용이다. 데이터 레코드를 가리킬 자리가 없다. 실측: lint 오류 8건(`[source-missing]`), plan·TTS 로 못 간다.

## 선택지

### A. `sources` 에 `series:<series_id>` 참조를 허용 + 수치 대조 — 권고
- 문법: `sources: ["series:FEDFUNDS"]`. 레코드(`data/series/<id>.yaml`)가 있으면 통과, 없으면 `source-unknown` 오류.
- **대조 린트(새 오류 한 줄 두 가지)**: 문장이 가리킨 레코드의 **문장 date 달 값**과 자막의 `N%`·`N%p` 가 다르면 오류(20 §9-4 "숫자가 화면과 내레이션에서 일치"). 문장 date 달이 레코드 `missing` 이면 값(`N%`)을 말할 때 오류(D-0086 보정 2 그대로).
- 검증 라벨: series 참조는 claim 이 아니므로 라벨 계산에서 빠진다(라벨 없음). 레코드 자체가 공식 1차 자료·라이선스·as_of 를 가진다(20 §5.1).
- 엔딩 카드: 이미 `auto: series` 절(레코드 출처·라이선스 표기 원문·기준 시점)로 나온다(작업 6 준비 커밋).
- 되돌리기: lint 분기 하나.

### B. intake/sources.json·claims.json 에 레코드를 claim 으로 넣는다
- 기존 경로 그대로. 대신 claim 의 status(verified·corroborated)를 사람이 손으로 정해야 한다. 인용 대조(D50) 없이 status 를 적으면 검증 기록을 지어내는 셈이다(G4 원칙에 어긋남).
- 수치 대조는 없다.

### C. 실증 원고만 lint 예외
- 규칙 예외를 만든다. 비권고(P6).

## Opus 권고 — A
- ② 문서: 20 §5.1 "모든 데이터는 레코드로", §9-4 숫자 일치, D-0086 보정 2(빈 달 값 금지 린트)를 한 곳에서 구현한다.
- ① 되돌리기: lint 한 분기. 기존 claim 경로·라벨 규칙은 그대로.
- 보강: 원고의 수치를 레코드와 코드가 대조한다 — 사람 손 대조보다 강하다.

## 근거 자료
- `script/lint.py:240-250`(source-missing·source-unknown), `script/labels.py:check_project_labels`.
- 원고 초안 `projects/fed_timeline_demo/script.yaml`(아직 미커밋), 레코드 `data/series/*.yaml`.

## 막히는 범위
- 기다림: 작업 6 의 plan·TTS·프리뷰·mp4.
- 계속함: 작업 6 준비(Assets geo 선택·지도 자산 권리 조건·엔딩 카드 auto: series), 작업 7 회귀, 작업 8 문서.

## §7 해당 여부
아니다.
