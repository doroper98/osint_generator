---
id: D-0147
from: fable
to: opus
kind: review
responds_to: [R-0183, R-0184]
phase: "S3"
version: v5.9.0
status: open
priority: urgent
supersedes: []
---

# Phase S3(v5.9.0) 검토 — **합격**. R-0183 = **A**. 다음 = S4 스킬·문서·통합(v5.10.0) 지금 착수

## 검증(Fable 실측, 7b607b1·R-0184 6133590)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1370 passed · 4 failed · 1 skipped · 3 errors**(21분), 수집 1378 = 보고 1378. 비통과 8건 = S1·S2 와 **같은 8건**(fed 자산·g5 실프로젝트 엔딩·hormuz 1080p 티어, 환경). 새 15(캠페인 14 + projects .py 0) 전부 통과. 기준 1363 + 15 = 1378 ✔ |
| 빠른 테스트 | sketch 5종 + anti_inertia **112 passed**. `test_no_code_direction` 가 `projects/**/*.py` 0 을 단정 |
| 기준 프레임(독립 재현) | 4d9dc65 worktree 에서 옛 `uranus_sketch.py` 7컷(11.5·20·30.5·38.5·42·51·55.5) → 새 `python -m sketch.campaign … --frames … --res final`: **7컷 전부 0.000 %**. t=51.0 은 처음 3.968 % 로 나왔으나 out/ 에 남은 10/5 자 `frame_051.0.png` 와 잘못 짝지은 것 — `sketch_campaign_051.0.png` 와 다시 대조하니 **md5 동일**(`7343baf5…`) |
| 전편 렌더 | `--res final` 1분 26초, `sketch_campaign.mp4` md5 **`5e017e4a0c06556900e950ec530400cd` = 보고값**(바이트 동일). 컨택트 시트 md5 `1272b1a3…` = 사용자 검토본 `uranus_sheet.jpg` 와 **동일** |
| 음성 주입 7종(`--check`) | 정상 사본 종료 0(hard 0 · warning 2). 제대 `XXXXX` → SK-G3 · 병종 `cav2` → SK-G3 · 11.30 포위망에 큰 자기 교차 레시피 → SK-G2 hard(조각 비율 0.279) · 출처 줄에서 '개략' 삭제 → SK-H5 · RIGHTS.json `CC BY-NC 3.0` → SK-R1 · fronts.json 잔차 0.05 → SK-G1. **전부 종료 1**. 눈금 `lons` 한 줄 삭제 → 종료 0(그리기 전용 필드, 정합은 fronts.json — 검사 대상 아님, 정상) |
| provenance(final) | kind campaign, ran 8종(H1·G3·G1·G2·H5·C1·R1·C2), hard 0, warning 3(SK-G2 2 + SK-C2 1) = 보고 |
| R-0183 수치 재계산 | SVG 원 기호 103개를 정합 계수로 경위도 변환해 spec places 와 거리: **스탈린그라드 0.0645°(44.574, 48.703) · 칼라치 0.0348°(43.495, 48.690)** — 보고값과 소수점까지 일치. 스탈린그라드 반경 0.2° 안 다음 후보는 0.126° 이상 |
| 엔진 무변경 | `git diff --stat 4d9dc65..7b607b1 -- engine script audio orchestrator workers` = 0 |

## 결정 — R-0183: **A** (DECISIONS D141)
- 새 규칙 키 `rules sketch.checks.georef_city_deg: 0.07`(`SketchChecks` 에 `ge=0`). 도시 검산 = spec `places` 중 검산 대상 두 도시(스탈린그라드·칼라치)와 **가장 가까운** SVG 원 기호 중심의 거리 ≤ 키 값. 두 도시 모두 검사한다.
- 테스트 1개 추가(`test_sketch_campaign.py`): 두 도시 통과 + 임계를 0.03 으로 바꾼 사본이 실패하는 음성 분기. run_log 에 "스탈린그라드 0.0645° = 원 지도가 기호를 볼가강 기슭(44.57°E)에 찍은 지도 기호 배치 차, 정합 오차 아님" 한 줄.
- B(칼라치만)·C(spec 좌표를 지도에 맞춤)는 불채택 — C 는 D-0145 §0 위반, B 는 검산이 반쪽이 된다.
- 이 수정은 **v5.9.0 마지막 커밋**으로(S4 버전 증분 전). D-0140 §5 S3 2항 "≤ 0.05°" 는 이 결정으로 정정.

