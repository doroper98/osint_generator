---
id: D-0225
from: fable
to: opus
kind: directive
responds_to: [D-0206(계획), D232]
phase: "P3-0"
version: v7.2.0 → v7.3.0
status: open
priority: urgent
supersedes: []
---

# 새 영상 「경유의 길 — 사흘에 한 번」(diesel_road_2026) — 밤샘 제작 + v7.3.0 flight·inset·press_cited 등록 + 자산 승격·main 병합

## 0. 사용자 원문(2026-10-17 밤, 감독 세션)
- "원고나 콘티의 나의 검토 없이 니 검토로 바로 내일 아침까지 영상이 제작될 수 있도록 해."
- "영상 제작 완료 되면 이번에 만들어진 자산들(드론 타격, 위성 사진, 새로운 인물 사진, 그래프 조판 등) 커밋 푸시 머지 해서 자산으로써 담아."
- "영상에 인물이 필요하면 인물 등장씬을 적극적으로 작동시켜. 기사도 적극적으로 조판하고. 이번에는 좀 방대한 영상이 될 수 있겠다?"
- 결정 표 U1~U8 에 이의 없음 → 권고안 채택(DECISIONS D232). 환경 허용 도메인: gibs.earthdata.nasa.gov · raw.githubusercontent.com · cdn.jsdelivr.net · commons.wikimedia.org · upload.wikimedia.org.

## 1. "검토 없이"의 범위(D-0223 §1 과 같다 — 코드 게이트는 우회하지 않는다)
- 건너뛰는 것 = 사용자 검토 대기. 단계는 전부 그대로: 원고 → 게이트 ① → 음성 → 연출 → `audio.mix` → 콘티 판(require_animatic) → 프리뷰 → 게이트 ② → 전편.
- 게이트 ①·② 는 `--by fable`, comment "사용자 위임 D232(아침 본영상 시청)". 감독 검수 2곳: ① 원고 검토 자료(gate-view 원고 전문·출처 표·린트) ② 콘티 판 mp4 + 프리뷰 시트. 각각 R 로 올리고 **감독 세션에 send_message**(session_016v5HgxdsPNKcUYQ94ZkAoo)로 알린다. 감독은 밤새 깨어 있다.
- C12 장치·검사 hard 0·권리 기록·AI 생성 금지·발음 텍스트 숫자 금지 — 그대로.

## 2. 시간 예산(KST) 과 순서 — 한 단계가 늦어지면 §7 폴백
| 단계 | 목표 시각 | 산출 |
|---|---|---|
| 0 준비 | ~23:00 | 브랜치·의존성·호스트 확인(§2.0) |
| 1 v7.3.0 엔진 | ~01:00 | flight·inset·press_cited 등록, 골든 불변, 커밋 4개(§2.1) |
| 2 자산 | ~02:00 | 초상 6인·위성 인셋·기사 카드·시리즈 3개 등록(§2.2) |
| 3 원고 | ~03:00 | 게이트 ① 자료 → 감독 판정(§2.3) |
| 4 음성·연출·콘티 판 | ~05:00 | animatic.mp4 + 프리뷰 시트 → 감독 판정 → 게이트 ②(§2.4) |
| 5 전편 | ~06:30 | artifacts 브랜치, R 최종(§2.5) |
| 6 승격·병합 | ~07:30 | promote, 전체 pytest, main 병합(§2.6) |

### 2.0 준비
- `git fetch origin && git checkout claude/flight-event-sat-inset-plan && git pull`. 작업·교신 브랜치 = **이 브랜치**(D129 방식). R 파일도 여기.
- 호스트 5개 curl 확인. 하나라도 막히면 R 로 보고하고 그 호스트가 필요한 작업만 §7 폴백.
- 의존성: requirements·requirements-engine, `python tools/fetch_data.py fonts`(IBM Plex 확인), 초상용 rembg(u2net_human_seg 모델이 GitHub release 에서 안 받아지면 R 보고 → 뱃지 수 줄임).
- 읽기: D-0206 전문(§1~§9), CLAUDE.md C0·C8·C12, docs/handoff/15, WORKFLOWS W0·W1, DECISIONS D232·D233, `projects/strike_demo_2026/`(시험본 기하·인셋·출처 json).

