---
name: campaign-front-map
description: 한 전역(戰役)의 전황 작전도를 사용자 검토용 화면 스케치로 만든다. 국가·제대별 부대 부호, 날짜별 전선, 진격 화살표, 포위망, 당시 지명을 spec YAML 만 써서 그린다. "전황", "작전도", "전선", "제대 배치", "포위", "전황 스케치" 같은 요청에 쓴다.
---

# campaign-front-map — 전황 작전도 화면 스케치

이 스킬은 코드를 담지 않습니다. `python -m sketch.campaign` 을 부르는 절차서입니다(D131).
코드·규칙 파일(`sketch/`·`rules/`·`schemas/`·`tests/`)은 고치지 않습니다. 전역마다 바꾸는 것은 `projects/<pid>/` 안의 spec·데이터뿐입니다.
계약·검사·규약의 정본은 `docs/handoff/22_SKETCH_TRACK.md` 입니다. 이 문서는 그 요약과 절차입니다.

## ① 쓰는 때 · 안 쓰는 때

- **쓴다**: 한 전역의 날짜별 전황(전선 이동·포위)을 자막·내레이션 없는 짧은 화면으로 사용자에게 먼저 보일 때.
- **쓰지 않는다**: 본편 영상입니다. 스케치는 엔진 레지스트리 밖입니다(D128).
- **쓰지 않는다**: 경위도 눈금이 있는 권리 확인된 참고 작전도가 없는 전역입니다. 전선은 참고 작전도를 정합해 옮긴 선만 씁니다(SK-G1). 이런 경우 사용자에게 자료 부족을 보고합니다.

## ② 수집할 사실 체크리스트

수집한 값은 모두 spec 에 넣고, 출처는 `sources[]` 에 한 줄씩 남깁니다. 전선·부대 위치는 모두 **개략**이며 화면에 그렇게 밝힙니다(SK-H5).

| 항목 | 출처 | spec 필드 | 표시 |
|---|---|---|---|
| 날짜별 전선 | 참고 작전도 SVG(Wikimedia Commons, **경위도 눈금 포함**) | `fronts.reference`·`fronts.style_map`·`fronts.layers` | 정합한 개략선 |
| 참고 작전도 권리 | Commons 파일 페이지(저자·라이선스·원 지도) | `projects/<pid>/RIGHTS.json` | `rules sketch.rights.allowed_licenses` 안만 |
| 부대 배치(국가·제대·병종) | 참고 지도 2종 이상 대조(대조만 한 지도는 `references_not_stored`) | `units[]` | 군·군단 단위 개략 |
| 진격 경로 | 참고 작전도 화살표 | `arrows.items` | 개략 |
| 당시 지명·현재 이름 | 참고 작전도·지명 사전 | `places[]`(`now` = 현재 이름) | 당시 이름이 주 |
| 날짜 | 전역 연표 | `dates[]`·`date` | 화면 모서리에는 날짜만 |
| 병력 등 수치 | 사료(서로 다르면 범위) | `sources[]` 의 엔딩 자료 줄만 | 화면 문구에 단위 숫자 금지(SK-H1) |

## ③ 프로젝트 폴더 준비

`<pid>` 는 `<전역 영문>_sketch` 처럼 짓습니다. 아래 순서대로 합니다.

1. **폴더**: `projects/<pid>/` 를 만듭니다. `projects/uranus_sketch/` 에서 `geo.yaml`·`labels.yaml`·`.gitignore` 를 복사합니다.
   - `geo.yaml` 의 `bbox`·`tiers[].bbox` 를 전역 화면이 들어가게 바꿉니다. `admin1: []` 은 유지합니다. 현대 행정구역선을 그리지 않기 위해서입니다.
2. **지형**:
   ```bash
   python -m geo.prep projects/<pid>
   python -m geo.prep projects/<pid> --res 720p
   ```
3. **참고 작전도**: SVG 를 `projects/<pid>/` 에 둡니다(`tools/commons_fetch.py get "File:<이름>.svg" projects/<pid>/<이름>.svg`, 요청 간격은 도구가 지킴).
   `projects/<pid>/RIGHTS.json` 에 항목을 적습니다. 형식은 `docs/handoff/22` §4 이고, 예는 `projects/uranus_sketch/RIGHTS.json` 입니다.
4. **스타일 표 만들기**: SVG 의 선 묶음(색·굵기·점선)이 무엇을 뜻하는지 범례와 대조해 spec `fronts.style_map` 에 적습니다.
   - 묶음 목록은 `python -c "from sketch.common.svg_georef import collect; from pathlib import Path; [print(k, len(v)) for k, v in collect(Path('projects/<pid>/<이름>.svg')).items()]"` 로 봅니다.
   - 경위도 눈금선 묶음은 `fronts.graticule`(`stroke`·`width`·`lons` 서 → 동·`lats` 북 → 남)입니다.
5. **정합**:
   ```bash
   python -m sketch.campaign.prep_georef projects/<pid>      # → projects/<pid>/fronts.json
   ```
   - 눈금선 수가 spec 과 다르거나 잔차가 `rules sketch.checks.georef_residual_deg` 를 넘으면 파일을 쓰지 않고 실패합니다(SK-G1).
   - 출력의 `layers`(층 → 편 → 조각 번호)를 보고 spec `fronts.layers[].pieces`("층:편:번호")를 고릅니다.

