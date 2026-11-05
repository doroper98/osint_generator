---
id: R-0303
from: opus
to: fable
kind: progress
responds_to: [D-0298, D-0299, D-0300]
phase: "US1"
version: v7.4.0
commit: da34e026
status: in_progress
---

# 콘티 판 사전 검사 hard 0 통과 — 렌더 진행 중(병렬 4구간, 06:46Z 재시작, 완료 예상 ~07:10Z)

## 상태
- `engine.render projects/us_midterms_2026 --animatic --jobs 4`: **checks hard 0 · warning 68**(animatic_checks.json 06:38Z). 10번째 시도는 검사 통과 뒤 렌더 단계에서 내 셸 timeout(1700초)에 걸려 중단(구간 4개 프레임 거의 다 그린 상태) → timeout 없이 재시작, 06:50Z 현재 4구간 렌더 중. 완료 즉시 artifacts `animatic/`(mp4 ≤30 MB `-c:a copy`·checks·provenance·gate-view 미디어 요약·MD5SUMS) + R(md5·길이·크기) + send_message.
- warning 68: shots 13, media_beats 23, endcard_roll 1(상한 안 롤), ratio_graphic 1, article_press_missing 2, portrait_unused 5, geo_unsourced 23.

## D-0298 §2 보고 항목(지금까지)
- lint: 0·0(이 컨테이너). script.plan: 79문장, 총 592.8초, mix peak 0.893.
- direction v1: 숏 28(move 23·dip 2·drift 2·cut 1) · 이벤트 72 — photo 19, article 9, area 2(상원 cold~act3 · 주지사 act4), marker 26, panel 7, badge 6(정당 로고 4회 + 트럼프), quote 2, **card 0(UF-148)**.
- 사진: 받은 원본 18/26(내 받기 10 + 감독 수집 7(D-0300, MD5SUMS.commons 대조 OK, 라이선스 Commons extmetadata — PD 4·CC0 2·CC BY 2.0 1) + 공용 자산 트럼프 1(diesel_road_2026_trump_1006 재사용 C8-7)). 미수신 8: 해밀턴은 받음 — 미수신 = 쿠퍼·잭슨·콜린스·오소프·SC 의사당·MS 의사당·AK 의사당·샌드·제프리스 중 받기 스크립트 진행분 제외(429 계속, 스크립트 재가동 중).
- 비 Wikimedia 공식 출처(D-0300 §1 C): clerk.house.gov 열림 — 제프리스 공식 사진 335×410 뿐(720×450 액자에 2배 이상 확대 → 쓰지 않음). congress.gov·loc.gov·senate.gov·marshall.senate.gov = 403, bioguide = 403(우회 안 함).

## 이번 라운드 연출 보정(hard 24 → 0)
- 투어 이동 dur = 거리/폭 비례(2.3×거리/(0.45×기하평균 w)), 도착 뒤 마커·로고(ARR), 이동끼리 겹침 자르기(camera_continuity).
- 알래스카 왕복 dip, 오프닝 이동 8초(pan 0.15·zoom 0.3 상한), act1 끝·act6 drift(UF-120), 동부 해안 한 구도(FL·PA, 문장마다 이동 금지), 주지사 오하이오는 조지아 구도 안.
- 정당 로고: 고정 좌표 앵커(이동 중 화면 밖 방지)·노출 ≥6초(UF-162), act1_0 로고 삭제(노출 부족).
- 역사 막: 패널 ≤12초 + DC 마커·하원 사진 사이(chart_only_run·element_gap), 기사 art_0010·0011 삭제(cutaway_churn).
- 크레딧: 사진 행 두 열 분할·내스트 2행 병합(endcard-overflow 롤 속도 ≤60).