### 2.1 v7.3.0 엔진 — D-0206 §2~§6 그대로 + 결정값
- 규칙 토큰(§3)에서 아이콘 크기만 U6: `icon.size_px: {drone: 16, missile: 18, jet: 19}`. 드론 다각형은 시험본 `render_demo.py` 의 샤헤드/게란 실루엣(`drone`·`drone_body`), 미사일은 순항미사일 다각형 — 좌표를 규칙 토큰으로 옮긴다(코드 리터럴 금지).
- U2 인셋: media kind `inset` + `media.density.inset_*` + `credit_formats.inset`. U1 권리: 레지스트리 라이선스 허용 목록에 `NASA GIBS (public domain)`·`Copernicus Sentinel data (free, full and open)` 한 곳만.
- U4 데이터: `data.sources_allowed` 에 `press_cited` 종류(코드가 받지 않는 값 — 레코드에 `cited: {outlet, date, url}` 필수, `transform.formula: "보도 인용값(매체·날짜)"`). 추정치 없는 달은 레코드에 없음 = 선을 끊어 그린다(보간 금지). 시리즈 레이어가 결측을 선으로 잇는다면 끊는 분기를 추가하고 테스트.
- U7 몽타주: `flight` 와 별개로 **기존 `boom`+`marker` 를 문장 하나에 여러 개 두는 것**을 검사 [one-element]가 막는다면, `salvo: true` 를 가진 `boom` 묶음(토큰 `boom.salvo_stagger_sec: 0.9`)을 허용하는 최소 변경 + 영상당 1회 검사 `[salvo-once]`. 검사가 막지 않으면 변경 없음(연출에서 stagger 만).
- U8 dark: direction `stage_config.mercator.theme: dark` + `theme_reason`.
- 골든 25컷(light·dark) md5 불변. 커밋: (a) 규칙·스키마·렌더러·예제·테스트 (b) 권리 목록 (c) 밀도·데이터 출처 규칙 (d) 문서·VERSION 7.3.0·CHANGELOG·YAML 헤더. 각 커밋 푸시.

### 2.2 자산(C8.7 공용 자산 우선·promote)
- **초상 6인**(Commons → `tools/portrait_fallback.py cutout --style engraving` → 권리 기록 → promote): 스콧 베선트(미 재무부 공식 초상, PD), 올레크 코제먀코(연해주 지사, kremlin.ru CC BY 4.0 또는 Commons), 알렉산드르 노박(government.ru CC BY 4.0), 블라디슬라프 블라시우크(president.gov.ua CC BY 4.0), 강유정(청와대 공식, KOGL 1유형), 김정관(산업통상부 공식, KOGL 1유형). 권리가 확인 안 되는 인물은 **뺀다**(뱃지 없이 직함 카드). 기존 6인(트럼프·푸틴·젤렌스키·이재명·네타냐후·하메네이)은 그대로.
- **위성 인셋**: 기존 3장(랴잔·라스라판·하르그, `projects/strike_demo_2026/inset_*.png` + `inset_sources.json`)을 kind inset 으로 등록. 추가 시도 2곳: 키리시(59.44 N, 32.08 E 근방)·볼고그라드(48.52 N, 44.59 E 근방) — 같은 GIBS HLS 방식, 시설 식별 안 되면 넣지 않는다.
- **기사 카드**(레지스트리 article, 프레스 사진은 권리 있는 것만): 가디언 2026-10-06(한국산 경유·제재 선박), 로이터/NV 2026-08-07(7월 말 3만t), IEA 커멘터리(사흘에 한 번), 로이터 2026-05-29(경유 생산 −20%), 블룸버그 2026-10-16(수출 7년래 최저), CNBC 2026-10-09(트럼프·푸틴 경유 거래), NBC(트럼프 "수치"), 경향 2026-09-06(물량 남는데 빗장), 한경 2026-10-04(수출 제한·항공유), 경향 2026-10-07(청와대 반박), SPN/파이낸셜뉴스 2026-10-08(정부 "제재 품목 아님"), 로이터 조사 2026-10-16(걸프 84개 사이트 135회), MEES 2026-08-28(호르무즈 경유), 카네기 2026-10(경유 거래 분석). 후보 문장에는 반드시 기사 카드(UF-102, [article-unused]).
- **데이터 시리즈 3개**(press_cited, 단위·출처는 §4 표 그대로): `ru_refinery_runs_2026`(mb/d), `ru_diesel_seaborne_exports_2026`(kb/d), `gulf_diesel_net_exports_2026`(kb/d). 경유 생산(3~5월 세 점)은 시리즈가 아니라 카드.

