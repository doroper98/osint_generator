<!--
tier: 3
last_synced_with: v5.15.0
ssot_for: [phaseQ2-run-log]
depends_on: [docs/handoff/23_QUALITY_GUIDE_20261010.md, docs/handoff/07_PEOPLE_FLAGS_EMBLEMS_RIGHTS.md, engine/layers/badges.py, rules/video_rules.yaml]
last_review: 2026-10-10
-->

# Phase Q2 실행 기록 — 인물 뱃지·국기 물결 V2 (v5.15.0)

지침은 D-0153 §5, D-0158 보강 2, **D-0159(사용자 지시 D152)** 입니다. 근거는 사용자 결정 D148(인물 뱃지 적용)과 가이드 23 §10 입니다.

D-0159 로 바뀐 것 세 가지입니다. ① 링 두께는 이전 그대로(가이드 2.4/0.8 미적용) ② 이재명 얼굴 잘림 수정(머리 우선 축소) ③ 이재명 사진 후보 시트(§3.1).

## 1. 바뀐 것

| 파일 | 내용 |
|---|---|
| `rules layout_480p.badge` | `portrait{width, min_width, alpha_top, alpha_thr, head_scan, head_h_ratio, head_margin_px, shadow_alpha, shadow_dy}`·`flag_wave{cx, cy, width, alpha, strip_px, strips_min, strips_max, speed, phase_span, amp, shade_alpha, shade_phase}`·`ring{outer_w, inner_w, outer_rgb, inner_alpha}` 추가, `head_inside_max` 삭제 |
| `engine/layers/badges.py` | `flag_wave` 다시 씀(작업 표면·정수 열), `wave_strips`·`strip_columns`·`portrait_alpha_top`·`head_box`·`portrait_fit`·`PortraitFitError` 추가, 인물 초상 배치·그림자 교체, 링 = 모든 뱃지 `badge.ring` 한 경로, `portrait_top` 삭제 |
| 문서 | handoff `07` §10 |

| 항목 | v5.14.0 | v5.15.0 |
|---|---|---|
| 초상 폭 | 1.72R | **2.04R**, 머리 상자가 원 안에 안 들면 1.4R 까지 줄임(이재명 R56 1.77R·하메네이 1.82R, 트럼프·노무현 2.04R) |
| 초상 세로 자리 | 발끝 1.02R, 정수리 > 0.9R 이면 내림(`head_inside_max`) | **정수리(알파 > 20 맨 윗줄) = 중심 위 0.83R** |
| 얼굴 분리 그림자 | 없음 | 초상 알파 모양, 0.8 설계 px 아래, 검정 0.16 |
| 국기 중심·폭 | (0.25R, −0.05R), 2.3R | **(0.16R, −0.05R)**, 2.3R |
| 띠 | 14띠, +1px 겹침 클립 | **장치 폭 기반 14~96**(480p solo 96·R30 69, 1080p 96), 정수 열(겹침·빈 줄 0) |
| 위상·진폭 | t·2.6 + i·0.5, 0.032·폭 | **t·2.6 + (i/n)·7, 0.018·폭** |
| 띠 그림자 | 0.16·(0.5 + 0.5 sin(위상 + 1.2)), 띠 사각형 전체 | 같은 식, 국기 픽셀에만(ATOP) |
| 링(모든 뱃지) | 어두운 3.2 + accent 1.5(같은 원), 리터럴 | **같은 값**(사용자 지시 D152), `badge.ring` 키 |
| 국기·휘장 뱃지, 국장 | — | 그대로 |

## 2. 골든(D-0158 보강 2)

골든 PNG 는 수정하지 않았습니다. `expected_deltas q2_portrait_flag_d148` 과 `phaseQ2/hormuz_baseline.json` 을 더했습니다.
phaseG17 대비 바뀐 컷은 9개입니다. 뱃지 8컷은 변화가 모두 원 안이고(링 두께 그대로), 엔딩 컷은 인물 사진 크레딧 줄만 바뀝니다(D-0160).