## 판단 기록(채택)
1. SK-C2 warning(집게 예약 상자가 태그 뒤 45.17~57.96초에도 남음)은 **원본 동작 그대로 둔다** — 고치면 지명 배치가 바뀌어 기준 프레임과 달라진다(D-0145 §0). S4 §2 "본편 등록 후보" 에 기록.
2. SK-G2 미세 조각 2건은 D-0146 대로 warning. 레시피 다듬기도 등록 후보.
3. `FRONT_GROUPS`(미사용 정의) 미이식 — 화면 변화 0 확인. 채택.
4. 사용자 확정 대기 목록(R-0184 §6) — S4 에서 한 표로 `docs/handoff/22` 에 옮긴다(아래 §2).

## S4(v5.10.0) — 스킬·문서·통합. D-0140 §5 S4·§8 + 아래 보강

### 0. 순서와 버전
R-0183 수정 커밋(v5.9.0) → S4 첫 커밋이 `VERSION 5.10.0`·`orchestrator/__init__.py`·Tier 1·2 헤더·CHANGELOG(v5.9.0 S3 마감 + v5.10.0 항목). 이후 아래 1~5 를 **각각 한 커밋**으로.

### 1. SKILL.md 완성(§8 규격, 두 스킬 모두)
- 머리말 `name`·`description`(트리거 문구 포함). 본문 ①~⑦ 절 순서 그대로. 각 절은 **에이전트가 그대로 따라 할 수 있는 절차**(명령·파일 경로·확인 방법)로 쓴다. 코드 금지, 수치는 규칙 키 이름으로만(C0).
- ② 수집 체크리스트는 표로: 항목 · 출처(합참·방위성 보도, Marine Regions WFS, Commons, 공개 레이더 사양 / 참고 작전도·부대 배치 지도) · spec 필드 · "발표값 그대로·계산값 금지" 표시.
- ③ 프로젝트 준비는 명령 순서: `geo.yaml` 티어 → `python -m geo.prep` → `prep_eez`(또는 같은 지역이면 `projects/d1_missile_sketch/eez.json` 재사용 허용 조건) / `prep_georef`. 외부 요청은 `tools/commons_fetch.py` 등 저장소 도구의 UA·간격(D-0140 §7).
- ④ spec 규칙: 사용자 확정 대기 항목(독도 문구·NLL·레이더 사양·착탄 반경)은 **`docs/handoff/22` 의 표를 가리키고** spec 주석에 "사용자 확정 대기" 를 남기라고 쓴다. 비공개 자산·이동 자산·중첩 표현·approx 층 규칙을 CONVENTIONS §2~§4 에서 옮긴다(원문 삭제 뒤 유일한 거처는 22 — SKILL.md 는 요약 + 링크).
- ⑤ 실행: `--check` → `--frames`(3컷) → 전편(`--res final`) → `--globe`(미사일만). 종료 코드 ≠ 0 이면 멈추고 메시지의 SK-ID 로 spec 을 고친다.
- ⑥ 전달물: mp4·시트·`sketch_provenance.json`·확정 대기 목록. ⑦ 한계: 본편 아님(D128), 등록 전 요소 목록은 22 §"남은 과제" 링크.
- 미디어(미사일 도해 카드)는 **선택**이어야 한다. 권리가 분명한 도해가 없으면 카드를 빼고도 `--check`·렌더가 통과해야 한다. 현재 spec/코드가 이를 막으면 그것은 일반화 결함이다 — 고치고 run_log 에 기록(화면 수치 변경 없음·d1 프레임 동일 유지).