### 2.3 원고(pid `diesel_road_2026`, 장르 지정학, 90~125문장, 7~10분 — U5 기준 10분(사용자 수정))
막 구성(감독 분석 2026-10-17 채팅 확정):
- **콜드 오픈**(5~6문장): 10월 15일 새벽 랴잔 재타격. 휴전이 깨진 순간.
- **1막 "사흘에 한 번"**(25~30): 우크라이나 → 러시아 정유소(키리시·랴잔·볼고그라드·노보쿠이비셰프스크·사라토프), 표적 논리(유전이 아니라 정제), IEA 수치, 경유 생산 3~5월 카드, 정제 처리량 시리즈 A, 수출 시리즈 B, 러시아 수출 금지·수입 급증(인도 휘발유 70%·한국 경유 2위).
- **2막 "철도 끝"**(20~25): 극동 지리(현지 정제 55~65%, 시베리아 철도), 콤소몰스크(로스네프트 800만t)·하바롭스크(NNK 500만t), 5월 연료난, 구매자 = 로스네프트·NNK(Kpler) — "극동 정유소 주인이 샀다"는 **감독 추론**이므로 "Kpler 가 확인한 구매자는 이 두 회사이고, 두 회사는 극동 정유소를 가지고 있습니다" 수준으로만. 한국 쪽: 수출 관리(전년 동월 100% 상한, 최고가격제), 1~8월 경유 수출 −3.4%, 정유사 "물량 남는데", 울산→블라디보스토크 이틀, 7척 14회 17만6천t, 제재 선박 3척·허위 목적지(니가타·싱가포르)·여수 해상 환적, 한국 정부 입장(제재 품목 아님·조사 중), 우크라이나 비판·포로 송환 갈등·대사 소환.
- **3막 "걸프"**(보조 무대, 20~25): 2월 28일 개전·호르무즈, 3월 18일 사우스파르스(귀속 논쟁 → 양측 병기, 비행 금지·링만), 라스라판 콜드박스(3~5년), 푸자이라 19회, 동서 파이프라인 펌프장 9월 10일, 하르그섬(석유 시설 미타격), 걸프 정부 "요격 파편" 34건 vs 로이터 "의도적" versus 패널, 걸프 경유 순수출 시리즈 D, 호르무즈 통과 경유 7월 16.5만.
- **4막 "역류"**(15~20): 로스네프트 SDN(2025-10-22) → 일반허가(2026-03) → 트럼프·푸틴 경유 거래(10/9, 2027-04 까지), 베선트, "수치", 에너지 휴전(10/11)과 붕괴(10/15), 러시아 → 하르키우·폴타바 가스 타격, 노박 "월 300만~350만t", 한국의 방패는 한국법이 아니라 미국의 변심. 이재명 "영원한 적도 우방도 없다"(10/13).
- **엔딩**: 네 전장을 관통하는 한 줄 + 엔딩 카드(출처, 맨 아래 가장 작은 글씨: "비행 경로·출발 위치는 개략 표현 · 51%·31%는 우크라이나 측 발표로 독립 검증 전").
- 귀속 규칙: §3. 인물 발언 문장마다 quote 후보 표시, 기사 출처 문장마다 기사 카드 후보 표시(UF-101·102). 발음 텍스트 숫자·기호 → 한글. banned_phrases 0.
- 원고가 10분을 넘으면 U5: 1부(콜드 오픈~2막) 먼저 완성, 2부는 아침 보고에 원고만.

### 2.4 음성·연출·콘티 판
- 음성 C0.2 표준(M3 ×0.95, final_fall C, MMS). BGM `audio.bgm_default` 첫 곡(Mario Bava).
- direction: theme dark + theme_reason("타격 중심 군사 전황 — D154 장르 예외, D232 U8"). 주 무대 = 메르카토르(울산~블라디보스토크~시베리아~서부 러시아~우크라이나, 경계는 geo.yaml 티어로), 보조 무대 = 걸프(암전 1회 진입·1회 복귀, 전환 2회).
- 1막: 카메라 region(w 20~30) 고정, 문장마다 `flight`(drone, origin = 우크라이나 북동부 개략 한 점으로 통일) + 맞은 자리 `marker(icon: boom)` 유지. 인셋은 랴잔·(키리시) 2곳 이하. 콤소몰스크는 보도 엇갈림 → marker + 카드만. "사흘에 한 번" 집계 문장 1회만 몽타주(U7).
- 2막: continental_route(w 88~96) 동쪽 이동 1회, 철도 `route`, 울산→블라디보스토크 `route` + `tanker_loop`. 뱃지: 이재명·강유정·김정관·코제먀코·블라시우크·젤렌스키.
- 3막: strait(w 12~16). 이란 → 라스라판·푸자이라·펌프장 `flight`(missile, origin 이란 남부 해안 개략). 사우스파르스 `boom` 만. 하르그 `marker` 만. versus 패널. 뱃지: 네타냐후·하메네이.
- 4막: `quote` 트럼프·젤렌스키·베선트·노박·푸틴, 러 → 하르키우·폴타바 `flight`(drone). 시리즈 패널 A·B(1막 끝)·D(3막 끝).
- 밀도: 기사 60초당 ≤2, 사진 분당 1 목표, 인셋 U2 값. static_window ladder 준수, 이유 없는 카메라 이동 금지.
- `python -m audio.mix` → `python -m engine.render projects/diesel_road_2026 --animatic` → 콘티 판 mp4 + 프리뷰 시트를 R 로 감독에게. 감독 판정 뒤 `approve --gate preview_approval --by fable`.