| 컷 | 내용 | 바뀐 픽셀 | 상자 |
|---|---|---|---|
| 01 open_1 `p_0007.82` | 이재명 solo R56(공식 초상) | 9,425 | 60,33 – 169,141 |
| 02 TITLE `p_0022.27` | 제목 뒤 이재명(어둡게) | 9,223 | 57,31 – 165,140 |
| 06 war_1 `p_0056.21` | 하메네이 solo | 9,385 | 545,21 – 654,129 |
| 09 ask_1 `p_0080.70` | 관계 패널 트럼프 R36 | 3,800 | 200,227 – 269,296 |
| 10 ask_2 `p_0087.06` | 같음 | 3,798 | 200,227 – 269,296 |
| 17 past_1 `p_0193.22` | 패널 노무현(작은 뱃지) | 1,622 | 171,300 – 216,344 |
| 18 past_3 `p_0207.41` | 같음 | 1,624 | 171,300 – 216,344 |
| 22 decision_0 `p_0245.56` | 이재명 solo(공식 초상) | 9,380 | 65,77 – 173,185 |
| 25 END `p_0288.44` | 엔딩 크레딧 인물 사진 줄(도장 가린 md5) | 759 | 64,258 – 223,266 |

나머지 16컷은 phaseG17 과 같습니다. 국기만 있는 뱃지(08컷 중국·인도 등)도 그대로입니다.
작업 전 렌더 25컷이 phaseG17 기준선과 같은지 먼저 확인했습니다(대조 시작점 검증).

## 3. 시트(사용자 확인용)

| 파일 | 내용 |
|---|---|
| `hormuz_badge_cuts_before_after.jpg` | 바뀐 9컷, 480p 실크기, 왼쪽 phaseG17 · 오른쪽 phaseQ2(이재명 = 공식 초상) |
| `hormuz_badge_faces_x4.jpg` | 같은 9컷의 바뀐 상자 4배(nearest) |
| `badge_sizes_480p.png` | 인물 4명 × R56·R34·R30, 480p 실크기, 옛/새 코드(이재명은 교체 전 사진 — 코드 비교용) |
| `badge_faces_x4.png` | R56·R30 얼굴 가운데 4배, 옛/새 |
| `golden_delta/*_old_new_diff.jpg` | 컷마다 옛·새·차이(×4) |

**시트에서 보인 점(기록):**
1. 옛 14띠 국기에 흰 세로 줄(띠 경계 빈 줄)이 보였습니다(하메네이·이재명 R56). 새 방식에는 없습니다.
2. 얼굴이 커지고 정수리가 원 안 0.83R 에 놓입니다.
3. 첫 시트(2.04R 고정)에서 이재명은 입·턱이 원 아래에 잘렸고, 링 0.8 은 색 구분이 약했습니다. 사용자 지시 D152 로 링은 이전 두께, 얼굴은 머리 우선 축소(§3.1)로 고쳤습니다. 지금 시트는 고친 뒤입니다.
4. 작은 뱃지(노무현 패널, R≈20)도 띠 뭉개짐 없이 국기 모양이 남습니다.

### 3.1 머리 우선 축소(D-0159 ②)

얼굴 인식 도구(OpenCV 등)는 저장소 의존성에 없습니다. 그래서 초상 알파 실루엣으로 머리 상자를 잡습니다.
- 머리 폭 = 정수리에서 아래로 초상 폭 × `head_scan`(0.5) 안의 줄 중 가장 넓은 줄(어깨 위). 머리 열 = 그 줄의 왼쪽~오른쪽.
- 턱 줄 = 정수리 + `head_h_ratio`(1.3) × 머리 폭. 사람 머리 높이 ≈ 폭의 1.3배라는 보수적 비율입니다. 4명 원본에 그어 보니 턱 바로 아래(이재명·하메네이)·옷깃 위(트럼프·노무현)였습니다.
- 정수리 ~ 턱 줄 × 머리 열 안의 초상 픽셀이 원(R − 1.6 설계 px) 안에 들 때까지 폭을 2.04R → 1.4R 사이에서 줄입니다(이분 탐색, 내림). 1.4R 로도 안 들면 `PortraitFitError`(렌더 전 오류).
- 어깨(머리 열 밖)는 원에 잘려도 됩니다. 원형 뱃지에서 어깨까지 원 안에 넣으면 얼굴이 너무 작아집니다(D-0159 표의 "어깨 잘림 0" 은 머리 열 기준으로 읽었습니다 — 판단 기록 7).
- 시도했다 버린 방법: 실루엣 폭이 가장 좁은 줄을 목으로 보는 방식은 이재명은 입을, 트럼프·노무현은 어깨를 목으로 잡아 쓰지 않았습니다.

