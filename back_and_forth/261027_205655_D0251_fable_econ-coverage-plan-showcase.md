---
id: D-0251
from: fable
to: opus
kind: directive
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 경제 사안 커버리지 보완 — 계획(E0~E6)과 쇼케이스 데모 2편(지경학·경제)

감독(Fable) 세션 `session_017Yuw8kbxf9Vxri6LoH5Je4`, 브랜치 `claude/sweet-galileo-7yok3b`. 이 문서는 **계획 전체(E0~E6)의 정본**이고,
착수는 단계마다 별도 D 로 낸다. 지금 착수하는 것은 **E0(쇼케이스 데모 2편 + 카탈로그 층)** 하나다. 한 커밋 = 한 의도(C5.5).

## 0. 사용자 결정(2026-10-27, 대화 원문) — DECISIONS D264·D265

- **D264 비공개 시청 전제** — 원문: "어짜피 어딘가에 올릴 영상도 아니고, 나를 위해 니가 가장 풍부한, 사고가능한, 다면적 입체적 정보를
  제공하고 나는 그걸 소화하는 목적으로 작성하는거기 때문에 무단이용에 대한 제한은 없으니 그부분을 너무 강제로 막거나 하지 마."
  → 영상 소스(인터뷰·홍보 영상·방송·팟캐스트 등 저작권 있는 공개 영상)는 길이·용도 제한 없이 쓴다. **권리는 기록만 한다**:
  기존 `scope: private_only`(사용자 결정 D234, 위성 타일)를 클립 전체로 넓힌다. **막는 검사를 새로 달지 않는다.** GOAL G4-8(권리 상태
  미기록 영상 금지)은 그대로 — "기록"으로 충족한다. 공개 전환 때만 provenance `private_only_assets` 목록으로 교체한다.
- **D265 보완 방향 동의** — 원문: "오케이 다 너의 의견에 동의해." 동의 범위: ① 번들 쪽 출처 계약이 0번(agents_reviewer
  `bundle_builder.py` 가 시세 매칭 외 모든 차트에 `sources=[]` 를 고정, `BundleSource.provider` 에 공시 없음, `BundleClaim` 비어 있음)
  ② 공시 데이터 경로는 `press_cited` 선례의 세 번째 분기 ③ 새 시각 요소는 막대 계열(워터폴 포함)과 생키 둘 ④ 영상 소스 적극 활용
  (발언 클립·움직이는 배경·양측 발언 나란히) ⑤ 홍보 영상은 "회사의 주장"으로 출처 줄에 성격 표기(권리가 아니라 정확성, G4-10 CG 구분)
  ⑥ **쇼케이스 데모 2편**(지경학·경제) — "요소·목소리·폰트를 다 담는다, 길이는 자유, 저장소가 커버하는 범위까지만 만든다."

## 1. E0 — 쇼케이스 데모 2편과 카탈로그 층 (지금 착수)

### 1.1 설계 결정(Fable)
- **프로젝트 둘**: `projects/showcase_geo`(genre geopolitics, mercator light) · `projects/showcase_econ`(genre macro_monetary, backdrop + timeline 보조).
  장르 프로필은 프로젝트당 하나, 지도 테마는 영상당 하나(C0)라서 한 프로젝트에 합치지 않는다. 결합본은 두 전편을 ffmpeg concat 한
  `showcase.mp4` 하나(결합은 `tools/` 스크립트, 각 전편 md5 를 README 에 적는다).
