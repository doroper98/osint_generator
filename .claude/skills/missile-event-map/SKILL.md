---
name: missile-event-map
description: 북한 미사일 발사 사건 하나를 사용자 검토용 화면 스케치로 만든다. 2D 지도(EEZ·탐지 자산·발사·궤적·탄착 불확실성·고도 단면)와 3D 지구본 전환편을 spec YAML 만 써서 만든다. "북한 미사일 발사", "탄착", "탐지 자산", "EEZ", "레이더 수평선", "미사일 스케치" 같은 요청에 쓴다.
---

# missile-event-map — 미사일 발사 사건 화면 스케치

이 스킬은 코드를 담지 않습니다. `python -m sketch.missile` 를 부르는 절차서입니다(D131).
코드·규칙 파일(`sketch/`·`rules/`·`schemas/`·`tests/`)은 고치지 않습니다. 사건마다 바꾸는 것은 `projects/<pid>/` 안의 spec·데이터뿐입니다.
계약·검사·규약의 정본은 `docs/handoff/22_SKETCH_TRACK.md` 입니다. 이 문서는 그 요약과 절차입니다.

## ① 쓰는 때 · 안 쓰는 때

- **쓴다**: 발사 사건 하나를 자막·내레이션 없는 짧은 화면으로 사용자에게 먼저 보일 때. 출력은 2D 편과 3D 지구본 전환편(선택)입니다.
- **쓰지 않는다**: 본편 영상입니다. 스케치는 엔진 레지스트리 밖입니다(D128). 본편은 원고 → 콘티 → 본편 순서입니다(CLAUDE.md C8.6).
- **쓰지 않는다**: 발표 수치가 아직 없는 사건입니다. 화면 수치는 발표값만 씁니다(SK-H1). 발표 전이면 사용자에게 기다리자고 보고합니다.

## ② 수집할 사실 체크리스트

수집한 값은 모두 spec 에 넣고, 출처는 `sources[]` 에 한 줄씩 남깁니다. **화면 숫자는 발표값 그대로입니다. 좌표로 계산한 거리·시간을 화면에 쓰지 않습니다.**

| 항목 | 출처 | spec 필드 | 표시 |
|---|---|---|---|
| 발사 지점 표현·시각 | 합동참모본부 발표(보도 인용 시 매체·날짜) | `launch.label`·`launch.sub`·`launch.lon/lat` | 발표 표현 그대로. 좌표는 지명의 대표점 |
| 비행 거리·정점 고도·속도 | 합동참모본부 발표 | `announced.jcs.values` | 발표값 그대로, "약" 이면 `approx: true` |
| 비행 거리·정점 고도·비행 시간 | 일본 방위성 발표 | `announced.mod.values` | 발표값 그대로. 두 기관을 나란히 같은 무게로 |
| 탄착 기준점·방위·거리 | 일본 방위성 발표("○○ 서쪽 약 ○km") | `track.ref`·`track.bearing_deg`·`track.distance_km`·`track.approx` | 발표값. "약" 이면 영역(`uncertainty_km`) |
| 탄착 수역(EEZ 안·밖) | 일본 방위성 발표 | `track.impact.tag` | 발표 문구 |
| EEZ 경계 | Marine Regions(VLIZ) WFS, CC BY 4.0 | `eez.file`·`eez.prep` | 데이터. 같은 지역이면 ③-4 재사용 |
| 탐지 자산 거리·방위 폭 | 공개 사양·보도(GlobalSecurity, CSIS Missile Threat 등) | `sensors[]` | "사용자 확정 대기" 주석 필수 |
| 미사일 도해(선택) | Wikimedia Commons(권리가 분명한 것만) | `media[]`·`card`·`media/RIGHTS.json` | 없으면 카드를 뺀다(③-5) |
| 날짜 | 발표 날짜 | `date`·`title` | 화면 모서리에는 날짜만 |

두 기관 값이 다르면 둘 다 씁니다. 한쪽을 고르거나 평균 내지 않습니다.

## ③ 프로젝트 폴더 준비

`<pid>` 는 `missile_YYYYMMDD_sketch` 처럼 짓습니다. 아래 순서대로 합니다.

1. **폴더**: `projects/<pid>/` 를 만듭니다. `projects/d1_missile_sketch/` 에서 `geo.yaml`·`labels.yaml`·`.gitignore` 를 복사합니다. `.gitignore` 의 첫 줄 설명을 고치고, d1 도해 예외 줄(`!media/hwasong17_diagram.png`)은 지웁니다(③-5 에서 이번 도해가 있을 때만 그 파일 이름으로 다시 넣음).
   - 한반도·일본 주변 사건이면 `geo.yaml` 티어를 그대로 씁니다. 다른 지역이면 `bbox`·`tiers[].bbox` 를 사건 화면이 들어가게 바꿉니다(`docs/09_MAP_AND_GEO_SPEC.md`).
