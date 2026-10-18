---
id: D-0229
from: fable
to: opus
kind: directive
responds_to: [R-0240, 사용자 의견 UF-104~UF-115(2026-10-18), DECISIONS D240]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
supersedes: [D-0225 §1 시간 예산·§2.0 10분 상한]
---

# diesel_road_2026 v2 착수 — 사용자 시청 의견 12건 반영(UF-104~115) + 엔진 보강 v7.4.0

사용자가 전편(artifacts/diesel_road_2026-v7.3.0)을 보고 의견 12건을 줬다. **원문은 `rules/user_feedback.yaml` UF-104~UF-115 가 정본**이다 — 이 문서는 그것을 구현 단위로 푼 것이다. 둘이 어긋나면 UF 원문이 이긴다.
길이 상한(10분, D234 U5)은 **해제**됐다(D240). 기준은 "이해하면서 넘어가는 호흡"이다. 예상 13~16분, 상한 없음.

## 0. 작업 환경·브랜치·버전

- 환경: 지난 트랙과 같은 컨테이너 설정(음성·arcgis·commons 허용). 표준 음성(C0.2)·MMS 정렬 그대로. Supertonic 가중치는 `config.yaml tts.supertonic` 대로 받는다.
- 브랜치: `main`(a4e7d61d 이후, UF-115 까지 반영된 HEAD) 에서 `claude/diesel-road-v2` 를 만든다. 교신(R/D)은 이 브랜치의 `back_and_forth/`.
- 버전: 새 레이어(도로·강)·새 이벤트 필드·새 검사가 들어가므로 **v7.4.0**(MINOR). 첫 커밋에서 `VERSION`·`orchestrator/__init__.py`·CHANGELOG 를 올린다. 이후 커밋은 한 의도씩(C5.5).
- 산출물 브랜치: `artifacts/diesel_road_2026-v7.4.0-animatic`, `artifacts/diesel_road_2026-v7.4.0`(이전 트랙과 같은 구성: mp4·srt·description·provenance·audio_qa·prev/sheet·MD5SUMS).
- 주의: 이 컨테이너에는 fed_policy_2026·hormuz 자산이 없다(R-0240). 전체 pytest 는 main 병합 직전 1회, 환경 의존 실패는 R-0240 과 같은 문구로 명기(D-0228).

## 1. 순서(바꾸지 않는다)

| 단계 | 내용 | 보고 |
|---|---|---|
| A | 엔진·규칙 보강(§2) — 연출이 쓰기 전에 먼저 | R(progress): 커밋 목록 + 골든 dark·light 25컷 + 새 테스트 |
| B | 원고 v2(§3) → `gate-view` 원고 검토 자료 | R(phase_report): 원고 전문·출처 표·린트. **감독이 사용자에게 보낸다 — 게이트 ① 은 이번에는 사용자 검토**(원고 내용 의견이 많았으므로 D232 위임을 쓰지 않는다) |
| C | 승인 뒤 음성 → 연출 v2(§4) → 콘티 판 | R: animatic.mp4·시트·checks. 게이트 ② 는 감독(Fable) |
| D | 전편 → QA hard 0 → artifacts 푸시 | R(최종) |
| E | 장치 달기(§6) → 전체 pytest → main 병합(merge --no-ff, PR 없음) | R |

A 단계 안에서 검사(check)·테스트가 싸게 붙는 항목은 **그 자리에서 장치까지 단다**(UF 의 guards 를 채우고 status guarded). 나머지 장치는 E.

## 2. 엔진·규칙 보강 (A 단계) — 항목마다 커밋 하나

