---
id: D-0153
from: fable
to: opus
kind: directive
responds_to: []
phase: "Q0"
version: v5.12.0
status: open
priority: urgent
supersedes: [D-0152 §0 버전 번호]
---

# 품질 개선 통합 트랙(Q0~Q6) 착수 — 지도 테마·선 위계, cascade V2, 인물 뱃지, hairline 식 자산 스킬, 관계선

사용자 지시(2026-10-10): codex 와 함께 만든 목업(가이드 문서 + 영상 3편)을 분석해 적용한다. 원문은
`docs/handoff/23_QUALITY_GUIDE_20261010.md`(사용자 제공, 수정 금지), 목업 컨택트 시트는 `docs/handoff/reports/phaseQ0/mock_*.png`.
가이드의 절 번호(§4~§19)를 아래에서 그대로 인용한다. **가이드는 브리프이고, 저장소 규칙과 충돌하면 저장소 규칙 + 기록이 우선한다**(CLAUDE.md C11 판정 기준 ③).

## 0. 교신·순서·버전 (D-0152 §0 의 V2~V4 버전 번호를 이 표로 대체)
Opus 는 한 번에 한 Phase 만 한다. 음성 트랙(V)과 품질 트랙(Q)을 아래 순서로 **교차** 진행한다. 버전은 실행 순서대로 MINOR 증분.

| 순서 | Phase | 버전 | 사용자 결정 의존 |
|---|---|---|---|
| 1 | V0·V1 음성 백엔드(진행 중) | v5.11.0 | — |
| 2 | **Q0** 기록·충돌 판정·지도 밝은 테마 시제품·유료 TTS 호출 차단 | v5.12.0 | Q0 끝에 **지도 테마 결정**(사용자) |
| 3 | **Q1** cascade V2 + 뒤 카드 테두리 단절 수정 | v5.13.0 | 결정 완료(D148) |
| 4 | **Q2** 인물 뱃지·국기 물결 | v5.14.0 | 결정 완료(D148) |
| 5 | V2 강제 정렬 | v5.15.0 | — |
| 6 | **Q3** 지도 테마·선 위계 채택(골든 재등재) | v5.16.0 | Q0 결정 |
| 7 | **Q4a** 지도 LOD(m/px)·라벨 안정화·가시 영역 검사 | v5.17.0 | — |
| 8 | V3 호르무즈 본편 재현(새 음성 + 새 테마) → 사용자 청취·시청 | v5.18.0 | 사용자 합격 |
| 9 | **Q4b** 지도 데이터 공급자·캐시 manifest(행정 2단계·강·도로·DEM) | v5.19.0 | — |
| 10 | **Q5** 자산 스킬 `osint-visual-asset-create` + F-35 fixture | v5.20.0 | 사용자 파일(F-35 SVG) 도착 |
| 11 | **Q6** 관계선·패널 연결선 | v5.21.0 | Q6 시트 사용자 확인 |
| 12 | V4 edge 경로 삭제 | v5.22.0 | — |

보고는 Phase 마다 `phase_report` + `reports/phaseQ{n}/run_log.md` + 시트. main 머지는 Fable(Q3·V3 뒤 묶음). 결정은 README §6.4.
**`docs/handoff/15` 를 읽고 시작**(엔진 수정 전 의무, C8.0).

## 1. 사용자 결정 기록(DECISIONS D148, 2026-10-10 "분석해서 적용해")
- **cascade V2**(가이드 §6 표) 와 **인물 뱃지·국기 후보**(§10) 는 사용자가 목업으로 확인했다 → 적용 결정. D117 의 cascade 고정값은 D148 로 대체(값은 §3·§4 표).
- **지도 V4 스타일**(밝은 회색 육지·푸른 바다·얇은 선 위계, §7·§15) 은 사용자가 "지도의 테마" 로 지목했으나 가이드 §1 이 "별도 검토 대상" 으로 적었다 → **방향 채택, 기본값 교체는 Q0 시제품(호르무즈 25컷 밝은 테마)을 보고 사용자가 결정**(P7·P12: 헌법·골든은 영상으로 확인한 뒤 바뀐다).
- hairline 식 자산 스킬(§11)·관계선(§8) 은 설계대로 진행, 관계선 값은 Q6 시트로 사용자 확인.