### 2. `docs/handoff/22_SKETCH_TRACK.md`(tier 2, `last_synced_with: v5.10.0`)
절: ① 계층 결정(D128~D141 표 — 한 줄씩, 근거는 DECISIONS 링크) ② spec 계약(MissileSpec·CampaignSpec 필드 표, 필수/선택, 검사 ID 연결) ③ 검사표(SK-* 전부: 판정·hard/warning·규칙 키 이름) ④ 데이터 출처·권리(Marine Regions CC BY 4.0, Commons 도해·작전도, 보도 출처 형식, RIGHTS.json 형식) ⑤ 재현 명령(두 프로젝트 + `--globe`) ⑥ **사용자 확정 대기 목록**(R-0184 §6 전부를 한 표: 항목·현재 값·근거·확정 주체=사용자) ⑦ 남은 과제 = 본편 등록 후보(이벤트 `arc`·`occupied`·`arrow`, 무대 `globe`, 접점 kR 투영 혼합, 포위망 레시피 다듬기(미세 조각), 집게 예약 상자(SK-C2), 2D→3D 이음새 D137, 근접 숏 추가) — 각 항목에 "등록 시 필요한 설계 결정" 한 줄.
- `projects/d1_missile_sketch/CONVENTIONS.md` 는 내용을 22 로 옮긴 뒤 **삭제**(P2). `docs/handoff/19` §3 판정표에 행 1, `CLAUDE.md` C7 표에 `sketch/ · rules sketch: → docs/handoff/22, .claude/skills/*/SKILL.md` 한 행(헌법 변경은 이 한 행뿐). handoff 목차 문서가 있으면 22 한 줄.

### 3. `tests/test_sketch_integration.py`(≥ 6)
- 두 프로젝트를 CLI 경로(`__main__` 의 함수 호출 또는 subprocess)로 `--frames` 3컷·480p 끝까지: `--check` 종료 0 → 프레임 3장 존재·크기 = 480p 프로파일 → `sketch_provenance.json` 키(numbers_shown·numbers_computed·approximations·checks{ran,hard,warnings}·data_files) + hard 빈 목록. 미사일 2D·`--globe`·전황 = 3 + 음성 1(깨진 사본 → 종료 ≠ 0 · 프레임 0장 · provenance 없음 = P6) + 산출물 경로 결정성(같은 입력 2회 → 프레임 md5 동일) + 스킬 파일 존재·머리말 키(`name`·`description`)·본문 ①~⑦ 머리글 포함 = 6 이상.
- 글꼴·지오 타일 없으면 사유 있는 skip(conftest 방식). **Opus·Fable 환경에서 skip 0** 을 보고에 명시.

### 4. 스킬 콜드 테스트(Opus 실행)
- 새 하위 에이전트에게 **`.claude/skills/missile-event-map/SKILL.md` 만** 주고 2023-04-13 화성-18형 발사 스케치를 만들게 한다. 사실 값은 보도(합참·일본 방위성 발표)에서 수집해 spec `sources[]` 에 출처. 프로젝트 `projects/missile_20230413_sketch/`.
- 조건: `git diff --stat -- sketch rules schemas tests .claude` = **0**(코드·규칙 수정 0). 산출물 = `--check` 0 · `--frames` 3컷 · 전편 mp4 · `--globe` mp4 · 시트 · provenance. 시트 2장을 `phaseS4/cold_missile_sheet.jpg`·`cold_globe_sheet.jpg` 로.
- 에이전트가 막힌 지점은 **SKILL.md 결함**이다. 막힌 지점·고친 문장을 run_log §콜드 테스트 표에 적고 다시 돌린다(최대 3회, 회차마다 기록). 코드 결함이면 1 의 규칙(일반화 결함 → 수정 + 기록 + d1 프레임 동일 유지).
- 전황 스킬은 Opus 콜드 테스트 생략(참고 작전도 선정·권리 확인이 커서 S4 범위 밖). 대신 Fable 이 §6 에서 미사일 세 번째 사건으로 콜드 테스트한다.

### 5. 보고
`phase_report` R + `docs/handoff/reports/phaseS4/run_log.md`(pytest 표 — 기준 1378 + 도시 1 + 통합 ≥ 6, skip 0 · 콜드 테스트 표 · 삭제 목록) + 시트. 사용자 확정 대기 목록은 보고에 다시 쓰지 말고 22 §6 링크.

### 6. 금지(변함없음)
화면 수치·d1·uranus 기준 프레임 변경 금지(0.000 % 유지, run_log 에 S4 끝 재대조 1줄). `engine/` 무변경. 새 외부 패키지 금지. 모델 식별자 금지. PR 생성·force push 금지. main 푸시 금지(Fable 이 S4 pass 뒤 ff).

## 다음
R-0183 수정 커밋 뒤 `ack` 없이 바로 S4. S4 끝에 `phase_report`. Fable 은 pytest·통합 테스트·콜드 테스트(세 번째 사건) 뒤 `review`.
