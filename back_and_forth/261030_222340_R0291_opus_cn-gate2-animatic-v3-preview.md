---
id: R-0291
from: opus
to: fable
kind: gate_request
responds_to: [D-0288]
phase: "CN1"
version: v7.4.0
status: open
---

# 게이트 ② 자료 — 콘티 판 v3 + 프리뷰 시트 (checks hard 0 · card 0)

## 자료(artifacts/china-export-controls-v7.4.0, 108e2edc — `china_tech_export_controls_2026/`)
- `animatic_v3.mp4` 27.8 MB(`-c:a copy`), 397.1초, md5 `8cc7343111631ce0031f6d174181c891` · `animatic_v3_sheet.jpg`(23컷) · `animatic_v3_changed_cuts.jpg`(바뀐 컷 4곳 854×480 원크기: 128초 MTA 커터헤드 · 175초 부산 회담 뱃지 · 224초 조시 quote · 322초 태양광 사진 act3_10) · `animatic_v3_checks.json`(hard 0) · `animatic_v3_provenance.json`
- `gate2/preview_sheet.jpg`(`--preview auto` 14컷, 렌더 사진·뱃지·국기 실물) · `gate2/preview_checks.json`(**hard 0** · 경고 22) · `gate2/preview_provenance.json`
- 원고 지문 69b37300(게이트 ① 과 같다). 콘티 판 기록 out/animatic_provenance.json(plan 길이 397.1초).

## v3 변경(D-0288 ①~⑤)
| # | 내용 |
|---|---|
| ① | act2_9 quote — 직함 "옵서버연구재단 마노즈 조시", 국기 in, 문장 "중국이 기술로 만든 제품은 팔면서 기술 우위는 지키려 한다"(원고 문장 안 구절, clm_0027 귀속) |
| ② | act2_3 트럼프·시진핑 badge(문장 앞부분 ~ "중국은") → 이어서 김해 회담 사진("중국은" ~ 끝). portrait_unused 해소 |
| ③ | act1_14 MTA 커터헤드 사진 `cn_mta_cutterhead_2019`(CC BY 2.0, MTA Capital Construction East Side Access Flickr — Commons 검색 통과·WebSearch 같은 계정 CC BY 2.0 대조, 해체 중인 실드·커터헤드 육안 확인). 후보 3장 중 커터헤드가 보이는 것 |
| ④ | act3_9 태양광 사진 → act3_10. act1 40초 창: 회전식 세포 배양 장치 사진 삭제(53~78초 3장 → 2장). 사진 합계 **10**(하한 9.93 유지) |
| ⑤ | media_note 에 베선트 뱃지 생략 사유(김해 회담 테이블 사진에 함께 찍힘 · act2_5 versus 위 뱃지 = badge-over-panel hard) |
| + | 프리뷰 hard `units_visible`: dots 패널 단위 없음 → `unit: 건`(rules data.units 에 '개' 없음), 패널 글자 40건·14건·26건. **콘티 판 v3 뒤 바뀐 패널 글자는 이것 하나** |
| + | 백악관 사진 2장: 레지스트리가 사진의 `scope: private_only` 를 금지(inset·video 만, D234·D264) → 미 정부 저작물(PD) rights_clear 로 두고, 엔딩 표기 행의 "백악관 사진은 비공개 시청 한정" 문구 삭제(프리뷰 엔딩 카드에는 아직 옛 문구 — 전편에서 반영) |

## 수치(프리뷰 provenance)
card 0 · photo 10(x 227·y 72·w 400) · article 9 · marker 11 · badge 4(트럼프·시진핑 ×2 장면) · quote 3 · panel 5(timeline 두 개 axis 2026-10-01→12-01 동일) · route 1(개략) · country 4 · dip 2 · camera keys 16.

## 경고(hard 아님)
- media_beats: 옛 40초당 1장 규칙 vs 밀도 하한 1.5/분 경계(10장 = 39.7초/장), 2막 168~208초 3장(희토류·김해 두 장), 장면당 사진 > 1.
- timeline-overlap: '공고 열흘' 10/16·10/19 핀 라벨 근접(사흘 차, 층 분리).
- 숏 머무름 < 6초 몇 곳, 엔딩 크레딧 롤 34.8 px/s(상한 60).

## 테스트(관련 + anti_inertia, not slow)
- 71 passed · 2 failed: ① `test_catalog_layer` — hormuz 골든 자산 미복원(환경, 복원 진행 중) ② `test_user_feedback_guards::test_doc_guards_only_for_process_items` — UF-145(커밋 929b4b2, 이 트랙 이전 원장 등재)의 장치 판정. 이 트랙 변경 파일(media_registry·entities·프로젝트 파일)과 무관.

## 다음
- 게이트 ② 승인 뒤: 720p 전편(`--jobs 4 --res final`) → audio_mix·deliver → final_deliver.mp4 ≤ 30 MB → artifacts → 최종 R(phase_report).
