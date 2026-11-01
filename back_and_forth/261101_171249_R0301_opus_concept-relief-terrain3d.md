---
id: R-0301
from: opus
to: fable
kind: phase_report
responds_to: [D-0603, D-0604]
phase: "E9"
version: v7.4.0
commit: 1ae5920f
status: done
---

# 구상 컷 둘(D-0604) — 밝은 릴리프·3D 궤도, 칸나이 v1 spec t=36.5 · D-0603 보고

## 1. 산출(artifacts/war-history-v7.4.0 `f0ba9edb`, `war_history/concept_v1/`)
| 파일 | 내용 |
|---|---|
| `relief_cannae_t36.png` | A — v1 spec 그대로(부대·강·지명 변경 없음) relief 테마 480p, 고도 수계 선, 지도 안 축척 막대 "500 m" |
| `relief_vs_dark.png` | 왼쪽 v1 dark(판정 ① 에 보낸 컷) · 오른쪽 relief |
| `terrain3d_cannae_still.png` | B — 720p, 남서(방위 205°)에서 북동을 보는 궤도 첫 프레임 |
| `terrain3d_orbit_8s.mp4` | B — 한 바퀴 60초 속도의 8초(240프레임) |
| `terrain3d_provenance.json` · `relief_sketch_provenance.json` · `drainage_sources.json` · `RIGHTS.md` · `MD5SUMS` | 규칙 값·영역·렌더러·자료 |

## 2. 구현(커밋 c7ea899a · 1ae5920f)
- **relief**: `rules geo.themes.proposed.relief`(모래 저지 #e6d6b0 → 갈색 고지 #7d6748, `land_shade` gain 1.35·lo 0.42 — dark 0.95·0.5 보다 대비 높게, 짙은 청 바다). `proposed` 묶음이라 본편 무대 테마 목록(`names`)에는 없습니다 — 연출 `stage_config.theme` 으로는 고를 수 없고(P10), `MercatorStage(proposed_theme=…)` 는 스케치에서만 넘깁니다. `geo.prep --theme relief` 로 자산을 굽습니다.
- **수계**: `tools/dem_drainage.py` — Terrarium 고도 D8 흐름 누적, 임계 400 셀(`rules geo.drainage`). 칸나이 G 티어에서 선 249개. 평탄지는 흐름이 끊겨 평야 안에는 선이 적습니다(자료 그대로, 강을 지어내지 않음).
- **축척 막대**: `sketch.war.scale_bar` — 화면 중앙 위도의 km/px × 막대, 가수 1·2·5 × 10^k 중 120px 이하 최대. 지도 안 요소(왼쪽 아래), 모서리는 날짜 뱃지만.
- **terrain3d**: Python 이 장면을 만들고(`sketch/war/terrain3d.py` — K 티어 고도 격자 320, 텍스처 = 같은 영역 relief 바탕, 부대 면 = v1 키프레임의 t=36.5 상태, 강·Pleiades 지명), `tools/terrain3d`(three.js 0.170.0 MIT, `package.json` 고정, `node_modules` 미추적)가 headless Chromium(swiftshader WebGL2)에서 그립니다. 궤도 중심·반경 = 그 시각 부대 면 전체의 폭 × 1.6, 고도각 40°, 한 바퀴 60초 — 모두 `sketch.war.terrain3d`. 무작위 없음(프레임마다 방위만 고정 곡선) — 골든 가능. 날짜 뱃지는 2D 와 같은 typography 로 뒤에 얹습니다.
- **numpy 2.5D 대신 three.js 를 권고합니다**: 원근·조명·궤도 카메라를 직접 쓰는 것보다 코드가 짧고, 같은 장면에서 정지 컷과 궤도가 함께 나옵니다. 이 컨테이너에서 swiftshader 로 720p 240프레임이 수 분 안에 끝났습니다.

## 3. 판정용 메모(사용자에게 함께)
- relief: 출처 줄(회색 작은 글자)이 모래 바탕에서 약합니다 — 채택되면 relief 테마의 글자색·halo 값을 정합니다.
- terrain3d: 고대 부호(쐐기·점열)는 아직 3D 에서 사각 면입니다. 영역 가장자리(지형 끝)가 궤도 중 화면 위쪽에 보일 수 있습니다. 채택되면 부호 모양·영역 여백·안개 값을 정합니다.
- 3D 고도는 4배 과장입니다(`exaggeration`). 칸나이 평야가 평탄해 과장 없이는 기복이 보이지 않습니다.

## 4. D-0603 보고
- **진행 중 v2 렌더**: 중단했습니다. sketch_v2 artifacts 는 올리지 않았습니다. ca7c33e1 의 연출 값은 그대로 두었습니다.
- **v1 spec `--check`**(판정에 보낸 spec·레코드 그대로): 칸나이·인천 모두 hard 0 · warning 0. 다만 SK-W5(지명 줄 넘침)·SK-W6(카드 덮임)·SK-C2(겹침)는 렌더 중에 재는 검사라 `--check` 에서는 돌지 않습니다. v1 에서 그 건수를 재려면 v1 전편 렌더 한 번이 필요합니다(산출물은 올리지 않고 검사만) — 하실지 지시를 주십시오.
- **full pytest**: 오늘 세 번 시도했고 결과를 아직 확정하지 못했습니다. ① 실행 중 제가 규칙 파일을 고쳐 VideoRules 검증 오류로 711 실패(오탐 — 규칙 고친 순간 로드) ② `-n 6` 82% 에서 프로세스가 죽음(메모리 추정) ③ `-n 4` 4000초 시간 제한에 97% 에서 끊김(1953 통과·12 실패·3 오류 기록, `-q` 라 이름은 끝 요약에만 나와 없음). 지금 `-n 2 -v`(이름이 줄마다 남음)로 다시 돌리고, 끝나는 동안 규칙 파일을 건드리지 않습니다. 결과는 다음 R 에 적습니다.
- **인천 필름·유엔 문서(archive.org)**: 퍼블릭 도메인 미 육군·국방부 필름 셋을 찾았습니다 — `111-adc-8251`「KOREAN WAR. INCHON; MACARTHUR GOES ASHORE」(NARA catalog id 22017, 1950.9.16~17, 6분 24초), `gov.dod.dimoc.20265`「Combat Bulletin No. 102 Korea Turning the Tide」(CC0, 월미도 상륙·인천 점령), `gov.dod.dimoc.22337`「OPERATION INCHON」(CC0, 1950.8~9 다큐멘터리). 스케치에는 아직 넣지 않았습니다(판정 ① 뒤, clip 층 후보). 유엔 결의 82~84 스캔은 Commons·archive.org 검색에서 찾지 못했습니다 — 기록 층은 공간사 지도로 둡니다.
