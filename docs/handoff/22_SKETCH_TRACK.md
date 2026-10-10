<!--
tier: 2
last_synced_with: v5.10.0
ssot_for: [sketch-track, sketch-conventions, sketch-spec-contract, sketch-checks, sketch-pending-user, sketch-registration-candidates]
depends_on: [back_and_forth/261009_210629_D0140_fable_sketch-skills-track-s0-s4-kickoff.md, docs/handoff/DECISIONS.md, rules/video_rules.yaml, sketch/, .claude/skills/missile-event-map/SKILL.md, .claude/skills/campaign-front-map/SKILL.md]
last_review: 2026-10-10
-->

# 22. 화면 스케치 트랙 — 미사일 사건도 · 전황 작전도

화면 스케치는 사용자 검토용 짧은 화면입니다. 자막·내레이션이 없고, 본편 엔진에 등록하지 않습니다(D128).
이 문서는 스케치의 계약·검사·출처·권리·재현·미결 항목의 정본입니다. 옛 `projects/d1_missile_sketch/CONVENTIONS.md` 의 내용도 여기로 옮겼습니다(§2.3~§2.5).
에이전트 절차서는 `.claude/skills/missile-event-map/SKILL.md`·`.claude/skills/campaign-front-map/SKILL.md` 입니다. 화면 수치의 정본은 `rules/video_rules.yaml sketch:` 하나입니다(D130). 이 문서는 수치를 **규칙 키 이름으로만** 인용합니다(C0).

## 1. 계층 결정

근거 전문은 `docs/handoff/DECISIONS.md` 의 해당 행입니다.

| ID | 결정 |
|---|---|
| D128 | 스케치는 엔진 레지스트리 밖 독립 패키지 `sketch/`(spec YAML 주도 + CLI). 본편 요소 아님 |
| D129 | 트랙 작업·교신 브랜치 = `claude/bold-mccarthy-ttmagk` |
| D130 | 화면 수치 SSOT = `rules sketch:`(`SketchRules`, extra=forbid). 사실·연출 값 = `projects/<pid>/sketch.yaml`. 코드 리터럴 금지(`tests/anti_inertia/test_sketch_no_literals.py`) |
| D131 | 스킬 = `.claude/skills/<name>/SKILL.md`. CLI 를 부르는 절차서, 코드 없음 |
| D132 | SK-C1 = 1차 + 2차 차분(`checks.max_dlogw_per_frame`·`checks.max_d2logw_per_frame`), 숏 경계 예외 없음 |
| D133 | SK-R1 허용 라이선스 = `rights.allowed_licenses`. 목록 밖·항목 없음 = hard |
| D134 | 커밋 트레일러 허용, 모델 식별자 금지는 코드·문서·산출물에 적용 |
| D135 | 3D 구간 SK-C1 = 기준점 화면 궤적 2차 차분 + 초점 거리 Δ ln f |
| D136 | 비행 사실 수치 = 발표값만(SK-H1). 기하 계산값(수평선 패널)은 허용 + provenance `numbers_computed` |
| D137 | 2D→3D 이음새 = 검토본 기하 유지, 회귀 임계 `checks.seam_px` |
| D138 | 전황 강 색 = `campaign.river.rgb`(검토본 RGB 그대로) |
| D139 | 참고 작전도 SVG = 데이터 파일. spec `fronts.reference{file, rights}`, SK-R1 = 프로젝트 `RIGHTS.json` |
| D140 | SK-G2 미세 자기 교차 조각 비율 ≤ `checks.pocket_sliver_ratio` → 통과 + warning, 초과 hard. 그리기는 레시피 그대로 |
| D141 | 전황 도시 검산 ≤ `checks.georef_city_deg`, spec `fronts.city_check` 도시 전부 |
| D142 | hormuz 엔딩 컷 도장 가림 상자 = `v99.99.99` 폭(PIPELINE-AP-021) |
| D143 | 정점·비행 시간·착탄 기준점 중 하나라도 두 기관 모두 미발표면 미사일 스킬 범위 밖 — 사용자에게 표로 보고, 개념값으로 채우지 않음 |
| D144 | SK-H1 시계 원천: `track.flight_sec` = announced sec(없으면 min × 60), provenance 시계 + 원천 키 |
| D145 | SK-E1 엔딩 자료 상자 검사(hard, 미사일·전황 공통), `profile.apex_label` 포맷터 경유, §7 후보 3행 |
| D150 | 사용자 확정: 독도 표현·NLL 빗금·레이더 값 + 추정값 주석·착탄 반경·3D 볼륨·라벨 그대로, 화살표 부드럽게, 3D 탄도 궤적 = 본편 등록(트랙 G) |

