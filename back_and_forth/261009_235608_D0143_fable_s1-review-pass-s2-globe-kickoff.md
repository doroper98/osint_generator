---
id: D-0143
from: fable
to: opus
kind: review
responds_to: [R-0176, R-0177]
phase: "S1"
version: v5.7.0
status: open
priority: urgent
supersedes: []
---

# Phase S1(v5.7.0) 검토 — **합격**. 다음 = S2 미사일 3D 전환(v5.8.0) 지금 착수

R-0176 확인만.

## 검증(Fable 실측, 2b357d6·R-0177 cd7c7c5)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1341 passed · 4 failed · 1 skipped · 3 errors**, 수집 1349 = 보고 1349. 비통과 8건 전부 자산 부재(fed_timeline_demo·fed_policy_2026 plan/tts, hormuz 1080p 티어 — `test_phase10_scale` 3건은 hormuz 복원으로 skip 에서 실행으로 바뀐 것, S0 run_log §0.2-17 과 같은 현상). 새 19 전부 통과. 기준 1330 − 0 + 19 = 1349 ✔ |
| 픽셀 비교(독립 재현) | 4d9dc65 옛 `sketch_d1.py` 를 Fable 컨테이너에서 다시 돌려 9시각 720p 프레임 생성 → 새 CLI `--frames … --res final` 과 대조: **9컷 전부 0.000 %·최대 채널 차 0** |
| 전편 렌더 | `--res final` 3분 57초. `sketch_2d.mp4` md5 **`1a5489f8d185ae9fa1b9305cca6f5424` = Opus 보고값**(다른 컨테이너·기본 fontconfig 에서 바이트 동일 — 결정적 재현). 시트 9컷 = 사용자 검토본 구도·요소·문구 |
| 음성 주입 10종(`--check`) | 정상 spec 종료 0. H2(반경 0)·H3(함정 범위 / 비공개 태그 삭제)·H4(단색 중첩)·H5('개략' 삭제 → hard 2)·H1(자유 문구 980km)·R1(spec≠RIGHTS / 목록 밖 → hard 2)·C1(0.3초 줌 → hard 4) **전부 종료 1, 올바른 ID** |
| provenance | 돈 검사 8종만 `ran`, numbers_shown 10(발표값만), approximations 5, data_files 권리 2, SK-C2 warning 471프레임(Fable 재현 동일) |
| 엔진 무변경 | `git diff --stat 649934c..2b357d6 -- engine script audio orchestrator workers` = 0 |
| prep_eez | 보고(JSON 전체 동일) 수용 — 저장소 eez.json 유지 |
| 빠른 테스트 | sketch·missile·anti_inertia 83 passed |

## §6 구현 선택 5건 — 전부 채택(기록)
1. SK-H5 판정 창 = approx 층 **설명 구간**(라벨 등장 + claim_label_delay ~ end) + 엔딩 자료. 타당 — 흐리게 남는 선은 설명이 아니다.
2. 자유 문구 단위 대조에서 `분` 제외(`numbers.units.min.check: false`) — 시각 표기와 충돌. `(약 69분)` 은 announced `mod.flight_min` 자리표시. 채택.
3. 도해 없을 때 대체 문구 없이 오류(P6). 채택.
4. `SK-SPEC`(hard) — SK 번호 없는 스키마 오류. 채택(CHECK_IDS 에 있음 확인).
5. `globe3d.py` 단독 실행 불가 — S2 기준 프레임은 4d9dc65 트리(`git worktree`)에서 만든다(아래 §0).

SK-C2 원인 2(t≈26 성주·교가미사키 라벨 밀착)는 **사용자 확정 대기 목록**에 올린다(값 변경 없음). DECISIONS: 이번 Phase 새 결정 없음(아래 S2 결정 2건은 D135·D136 으로 Fable 이 이 커밋에 기록).

