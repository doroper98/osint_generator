---
id: R-0298
from: opus
to: fable
kind: gate_request
responds_to: [D-0292]
phase: "US1"
version: v7.4.0
commit: HEAD
status: open
---

# 게이트 ① 자료 — 원고 v1.1(72문장, script.yaml sha1 e9cc97e4…) · 사용자 전달용

## D-0292 §2.1 여섯 조건 반영
| # | 문장 | 반영 |
|---|---|---|
| 1 | act1_6 | "엔비씨 집계로는 민주당이 16년 만에 주지사 과반도 차지했습니다." |
| 2 | act5_6 | "엔비씨 집계로는 이번에 하원에서 지금까지 확정된 자리만으로 공화당이 34석을 잃어, 90년 평균보다 많습니다." |
| 3 | act3_2 | "…표 차가 집계 매체와 시각에 따라 수십 표에서 2천 표 남짓입니다." — 출처에 The Hill(DDHQ 2,169) 추가(src_art_0045) |
| 4 | v1 act1_13·act4_11 | 삭제. 막 정리(outro) 역할은 앞 문장(act1_12 트럼프 발언·act4_10 미주리)에 옮겼다(린트 act-frame 0) |
| 5 | act1_10 | "씨비에스 초기 출구조사에서 …" |
| 6 | act2_11 | 표시·발음 모두 "제이디 밴스" |
- 제목 『뒤집힌 일곱 자리』 · 부제 "2026 미국 중간선거 — 주별 결과·격전지·역사 맥락"(D-0292 확정).
- 린트 오류 0·경고 0. 문장 72, 내레이션 3,615자 → 약 8분 30초(중국 영상 실측 비율; gate-view 의 677.8초는 320자/분 추정).

## 파일(브랜치 claude/vigilant-fermat-w8c2ti)
- 원고 전문·출처 표·린트·미디어 계획 표: `projects/us_midterms_2026/gate1_view.txt`(gate-view 출력)
- 막마다 요소: `projects/us_midterms_2026/gate1_elements.md`
- 미디어 계획: `projects/us_midterms_2026/media_notes.yaml`(선택 24행 — 인물 사진 16·의사당/의회 자료사진 7·1937 개표 1, 목표 16 이상 충족), 검색 기록 `media_search.json`
- 데이터: `projects/us_midterms_2026/data/state_results.yaml`(상원 35·주지사 36·하원 뒤집힘 19)

## state_results 요약(뒤집힘·개표 중·주요 유지)
| 주 | 레이스 | 승자(또는 선두) | 당 | 득표율 | 상태 | 콜 |
|---|---|---|---|---|---|---|
| 알래스카 | 상원 | (선두) Mary Peltola | none | 48.2 대 47.9 | counting | — |
| 알래스카 | 주지사 | (선두) Jonathan Kreiss-Tomkins | none | 49.1 대 29.2 | counting | — |
| 플로리다 | 상원 | Ashley Moody | rep | 50.9 대 48.0 | called | NBC 결정데스크 추정(projection) |
| 플로리다 | 주지사 | Byron Donalds | rep | 50.0 대 48.7 | called | AP(NPR 인용, 11/3) |
| 조지아 | 상원 | Jon Ossoff | dem | 59.0 대 41.0 | called | NBC 결정데스크 추정(projection) |
| 조지아 | 주지사 | Keisha Lance Bottoms | dem | 54.3 대 45.7 | called · 뒤집힘 | AP(NPR·AJC 인용) |
| 아이오와 | 상원 | Josh Turek | dem | 50.5 대 46.4 | called · 뒤집힘 | AP(NPR·CBS 인용) |
| 아이오와 | 주지사 | Rob Sand | dem | 55.5 대 44.5 | called · 뒤집힘 | NBC 결정데스크 추정(projection) |
| 캔자스 | 상원 | Adam Hamilton | dem | 51.0 대 46.0 | called · 뒤집힘 | AP(NPR·KCUR 인용) |
| 캔자스 | 주지사 | (선두) Cindy Holscher | none | 50.3 대 49.7 | counting | — |
| 메인 | 상원 | Troy Jackson | dem | 53.4 대 46.5 | called · 뒤집힘 | AP(NPR·Maine Public 인용, 11/4 01:02 ET) |
| 미시간 | 상원 | Abdul El-Sayed | dem | 52.5 대 45.5 | called | NBC 결정데스크 추정(projection) |
| 미시간 | 주지사 | Jocelyn Benson | dem | 54.5 대 43.8 | called | NBC 결정데스크 추정(projection) |
| 미시시피 | 상원 | (선두) Scott Colom | none | 49.0 대 48.9 | counting | — |
| 노스캐롤라이나 | 상원 | Roy Cooper | dem | 58.7 대 39.1 | called · 뒤집힘 | NBC 결정데스크 추정(projection) |
| 네바다 | 주지사 | Aaron Ford | dem | 51.5 대 44.3 | called · 뒤집힘 | AP(NPR 인용) |
| 오하이오 | 상원 | Sherrod Brown | dem | 50.0 대 45.2 | called · 뒤집힘 | NBC 결정데스크 추정(projection) |
| 오하이오 | 주지사 | Amy Acton | dem | 52.3 대 44.4 | called · 뒤집힘 | NBC 결정데스크 추정(projection) |
| 사우스캐롤라이나 | 상원 | Annie Andrews | dem | 51.1 대 46.7 | called · 뒤집힘 | AP(NPR 인용) |
| 텍사스 | 상원 | James Talarico | dem | 55.1 대 43.0 | called · 뒤집힘 | AP(Texas Tribune·Houston Public Media 인용, 11/3 22:04 CT) |
| 텍사스 | 주지사 | Gina Hinojosa | dem | 52.8 대 45.7 | called · 뒤집힘 | AP(Texas Tribune 인용, 11/3 22:17 CT) |

## 미디어 메모
- 인물 사진 우선(D-0292 §2.2): 해밀턴 유세(CC0, 2026-10-30)·앤드루스(CC0)·브라운(PD 공식)·쿠퍼(CC BY)·잭슨(CC0)·콜린스(PD 공식)·오소프(CC BY)·마셜(PD 공식)·펠톨라(PD 공식)·이노호사(CC0)·보텀스(CC0)·액턴(PD)·샌드(CC0)·도널즈(PD 공식)·제프리스(PD 공식). 탈라리코는 CC BY 4.0 유세 사진 1건(피사체 등록 때 대조). 투렉은 허용 라이선스 사진 없음 → 아이오와 의사당.
- 미시시피·알래스카(개표 중)는 한쪽 후보 사진을 고르지 않고 주 의사당.
- 뱃지: 발언 문장만(슈머 PD 공식·트럼프 라이브러리). 원본 받기·피사체·시기 대조·cutout 은 승인 뒤.

## 대기 중 계속하는 일
- R-0297 결정(① 골든 badge_hold 면제 ② called 기준) 대기 — 막히는 것 없음.
- 연출 direction v1 뼈대(cold area 동→서 경도 순 delay, act1 패널, act2 주 투어 카메라)·초상 권리 대조·기사 카드 등록 준비.
