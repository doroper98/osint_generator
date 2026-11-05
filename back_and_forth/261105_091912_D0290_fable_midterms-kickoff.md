---
id: D-0290
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 새 영상 『2026 미국 중간선거 — 주별 결과·격전지·역사 맥락』(pid `us_midterms_2026`) 착수

## 0. 사용자 원문·권한
- 사용자 원문(2026-11-05 09:12 KST, 감독 세션 대화): "미국 중간선거 결과를 분석하는 영상을 만들어. 구현 세션 띄워서 구현 하도록 하고 너가 감독해. 최대한 미국의 주별 결과, 주요한 격전지나 핫스팟, 역사적 맥락이 있는 곳 등에 대해 비쥬얼하게(우리 기존 지도 형식 적용 안해도 됨) 잘 설명해주는 영상을 만들어."
- 감독 세션 = `session_017Yuw8ixNRzov4VpELs53Xx`. **모든 R 은 이 id 로 `send_message`** 한다(다른 감독 세션에 보내지 않는다).
- 게이트 ①(원고)·②(프리뷰)는 **사용자 승인**이다(D-0282 같은 위임 없음). 감독이 gate-view 자료·콘티 판을 사용자에게 보내 승인을 받은 뒤 `approve --by user` 를 친다. Opus 는 승인 명령을 치지 않는다. 기다리는 동안 막히지 않는 작업(엔진 M1·자산·연출 초안)은 계속한다.
- 사용자에게 직접 묻지 않는다. 결정이 필요하면 `decision_request` R → 감독(README §6.4). 되돌릴 수 있는 선택 우선.

## 1. 브랜치·환경·번호
- 작업·교신 브랜치 = **`claude/vigilant-fermat-w8c2ti`**(main 16f6ae8 위, 감독 세션과 같은 브랜치). `git config core.hooksPath .githooks`. 커밋 첫 줄 `v7.4.0: …`(VERSION 그대로 — 병합 시 감독이 v7.5.0 으로 올린다, 새 이벤트 타입 = MINOR). 커밋마다 `git push -u origin claude/vigilant-fermat-w8c2ti`(거부 시 `pull --rebase`, force 금지).
- 환경 복원 = D-0283 §2.0·R-0284 §환경 그대로(pip requirements·requirements-engine + pycairo·numpy·scipy·shapely·librosa·onnxruntime·cairosvg·yt-dlp 2026.10.21·torch cpu·torchaudio·pyworld·uroman·rembg·`setuptools<81`; apt ffmpeg·fonts-noto-cjk; FONTCONFIG 12-unhinted-grayscale 제외; `python tools/fetch_data.py fonts ne tiles flags supertonic mms_fa bgm people`). 표준 음성 Supertonic 3 M3 ×0.95(C0.2 — 묻지 않는다).
- 네트워크(D-0284 §1 실측): 컨테이너 curl·WebFetch 는 허용 도메인 밖 DNS 실패. **조사는 WebSearch(allowed_domains 로 1차 출처 도메인 한정)** 로. 차단 호스트는 최종 R 표. 크롤러 차단 도메인(WebSearch 400) 은 검색에 넣지 않는다.
- 번호: 이 트랙 D 는 D-0290 부터, R 은 `check.py --me opus --next-name` 이 준다(R-0295 부터). DECISIONS 행은 D515 부터(감독이 쓴다).