## 2. spec 계약

spec 파일은 `projects/<pid>/sketch.yaml` 하나입니다. Pydantic v2, extra=forbid, `schema_version: 1` 입니다.
산출은 `projects/<pid>/out/`(미추적)입니다. 검사 ID 는 §3 을 보십시오.

### 2.1 공통(`sketch/common/spec.py SketchSpec`)

| 필드 | 필수 | 내용 | 검사 |
|---|---|---|---|
| `schema_version` | 필수 | 1 | SK-SPEC |
| `kind` | 필수 | `missile` / `campaign` | SK-SPEC |
| `title`·`date` | 필수 | 제목, 화면 모서리 날짜(모서리 유일 요소, C0) | SK-H1 |
| `duration_sec` | 필수 | 영상 길이(초) | — |
| `sources[]` | 필수 ≥ 1 | 엔딩 자료 줄 `{text, url?}` | SK-H1·H5 |
| `shots[]` | 필수 ≥ 1 | `{t0, t1, lon, lat, w}` — 숏 사이 이동은 앞 숏 끝 상태에서 시작 | SK-C1 |
| `media[]` | 선택 | `{file, credit, license, caption, t0, t1}` — 파일은 `media/`, 권리는 `media/RIGHTS.json` | SK-R1 |
| `sheet_times[]` | 필수 ≥ 1 | 컨택트 시트 시각 | SK-SPEC |

### 2.2 미사일(`sketch/missile/spec.py MissileSpec`)

| 필드 | 필수 | 내용 | 검사 |
|---|---|---|---|
| `launch` | 필수 | 발표 표현 그대로의 발사 지점·시각·색 | SK-H1 |
| `track` | 필수 | 기준점 `ref`·방위·발표 거리·`approx`·`uncertainty_km`·발표 비행 시간·`hud`·`impact` | SK-H1·H2 |
| `announced{기관}` | 필수 ≥ 1 | `{who, color, values{키: Num}, rows[]}` — 화면 숫자 원천. 두 기관은 나란히 같은 무게 | SK-H1 |
| `sensors[]` | 선택 | `radar` / `ship`, `location_public`, `range_km`·`az_width_deg`, `tag`, 3D `el_deg`·`short`·`globe_name`·`globe_label` | SK-H3 |
| `eez` | 필수 | `file`(eez.json)·`nations`·`regions`(overlap/joint)·`claim_lines`·`places`·`pulse`·`prep` | SK-H4·H5 |
| `card` | **선택** | 도해 카드 `{media, title, sub, t0, t1, crop, rotate_deg}` — `media[]` 에 같은 파일 필요. 권리가 분명한 도해가 없으면 `card`·`media` 를 빼도 검사·렌더 통과 | SK-R1 |
| `profile` | 선택(`globe` 있으면 필수) | 고도 단면 — `curve` = 정점·거리를 가져올 `announced` 기관 키 | SK-H1 |
| `dim` | 필수 | 장면별 초점(층 밝기 키) | — |
| `notes` | 필수 | `source_lines[]{t0, t1, text}`·`end_title`·`end_note`·`end_sec` | SK-H5 |
| `globe` | 선택 | 3D 전환편 — `texture_project`·`center`(= 마지막 숏 중심)·키프레임·`labels`·`panel`·`hud_notes` | SK-C1(3D)·H6 |

화면 숫자는 자리표시만 씁니다. `{기관.키}`·`{track.distance_km}`·`{sensor.range_km}`·`{profile.ref_km}`·`{const.earth_radius_km}` 를 `sketch/missile/numbers.py` 포맷터가 채웁니다.

### 2.3 미사일 사실 표기 규약(옛 CONVENTIONS §2)

