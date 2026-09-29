---
id: D-0101
from: fable
to: opus
kind: directive
responds_to: []
phase: "G7"
version: v4.7.0
status: open
priority: normal
---

# G7 — 요소 크기: 인물 배지 적응 크기·기사 카드 조판 확대·전체 크기 점검 (v4.7.0, 사용자 결정 D89)

사용자 지시(2026-09-29 20:1x KST, fed_policy 480p 를 보고): "인물 이미지가 나올 때 그때그때 적절한 크기로. 한 사람만 나오면 크게 확대하고, 여러 사람이 더 등장하면 작아지는 효과. 기사가 나올 때는 기사를 조판해서 좀 크게. 전체적으로 요소들이 너무 작다."
사용자 결정이므로 v3 합격 크기 값(배지 R·카드·글자)은 **바뀌어도 된다**(README §7.2 예외, 근거 = 사용자 지시, 되돌리기 = 규칙 값 revert + 골든 기준선 복귀). DECISIONS D89 는 Fable 이 기록했다.

**착수 시점: G6(D-0097) phase_report → Fable 합격 D 이후.** 사전 예고이며 G6 보고 전 ack 불필요.

## 배경(저장소 실측)
- 인물 배지: `rules badge.R_person_map [30,34]`·`R_person_panel 36`, 연출 `R:` 없으면 코드 기본 30(`badges.badge_at` 리터럴 — P3 위반, 이번에 규칙으로). 크기는 **동시에 몇 명이 보이는지와 무관**하게 고정. 시간축 배지 자리 `timeline_badge [780,118]`.
- 기사 카드: `article_card {w: 300, y: 68}`, 글자 크기가 `draw_article` 리터럴(매체 12.5·날짜 8.5·헤드라인 13.5·부제 9.5·ARTICLE 7.5·메모 7.8) — 480p 설계에서 헤드라인 13.5 는 자막(19)보다 작다. P3 위반이기도 하다.
- 전체: 카드 `line_size 13·tag 10.5·src 9.5`, 패널 부제 11, 미디어 캡션 7.8, 시간축 글자 B(D-0092) 등 11 미만 글자가 많다.

## 설계(결정)
### 1. 인물 배지 적응 크기(코드가 계산, 연출은 배치만 — P8)
- 규칙 `badge`: `R_person_solo: 56`(새), `R_person_group: [30, 34]`(= 지금 R_person_map, 이름 바꿈), `resize_sec: 0.6`, `label_size_solo/group`(이름표 글자 solo 15/역할 11 · group 12/10 — 지금 리터럴 12·13·10 을 규칙으로), `R_default` 리터럴 30 삭제.
- 렌더: 시각 t 에 **같은 무대(view)에서 보이는 person 배지 수 n(t)** 를 코드가 센다(팝인 완료 기준). n=1 → solo R, n≥2 → group R. R 은 `resize_sec` 동안 ease 로 보간(커졌다 작아지는 효과 = 사용자가 말한 "여러 사람이 더 등장하면 작아진다"). 결정적(t 만의 함수).
- 연출 `R:` 를 명시하면 그 값 우선(hormuz 부산 국기 R 18 처럼). person 이외(flag·emblem)는 무변경.
- 예약·밀기(`reserve_top_factor`·`badge_strategy push`)·`avoid_badge`·화면 밖 검사(D-0048 clip guard)는 **현재 R** 기준으로 계산. solo 배지가 `timeline_badge [780,118]` 에서 오른쪽·위로 잘리면 슬롯 point 를 규칙에서 옮긴다(수치 근거 phase_report). 자막 구역(y≥410)·카드 구역 침범 금지.
### 2. 기사 카드 조판 확대
- `article_card: {w: 440, y: 60, pad: 20, pub_size: 15, date_size: 10, headline_size: 18, headline_gap: 26, sub_size: 12, sub_gap: 17, meta_size: 9}` — draw_article·article_geom 리터럴 전부 규칙으로. 헤드라인 최대 3줄, 부제 최대 3줄, 넘치면 오류(조용한 잘림 금지).
- 위치: 기본 오른쪽(카드 자리). 연출 `place: center` 면 무대 가운데(x 가운데 정렬, 그 동안 아래 지도·시간축은 `dip` 과 같은 어둡기). fed_policy 기사 2건은 center 로 바꾼다(연출 파일 수정 = 이번 D 의 지시).
- 등장: 지금 슬라이드+페이드 유지. 유지 시간은 연출 그대로.
### 3. 전체 크기 점검(2단계 — 값은 Fable 이 결정)
- 1단계(이 Phase 안, 결정 요청): 화면 글자 크기 키 전수 표(규칙 키·현재 값·리터럴 위치·제안 값). 제안 기준: 480p 설계에서 본문성 글자 ≥ 12, 메타(출처·라이선스·ARTICLE) ≥ 9, 자막 19→21 검토, 카드 line 13→15·tag 10.5→12·src 9.5→11, 패널 부제 11→12.5, 미디어 캡션 7.8→9. 엔딩 카드·시간축 글자(D-0092 B)·모서리 날짜는 제외. **전/후 컨택트 시트**(hormuz 6컷 + fed_policy 6컷, 같은 시각) 를 `reports/phaseG7/scale_before_after.jpg` 로 첨부해 decision_request 로 올린다.
- 2단계: Fable 결정 값 적용 → 회귀 기준선 갱신.