| 초상 | R56 | R34 | R30 | R20 |
|---|---|---|---|---|
| 이재명 | 1.7708 | 1.7509 | 1.7442 | 1.7155 |
| 하메네이 | 1.8218 | 1.8013 | 1.7943 | 1.7647 |
| 트럼프 | 2.04 | 2.04 | 2.04 | 2.04 |
| 노무현 | 2.04 | 2.04 | 2.04 | 2.04 |

### 3.2 이재명 초상 = 대통령실 공식 초상(D-0160, 사용자 결정 D153)

D-0159 의 후보 시트(A·B·C)는 D-0160 으로 취소됐습니다. 받던 후보 B 는 만들다 멈췄고 저장소에 넣지 않았습니다.
조사 중 확인한 사실: **옛 사진(v01)이 바로 후보 A(백악관 PD, Commons 크롭본)** 였습니다. 출처는 프로젝트 `rights_registry.json` 에 완전히 기록돼 있었고, 라이브러리 승격만 안 돼 있었습니다(`asset_library check` = 이재명·노무현·휘장 2). 그래서 RIGHTS-AP 는 더하지 않았습니다.

| 항목 | 값 |
|---|---|
| 원본 | `https://www.president.go.kr/greeting` 프로필 사진 `…/type/www/img/contents/president/profile_img.png` |
| 원본 정보 | 983×656 RGBA(배경 투명), Last-Modified 2026-04-17, sha256 `9010ae995141a55733f3f0ea6ce5f0e0b888a7ef1e8f7ea5a7861534d4825306`, 받은 때 2026-10-10 13:10 UTC |
| 라이선스 전문 | 공공누리(KOGL) 제4유형: 출처표시, 비상업적 이용만 가능, 변형 등 2차적 저작물 작성 금지(`/copyright-policy`) |
| 처리 | 흰 바탕 합성(rembg 입력용) → 머리 폭 × 2.4 가로 자르기(x 166~822, 세로 전체 — 원본이 어깨가 넓어 그대로면 얼굴이 작다) → `portrait_fallback.py` v3(rembg u2net_human_seg·알파 흐림 0.8·흑백·정규화 420) |
| 권리 | `rights_status: restricted`, `user_exception: U20261010`(`USER_EXCEPTIONS` — 인물에도 같은 사전), `exception` 사유 문구. 라이브러리 `lee_jae_myung_mono_v02.png` 에 같은 기록 |
| 크레딧 | "이재명" / "대통령 공식 초상 · 대통령실 · 공공누리 제4유형"(이름은 직함 없이 — D-0106 2-B, 문구는 D-0160 그대로) |
| 점검 | `engine.credits.check_credits` 는 등록된 예외가 있는 restricted 인물만 통과시킵니다. provenance `rights.exceptions` 에 1건이 남습니다(P6) |
| 옛 v01 | `projects/hormuz_korea/assets/portraits_archive/lee_jae_myung_v01_whitehouse.png`(삭제 안 함, 권리 기록은 새 항목 `processing.replaces` 에) |
| 받는 경로 | `fetch_data people` 이 이재명을 라이브러리(v02)에서 받습니다. v5.15.1(D-0164)부터 변형 `normalized: true` 면 바이트 그대로 복사하고, 권리 상태·예외는 라이브러리 값 그대로 옮깁니다(§9) |
| 머리 맞춤 | 공식 초상은 R56·R30 모두 2.04R 그대로 들어갑니다(정수리·턱 잘림 0) |