| 항목 | 규약 |
|---|---|
| 발사 지점 | 발표 표현 그대로("평양 순안 일대"). 발사 기호(삼각형)와 시각 |
| 착탄 지점 | 점이 아니라 **불확실성 영역**(발표가 "약 ○km" 면 반경 원, SK-H2). 발표 기준점까지 거리선을 함께 |
| 비행 거리 | **발표값만** 화면에(SK-H1). 근사 좌표로 계산한 거리를 보이지 않는다(980km 대 발표 1,000km 사고) |
| 두 기관 수치 | 합참·일본 방위성을 **나란히 같은 무게**로(고도 단면 패널) |
| 궤적 | 2D 지도에는 지상 투영(대원)만. 고도는 단면 패널 또는 3D. 곡선 모양은 "개념", 정점 고도는 발표값 |
| 미사일 이미지 | 권리가 분명한 도해 우선. 방송 화면 캡처는 라이선스가 의심되면 쓰지 않음. 없으면 카드 생략 |

### 2.4 탐지 자산 규약(옛 CONVENTIONS §3)

| 경우 | 표현 |
|---|---|
| 위치 공개(성주·샤리키·교가미사키) | 기준점 + 부채꼴 테두리 선명. 거리 = 공개 사양 |
| 위치 비공개(그린파인) | **기준점을 찍지 않음**. 여러 겹 흐림 + `tag`("위치 비공개 · 범위는 개념도") 필수(SK-H3) |
| 이동 자산(이지스함) | `kind: ship`, `tag`("함정 위치는 예시 · 탐지 거리 비공개") 필수, `range_km: null`(SK-H3) |
| 3D 방위·고각 | 공개 정밀 사양 없음 → 라벨에 "(개념)" |
| 가시 판정 | "탐지 시각" 은 쓰지 않는다(지어낸 정밀도). **레이더 수평선 최소 고도** = R(1/cos(d/R) − 1) 만(SK-H6, D136) |

### 2.5 해양 경계 규약(옛 CONVENTIONS §4)

| 경우 | 표현 |
|---|---|
| 확정·단독 EEZ | 나라 색 옅은 채움 + **바다 쪽 경계만** 점선 |
| 중첩 주장(독도·쿠릴 등) | **청구국 두 색이 번갈아 드는 사선**(SK-H4) — 한쪽 색으로 칠하지 않는다 |
| 공동 관리(한일 공동개발구역) | 합의 색 점무늬(`kind: joint`) |
| 서해 남북 | Marine Regions 남북 계산선은 **쓰지 않는다**. NLL(금색 실선)과 북한 1999 해상군사분계선(붉은 점선) 사이를 남북 두 색 빗금. 북한선 3점 이후는 "방향 미발표" 점선·태그 |
| approx 층 | NLL 처럼 개략 재구성한 층은 `approx: true` → 설명되는 동안 출처 줄과 엔딩 자료에 `checks.approx_word`(SK-H5) |
| 동해 남북 | 아직 계산선 그대로 — §7 과제 |

### 2.6 카메라 규약(옛 CONVENTIONS §5)

- 숏 전환 이동은 **앞 숏이 끝난 상태(푸시인 포함)에서 시작**합니다. 원래 값에서 다시 시작하면 첫 프레임 줌이 튑니다(멈칫 사고, SK-C1 2차 차분이 잡음).
- 큰 줌(4배 안팎) 이동은 `camera.move_min_sec` 이상 둡니다(SK-C1 이 너무 빠른 이동을 잡음).
- 2D → 3D: 접점 기준 반지름 kR 구로 k 를 줄여 평면을 지구본으로 휩니다. 궤적은 실제 축척입니다.

### 2.7 전황(`sketch/campaign/spec.py CampaignSpec`)

| 필드 | 필수 | 내용 | 검사 |
|---|---|---|---|
| `nations{코드}` | 필수 | `{color, label, light_name}` | — |
| `units[]` | 선택 | `{nation, echelon, arm, name, lon, lat, t, fade[]}` — echelon ∈ XXXX/XXX/XX, arm ∈ inf/arm/cav | SK-G3 |
| `fronts` | 필수 | `file`(fronts.json)·`reference{file, rights}`·`source`·`style_map[]`·`graticule`·`layers[]`·`city_check[]` | SK-G1·R1·SPEC |
| `pockets[]` | 선택 | `{name, build[], show}` — 레시피 단계 = `piece`("층:편:번호") 또는 `points`, `lon_min`·`lon_min_of`·`start_near`·`reverse` | SK-G2 |
| `arrows` | 선택 | `{color, dim, label_end, items[]}` | — |
| `places_t`·`places[]` | 선택 | 당시 지명 `{name, now?, lon, lat}` | SK-G1(도시 검산) |
| `rivers_label[]` | 선택 | 강 이름 | — |
| `dates[]` | 필수 | 날짜 배지 `{t, text}` | — |
| `tags[]`·`pincer`·`legend` | 선택 | 국면 태그·집게·범례 | SK-H1·C2 |
| `notes` | 필수 | `source_lines[]`(전 구간 '개략')·`end_*` | SK-H5 |