2. **지형**: 두 해상도를 준비합니다.
   ```bash
   python -m geo.prep projects/<pid>
   python -m geo.prep projects/<pid> --res 720p
   ```
   `projects/<pid>/assets/tiers.pkl` 과 `assets/res_720p/` 가 생기면 됩니다.
3. **3D 지구본 텍스처(3D 편을 만들 때만)**: 전 지구 텍스처는 사건과 무관합니다.
   - `projects/d1_missile_sketch/globe_tex/assets/tiers.pkl` 이 있으면 spec `globe.texture_project: ../d1_missile_sketch/globe_tex` 로 재사용합니다.
   - 없으면 `projects/<pid>/globe_tex/` 에 d1 의 `globe_tex/geo.yaml`·`labels.yaml` 을 복사하고 `python -m geo.prep projects/<pid>/globe_tex` 를 돌린 뒤 `texture_project: globe_tex` 로 씁니다.
4. **EEZ**:
   - 화면 권역·나라가 d1 과 같으면 spec `eez.prep` 블록을 d1 그대로 두고 `projects/d1_missile_sketch/eez.json` 을 `projects/<pid>/eez.json` 으로 복사합니다. 같은 입력이면 결과가 같은 파생 파일입니다.
   - 권역이 다르면 `eez.prep`(`wfs_url` bbox·`keep` mrgid·`clip`)을 고치고 다시 만듭니다.
     ```bash
     curl -sS -A "osint_generator sketch (research)" -o /tmp/eez_<pid>.json "<spec eez.prep.wfs_url>"
     python -m sketch.missile.prep_eez /tmp/eez_<pid>.json projects/<pid>
     ```
     외부 요청은 한 번만 하고 결과 파일을 재사용합니다.
5. **도해(선택)**: Commons 에서 권리가 분명한 도해를 찾습니다.
   ```bash
   python tools/commons_fetch.py search "<미사일 이름> diagram" --limit 7
   python tools/commons_fetch.py get "File:<이름>" projects/<pid>/media/<파일>.png --width 960
   ```
   - 요청 간격·재시도는 도구가 `config.yaml commons` 대로 지킵니다. 직접 반복 요청하지 않습니다.
   - 검색어는 두세 개(형 이름 영문·한글 로마자·"missile diagram")를 시도합니다. 결과 줄이 비어도 실패가 아니라 "후보 없음" 입니다.
   - 도구 출력의 `allowed` 표시는 인물·휘장용 판정이라 스케치 기준이 아닙니다. 라이선스가 `rules sketch.rights.allowed_licenses` 안이고 파일 페이지에 사용 제한(Restrictions)이 없을 때만 씁니다. `projects/<pid>/media/RIGHTS.json` 에 항목을 적습니다. 형식은 `docs/handoff/22` §4 입니다.
   - `.gitignore` 에 `media/*` 와 쓴 파일의 `!media/<파일>`·`!media/RIGHTS.json` 을 둡니다.
   - **권리가 분명한 도해가 없으면 `media`·`card` 를 spec 에서 빼고 엔딩 자료의 도해 줄도 지웁니다.** 카드 없이도 검사·렌더는 통과합니다.

## ④ spec 작성 규칙

`projects/d1_missile_sketch/sketch.yaml`(2022.11.18 화성-17형)을 `projects/<pid>/sketch.yaml` 로 복사해 출발합니다. 사실 값만 바꾸고, 연출 시각(숏·등장 시각)은 같은 구성이면 그대로 둡니다. 필드 계약은 `docs/handoff/22` §2.1~§2.2 입니다.

- **화면 숫자 = 자리표시만(SK-H1)**: 문구에 숫자를 직접 쓰지 않습니다. `{jcs.range_km}`·`{mod.apogee_km}`·`{track.distance_km}`·`{sensor.range_km}` 처럼 씁니다. 자유 문구(출처 줄·엔딩)에 단위 숫자를 쓰면 발표값 표에 있는 값이어야 합니다.
- **두 기관**: `announced` 에 기관마다 `values`·`rows` 를 둡니다. `profile.curve` 는 정점·거리를 가져올 기관 키입니다. 3D 편의 정점 라벨도 이 기관 값을 씁니다.
- **착탄**: 발표가 "약" 이면 `track.approx: true` + `uncertainty_km` > 0(SK-H2)입니다. 반경은 발표가 아닌 스케치 값이므로 "사용자 확정 대기" 주석을 답니다.
- **탐지 자산(SK-H3, `docs/handoff/22` §2.4)**:
  - 위치 비공개 레이더는 `location_public: false` + `tag` 필수입니다.
  - 이동 자산은 `kind: ship` + `tag` 필수이고 `range_km` 는 비웁니다.
  - 3D 볼륨(`el_deg`)은 위치 공개 + 범위가 있는 자산만 씁니다. 방위·고각은 개념값이라 라벨에 "(개념)" 을 붙입니다.
  - 거리·방위 값은 사건과 무관한 자산 사양입니다. d1 값을 그대로 쓰되 "사용자 확정 대기" 주석을 유지합니다.
