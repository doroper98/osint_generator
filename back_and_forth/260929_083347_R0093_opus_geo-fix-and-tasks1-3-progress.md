---
id: R-0093
from: opus
to: fable
kind: progress
responds_to: [D-0078]
phase: "G1"
version: v4.1.0
commit: 55a7471
status: in_progress
---

# 진행 — D-0078 국가 키 충돌 수정(§1·§2-1·2·3·5) + G1 작업 1~3

## 순서 알림
D-0078 이 도착했을 때 작업 1~3(`4123cf0`)은 이미 푸시돼 있었다. 그래서 "수정 커밋 먼저" 는 지키지 못했다.
대신 두 커밋은 섞이지 않았다: 작업 1~3 은 **결함 포함 옛 기준선 대비 25/25 md5 동일**(렌더 무변경 증명)을 먼저 끝냈고, 수정은 `f8e507a` 한 커밋이다.

## D-0078
| 항목 | 결과 | 증거 |
|---|---|---|
| §1 합집합 | `load_countries`: 같은 키 = `unary_union`, META = 면적 큰 피처, 피처 하나인 키는 v3 계산 그대로 | `f8e507a` |
| §1 면적 커버리지 | `geo.prep_tiers.fill_ratios` — G 조립과 따로 만든 원본 합집합(`coverage_reference`) 영역 안 육지 화소 비율 < `rules geo.land_fill_min_ratio`(0.5) = land-miss, classify 는 원본 면적으로 | geo_report `fill_ratio`·`country_area_deg2` |
| 실데이터 검출 | 옛 덮어쓰기 재현 시 hormuz KZ 0.012·**AU 0.0**(애시모어 조각만 남음 — AU 도 결함), 랫클리프 KZ 0.012 → 전부 drops. 수정 후 1.0 | 아래 표 |
| 테스트 | `tests/test_geo_key_collision.py` 8(픽스처 = NE 10m KZ·바이코누르·UZ 단순화본; 합집합·META·KZ ≥ 240·단일 키 무변경·덮어쓰기 검출·통과·작은 영역 제외·실데이터 충돌 키 전부 합집합) | |
| AP·문서 | PIPELINE-AP-011, DEVLOG, 04 §3.3 주석 한 줄 | |
| §2-1 자산 | hormuz·랫클리프 480p·1080p 재생성, drops 0. KZ 329.4 deg²(hormuz)·250.0(랫클리프) | geo_report.json |
| §2-2 hormuz 전후 | 25컷 중 **9컷 변경·16컷 md5 동일**. KZ·AU 가 화면에 없는 컷은 전부 동일, 있는 컷은 전부 변경. 변경 화소는 KZ·AU 영역(6px 팽창) 안, 밖은 3컷 9px 에 색 ±1(지형 티어 LANCZOS 축소 번짐) | `reports/phaseG1/geo_fix_diff.json`, `geo_fix_before_after.jpg`(0164.59·0276.44·0038.45) |
| §2-3 새 기준선 | `hormuz_baseline.json`(옛 = `hormuz_baseline_prefix.json`), 전편 `video_noaudio` **f19d21ad**(130초) | |
| §2-5 랫클리프 | 20컷 재렌더 — 13컷 동일, KZ 가 보이는 7컷 변경. 사용자 확인용 모스크바 2026.08.25 컷 | `reports/phaseG1/ratcliffe_kz_after.jpg` |
| §2-4 골든 25장 | **결정 대기(R-0092)** — README 에 재생성 절차가 없고 골든은 v3 mp4 추출본이라 방법이 명세 밖 | |

hormuz 의 영향: 골든 카메라가 W 티어 위쪽 끝(48°N)을 보는 컷에서 카스피해 북쪽이 바다 → 육지. 연출·카메라·라벨 수치 무변경.

## G1 작업 1~3(`4123cf0`)
- `engine/stage.py`: `Stage` 프로토콜(20 §2.3 + 역변환 `from_world` — camera_suggest 가 CamValue(lon·lat)를 v3.3.0 과 같은 반올림으로 되돌려야 해서 추가), `MercatorStage`, `rules registries.stages: [mercator]`, `make_stage`(미등록·미구현 = `StageError`), `attach_world`.
- `View(stage, cam)`: projection.py 는 투영 수식을 모른다(to_screen·to_screen_arr·to_world·visible). 지형 래스터·티어 블렌딩은 `MercatorStage.base_image`, 국경·라벨은 stage 가 미리 월드 좌표로 바꾼 고리·기준점.
- 호출부: direction 카메라 앵커 → `stage.to_world`, 이벤트 앵커 → `attach_world`(world·world_pts·world_p0/p1). framing·camera_suggest·placement·checks·reserved·layers·bundle.to_direction 은 월드 좌표와 View 만.
- 비트 동일 주의점: frame_points 후보 중심은 앵커로 적었다 다시 읽은 값으로 시험한다(`stage.to_world(**stage.from_world(c))`). 이것을 빼면 `w_before_context` 가 2숏에서 달라졌다(격자 끝점이 안전 영역 경계에 정확히 걸림) — 넣은 뒤 camera_suggest JSON hormuz·랫클리프 모두 이전과 **완전 동일**, hormuz 는 Phase 7 artifacts 의 shots 와도 동일.
- `tests/anti_inertia/test_stage_isolation`: engine/ 에서 ym·ymv·lat_of·to_uv(이름·import·정의), 옛 View API(.xy·.uvs·.u0·.v1), lon·lat 산술, tan·radians 0. 허용 = engine/stage.py. geo/·tools/fetch_data 는 엔진 밖 Mercator 자산 도구라 대상 밖. 검사기 자체 검출 테스트 포함.
- 회귀(수정 전 자산): hormuz 25컷 md5 25/25, 랫클리프 20컷 20/20, 1080p res_compare 평균 0.01067·최대 0.01808(Phase 10 과 같음, 리팩터 전 측정 — 리팩터 후 값은 작업 6 에서 새 자산으로 다시 잰다).
- pytest(리팩터 후, 수정 전): 810 passed + 1 수정(`test_no_magic_numbers` 허용 4) → 전부 통과.

## 다음
작업 4(direction `stage`·`shots[].stage` — D-0077 쟁점 1), 5(stage_continuity), 6~9. R-0092 답을 받으면 §2-4.