### 2.1 지도 레이어 (UF-106)
1. **수도 상시 표기**: `rules labels.capital_always: true` 추가 → `engine/layers/labels.py` 의 도시 선택에서 `plc_cap` 은 폭(w)과 무관하게 후보에 넣는다(기존 `rank ≤ rk+2` 가산은 유지, 상시는 그 위에). 화면당 상한 `city_labels_max` 는 그대로. 골든 25컷에서 바뀌는 컷이 있으면 R 에 전후 컷 첨부(호르무즈 골든은 사용자 합격 값이므로 **바뀌면 안 된다** — 바뀌면 상시 표기를 w ≤ 60 으로 제한하고 사유 기록).
2. **도로·강 레이어(Natural Earth, 공개 도메인)**: `geo/prep.py NE_FILES` 에 `ne_10m_roads`, `ne_10m_rivers_lake_centerlines` 추가(같은 `tools/fetch_data.NE_URL`, 허용 호스트 추가 없음). `geo/prep_geometry.py` 에 `load_roads(bb)`(type ∈ {Major Highway, Secondary Highway, Road} → class motorway/trunk/primary 로 매핑, 열 이름은 NE 속성 확인 후 R 에 기록)·`load_rivers(bb)`(scalerank 유지) → geo.pkl 에 `roads`·`rivers` 키(coarse/fine 두 해상도).
   렌더: 새 모듈 `engine/layers/roads.py`(도로)·`engine/layers/rivers.py`(강). 그리기 순서 = 지형 → 강 → 행정선 → 도로 → 국경 → 지명(가이드 23 §15 "국경이 가장 분명"). 스타일은 `rules geo.themes.<테마>.map.roads/rivers` 토큰으로만(두 테마 모두 채운다):
   - dark: roads `{motorway: {rgb: [0.62,0.64,0.68], width: 0.55, alpha: 0.55}, trunk: {rgb: [0.56,0.58,0.62], width: 0.45, alpha: 0.5}, primary: {rgb: [0.5,0.52,0.56], width: 0.35, alpha: 0.42}}`, rivers `{rgb: [0.42,0.62,0.74], width_major: 0.5, width_minor: 0.35, alpha_major: 0.6, alpha_minor: 0.4}` — 시안 값, 콘티에서 보고 조정. 설계 px(480p).
   - light: 가이드 23 §15 값(720p px ÷ 1.5): motorway .53/gray73/α.80, trunk .43/gray91/α.73, primary .33/gray119/α.59; rivers RGB 135/183/208, major .47/α.88, minor .33/α.57.
   - LOD: `MERCATOR_LOD` 에 `roads_fade: {w: 14, span: 5}`(w<14° 에서 나타나 9° 에서 완전; motorway 만 w<22 부터), `rivers_fade: {major_w: 40, minor_w: 12, span: 6}`. 단일 stroke, casing·glow 없음(가이드 §15).
   - 권리: `assets/rights_bundles.yaml natural_earth` 에 roads·rivers 레이어명 추가(크레딧 "지도" 행 자동).
   - 테스트: `tests/test_v740_map_layers.py` — (a) geo.pkl 에 roads/rivers 키, (b) w=8 렌더 컷에서 도로 색 화소 > 0, w=60 에서 0, (c) 두 테마 토큰 키 집합 동일(anti_inertia 레지스트리 방식), (d) 골든 dark·light 25컷 md5 **무변화**(골든 숏은 모두 w ≥ 14 이거나 호르무즈 근접 숏 — 근접 숏에서 바뀌면 R 에 전후 컷, 감독 판정).
3. 연출 지침(§4)에서 타격지·항구마다 폭 6~10° 근접 숏을 쓴다 — 행정선(w<24)·도명(w<8.5)·도로가 켜지는 폭이다.

### 2.2 시점 전환 장치 (UF-105)
- `rules transition:` 블록 신설: `bridge_pause_sec: 1.5`(전환 직전 내레이션 공백, 음악만), `camera_move_min_sec: 4.0`(무대·시대 점프 시 카메라 이동 하한), `date_badge_xfade_sec: 0.6`, `jump_days: 30`(이 이상 날짜가 뛰면 '시점 전환'으로 본다).
- 원고 계약: 시점 전환 문장은 `role: bridge` 로 표시(plan.json sentences[].role). 린트 `[transition-bridge]`: 무대 전환(stage 변경) 또는 날짜 배지가 jump_days 이상 뛰는 지점 ±1문장 안에 bridge 문장이 없으면 **hard**.
- 렌더: bridge 문장 앞 `bridge_pause_sec` 를 `audio.mix` 타임라인이 넣는다(문장 간격이 아니라 전환 전용 간격, provenance 에 `transitions[]` 기록). 날짜 배지는 즉시 교체가 아니라 xfade.
- 테스트: `tests/test_v740_transition.py` — bridge 없는 무대 전환 fixture 가 hard, 있는 fixture 가 통과; mix 타임라인에 간격이 들어가는지.