- **내용 = 기존 합격 프로젝트의 축약 재구성.** 새 수치·새 사실 없음(G4 출처 없는 수치 금지). 장(章)마다 한 프로젝트의 claims·sources·
  미디어·레코드를 그대로 쓴다. 원고는 새로 쓴다(짧게) → 게이트 ① 필요(사용자).
  - geo: `hormuz_korea`(골든) 1장 + `diesel_road_2026`(v2 합격) 1장 + 필요하면 `dmz_mine_2026`(site_diagram) 1컷. 영상 안 장 전환은 카드 한 장으로 끊는다.
  - econ: `fed_policy_2026`(v16 합격) 축약 1편. 데이터 = `data/series` FEDFUNDS·CPIAUCSL·DFEDTARU·DFEDTARL + fed_policy_2026 의 SEP 점도표 레코드
    (`data/series` 에 SEP 파일이 보이지 않는다 — 위치 확인, 없으면 `tools/fetch_sep.py` 로 재수집하고 레코드로 커밋).
- **길이**: geo 90~120초(문장 18~24), econ 60~90초(문장 12~18). 문장당 요소 2~3개. "한꺼번에 튀어나오는" 등장 금지(C0 되돌리면 안 되는 것).
  사용자 원문 "꼭 1분이 아니어도 된다" — 요소 확인이 목적이다.
- **카탈로그 층(`--catalog`)**: 전편 레이어 전부 + 라벨 층 하나. 콘티 판(D-0108)과 같은 구조로 **별도 산출물**이다.
  - 코드: `engine/layers/catalog.py:CATALOG_LAYERS`(= FULL_LAYERS + catalog_label), `engine/project.py:_layers` 분기, `engine/render.py --catalog`,
    산출 `out/catalog_noaudio.mp4 → out/catalog.mp4`, 미리보기 `prev_catalog/`, provenance `catalog: true`. `engine/mux.py refuse_*` 가 콘티 판과 같은
    mp4 comment 표식으로 **deliver 거부**. `final.mp4` 에는 절대 들어가지 않는다(GOAL 불변 6 "Debug Layer 금지", C0 모서리 규칙은 final 기준).
  - 규칙: `rules/video_rules.yaml catalog:` 신설 — `profile`, `output`, `preset`, `mp4_comment`, `label: {font: mono, size, pos, alpha, line_gap, max_lines}`
    (값은 Opus 가 480p 설계 px 로 제안 → `decision_request`). 상수 금지(P3). 스키마 `schemas/rules_models.py` 동시.
  - 라벨 내용(코드가 provenance 와 같은 출처에서 뽑는다 — 손으로 쓰지 않는다, P5):
    1) 지금 화면에 살아 있는 이벤트의 레지스트리 이름: `type`(panel 은 `panel:<kind>`, primitive 는 `primitive:<id>`, badge 는 `badge:<kind>`), 무대·테마
    2) 이 숏에 그려진 글꼴 키 → 이름(`rules fonts`: sans·serif·display·mono) — 실제 그린 키만
    3) 음성 한 줄: `config tts.backend_default`·`tts.supertonic.voice_style`·speed + `rules tts_rules.prosody.final_fall` 요약(문자열 조립은 코드, 값은 config·rules)
  - 위치: 날짜 뱃지(오른쪽 위)·자막·엔딩 카드·핀 카드와 겹치지 않는 **왼쪽 위**. 자막 상자·날짜 뱃지 상자와 교차하면 검사 `[catalog-label-overlap]` hard(카탈로그 산출물에만).
  - 테스트: `tests/anti_inertia/` 에 ① `--catalog` 산출물 deliver 거부 ② rules `catalog` 스키마 ③ 라벨 비교차 ④ 전편(`--res final`) 프레임 md5 가 카탈로그 유무와 무관(골든 25/25 유지).
- **요소 표**(사용자에게 보내는 것): provenance `features_used` 와 frames 기록에서 **코드가 생성**한 "초 → 요소·글꼴" 표(`tools/catalog_table.py`, md).
  손으로 쓴 표는 받지 않는다(P12).