## 2. 영상 설계(감독 결정 D515) — "지도를 버리지 않고 주(州) 채움을 더한다"
사용자가 "기존 지도 형식 적용 안 해도 됨" 이라 했다. 감독 판단: 선거 결과는 **주별 색 지도**가 시청자가 아는 형태이고, 기준 작품(diesel v2) 문법 = 연속 세계 위 카메라 이동(C0)을 지키려면 **메르카토르 light 무대 + 주(admin-1) 채움 이벤트 `area`** 가 가장 작고 되돌릴 수 있는 길이다(새 무대 Albers 는 engine·camera·checks 전부를 건드린다 — 이번엔 만들지 않는다).
- 주 무대: mercator **light**(지정학 장르 기본 D154). 미국 본토·알래스카·하와이가 W 티어 안. 카메라는 사건이 있는 주로 들어간다(diesel 문법: 문장 사유 있을 때만 이동, 한 문장 요소 2~3개).
- 새 이벤트 `area`(§3): 주별 결과(상원·주지사·하원 뒤집힘)를 색으로 입힌다 — 콜드 오픈에서 동→서로 주가 차례로 색을 입는 장면(투표 마감 시각 순, 출처 있으면 그 순서·없으면 경도 순).
- 데이터 패널(지도 위, 이야기 안): 상원 `versus`(민주 대 공화, 미확정 별도 줄), 하원 `dots`(435 중 민주·공화·미확정, 출처 줄 "NBC 추정/AP 집계 + 시각"), 역사 `precedent`(연도 카드 ≤4: 1994·2010·2018·2026 등 — 값은 APP 표), 출구조사 `versus`/`dots`(NBC 출구조사 귀속). 축척 다른 독립 차트 번갈아 띄우기 금지(chart_world_split hard). **card 이벤트 0**(UF-148, D-0287 — 자막 되풀이 카드 금지. 날짜·수치는 marker sub·패널·핀으로).
- 사진·초상: 연방 의원 공식 초상 = 미국 정부 저작물 PD(Commons 확인 후 등록). 주지사·주 공직자 초상은 Commons 라이선스 확인된 것만, 없으면 직함 quote. 사진·영상 밀도 ≥1.5/분(UF-139), 기사 카드 60초당 ≤2, 클립 액자(UF-141) 는 **C-SPAN(허용 도메인)** 승리·승복 연설 우선(콜린스 승복·탈라리코 승리·잭슨 등), 안 받아지면 사진. 사실 장면 AI 생성 금지.
- 길이: 내용이 정한다 — 목표 6~8분(문장 70~90). 막 구성은 §4.

## 3. M1 엔진 — `area` 이벤트(admin-1 채움) 명세 — **먼저, 조사와 병행**
레지스트리 3곳 동시(C7·P10): 스키마 + 렌더러 + 예시(파리티). 조용한 폴백 금지(P6). 수치는 규칙 파일(P3, `tests/anti_inertia/test_no_magic_numbers`).
1. **지오**: `geo/prep_geometry.py load_admin1` 이 NE 속성 `iso_3166_2`(예 `US-TX`) 를 항목 `code` 로 보존. `engine/stage.py MercatorStage.adm` 항목에 `code`. 옛 geo.pkl(code 없음) 에 area 이벤트가 오면 `StageError("geo.prep 다시")` — area 없는 영상(hormuz 골든)은 그대로 돈다 → **골든 25/25 dark·light 불변**이 합격 조건.
2. **스키마** `engine/events.py AreaEvent(_Event)`:
   ```yaml
   - type: area
     t0: {sid: cold_1, off: 0.0}      # 공통 시간 키 그대로
     t1: {sid: act1_3, edge: end}
     country: US                       # geo.yaml admin1 에 있어야 한다
     src: "AP 집계 · 2026-11-05 09:00 KST"   # 출처 줄 필수(빈 문자열 = 오류)
     items:                            # 1개 이상
       - {code: US-TX, col: dem, band: solid, status: called, delay: 0.0}
       - {code: US-MS, col: muted, band: lean, status: counting, delay: 1.2}
   ```
   `col` ∈ `registries.accents`(**`dem`·`rep` 를 추가** — colors 공통값 + light 테마값, 글자 아님·채움 전용), `band` ∈ `{lean, solid, landslide}` → 알파는 `rules area.alpha_bands`, `status` ∈ `{called, counting}` — counting 은 muted 빗금(`rules area.hatch`). `delay` 는 t0 기준 초(동→서 차례 등장). 연출 LLM 은 픽셀·알파 수치를 쓰지 않는다(P8).