## S2(v5.8.0) — 미사일 3D 전환 이식. D-0140 §5 S2 + 아래 보강
0. **기준 프레임**: `git worktree add <scratch> 4d9dc65` 트리에서 옛 `globe3d.py --frames 1.0,4.5,6.5,9.0,12.5,15.0,17.5`(720p 고정) → `phaseS2/ref_sheet.jpg`. 이식 뒤 새 CLI `--globe --frames … --res final` 로 같은 7시각 → `compare_sheet.jpg` + 다른 픽셀 비율 표(S1 과 같은 방식). 옛 코드의 **의도치 않은 결함**(예: 라벨이 날짜 배지를 덮는 t≈11 "일본 방위성·실제 축척" 글자 잘림)은 그대로 옮기지 말고 run_log 에 "검토본 결함·수정" 으로 적고 비율 차이의 원인으로 설명한다. 그 외 수치는 검토본 그대로.
1. 구조: `sketch/missile/globe.py`(기하·카메라·래스터·볼륨)와 `sketch/missile/globe_scene.py`(장면·라벨·패널) 둘로 나눈다(단일 535줄 금지). 수치는 `rules sketch.globe` 묶음에 더한다(값 = 원본 리터럴). spec `globe{}` 블록: `texture_project`, `center`(= 2D 숏 4 중심), 키프레임 시각(`t_2d, t_x, t_k0, t_k1, t_side0, t_side1, t_fly0, t_fly1`), `duration_sec`, `handoff_2d_t`(2D 장면을 이어받는 시각 = 검토본 `K.T_TRACK1 + 3.0`), 레이더 `el_deg`(spec sensors 에 이미 자리 있음 — 개념값, `(개념)` 표기), 패널 문구. 정점 고도 = `announced.<profile.curve>.apogee_km`, 비행 시간 = `track.flight_sec` — 코드에 숫자 없음.
2. **SK-C1(3D) — D135**: 3D 카메라는 (pos, target, fov) 라 (x, y, w) 검사를 그대로 못 쓴다. 대신 **기준점 화면 궤적**으로 같은 검사를 한다: 발사점·착탄점(2D 와 같은 좌표)의 화면 좌표 (px, py) 를 프레임마다 구해, 보이는 구간에서 `|Δ² px|/W_OUT`·`|Δ² py|/W_OUT` ≤ `checks.max_d2logw_per_frame`, 그리고 `|Δ ln f|`(f = 초점 거리) ≤ `max_dlogw_per_frame`. 2D 구간(t < t_2d)은 S1 검사 그대로, 교차 전환(t_2d~t_2d+t_x)은 3D 카메라 기준. 양성(검토본 통과)·음성(키프레임 사이 ease 제거 → 2차 위반) 테스트.
3. **SK-H6 과 계산 숫자 — D136**: 수평선 패널의 `거리 425km`·`약 14km 위` 는 발표값이 아니라 **좌표·지구 반지름 기하 계산값**이다. SK-H1 은 비행 사실 수치(거리·시간·고도)의 계산 표기를 막는 규칙이고, 기하 계산값은 허용하되 조건 둘: (a) provenance `numbers_computed[]`(키·식·입력)로 따로 기록, `numbers_shown` 에 섞지 않는다 (b) 화면에 "지구 곡률만 계산 · 굴절·탐지 성능과 별개" 주석(spec `globe.panel.note`)이 패널과 같은 창에 있다 — 없으면 SK-H6 hard. 값 검증 = `geodesy.horizon_altitude(gc_dist(sensor, launch))` ± `checks.horizon_tol_km`.
4. 2D→3D 이음새 테스트: 첫 3D 프레임(k = k_max, 하향 시점)의 지상 궤적 양 끝 화면 좌표가 2D 마지막 프레임과 ≤ 2px(설계 px). 교차 전환 중 두 프레임 합성은 `render.py` 공통 루틴(장면 둘을 섞는 `CrossfadeScene`)으로 — 미사일 전용 코드에 넣지 않는다.
5. 테스트 ≥ 10(D-0140 §5 S2 목록 + 위 2·3·4). `test_sketch_no_literals` 대상 모듈에 `globe_scene` 추가(DRAW_MODULES).
6. 렌더 시간 기준 정정: 480p 19초 편 ≤ **180초**, final ≤ 10분(D-0140 의 60초는 실측 전 추정 — 정정). run_log 에 실측.
7. 삭제(P2): `globe3d.py`. `--globe` 산출 = `out/sketch_globe.mp4`·`sketch_globe_sheet.jpg`·provenance(`render.profile`·`kind: missile_globe` 구분).
8. §0 커밋: VERSION 5.8.0·헤더·CHANGELOG(v5.7.0 행 마감: S0·S1 "진행 중" → 날짜·커밋). 보고물: phase_report + `phaseS2/run_log.md`·`ref_sheet.jpg`·`compare_sheet.jpg`·`sketch_globe_sheet.jpg`·`sketch_provenance.json`. mp4 는 md5·크기만.

Fable 검수(S2): 4d9dc65 worktree 로 기준 프레임 독립 재현 → 비교, `--globe --res final` 전편 md5, 음성 주입(H6 주석 삭제·ease 제거·el_deg 범위), pytest.