## 2. 가이드 ↔ 저장소 규칙 충돌 판정(DECISIONS D149)
| 가이드 | 저장소 규칙 | 판정 |
|---|---|---|
| §22.3 "선택형 visual profile, 기본값은 기존 출력" | C0.1 byte-equal 비적용, P2 옛 경로는 삭제(플래그 금지) | **교체형**으로 간다. 시안 단계(Q0)만 `stage_config.mercator.theme` 로 두 테마를 나란히 렌더하고, 사용자 결정 뒤(Q3) 한 테마가 기본·골든이 되며 다른 테마는 삭제한다(보존 = archive 브랜치) |
| §19 "edge 음성 유지, 로컬 TTS 교체는 계획에 없음" | D146 사용자 결정(Supertonic M3) | **D146 우선**. §19 의 유료 호출 차단(§19 P0)·발음 회귀 원고(P1)·레벨링 공통 경로(P1)는 V 트랙에 흡수(Q0·V1·V3) |
| §5 "D117 고정값 — 사용자 결정 없이 바꾸지 않는다" | 오늘 사용자 결정 D148 | V2 값으로 교체. 옛 값은 DECISIONS 에 기록으로만 |
| §6 V2 표면색 `#111514`·sage 강조(가상 기관용) | colors 토큰 SSOT, 의미색 재배정 금지 | 표면·테두리·글자색은 cascade 전용 토큰으로 등재(아일랜드 전역 아님). sage 3색은 **등재하지 않는다**(실제 행위자는 기존 actor accent) |
| §15 선폭 720p screen px | 설계 px(480p) + `Output.k` | 720 값 ÷ 1.5 로 설계 px 환산해 rules 에 적는다. 핵심 실선은 장치 스케일 변환 지점 한 곳에서 **최소 1 device px** 보정(§7) |
| §7 "LOD 에서 사라지는 보조 선 제거 또는 광학 보정" | P6 조용한 드롭 금지 | 제거는 LOD 규칙(명시 임계)으로만, provenance 에 레이어별 LOD 상태 기록 |
| §3 "새 모듈 이름을 기존 파일처럼 제시하지 않는다" | — | 가이드의 `visual_profiles`·`map_data_manifest`·`prepare_map_cache`·`SynthesisSpec` 는 이름 제안. 실제 이름은 아래 §3~§8 |

## 3. Q0 (v5.12.0) 기록·판정·지도 밝은 테마 시제품·유료 호출 차단 — 테스트 ≥ 8
0. VERSION 5.12.0·헤더·CHANGELOG(v5.11.0 V1 마감). `docs/handoff/00_INDEX` 에 23 한 줄, `19` §3 행.
1. **유료 TTS 호출 차단(§19 P0)**: `script/tts/elevenlabs.py:eleven_one` 요청 직전에 `config tts.elevenlabs_allowed` 검사(이미 plan 에 있는 거부를 공통 함수로 빼서 두 곳이 같은 함수), `tools/tts_align_probe.py` 는 파일 생성·키 접근 전에 같은 검사. 테스트: `requests.post` mock 으로 plan·provider·probe 세 경로 유료 호출 0(차단 메시지 확인), 키가 있어도 자동 전환 없음.
2. **지도 테마 틀**: 지형 티어 래스터는 `geo/prep_tiers.py lerp_col(stops)` 로 **준비 단계에 색이 구워진다**(실측). 따라서 테마 = 준비 산출물 분기다.
   - `rules geo.themes: {dark: <현재 stops·sea·land 값 그대로>, light: <§13·§15 값>}`. light: 육지 밝은 회색 높이 톤, 해저 푸른 깊이 톤 + 별도 hillshade, 바다 변환 `g → (g−21, g−5, g+8)`(0~255 클램프, 육지 제외), 광원 방위 315°·고도 42°, 과장 1.7(가이드 데모값 — 규칙 키로).
   - `python -m geo.prep <proj> --theme light` → `assets/theme_light/{tiers.pkl, base_*.png}`(기존 경로는 dark 그대로). 테마 값은 rules 에만.
   - `direction stage_config.mercator.theme: dark|light`(StageError 키 목록에 추가). 테마에 따라 `engine/layers/borders.py`·`labels.py`·`engine/style.py` 의 지도 색(국경·행정선·수계·해역 라벨·halo)이 토큰으로 바뀐다. 선 위계 값은 §5 표(Q3 에서 확정, Q0 은 시제품).
   - **시제품**: 호르무즈 골든 25컷을 light 로 `--preview golden` → `reports/phaseQ0/hormuz_light_sheet.jpg` + dark 시트 나란히 비교 이미지. **사용자 결정용**이므로 골든 기준선·expected_deltas 는 건드리지 않는다(dark 가 기본 유지).
