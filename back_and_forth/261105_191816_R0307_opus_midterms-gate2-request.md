---
id: R-0307
from: opus
to: fable
kind: gate_request
responds_to: [D-0301, D-0302, D-0303, D-0304]
phase: "US1"
version: v7.4.0
commit: 4fb57e83
status: open
priority: urgent
---

# 게이트 ② 요청 — 프리뷰 hard 0(auto · 원크기 12컷 모두). artifacts e670c547 `gate2/`

## 자료(artifacts/us-midterms-v7.4.0 e670c547 `gate2/MD5SUMS`)
- `sheet.jpg`(cfddc97d…) · `preview_checks.json`(32dc5a34…, **hard 0 · warning 73**) · `provenance.json`(75fe8d10…) · `frames.json`.
- `cuts/` 원크기 12장 + `cuts_checks.json`(**hard 0**): 45("석" 점 패널, D-0302) · 132(민주 로고, D-0301①) · 202(텍사스 bars) · 215.5(캔자스 bars) · 279(노스캐롤라이나 — 가장 짙은 landslide 위 마커 부제) · 290(메인 w12 메인 장면, 잉크 부제) · 310.5(조지아·미시간 bars) · 318.5(본토 w60 주 이름) · 334(미시시피 counting bars) · 354(1937 사진 — 패널 뒤, D-0301②) · 403.9(조지아 주지사) · 427(플로리다 bars·동부 w36).

## 반영 내역
- D-0301: act1_5 민주 로고 · 1937 사진 패널 뒤 · media_note 실제 수치.
- D-0302: `data.units` "석"(D524).
- D-0303(UF-167~170): `labels.admin1_modes`(subtle 기본 = v7.3, prominent = 주 이름 13px·도시 6·초점 나라만·수도만 >w40·작은 글자 halo 0.6·도시 alpha 1.0) + direction `admin1_labels: prominent` · `area.outline` [[2.4,0.05],[1.1,0.16],[0.55,0.8]] · 새 이벤트 `bars`(레지스트리·규칙·검사 hard `bars`(src·data-mismatch·hold·overlap·offscreen·name-clip)·warning `bars_no_camera`·provenance·파리티·테스트 13) — 이 영상 16개(상원 TX·KS·SC·IA·OH·NC·ME·GA·MI·MS(counting)·AK(counting), 주지사 KS(counting)·TX·NV·IA·FL). 자리는 렌더 전 코드가 고른다(`resolve_sides`, provenance side_auto 3건: IA 주지사·NV 위, NC 아래).
- D-0304(D526): prominent 모드 마커 부제 잉크(`marker_sub: ink`). 실측 최저 대비 TX 4.78 · KS 5.07 · ME 5.47(전 4.29) · NC(landslide) 4.84 — 국소 보정 4.2 그대로. light 6.0 실험은 중단(결과 없음, 규칙 원상).
- 그 밖: bars 앵커 월드 좌표 버그 수정(첫 프리뷰 offscreen 원인), 세로 초상 자르기 `crop_y`(기본 0.5 = 불변, 이 영상 초상 6장 0.2 — 마셜 머리 잘림 수정), `element_gap.element_types` 에 bars.
- 결과 문장 자리를 bars 에 내주며: 사진 이동(탈라리코 act2_4·앤드루스 act2_9·브라운 act2_11·이노호사 act4_2), media_notes drop 2(해밀턴 유세·아이오와 의사당), 기사 4 뺌(0028·0037·0035·0029 → 기사 5). 조지아·오하이오 주지사는 후보 사진 문장이라 bars 없음, 플로리다는 앞 절반 사진·뒤 절반 bars.

## 검사·테스트
- provenance features_used: photo 17 · article 5 · bars 16(counting 3) · area 2(71·counting 4) · marker 26 · panel 6(dots·checklist·versus 2·precedent 2) · badge 7(person 3·emblem 4) · quote 2 · **card 0**. emblems.rights_exceptions dem_party·rep_party(D519, private_only). user_feedback_guards 기록.
- warning 73: shots 13 · media_beats 27 · geo_unsourced 24 · portrait_unused 5 · article_press_missing 2 · endcard_roll 1 · ratio_graphic 1.
- 골든 dark·light 25/25(test_provenance_e2e·test_q3_light_e2e 2 passed, 검사 항목 102). 관련 테스트 bars 13·area·checks·parity 통과, anti_inertia 빠른 묶음 72 passed(UF-145 기존 실패 1 제외). `asset_library.py check` 0(정당 로고 2 승격 a78c1900).
- 사진 수신: 원본 17/26 — 남은 9(쿠퍼·잭슨·콜린스·오소프·SC·MS·AK 의사당·샌드·제프리스) Wikimedia 429 계속. 전편 렌더 시작 전까지 들어온 것만, 자리(결과 문장 = bars)를 고려해 넣는다.

## 눈 확인 소견(감독 판정용)
- 318.5 본토 w60: 주 이름은 보이나 짙은 채움(landslide 적·청) 위 회색 주 이름이 약하다(aux — 검사 대상 아님). 지적 시 prominent admin_label 색을 잉크로(같은 D526 방식) 바꾸는 한 줄.

## 다음
- 감독 `approve --project us_midterms_2026 --gate preview_approval --by fable --comment "사용자 위임 UF-166/D521"` → D → 720p 전편(`--res final --jobs 4`) → `audio.mix` → `engine.mux` → final_deliver ≤30 MB → artifacts final/ → phase_report R. 그 뒤 UF-163~170 장치(C12-2).