### 2.3 컷어웨이 급전환 검사 (UF-110)
- 검사 `[cutaway-churn]` hard: 전면 이벤트(article·photo·clip·cutout 전면·backdrop 전환) 가 끝난 뒤 `shot_min_hold_sec`(규칙 272행, 6초) 안에 다른 전면 이벤트가 시작하면 실패. 같은 문장 묶음에서 연속이면 **한 이벤트로 합치라**는 메시지.
- 테스트: 현재 direction.yaml(v1) 을 fixture 로 돌리면 오프닝 22.4~27.1 에서 걸려야 한다(재현 → v2 연출에서 통과).

### 2.4 단위 글꼴 (UF-111)
- `rules fonts.unit_font: sans`. `engine/cards.py` bigs, `engine/panels/*` 의 값 글자, `engine/layers/series.py fmt_value` 가 쓰는 축·값 글자에서 **끝의 라틴 단위 토큰**(`t`, `kb/d`, `mb/d`, `%`, `$`, `bbl` 등 — 정규식 `\s*[A-Za-z/%$]+$`)을 분리해 unit_font 로 그린다. 숫자·한글(만·천·억)은 기존 글꼴.
- 검사 `[unit-glyph-font]`: display 글꼴(`disp`)로 그리는 문자열에 라틴 소문자가 남아 있으면 hard(typography.text 에 role 로 잡는다).
- 테스트: `tests/test_v740_unit_font.py` — split 함수 단위 시험 + 카드 렌더에서 단위 글리프가 sans 로 그려지는지(글꼴 호출 기록).

### 2.5 굴절 항로 (UF-112)
- route 이벤트에 `declared: {place: <gazetteer 이름 또는 lon/lat>, label: "신고: 니가타"}` 필드. 렌더러가 `pts` 를 **출발 → 신고지 앞바다(꺾임점) → 실제 도착**으로 쓰되, 꺾임점까지는 `muted` 점선(dashed) + 라벨, 꺾임 뒤는 이벤트 col 실선. 꺾임점은 연출이 `pts.path` 에 직접 준다(자동 생성 안 함 — 항적을 지어내지 않는다, 엔딩 표기 행 "비행·항로 개략" 유지). `declared.bend_index` 로 몇 번째 점부터 실선인지 지정.
- 테스트: `tests/test_v740_route_declared.py` — bend_index 앞 구간 dash, 뒤 구간 solid, 라벨 위치가 꺾임점 근처.

### 2.6 "N 중 M" 점 패널 (UF-113)
- `engine/panels/dots.py` 는 이미 `highlight` 를 받는다(31행). 부족한 것만 보강: `big` 글자에 "3 / 7" 같은 분수 표기 허용(단위 글꼴 규칙 적용), 강조점 색을 `accent` 토큰으로.
- 원고 린트 `[ratio-without-graphic]` warning: 문장에 `(\d+|[일이삼사오육칠팔구십]+)\s*(척|곳|건|명|개)\s*(중|가운데)` 가 있는데 그 문장 구간에 dots·versus·series 패널이 없으면 경고.

### 2.7 인셋 유지 (UF-107)
- `rules flight.inset.hold_same_place: true` — 인셋은 `hold_sec` 뒤에도 **다음 문장들이 같은 장소(gazetteer 이름 또는 마커 at_place)를 앵커로 말하는 동안** 유지, 장소가 바뀌는 문장의 시작에서 fade. 연출은 `inset.hold_until: {sid, edge}` 로 명시 지정도 가능(이번 오프닝은 명시 지정: cold_3 끝).
- 자리: 마커·카드와 겹치면 `card_layout` 의 빈 사분면으로 옮긴다(검사 `inset_overlap` 이 이미 있으면 그것으로, 없으면 warning 추가).

### 2.8 원고 어휘 린트 (UF-108·UF-114)
- `[verb-target-mismatch]` hard: `맞히|맞혔|맞힌` + 고정 시설 명사(정유소·공장·기지·설비·펌프장·터미널·발전소·저장고·항만·다리) 같은 문장 → 실패. 이동 표적(무인기·미사일·항공기·차량·선박)은 허용.
- `[contrast-conjunction]` warning: 문장 머리 `반면` 앞 문장이 발표·주장 문장(`밝혔|말했|전했|주장`)이면 "이에 대해·한편" 권고.
- 둘 다 `script/lint`(현 린트 모듈)에 넣고 `prompts/` 원고 템플릿에도 규칙 문장 추가(P3: 규칙 파일에서 생성).

