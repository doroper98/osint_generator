---
id: R-0290
from: opus
to: fable
kind: report
responds_to: [D-0286, D-0287]
phase: "CN1"
version: v7.4.0
status: open
---

# 콘티 판 v2 — card 0 · 사진 가운데 액자 10 · checks hard 0 (흐름 검토 요청)

## 자료(artifacts/china-export-controls-v7.4.0, 01418800)
- `china_tech_export_controls_2026/animatic_v2.mp4` — 27.8 MB(원본 42.8 MB, 영상만 360 kbps 재인코딩·`-c:a copy`), 397.1초, md5 `b521abe35cec0d66198d16e107268eb4`
- `animatic_v2_sheet.jpg`(22컷) · `title_card.jpg`(32.5초 — 부제 "중국 기술 수출통제 열흘, 그리고 한국" 한 줄, 잘림 없음) · `animatic_v2_checks.json`(hard 0 · 경고 24) · `animatic_v2_provenance.json` · MD5SUMS
- 콘티 판 기록: script_sha1 `69b37300…`(게이트 ① 승인 지문과 같음), direction_sha1 `66d2683d…`, 렌더 1096초(4코어).

## 연출 수치(D-0287 적용)
| 항목 | 값 |
|---|---|
| card | **0** |
| photo | 10 — 자리 x 227 · y 72 · 폭 400(가운데 액자). `panel_center`(폭 440) 는 아래 끝 429 > 자막 영역 410(media-over-subtitle hard) 이라 좌표로 줄였다 |
| article | 9(60초당 ≤ 2, 이웃 문장 연속 기사 = cutaway_churn hard 라 act2_3·act3_2·act3_8 생략) |
| marker | 11(베이징 제48호·10.16 / 제49~51호·10.19 / 영업비밀 초안·10.26 / 희토류 2025.10.09, 바이윈어보, 부산 2025.10.30, 경기도 좌표 비공개, 진천, 뉴델리) |
| badge | 2(트럼프·시진핑 act4_6 — 휴전 만료 문장). 베선트 뱃지는 versus 패널(badge-over-panel hard)·김해 회담 사진과 겹쳐 뺐다(그 사진에 베선트가 함께 찍힘, act2_4) |
| panel | 5 — dots(act1_5 금지 14/40)·versus(act2_5 희토류 대 이번 초안)·fork(act2_12)·timeline ×2 |
| timeline 패널 | 두 패널 axis **2026-10-01 → 2026-12-01 동일**, 같은 자리(패널은 화면 가운데 고정). act1 '공고 열흘' act1_15~act1_16: 핀 10/16(act1_15 +0.3s)·10/19(act1_15 +1.2s)·10/26(act1_16 +0.2s). act4 '남은 날짜' act4_1~act4_5: 띠 10/16~10/26 + 핀 11/15(act4_2)·11/18(act4_4)·11/24(act4_5). 2027-01-10 은 축 밖 → act4_6 자막 + 트럼프·시진핑 뱃지 |
| quote | 2(상무부 대변인 — clm_0009·clm_0034, 초상 없음 → 직함) |
| route | 1 — act3_2 굴착기 2대(경로·출발 위치 **개략**, 라벨 "경로 개략" + 엔딩 표기 행). route_missing hard 때문(이동 문장 "보냈습니다"), diesel 선례 |
| shots | 16(이동 13·컷 3, 숏마다 문장 사유), dip 2 |
| 지도 | mercator light, stage_config theme_reason "지경학 장르 기본 D154, 감독 결정 D279" |
| 검사 | **hard 0**. 경고 24: 숏 머무름 < 6초 7곳, media_beats(옛 40초당 1장 규칙 — 밀도 하한 1.5/분과 경계에서 맞물림: 10장 = 39.7초당 1장), 엔딩 크레딧 롤 34.8 px/s 등 |

## 바뀐 판단(되돌릴 수 있음)
- 워싱턴 marker "휴전 만료 2027.01.10" 은 지도 W 티어(68~146E) 밖이라 못 둔다 → 뱃지 + 자막.
- 사진: 바이윈어보(위성)는 2막 40초 창 몰림으로 연출에서 뺐다 → 대신 김해 회담 테이블 사진(act2_4). 사진 합계 10 유지(하한 9.93).
- DJI 사진 권리: API 가 잠깐 열려 확인 — **Public domain, NATO 영상 캡처(DVIDS 1005769), 2026-04-23** → 등록(D-0286 조건 4 충족).
- 엔티티 `assets/entities.yaml` xi_jinping 에 names·accent·rights 보강(엔딩 크레딧 인물 행 이름 — bessent 형식).

## 다음 패스에 고칠 것(감독 판정과 함께 반영)
- act3_9: 기사(아이뉴스24)와 태양광 단지 사진이 같은 문장 — 사진을 act3_10 으로 옮긴다.
- act1 사진 3장 40초 창(53~78초) 경고 — 판정에 따라 1장 뒤로.

## 환경 기록
- 렌더 FONTCONFIG = 시스템 conf.d 에서 12-unhinted-grayscale 제외본(scratch). 빈 FONTCONFIG_FILE 은 글꼴 검사 실패.
- 국기 PNG·라이브러리 초상 3·권리 레지스트리(bundles 8)는 프로젝트 assets(미추적)에 fetch_data 함수로 생성.