**배포(공개 게시) 전에는 이 예외를 다시 확인해야 합니다.** 공공누리 제4유형은 변경 금지·비상업 조건이고, 뱃지는 흑백·배경 제거·자르기 가공입니다(07 §3.2, 19 §3 3.22).

함께 승격된 것: 노무현 초상(`roh_moo_hyun_mono_v01`, KOGL Type 1)과 휘장 2개(청와대·NAVCENT). `promote` 가 프로젝트의 승격 대기 자산을 한 번에 올리기 때문입니다(C8.7 이 요구하는 상태).
`promote --version 2` 가 노무현에게도 v02 를 붙여, 노무현만 v01 로 바로잡았습니다(판단 기록 9).

## 4. 성능(D-0158 보강 1, 가이드 §21)

같은 장면(hormuz 01·06·22컷)에서 컷마다 프로세스 하나, 데운 뒤 연속 48프레임입니다. 4코어 CPU입니다.

| 해상도 | 컷 | 전 평균 / p95 ms | 후 평균 / p95 ms | 전 / 후 최대 메모리 MB |
|---|---|---|---|---|
| 480p | 01 (7.82) | 56.6 / 75.1 | 51.1 / 54.9 | 179.7 / 181.2 |
| 480p | 06 (56.21) | 65.8 / 71.5 | 66.3 / 76.9 | 180.9 / 181.3 |
| 480p | 22 (245.56) | 53.5 / 70.2 | 55.7 / 68.5 | 182.5 / 184.2 |
| 1080p | 01 | 117.9 / 159.7 | 119.2 / 161.5 | 358.6 / 359.5 |
| 1080p | 06 | 155.4 / 175.9 | 149.4 / 158.0 | 359.2 / 361.5 |
| 1080p | 22 | 113.7 / 129.1 | 114.7 / 126.9 | 361.1 / 360.9 |

프레임 시간 차이는 측정 흔들림 안입니다. 최대 메모리는 1~2 MB 늘었습니다(작업 표면).

**국기 물결만 따로**(호출 400회 평균, `kr` 국기):

| 해상도 | R | 장치 폭 px | 새 띠 수 | 옛 14띠 ms | 새 방식 ms | 새 방식 14띠 고정 ms |
|---|---|---|---|---|---|---|
| 480p | 56 | 129 | 96 | 0.145 | 0.598 | 0.167 |
| 480p | 30 | 69 | 69 | 0.085 | 0.335 | 0.098 |
| 1080p | 56 | 291 | 96 | 0.464 | 1.225 | 0.517 |
| 1080p | 30 | 156 | 96 | 0.199 | 0.768 | 0.214 |

- 새 방식을 14띠로 고정하면 옛 방식과 비슷합니다(+0.02~0.05 ms). 늘어난 비용은 띠 수(최대 96) 몫입니다.
- 뱃지 하나에 프레임당 최대 1.2 ms(1080p)로, 프레임 시간의 1 % 안팎입니다.
- 얼굴·국기 표면은 크기당 한 번만 만듭니다(`Assets.scaled` 캐시). 정수리 재기는 초상당 한 번입니다(`R.cache`). 테스트로 확인했습니다.

## 5. 판단 기록(되돌릴 수 있는 선택)