### 2.9 템포 규칙 (UF-115·UF-104)
- `rules tempo:` 신설: `fact_sentences_per_min_max: 8`, `act_intro_min: 2`(막 도입 문장 수), `act_outro_min: 1`, `sentence_gap_sec: 0.9`(현 timeline_gaps.gap_sec 0.5 → 이 영상은 0.9; 골든은 바꾸지 않는다 — 장르 프로필 또는 프로젝트 `order.yaml tempo` 로 override, 규칙 키는 하나).
- 린트 `[tempo-density]` warning: 1분 창에서 사실 문장(출처 귀속 문장)이 상한 초과. `[act-frame]` hard: 막마다 `role: intro` ≥ 2, `role: outro` ≥ 1 없으면 실패.

### 2.10 v1 관찰 사항(D-0227 §비차단·아침 보고) — 같이 고친다
- act4_2 트럼프 발언: 트럼프 뱃지(라이브러리 `trump_mono_v01`)를 푸틴 뱃지와 나란히.
- 125초·480초 빈 지도 구간: `country` 강조(a 0.05~0.08)로 바탕 채움.
- 인셋 출처 줄과 마커 라벨 겹침: 2.7 의 자리 규칙으로 해결.
- 크레딧 "NNK 자산 보고서" 행 오른쪽 열 근접, 엔딩 표기 행 전용 슬롯: `credits` 레이아웃에서 표기 행을 마지막 전용 줄로.

## 3. 원고 v2 (B 단계) — UF-104·105·108·114·115

원고 모듈(`script.plan`)의 규칙·프롬프트(2.8·2.9)를 먼저 고친 뒤 **다시 생성**한다(P3·P9: 옛 원고를 참고로 넣지 않는다 — facts.json·claims·sources 만). 생성 뒤 아래를 감독·사용자 검토용 `gate-view` 에 반드시 보이게 한다.

### 3.1 구조(막전 막후)
각 막 = **도입(intro 2~3문장: 왜 지금 이 이야기인가, 앞 막과의 연결) → 본문 → 정리(outro 1~2문장: 무엇이 바뀌었나, 다음 막으로의 질문)**. 시점·무대가 바뀌는 자리에는 **bridge 문장 1개**(예: "시점을 올해 6월, 페르시아만으로 옮깁니다. 같은 경유를 두고 다른 전쟁이 있었습니다.").

### 3.2 인과 문장(UF-104) — 사건 문장 뒤 "왜" 문장. 출처가 있는 것만, 없으면 넣지 않는다(G4). 반드시 다뤄야 할 "왜" 목록:
1. **왜 우크라이나는 유전이 아니라 정유소를 때리나** — IEA 보고 근거(정제 제품 = 수출 수입 + 군 연료; 2차 설비는 수리 6~8개월; 유전은 피격해도 원유 수출 경로가 남음). 지금 원고의 act1_1·act1_2 를 "왜" 문장으로 묶는다.
2. **왜 러시아 극동은 경유가 모자라나** — 극동 정제소(하바롭스크·콤소몰스크) 처리량·장애, 서부 정제소에서 극동까지 철도 거리(출처 필요: 러시아 철도·업계 보도), 5월 연료난 보도(act2 보강 문장은 D-0226 에서 이미 넣은 출처 사용).
3. **왜 한국산 경유가 러시아로 갈 수 있었나** — 한국 수출 통제 품목(1,159개 등 자료 확인) 에 경유가 없음, 유가 상한은 러시아산 원유·제품의 **수출**에 적용되는 것이지 러시아로의 **판매**를 막지 않음, EU·영국 제재 선박은 EU·영국 관할에만 효력(가디언 보도 인용) — 각각 출처 귀속. 정부 입장(산업부 코멘트)·업계 입장(정유사 "중개상 판매·목적지 몰랐다") 을 **같은 무게**로.
4. **왜 울산(·여수)에서 블라디보스토크인가** — 동해 직항 2~3일, 극동에 정제 여력 부족, 블라디보스토크가 극동 소비지·철도 집결지(출처: 항만·업계 보도). 추정은 "추정"으로.
5. **왜 미국은 러시아 정유소 타격에 에너지 휴전을 들고 나왔나** — 트럼프 발표(10월 11일) 원문과 러시아·우크라이나 반응(AP). 휴전이 깨진 뒤 행정부 코멘트가 있으면 인용.
6. **왜 걸프 타격이 경유 시장에 닿나** — 라스라판·하르그·푸자이라가 경유 수출·환적 경로라는 점(IEA·Kpler·Vortexa 인용값, 기존 series 데이터), 한국 정유사의 원유 조달·경유 수출 구조.
7. **왜 이 거래가 제재 저촉 논쟁이 되나** — 2차 제재 위험(미 재무부 OFAC 기준), 한국 정부의 "자체 제재 품목 아님" 입장, 우크라이나 측 비판(키이우 인디펜던트). 양측 병기.

