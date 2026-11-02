---
id: R-0325
from: opus
to: fable
kind: phase_report
responds_to: [D-0616, D-0617, D-0618]
phase: "E9"
version: v7.4.0
commit: HEAD
status: done
---

# 칸나이 콘티 판 v1 — artifacts `78158fa8` `war_history/cannae_216bc/animatic_v1/`

## 1. 산출

- animatic.mp4: 480p, 371.6초, 19.5MB. 렌더 원본은 34.3MB(md5 52481fb9)이고 crf 26 으로 줄인 전달용입니다.
- contact_sheet.jpg(20컷), animatic_checks.json, animatic_provenance.json, terrain3d_manifest.json, rights_registry.json, 입력 셋(direction·forces·credits).
- 음악: 콘티 판 = Zabriskie(bgm_default 첫째). 같은 구간 30초 견본 둘 = sample_coriolan_30s.m4a · sample_zabriskie_30s.m4a(encirclement_5 부터 201.6~231.6초, 같은 mix()·bed_gain 0.43). 판정 ③ 에서 사용자가 고릅니다.
- 카드·사진·인용은 콘티 판 규칙대로 자리표시입니다.

## 2. 검사 — hard 0, warning 15(passed)

| warning | 수 | 요지 |
|---|---|---|
| media_beats | 7 | 장면 안 사진 2장(prelude·deployment·ending), 이웃 장면 같은 형태(photo) |
| geo_unsourced | 4 | 칸나이·타렌툼·갈리아 키살피나·베누시아 좌표가 현대 지명 사전에 없음(고대 지명) |
| shots | 4 | 숏 머무름 < 6초(구간 안 궤도 숏 152.8→162.5 5.7초 등) |

- media_density: 레퍼런스 10 / 6.2분 = 분당 1.62 ≥ 1.5. 종류별 photo 8 · quote_source 2(몫 0.20 ≤ 0.34). D-0618 규칙 그대로입니다.
- [war-units-approx] 0. 구간 동안 출처 줄 "부대 위치·크기: 폴리비오스 『역사』 III.113~116(Paton 영역 1922) — 개략(축척 아님)".
- static_camera·sea_only_frame·route_frame 은 구간 프레임에 해당 없음 사유가 notes 에 남았습니다([terrain3d-na]).

## 3. terrain3d 구간 카메라 숏 표

구간 seg00 = 113.47~256.26초(142.8초, 3427프레임). 들어감·나옴 = 90° 내려다보기·북쪽 위·그 시각 mercator 화면 폭입니다.

| 숏 | 문장 | 모드 | 카메라(lon·lat·w°) | 3D |
|---|---|---|---|---|
| 6 | deployment_1 | cut | 16.11 · 41.334 · 0.09 | 90° 진입, 부대가 원고 순서대로 나타남 |
| 7 | deployment_10 | drift | 같음 | 궤도 152.8~162.5초(초승달), 기울기 2.5초 |
| 8 | deployment_12 | move | 같음 | 되돌리기(90°·북쪽 위) |
| 9 | encirclement_0 | move | 16.097 · 41.337 · 0.06 | 강가 기병 충돌로 pan·push |
| 10 | encirclement_5 | move | 16.11 · 41.334 · 0.08 | 중앙 보병으로 |
| 11 | encirclement_6 | drift | 같음 | 궤도 206.9~220.9초(양익 포위) |
| 12 | encirclement_9 | move | 16.12 · 41.325 · 0.11 | 되돌리기, 나올 때 칸나이 마을 자리까지 |

- 궤도는 drift 숏 두 곳뿐입니다. 그 밖은 90° 시점 숏 단위 pan·push 입니다. 문장마다 회전하지 않습니다.
- 3D 카메라는 프레임마다 mercator 카메라(숏 키)를 따릅니다(34698dba).

## 4. 작품·기록 표(캡션 = 레지스트리 문구, 당대/후대 라벨은 코드)

