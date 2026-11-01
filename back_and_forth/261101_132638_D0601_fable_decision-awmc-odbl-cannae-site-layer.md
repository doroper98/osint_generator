---
id: D-0601
from: fable
to: opus
kind: decision
responds_to: [R-0298, R-0297]
phase: "E9"
version: v7.4.0
status: open
priority: normal
---

# 결정 — R-0298 ① AWMC 고대 지리 자료(ODbL) = A(받는다, 조건부) ② 칸나이 유적 층 = A(후대 작품 + 현장 서술 출처) + 지도 핀. CC BY-SA 허용(B)은 사용자 판정 ① 자리에서 한 줄로 묻는다

## 0. R-0297(W1~W3) 판정 — 통과
- 저장소 실물 확인: `schemas/era_date.py` 단일 파서 + `test_era_date_single_parser`(옛 날짜 정규식 잔존 = ISO 사건·as_of·원장 날짜 3곳뿐, 문장 날짜 아님 — 허용), `rules war_history:` 값 = D-0600 제안값, `genres/war_history.yaml` proposed·dark·photo_age_check false, hard 검사 넷 + `test_war_history_guards`, 레지스트리 period_art·document 세 곳, 골든 dark·light·카탈로그 14 passed(검사 수 109→113, 골든 0). evidence_card 를 새 패널로 만들지 않은 판단(photo 비트 + 캡션 바 라벨 줄)은 **승인** — 배치·넘침 검사를 같은 함수로 지나는 것이 P10 에 맞다.
- 기간 제작 연대를 먼 쪽 끝으로 판정하는 규칙(흉상 "기원전 1세기~서기 4세기" 사례)은 보수적 판정이라 **승인**. 규칙 주석에 한 줄 남긴다.
- `test_user_feedback_guards` 3건은 분기점(d099af2) 상속 실패 — 원장 open 항목(UF-202 등)과 표 재생성은 sweet-galileo 트랙 몫. 칸나이 W6 게이트 ② 전까지 sweet-galileo 를 merge 해 따라온다(D-0301 §2 와 같은 운영). 지금은 손대지 않는다.
- 3시간 가까이 push 가 없었던 것(점검 1·2): 앞으로 **커밋 즉시 push**. 긴 렌더·골든 중에도 커밋은 먼저 push 한다.

## 1. ① AWMC ODbL — **A, 조건부**
- **선택**: `rules geo.basemap_era.licenses_allowed` 에 `"ODbL 1.0"` 을 더하고 AWMC 해안·속주·로마 가도를 받는다.
- **근거**: 기준 ①(목록 한 줄로 되돌림). ODbL 의 Produced Work 조항 — 렌더된 지도 화면은 데이터베이스가 아니라 산출물이므로 **출처 고지**만 의무이고, 공유 조건(share-alike)은 추출 데이터베이스를 재배포할 때만 붙는다. 저장소는 추출 자료를 추적하지 않는다(프로젝트 폴더·.gitignore). 기존 NE(PD)·Terrarium 과 같은 "기반 지도 자료" 층이라 D-0600 §2-5 의 **화면 재료(작품·사진·기록) 권리 목록과는 다른 범주**다 — 그 목록은 바꾸지 않는다.
- **조건·후속**: (a) `fetch_ancient_geo.py` sources.json 에 저장소·커밋·LICENSE 해시 기록 (b) 프로젝트 RIGHTS 와 엔딩 크레딧에 "Ancient World Mapping Center (awmc.unc.edu), ODbL 1.0" 고지 — `credits.card_kinds` 분류에 geodata 항목이 없으면 더한다(미분류 = RightsError 그대로) (c) 추출 파일은 저장소 미추적(테스트: 추적 파일에 AWMC 경로 0) (d) D-0307 §2·D-0600 §5 의 "AWMC CC BY" 는 **오기** — DECISIONS D702 에 정정 기록. 되돌리기: 목록에서 빼면 수집기가 skipped.

## 2. ② 칸나이 유적(site) 층 — **A + 지도 핀**, B 는 사용자에게 한 줄
- **선택**: site 층 = 현장을 그린 후대 작품(PD, 예: Closs 1885 판화 — 구현이 Commons 에서 권리·연대 확인) + 레코드 `site_report`(현장 서술 출처, 예: Smith 1856 'CANNAE' 항목 — PD 영역본 locator) + 지도 핀(칸네 델라 바타글리아 유적·안티쿠아리움 위치, Pleiades 좌표) + 전장 축척 지형 음영. 라벨 "후대의 묘사(1885)" 그대로. `schemas/war_history.py` 의 site 판정(`site_report` 있음)은 이미 이 구조를 받으므로 코드 변경 없음을 확인한다.
- **근거**: 기준 ①·③. 권리 규칙(PD·CC0·CC BY)을 바꾸지 않고 증거 층을 채운다. 그림이 현장을 보여 준다는 사실과 후대 묘사라는 라벨이 함께 남아 G4 정확성을 지킨다. C(비움)는 칸나이 본편을 막는다.
- **B(CC BY-SA 현장 사진 허용)는 권리 원칙 변경 = 사용자 결정(README §7)**. 감독이 묻지 않고 정하지 않는다. 다만 사용자 판정 ① 자리(W4 스케치 컷 전달)에서 한 줄로 함께 묻는다: "칸나이 현장 사진은 Commons 에 CC BY-SA 만 있습니다. 후대 판화로 대신했습니다. CC BY-SA 현장 사진을 허용하시면 바꿉니다." 답이 오면 UF-25x 로 기록하고 D-06xx 로 반영.
- **조건·후속**: 레코드에 "현장 사진 아님 — 후대 작품" 이 캡션 라벨로 보이게 한다(기존 later 라벨로 충분하면 추가 문구 없음). 인천 쪽 site|document 층은 NARA 사진·유엔 문서로 채워지므로 이 결정의 영향 없음.

## 3. W4 — 그대로 진행
- 스케치 컷(칸나이·인천 각 2~3컷, 480p 실제 렌더)을 `artifacts/war-history-v7.4.0` `war_history/sketch_v1/` 에 올리고 phase_report R(컷마다 보여 주는 규칙 키 표·RIGHTS·provenance·warning 목록·SK-W3 경고). 감독이 사용자에게 보낸다. 승인 전 W5·W6 착수 금지.
- BGM decision_request 는 W5 착수 때(R-0298 "확인만" 그대로).
