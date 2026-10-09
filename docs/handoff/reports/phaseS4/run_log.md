<!--
tier: 3
last_synced_with: v5.10.0
ssot_for: [phaseS4-run-log]
depends_on: [back_and_forth/261010_015352_D0147_fable_review-s3-pass-s4-directive.md, back_and_forth/261010_022054_D0148_fable_decision-stamp-mask-box-v2digit-minor.md, back_and_forth/261010_024124_D0149_fable_decision-cold-test-event-unannounced-sk-h1.md, docs/handoff/22_SKETCH_TRACK.md, .claude/skills/missile-event-map/SKILL.md, .claude/skills/campaign-front-map/SKILL.md, tests/test_sketch_integration.py]
last_review: 2026-10-10
-->

# Phase S4 실행 기록 — 스킬·문서·통합 (v5.10.0)

이 단계의 지침은 D-0147 §S4 입니다. 결정은 D-0148(도장 가림 상자)과 D-0149(콜드 테스트 사건·미발표 사건·SK-H1 시계)입니다.
사용자 확정 대기 목록은 여기에 다시 쓰지 않습니다. `docs/handoff/22` §6 이 정본입니다.

## 0. 컨테이너

S0~S3 와 같은 컨테이너를 썼습니다(`FONTCONFIG_FILE` 표준 설정, S0 §0.2 자산).
콜드 테스트 프로젝트의 지형은 `python -m geo.prep` 두 해상도로 새로 만들었습니다. EEZ 와 지구본 텍스처는 SKILL ③ 의 재사용 조건대로 d1 것을 썼습니다.

## 1. 변경 요약

| 항목 | 결과 |
|---|---|
| SKILL.md 두 개(§8 ①~⑦) | 수집 체크리스트 표, 준비 명령 순서(EEZ·텍스처 재사용 조건), spec 규칙(22 링크), 실행, 전달물, 한계. 코드 없음. 콜드 테스트로 세 번 고침(§3) |
| 미디어 카드 선택 | 이미 선택이었습니다. `card`·`media` 를 뺀 d1 사본이 `--check`·2D·3D 프레임을 통과합니다. 코드 변경 없음, 통합 테스트로 고정 |
| `docs/handoff/22_SKETCH_TRACK.md` | 계층 결정 D128~D144, spec 계약, 검사표, 출처·권리, 재현, 사용자 확정 대기, 본편 등록 후보 |
| 삭제(P2) | `projects/d1_missile_sketch/CONVENTIONS.md`(→ 22 §2.3~§2.6). 코드 주석의 참조를 22 §2.x 로 바꿈 |
| 헌법·색인 | `CLAUDE.md` C7 한 행, `docs/handoff/19` §3 3.19, `00_INDEX` 한 줄 |
| SK-H1 시계 원천(D-0149 3-3) | `track.flight_sec` = announced sec(없으면 min × 60), 아니면 hard. provenance `numbers_shown` 에 `track.flight_sec ← 원천` |
| SK-E1·apex_label(D-0150 마감) | 엔딩 자료 줄 수·폭 hard(미사일·전황), 고도 단면 정점 라벨 포맷터 경유, 22 §1·§3·§7 |
| 도장 가림 상자(D-0148) | hormuz 기준선 `stamp_box` 를 `v99.99.99` 폭으로, `md5_masked` 재등재, 재발 방지 테스트, PIPELINE-AP-021 |
| 도시 검산(D-0147 R-0183 A) | v5.9.0 마지막 커밋 a95f833 |

## 2. 통합 테스트(`tests/test_sketch_integration.py`, 7개)

| 테스트 | 내용 |
|---|---|
| `test_2d_frames` | d1 사본 `--check` 0 → `--frames 5,27,34` 3장(854×480) → provenance 키·hard 0·numbers_shown |
| `test_globe_frames` | `--globe` 같은 경로, SK-H6 실행·numbers_computed 있음 |
| `test_card_is_optional` | `card`·`media` 를 뺀 사본 통과, 카드 그리기 0·media 데이터 파일 0 |
| `test_broken_spec_writes_nothing` | SK-H2 위반 사본 → 종료 ≠ 0, 프레임 0, provenance 없음(P6) |
| `test_campaign_frames` | uranus 사본 3장, G1·G2·G3·H5 실행, warning = SK-G2(+ 51초 SK-C2) |
| `test_deterministic_frames` | 같은 입력 2회 → 같은 파일 이름·md5 |
| `test_frontmatter_and_sections` | 두 스킬 머리말 `name`·`description`, 본문 ①~⑦ 순서, 22 링크, 코드 블록 없음 |