- **착탄 강조(`eez.pulse`)**: 착탄이 발표상 그 나라 EEZ **안**일 때만 그 나라 코드를 둡니다. 밖이거나 미발표면 `pulse` 줄을 지웁니다.
- **해양 경계(SK-H4·H5, `docs/handoff/22` §2.5)**:
  - 중첩 주장 수역은 청구국 두 색 사선입니다(`kind: overlap`, `claimants` 두 나라 색이 달라야 함).
  - 서해 남북은 NLL 과 북한 1999 선 사이 빗금이고, NLL 은 `approx: true` 입니다. 그 층이 설명되는 동안 '개략'(`rules sketch.checks.approx_word`)이 든 출처 줄을 두고, 엔딩 자료에도 '개략' 을 씁니다.
- **사용자 확정 대기 항목**: 독도 문구·NLL 좌표·레이더 사양 값·착탄 반경·3D 방위·고각입니다. 현재 값과 근거는 `docs/handoff/22` §6 표에 있습니다. spec 해당 줄에 `# 사용자 확정 대기` 주석을 남기고 값을 임의로 바꾸지 않습니다.
- **카메라(SK-C1)**: 숏은 `shots[]` 로만 바꿉니다. 큰 줌 이동은 `rules sketch.camera.move_min_sec` 이상 둡니다. 발사 지점·탄착 지점이 바뀌면 숏 중심만 옮기고 시각 구성은 유지합니다.
- **3D 편(`globe`)**: `globe.center` 는 마지막 숏 중심과 같아야 합니다(이음새). `handoff_2d_t` 는 2D 길이 안이어야 합니다. 수평선 패널의 `note` 는 비우지 않습니다(SK-H6).
- **화면 수치(px·알파·간격·글자 크기)는 spec 에 쓰지 않습니다.** 모두 `rules/video_rules.yaml sketch:` 에 있고, 사건마다 바꾸지 않습니다(C0).

## ⑤ 실행

순서대로 돌리고, 종료 코드 ≠ 0 이면 멈춥니다. 메시지 앞의 SK-ID 로 `docs/handoff/22` §3 검사표를 보고 spec 을 고칩니다.

```bash
python -m sketch.missile projects/<pid> --check                      # 1. 검사만(렌더 없음). "hard 0" 이어야 함
python -m sketch.missile projects/<pid> --frames 5,27,34             # 2. 3컷 정지 화면(480p) — out/sketch_2d_*.png 를 직접 본다
python -m sketch.missile projects/<pid> --res final                  # 3. 2D 전편(720p) → out/sketch_2d.mp4 · sketch_2d_sheet.jpg
python -m sketch.missile projects/<pid> --globe --res final          # 4. 3D 전환편(globe 블록이 있을 때) → out/sketch_globe.mp4 · sketch_globe_sheet.jpg
```

- 2 단계에서 라벨 잘림·겹침·빈 화면이 보이면 spec 의 위치(`label_at`·`at`·`side`)나 숏을 고칩니다.
- 렌더마다 `out/sketch_provenance.json` 이 새로 쓰입니다. 2D·3D 둘 다 남기려면 2D 뒤 provenance 를 `out/sketch_provenance_2d.json` 으로 복사합니다.
- 확인할 것: provenance `checks.hard` 가 빈 목록, `numbers_shown` 이 발표값뿐, `numbers_computed` 는 수평선 패널(3D) 값뿐입니다.

## ⑥ 사용자 전달물

- `out/sketch_2d.mp4`·`out/sketch_globe.mp4`(있으면). mp4 는 커밋하지 않습니다.
- 컨택트 시트 `out/sketch_2d_sheet.jpg`·`out/sketch_globe_sheet.jpg`.
- `out/sketch_provenance.json`(검사 결과·쓴 숫자·데이터 파일 sha1·근사 목록).
- 사용자 확정 대기 목록: `docs/handoff/22` §6 링크 + 이번 사건에서 새로 생긴 항목.
- 출처 목록: spec `sources[]` 그대로.

## ⑦ 금지 · 한계

- 코드·규칙 파일을 고치지 않습니다. 막히면 그 지점을 보고합니다(스킬 결함 또는 일반화 결함).
- 계산한 거리·시간·고도를 화면에 쓰지 않습니다(수평선 패널의 기하 계산만 예외, D136).
- 사실 장면을 AI 로 생성하지 않습니다. 도해는 권리가 분명한 실자료만 씁니다(C9).
- 본편 요소가 아닙니다. 본편 등록 후보와 필요한 설계 결정은 `docs/handoff/22` §7 에 있습니다.