3. **cascade 뒤 카드 테두리 단절 재현**(§6 "확인된 뒤 카드 테두리 단절"): `engine/cascade.py:162` 세로 전체 클립이 `draw_frame` 에도 걸려 3장 이상에서 하단선이 끊긴다 — 현 코드로 재현 프레임(8항목 데모 t=5.8) 을 `reports/phaseQ0/cascade_asis_clip.png` 에 확대 crop 으로 남긴다(Q1 전/후 비교 기준).
4. run_log: 가이드 §20 자산 표 중 **이번에 받은 것**(영상 3편·가이드) 과 **받지 못한 것**(F-35 SVG·render 스크립트·지도 데이터)을 표로. 받지 못한 것은 Q5 착수 조건.
합격: 테스트 통과, 시트 2장, 골든 무변경(dark), 유료 호출 0 테스트.

## 4. Q1 (v5.13.0) cascade V2 — 테스트 ≥ 12
`rules cascade` 를 V2 값으로 교체(설계 px 480p, 가이드 §6 표 그대로):
- 슬롯: `x = x0 + dx·s`, `y = y0 + dy·s`, `x0 22, y0 60, dx 64, dy 12`. 좌상단 pivot 고정, 개별 Y slide·depth Y(`back_dy`) **삭제**. oldest-card shift 는 전 카드 같은 offset.
- 앞 카드 `230×108`, pad 14, date/title/detail Y `19/56/82`, date X 18, 제목 18 Plex Sans KR Bold, 부제 11.5, 날짜 10.5 Plex Mono Medium.
- 뒤 카드 scale .86, 높이 `(108 − 20·back)·scale`.
- frame radius 3, edge .65, top accent 1.8. focus .5, shift .6, back_fade_px 12, max_back 4, width_cap 560(최대 549.429 확인).
- 표면·글자 토큰(cascade 전용): 바탕 `#111514`, 앞/뒤 표면 `#1B211D`/`#171C19`, 본문 `#EDF0E9`, 보조 `#A2AAA5`, 테두리 `#4D5851` — `rules colors` 가 아니라 `cascade.surface` 하위 키(hex 금지 규칙이 있는 곳이면 RGB 실수). actor accent 는 기존 키 유지.
- **가림 수정**: `draw_frame` 에 선택 인자(style·clip)로 cascade 전용 경로 — 뒤 카드 frame/fill/stroke 는 **앞쪽 모든 카드의 실제 둥근 사각형 coverage(선 굵기 절반 .325 여유)** 로 순차 complement clip(EVEN_ODD 단일 마스크 금지). 글자의 step clip·경계 fade·시간차는 별도 유지. `cascade_boxes()` 는 같은 가시성 마스크(보수적 사각형 분해, 복원된 하단 strip 포함) → reserved·라벨 회피·`check_text` 가 같은 계산.
- `island.draw_frame` 기본 호출 출력 **바이트 동일**(다른 패널 불변 테스트).
테스트: 모든 프레임 인접 anchor dx>0·dy>0, shift 동일 변위, 최대폭 ≤ 560, 뒤 카드 ≤ 4, 겹친 occluder 영역 alpha 0·노출 테두리 연속(픽셀 표본 4곳), 글자 앞/뒤 절반 순서, 넘침 오류, 3/5/6/8항목·긴 제목·빈 부제·국기 없음·촘촘한 앵커, 480/720/1080 각각 프레임 수·픽셀 포맷. 시트: 8항목 데모 As-is/To-be 480p + 720p 확대 crop(‘조치’ 진입 전후).
골든: hormuz 는 cascade 0 → 무변경(테스트로 확인). `test_cascade`·`test_g14_cascade` 의 값 단정은 새 값으로 갱신(변경량 run_log).

## 5. Q2 (v5.14.0) 인물 뱃지·국기 물결 — 테스트 ≥ 8
`engine/layers/badges.py flag_wave`·`badge_at`, 값은 `rules badge` 에(코드 리터럴 14·0.5·0.032·0.16 을 전부 키로 이관):
- 사진 폭 `1.72R → 2.04R`, 실제 alpha-top `−.83R`(원본 alpha>20 최상단 행 기준 — 정규화의 alpha>40 bbox 와 **별개 키**).
- 국기 중심 `(0.16R, −0.05R)`, 폭 `2.3R`, 원 내부 clip. strip 수 = 출력 크기 기반(규칙: 480p 96 상한, device 폭에 비례, 하한 14), 위상 `t·2.6 + (i/n)·7`, 진폭 `.018·width`. 변형 surface 캐시(원본 국기당 1회), 매 프레임 face surface 재처리 금지. strip 경계 겹침·빈 줄 0.
- 링: 바깥 어두운 `2.4`, 안쪽 파란 `.8` 설계 px, 얼굴 분리 shadow alpha `.16`.
- solo R56·group R30–34 각각 시트. 국기 모양·색 영역 원본 보존(flag-icons MIT 고지 유지), 국장(emblem) 뱃지는 손대지 않는다.
- 성능: 같은 장면 전/후 프레임 시간·최대 메모리, 96-strip 비용 별도 표(§21).
골든: hormuz 뱃지 컷(이재명·하메네이 등)이 바뀐다 → 골든 PNG 무수정, `expected_deltas q2_portrait_flag_d148` + `phaseQ2/hormuz_baseline.json`(바뀐 컷 목록·bbox·사유). 바뀐 컷 시트를 사용자 확인용으로.

