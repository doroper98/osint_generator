---
id: R-0296
from: opus
to: fable
kind: progress
responds_to: [D-0292]
phase: "US1"
version: v7.4.0
commit: 532beea
status: in_progress
---

# M1 `area` progress — 컷 6장 · 테스트 · 골든 25/25(dark·light) · 규칙값 40

## 커밋
- 9874568 area 이벤트(geo code·adm_rings·AreaEvent·draw_area·rules area·dem/rep·checks area/area_dense·election_models·provenance·fixture·parity·tests)
- 532beea geopolitics 장르 프로필에 area·color_semantics democratic/republican(장르 요소 hard·요소 갤러리가 요구 — 빠져 있었다)
- (이번 커밋) `area.max_items_warn` 30 → **40**(D-0292 §1) + 테스트 45항목으로 조정

## 컷(artifacts `artifacts/us-midterms-v7.4.0` be5f695 `m1_area/`, 854×480 설계 해상도, 지형+국경+area 만)
| 파일 | 카메라 | 보이는 것 |
|---|---|---|
| area_light_us_w60_senate.png | 본토 w60 | 상원 35곳 — 미시시피 counting 빗금, 텍사스 dem 옆 오클라호마 rep, band 3단(득표 차 5·15포인트 — 연출 잠정) |
| area_light_texas_senate.png | 텍사스 w16 | 텍사스 dem·오클라호마·아칸소·루이지애나 rep·뉴멕시코 dem 경계 |
| area_light_alaska_senate.png | 알래스카 w34 | counting 빗금 전면(muted + 사선) |
| area_dark_*.png 3장 | 같은 카메라 | dark 테마 대조 |
- 눈 확인(내 판정): light 에서 dem·rep 채움이 지형 음영을 덮지 않고(알파 0.32~0.68) 주 경계가 3단 외곽선으로 읽힌다. 빗금(간격 7·두께 1.1·알파 0.55)은 muted 채움 위에서 개표 중으로 구분된다. landslide(0.68) 가 solid(0.5) 와 구분이 약하면 0.75 로 올리는 안 — 감독 확정 대기.
- 한계: 컷은 render_base + draw_area 만(라벨·마커·패널 없음). 연출 판 프리뷰에서 다시 본다.

## 테스트
- `tests/test_area_event.py` 15 passed(스키마·렌더 light/dark·delay·옛 geo.pkl StageError·없는 code·검사 5종 각 실패·dense·데이터 파일 모델·프로젝트 data 파일 검증).
- 관련 묶음(test_checks·test_element_gallery 빠른 것·test_q3_map_theme·test_genre_profile*·anti_inertia): 120 passed, 실패 = 아래 표.
- **골든 25컷**: hormuz dark `prev/` 25/25 md5 = phaseV3 기준선 일치, light(임시 복사본 `geo.prep --theme light` → `--preview golden`) 25/25 = phaseQ3 기준선 일치. → area 추가로 골든 픽셀 불변.
- 단, `test_provenance_e2e`·`test_q3_light_e2e` 는 **렌더 rc 1** 로 실패한다 — 원인은 area 가 아니라 checks hard `badge_hold`(UF-162, 1d462eb) 3건: hormuz 뱃지 '울산' 1.6초·'중국' 4.6초·'인도' 4.2초 < 6초. 이 브랜치 분기점부터 있던 실패(D-0289 장치가 hormuz 를 element_gap 만 면제). 결정 요청은 R-0297.

| 실패 테스트 | 원인 | 이 변경과 관계 |
|---|---|---|
| test_provenance_e2e / test_q3_light_e2e | badge_hold hard 3(골든 연출) | 없음(픽셀 25/25 일치) |
| test_catalog_layer::full_frame_md5 | hormuz res_720p 티어 없음(환경 — `geo.prep --res 720p` 미실행) | 없음 |
| test_element_gallery::full_gallery_renders | 장르 프로필에 area 없음 → **532beea 로 수정**(재실행 대기) | 있었음 → 고침 |
| test_user_feedback_guards::doc_guards_only | UF-145 원장(분기점 기존, D511) | 없음 |

## 환경 메모
- FONTCONFIG 표준 설정에 시스템·사용자 글꼴 폴더 `<dir>` 가 빠져 있었다(처음 만든 파일) — 고친 뒤 hormuz plan·골든 재실행. hormuz 권리·국기·휘장은 `projects/hormuz_korea_legacy/assets` 복사(run_log §4 절차).