### 1.2 showcase_geo 체크리스트(현 레지스트리 전부 — 자료 있는 것만, 없는 것은 "미포함 + 이유")
- 무대 mercator **light**(장르 기본, D154). 이벤트: marker, route, tanker_loop, barrier, ships, boom, country, badge(person·flag·emblem 셋 다),
  card, cascade, panel 11종(relation, statement, timeline, precedent, versus, dots, gantt, dual_line, fork, checklist, network), dip, photo, clip, cutout,
  article, post, quote, flight(+위성 인셋, Esri private_only), primitive site_diagram. 엔딩 카드(크레딧·권리·보도 출처).
- 글꼴 4종이 모두 실제로 그려져야 한다: sans(자막·카드), serif(기사 헤드라인), display(큰 숫자), mono(날짜 뱃지·크레딧).
- 음성: 표준(C0.2) 그대로. 묻지 않는다.
- 패널 중 레코드가 필요한 것(dual_line·dots·gantt·versus)은 기존 프로젝트 레코드·facts 만 쓴다. 자료가 없으면 넣지 않고 `media_note`/설명란에 미포함 사유.

### 1.3 showcase_econ 체크리스트(저장소가 지금 커버하는 범위만)
- 무대 backdrop(Flickr PD 에클스 빌딩·이사회실·아트리움·워시 회견 사진 — 레지스트리 등재본) + island(series step FEDFUNDS·band DFEDTARU/L·line CPIAUCSL yoy·dual_line),
  보조 timeline(레인 3: policy_rate step·inflation line·events pins, 압축 물결, 핀 확대). card(bigs = display 글꼴), article(fed 기사 4건 등재본), badge person(워시 라이브러리),
  photo, primitive statement_diff, primitive **dot_plot**(SEP — provenance `elements.approval: pending` 상태. 이 데모가 사용자 승인 자료다), panel dots·versus·checklist·timeline,
  quote, 엔딩 카드 `auto: series` 출처 줄 + "투자 권유가 아닌 정보 제공 목적" 줄(credits.yaml, fed 선례).
- **미포함(아직 없음, 데모 설명란에 명시)**: 막대 계열·워터폴·생키, 공시(filing) 레코드, company 엔티티·로고, corporate 프로필, 경제 클립(E2 뒤).
- `macro_monetary` 는 `status: proposed` 그대로 돈다(provenance 기록, P6). approved 전환은 데모를 본 사용자 결정.

### 1.4 공정(WORKFLOWS W0 그대로 — 건너뛰기 없음)
원고 → `gate-view` 원고 검토 자료 → **게이트 ①(사용자)** → `script.plan`(표준 음성) → 미디어 등록(article_register·media_fetch, 기존 레지스트리 재사용) →
연출(`ai_direction_run`) → `audio.mix` → `engine.render --animatic` → **콘티 판 2편을 사용자에게**(흐름 검토) → 게이트 ② → `engine.render --res final` + `--catalog` →
결합 `showcase.mp4` + 요소 표 2장 → `artifacts/showcase-v7.x/`(final 둘·catalog 둘·결합본·MD5SUMS·README 미포함 목록).
자산 보관(PIPELINE-AP-016): 새 자산은 없어야 정상 — `asset_library.py check` = 0.

### 1.5 합격 기준(E0)
checks hard 0(두 프로젝트, 전편·카탈로그) · provenance `features_used` ⊇ 체크리스트(미포함 항목은 설명란 사유와 1:1) · 골든 dark·light 25/25 ·
`python -m pytest -q -m "not slow"` + 새 테스트 4건 · 카탈로그 라벨이 레지스트리 밖 이름을 내면 오류(P10) · 음성 표준 지문(믹스 기준선 그대로).
R 보고(README §6.3): 커밋 목록, 테스트, 콘티 판·전편·카탈로그 경로와 md5, 요소 표, provenance 요약, DECISIONS 새 행.

## 2. E1~E6 — 보완 단계(순서 = 착수 순서, 단계마다 별도 D)