3. **렌더** `engine/layers/areas.py draw_area`: `view.stage.adm[country]` 에서 code 로 rings 를 찾아 even-odd 채움 + 외곽선(`rules area.outline` 두께·알파 3단, `draw_country` 와 같은 방식) + `area.fade_sec` 등장. `engine/registry.py` `"area": Entry(ev.AreaEvent, draw_area, "map")`, `MAP_LAYER_ORDER` = `("island", "country", "area", "ships", …)`(country 바로 뒤). 콘티 판은 전편과 같게 그린다(지도 요소).
4. **규칙** `rules/video_rules.yaml`: `registries.event_types` 에 `area`, `registries.accents` 에 `dem`·`rep`, `colors.dem`·`colors.rep`(+`themes.light`), 새 블록 `area: {alpha_bands: {lean, solid, landslide}, outline: [[w, a] ×3], fade_sec, hatch: {spacing, width, alpha}}`(값은 Opus 가 light 지도 위 눈 확인으로 정해 R 에 컷을 첨부 — 감독이 확정), `direction_grammar` 한 줄("주별 결과는 area 로 — src 출처 줄 필수, 개표 중인 주는 status counting, 결과 데이터 파일과 다르면 오류"). `prompts/director.md` 문법 1~2줄(프롬프트는 템플릿 + 규칙에서 생성, P3).
5. **정직성 검사** `engine/checks.py`(hard): `[area-code-missing]`(admin1 에 없는 code) · `[area-src-missing]` · `[area-col]`(dem·rep·muted 외) · `[area-data-mismatch]`(**프로젝트 `data/state_results.yaml`** 의 해당 주·해당 레이스 `winner_party`·`status` 와 item 의 col·status 가 다르면 오류 — 데이터 파일 형식은 §4-3) · `[area-overlap]`(같은 t 에 같은 code 두 번). 경고: 같은 area 이벤트가 `area.max_items_warn` 을 넘으면 `[area-dense]`.
6. **예시·테스트**: `tests/fixtures/direction/area_minimal.yaml` 을 `tests/anti_inertia/test_prompt_schema_parity.py EXAMPLE_FILES` 에 등록. `tests/test_area_event.py`: 스키마(필수 키·band·status 리터럴), 1프레임 렌더 뒤 주 내부 픽셀이 dem/rep 색으로 바뀜(light·dark), 검사 5종 각각 실패 재현, 옛 geo.pkl + area → StageError. `python -m pytest -q tests/test_area_event.py tests/anti_inertia`(골든 dark·light 포함) 통과.
7. **문서**: `docs/handoff/06_OVERLAYS_AND_DATA_LAYERS.md` 에 area 절(규칙 키 인용, 값 복사 금지), CHANGELOG `Added`(v7.4.0 절 아래 "Unreleased — 병합 시 v7.5.0"). provenance `features_used.area` 수.
8. R(progress) 에 light 지도 위 area 컷 3장(본토 전체 w≈60 · 텍사스 권역 · 알래스카)을 artifacts 로 첨부 — 감독이 색·알파 확정(D 로 답한다).