### 2.5 전편
- 720p 전편 → `artifacts/diesel_road_2026-v7.3.0` orphan 브랜치 푸시(D186 방식). R 최종: md5·길이·LUFS·checks(hard 0)·provenance(features_used 에 flight·inset·series press_cited, user_feedback_guards)·컨택트 시트 경로·육안 확인 컷 6개 이상.
- 사용자에게 직접 보내지 않는다. 감독이 아침 전달.

### 2.6 자산 승격·main 병합(사용자 지시 D232 ②)
- `python tools/asset_library.py promote projects/diesel_road_2026`(초상·인셋·휘장), 기사·시리즈는 레지스트리 커밋으로 이미 공용.
- 전체 pytest(C8.3 main 병합 직전 1회, `-m "not slow"` 아님 — 전체). 실패가 있으면 고치고, 못 고치면 병합하지 않고 R 보고.
- 병합: `git checkout main && git pull && git merge --no-ff claude/flight-event-sat-inset-plan && git push origin main`(force 금지, PR 없음 — 사용자 명시 지시). 병합 기록 커밋 1개("v7.3.0: main 병합 기록 — 전체 pytest N passed").

## 3. 사실·귀속(G4·C9)
- 확정 출처 사용 가능: IEA 커멘터리·OMR(사흘에 한 번, 6월 20년래 최저, 경유 −30%), 로이터 산정(정유소별 상태·3~5월 경유 생산·1~9월 −14%), 블룸버그(7월 3.6 mb/d, 수출 7년래 최저), Vortexa(수출 kb/d), 가디언(7척 14회 17만6천t, 제재 3척, Layla·Astoria·Chongchon, Kpler 구매자 로스네프트·NNK), CREA(8월 수입 7배·인도 70%), 로이터 조사(걸프 84개 사이트 135회·34건 공식 성명), 카타르가스 CEO(3~5년), 한국 정부 발표(10/7·10/8), 산업부(수출 상한 100%·1~8월 경유 −3.4%).
- 양측 병기 의무: 사우스파르스 귀속(이스라엘/미국), 걸프 피해(정부 "요격 파편" vs 로이터 "의도적"), 8월 한국산 수입량(CREA 1만8천t vs Kpler 11만2천t), 51%(우크라 국방부, 미검증).
- 본문 금지: 콤소몰스크 "피격"(엇갈림 → "화재 보도가 있었으나 확인되지 않았습니다"), 나프토가스 "공격 2배"(단일 매체 익명), 러시아 구매 가격·프리미엄(미확인), "로스네프트·NNK 가 자기 주유소를 채우려고"(추론 → §2.3 문구로 한정).
- 숫자는 발표값 그대로, "약" 표기 유지. 환산값(2월 수출 760 kb/d 등)은 화면에 "환산" 표기.

## 4. 시리즈 값(press_cited, 감독 그래프 2026-10-17 각주가 정본)
| 시리즈 | 단위 | 값(월: 값 · 출처) |
|---|---|---|
| ru_refinery_runs_2026 | mb/d | 3월 5.1(IEA OMR 3월) · 4월 4.7(IEA OMR 5월) · 6월 3.8(IEA 커멘터리) · 7월 3.6(블룸버그/EA Analytics) · 9월 3.9 "4 미만"(로이터 산정, open 마커) · 기준선 2025 1~9월 평균 ≈5.3(197 Mt 환산) |
| ru_diesel_seaborne_exports_2026 | kb/d | 1월 963(LSEG) · 2월 760(LSEG 2.85 Mt 환산) · 5월 740(Vortexa) · 7월 171(S&P 713 kt 환산) · 8월 150(Vortexa) · 9월 144(Vortexa/블룸버그) · 10월초 146(Vortexa) |
| gulf_diesel_net_exports_2026 | kb/d | 2월 1,450(IEA 9월 OMR, 1.4~1.5 mb/d 범위) · 8월 390(IEA) · 9월 ≈670(언론 집계 5개국 = IEA 10월 '중동+러시아 820' 역산 일치, "≈" 표기) |
결측 달은 레코드 없음(보간 금지). 각 레코드 `cited` 필수.

