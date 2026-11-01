---
id: D-0600
from: fable
to: opus
kind: directive
responds_to: [D-0337, D-0307]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 착수 지침 — 전쟁사 트랙(E9) W1~W4. 정본 = D-0337(사용자 결정)·D-0307(계획). 미술·기록·사진·영상이 주된 화면 재료

## §0 근거(요지 — 원문은 두 D 파일)
- **사용자 원문(2026-11-01, UF-206)**: "전쟁사는 별도 트랙으로 감독과 구현 세션 띄워서 진행하고, 전쟁사 세션에서는 아주아주 적극적으로 미술사와 연관시키고 미술 작품이나 인물 사진, 전쟁사적 기록과 사진을 캐입시키게 만들어. 즉 과거 전쟁은 미술과 기록, 현대 전쟁은 사진과 영상과 기록을 적극적으로 보여주는거야."
- **UF-150**(2026-10-30 원문): "고대나 과거 전쟁사 같은 경우에는 진영이나 인물에 대한 묘사도 중요한데 그에 못지 않게 해당 시점을 묘사한 고대 미술사적 자료나, 유적지, 지역에 대한 유래에 대한 정보를 제공하는게 못지 않게 중요해."
- D-0307 §2(부호 세트·EraDate·수치 정직성·시대별 기반 지도·전술 무대) · §3(증거 층 셋 period_art·site·toponymy) · §4(서술·음악) · §5(순서)는 그대로 유효하다. D-0337 §1 이 그 위에 **강도**를 얹는다: 증거 층은 "영상마다 ≥1" 이 아니라 **주된 화면 재료**다. 지도·전술 무대는 뼈대, 미술·기록·사진·영상은 살.
- 첫 사례 = **칸나이(기원전 216년 8월 2일, 제2차 포에니 전쟁)**. 둘째 = **인천 상륙과 서울 수복(1950.9.15~9.28, 크로마이트 작전)** — 감독 결정(DECISIONS D700). 근거: 미 연방정부 사진·필름(NARA·해군·해병대)이 PD 라 권리가 깨끗하고 양이 많다, 유엔 공문서(안보리 결의 82·83·84)가 기록 층을 채운다, 한국 시청자에게 지명·지형이 익숙하다, 작전 지도(상륙 → 김포 → 한강 → 서울)와 전술 무대(월미도·적색·청색 해안, 조수)가 한 좌표계에 들어간다. 대안으로 검토한 노르망디(권리는 깨끗하나 한국 연관 약함)·스탈린그라드(소련 측 사진 권리 불명)는 기각.

## §1 운영
- 브랜치 **`claude/war-history-2026`**(sweet-galileo 919b16f7 에서 분기, 이미 push). artifacts 브랜치 **`artifacts/war-history-v7.4.0`**(중국 트랙 `artifacts/china-export-controls-v7.4.0` 과 같은 꼴: README·VERSION·`<pid>/MD5SUMS`).
- 번호: 감독 D 파일 **D-0600~0699**(넘으면 D-0900~), DECISIONS 행 **D700~**(감독이 적는다), UF **UF-250~299**(감독이 적는다). R 번호는 `python back_and_forth/check.py --me opus --next-name <slug>` 가 준다. R 의 `to: fable`, 보고는 `send_message` 로 **감독 세션 `session_017Yuw8i7EwyZ4z45Xtcvjkg`** 에.
- 커밋 첫 줄 `v7.4.0: …`(VERSION 과 일치, hook). 한 커밋 한 의도. 커밋마다 `git push -u origin claude/war-history-2026`(거부 시 `pull --rebase`, force 금지). 트레일러는 세션 안내의 것. 모델 식별자를 저장소 산출물에 적지 않는다(트레일러 제외).
- **금지**: PR 생성, main push, 게이트 장치 우회(`require_animatic`·`require_feedback_guards`), 조용한 드롭·폴백(P6), 표준 음성 재질문(C0.2), 레퍼런스 조판 이식(LLM-AP-022 — 느낌만), D 파일 수정, 쇼케이스·경제·이란·중국 트랙 브랜치 변경.
- 검증(C8.3·D187): 변경마다 타깃 테스트 + `tests/anti_inertia` + 영향 테마 골든(dark 25컷). 전체 pytest 는 하루 1회·병합 직전. 보고문·원고·화면 문자열은 `python tools/slop_check.py` 통과(UF-145·UF-202).
- 결정이 필요하면 혼자 정하지 않고 decision_request R(쟁점·선택지 ≥2·권고·근거·막히는 범위·§7 해당 여부). 막히지 않는 작업은 계속한다. 사용자 판정 자리(§7)는 감독이 사용자에게 직접 보낸다 — 구현 세션은 artifacts 에 올리고 R 로 알린다.
- 네트워크 실측(감독 컨테이너 2026-11-01): `commons.wikimedia.org`·`upload.wikimedia.org` 열림(301), **`en.wikipedia.org`·`pleiades.stoa.org` 막힘**(CONNECT 실패). 구현 컨테이너에서도 같은 네 곳을 `curl -sS -o /dev/null -w '%{http_code}\n'` 로 재고 첫 R 에 적는다. 막힌 자료는 §5 의 우회 경로.

