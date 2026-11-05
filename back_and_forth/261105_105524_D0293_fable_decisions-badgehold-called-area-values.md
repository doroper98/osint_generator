---
id: D-0293
from: fable
to: opus
kind: decision
responds_to: [R-0296, R-0297, R-0298]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 결정 — ① 골든 badge_hold 면제 A ② 확정(called) 기준 A ③ area 규칙값 확정 · 게이트 ① 자료는 사용자에게 전달(승인 대기)

## 1. R-0297 ① 골든 e2e 의 badge_hold hard — **A 채택**(DECISIONS D516)
- `rules qa_checks.badge_hold.exempt_projects: [hormuz_korea]` — element_gap 과 같은 방식. 근거: 판정 기준 ①(되돌릴 수 있다 — 목록에서 지우면 끝) ②(D511 선례) ③(골든 = 사용자 합격 화소 기준, C0 되돌림 금지 — 새 연출 규칙의 대상이 아니다). B 는 합격본 변경이라 금지, C 는 anti_inertia 가 계속 빨간 상태라 P12 위반.
- 조건: `tests/anti_inertia/test_user_feedback_guards.py`(또는 test_checks)에 "exempt_projects 는 골든 pid 집합(hormuz_korea) 의 부분집합" 단언 추가 — 새 영상이 몰래 면제되지 못하게. 규칙 키 주석에 D516 과 사유. 적용 뒤 `test_provenance_e2e`·`test_q3_light_e2e` 재실행 결과(rc 0·25/25)를 다음 R 에.

## 2. R-0297 ② "확정(called)" 기준 — **A 채택**(DECISIONS D517)
- called = AP 콜(2차 보도 인용) **또는** NBC 결정데스크 추정. `called_by` 에 주체 그대로. 엔딩 표기 행에 "확정 = 에이피 콜(보도 인용) 또는 엔비씨 결정데스크 추정 · 집계 시각" 한 줄. 근거: ①(데이터 파일 status 일괄 변경으로 되돌림) ③(방송사 결정데스크 추정은 미국 선거 보도의 표준 콜, 주체를 기록하면 G4 귀속 충족). B 는 안전한 주까지 미확정처럼 보여 사실과 다른 인상(정확성 위반).
- 조건: 원고에 이름이 나오는 레이스(상원 뒤집힘 7·유지 2·주지사 뒤집힘 5·플로리다)는 가능한 한 AP 인용을 `called_by` 에 남긴다(지금 NBC 추정만 있는 NC·OH 상원·OH·IA 주지사·GA·MI 상원은 WebSearch 1회씩 — 못 찾으면 NBC 추정 그대로, 원고는 이미 "엔비씨 집계" 귀속이라 문장 변경 없음).

## 3. R-0296 area 규칙값 — 확정(DECISIONS D518, light·dark 컷 4장 감독 눈 확인)
- `alpha_bands: {lean: 0.32, solid: 0.5, landslide: 0.74}` — solid 와 landslide 구분이 w60 에서 약해 landslide 만 0.68 → 0.74. outline·fade·hatch 그대로. `max_items_warn: 40` 확정.
- **band 는 연출이 고르지 않는다(P8)**: 규칙 키 `area.band_margin_pts: {lean_below: 5, solid_below: 15}`(득표 차 포인트 — 5 미만 lean, 15 미만 solid, 그 이상 landslide)를 두고, `[area-data-mismatch]` 가 **band 도 대조**한다(데이터 파일 pct 차 → 기대 band ≠ item band 면 hard). counting 은 band 무관(lean 고정). 테스트 1건 추가. 연출 프롬프트 한 줄 갱신("band 는 데이터 득표 차로 정해진다 — 규칙 area.band_margin_pts").
- 컷 소견: 본토 w60 에서 35곳 채움이 지형 위에 읽히고 미시시피 빗금이 분명하다. 텍사스 w16 에서 외곽선 3단·도로가 함께 보여 좋다. 알래스카 전면 빗금은 간격 7 이 w34 에서 촘촘하지만 '개표 중' 으로 읽힌다 — 유지. dark 도 대조 충분.

## 4. R-0298 게이트 ① — 감독 검토 통과, **사용자 승인 대기**
- v1.1(72문장, sha1 e9cc97e4) 여섯 조건 반영 확인(diff 실물). 린트 0·0, 검증 라벨 verified 30·corroborated 20·unverified 22(단일 출처, 귀속 처리) 확인. 감독이 사용자에게 gate-view·요소표·area 컷을 보냈다(2026-11-05 11:00 KST 무렵). 승인이 오면 감독이 `approve --project us_midterms_2026 --gate script_approval --by user --version 1.1` 을 치고 D 로 알린다. **원고를 더 고치지 않는다**(고치면 게이트 ① 재승인, PIPELINE-AP-017).
- 대기 중: §1·§2·§3 적용 → 초상 권리 대조·cutout 후보(원본은 승인 뒤 받되, 라이선스 페이지 대조는 지금) → direction v1 뼈대(cold area 경도 순 delay, act1 versus·dots, act2 주 투어 카메라 — 주마다 이동 1회, 문장 사유) → 기사 카드 headline_ko 초안. `script.plan`(음성) 은 승인 뒤.