전황 규약입니다.
- 현대 국경·행정구역선·현대 지명은 그리지 않습니다(`geo.yaml admin1: []`, 지명은 spec `places` 의 당시 이름).
- 전선·부대 위치는 전부 개략입니다. 화면이 열린 뒤부터 엔딩 직전까지 '개략' 출처 줄이 이어져야 합니다(SK-H5).
- 병력 등 수치는 화면 문구에 쓰지 않고 엔딩 자료에 범위로만 둡니다(SK-H1).

## 3. 검사표

`--check` 는 렌더 없이 spec 단계까지 돌립니다. 종료 코드 1 = hard 위반이고, hard 위반이면 렌더하지 않습니다(P6). 등급의 정본은 `sketch/common/checks.py CHECK_IDS` 입니다.

| ID | 판정 | 등급 | 규칙 키 | 종류 |
|---|---|---|---|---|
| SK-H1 | 화면 숫자는 포맷터만. 자유 문구 단위 숫자가 발표값 표 밖이면 위반(전황 = 단위 숫자 전부 금지). 미사일 시계 `track.flight_sec` = announced sec 값(없으면 min × 60, D-0149) — 발표값의 진위는 출처 책임(사람) | hard | `numbers.units`(check) | 둘 다 |
| SK-H2 | `track.approx` → `uncertainty_km` > 0, 착탄 영역을 그림 | hard | — | 미사일 |
| SK-H3 | 비공개 레이더 tag·이동 자산 tag·범위 없음, 기준점은 위치 공개 자산만 | hard | — | 미사일 |
| SK-H4 | 중첩 수역 청구국 색 ≥ 2 | hard | — | 미사일 |
| SK-H5 | approx 층이 보이는 동안 '개략' 출처 줄, 엔딩 자료에 '개략' | hard | `checks.approx_word`·`checks.approx_note_end_gap_sec` | 둘 다 |
| SK-H6 | 수평선 패널 주석 필수 + 패널 값 = 기하 계산 ± 허용 폭 | hard | `checks.horizon_tol_km` | 미사일 3D |
| SK-C1 | 카메라 연속(1차·2차 차분, 3D 는 기준점 궤적·Δ ln f) | hard | `checks.max_dlogw_per_frame`·`checks.max_d2logw_per_frame` | 둘 다 |
| SK-C2 | 라벨 예약 상자 겹침 | warning | `checks.label_overlap_px` | 둘 다 |
| SK-R1 | 미디어·참고 데이터 권리 기록 + 허용 라이선스 | hard | `rights.allowed_licenses` | 둘 다 |
| SK-G1 | 참고 작전도 정합 잔차 + 도시 검산 | hard | `checks.georef_residual_deg`·`checks.georef_city_deg` | 전황 |
| SK-G2 | 포위망 다각형 유효(미세 조각은 warning) | hard / warning | `checks.pocket_sliver_ratio` | 전황 |
| SK-G3 | 제대·병종 값 | hard | — | 전황 |
| SK-E1 | 엔딩 자료 줄 수: `y0` + 줄 수·`dy` 가 맺음 줄(end_note) 기준선을 넘으면 겹침. 줄 폭 > 화면 폭 − 2·`x` 면 넘침 | hard | `text.end_line`·`text.end_note`(전황 `campaign.end`) | 둘 다 |
| SK-SPEC | 그 밖 스키마·참조 오류 | hard | — | 둘 다 |

2D→3D 이음새는 검사가 아니라 회귀 테스트입니다(`checks.seam_px`, D137).

## 4. 데이터 출처 · 권리