1. 띠 수 공식 = `clamp(ceil(장치 폭 ÷ strip_px), 14, 96)`, `strip_px` 1.0. D-0153 "480p 96 상한, device 폭에 비례, 하한 14" 를 장치 1px 당 띠 하나로 읽었습니다.
2. 겹침·빈 줄 0 을 위해 띠를 장치 해상도 작업 표면의 **정수 열**로 나눴습니다. 결과는 알파 한 번으로 칠합니다(옛 방식은 띠마다 알파를 칠하고 +1px 겹쳐서, 겹친 열이 진해지거나 빈 줄이 생겼습니다).
3. 얼굴 분리 그림자의 오프셋 0.8 설계 px 는 가이드에 값이 없어 링 안쪽 폭과 같은 값으로 정했습니다. 흐림은 넣지 않았습니다(머리 둘레 halo 방지, 가이드 §10).
4. 링 위치: 어두운 링은 원 바깥쪽(R ~ R + 2.4), accent 는 원 안쪽(R − 0.8 ~ R). "바깥 어두운·안쪽 파란"을 그대로 그렸습니다.
5. `head_popout: true`(v3 머리 내밀기) 경로는 옛 배치(1.72R)를 그대로 둡니다. 현재 규칙은 false 이고, 이번 지시 범위 밖입니다.
6. 링은 사용자 지시 D152 로 이전 두께(3.2/1.5)입니다. 모든 뱃지가 `badge.ring` 한 경로를 쓰고, 값이 같아 국기·휘장 뱃지 출력은 그대로입니다(골든 08컷 무변경).
7. D-0159 의 "정수리·턱·어깨 잘림 0" 중 어깨는 머리 열 안만 봅니다(§3.1). 원형 뱃지 구도상 어깨 바깥쪽은 잘립니다(v3 이후 같음).
8. 얼굴 인식 의존성을 더하지 않고 실루엣 비율 규칙으로 했습니다(되돌릴 수 있음 — 규칙 키 두 개). 맞지 않는 초상은 렌더 전 오류로 드러납니다.
9. `asset_library promote --version N` 은 이번 승격 전체에 같은 번호를 붙입니다. 이번에는 노무현을 v01 로 손으로 바로잡았습니다. 인물별 번호가 필요하면 다음에 인자를 인물 단위로 바꿉니다.
10. 공식 초상의 가로 자르기(머리 폭 × 2.4)는 구도 맞춤입니다. 얼굴·색은 바꾸지 않았고, 처리 이력(`pre_steps`)에 좌표를 남겼습니다.
11. 크레딧 문구는 D-0160 대로 두되, 이름 칸은 직함 없는 "이재명"(D-0106 2-B 규칙·테스트)으로, 나머지를 라이선스 칸에 적었습니다.

## 6. 테스트

`tests/test_q2_portrait_flag.py` 14개입니다(요구 ≥ 8).

| 테스트 | 내용 |
|---|---|
| `test_strip_count_follows_device_width` | 480p solo 96, R30 = 장치 폭, 1080p 상한 96, 아주 작으면 14 |
| `test_columns_partition_without_overlap_or_gap` | 정수 열 분할 = [0, 폭) 정확히 한 번씩 |
| `test_wave_surface_full_columns_single_alpha` | 작업 표면 가운데 줄 모든 열 불투명, a = 0.5 결과 알파 일정(겹침 진해짐 0) |
| `test_wave_phase_amplitude_and_surface_reuse` | 띠마다 윗변 = pad + sin(위상)·진폭(±1px), 작업 표면 하나 재사용 |
| `test_crown_at_alpha_top` | 정수리 = 중심 위 0.83R(±1.5px), R56·R34·R30 |
| `test_alpha_top_measured_once_and_threshold_separate` | 정수리 재기 한 번, 표면 캐시 늘지 않음, 배치 문턱 20 ≠ 정규화 40(알파 30 윗줄 = 정수리) |
| `test_flag_wave_and_person_paths_have_no_magic_numbers` | 옛 리터럴이 flag_wave·인물 경로에 없음, 규칙 값 = 가이드 |
| `test_ring_one_path_for_all_badges` | 링 = 모든 뱃지 `badge.ring` 한 경로, 리터럴 없음 |
| `test_ring_same_thickness_as_before` | 링 이전 두께 3.2/1.5(D152) |
| `test_four_people_head_inside_circle` | 4명 × R56·R30 머리 상자 원 안, 옛 이재명 사진은 줄어듦 |
| `test_too_wide_head_shrinks_or_errors` | 넓은 머리는 축소(정수리 자리 그대로), 못 맞추면 PortraitFitError |
| `test_registry_accepts_only_listed_exception` | 예외 목록 밖 인물·사유 없는 예외 거부 |
| `test_credit_check_and_provenance` | 등록 예외만 restricted 통과, provenance 1건 |
| `test_library_v02_and_fetch_keep_restricted` | 라이브러리 v02 restricted·파일, fetch_data 라이브러리 경로·restricted 유지 |