| 단계 | 내용 | 비고 |
|---|---|---|
| **E1** (병렬, 다른 저장소) | agents_reviewer: 차트마다 `provenance.sources` 필수 + locator(양식·접수번호·쪽/표 id), `BundleSource.provider` 에 `sec_edgar`·`dart`, `BundleClaim` 채우기(`BundleEvidence.locator`). osint 쪽: 어댑터가 출처 0 차트를 `drops[]` 사유 `no_source` 로 남기는지 확인(P6) | 착수 시점은 사용자 결정(저장소가 다르다) |
| **E2a** 영상 소스 — 기록·공급 | `schemas/media_models.py`: `scope: private_only` 를 inset 전용에서 `video`·`photo` 로 확장(`rights_status: restricted` + `scope: private_only` 조합 허용, provenance `private_only_assets` 포함). `rules media_beats.sources_order` 에 `youtube_official`·`broadcast`(via fetcher) 추가, `tools/media_fetch.py` 가 yt-dlp 로 받기(`config.yaml media.video_fetch`: 허용 도메인·해상도·도구 revision 고정, raw 는 `media/` 보관·md5 = `source_hash`), 12장 검수 시트·segment 사람 선택은 그대로. `triggers.clip` 에 비군사 어간(발언·인터뷰·발표·시연·회견·공장·데이터센터·청문). **막는 검사 추가 금지(D264).** 홍보 영상은 `file_note` 접두 "홍보 영상"(FILE_PHOTO_PREFIXES 옆, 정확성 표기) | 장르 무관·영상미 직결 — E3 앞 |
| **E3** 공시 데이터 경로 | `SeriesRecord.source_kind` 에 `filing`(press_cited 분기 모방): 값마다 `filing {form, accession, filed_on, item, locator, url}`, `transform.op filing`, 라이선스 범주 이름은 decision_request(공개 기록이지 US Gov Work 가 아니다). `units` 추가(백만 달러·십억 달러·조 원·곳·배), `frequencies` 추가(quarterly·half_year·annual·asof). `tools/fetch_filing.py`: EDGAR 표 추출(`pandas.read_html`, 표 위치 기록) + 정정본 추적(같은 CIK 의 최신 S-1/A → 화면 `as_of` "MM월 DD일 제출본 기준") + DART(API 키 .env, C9). 검증 LLM 긴 문서: 목차 단위 분할(`body_max_chars` 는 그대로, 항목별 입력). 발음 사전: EDGAR·NRR·PBC·Class F·TTM·티커. **주의**: sec.gov 는 감독 컨테이너에서 프록시 403 — 구현 컨테이너에서 접근 확인, 불가하면 사용자 PC 다운로드 → `raw/` 보관 경로를 공정으로 | XBRL: 최초 S-1 에는 재무 XBRL 이 없을 수 있다(가격 범위 정정본부터). 표 추출이 본선 |
| **E4** 새 시각 요소 2 | 20 §4.1 절차(제안 → 실제 엔진 스케치 1~3컷 → 사용자 승인 → 등록). ① panel kind `bars`(옵션 basic·diverging·lollipop·range·waterfall — 렌더러 하나, series 레코드 입력, "막대는 0 에서" 정직성 검사 적용) ② panel kind `sankey`(흐름이 문장 앵커마다 하나씩 자란다 — 한꺼번에 금지, 합이 맞지 않으면 오류). 영상당 새 요소 ≤3(20 §4.3). `rules bundle.chart_panels` 갱신: bar·diverging_bar·lollipop·range_bar·waterfall·funnel → bars(옵션), sankey → sankey, treemap → dots, tree → network/fork. **기각**: gauge·donut·decision_matrix·spectrum(C0 "보고서 화면"), `prerendered_svg` 그대로 붙이기 | 스키마·렌더러·프리뷰 예제 세 곳 동시(C7) |
| **E5** 기업 장르 | `genres/corporate.yaml`(proposed, stage backdrop, 색 의미, narration: `company_metric_attribution`(회사 산정 지표 귀속)·`filing_version_attribution`), 투자 고지 엔딩 줄을 장르 요구 시 결정적 검사 `[invest-notice-missing]` hard 로, `EntityIn.kind` 에 `company`(name·ticker·exchange; 배지 = 코드 조판 회사명, 로고는 private_only 기록 시 허용 — D264), `prompts/intake_planner_category_guidance.yaml` economy 항목(Bloomberg → 공시·공개 통계·DART), 공용 사진(SEC·나스닥·데이터센터, PD/CC) 확보 | |
| **E2b** 영상 소스 — 연출 | 발언 클립: `quote` 이벤트에 `clip` + 클립 음성 재생 구간 내레이션 덕킹(`rules audio.duck_db`·`duck_fade_sec`, 표준 음성 규칙 C0.2 불변). 움직이는 배경: `backdrop` kind clip(무음·블러·감광 = 사진 배경 수치 그대로, D-0134). 양측 발언 나란히(quote 둘 좌우) 연출 문법 → 스케치 → 승인 | 영상미 상승이 가장 큰 단계 |
| **E6** 첫 실증 | 앤트로픽 S-1 영상(E1 반영 번들 필요) — W0 전 공정(게이트 ① → 콘티 판 → 게이트 ②). 완료 뒤 `showcase_econ` v2 재렌더로 카탈로그 갱신(P12 — 적용은 영상으로 증명) | |
| **E7** 기업 실적 발표 템플릿 | 사용자 요청 2026-10-30(DECISIONS D274): 예상치·실제·가이던스·주가 반응·지경학 다섯 막, 첫 사례 삼성전자·인텔 Q3 2026. E3(filing)·E4(bars)·E5(company) 를 끌어당긴다 — 정본 **D-0278** | 착수는 사용자 승인 대기 시간에(D-0278 §9) |

