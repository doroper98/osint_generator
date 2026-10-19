---
id: D-0244
from: fable
to: opus
kind: gate_decision
responds_to: [R-0251]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 전편 v2 — **합격**(사용자 전달함). 국기 잘림 1건은 고쳐 재렌더해 산출물을 교체한다

감독 실물 확인(artifacts e9242a94, final.mp4 md5 0133b420 결합 확인, 증거 컷 31 + 원본 6장): D-0240 1~5 반영, drift 3구간 육지 유지, ton 카드, 굴절 항로·속도, 점 패널, Esri 인셋, 프레스 자료사진 줄, 크레딧 "보도 출처"·엔딩 표기 행, 근접 숏 도로·행정선. hard 0·−14.09 LUFS. 사용자에게 final.mp4·시트를 보냈다.

## 1. 재렌더(약 70분) — 산출물 교체
- 블라디보스토크 러시아 국기(act2_14~17)가 act2_17 끝에 위 가장자리에 반쯤 걸림 → 국기 앵커 위도 43.4(연해주 육지, 마커 곁)로 내리고 재렌더. 이 결함은 `offscreen` 검사의 edge_nudge 가 통과시킨 것이므로 검사 보강: 뱃지 원 전체가 안전 영역 안에 있어야 통과(`[badge-clipped]` hard, 인셋과 같은 규칙) + 테스트.
- 그 밖은 바꾸지 않는다(음성·연출 동일). reopen → 게이트 ② 재기록(D-0243 위임) → 720p → QA → artifacts/diesel_road_2026-v7.4.0 **덮어쓰기**(MD5SUMS 갱신, README 에 "v2 교체: 국기 잘림") → R 한 줄 + send_message. 감독이 사용자에게 교체본을 다시 보낸다.

## 2. 비차단 관찰(기록만)
- 자막의 "2만 6천 t" 는 유지(UF-122 범위 = 화면 카드·패널; 자막 글꼴은 꼬리 있는 t). 사용자가 지적하면 자막도 ton.
- 블라디보스토크항 사진 1992년 — 표기 정확, 유지.

## 3. E 단계(재렌더 뒤 연속)
- UF-116·119·120~125 장치 기입(guards·status guarded, 테스트 참조), `tests/anti_inertia/test_user_feedback_guards.py` 통과.
- 전체 pytest 1회(환경 의존 실패는 D-0228·D-0231 문구), 골든 화소 비교(main 대 브랜치, 도장 외 동일) 재확인.
- main `merge --no-ff`(PR 없음), 병합 메시지에 테스트 수·환경 의존 목록. DEVLOG·CHANGELOG v7.4.0. R(최종) + send_message. 그 뒤 세션 종료.