## 4. M2 조사·원고
1. **감독 조사표 D-0291** 이 1차 자료다(출처 URL·수치·"2차 확인 필요" 표시). Opus 는 각 행을 WebSearch(allowed_domains: apnews.com·nbcnews.com·cbsnews.com·npr.org·주 선관위) 로 재확인한다. **AP 콜이 있는 결과만 "확정"**, 없으면 "개표 중"(status counting). 출처·시각마다 수치가 다르면 **원고는 AP 또는 NBC 하나를 고르고 귀속 + 집계 시각**(예 "NBC 추정, 11월 5일 기준"). 두 출처가 서로 다른 '사실'(연도 등)은 1차 출처(APP 표·AP)를 따르고, 못 정하면 뺀다.
2. 프로젝트: `new-project us_midterms_2026 --category geopolitics`, `order.yaml` 은 china 와 같은 틀(genre geopolitics, tempo breath, attribution_mode credits(D243), map_theme light, bgm `audio.bgm_default` 첫 곡, resolution 720p, decisions.gates "게이트 ①·② 사용자 승인"). credits.yaml 음악 행(W1.1 M1). 제목(안) 『뒤집힌 일곱 자리 — 2026 미국 중간선거』, 부제 "주별 결과·격전지·역사 맥락". 타이틀 카드 한 컷으로 길이 확인(M3). 제목은 감독이 게이트 ① 에서 확정.
3. **주별 결과 데이터 파일** `projects/us_midterms_2026/data/state_results.yaml`(schema_version 1, Pydantic 모델 `schemas/election_models.py` 신설 — C2): 주마다 `senate`·`governor`·`house_flips` 항목에 `winner`·`winner_party(dem|rep|none)`·`loser`·`pct`·`status(called|counting)`·`called_by(AP 등)`·`source_url`·`retrieved_at`. 이 파일이 `area` 검사·패널 수치·엔딩 카드 출처의 기준(한 곳). `data/documents` 로 등록.
4. **막 구성**(감독 설계 — 연출 LLM 이 다듬되 뼈대 유지; 문장 수는 안내):
   - **cold**(3~4): 11월 3일 밤, 지도에 주가 하나씩 색을 입는다(area 동→서) → 민주당이 하원·상원을 모두 되찾았다(AP/CNN 콜). 트럼프 집권 2년차 중간선거라는 한 문장.
   - **act1 "전국 성적표"**(10~12): 상원 54 대 44·미확정 2(NBC) — 뒤집은 7곳 이름 / 하원 과반(218) + NBC 추정 258(개표 중) / 주지사 36곳 중 민주 5곳 뒤집음·알래스카 집계 중 / 출구조사(NBC): 경제 "좋지 않다" 75%, 물가 책임 62%, 경제 신뢰 민주 43 대 공화 37, 트럼프 지지 38%(CBS). 패널: versus·dots. 해석은 귀속(NBC "트럼프 심판"·CNN).
   - **act2 "뒤집힌 일곱 자리"**(16~20): 지도 투어 — 텍사스(탈라리코 55 대 43, 1988년 이후 첫 민주 상원, 팩스턴 승복) → 캔자스(해밀턴, 1932년 이후 처음, 트럼프 +16 주) → 사우스캐롤라이나(앤드루스, 그레이엄 7월 사망 뒤 여동생 임명, 1998년 이후·첫 여성) → 아이오와(투렉, 2008년 이후) → 오하이오 보궐(브라운 복귀, 밴스 의석) → 노스캐롤라이나(쿠퍼, 틸리스 은퇴) → 메인(잭슨, 콜린스 약 30년 종료, 7월 말 출마). 각 주 `area` 강조 + marker + 초상 뱃지(PD 확인) + 기사 카드(AP·NBC·Texas Tribune·Maine Public 등). 유지 두 곳(조지아 오소프 59 대 41, 미시간 엘사예드) 한 문장씩.
   - **act3 "아직 안 끝난 곳"**(6~8): 미시시피(콜롬 대 하이드스미스, 수십~수천 표 차, 재검표 제도 없음, 남은 표) · 알래스카(펠톨라 대 설리번, 순위선택 집계 11월 중순) · 캔자스·알래스카 주지사 집계 중. area status counting(빗금). "결과가 바뀔 수 있다" 는 사실 서술로(예언형 결론 금지).
   - **act4 "주지사·주의회·지도 다시 그리기"**(10~14): 텍사스 이노호사(1990 리처즈 이후), 조지아 보텀스(미국 첫 흑인 여성 주지사 — 2건 이상 확인), 오하이오 액턴 대 라마스와미, 아이오와 샌드, 네바다 포드 대 롬바르도(현직 낙선), 플로리다 도널즈 유지(50.0 대 48.7, 플로리다 첫 흑인 주지사). 주의회: 펜실베이니아 트라이펙타(1993 이후, AP), MN·MI·NH·NC·WI 체임버(NCSL), 텍사스 주하원(2건 확인 때만). 재획정: 텍사스 새 지도에도 민주 순증 +1(The Hill), 캘리포니아 Prop 50 지역구 결과, 미주리 지도 주민투표 부결 — 해석("효과 없었다") 은 매체 귀속.
   - **act5 "역사 속의 2026"**(8~10): APP 표 1934~2022 — 대통령 당 평균 하원 −27·상원 −3, 하원 증가 3회(1934·1998·2002). 연도 카드 precedent: 1994·2010·2018·2022 + 2026(추정, 개표 중). 2026 상원 −7 이 어느 해 이후 최대인지는 **APP 표 값으로 계산한 것만** 쓴다. 하원 벨웨더 3곳(MI-7·KY-6·IN-5 트럼프 +17 지역)을 지도에서 한 번씩.
   - **act6 "다음"**(4~6): 2027년 1월 새 의회, 제프리스 하원의장 예정(NBC), 슈머 발언(CBS, 귀속), 트럼프·밴스 반응(2건 이상 확인된 것만). 주민투표 한 묶음(낙태권 VA·NV 통과, MO 폐지안 부결, ID 부결 / 유권자 신분증 OH·NC) 두 문장.
   - **ending**(2~3): 사실 한 줄 정리 + 엔딩 카드(출처·권리·보도 출처 장면별, 맨 아래 가장 작은 글씨 D85: "집계는 11월 N일 N시 기준 · 알래스카·미시시피 등 개표 중 · 해석은 각 매체 견해").