## 3. 사용자 결정 대기(README §7 사용자 고유 결정)
① showcase 두 편의 게이트 ①·② ② dot_plot 승인(데모 시청 뒤) ③ `macro_monetary` approved 전환 ④ E1 착수 시점 ⑤ E3 공시 라이선스 범주 이름(Opus 제안 뒤).
권리 예외는 D264 로 끝났다 — 다시 묻지 않는다.

## 4. 금지·주의
- 쇼케이스를 위해 레지스트리 밖 요소를 임시로 만들지 않는다(P10). 미포함은 사유로 남긴다.
- 카탈로그 층 라벨을 final.mp4 에 넣지 않는다. 콘티 판·카탈로그 둘 다 `prev/` 를 덮지 않는다.
- 코드 상수로 라벨 문자열·글꼴 이름·음성 설정을 적지 않는다(P3). 모두 config·rules 에서 읽는다.
- 새 검사는 카탈로그 산출물의 라벨 비교차 하나뿐. 영상 소스에 대한 금지 검사는 없다(D264).

## 5. 보정(2026-10-27 같은 날, 사용자 의견 UF-132·133·134) — 쇼케이스 재료 교체

사용자 원문: "참고로 예전에 니가 만들었던 연준영상은 탈락이야. 그리고 호르무즈 이슈도 내 맘에 썩 들지 않아. 굳이 따지자면, 한국의 유조선이
블라디보스토크로 갔던 그 영상이 최고점이랄까?"

- **연준 영상(fed_policy_2026 v16)은 사용자 판정 탈락 — 쇼케이스·새 영상의 기준으로 쓰지 않는다.** §1.1·§1.3 의 "fed_policy_2026 축약" 은 폐기.
- **호르무즈 영상(hormuz_korea v3)은 사용자 판정 '썩 들지 않음' — 골든 25컷은 회귀 기준(화소)으로만 남고 연출 기준으로 쓰지 않는다.**
  §1.1 의 "hormuz_korea 1장" 은 요소 자료(ships·tanker_loop·barrier·clip·statement·precedent 패널 등 diesel 에 없는 것) 공급으로만 쓴다.