### 3.3 어휘·표현
- UF-114: 고정 시설 = "타격했다·때렸다". 린트 2.8 이 막는다.
- UF-108: cold_2 → "이에 대해 우크라이나 당국자는 이번 공격을 확인했다고 AP통신은 전했습니다."
- 금지 문구(`banned_phrases`)·발음 텍스트 숫자 금지 등 기존 규칙 그대로.

### 3.4 분량
- 상한 없음. 문장 수가 늘어나는 만큼 `tempo` 규칙이 호흡을 보장한다. 예상 13~16분. 15분을 넘으면 R 에 "어느 막이 왜 길어졌는지" 한 줄.

### 3.5 게이트 ① 자료
- `gate-view` 출력 + 린트 결과 + 출처 표 + **v1 대비 diff(추가·수정 문장 표시)** 를 R 에 첨부. 감독이 사용자에게 전달한다. 사용자 수정이 오면 다시 생성·재린트 후 재제출.

## 4. 연출 v2 (C 단계)

### 4.1 오프닝(UF-107·109·110)
- cold_0~cold_1: 드론 비행·착탄·랴잔 인셋(인셋 `hold_until: cold_3 끝`, 자리는 왼쪽 아래 — 카드는 오른쪽 위).
- cold_2: 우크라이나 카드(문구 수정).
- cold_3~cold_4: **AP 기사 카드 한 장**(art_0032, press 사진 포함)을 cold_3 시작 ~ cold_4 끝까지 유지. 젤렌스키 인용은 카드 위 quote 로 겹쳐 올리지 말고 카드가 떠 있는 동안 자막·내레이션만(카드 안 둘째 줄로 "젤렌스키: '이제 끝났다'" 가능하면 그렇게).
- cold_5: 지도 복귀, 울산 쪽으로 **느린** 카메라 이동(≥ 5초) + 음악만 1.5초 → 타이틀.
- 키이우 인디펜던트 기사(art_0001)는 2막 한국 수출 설명 자리로 이동.
- press 사진(UF-109): 위키미디어 공용에서 **미국 정부 저작(공개 도메인) 사진** — 2026년 10월 11일 전후 트럼프 발표 장면(백악관 공식 사진). 검색: commons 카테고리 "Donald Trump in October 2026" 또는 "White House photographs 2026". 라이선스 PD-USGov 만. 미디어 레지스트리에 kind photo·license·source url·`is_file_photo: true`("자료사진" 표기). **그 날짜 사진이 없으면 같은 달 공식 사진 + 자료사진 표기**. 공식 사진 자체가 없으면 press 없이 블러 무대(기존 규칙) + R 에 사유.

### 4.2 지도 숏(UF-106)
- 타격지·항구마다 근접 숏(w 6~10°): 랴잔(모스크바·랴잔주 행정선·M5 도로), 키리시(레닌그라드주), 볼고그라드·사라토프, 하바롭스크·블라디보스토크(연해주·하바롭스크주, 시베리아 횡단 철도는 도로 데이터가 아니므로 **그리지 않는다**), 울산·여수, 라스라판·하르그. 각 근접 숏은 `shot_min_hold_sec` 이상 유지하고 전후 카메라 이동은 느리게(≥ 4초).
- 수도는 상시 표기(모스크바·키이우·서울·테헤란·도하·아부다비 등).

### 4.3 2막(UF-112·113)
- act2_9~act2_10: dots 패널 — 점 7(유조선), highlight 3(제재 대상), big "3 / 7", 부제 "일곱 척 · 열네 번 항해 · 가디언". 사실 주의: 제재 대상은 **척수 기준(7척 중 3척)**, 열네 번은 항해 횟수.
- act2_11~act2_13 레일라·아스토리아: `declared` 굴절 항로 — 울산 → 니가타 앞바다(약 138.2E, 38.3N, 해안 밖) 꺾임 → 블라디보스토크. 아스토리아(신고 "일본"): 같은 꺾임점, 라벨 "신고: 일본". 청천(act2_15, 신고 싱가포르): 여수 → 대한해협 남쪽(약 129.5E, 33.8N) 꺾임 → 북상 → 블라디보스토크, 라벨 "신고: 싱가포르". 세 항로가 겹치지 않게 시작 시각·색을 나눈다.
- 키이우 인디펜던트 기사 카드(art_0001)는 한국 수출 설명 문장에.

