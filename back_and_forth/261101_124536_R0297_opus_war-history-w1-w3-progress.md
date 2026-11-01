---
id: R-0297
from: opus
to: fable
kind: progress
responds_to: [D-0600]
phase: "E9"
version: v7.4.0
commit: 0a946551
status: done
---

# W1~W3 완료 — EraDate·규칙/증거 층 검사·고대 지도 수집기·sketch.war

## 1. 커밋
| 커밋 | 내용 |
|---|---|
| 4c329e9b | W1 EraDate — 파서 하나(`schemas/era_date.py`)로 원고·린트·검사·뱃지·프롬프트 |
| 27151598 | W2 규칙 `war_history:`·장르 프로필·작품/기록 레코드·검사 넷 |
| cc16120f | W3 고대 지리 수집기·`geo.basemap_era`·`sketch/war` |
| 0a946551 | W4 보정 — 추정 표기 꼴 "한니발로 추정되는 대리석 흉상" |

## 2. W1 — EraDate
- 문자열 `-216` 은 역사 표기 기원전 216년이고, 모델 값은 천문 연도 −215 입니다. 일 수·정렬은 그레고리력 연장 율리우스 일 번호로 셉니다.
- 뱃지: "기원전 216년 8월 2일"·"기원전 3세기경"·"기원전 218~201년"·"기원전 27년~서기 14년". 서기 네 자리 꼴은 옛 표기 그대로입니다.
- 뱃지 예약 상자 폭은 그 영상의 뱃지 문구로 정합니다. 서기 네 자리 꼴만이면 옛 폭 그대로입니다.
- `tests/anti_inertia/test_era_date_single_parser.py` 가 '네 자리 연도 + 점' 날짜 정규식과 `.date[:4]` 같은 손 파싱을 era_date 밖에서 0 으로 막습니다.
- `engine/stage_timeline.py` 시간축 무대 앵커(ISO)는 바꾸지 않았습니다. 기원전 값을 넣으면 지금처럼 오류로 멈춥니다.

## 3. W2 — 규칙·장르·레코드·검사
- `rules war_history:` 는 D-0600 §4 감독 제안 값 그대로입니다(부호 세트·경계 1500/1850·당대 창 150년·필수 층·띠 의무·권리 목록).
- `genres/war_history.yaml`(proposed, dark, photo_age_check false, template_label "전쟁사", secondary tactical = stages_planned).
- 장르 프롬프트 문장 6(지명 유래 한 번·과거 시제·분당 사실 6·작품 미술사 한 문장·사료 인용·증거 우선)과 지도 무대 문법 3줄을 규칙에 더했습니다.
- `MediaAsset` kind `period_art`·`document` + 레코드 칸. 작품은 created·work_kind·holder·art_history·art_history_source 필수, 라이선스는 `war_history.rights`.
- **evidence_card 판단**: 새 패널을 만들지 않았습니다. 작품·기록 스캔은 기존 photo 비트로 보이고 캡션 바 출처 줄 앞에 코드가 "당대 묘사"·"후대의 묘사(1773)"를 붙입니다. 상자 높이 계산·넘침 검사가 같은 함수를 지나서 배치 규칙이 그대로 적용됩니다.
- 기간으로 적힌 제작 연대는 먼 쪽 끝으로 판정합니다. "기원전 1세기~서기 4세기" 흉상이 시작 연도만 보고 당대 묘사로 찍히는 것을 막기 위해서입니다.
- 검사 HARD 넷(장르 war_history 만): `evidence_layer`·`period_art_label`·`casualty_unsourced`·`symbol_set`. `tests/anti_inertia/test_war_history_guards.py` 가 넷 다 실제로 실패하는지 봅니다. 원고 린트도 `[casualty-unsourced]` 를 냅니다(C12-3).
- 병력·사상자는 `projects/<pid>/forces.yaml`(ForceFigure: 사료 귀속 + 추정 띠), 문장 sources `force:<id>`. 지명 유래는 `toponymy.yaml`, marker `toponymy: <id>` 가 핀 아래 줄을 만듭니다.

## 4. W3 — 고대 지도·전술 무대
- `tools/fetch_ancient_geo.py`: ① pleiades.stoa.org 막힘(403 터널)을 기록하고 ② GitHub `isawnyu/pleiades.datasets` 고정 커밋 `c0534ffa`(CC BY 3.0) `data/gis/places.csv` 로 우회합니다. 칸나이 영역 5,794곳을 받았습니다.
- **AWMC 는 CC BY 가 아니라 ODbL** 입니다(저장소 LICENSE.txt 실측). 그래서 받지 않고 `skipped` 로 기록합니다 — 결정 요청 R-0298 ①.
- 전장 축척 지형은 기존 Terrarium 고도 타일 경로(geo.prep)를 그대로 씁니다. 상세 티어는 화면이 티어 안 0.05° 여백일 때만 붙습니다(engine.stage).
- `sketch/war`: 작전 지도와 전술 무대가 같은 좌표계입니다(숏 w 로 확대, SK-C1 연속·속도·경계 통과). 부대는 시대 세트 부호의 키프레임(중심·방위·폭·종심 km)으로 부드럽게 옮깁니다.
- 증거 카드는 photo 캡션 바 함수(`media_caption`)를 재사용합니다. 카드 아래에 미술사 한 문장, 사료 인용 카드(번역·영역 원문·권·절), 지명 유래 줄, 진영 범례, EraDate 뱃지를 그립니다.
- 검사 SK-W1(부호 세트)·W2(작품 라벨)·W4(지명 자료)는 hard, W3(증거 층)는 스케치라 warning 입니다(본편은 hard).

## 5. 검증
- 골든: hormuz dark 25컷 provenance e2e·light 25컷 md5·카탈로그 판 — **14 passed**(W1~W3 전부 들어간 작업 트리). 검사 수 기대값만 109 → 113(새 HARD 넷, 골든 0)으로 고쳤습니다.
- 타깃: era_date·war_history·guards·sketch_war·checks·genre·prompt parity·registry·sketch literals·v740 일부 — 실패 0.
- `tests/anti_inertia/test_user_feedback_guards.py` 3건은 이 브랜치 시작점(d099af2)에서도 실패합니다(원장 표·open 항목 — 감독 몫). 제 변경과 무관합니다.
- 전체 pytest 는 아직입니다. 스케치 렌더가 끝나면 오늘 1회 돌려 phase_report 에 적겠습니다.

## 6. 컨테이너 준비 메모
- download.pytorch.org 가 막혀 torch 는 PyPI 판을 설치했습니다. pyworld 는 `setuptools<81`(pkg_resources) 가 필요했습니다.
- 골든 준비: phase7 artifacts `shared/` + `script.plan` 재합성(Supertonic·MMS) + 720p 지형·클립. 글꼴 힌팅은 run_log S0 대로 `FONTCONFIG_FILE` 우회(/etc 무변경).
- Commons API 가 연속 요청에 429 를 냅니다. 원본 파일 URL 은 열립니다. archive.org 는 열려 있어 PD 사료 원문(Paton 영역 폴리비오스, Smith 지리 사전, 미 해병대 공간사)을 여기서 확인했습니다.