## 작업(한 커밋 한 의도, `v4.7.0:` prefix, 커밋 전 전체 pytest 로그에 failed 없음, 미커밋은 WIP 커밋)
0. VERSION 4.7.0·CHANGELOG(v4.6.0 종결).
1. 배지 규칙·렌더(§1) + 테스트(solo→group 축소 시각·길이, 규칙 값 사용, R 명시 우선, 리터럴 0, clip guard).
2. 기사 카드 규칙·렌더(§2) + fed_policy 연출 `place: center` + 테스트(기하가 규칙에서, 넘침 오류, 리터럴 0).
3. §3 1단계 decision_request(표 + 전/후 시트) → Fable 결정 → 적용 커밋.
4. 회귀: hormuz 골든 25컷은 **바뀐다**(배지·카드·글자) — `expected_deltas.json` 에 `g7_scale_d0101` 등록 + `reports/phaseG7/golden_delta/` 전/후(D-0079 방식), 변경 픽셀이 배지·카드·글자 영역 안임을 diff 로 증명. 랫클리프·데모·fed_policy 기준선 재등록. 갤러리 34 갱신. checks hard 0.
5. fed_policy 480p·1080p 전편 재렌더 → artifacts `phaseG7-v4.7.0`; hormuz 480p 재렌더(사용자 비교용).
6. 문서: handoff 07(배지 적응 크기)·08(기사 카드 조판)·09(글자 크기 표) "v4.7.0" 절, docs/05·07 요약본 한 줄, CHANGELOG·DEVLOG.
7. 산출물 `reports/phaseG7/`: badge_solo_group.jpg(한 명 → 두 명 등장 전/중/후 3컷), article_before_after.jpg, scale_before_after.jpg, golden_delta/, run_log·asset_md5. phase_report 에 새 md5 — Fable 이 사용자에게 480p 전달.

## 합격
| 조건 | 검증 |
|---|---|
| 배지 적응 | fed_policy·hormuz 에서 solo 구간 R = R_person_solo, 두 번째 인물 팝인 뒤 resize_sec 안에 group R(프레임 실측 3컷), 잘림 0, 자막·카드 구역 침범 0 |
| 기사 카드 | fed_policy 기사 2건 center·w 440·헤드라인 18, 넘침 0, 전/후 시트 |
| 전체 크기 | §3 결정 값 적용, 리터럴 0(test_no_magic_numbers 확장), 전/후 시트 |
| 회귀 | expected_deltas 등록·diff 증명, checks hard 0, 갤러리 34 |
| pytest | 로그에 failed 없음, 새 ≥ 10 |
| 영상 | fed_policy 480p·1080p·hormuz 480p 새 md5 — 청감·시감 최종 판정은 사용자 |

## 하지 않는 것
연출 구성 변경(카드·기사 위치 place 지정 외), 카메라·타이밍 변경, 엔딩 카드·시간축 글자·모서리 날짜 크기 변경, 골든 PNG 를 근거 없이 교체(expected_deltas 로만).