| 자료 | 출처 | 라이선스 | 기록 위치 |
|---|---|---|---|
| EEZ 경계 | Marine Regions(VLIZ) WFS — spec `eez.prep.wfs_url` | CC BY 4.0 | spec `eez.prep.license`, provenance `data_files` |
| 미사일 도해 | Wikimedia Commons(`tools/commons_fetch.py` — UA·요청 간격 `config.yaml commons`) | `rights.allowed_licenses` 안 | `projects/<pid>/media/RIGHTS.json` |
| 참고 작전도 | Wikimedia Commons SVG(경위도 눈금이 있는 것) | 같음 | `projects/<pid>/RIGHTS.json`(D139) |
| 발사 사실 | 합참·일본 방위성 발표(보도 인용 시 매체·날짜) | 사실 — 인용 출처 표기 | spec `sources[]` |
| 레이더 사양 | 공개 사양·보도(GlobalSecurity, CSIS Missile Threat 등) | 같음 | spec `sources[]` + "사용자 확정 대기" 주석 |
| 지형 | 엔진 `geo.prep`(Natural Earth 등, `data/geo`) | 엔진 규칙 | 엔진 |

`RIGHTS.json` 형식입니다.

```json
{"schema_version": 1,
 "files": {"<파일 이름>": {"source_url": "…", "author": "…", "license": "CC BY-SA 4.0",
                           "rights_status": "cleared_with_attribution", "fetched": "YYYY-MM-DD", "use": "…"}},
 "references_not_stored": {"<대조만 한 자료>": {"source_url": "…", "author": "…", "license": "…", "use": "…"}}}
```

보도 출처 형식: `"<항목>: <기관> YYYY.MM.DD 발표(<매체> 보도)"`. 서로 다른 기관 값은 한 줄에 나란히 씁니다.

## 5. 재현 명령

글꼴은 `fonts-noto-cjk` 와 `python tools/fetch_data.py fonts` 로 준비합니다. 지형 원자료는 `data/geo` 입니다.

```bash
# 미사일 2022.11.18 화성-17형
python -m geo.prep projects/d1_missile_sketch && python -m geo.prep projects/d1_missile_sketch --res 720p
python -m geo.prep projects/d1_missile_sketch/globe_tex
curl -o /tmp/eez.json "<spec eez.prep.wfs_url>"            # eez.json 을 다시 만들 때만
python -m sketch.missile.prep_eez /tmp/eez.json projects/d1_missile_sketch
python -m sketch.missile projects/d1_missile_sketch --check
python -m sketch.missile projects/d1_missile_sketch --res final
python -m sketch.missile projects/d1_missile_sketch --globe --res final

# 전황 1942.11 천왕성 작전
python -m geo.prep projects/uranus_sketch && python -m geo.prep projects/uranus_sketch --res 720p
python -m sketch.campaign.prep_georef projects/uranus_sketch    # fronts.json(이미 커밋됨 — 다시 만들 때만)
python -m sketch.campaign projects/uranus_sketch --check
python -m sketch.campaign projects/uranus_sketch --res final
```

검토본 대조 기록은 `docs/handoff/reports/phaseS1~S4/run_log.md` 에 있습니다.

## 6. 사용자 확정 목록(사용자 결정 D150, 2026-10-10)

확정 주체는 **사용자**입니다. 확정된 항목은 spec 주석을 "사용자 확정(D150)" 으로 둡니다. 남은 대기 항목만 "사용자 확정 대기" 주석을 씁니다.