기준선 테스트 2개(`test_provenance_e2e`·`test_g12_version_stamp`)의 기준선 경로를 phaseQ2 로 바꿨습니다. `test_g65_merge` 는 문구를 직접 적은 인물 크레딧 행도 읽게 바꿨습니다(수 변화 없음).

## 7. 전체 pytest

`FONTCONFIG_FILE` 표준 설정입니다.

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| Q1 끝 | 1445 | 0 | 0 | 0 |
| Q2 끝(76b5cfa 전체 실행) | 1458 | 1 | 0 | 0 |
| 실패 1건 고친 뒤 | **1459** | **0** | **0** | 0 |

- 실패 1건 = `test_g7_cheongwadae.test_registry_entry_and_exception` — 사용자 예외 목록 전체를 고정 단정하는 테스트라, 새 예외(U20261010, D153)를 목록에 더했습니다. 고친 뒤 그 파일 단독 4 passed.
- 기준 1445 + 14 = 1459 = 실측입니다(28분 8초). `-rs` 출력에 SKIPPED 줄이 없습니다.

## 9. v5.15.1 — 받는 경로 수정(D-0164)

Fable 검수에서 나온 결함 2개와 작은 것 1개를 한 커밋으로 고쳤습니다. 기준선·expected_deltas 는 바꾸지 않았습니다.

| # | 결함 | 수정 |
|---|---|---|
| 1 | `library_portrait` 가 승격된 정규화 완료본을 다시 `normalize_portrait`(비멱등 — 끝 줄·열 탈락, 420 재샘플, 415×420 → 414×420) → 새 컨테이너 이재명 3컷 불일치(22/25) | 변형 기록 `normalized: true`(`LibraryAssetVariant`, 기본 false) → 바이트 그대로 복사. `promote` 가 적고, 기존 이재명 v02·노무현 v01 에 적음. 트럼프·하메네이(원본)는 그대로 정규화 |
| 2 | `fetch_data` 가 권리 상태를 예외 유무로 추정(예외 없는 restricted → rights_clear) | `fetch_data.library_rights()` — 라이브러리 `rights_status` 그대로, 예외 필드는 있으면 복사 |
| 작은 것 | `PortraitFitError` 가 첫 뱃지 그리기에서 났다("렌더 전" 문구와 다름) | `engine.project.portrait_fit_errors` 를 preflight 에서 인물마다 R(solo 56·group 30·34·panel 36)로 |

**라이브러리에서 받은 프로젝트로 골든 재현**(스크래치 사본, 초상 4장을 `library_portrait` 로 다시 받음):

| 초상 | 받은 파일 md5 | 저장소 프로젝트 파일과 |
|---|---|---|
| 이재명(v02, normalized) | `93681b132b42a2be04da323ca5a116b0` | 같음 |
| 노무현(v01, normalized) | `f3a37ba74fb1c2e121b04819cf0b97a4` | 같음 |
| 트럼프(원본 → 정규화) | `f2cd16bd229947837c8db5f19c401459` | 같음 |
| 하메네이(원본 → 정규화) | `4b531c7b949e41b5f687895ef0ebf9df` | 같음 |

`python -m engine.render <사본> --preview golden` → phaseQ2 기준선 **25/25**(25_END 도장 가린 md5 포함).

테스트 4개 더함(`tests/test_q2_receive_path.py`): normalized 변형 바이트 복사(+ 재정규화 비멱등 재현), promote → 받기 왕복 바이트 동일, 예외 없는 restricted 유지 → 크레딧 점검 오류, 맞지 않는 초상 → preflight 오류(pid·R). `test_library_v02_and_fetch_keep_restricted` 의 소스 문자열 단정은 동작 단정으로 바꿨습니다.

전체 pytest(v5.15.1, 2165ddd): **1463 passed · 0 failed · 0 skipped**(1459 + 4, 29분 5초). `-rs` 출력에 SKIPPED 줄이 없습니다.