- **기준 영상 = diesel_road_2026 v2(교체 3, md5 554f4f85) — 쇼케이스 두 편은 이 영상의 문법으로 만든다.**
  실측 차이(direction.yaml): diesel 은 카메라 키 39·카드 74·마커 25·뱃지 20·기사 15·flight(위성 인셋) 12·경로 8·데이터 패널 9(dots 3·versus 3·dual_line 3)·quote 2,
  무대 mercator. hormuz 는 카메라 10, fed 는 backdrop 무대 + 카메라 7·배경 사진 10·series 2(정적). 즉 **지도 위에서 사건을 따라가며 데이터 패널이
  이야기 안에 박히는 밀도** 가 합격 요인이라는 가설이다. 원인 확정은 사용자 답(§5.1)을 받은 뒤 한다.
- 쇼케이스 재설계:
  - `showcase_geo` = diesel_road_2026 축약(주) + hormuz·dmz 자료 1장(요소 보충). 문법은 diesel(카메라 밀도·카드·인셋·데이터 패널) 그대로.
  - `showcase_econ` = **backdrop 정적 문법 금지.** 1안(기본): diesel 의 경제 줄기(경유 수출입·가격·물량 = 시계열·점·대비 패널)를 지도 위에서 다시 자르고,
    macro_monetary 요소(차트 아일랜드 series·statement_diff·dot_plot)는 같은 지도 문법 안에 1장 삽입. 2안: Fed 사실을 유지하되 무대를 mercator(달러·금리의 지리적 전파)로.
    **사용자 답(§5.1 ①) 뒤 Fable 이 1안/2안을 결정한다.** 그때까지 Opus 는 geo 편과 카탈로그 층(§1.1)을 먼저 한다.
  - 카탈로그 층·공정·합격 기준(§1.1·§1.4·§1.5)은 그대로.

### 5.1 사용자에게 물을 것(§7 사용자 고유 결정 — 감독이 대신 정하지 않는다)
① 연준 영상에서 무엇이 탈락 요인이었나(정적 배경? 차트 아일랜드? 이야기 없음? 길이?) — 원장 장치를 달려면 원인이 필요하다.
② 호르무즈에서 아쉬운 점 한 가지.
③ C0 "기준 작품 = v3 호르무즈" 를 "diesel_road_2026 v2" 로 바꿀지(헌법이 먼저 바뀐다, P7). 바꾸면 골든 25컷은 회귀용으로만 남긴다.

## 6. 보정 2(2026-10-27, 사용자 의견 UF-135·136) — 탈락 원인 확정: "차트가 하나의 세계가 아니었다"

사용자 원문(연준): "연준 영상에서 탈락 요인은 너무 차트만 나오기도 하고, 여러 맥락의 차트들이 나오는데, 그게 같은 축척 혹은 같은 차트 안에서
움직이거나 보여주는게 아니니까 전혀 눈에 들어오거나 맥락을 파악하기가 어려웠어."
사용자 원문(호르무즈): "호르무즈는 처음이라 좀 어색한 연출들이 많았지."

### 6.1 원인(확정)과 원칙
- 탈락 요인은 둘이다. ① **차트만 나온다**(사건·인물·장소·사진이 없는 구간이 길다) ② **차트마다 축척·좌표계가 다르다** — 아일랜드가 하나씩 떴다 사라지며
  서로 다른 축에 그려져 맥락이 이어지지 않는다. fed_policy_2026 은 backdrop 무대 + island 10 회·series 2 로 정확히 이 구성이었다.
- **원칙(영상 문법)**: **경제 영상의 차트는 지도처럼 하나의 연속 세계여야 한다.** 모든 시계열은 같은 시간축·같은 레인 축척 위에 살고, 카메라가 그
  세계 안에서 이동·확대한다(= timeline 무대의 본래 설계, 20 §2.1·D-0084). 서로 다른 축척의 독립 차트를 번갈아 띄우는 구성은 금지한다.
  새 차트 요소(E4 막대 계열·생키)도 **무대 안 요소**로 만든다 — 시간축의 한 날짜에서 같은 y 축척으로 자라나는 막대, 같은 세계 안에서 펼쳐지는 흐름. 독립 패널로 띄우지 않는다.