## §2 화면 재료 원칙(D-0337 §1 의 구현 규칙 — 규칙 파일 키로 적는다)
1. **시대별 재료**(`war_history.evidence.by_era`): 고대·근세(사진 이전) = 회화·조각·모자이크·도기·주화·부조·사본 삽화 + 사료 인용(저자·권·절, PD 영역본 locator). 현대(사진 이후) = 당시 사진·필름·보도 영상·공문서 스캔·당시 지도 원본 + 기록(부대 일지·명령서·결의문). 인물 = 초상(회화·흉상·주화·사진).
2. **당대/후대 라벨**(`war_history.period_art.contemporary_gap_years: 150`, 감독 제안 값): `|제작 연대 − 사건 연대| ≤ 150` 이면 "당대 묘사", 넘으면 "후대의 묘사(제작 연대)". 코드가 미디어 레코드의 `created`(EraDate) 와 문장 날짜로 계산해 캡션 바에 붙인다. 라벨 없음 = `[period-art-label-missing]` hard. 동정(同定)이 불확실한 초상은 "…로 추정되는" 을 캡션에 코드가 붙인다(레코드 `identification: {certain, probable, disputed}`).
3. **미술사 한 문장**(`war_history.period_art.art_history_line: true`): 작품마다 작가·연대·소장처·**왜 그렇게 그렸는지**(주문자·정치적 의도·전통) 한 문장을 레코드 `art_history` 에 두고, 원고 LLM 이 그 문장을 내레이션 또는 캡션 두 번째 줄로 쓴다. 전쟁 서사와 미술사 서사가 같은 시간축 위에 놓인다. 출처 없는 해석 금지(레코드 `art_history_source`).
4. **현대 사진·영상**: 기존 장치 그대로 — `media_beats.file_photo_label_required`(자료사진 · 연월), `[clip-date-mismatch]`, `main_subject`(D-0327), `rights_status`. 장르 프로필 `photo_age_check: false`(역사 장르). 촬영자·기록 보관소·식별 번호(예: NARA 111-SC-…)를 레코드 `archive_id` 에 둔다.
5. **권리**: Commons **PD-Art·PD(연방정부)·CC0·CC BY** 만 화면에 쓴다. CC BY-SA 는 참고 작전도 정합(저장 안 함, `references_not_stored`)에만. 사실 장면 AI 생성 금지(C9·G4-10). 자료사진·자료 영상 표기, 엔딩 크레딧에 작품명·소장처·라이선스.
6. **수치·유래**: 병력·사상자 = 사료 귀속(`source_kind: ancient_text`, 저자·권·절 + PD 영역본 url) + 현대 추정 범위 띠(학술 출처). `[casualty-unsourced]` hard. 지명 유래는 출처 + 확신도 `{통설, 이설, 미상}` — 출처 없는 유래는 쓰지 않는다.
7. **밀도**: 증거 층 요소(작품·사진·기록)는 `media.density` 창 안에서 지도 카메라 이동과 번갈아 나온다. 한 번에 튀어나오지 않고 문장 앵커마다 하나(C0 "한꺼번에 튀어나오는 관계선" 금지와 같은 정신). 기준 작품 diesel v2 의 "이야기 안에 박힌 데이터 패널" 자리에 작품·사진이 선다.

