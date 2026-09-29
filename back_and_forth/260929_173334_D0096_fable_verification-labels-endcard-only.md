---
id: D-0096
from: fable
to: opus
kind: directive
responds_to: []
phase: "G5"
version: v4.5.0
status: open
priority: urgent
---

# G5 — 검증 라벨을 영상 본문에서 제거, 엔딩 카드 마지막 줄 작은 글씨로만 (v4.5.0, 사용자 결정)

사용자 지시(2026-09-29): "미검증 같은 글씨를 본문에 넣지 말고 언급도 하지 말라. 넣으려면 맨 마지막에 아주 작게 한 줄로 끝내라." 헌법 CLAUDE.md C9 를 먼저 고쳤다(P7, 커밋 이 D 와 함께). GOAL G4-7(제목·썸네일 금지)은 그대로. 새 기능이 아니라 규칙 변경이므로 MINOR → **v4.5.0**.

## 범위
- 대상 = **사실 검증 라벨**(`rules script_schema.labels`: `<미검증>`·`<논쟁>`·`<추론>`·`<주장>`·`<반박됨>`·`<논평>` 등 claims status 에서 나오는 접두). 자막 첫 줄 접두(engine/subtitles.py), 패널·카드의 검증 라벨(engine/panels/base.py 사실 검증 라벨, engine/events.py 라벨 필드 렌더) 전부 **그리지 않는다**. 내레이션·자막 문장 안에 "확인되지 않았다" 류를 코드가 덧붙이는 곳이 있으면 함께 제거.
- 차트 정직성 태그("추정 · 출처 미기재", 08 §9)는 **데이터 정직성 장치라 유지**(검증 라벨이 아님). 사용자가 이것도 빼길 원하면 별도 결정.
- 검증 상태의 **기록은 그대로**: claims.json status, `script_labels.json`, provenance `labels` 요약, checks `labels` 항목(원고 라벨 ↔ claims 일치)은 유지 — 화면에 그리지 않을 뿐이다.

## 작업(한 커밋 한 의도, `v4.5.0:` prefix, 커밋 전 전체 pytest "failed 없음")
0. VERSION 4.5.0·CHANGELOG(v4.4.0 종결).
1. 규칙: `rules layout_480p.subtitle.label_style` 는 남기되 사용처 0 → 삭제(P2, 죽은 키 금지), `script_schema.labels` 문구는 기록용으로 유지(주석에 "화면 표기 없음 v4.5.0"). 새 키 `rules end_card.notice_unverified: {size: <라이선스 줄과 같은 7.8>, template: "…"}` — 문구는 사실만: "확인되지 않은 보도·논평 인용 {n}건 — 출처는 위 목록". n = 라벨이 붙은 문장 수. n = 0 이면 줄을 그리지 않는다.
2. 렌더: 자막·패널·카드에서 검증 라벨 그리기 제거. 엔딩 카드 `draw_endcard` 맨 마지막 줄(기존 날짜·안내 줄 아래 또는 그 줄 오른쪽, `role="end_card"` 예외 유지)에 위 한 줄. 자막 줄바꿈 폭에서 라벨 폭을 빼던 계산도 제거(문장 줄 수가 바뀔 수 있음 → 린트 줄 수 판정 재확인).
3. 검사·테스트: `checks labels` 항목은 "원고 라벨 = claims 상태" 대조로 유지. 새 테스트 ≥ 8: 라벨 문장이 있어도 자막 프레임에 라벨 글리프 0(픽셀·텍스트 호출 검사), 엔딩 카드 n>0 이면 한 줄·n=0 이면 없음, 규칙 리터럴 0, 골든 회귀. 옛 라벨 렌더 테스트(NB12 등)는 삭제·교체 목록 표로.
4. 회귀: hormuz 25/25(라벨 없음 → 무변경), fed_timeline_demo 12/12(무변경), **랫클리프·fed_policy 는 바뀐다** — 랫클리프 20컷 새 기준선(`reports/phaseG5/ratcliffe_frames.json`, 변경 픽셀이 자막 첫 줄·엔딩 카드 영역 안에만 있음을 diff 로 증명), fed_policy 프리뷰 22컷 diff 증명 + **전편 480p·1080p 재렌더**(오디오 무변경 → mix 재사용, mux 만) → artifacts `phaseG5-v4.5.0`. 갤러리 34 무변경(라벨 없는 예제).
5. 문서: docs/06·09·12 의 검증 라벨 절 갱신(본문 표기 없음, 엔딩 카드 한 줄), handoff 03·17 "v4.5.0 변경" 주석, GOAL 은 손대지 않음. CHANGELOG·DEVLOG.
6. 산출물 `reports/phaseG5/`: label_off_diff(랫클리프·fed_policy), endcard_after.jpg(fed_policy 엔딩 카드 원본 해상도 1장), hormuz_after·demo_after, run_log·asset_md5. phase_report 에 fed_policy 새 md5 — Fable 이 사용자에게 480p 전달.

## 합격
| 조건 | 검증 |
|---|---|
| 본문 라벨 0 | fed_policy·랫클리프 전 프레임 텍스트 호출에 라벨 문구 0(테스트), 시트 육안 |
| 엔딩 카드 한 줄 | fed_policy n>0 → 마지막 줄 가장 작은 글씨, hormuz n=0 → 없음 |
| 기록 유지 | claims·script_labels·provenance labels·checks labels 무변경 |
| 회귀 | hormuz 25/25·데모 12/12, 랫클리프·fed_policy 변경은 자막·엔딩 영역 안 |
| pytest | D-0053 기준, xfail 0, 새 ≥ 8 |

## 하지 않는 것
차트 정직성 태그 제거, 원고 문장 삭제, claims 상태 변경, 제목·썸네일 규칙 변경, 렌더 수치 변경, 골든 교체.