자산이 있는 이 환경에서 **skip 0** 입니다(`pytest -rs` 기록 §5).

## 3. 스킬 콜드 테스트(D-0147 §4)

매 회차 새 하위 에이전트에게 `missile-event-map/SKILL.md` 만 주었습니다. 회차마다 `git diff --stat -- sketch rules schemas tests .claude engine` = 0 이었습니다.

### 1회차 — 2023-04-13 화성-18형(첫 발사)

두 기관 모두 정점·비행 시간·착탄 기준점을 발표하지 않았습니다. 사실 spec 은 `track.flight_sec` 필수에서 SK-SPEC 으로 실패했습니다(`cold_r1/sketch_20230413_faithful.yaml`).
→ R-0186 → D-0149: 이런 사건은 스킬 범위 밖(D143)이고, 2회차 사건은 2023-07-12 로 정했습니다.

| # | 막힌 지점 | 고친 문장 / 조치 |
|---|---|---|
| 1 | 비행 시간 미발표, 필드 필수 | ① "정점·비행 시간·착탄 기준점 중 하나라도 두 기관 모두 미발표면 쓰지 않고 표로 보고"(D143) |
| 2 | 정점 미발표 → profile·globe 불가 | 같은 문단. 22 §7 에 "미발표 수치 사건 표현" 등록 후보 |
| 3 | 착탄 기준점·방위 미발표 | 같은 문단(개념값으로 채우지 않음) |
| 4 | `eez.pulse` 가 EEZ 밖 착탄을 강조 | ④ "착탄이 그 나라 EEZ 안일 때만" |
| 5 | Commons 검색 빈 출력, 도구 `allowed` 표시 혼동 | ③-5 "`allowed` 는 인물·휘장용, 스케치 기준은 `rights.allowed_licenses`", 검색어 여러 개 |
| 6 | 지어낸 비행 시간·정점이 hard 0 통과(진단 사본, 저장소 밖) | SK-H1 시계 원천 검사(D144) + ② "announced 값마다 출처 1건 이상" |
| 7 | `.gitignore` 의 d1 도해 예외 줄 | ③-1 "도해 예외 줄은 지운다" |

### 2회차 — 2023-07-12 화성-18형(두 번째 발사)

모든 단계 종료 0, `--check` hard 0. 산출은 `projects/missile_20230712_sketch/`(spec 커밋, mp4 미커밋), 시트 `cold_missile_sheet.jpg`·`cold_globe_sheet.jpg`, provenance `cold_r2/` 입니다.

| 단계 | 결과 |
|---|---|
| `--check` | 0, hard 0 · warning 0 |
| `--frames 5,27,34` | 0(27초 SK-C2 warning 1프레임) |
| `--res final` 2D | 0, `sketch_2d.mp4` 14,133,965 B, md5 `65b21db15386861556ed46b856a2ced4`(2회차 원본 — 엔딩 6줄 겹침). D-0150 뒤 5줄로 고쳐 다시 렌더: 14,135,698 B, md5 `965975bb83271d298272353012cfaf39`, provenance ran 에 SK-E1 |
| `--globe --res final` | 0, `sketch_globe.mp4` 2,751,204 B, md5 `0b4b0c17bcf084cfb1de80434155e708` |
| provenance 2D | hard 0, warning SK-C2(471프레임 21.12~55.96초). 시계 `track.flight_sec ← mod.flight_min×60` = "+74:00" |
| provenance 3D | hard 0, warning 0. `numbers_computed` = 수평선 패널 3자산 |

사실(출처 `sources[]`):
- 합참: "평양 일대" 10시경, 고각, 약 1,000km 비행 후 동해상 탄착(뉴시스 2023.07.12).
- 일본 방위성: 9시 59분경, 약 74분 비행, 약 1,000km, 정점 약 6,000km 초과, 오쿠시리섬 서쪽 약 250km, 일본 EEZ 밖.