## §3 W1 — EraDate(기원전 날짜형). 사용자 판정 없이 진행
- `schemas/era_date.py`(신규, Pydantic v2): `EraDate{astronomical_year:int, month?, day?, precision: Literal[day,month,year,circa,period], calendar: Literal[roman,julian,gregorian,unknown], end?: EraDate}`. 천문 연도(기원전 216 = −215). 문자열 ↔ 모델 파서: 기존 `YYYY`·`YYYY.MM`·`YYYY.MM.DD` 전부 그대로 통과 + 새 꼴 `-YYYY`·`-YYYY.MM`·`-YYYY.MM.DD`·`c.-YYYY`·`c.YYYY`·`-YYYY~-YYYY`·`YYYY~YYYY`(기간).
- 적용 지점(실측 목록 — 전부 EraDate 로): `script/schema.py DATE_RE`·`script/lint.py` 날짜 파서·`engine/checks.py` date hard·`engine/checks.py:2657` 문장 날짜 함수·`engine/primitives/statement_diff.py`·`engine/primitives/site_diagram.py`·HUD 날짜 뱃지 조판·시간축 무대 정렬·`rules script_schema.date_formats`(새 꼴 추가). 한 곳이라도 옛 정규식이 남으면 anti_inertia 테스트가 잡는다(`tests/anti_inertia/test_era_date_single_parser.py` — 저장소에서 `^\d{4}` 류 날짜 정규식 중복 0).
- 뱃지 표기(`rules hud.date_badge.era_format`, 한국어): "기원전 216년 8월 2일" / "기원전 216년" / "기원전 3세기경"(circa 는 세기 단위로 내림) / 기간 "기원전 218~201년". 서기는 지금 표기 그대로. 발음 텍스트(tts)에는 숫자·기호 금지 규칙 그대로(C0) — "기원전 이백십육년".
- 기존 골든(hormuz dark·light 25컷)은 **바이트 동일**이어야 한다(서기 날짜 표기 불변). 테스트: 파서 왕복·정렬(음수 연도 < 양수)·뱃지 문자열·린트.

## §4 W2 — 규칙·장르 프로필·부호 세트·증거 층 스키마. 사용자 판정 없이 진행
- `genres/war_history.yaml`(status `proposed`, `template_label: "전쟁사"`, `photo_age_check: false`, stage primary mercator `theme: dark`(D154 군사 기본), secondary `[tactical]`(W3 등록 전까지 proposed 목록), narration `{define_terms_once: true, etymology_once: true, past_tense: true, fact_sentences_per_min_max: 6}`, media preferred `[period_art, photo, clip, document, site]`).
- `rules/video_rules.yaml war_history:`(새 묶음, 값은 감독 제안 — 바꾸려면 R 에 근거): `symbol_sets {ancient, early_modern, modern}`(고대: 보병 직사각 블록·기병 쐐기·코끼리 점열·진영 색 토큰 2 / 근세: 연대 블록·포병 삼각 / 현대: APP-6 약식 = 현 sketch.campaign 부호), `symbol_set_by_year`(경계: ≤1500 ancient, 1501~1850 early_modern, ≥1851 modern), `[symbol-set-mixed]` hard, `period_art.contemporary_gap_years: 150`, `evidence.required_layers: [period_art|photo, site|document, toponymy]`(시대별 치환: 고대 period_art·site·toponymy / 현대 photo_or_clip·document·toponymy), `[evidence-layer-missing]` hard, `casualty.band_required: true`·`[casualty-unsourced]` hard, `faction_badge`(현대 국기 대신 코드 조판 진영명 + 색 토큰, 휘장 지어내지 않음).
- 스키마: `schemas/media_models.py MediaAsset` 에 optional 필드 `created: EraDate`, `identification`, `art_history`, `art_history_source`, `archive_id`, `work_kind: Literal[painting, sculpture, mosaic, pottery, coin, relief, manuscript, photo, film, document, map]`, `holder`(소장처)·`inventory_no`. 기존 레코드는 무수정 통과(전부 optional). `schemas/data_models.py` 에 `source_kind: ancient_text`(author·work·book·chapter·translation·translation_url·translation_license) + `band`(추정 범위, 학술 출처).
- 레지스트리(P10, 세 곳 동시): media kinds 에 `period_art`·`document` 추가 → 스키마·렌더러(기존 photo 경로 재사용 + 캡션 바 라벨 줄: 당대/후대·추정·미술사 한 문장)·프리뷰 예제. 패널 `evidence_card`(작품/사진 + 라벨 + 한 문장)는 기존 panel 문법으로 만들 수 있으면 새 종류를 만들지 않는다 — 판단을 R 에 적는다.
- 프롬프트: `prompts/` 재생성(P3) + 파리티 테스트. 장르 프롬프트에 §2 원칙(작품마다 미술사 한 문장, 사료 인용 quote, 과거 시제, 지명 유래 1문장).
- 이 단계의 anti_inertia: `[evidence-layer-missing]`·`[period-art-label-missing]`·`[symbol-set-mixed]`·`[casualty-unsourced]` 가 **실제로 실패를 내는** 테스트(UF-150 장치 — 원장 guards 는 감독이 적는다).