| 항목 | 값(spec) | 확정 | 나온 곳 |
|---|---|---|---|
| 독도 문구 | "독도 주변 수역 · 일본이 영유권 주장 · 대한민국 실효 지배" | **확정** — "독도" 로 표현(다른 명칭 금지) | S1 |
| NLL 표현 | 개략선 + NLL ~ 북한 1999 선 사이 남북 두 색 빗금 | **확정**(빗금 문법). 공식 좌표 교체는 본편 전 과제(§7), 그때까지 "개략" 표기 유지 | S1 |
| 레이더 사양 값 | 사드 종말 모드 약 600km, 그린파인 블록-C 약 800km, 전진배치 1,000km | **확정** — 값 유지 + 화면 하단 주석 "탐지 거리 표현은 공개 자료를 토대로 한 추정값" | S1 |
| 착탄 반경 | `track.uncertainty_km` 25 | **확정** | S1 |
| 3D 레이더 방위·고각 | 방위 폭 120°, 고각 0~60° | **확정** — 볼륨으로 보이게(현재 렌더 유지) | S2 |
| 성주·교가미사키 라벨 밀착 | 2D t ≈ 26 | **확정** — 그대로 | S2 |
| 2D→3D 궤적선 이중 겹침 | 교차 전환 중 ≈ 12px | 본편 등록(트랙 G)에서 투영 혼합으로 해결 | S2 |
| 전황 진격 화살표 | 성장 애니메이션 | **해결(S5)** — 호 길이 보간으로 프레임마다 이어 자람 | S5 |
| 포위망 미세 조각 | (44.669, 48.918) 레시피 맞물림 | 대기(D140 warning, 본편 등록 때 레시피 다듬기) | S3 |
| 집게 예약 상자 | 태그가 사라진 뒤에도 예약(SK-C2 warning) | 그대로(원본 동작). 집게 = 남북 두 갈래 진격이 만나는 순간을 찍는 점·태그(D-0154 §4) | S3 |

## 7. 남은 과제 = 본편 등록 후보

스케치는 본편이 아닙니다. 본편 요소로 등록하려면 엔진 레지스트리(`rules registries`)·스키마·렌더러·프리뷰 예제를 동시에 고쳐야 합니다(C7, P10).

| 후보 | 등록 시 필요한 설계 결정 |
|---|---|
| 이벤트 `arc`(탄도 궤적·고도 단면) | 원고 문장 앵커와 비행 진행률의 연결 방식, 두 기관 값 표기 위치 |
| 이벤트 `occupied`(EEZ·중첩·공동 수역 채움) | 사선·점무늬 문법을 엔진 채움 규칙에 넣을지, 나라 색 토큰 |
| 이벤트 `arrow`(전황 진격 화살표) | 성장 타이밍을 문장 앵커에 묶는 법, 라벨 위치 규칙 |
| 무대 `globe`(3D 지구본) | 엔진 무대 레지스트리 편입, 텍스처 준비를 `geo.prep` 표준 산출로 |
| 접점 kR 투영 혼합 | 메르카토르 ↔ 방위 등거리 혼합식 — 이음새(D137) 근본 해결 |
| 포위망 레시피 다듬기 | 도시 점과 북쪽 전선 맞물림 처리(미세 조각 0), 레시피 문법 고정 |
| 집게 예약 상자 | 예약을 태그 알파에 맞출지 — 지명 배치 변화 수용 여부 |
| 2D→3D 이음새 | 위 투영 혼합과 같은 결정 |
| 근접 숏 추가 | 실제 축척 옆 시점에서 레이더 볼륨이 작아 보임 — 근접 숏 카메라 규칙 |
| 동해 남북 경계 | 서해와 같은 두 주장선 방식으로 정리할지 |
| NLL 공식 좌표 | 개략 재구성을 국방부 자료·해도 좌표로 바꿀 때 출처·권리와 서해 빗금 재계산(D150 #2 — 표현은 확정, 좌표만 본편 전) |
| `launch` 라벨 위치 필드(`label_at`/`side`) | 발사 라벨이 배경 도시 이름("평양직할시")과 겹칠 때 옮길 수단 — 라벨만 옮기고 기호는 좌표에 둘지, 배경 도시 라벨을 숨길지(콜드 테스트 2·3회차·Fable 회차 공통) |
| SK-C2 메시지에 겹친 두 상자 이름 | 예약 상자에 주인(라벨 종류·이름)을 달아 warning 이 "무엇과 무엇" 을 말하게 할지 — 상자 자료형 변경(D-0150 발견 2) |
| 3D `{sensor.range_plain}` '약' 없음 | 3D 라벨이 2D 의 '약 ○km' 와 달리 '약' 을 뺀 검토본 표기 — 통일할지(검토본 값 변경이라 사용자 확인) |
| 미발표 수치 사건 표현(시계 없는 HUD · 방향만 있는 궤적 · '착탄 위치 미발표' 영역 · 고도 단면/3D 생략) | 어느 요소를 빼고 무엇을 남길지는 사용자 검토 전 새 화면 문법(D-0149, 사례 2023-04-13 화성-18형 — `reports/phaseS4/cold_r1/`) |