5. 원고 규칙: 발음 텍스트 숫자·기호·라틴 약어 금지(AP → "에이피", NBC → "엔비씨", GOP → "공화당"), 문장 끝 "~니다", `banned_phrases` 0(특히 '승부는'·'방향을 정한다'·'이것이 바로'·'~가 남는다' 끝맺음·예언형 결론), 인물 발언마다 quote 후보, 보도 문장마다 기사 카드 후보. 논쟁 해석(심판론·이란 전쟁 영향)은 양측 귀속, 같은 무게. `lint-script` 0.
6. 게이트 ① 자료: `gate-view` 전문 + `gate1_elements.md`(막마다 요소 한 줄) + 미디어 계획 표 + `state_results.yaml` 요약표(주·레이스·승자·상태·출처) 를 R(gate_request) + send_message. 감독이 사용자에게 보낸다.

## 5. M3 미디어·연출·콘티 판
- 미디어 등록: `article_register.py`(headline_ko 채움, 60초당 ≤2), 초상 `media_fetch.py search` → Commons 라이선스·피사체·시기 대조 → `portrait_fallback.py cutout` → `asset_library.py promote`(check 0, C8.7). 국기 us. C-SPAN 클립(허용 도메인, `config media.video_fetch`) 권리 기록 `scope: private_only`(D264). 위성 인셋 없음.
- 연출: `python -m script.plan` → 미디어 등록 → direction(diesel 문법: 문장마다 카메라 사유, 핀은 선 위 UF-142, 한꺼번에 튀어나오는 관계선 금지, 요소 공백 ≤ `element_gap.max_sec`(UF-160), 라벨 금지어(UF-161), 뱃지 최소 유지(UF-162), 사진 가운데 큰 액자(UF-148)) → `python -m audio.mix` → `python -m engine.render … --animatic` → **콘티 판 mp4(≤30 MB, `-c:a copy`) + gate-view 미디어 요약을 R + send_message**. 감독이 사용자에게 보내 흐름 검토를 받는다. 고칠 것 있으면 direction 수정 → 재콘티. 통과 → `--preview auto` 시트 R → 게이트 ②(사용자).
- C12: 앞선 영상 UF 전부 guarded 여야 게이트 ② 통과(`require_feedback_guards`) — 착수 때 `python tools/feedback_ledger.py` 로 open 0 확인, 아니면 첫 R 에 보고.

## 6. M4 전편·전달
- 720p 전편 → `artifacts/us-midterms-v7.4.0` orphan 브랜치(D186 방식: mp4·전달본 ≤30 MB·시트·provenance·phase_report·MD5SUMS·media_src). 최종 R(phase_report): 커밋 목록·테스트(관련 + anti_inertia, 전체 pytest 1회 C8.3)·checks hard 0·provenance(features_used 에 area·user_feedback_guards·private_only_assets)·컨택트 시트·육안 컷 6장 이상·차단 호스트 표·미포함 사유 표·길이·md5. 사용자에게는 감독이 보낸다(UF-144: 나오는 즉시).

## 7. 금지
사용자에게 묻기 · 구글맵 화면 · AI 생성·합성 이미지 · 권리 미확인 초상 · 확정 안 된 결과를 확정처럼 칠하기(AP 콜 없으면 counting) · 출처 없는 수치 · 발음 텍스트 숫자·라틴 약어 · banned_phrases · card 이벤트 · 새 무대(Albers 등) 신설 · force push · PR · main 푸시 · 모델 식별자(산출물) · D 파일 수정 · 대용량 미추적 파일 커밋(tts/·out/·prev/·media/ .gitignore 확인) · yt-dlp 봇 우회.

## 8. 폴백
- Commons 429 → upload.wikimedia.org 원본 직접 + WebSearch 라이선스 대조(R-0292 선례). 초상 권리 미확인 → 직함 quote. C-SPAN 못 받으면 사진 액자(clip 0 허용, media_note).
- APP 표를 도구로 못 읽으면 act5 는 "평균 −27·−3·증가 3회"(2건 이상 일치) 만 쓰고 연도별 값은 뺀다.
- 미시시피·알래스카가 콘티 판 전에 확정되면 data 파일·원고 갱신(원고가 바뀌면 게이트 ① 재승인 — PIPELINE-AP-017).
- 세션 한도로 끊기면 감독이 새 세션을 띄운다 — 커밋·푸시를 작게 자주.

## 9. 보고 순서
① ack R(환경·호스트 표·C12 open 수·조사 착수) ② M1 progress R(area 컷 3장 + 테스트 수) ③ sources/claims/data 초안 수 R ④ 게이트 ① 자료 R(gate_request) ⑤ 콘티 판 R ⑥ 프리뷰 시트 R(gate_request) ⑦ phase_report. 매 R 뒤 `send_message(session_017Yuw8ixNRzov4VpELs53Xx)`.