| 문장 | 레코드 | 캡션 | 출처 줄 | 라이선스 |
|---|---|---|---|---|
| prelude_6 | cannae_bust | 대리석 흉상 | 대리석 흉상 · 나폴리 국립고고학박물관 · Fratelli Alinari | Public domain |
| prelude_7 | cannae_coin | 전투 코끼리를 탄 기수를 새긴 카르타고 은화 | 셰켈 은화 · 히스파니아 주조 · 베를린 알테스 무제움 · Sailko | CC BY 3.0 |
| deployment_8 | cannae_tanit | 타니트 기호를 새긴 석회암 비석 | 루브르 박물관(AO 5244) · Tangopaso | Public domain(PD-self) |
| deployment_12 | cannae_montefortino | 몬테포르티노형 청동 투구 — 같은 시대 유형의 유물 | 에트루리아 · 기원전 4세기 말~3세기 초 · 메트로폴리탄 미술관 — 칸나이 출토품이 아니다 | CC0 |
| encirclement_11 | cannae_trumbull | 칸나이 전투에서 숨지는 집정관 파울루스 | 존 트럼불 · 유화 · 예일대학교 미술관 | Public domain |
| aftermath_5 | cannae_slodtz | 칸나이에서 죽은 로마 기사들의 반지를 세는 한니발 | 세바스티앵 슬로츠 · 대리석상 · 1704 · 루브르 박물관(MR 2093) · Jastrow | Public domain(PD-self) |
| ending_3~4 | cannae_smith1856 | 그리스 로마 지리 사전의 '칸나이' 항목 | 1856년 런던 사전 499쪽 'CANNAE' 첫머리 · W. Smith | Public domain(archive.org 스캔, photo_pd_basis) |
| ending_5 | cannae_closs | 칸나이 전투가 벌어진 들판 | 화보 삽화 · L'illustrazione popolare(1885) · G. A. Closs | Public domain |

사료 인용 2(quote.source):
- aftermath_6: 폴리비오스 『역사』 III.117.1 · W. R. Paton 영역(1922, 퍼블릭 도메인)
- aftermath_7: 리비우스 『로마사』 XXII.51.4 · B. O. Foster 영역(1929, 퍼블릭 도메인 미국 2025년부터), 작은 줄 라틴 원문 "vincere scis, Hannibal, victoria uti nescis"

## 5. 이번에 고친 엔진·규칙(콘티 판까지)

| 커밋 | 내용 |
|---|---|
| efa0a064 | 구간 경계 암전 요구 제외(이어 찍기), 구간 = 시각 요소, 입력 지문에 지형 티어 |
| 7662885d | 90° 북쪽 위 방위 기준(뒤집힌 화면) |
| 28ae967c | terrain3d 모듈 load_rules 프로세스당 한 번(30분+ 멈춤) |
| dbd2375b | mercator basemap_era ancient |
| d6f2445f | quote.source 사료 인용 카드 |
| e09ea1f6 | media_density 장르·시대별 셈(D-0618) |
| db38133b | frame_missing — 고대 지도에서 현대 나라 이름 제외("그리스·로마 지리 사전" 오판) |

## 6. 알릴 것

- 슬로츠 캡션에 "리비우스 XXIII.12 일화를 조각" 표기는 넣지 않았습니다. 이번 원천(Commons 파일 설명·영역본 XXII)에 그 locator 가 없습니다.
- 몬테포르티노 투구는 원고 "노획한 로마 무기" 문장 자리에 있지만 라벨은 Commons 대로 에트루리아입니다(D-0617 조건 ②).
- 날짜 뱃지 150초 "2026. 11. 01"은 원고 deployment_9(재현 고지 문장)의 date 입니다(D-0612 ①).
- 쓰지 않은 후보: 팔카타(연대 기원전·후 표기 없음), 마시니사 주화·폴리비오스 비석(사진 CC BY-SA).
- 미리 렌더 3D 는 렌더 쪽 지문 대조를 거쳤습니다. dry run(반복용 스크립트, 저장소 밖)만 지문 대조를 건너뛰었고 최종 렌더는 그대로 대조했습니다.

## 7. 다음

1. 감독이 사용자에게 콘티 판·코리올란 견본 전달(판정 ③). "고대 편은 사료 인용 카드도 레퍼런스로 셌다" 한 줄(D-0618 §3).
2. 판정 뒤 지적 반영 → 프리뷰·게이트 ②.
3. terrain3d 남은 일: 합성 골든(엔진 컷 md5 fixture)·anti_inertia(레지스트리·provenance stage:terrain3d) — R-0322 순서의 마지막 둘.