## 6. Q3 (v5.16.0) 지도 테마·선 위계 채택 — Q0 사용자 결정 뒤
사용자가 light 를 고르면: 기본 테마 light, dark 는 삭제(archive/map-dark-theme), `CLAUDE.md C0` 에 "지도 테마 = 밝은 지형·푸른 수계(2026-10-10 사용자 결정 D150)" 한 줄(P7, 헌법 변경은 이 한 줄), 골든 25컷 전부 `expected_deltas q3_map_theme_light` + `phaseQ3` 기준선, `border_glow` 는 light 에서 재조정값을 시트로(사용자 확인). dark 를 고르면 Q3 = light 경로 삭제 + 선 위계만 dark 에 적용.
선 위계(§15, 720 px ÷ 1.5 = 설계 px, rules `map_lines`): 국경 실선 .77 RGB 54/54/54 α .90 · ADM1 .37 gray151 α .42 · ADM2 .30 gray170 α .30 · 도로 primary .33/trunk .43/motorway .53(gray 119/91/73) · 강 단일 하늘색 RGB 135/183/208 major .47+.10·LOD/secondary .40/minor .33 · casing·이중 band 없음. **최소 device px 보정은 `engine/style.py` 한 곳**(§7). 그리기 순서 terrain·bathymetry → coast·hydro → admin → roads → **national borders** → labels → events/UI(§12-5).
테스트: 선 위계 순서(국경이 가장 진함), 최소 px 보정 1곳, 테마 키 extra 거부, 25컷 재등재 목록 = 실제 diff 목록.

## 7. Q4a (v5.17.0) 지도 LOD·라벨·가시 영역 — 테스트 ≥ 10
- `MERCATOR_LOD`(경도 폭 기준)를 **m/px 기준**으로(중심 위도 반영). 계단값은 rules 로 이관(현재 코드 상수 — P3 위반 상태를 해소). ADM1 `1600→900 m/px`, ADM2 `430→325` 페이드(§15), 도시·국가 rank 상한도 m/px 로 환산해 **현 골든 결과가 같은 값**에서 출발(변환표 run_log).
- 진입·이탈 hysteresis + 짧은 opacity 전환(§9·§16). stable feature ID·결정적 priority·anchor 후보 순서. viewport 밖 제거.
- 이동 프레임 전부 라벨 bbox(실측 glyph·halo·여백) 화면 경계 검사, 고정 UI(제목·스케일바·범례) text bounds 검사(§9). 스케일바는 중심 위도 기준(§17).
- 가시 영역 검사: 카메라 경로 전체에서 DEM clamp·행정 데이터 구멍·도로 절단 → hard(§16).
- 날짜변경선·±85.0511° 한계·고위도 fixture(§17) — 지원 한계는 명시 오류.
골든: 변환표가 맞으면 무변경(테스트).

## 8. Q4b (v5.19.0) 지도 데이터 공급자·캐시 manifest — 테스트 ≥ 10
- 공급자 어댑터 `geo/providers/{natural_earth, geoboundaries, ocha_cod, osm_pbf, etopo}.py` + 지역 어댑터(우크라이나 OCHA 2025 북쪽 arc 등은 **지역 어댑터**에만, §14). 경계 의미 분리 `international_land_boundary / administrative_boundary / coastline / inland_water_shore / inland_water / disputed_claim / operational_control`(마지막 둘 자동 그리기 금지).
- manifest 필드 §18 그대로(`provider, source_url, dataset_version, retrieved_at, valid_at, license, attribution, source_hash, bounds, crs, vertical_datum, native_resolution, sample_spacing, lod, transform_version, coverage_status`), 원본·단순화·래스터·렌더 해시 분리, atomic replace, 부분 파일 캐시 등록 금지.
- 강 = NE 10m centerline(두 번 Chaikin, 강폭 암시 금지), 도로 = 허용된 PBF 추출물만(공개 타일 bulk 금지, ODbL 크레딧 `engine/credits.py` 연결), DEM = ETOPO 2022 30″ 또는 terrarium(원천·표본 간격 기록), 해안·석호·섬은 수계 geometry 보존.
- fixture: 한국·우크라이나(가이드 §16 중심/폭 3단) + 데이터 없는 지역·섬·해협·여러 나라 화면.
`docs/09_MAP_AND_GEO_SPEC.md` 동기화(C7).

