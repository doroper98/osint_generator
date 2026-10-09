<!--
tier: 3
last_synced_with: v5.7.0
ssot_for: [phaseS1-run-log]
depends_on: [back_and_forth/261009_225012_D0142_fable_s0-review-pass-s1-missile-2d-kickoff.md, rules/video_rules.yaml, sketch/missile/, projects/d1_missile_sketch/sketch.yaml]
last_review: 2026-10-09
-->

# Phase S1 실행 기록 — 미사일 2D 이식 (v5.7.0)

지침 D-0140 §5 S1 + D-0142 보강 8항목.

## 0. 컨테이너 준비

S0 §0 그대로(같은 컨테이너 이어서). 차이:
- EEZ WFS 원본 다운로드: `curl -o eez_wfs.json "<spec eez.prep.wfs_url>"` — 3.7초, 30,478,619 바이트.
- 글꼴: 기준·새 프레임 모두 `FONTCONFIG_FILE`(S0 §0.2 표준 설정)으로 그렸다.

## 1. 기준 프레임과 비교 (D-0142 §0)

옛 `sketch_d1.py`(삭제 전, 커밋 a5a2535 시점)로 9시각 720p 정지 화면 → `ref/`(PNG 미커밋), `ref_sheet.jpg`.
새 `sketch.missile` 로 같은 9시각을 `--res final` 로 그려 비교 → `compare_sheet.jpg`(좌 옛 / 우 새).

| t(초) | 다른 픽셀 비율 | 최대 채널 차 |
|---|---|---|
| 5.0 | 0.000 % | 0 |
| 8.4 | 0.000 % | 0 |
| 14.0 | 0.000 % | 0 |
| 20.5 | 0.000 % | 0 |
| 27.0 | 0.000 % | 0 |
| 34.0 | 0.000 % | 0 |
| 41.0 | 0.000 % | 0 |
| 48.0 | 0.000 % | 0 |
| 54.0 | 0.000 % | 0 |

9컷 모두 **픽셀 동일**. 예상했던 차이(`hatch` 반복 끝)는 클립 밖이라 화면에 나타나지 않았다.

## 2. prep_eez 대조 (D-0142 §4)

| 비교 | 결과 |
|---|---|
| 오늘 받은 WFS → 옛 `prep_eez.py` → eez.json vs 저장소 eez.json | features 11/11 동일(code·kind·polys·lines·rep·area) |
| 같은 WFS → 새 `python -m sketch.missile.prep_eez … --fetched 2026-10-05` vs 저장소 eez.json | **JSON 객체 전체 동일**(source 문구 포함) |

Marine Regions 원본은 2026-10-05 이후 바뀌지 않았다. 저장소 eez.json 을 그대로 둔다.

## 3. 전편 렌더 (`--res final`)

| 항목 | 값 |
|---|---|
| 명령 | `python -m sketch.missile projects/d1_missile_sketch --res final` |
| 시간 | 4분 22초(렌더 255.5초) |
| mp4 | `out/sketch_2d.mp4` 14,065,244 바이트, md5 `1a5489f8d185ae9fa1b9305cca6f5424`, 1280×720, 24fps, 1344프레임, 56.0초(미커밋) |
| 시트 | `sketch_2d_sheet.jpg`(9컷, 커밋) |
| provenance | `sketch_provenance.json`(커밋) — spec_sha1 `946de132…`, rules_hash `2b19ea81…` |
| 검사 | hard 0, warning 1(SK-C2) |

### SK-C2 경고 471프레임 — 원인(검토본 그대로, 값 바꾸지 않음 D-0140 §7)
1. 같은 자산의 전체 라벨(이름 + 부제)과 이름만 남은 라벨이 교차 페이드하는 동안 같은 자리에 겹친다(의도된 전환).
2. t≈26초 `사드 AN/TPY-2 · 성주`(이름만)와 `AN/TPY-2 · 교가미사키` 라벨 상자 — 검토본 t=27 컷에도 두 라벨이 붙어 보인다.
3. t≥40초 `착탄 추정 영역` 라벨 상자 아래(+20)와 `일본 EEZ 안쪽` 태그 상자 위(−13)가 1px 겹침 — 예약 상자 여백 탓, 글자는 겹치지 않는다.

2번은 사용자 검토 때 함께 보면 좋다(확정 대기 목록 후보).

## 4. 구현 메모

- spec 계약 `sketch/missile/spec.py`(MissileSpec). 스키마 단계 검사: SK-H2(approx → 반경 > 0), SK-H3(비공개 레이더 tag, 이동 자산 tag·범위 없음), SK-H4(중첩 청구국 색 ≥ 2). 스키마 위반은 메시지의 SK 번호로 보고(SK 번호 없는 형식 오류 = SK-SPEC).
- 화면 숫자 = `sketch/missile/numbers.py` 포맷터 하나(자리표시 `{기관.값}`·`{track.distance_km}`·`{sensor.range_km}`·`{profile.ref_km}`). 자유 문구(출처 줄·엔딩) 안 단위 숫자는 허용 값 집합과 대조. `분` 은 시각(오전 10시 15분)과 겹쳐 자유 문구 대조에서 뺐다(규칙 `numbers.units.min.check: false`).
- 발표값 `mod.flight_min: 69`(약 69분)를 announced 에 두었다 — 옛 화면의 "(약 69분)" 문자열.
- 도해 이미지가 없으면 옛 코드는 "도해 이미지 받는 중" 대체 문구를 그렸다. 새 코드는 오류(P6) — SK-R1 이 파일을 먼저 확인한다.
- SK-H5 판정 창 = approx 층의 **라벨 설명 구간**(등장 + `eez.claim_label_delay` ~ end). NLL 선 자체는 흐리게 끝까지 남지만, 설명 구간에 '개략' 출처 줄이 있고 엔딩 자료에도 '개략'이 있으면 통과.
- `globe3d.py` 는 S2 까지 보존(D-0142 §6). `sketch_d1` 을 import 하므로 S1 뒤에는 단독 실행되지 않는다 — 옛 3D 기준이 필요하면 4d9dc65 트리에서 돌린다.

## 5. 테스트

`FONTCONFIG_FILE` 표준 설정, S0 §0.2 자산 그대로:

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S0 끝(8690ab8) | 1330 | 0 | 0 | 0 |
| S1 끝 | **1349** | **0** | **0** | 0 |

- 새 테스트 19개(요구 ≥ 14): `tests/test_sketch_missile.py` — 검토본 양성 1, SK-H1 3(포맷터·계산 거리 음성·렌더 표 밖), H2 2, H3 2, H4 2(스키마·hatch 가드+렌더 기록), H5 2, C2 2, R1 2, prep_eez 분할 1, CLI 종료 코드 1, 프레임 렌더 provenance 1(자산 없으면 사유 있는 skip — 이 환경 skip 0).
- P2 삭제: `sketch_d1.py`·`prep_eez.py`(테스트 없음, 삭제 테스트 0). 기준 = 1330 − 0 + 19 = 1349.
- 골든·엔진 무변경(`test_hormuz_preview_provenance` 통과).