| # | 막힌 지점(진행은 막지 않음) | 고친 문장 / 조치 |
|---|---|---|
| 1 | 정점 "초과"(하한 발표) 표기 방법 없음 | ② "자리표시 뒤에 '초과'·'이상', 곡선은 개념 — 사용자 확정 대기" |
| 2 | 합참이 거리만 발표 → 패널 1줄 대 3줄 | ② "한 기관만 발표한 값은 그 기관 줄에만, 채우지 않음" |
| 3 | 방위성 1차 페이지 403 | ② "인용 보도로 확인, `sources[]` 에 인용 경로" |
| 4 | Commons 429 뒤 빈 출력 = 후보 없음과 구분 안 됨 | ③-5 "429 가 보였으면 한 번 재시도, 그래도 비면 '제한으로 확인 못 함'" |
| 5 | 도해 없을 때 RIGHTS.json 여부 | ③-5 "media 폴더·RIGHTS.json 만들지 않음" |
| 6 | 발사 라벨 위치 필드 없음 → "평양직할시" 와 겹침 | ④ "좌표를 옮기지 않고 확인 항목으로 보고"(코드 일반화 후보, 아래 §4) |
| 7 | 엔딩 자료 긴 줄이 화면 밖(검사 없음) | ④ "한 줄 짧게, 기관별로 나눔", ⑤ "시트 마지막 컷 확인"(검사 후보, §4) |
| 8 | SK-C2 허용 여부 | ⑤ "warning 은 막지 않음, 시각을 전달물에 적음" |

### 3회차 — 2023-07-12 검증(같은 사건, `--check`·3컷까지)

2회차 결함을 고친 SKILL 로 새 에이전트가 같은 사건을 처음부터 만들었습니다(②~④, ⑤ 1·2단계 + `--globe --check`). spec 은 `cold_r3/sketch_20230712_r3.yaml` 이고, 프로젝트 폴더는 지웠습니다.

| 단계 | 결과 |
|---|---|
| `geo.prep` 두 해상도 | 0 |
| `--check` / `--globe --check` | 0 / 0, hard 0 · warning 0 |
| `--frames 5,27,34` | 0, warning SK-C2 1프레임(27초). `numbers_shown` = 발표값 + 시계 `track.flight_sec ← mod.flight_min×60` |

2회차에서 고친 8건(하한 표기·한 기관 값·403 인용·429·media 생략·발사 라벨·엔딩 줄·SK-C2)은 다시 막히지 않았습니다. 새로 나온 3건은 아래와 같습니다.

| # | 막힌 지점(진행은 막지 않음) | 고친 문장 |
|---|---|---|
| 1 | 2회차에 넣은 "`profile.apex_label` 에도 '초과'" 가 틀림 — `apex_label` 은 자리표시를 채우지 않는 글자 | ② "`profile.apex_label` 은 숫자 없이 둔다('정점')" |
| 2 | 도해 없을 때 `.gitignore` 의 `media/*` 줄 | ③-1 "도해를 쓰지 않으면 그 줄도 지운다" |
| 3 | 숏 중심을 옮길 기준 없음 | ④ "`--frames <track.t1>` 에서 발사점·착탄 영역·기준점이 화면 안이면 유지, 밖이면 마지막 숏·`globe.center` 를 옮김" |

회차 상한(3회)에 닿아 4회차는 돌리지 않았습니다. 3회차 문장 수정은 위 표가 기록입니다.

### Fable 회차 — 2024-10-31 화성-19형(D-0150, `cold_fable/`)

Fable 이 SKILL 만으로 `projects/missile_20241031_sketch/` 를 만들었습니다. 코드 수정은 0 이고, hard 0 으로 2D·3D 전편까지 나왔습니다.
출처 줄을 6개 쓰자 6번째 줄이 맺음 줄과 포개졌는데, 검사가 없어 통과한 것이 발견됐습니다. 그래서 SK-E1 을 더했습니다(D145).

### 마감 커밋(D-0150) 뒤 2회차 프로젝트