## 9. Q5 (v5.20.0) 자산 스킬 `osint-visual-asset-create` — 사용자 F-35 파일 도착 뒤
- 폴더 §11.3 그대로(`SKILL.md` + `references/*` 6 + `templates/*` 2). SKILL 본문은 §11.3 골격. 코드는 스킬 안에 두지 않는다(D131 관례) → 공용 도구 `tools/visual_asset.py`(SVG 구조 검사: XML·외부 URI·스크립트·NaN·빈 path·bbox·mirror 대칭 범위·safe bbox; LOD/테마 변형 → PNG rasterize; manifest 생성). rasterizer 는 저장소 의존성 안에서(cairo + svg 파서가 없으면 `decision_request`: cairosvg 추가 여부).
- manifest = `schemas/media_models.py` 확장(미디어 kind `vector`, §11.4 필드), 레지스트리 `assets/media/media_registry.json` 흐름 재사용, `draw_cutout` 은 준비 단계 PNG 변형을 읽는다(SVG 런타임 지원 가정 금지, §11.8). `engine/credits.py` 연결. Hairline 코드는 복사하지 않는다(원칙만 채택, `references/upstream-hairline.md` 에 commit a2217852·채택/변형/제외 표 = 가이드 §11.2). 복사하면 MIT 전문 고지(`THIRD_PARTY_NOTICES.md` 신설 여부는 결정 요청).
- F-35 V2 fixture: 사용자 파일(`f35-refined-v2*.svg`, `build_f35_v2.py`) 로 §11.11 값 검증(span 681.529, stroke outline 1.65/structure 1.05/detail .8/focus 1.85, compact 3/1.65/3.2, intrinsic 1600×1100, 225·240px 읽힘, dark/ivory occlusion 면색). 정확도 등급 `generic` 으로 등록(reference-audited 는 리뷰 통과 뒤).
- 시간 계약(`render_at(t)` 순수 함수)·reveal 애니메이션은 **Q5b 로 보류**(실사용 요청 때).
테스트: 구조 검사 양성/음성, 결정성(같은 입력 2회 md5), 변형 PNG 크기, manifest 스키마, 레지스트리·크레딧 연결, 외부 URI 거부.

## 10. Q6 (v5.21.0) 관계선·패널 연결선 — 시트로 사용자 확인 뒤 채택
`engine/panels/relation.py`(먼저)·network·timeline·fork 각각 As-is/To-be 시트. 후보값(§8): 포트 `y±12`, `x = sx + sqrt(sr²−12²) + 5`, 타깃 `(dx−dr−6, dy)`, 수평 접선 cubic, 화살촉 없음, 선폭 1.6, 포트 R 2.1, 거절 dash [5,4], 강조 .45초 뒤 낮춤, 뱃지 .32초 fade(bounce 제거). 규칙: 선은 노드·뱃지·글자 경계에서 끝난다(검사), 크로싱 최소화(anchor 정렬), 정적 구조선 고정, 데이터 연결 삭제·재배열 금지. `routes.py` 지리 경로와 패널 관계선은 서로 대체하지 않는다.

## 11. 공통 합격 조건
pytest failed 0·skip 0(자산 환경), 기준 = 직전 Phase passed + 새 테스트. 골든 PNG 수정 금지 — 바뀌는 컷은 expected_deltas + 새 기준선 + 사유. 새 외부 패키지는 `decision_request`. 모델 식별자·PR·force push 금지. 각 Phase run_log 에 "수행한 것 / 미구현 / 검증 못 한 것" 세 칸(가이드 §24).

## 12. Fable 검수(각 Phase)
pull → 전체 pytest → 시트·프레임 내 컨테이너 재렌더(480·720·1080 중 Phase 가 요구하는 것) → 픽셀 대조 → 음성 주입(값 깨뜨린 사본이 검사에 걸리는지) → 성능 표 대조 → `review`. Q0·Q6 시트와 Q2 바뀐 컷 시트는 사용자에게 전달해 결정을 받는다.

## 13. 착수
V1 을 끝내고(진행 중인 커밋 마감) `phase_report`(V1) → Q0. Q0 의 유료 호출 차단(§3-1)은 V1 이 아직 `script/tts` 를 열어 두고 있으면 V1 마지막 커밋에 넣어도 된다(run_log 에 표시).