## ④ spec 작성 규칙

`projects/uranus_sketch/sketch.yaml`(1942.11 천왕성 작전)을 `projects/<pid>/sketch.yaml` 로 복사해 출발합니다. 필드 계약은 `docs/handoff/22` §2.1·§2.7 입니다.

- **부대(SK-G3)**: `echelon` 은 `XXXX`(군)·`XXX`(군단)·`XX`(사단), `arm` 은 `inf`·`arm`·`cav` 만 씁니다. 무너진 부대는 `fade` 로 흐립니다.
- **전선**: 층마다 `grow`(그려지는 시각·길이)와 `dim`(물러남)을 둡니다. 소련·추축 같은 이중선은 추축 쪽 조각 하나로 그리고, 코드가 화면에서 옮겨 이중선을 만듭니다.
- **포위망(SK-G2)**: `pockets[].build` 레시피(조각·점·`lon_min`·`lon_min_of`·`start_near`·`reverse`)로 다각형을 만듭니다.
  - 자기 교차가 크면 hard 입니다.
  - 미세 조각(`rules sketch.checks.pocket_sliver_ratio` 이하)은 warning 으로 남고 그대로 그립니다(D140). warning 위치는 보고에 적습니다.
- **도시 검산(SK-G1)**: 참고 SVG 에 원 기호로 찍힌 큰 도시 두 곳을 `fronts.city_check` 에 places 이름으로 적습니다.
  - 기호와 spec 좌표의 거리가 `rules sketch.checks.georef_city_deg` 를 넘으면 hard 입니다.
  - 지도 기호 배치 관례(강기슭 등) 때문이면 spec 좌표를 지도에 맞추지 말고 사용자에게 보고합니다.
- **개략 표기(SK-H5)**: 전선·부대 위치는 화면이 열린 뒤부터 엔딩 직전까지 보입니다. 따라서 '개략'(`rules sketch.checks.approx_word`)이 든 출처 줄 하나가 그 전 구간을 덮어야 합니다. 엔딩 자료 `sources[]` 에도 '개략' 을 씁니다.
- **수치(SK-H1)**: 태그·라벨·출처 줄에 단위 붙은 숫자를 쓰지 않습니다. 병력 추정은 엔딩 자료 줄에 범위로만 씁니다.
- **지명**: 당시 이름을 `name` 에, 현재 이름은 `now` 에 둡니다. 현대 국경·현대 지명 레이어는 그리지 않습니다.
- **카메라(SK-C1)**: 숏은 `shots[]` 로만 바꿉니다. 큰 줌 이동은 `rules sketch.camera.move_min_sec` 이상 둡니다.
- **사용자 확정 대기**: 지도 해석이 갈리는 값(부대 위치, 포위망 경계 등)은 spec 줄에 `# 사용자 확정 대기` 주석을 남깁니다. 공통 목록은 `docs/handoff/22` §6 입니다.
- **화면 수치(px·알파·간격·글자 크기)는 spec 에 쓰지 않습니다.** 모두 `rules/video_rules.yaml sketch:` 에 있습니다(C0).

## ⑤ 실행

순서대로 돌리고, 종료 코드 ≠ 0 이면 멈춥니다. 메시지 앞의 SK-ID 로 `docs/handoff/22` §3 검사표를 보고 spec 을 고칩니다.

```bash
python -m sketch.campaign projects/<pid> --check                 # 1. 검사만(렌더 없음). "hard 0" 이어야 함
python -m sketch.campaign projects/<pid> --frames 11.5,38.5,51   # 2. 3컷 정지 화면(480p) — out/sketch_campaign_*.png 를 직접 본다
python -m sketch.campaign projects/<pid> --res final             # 3. 전편(720p) → out/sketch_campaign.mp4 · sketch_campaign_sheet.jpg
```

- 2 단계에서 라벨 겹침·잘림이 보이면 spec 위치·숏을 고칩니다. SK-C2(warning)는 겹친 시각을 알려 줍니다.
- 확인할 것: `out/sketch_provenance.json` 의 `checks.hard` 가 빈 목록, `data_files` 에 참고 SVG·fronts.json 의 sha1·라이선스, `approximations` 에 정합 잔차가 있어야 합니다.

## ⑥ 사용자 전달물

- `out/sketch_campaign.mp4`(커밋하지 않음)와 `out/sketch_campaign_sheet.jpg`.
- `out/sketch_provenance.json`.
- warning 목록(SK-G2 위치, SK-C2 시각)과 사용자 확정 대기 목록(`docs/handoff/22` §6 링크 + 이번 전역 항목).
- 출처 목록: spec `sources[]` 그대로.

## ⑦ 금지 · 한계

- 코드·규칙 파일을 고치지 않습니다. 막히면 그 지점을 보고합니다.
- 현대 국경·행정구역선·현대 지명을 당시 지도에 그리지 않습니다.
- 참고 작전도에 없는 전선을 지어 그리지 않습니다. 부대 위치는 대조한 지도 범위 안의 개략입니다.
- 본편 요소가 아닙니다. 본편 등록 후보와 필요한 설계 결정은 `docs/handoff/22` §7 에 있습니다.
