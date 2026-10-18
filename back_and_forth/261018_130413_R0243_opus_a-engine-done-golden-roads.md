---
id: R-0243
from: opus
to: fable
kind: progress
responds_to: [D-0230]
phase: "P3-1"
version: v7.4.0
commit: 92f30b9c
status: awaiting_decision
---

# A 단계 완료 — 엔진·규칙 보강(D-0229 §2.1~2.10) + 골든 실측

D-0230 결정(장면 경계 B·범위 X)은 7a16a066 에 반영했다(§5 테스트 5항목 포함). 골든 변화 1건은 R-0244 결정 요청으로 따로 올린다.

## 1. 커밋(항목마다 하나)
| 항목 | 커밋 | 내용 |
|---|---|---|
| 버전 | d683e3e3 | v7.4.0 |
| 2.1-1 | f511f838 → 92f30b9c | 수도 상시 표기 `labels.capital_always`. 골든 light 실측에서 NE `Admin-1 capital`(담맘·라스알카이마·푸자이라 등)까지 켜지는 결함을 찾아 **나라 수도만**(places `cap0` = Admin-0 capital)으로 보정 |
| 2.1-2 | fc7c4491 | 도로·강 레이어(NE 10m, 공개 도메인). `type` 열 매핑: Major Highway→motorway, Secondary Highway→trunk, Road→primary(Unknown·Ferry·Track 제외). 강 = `scalerank` ≤ 5 큰 강(`geo.river_major_scalerank_max`, 볼가·아무르·티그리스·유프라테스·네바). 두 테마 토큰은 지침 값 그대로. 옛 geo.pkl = 오류 |
| 2.2 | 0f5e125b · 7a16a066 · ec721c97 | role(intro·outro·bridge·background)·stage·kind, bridge 앞 호흡 1.5초, plan `transitions[]`, 날짜 배지 xfade(bridge 문장에서만 — 골든 무변화), `[transition-bridge]` hard(D-0230), `[transition-in-scene]` warning, `[transition-camera]` hard(전환 카메라 이동 ≥ 4초) |
| 2.3 | babe8744 | `[cutaway-churn]` hard. 전면 = `qa_checks.cutaway_full_types: [article, backdrop]`(사진·영상은 상자 배치라 지도가 보임). v1 연출에서 6곳 재현(오프닝 27.0초 포함) |
| 2.4 | e9e2b3b5 | `fonts.unit_font: sans` — display 숫자 뒤 라틴 단위(t·kb/d·mb/d·bbl)를 Plex Sans KR 같은 굵기로. `%`·`$` 는 제외(골든 카드 보호). `[unit-glyph-font]` hard |
| 2.5 | 37b93af9 | route `declared{label, bend_index, place}` — 꺾임점까지 muted 점선+신고 라벨, 뒤 col 실선 |
| 2.6 | 06658f4e | dots `total`(≤20 이면 한 줄 큰 점)·`accent`·분수 big. `[ratio-without-graphic]` 은 원고 린트가 아니라 **검사(warning)** 로 — 연출의 패널을 봐야 판정되므로 |
| 2.7 | ac4f1373 | `inset.hold_until`(명시)·`inset.place`(같은 장소 연속 문장 동안, `flight.inset.hold_same_place`)·대각 자리 4종, `[inset-overlap]` warning |
| 2.8 | f4a79cd7 | `[verb-target-mismatch]` hard·`[contrast-conjunction]` warning(v1 cold_2·act1_0·act1_2 정확히 재현), 원고 규약 줄 |
| 2.9 | 83a30721 | `rules tempo`, `[act-frame]` hard(bridge 를 도입으로 셈), `[tempo-density]` warning(원고·검사 같은 함수), `order.yaml tempo: breath` → 문장 간격 0.9초 |
| 2.10 | 3c091c9e | 엔딩 카드 표기 전용 줄(`credits slot: notice`, 구분선 위, 열 한도에서 그 높이 뺌), 열 폭 넘는 항목 줄바꿈. 트럼프 뱃지·빈 지도 country 강조는 연출(C)에서 |
| §5 | 03c74a5b | provenance `map_layers{roads,rivers,capitals}`·`transitions[]` |
| §6 | 71bd7676 | UF-101·102·104~115 장치 기입(미보호 0, `tests/anti_inertia/test_user_feedback_guards.py` 통과) |

새 테스트 10개 파일: test_v740_map_layers·transition·cutaway_churn·unit_font·route_declared·dots_ratio·inset_hold·script_vocab·tempo·endcard_notice·article_press.

## 2. 판단 기록(지침 밖 구현 세부 — 되돌리기 쉬움)
- `[act-frame]` 옛 원고 면제는 D-0230 §3 을 같은 이유로 **준용**했다(18개 프로젝트 149행, 결정자 칸 D-0230). 이의가 있으면 되돌린다.
- 도로·강·행정선 그리기 순서: 지형 → 강 → 도로 → 해안·국경 → 행정선(기존 순서 유지). 지침의 "행정선 → 도로 → 국경" 은 행정선을 국경 앞으로 옮겨야 해 골든이 바뀌므로 하지 않았다.
- 콘티 판(막지도 FlatMercatorStage)에는 도로·강·지명이 없다(D-0108 설계 그대로).

## 3. 테스트
- 변경마다 관련 테스트 파일 + `tests/anti_inertia -m "not slow"`: 매번 58 passed.
- 영향 묶음(-n 4): 원고·린트 41파일 342 passed / 검사 401 passed / 글꼴·패널 313 passed / provenance 322 passed / 엔딩 카드 207 passed(실패 2건은 테스트 가짜 객체에 slot 추가로 해결).
- 전체 pytest 는 아직 돌리지 않았다(main 병합 직전, C8.3).

## 4. 골든 dark·light 25컷 — 환경 의존과 이번 변경 분리
- **이 컨테이너에서는 main(372be03) 자체도 V3·Q3 기준선 md5 를 25/25 못 맞춘다.** 같은 자산(plan 260.658초 동일)으로 main 워크트리를 렌더해 확인. 원인은 환경(글꼴 빌드·cairo·타일 재수신 중 하나로 추정, 미확정) — D-0228 과 같은 환경 의존으로 본다.
- 그래서 **같은 컨테이너·같은 자산에서 main 과 이 브랜치를 화소 비교**했다.
  - dark 17컷·light 17컷이 다르다. 그중 25_END 는 버전 도장(v7.3.0→v7.4.0, 가림 대상)뿐.
  - 나머지 16컷의 차이는 **전부 도로·강 레이어**다: 도로·강을 끄고 렌더하면 main 과 도장 외 바이트 동일, 수도 상시(나라 수도만)는 차이 0.
  - 근접 숏(w 3.3~6.4: 한반도·호르무즈)은 도로·강, w 13~24 숏은 큰 강(티그리스·유프라테스) 선이 더해진다.
- 전후 시트: `docs/handoff/reports/phaseV740/golden_dark_before_after.jpg`, `golden_light_before_after.jpg`, 확대 `p_0006.95_roads_crop_x2.png`(왼쪽 main·가운데 v7.4.0·오른쪽 차이×4).
- `test_provenance_e2e` 의 검사 수 기대값을 64 → 71(새 검사 7)로 고쳤다(이 R 커밋에 포함). 기준선 md5 는 결정(R-0244) 전이라 손대지 않았다.

## 5. 다음
- R-0244 결정과 별개로 B(원고 v2)는 진행했다 — R-0245(게이트 ① 자료)를 바로 올린다.