## 5. 보고
- 단계마다 짧은 R(progress) + 게이트 2곳은 send_message 로 감독 호출. 결정이 필요하면 decision_request R + send_message, 막히지 않는 작업은 계속.
- 아침 보고(최종 R)에 §7 폴백 적용 여부를 반드시 적는다.

## 6. 금지
- 구글맵 화면, AI 생성·합성 이미지, 권리 미확인 사진·초상, 발음 텍스트 숫자, banned_phrases, force push, PR, 모델 식별자(산출물), D 파일 수정, 추적 대상 아닌 대용량 파일 커밋(tts/·out/·prev/·assets/ 는 프로젝트 .gitignore 에 먼저).

## 7. 폴백(시각 기준)
- 01:30 까지 `flight` 미완 → 1막·3막·4막 타격은 `boom`+`marker(icon: boom)` 문법으로 진행, `flight` 는 아침 보고에 "미등록" 명기. 인셋(U2)·press_cited(U4)는 독립이므로 계속.
- rembg 모델·Commons 실패 → 해당 인물 뱃지 생략, 직함 카드.
- GIBS 추가 인셋 실패 → 기존 3장만.
- 원고 10분 초과 → U5 1부만 전편.
- 전체 pytest 실패를 07:30 까지 못 고침 → main 병합 보류, 브랜치만 푸시, R 에 실패 목록.

---

## 8. 추가 지시(D234, 2026-10-17 22:40 KST) — U1·U6 변경
- **U6**: `flight.icon.size_px: {drone: 11, missile: 13, jet: 14}`(계획값). §2.1 의 16~19 는 무효.
- **U1**: 위성 인셋은 **구글맵급 상업 타일 허용, 비공개 시청 한정**. 미디어 레지스트리 항목에 `scope: private_only`, `license: "Esri World Imagery (Maxar et al.) — 비공개 시청 한정, 사용자 결정 D234"` 처럼 적고 출처 줄은 "위성 · YYYY · Esri/Maxar"(구글이면 "Google/Maxar"). 공개 전환 시 교체 의무를 레지스트리 주석에 남긴다. 권리 허용 목록에는 이 라이선스를 `private_only` 플래그와 함께 추가하고, provenance 에 `private_only_assets: [...]` 를 기록한다(공개용 산출물이 아님을 코드가 말하게).
- 구현 경로 우선순위: ① `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`(z 16~17, 타일 4~9장 모자이크, 키 불필요) — 호스트 허용 여부를 curl 로 먼저 확인 ② 환경 시크릿 `GOOGLE_MAPS_API_KEY` 가 있고 maps.googleapis.com 이 열려 있으면 Static Maps(`maptype=satellite`, zoom 15~16, 640×640, scale 2) ③ 둘 다 안 되면 기존 NASA HLS 3장(U1 원안) 으로 진행하고 아침 보고에 "상업 타일 호스트 미허용" 명기.
- 대상 5곳(랴잔·키리시·볼고그라드·라스라판·하르그섬) + 가능하면 노보쿠이비셰프스크·사라토프. 이미지를 Read 로 보고 시설이 식별되는지 확인한 뒤 등록. 밀도는 U2 값 안에서 장면당 ≤3.

## 9. 추가 지시(UF-103, 2026-10-17 22:50 KST) — 위성 인셋은 원형
- 사용자 원문: "위성사진은 네모낳게 표시하지 말고 동그랗게 표시해."
- 구현: 위성 인셋(`flight.inset` 및 kind inset 의 `cutout`)은 **원형 마스크**로만 그린다. 규칙 토큰 `flight.inset.shape: circle`(다른 값 없음 — 사각형 금지), 지름 = `inset.w_px`, 테두리 = 가는 흰 선(기존 상자 선 알파 재사용), 출처 줄은 원 아래 가운데 정렬. 콘티 판 자리표시도 원형. 위성 타일은 정사각 크롭 뒤 원으로 잘라 중심에 시설이 오게 한다.
- 장치(UF-103 guarded 로 올릴 것): 렌더 테스트 — 인셋 프레임에서 원 바깥 네 모서리 픽셀이 바탕색과 같고 중심은 다르다(전편·콘티 판 둘 다). 원장 `guards` 에 rule·test 를 적고 status guarded.