- SK-E1 이 2회차 spec(`missile_20230712_sketch`, 출처 6줄)에서도 같은 겹침을 잡았습니다. 2회차 시트 엔딩 컷에서 6번째 줄이 맺음 줄과 겹쳐 보였던 것이 그것입니다.
- 방위성 두 줄을 한 줄로 합쳐 5줄로 맞췄습니다(폭 검사도 통과하게 괄호 출처를 줄임). `--check`·`--globe --check` hard 0 입니다.
- 2D 전편을 다시 렌더해 `cold_missile_sheet.jpg`·`cold_r2/sketch_provenance_2d.json` 을 바꿨습니다(md5 아래 §3 갱신). 3D 편은 엔딩 자료가 없어 그대로입니다.
- SK-E1 판정은 "`y0` + 줄 수·`dy` > `end_note.y`"(초과)로 했습니다. D-0150 문구의 "≥" 로 하면 d1 의 5줄(200 + 5 × 20 = 300 = `end_note.y`)이 걸립니다. 5줄의 마지막 기준선은 280 이고 맺음 줄과 한 줄 간격이 정확히 남으므로, 등호는 통과로 두었습니다.

## 4. 콜드 테스트가 드러낸 코드 쪽 후보(이번 범위에서 고치지 않음)

- `launch` 라벨 위치 필드(`label_at`/`side`)가 없어 배경 도시 라벨과 겹칠 때 피할 수 없습니다. spec 필드 추가는 화면 문법 변경이라 22 §7 후보입니다.
- 엔딩 자료 줄 넘침 검사가 없었습니다 → **D-0150 으로 SK-E1 추가(해결)**.
- 3D 레이더 라벨 `{sensor.range_plain}` 은 '약' 없이 나옵니다(d1 검토본 그대로).
- `profile.apex_label` 이 `nums.fill` 을 거치지 않았습니다 → **D-0150 으로 포맷터 경유(해결)**. d1 은 "정점" 이라 화면이 같습니다(48초 컷 0.000 %).
- `launch` 라벨 위치 필드, SK-C2 메시지의 두 상자 이름, 3D '약' 표기는 22 §7 등록 후보로 올렸습니다(D-0150).

## 5. 테스트

`FONTCONFIG_FILE` 표준 설정과 S0 §0.2 자산으로 돌렸습니다.

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S3 끝(R-0183 반영 전) | 1378 | 0 | 0 | 0 |
| S4 끝(a925a83 — 뒤 커밋은 SKILL 문장·프로젝트 데이터·보고뿐) | **1390** | **0** | **0** | 0 |

| 더한 테스트 | 수 |
|---|---|
| 도시 검산(v5.9.0, D-0147) | 1 |
| 통합(`test_sketch_integration.py`) | 7 |
| 도장 가림 상자 재발 방지(D-0148) | 1 |
| SK-H1 시계 원천(D-0149) | 3 |
| SK-E1 엔딩 자료(D-0150) | 3 |
| `profile.apex_label` 포맷터(D-0150) | 1 |
| 삭제 | 0 |

기준은 1378 + 12 = 1390 이고, 실측 1390 passed(23분 30초)입니다. `-rs` 출력에 SKIPPED 줄이 없습니다 — **skip 0**.

D-0150 마감 커밋 뒤: 1390 + 4(SK-E1 3, apex_label 1) = **1394 passed · failed 0 · skip 0**(22분 44초, `-rs` 에 SKIPPED 없음).

## 6. 기준 프레임 재대조(S4 끝)

d449c25 에서 `--res final` 로 다시 그려 검토본 기준 프레임과 대조했습니다.

| 기준 | 컷 | 다른 픽셀 비율 |
|---|---|---|
| S1 미사일 2D(phaseS1/ref) | 9 | 전부 0.000 % |
| S2 3D(phaseS2/ref) | 7 | 1.0·4.5·6.5·9.0 = 0.000 %, 12.5·15.0·17.5 = 0.987·0.985·0.989 %(S2 결함 수정 그대로 — S2 run_log 와 같은 값) |
| S3 전황(phaseS3/ref) | 7 | 전부 0.000 % |

`git diff --stat 7b607b1..HEAD -- engine` = 0 입니다.

D-0150 마감 커밋 뒤 1컷씩 다시 대조했습니다. d1 48.0초(고도 단면 정점 라벨 포함)와 uranus 55.5초(엔딩 자료) 모두 0.000 % 입니다.
