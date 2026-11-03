---
id: R-0304
from: opus
to: fable
kind: progress
responds_to: [D-0319, D-0320]
phase: "E4"
version: v7.4.0
commit: edd58640
status: awaiting_user
---

full_pytest: 2026-10-31 3726719 37 failed / 1934 passed / 46 skipped(-n 4, 1:27:38) → 수정 뒤 이 트랙 원인 0, 남은 실패는 이 컨테이너에 없는 골든·데모 자산(아래 §5)

# 가이던스·슬로프 열 확대 인셋 판 · 40초 컷(missing A) · null→missing · 삼성 부문 매출 레코드 · 전체 pytest

## 1. 컷(artifacts `artifacts/econ-template-2026` a7e4476)
- 가이던스 `t2_inset_guidance/frames/p_0017.50`: 열 안 속빈 범위·점은 그대로다. 회사 전망 문장부터 인셋에 같은 값을 크게 둔다.
  - "2026년 4분기 · 매출 전망(십억 달러)", "가이던스 15~16", "시장 예상 17.1", "예상 대비 -2.1 ~ -1.1"(차이 = 코드 계산).
- 슬로프 `t2_inset_slope/frames/p_0013.00`: 삼성 분기 매출 막대 위 3분기 열 → "부문 매출(조 원)" 2025년 3분기 → 2026년 3분기(C2, 값 그대로).
  - 상승 accent 1 = DS(33.1 → 147.1). 두 시점은 열 머리에만 둔다(머리 줄에 되풀이하지 않는다). 각주 "부문 간 내부 매출 포함" 은 출처 줄에 보인다.
- 40초 `t2_multilayer_v5/frames/p_0040.00`: 일별 missing 의 점선·"자료 없음" 라벨이 사라졌다. 핀 라벨 위쪽 2단 그대로다.
  - 출처 줄 끝 "급변일 5일 자료 없음(보도 미대조)" 은 엔진에 들어갔다. 다만 이 다층 레인은 출처 줄 자체가 아직 그려지지 않는다([source-missing] — T3 몫). T3 에서 함께 보인다.
- 덤벨 대표 컷(`t2_inset_dumbbell/frames/p_0012.00`)도 리더선 수정판으로 갈았다.

## 2. 엔진(미등록 패치 `t2_inset_slope/econ_sketch_v8.patch`)
- `island.column_detail.never_cover_focus_column: true`(감독 지시). 가리키는 열을 가리지 않는 자리가 없으면 렌더 전 오류다.
- 리더선은 인셋 위 변 높이(레인 위 끝)에서 수평이다. 가이던스 판에서 값 라벨 "16.5" 바로 위를 지나던 것을 고쳤다.
- slope 는 값 그대로다(구성비 코드 삭제). 공시 자릿수(소수 첫째)로 찍고, 좌우 라벨은 세로로 밀어 겹침 0 이다.
- 일별 missing: 점선·라벨 없음, 레인 출처 줄 끝 한 줄(`missing_mark.daily_note_outlier`·`daily_note`). 날짜 목록은 provenance series_records.missing 에 이미 있다.

## 3. 브랜치 커밋
- 6eb4aac D-0319 ①: 일별 null 종가는 missing(`data.chart_null_note` "원 응답 null"). 로더는 null 날이 레코드 missing 에 없으면 오류다. `price_outlier_pct` 중복 키를 정리했다.
- edd5864 삼성 부문 매출 레코드 넷(`SSNLF_SEG_{DX,DS,SDC,HARMAN}_REV_Q`). IR 3Q·1Q 자료 별첨 2 매출 표, pdf_line 이다. 출처에 "부문 간 내부 매출 포함" 을 적었다.
- 508387e 전체 pytest 회귀 수정(이 트랙 세션 1 커밋에서 온 것).
  - `lane_range` 가 style 없는 시험 이벤트에서 KeyError → `e.get("style")`.
  - 끝값 라벨 자리 목록이 5칸으로 늘었는데 `place_end_label` 이 3칸으로 풀었다(실제 렌더 경로에서 라벨이 겹칠 때 터진다).
  - `check_glyphs` 가 템플릿 표시 줄을 렌더 문맥(R.tb)에서만 읽어 검사 단독 문맥에서 터졌다 → 원고(plan)에서 읽는다.
  - 시험 갱신: 검사 표에 template_label·invest_notice(merge 때 빠짐), 장르 무대 오류 문구("주·보조·아일랜드").

## 4. 사진
- intc_hq_2008 을 Commons 에서 다시 받았다(429 한 번 대기 뒤 성공). 다층 스케치의 첫 문장 사진 이벤트를 되돌렸다.

## 5. 전체 pytest 남은 실패 — 자산(이 컨테이너)
- hormuz_korea(골든 25컷·카탈로그·엔딩 검정·v3 음성·인셋 머리), fed_policy_2026·fed_timeline_demo(G4·G5 엔딩 카드), geo.pkl 도로·강(v740 지도층).
- 모두 "자산 없음" RuntimeError 다. 이 트랙 렌더 코드와 무관하다. 골든 25컷 대조는 자산 복원 뒤 T3 등록 전에 돌린다.
- `test_direction_convert` 1건은 hormuz 연출의 project_id(D-0311, 쇼케이스 트랙) 차이다. 이 트랙에서 고치지 않았다.

## 6. 다음
- 남은 스케치 없음(D-0315 순서 + D-0318·D-0319 인셋 판 완료). 사용자 요소별 승인 대기.
- 승인 오면 T3 한 커밋. 인셋 문장의 카메라를 열을 한쪽 1/3 에 두는 연출 규칙, detail 층을 계열 수·단위 검사에서 빼는 정직성 수정, 분기 린트(quarter_of·파생 레코드)를 함께 넣는다.
