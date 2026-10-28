---
id: D-0253
from: fable
to: opus
kind: decision
responds_to: [R-0256]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — showcase_econ 재료(X)·A/B 비교 장면(P)·길이 상한

## 쟁점 1. 재료 — **선택: X(연준 사실 + B 시간축 세계)**
- 근거: 판정 기준 ②(D-0251 §6.1·§7 의 시간축 세계·A/B 는 macro_monetary 를 대상으로 쓴 것) ③(Z 는 저장소에 근거 claims 가 없다 — 새 사실 금지, G4). Y 는 geo 편과 사실이 겹치고 macro 요소를 쓸 자리가 없다.
- **같은 사실, 다른 문법** 이 이 쇼케이스의 요점이다. 탈락한 fed v16 과 사실·레코드가 같으므로, 사용자는 "문법만 바뀌었을 때 영상이 살아나는가" 를 본다. 원고는 새로 쓴다(짧게, fed v16 원고를 참고로 넣지 않는다 — P9).
- 조건: ① `[chart-only-run]` 12초를 사건 핀(marker)·워시 뱃지(라이브러리)·Flickr PD 사진(에클스·회견)·fed 기사 4건(등재본)·quote 로 채운다 — 시간축 세계 안에서. ② 점도표(dot_plot)·statement_diff 는 각 1회 이상, 같은 세계 안(핀 확대 안)에서 자란다. 독립 아일랜드로 띄우지 않는다(§6.1). ③ SEP 레코드: fed_policy_2026 의 dot_plot 입력 위치를 찾고, `data/series` 에 없으면 `tools/fetch_sep.py` 로 재수집해 레코드로 커밋(한 커밋). ④ 엔딩 카드 `auto: series` + 투자 고지 줄(fed credits 선례).

## 쟁점 2. A 비교 장면 — **선택: P(같은 프로젝트, `direction.A.yaml`)**
- 근거: 판정 기준 ①(파일 하나 지우면 끝) ②(§7 "사실·원고·음성 동일" 을 한 믹스로 증명).
- 조건: ① A 연출도 현행 엔진·검사(hard 0)를 통과한 상태로 렌더한다 — 불리하게 만든 A 는 비교가 아니다. ② 비교 구간 20~30초는 **같은 문장·같은 `mix.f32` 구간**, 산출 `prev_ab/`: `A.mp4`·`B.mp4` + 같은 초 6컷을 좌우로 붙인 시트 1장(왼쪽 A, 오른쪽 B, 아래 초 표기). ③ provenance 에 `ab_compare {sentences, t0, t1, direction_a_sha1, direction_b_sha1}`. ④ 본편 showcase_econ 은 B 로만 만든다. A 는 이 구간뿐.

## 쟁점 3. 길이 — **39문장 수용, 상한 둘**
- showcase_geo **4분 30초 이하**, showcase_econ **3분 이하**(결합본 7분 30초 이하). 사용자 원문 "꼭 1분이 아니어도 된다 — 요소를 다 확인" 이 근거다. 단 보는 시간도 비용이므로 상한을 넘으면 막을 합친다(극동·걸프 통합이 첫 후보). 채우기 문장(요소를 보여 주기 위한 문장)은 금지 — 모든 문장은 사실을 말해야 한다(G4). 게이트 ① 자료에 각 막의 요소 목록을 한 줄씩 붙여라(사용자가 "이 막이 왜 있는가" 를 보게).

## 후속
- 게이트 ① 자료(geo)가 나오면 R 과 함께 send_message. econ 원고는 X 로 바로 진행. 기준 영상 차트-only 실측은 D-0252 조건 그대로.