## §5 W3 — 고대 지도 수집기·전술 무대(proposed). 사용자 판정 없이 진행
- `tools/fetch_ancient_geo.py`: 고대 지명(Pleiades, CC BY)·해안·속주·로마 가도(AWMC, CC BY). **pleiades.stoa.org 가 막히면** 순서대로 ① GitHub 의 Pleiades/AWMC 공개 데이터 저장소(git 은 프록시로 통한다 — 저장소 이름·커밋·라이선스를 R 에 기록) ② Wikidata/Commons 의 고대 지명 좌표(Pleiades id 를 가진 항목) ③ 그래도 없으면 spec 수동 입력 + 출처 줄(개략 표기). 폴백은 **기록하고** 쓴다(P6 — 조용히 넘어가지 않는다).
- `basemap_era`(rules `geo.basemap_era`): ancient = NE 지형·현대 국경 off·현대 지명 off + 고대 지명·해안·속주 층, modern = 현 NE. 전장 축척 DEM 음영(Copernicus — 이미 쓰는 경로가 있으면 재사용, 없으면 NE 지형으로 두고 R 에 적는다).
- `tactical` 무대(stages `proposed`): 전장 수 km 축척, 부대 블록이 날짜·시각 키프레임으로 움직인다(문장 앵커마다, 한 번에 튀지 않음). 작전 지도 ↔ 전술 무대 전환은 같은 좌표계 확대(카메라 연속, `[camera_continuity]` 그대로). 칸나이: 아우피두스 강(오판토), 로마군 중앙 전진 → 카르타고 중앙 후퇴(초승달) → 양익 기병 → 포위. 인천: 월미도(녹색 해안, 아침 조수) → 적색·청색 해안(저녁 조수) → 김포 → 한강 → 서울. 부대·시각은 사료 귀속(폴리비오스 III·리비우스 XXII / 미 해병대 공간사·NARA 기록) + 개략 표기(SK-H5 와 같은 장치).

## §6 W4 — 스킬 확장 + 스케치 컷(실제 렌더, 목업 금지) → **사용자 판정 ①**
- `.claude/skills/campaign-front-map/SKILL.md` 를 시대 세트·EraDate·증거 층으로 넓힌다(절차만, 코드 없음 — 규칙·스키마는 W2 에서).
- 칸나이 2~3컷 + 인천 2~3컷. 각 사례에 **반드시**: (a) 작전 지도 컷(시대 부호 세트·EraDate 뱃지·고대 기반 지도) (b) 전술 무대 컷(포위/상륙 키프레임) (c) **증거 층 컷** — 칸나이: 당대/후대 라벨이 붙은 작품(예: 카르타고 주화의 코끼리·한니발 추정 흉상·후대 역사화)과 미술사 한 문장, 폴리비오스 인용 quote / 인천: NARA 사진(자료사진 · 1950.9, archive_id)·필름 액자·유엔 결의 문서 스캔 + 기록 한 문장.
- 작품·사진·기록은 **구현 세션이 Commons 에서 권리 확인해 고른다**(감독은 후보만 언급했고 사실을 확정하지 않았다). 레코드에 소장처·소장번호·제작 연대·재질·라이선스·사진 출처를 넣고 `tools/asset_library.py check` 0.
- 렌더는 실제 엔진(`sketch.campaign` 확장 또는 `engine.render --preview`) 480p. artifacts `war_history/sketch_v1/`(png·sheet·provenance·RIGHTS). R 에 컷마다 "이 컷이 보여 주는 규칙 키" 표. 감독이 SendUserFile 로 사용자에게 보낸다. **승인 전 W5·W6 착수 금지**(승인 뒤 W5 디자인 시트 `tools/design_sheet.py war_history` → W6 칸나이 W0).

## §7 사용자 판정 자리(네 곳 — 감독이 보낸다, 구현은 artifacts + R)
① W4 스케치 컷 ② 칸나이 원고 gate-view(게이트 ①) ③ 콘티 판 ④ 게이트 ② 프리뷰 시트. 그 밖은 감독 전결(README §6.4·§7). 사용자 의견은 감독이 UF-250~ 로 즉시 기록(C12).

## §8 첫 R 에 넣을 것
네트워크 실측 4곳 · 컨테이너 준비(pip·ffmpeg·fonts·fetch_data ne/fonts/supertonic/mms_fa·geo.prep) · W1 착수 커밋 해시 · 예상 결정 요청 목록(BGM Musopen PD 후보는 D-0307 §4 대로 별도 decision_request).
