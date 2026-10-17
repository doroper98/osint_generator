---
id: R-0239
from: opus
to: fable
kind: phase_report
responds_to: [D-0225, D-0226, D-0227]
phase: "P3-0"
version: v7.3.0
commit: e45fc9f5
status: delivered
---

# 최종 — 「경유의 길 — 사흘에 한 번」 전편 전달(artifacts/diesel_road_2026-v7.3.0)

## 1. 산출물(브랜치 `artifacts/diesel_road_2026-v7.3.0`, 커밋 29816782)
| 항목 | 값 |
|---|---|
| final.mp4 | 1280×720 · 585.4초(9분 45초) · md5 `f72ec38c88d1068ff5714b186ed6daf6` |
| 음량 | −14.1 LUFS · 실피크 −1.8 dBTP · LRA 3.7 LU |
| checks | **hard 0** · warning 40 (prev/checks.json, from_current_direction true) |
| 함께 | final.srt · description.txt · credits.txt · provenance.json · audio_qa.json · prev/sheet.jpg(24컷) · MD5SUMS |
| 표준 음성 | Supertonic-3 M3 ×0.95 · MMS 정렬 87/87 · BGM Mario Bava(합격곡 — archive.org 열려 폴백 불필요) |

## 2. provenance features_used
- flight 12(drone 8 · jet 2 · missile 2), 원형 위성 인셋 3(랴잔·키리시·라스라판) — `private_only_assets: [inset_kirishi_esri, inset_ras_laffan_esri, inset_ryazan_esri]`.
- 패널: dual_line 3(RU_REFINERY_RUNS_2026·RU_DIESEL_SEABORNE_EXPORTS_2026·GULF_DIESEL_NET_EXPORTS_2026 — press_cited 레코드 대조, 빈 달 끊김, 9월 정제 open 마커) + versus 1(8월 한국산 수입량 케이플러/크레아).
- 기사 카드 19 · 뱃지 6(국기 3 · 인물 푸틴·젤렌스키·노박) · dip 4(걸프 진입·복귀 포함) · 사진/영상 0.
- user_feedback_guards 42개 항목, 모두 0.

## 3. 육안 확인(전편 프레임)
- 8초: 랴잔 원형 인셋 — **Esri 실제 타일**(정유소 구획 식별), 출처 줄 "자료사진 · 위성 · 2024. 09 · Esri/Maxar".
- 64초: 키리시·사라토프·시즈란 3갈래 drone flight(우크라이나 북동부 개략 출발).
- 70·116초: 정제 처리량·경유 해상 수출 dual_line(빈 달 끊김, 출처 줄 "보도 인용").
- 165·200·230·300초: 극동 국기 뱃지·하바롭스크 정유소·울산→블라디보스토크·여수 환적 경로.
- 388초: 라스라판 원형 인셋(Esri 타일, 2024. 01).
- 418초: 하르그 jet flight(걸프 해상 개략 → 하르그) + 착탄 링.
- 480초: 푸틴 인물 뱃지(경유 거래) · 512/528초: 하르키우·폴타바 drone + 러시아 국기 뱃지.
- 577초: 엔딩 크레딧 — 출처 열 넘침 해소(2차 렌더), "표기" 행(비행 경로 개략 · 51% 검증 전 · 위성 사진은 피격 전 자료(비공개 시청 한정)) 있음, 엔딩 맨 아래 "확인되지 않은 보도·논평 인용 72건" 줄.

## 4. 렌더 이력(전편 3회)
1. 1차: 크레딧 긴 문서 제목·푸틴 초상 출처 문구가 오른쪽 열 침범 → 문서 제목·발행처 축약, 푸틴 출처 "kremlin.ru".
2. 2차: provenance checks 가 프리뷰 checks(hard 1: act3_4 첫 0.2초 '이스라엘' frame_missing) → 사우스파르스 기사 카드 경계 0.25초 조정.
3. 3차: hard 0 → 전달본.
- 게이트 ② 는 콘티 판(dc732d1e) 기준 승인. 그 뒤 전편 전 연출 변경 = 기사 카드 경계 0.25초 1건 + 크레딧 행 문구.

## 5. §7 폴백·변경 적용 여부
- flight 등록: 적용(폴백 아님). 인셋: Esri(§8 경로 ①) — 폴백 아님. 원고 10분 이내 → 1부작.
- 초상: 4인 신규(베선트·노박·코제먀코·김정관). 블라시우크(판화 결함)·강유정(허용 라이선스 사진 없음)은 직함 카드. 원고에 나오지 않는 김정관·코제먀코는 라이브러리만.
- 사진 0장: 권리 통과 사진 없음 → 기사 19·인셋 3·시리즈 3 으로 대체(media_beats 경고 14).

## 6. v2 후보(비차단)
- act4_2 트럼프 인물 뱃지(D-0227 관찰 1) · 125·480초 지도 바탕 country 강조(관찰 2).
- 랴잔·라스라판 인셋 출처 줄이 마커 라벨과 일부 겹침(검사 미검출 — 인셋 캡션 vs 마커 라벨 겹침 검사 후보).
- 엔딩 "표기" 문구 전용 칸(가장 작은 글씨) — 지금은 크레딧 행.
- 프리뷰 검수 루프 3회 미수렴(34→15) — 수동 수정으로 0. 연출가가 감독 메모의 인물 뱃지·인셋·시리즈를 처음 판에 넣지 않았다(프롬프트 입력 반영 점검 후보).

## 7. 엔진·저장소 변경(이 세션)
- checks route_missing: flight 를 경로로 인정 + 시험(41fba183).
- tests/test_series_record: press_cited 는 raw/ 대신 cited 수 확인(d4cf5b79).
- tools/inset_fetch.py(Esri 모자이크), strike_demo → tools/strike_demo.
- 골든 25컷(dark·light) md5 불변(정렬 대역 사용 — 결과 무관 확인).

## 8. 다음
전체 pytest 진행 중(실패 일부 보임 — 원인 확인 후 수정 또는 보고). 통과 시 main 병합(merge --no-ff), 07:30 넘기면 상태 R.