- 호르무즈(UF-136)는 "처음이라 어색한 연출" — 첫 작품의 미숙이다. 이후 문법(카메라 연속 변환·핀 확대·인셋 등, D100~D260)이 이미 그 자리를 채웠다.
  별도 장치 없이 기록만 하고, 기준 영상은 diesel 로 둔다(§5).

### 6.2 장치(E0 안에 단다 — 영상 전달 뒤가 아니라 쇼케이스 전에, 쇼케이스가 "다음 영상"이다, C12-2)
1. **규칙**: `genres/macro_monetary.yaml stage.primary` 를 backdrop → **timeline** 으로 되돌린다(D-0123 이전 값). backdrop 은 secondary(사진이 필요한 비차트 순간).
   D108("비지도 주제 = 사진 배경 + 아일랜드")은 **아일랜드가 하나의 차트 세계일 때만** 유효하도록 보정 — 이 보정은 사용자 결정(§6.3 ①).
2. **검사 `[chart-world-split]` hard**: 한 영상에서 island 이벤트가 2개 이상이고 그 안의 series 가 같은 단위인데 다른 y 축척(레인 범위)이면 실패.
   같은 단위 = 같은 레인 축척(`series_models` 레인 범위는 무대가 정한다, 사용자 값 아님).
3. **검사 `[chart-only-run]` hard**: `rules qa_checks.chart_only_run_max_sec`(값 제안 → decision_request) 보다 길게 "차트·카드만 보이는 구간"(사건·인물·사진·기사·경로 등 비차트 요소 0)이 이어지면 실패. 모든 장르.
4. **연출 프롬프트 줄**(rules 에서 생성, P3): "경제·데이터 영상의 차트는 하나의 시간축 세계다. 카메라가 그 안에서 이동한다. 축척이 다른 독립 차트를 번갈아 띄우지 않는다."
5. 원장 UF-135 의 guards 를 위 1~4 로 보강(status 유지, 칸 보강만).

### 6.3 사용자 결정(§7)
① D108 보정 수용 여부(macro 기본 무대 timeline, backdrop 은 보조) ② `[chart-only-run]` 상한 초(Opus 제안 뒤) ③ §5.1 ③ C0 기준 작품 교체(미답).

## 7. 보정 3(2026-10-27, 사용자 "내가 어떻게 뭘 보고 결정할 수 있지?") — 결정은 문서가 아니라 영상으로(P12)
- §5.1 ③·§6.3 ① 은 사용자에게 **문서로 묻지 않는다.** C0 기준 작품은 사용자 판정(UF-134)을 그대로 헌법에 반영했다(D268, 커밋 eb70e7a).
- **D108 보정은 쇼케이스 A/B 로 결정한다**: `showcase_econ` 의 같은 장면(사실·원고·음성 동일, 20~30초)을 두 문법으로 렌더한다 —
  **A** 사진 배경 + 아일랜드(현행 D108), **B** 시간축 세계(§6.1). 산출: 각각 mp4 + 컨택트 시트(같은 초의 컷을 좌우 나란히). 사용자는 게이트 ② 에서 A/B 를 고른다.
  고른 쪽이 `genres/macro_monetary.yaml stage.primary` 값이 되고(코드 변경은 그 뒤), 고르지 않은 쪽은 `prev/` 에만 남긴다. 본편 쇼케이스는 B 로 먼저 만들고 A 는 비교 장면 하나만 만든다(비용).
- 사용자가 보는 것은 세 번뿐: 게이트 ①(원고 전문·출처 표), 콘티 판(흐름), 게이트 ②(프리뷰 시트 + A/B 시트 + 카탈로그 요소 표). 그 밖의 결정은 감독이 한다(README §6.4·§7).