### 4.4 시점 전환(UF-105)
- 1막(러시아 정유소) → 2막(극동·한국): 무대 같음, 시간 점프 없음 → bridge 1문장만.
- 2막 → 3막(걸프, 6월): **무대 전환 + 시간 점프** → bridge 문장 + 1.5초 음악 호흡 + 느린 카메라(≥ 4초) + 날짜 배지 xfade. 3막 → 4막(10월 복귀)도 같다.
- 막 도입·정리 문장 동안은 지도 위 `country` 강조와 날짜 배지만(새 정보 요소 없이 호흡).

### 4.5 v1 관찰 반영(2.10)과 기존 규칙
- 사진 0장 문제: 이번에도 권리 통과 사진이 없으면 그대로 명기. 기사 카드는 적극 조판(UF-102)하되 2.3 검사 안에서.
- 콘티 판은 의무(C8.6). 콘티 R 에 시트 + 추출 컷(전환 지점 5곳·근접 숏 6곳·점 패널·굴절 항로) 첨부.

## 5. 검증(단계마다)
- A: 변경마다 관련 테스트 + `pytest -q tests/anti_inertia` + 골든 dark·light 25컷. 새 테스트 5개 파일(2.1~2.5) 이상.
- B: 린트 hard 0(새 린트 포함), warning 은 R 에 전수 기재·처리 사유.
- C·D: checks hard 0, `[cutaway-churn]`·`[transition-bridge]` 0, audio_qa 범위 안(−14 LUFS, TP ≤ −1), provenance 에 `transitions[]`·`map_layers{roads,rivers,capitals}`·`user_feedback_guards`(UF-104~115 중 guarded 된 것) 기록.
- E: 전체 pytest 1회(환경 의존 실패는 D-0228 문구), main 병합.

## 6. 장치(C12) — E 단계에서 `rules/user_feedback.yaml` 의 UF-104~115 `guards`·`status` 를 채운다
| UF | 장치 |
|---|---|
| 104 | `[act-frame]` hard + `tempo.fact_sentences_per_min_max` |
| 105 | `[transition-bridge]` hard + `tests/test_v740_transition.py` |
| 106 | `labels.capital_always` + roads/rivers 토큰·LOD + `tests/test_v740_map_layers.py` |
| 107 | `flight.inset.hold_same_place` + 테스트 |
| 108 | `[contrast-conjunction]` warning |
| 109 | 기사 카드 press 사진 규칙은 기존(없으면 블러) — 장치는 `[article-press-missing]` warning(인물 발언 보도 문장의 article 에 press 없음) |
| 110 | `[cutaway-churn]` hard |
| 111 | `fonts.unit_font` + `[unit-glyph-font]` hard + 테스트 |
| 112 | route `declared` + 테스트 |
| 113 | `[ratio-without-graphic]` warning |
| 114 | `[verb-target-mismatch]` hard |
| 115 | `tempo` 블록 + `[tempo-density]` warning |
UF-101·102(인물·기사 적극)는 이번에 `[portrait-unused]`·기사 수 하한(장르 프로필) 을 장치로 올려 guarded 로.

## 7. 결정 요청이 필요한 것(§6.4)
- 골든 호르무즈 25컷이 2.1 로 바뀌는 경우(수도 상시 표기·근접 숏 도로) — 감독 판정. 바꾸지 말고 R 에 전후 컷.
- 공개 도메인 트럼프 사진이 없을 때 — 블러 무대로 가고 R 에 기록(결정 요청 불필요).
- 그 밖의 설계 선택은 `decision_request` 로. 사용자 고유 결정(§7)은 감독이 사용자에게 묻는다.

## 8. 보고
- 단계 A 끝: R(progress). B 끝: R(phase_report, 게이트 ① 자료). C 끝: R(콘티). D 끝: R(최종). E 끝: R(병합).
- 매 R 뒤 send_message(감독 세션 session_016v5HgxdsPNKcUYQ94ZkAoo). 막히면 30분 안에 R(question).
