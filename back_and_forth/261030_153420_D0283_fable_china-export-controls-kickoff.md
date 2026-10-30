---
id: D-0283
from: fable
to: opus
kind: directive
responds_to: [D-0282]
phase: "CN1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 새 영상 『중국의 기술 수출통제 확대(2026.10)』(china_tech_export_controls_2026) — 묻지 않고 완성본까지

## 0. 권한·사용자 원문(D-0282, 커밋 929b4b2)
- 사용자 원문: "fable 감독 세션 하나 띄워서 … 나한테 뭐 묻지 말고 새로 띄운 fable 에서 알아서 영상 완성본을 나한테 전달하도록 해."
- 감독 세션(이 D 의 작성자) = `session_017Yuw8hTb2zPgG7PvjAbjyu`. **모든 R 은 이 세션 id 로 `send_message`** 한다(부모 감독 session_017Yuw8kbxf9Vxri6LoH5Je4 에는 보내지 않는다 — 쇼케이스 트랙과 독립).
- 게이트 ①·② 는 **감독이 사용자 위임으로 승인**한다. Opus 는 승인 명령을 치지 않는다 — 자료를 R 로 올리고 감독 판정을 기다리되, 막히지 않는 작업(자산·연출 준비)은 계속한다.
- 소재 원문(감독 추천안 2번): "중국의 기술 수출통제 확대 (10/14~10/26) — 드론군집(10/14), AI·바이오·태양광 40개 기술 초안(10/16, 의견수렴 11/15), 터널굴착기·건설기계 허가제(10/19, 11/18 시행), 영업비밀 보호 제재 도구 초안(10/26)이 보름 안에 쏟아졌습니다. 핵심은 "제품은 팔고, 만드는 능력은 안 판다"는 전환입니다. 한국 언론 보도가 얇아 설명 가치가 크고, 지도(민감 지역 허가제)와 시간축(공고 날짜)이 한 세계로 묶입니다. 페로브스카이트 태양광·세포치료 공정·GTX 굴착기까지 한국 산업과 닿습니다."

## 1. "묻지 않고"의 범위(D-0225 §1 과 같다 — 코드 게이트는 우회하지 않는다)
- 단계는 전부 그대로: 소스 → claims → 원고 → 게이트 ①(감독) → 음성 → 미디어 등록 → 연출 → `audio.mix` → 콘티 판(require_animatic) → 프리뷰 → 게이트 ②(감독) → 전편 → 전달본.
- 게이트 승인은 감독이 `--by fable`, comment "사용자 위임 D-0282". Opus 는 게이트마다 자료를 R 로 올리고 **send_message 로 감독을 호출**한다.
- C12 장치(앞선 영상 UF 전부 guarded 상태여야 게이트 ② 통과)·검사 hard 0·권리 기록·AI 생성 금지·발음 텍스트 숫자 금지·banned_phrases 0 — 그대로.

## 2. 준비(§2.0) 와 환경
### 2.0 브랜치·환경
- `git fetch origin && git checkout claude/china-export-controls-2026 && git pull --rebase origin claude/china-export-controls-2026`. 작업·교신 브랜치 = **이 브랜치**. 커밋 첫 줄 `v7.4.0: …`(VERSION 과 일치, hook). `git config core.hooksPath .githooks`.
- 환경 복원 = R-0284 §환경 그대로: pip(requirements·requirements-engine) + pycairo·numpy·scipy·shapely·librosa·onnxruntime·cairosvg·yt-dlp **2026.10.21**·torch cpu·torchaudio·pyworld·uroman·rembg·`setuptools<81`; apt ffmpeg·fonts-noto-cjk; FONTCONFIG(12-unhinted-grayscale 제외); `python tools/fetch_data.py fonts ne tiles flags supertonic mms_fa bgm people`. 표준 음성 Supertonic 3 M3 ×0.95(C0.2 — 묻지 않는다).
- **네트워크 실측(감독 컨테이너, 같은 환경 2026-10-30 15:30 KST)**: 컨테이너 curl 로 열린 호스트 = commons.wikimedia.org·upload.wikimedia.org·youtube.com·server.arcgisonline.com·pypi.org·huggingface.co. **막힌 호스트** = mofcom.gov.cn·english.mofcom.gov.cn·reuters.com·scmp.com·globaltimes.cn·yna.co.kr·news.cn·cctv.com·whitecase.com·pillsburylaw.com·orfonline.org.
  → 출처 대조는 컨테이너 curl 이 아니라 **세션 도구 WebFetch·WebSearch**(Anthropic 경유)로 한다. 그래도 못 여는 URL 은 sources.json `note` 에 "컨테이너·도구 차단, 2차 보도로 대조" 라고 적는다(diesel src_art_0001 선례). 차단 목록은 최종 R 에 표로.
- 환경 복원 중에도 §3 조사(WebSearch·WebFetch)는 병행한다.

## 3. 사실·출처(G4·C9) — 1차 출처 대조 의무
- **1차 출처 = MOFCOM 공고 원문**(mofcom.gov.cn 공고·회견 녹취, 영문판 english.mofcom.gov.cn). 수치(기술 40개·AI 23·바이오 5·태양광 12 / 금지 14·제한 26 등)와 날짜(10/14·10/16·10/19·10/26·11/15·11/18)는 **공고 원문 또는 신화·CCTV 등재본으로 대조된 것만** claims 에 넣는다. 출처별로 수치가 다르면 원문 값을 쓰고, 원문을 못 열면 양측 값을 귀속해 병기하거나 수치를 빼고 "40개 안팎" 같은 표현 금지 — 수치를 빼라.
- 감독 조사표(1차 출처 URL·공고 번호·수치)는 **D-0284 로 뒤따른다**(감독이 지금 조사 중). D-0284 전에는 Opus 도 독자 조사를 시작하되, claims 확정은 두 조사가 맞는 것만.
- 2차 자료(법무법인 알림 Pillsbury·White & Case, ORF, Global Trade Alert)는 **해설 근거로만** — 기사 카드 아님(§5). 보도는 로이터·SCMP·블룸버그·신화·Global Times·연합·한경·전자신문 등 **등재 가능한 보도 매체**.
- MOFCOM 입장("특정 국가를 겨냥한 것이 아니다, 정례 목록 정비")은 **당사자 발언으로 귀속해 반드시 넣는다**(양측 같은 무게, C0 경계). 서방·업계의 "기술 봉쇄" 해석도 귀속.
- **지도에 지어내지 않는다**: MOFCOM 이 "민감 지역·국가 목록"을 공표하지 않았으면 지도에 특정 국가를 허가제 대상으로 칠하지 않는다. 허가제/등록제 **구분 설명**만(카드·패널). 공장·항만·회사 위치는 출처가 있는 지점만(W1.1 M5).
- 한국 접점은 **출처 있는 것만**: ① 국내 지하 공사(GTX 등)의 중국산 TBM 의존(국토부·업계 보도·국회 자료 중 하나 이상), ② 페로브스카이트 탠덤 개발사(한화큐셀·유니테스트 등 — 보도), ③ 세포·유전자 치료 위탁생산(삼성바이오로직스·SK 등 — 보도). 출처가 없는 항목은 **뺀다**(원고에 "한국도 영향" 같은 무출처 일반화 금지).
- 배경 맥락(2025-10 희토류 통제 → 부산 휴전 → 2026-09 정상회담 뒤 휴전 2027-01-10 연장, 2026-06-22 MP Materials·USA Rare Earth 통제 목록)은 **보도 출처 1건 이상**이 있을 때 한 장(act2) 에서 "원리 대비"로만 쓴다.
- "제품은 팔고 만드는 능력은 안 판다" 는 감독 해석 — 원고에서는 **ORF·법무법인 해설에 귀속**하거나 "이번 조치가 겨누는 것은 완제품이 아니라 생산 공정·설계 능력입니다" 같은 **사실 서술(목록 항목이 기술·공정임)** 로 쓴다. banned_phrases 주의: "핵심은 … 입니다" 문장 끝 패턴 금지, "겨누/겨냥" 과 제도 주어 결합 금지(패턴 있음 — 린트가 잡는다. 대신 "대상은 …" 로 쓴다).

## 4. 프로젝트·원고
- pid `china_tech_export_controls_2026`, `new-project --category geopolitics`. `order.yaml`: genre geopolitics, tempo breath, attribution_mode credits(D243 — 보도 귀속은 엔딩 크레딧, 당사자 발언·논쟁 해석은 본문 귀속), length "내용이 정한다"(목표 3~5분 ≈ 문장 45~70), map_theme light(D154 장르 기본, 감독 결정 — 지경학), bgm `audio.bgm_default` 첫 곡(기준 작품과 같다), resolution 720p, decisions.gates "게이트 ①·② 감독 위임(D-0282)". credits.yaml 에 음악 행(W1.1 M1).
- 제목(안): 『제품은 팔고, 능력은 안 판다 — 중국 기술 수출통제 보름』. 부제: "드론·AI·태양광·굴착기, 그리고 한국". 타이틀 카드 한 컷으로 길이 확인(M3). 제목은 감독이 D-0284 에서 확정할 수 있다.
- 막 구성(감독 설계 — 연출 LLM 이 다듬되 뼈대 유지):
  - **cold**(3~4문장): 11월 18일부터 중국 TBM(터널굴착기)·대형 건설기계 수출이 허가제가 된다 — 한 장면(10/19 공고). 왜 한국 지하 공사 이야기로 이어지는지 한 문장 예고.
  - **act1 "보름"**(14~18): 10/14 드론 관련 통제 개정 → 10/16 수출금지·제한 기술 목록 개정 초안(공고 번호·기술 수·분야·예시 3개: AI 악성코드 생성·변이, 세포·유전자 치료 공정 플랫폼, 페로브스카이트·탠덤 모듈 생산기술; 오픈소스 공개도 기술 수출로 취급; 등록 의무; 의견수렴 11/15) → 10/19 TBM 허가제(11/18 시행; 허가제·등록제 구분) → 10/26 영업비밀 보호 특별규정 초안(역외 침해 제재 도구). 시간축 보조 무대에서 네 날짜가 **한 세계**(w 고정, §6).
  - **act2 "제품과 능력"**(10~14): 2025-10 희토류 통제(제품·소재의 수출 통제)와 이번(기술·공정·설계의 통제)의 차이. MOFCOM 입장(정례 정비·특정 국가 아님) ↔ 해설(기술 봉쇄·대칭 조치) 양측 귀속. 미·중 휴전(2027-01-10 만료) 맥락 1~2문장(출처 있을 때).
  - **act3 "한국"**(10~14): 출처 있는 접점만(§3). 없는 항목은 장면 수를 줄인다.
  - **act4 "다음 날짜"**(4~6): 11/15 의견수렴 마감 → 11/18 시행 → 2027-01-10 휴전 만료. 무엇이 정해지고 무엇이 미정인지.
  - **ending**(2~3): 사실 한 줄 정리 + 엔딩 카드(출처·권리·보도 출처 장면별, 맨 아래 가장 작은 글씨 미검증 표기 D85).
- 원고 규칙: 발음 텍스트(tts) 숫자·기호·라틴 약어 금지(TBM → "티비엠", AI → "에이아이", GTX → "지티엑스", MOFCOM → "중국 상무부"). 문장 끝 "~니다". 인물 발언마다 quote 후보, 보도 문장마다 기사 카드 후보(UF-101·102). `lint-script` 0. **gate-view 자료 + `gate1_elements.md`(막마다 요소 한 줄, showcase_geo 형식) + 미디어 계획 표**를 R 로 올리고 감독 호출.

## 5. 미디어(UF-139 밀도 1.5/분 hard, Commons 탐색 의무, 등재 0 금지)
- **기사 카드**(`article_register.py`, headline_ko 채움, 60초당 ≤2): 공고 4건 각각의 보도 1건 이상(로이터·SCMP·블룸버그·신화·GT 중 등재 가능한 것), 한국 접점 보도(한경·전자신문·연합·조선비즈 등). 법무법인 알림은 기사 카드로 조판하지 않는다(해설 출처로 claims 에만).
- **사진**(Commons, 라이선스·피사체·시기 대조): 상무부 건물(北京 商务部), 터널굴착기(TBM 커터헤드 — 중국철건중공 CREG·Herrenknecht 등 Commons 사진), 페로브스카이트 셀·탠덤 모듈 연구 사진, 드론 군집 비행(공연·전시 사진 PD/CC), 세포배양·바이오리액터, 희토류(배경 한 장), GTX·지하철 터널 공사(한국 Commons 사진 있으면). 자료사진 표기.
- **클립 액자(UF-141, 원음·덕킹)**: MOFCOM 정례 회견(대변인 何亚东 허야둥) 또는 CCTV·CGTN 보도 클립. 받기 경로 우선순위: ① Commons 영상 ② **YouTube 공식 채널(CGTN·CCTV Video News Agency·新华社)** — 감독 결정으로 이 영상에 한해 `config.yaml media.video_fetch.allowed_domains` 에 `youtube.com`·`youtu.be`·`googlevideo.com` 추가 허용(DECISIONS D500, 되돌릴 수 있음). 봇 검사 우회 옵션은 쓰지 않는다 — yt-dlp 가 그냥 안 받아지면 포기하고 사진으로. 권리 기록 `scope: private_only`(D264), 출처 줄에 매체·날짜. 클립 0건이어도 막지 않는다(사유 media_note).
- **인물 뱃지**: 공용 라이브러리 먼저(`assets/library/people` — xi·trump·lee_jae_myung 등 있음). 새로 필요하면 왕원타오(상무부장)·허야둥(대변인) — Commons/정부 공개 초상 권리 확인된 것만, `portrait_fallback.py cutout` → promote. 권리 미확인은 직함 카드.
- **국기**: cn·kr·us·eu(+ 출처 있는 흐름의 상대국). 대만은 국기가 아니라 지명 라벨만.
- **위성 인셋**: 이 영상은 타격이 없다 — 쓰지 않는다(공장·항만 인셋은 출처 있는 지점이 있을 때만 1~2곳, 원형 UF-103).
- 콘티 판 전 `python tools/asset_library.py promote` → `check` = 0(C8.7).

## 6. 연출(기준 작품 diesel v2 문법 — 카메라 밀도·이야기 안의 데이터 패널)
- 주 무대 mercator **light**(`theme_reason: "지경학 — 장르 기본 D154, 감독 결정 D500"`). 권역: 베이징(상무부) → 동아시아(한국·대만·일본) → 미국·EU·동남아 흐름(출처 있는 교역·공급 관계만 route). 핀은 선 위(UF-142), 한꺼번에 튀어나오는 관계선 금지, 문장마다 요소 2~3개.
- **보조 무대 timeline(한 세계, UF-135·138)**: 축 범위 **2026-10-01 → 2026-12-01 고정**(w_changes 0). 네 공고 날짜(10/14·10/16·10/19·10/26)와 두 마감(11/15·11/18)이 같은 축 위에 핀. 2027-01-10 휴전 만료는 축에 올리지 않고 **카드**로(축 고정 때문 — 감독 결정). 시간축은 act1·act4 두 번만 진입·복귀(암전 dip), 안의 카메라 이동만.
- 데이터 패널: 수치가 출처로 확정될 때만 — 기술 수 분야별(AI·바이오·태양광) dots 또는 bars, 금지/제한 versus. 축척 다른 독립 차트 번갈아 띄우기 금지(chart_world_split hard). 차트만 보이는 구간 ≤ `qa_checks.chart_only_run.max_sec`.
- 카드: 허가제 vs 등록제 대비(한 줄 병렬), "오픈소스 공개 = 기술 수출" 카드, 의견수렴·시행 날짜 카드. AI 상투 문구 0(linter).
- 밀도: 기사 60초당 ≤2, 사진+영상 ≥1.5/분, 카메라 이동은 문장 사유 있을 때만, static_window ladder 준수.
- `python -m script.plan`(표준 음성) → 미디어 등록 → direction → `python -m audio.mix` → `python -m engine.render … --animatic` → **콘티 판 mp4(30 MB 이하, `-c:a copy`) + gate-view 미디어 요약을 R + send_message**. 감독 판정 → 고칠 것 있으면 direction 수정 → 재콘티. 통과 → `--preview auto` 시트 R → 감독 게이트 ② 승인.

## 7. 전편·전달
- 720p 전편 → `artifacts/china-export-controls-v7.4.0` orphan 브랜치(D186 방식: mp4·전달본·시트·provenance·phase_report·md5). 전달본 = `final_deliver.mp4` ≤ 30 MB(`-c:a copy`).
- 최종 R(phase_report): 커밋 목록·테스트(관련 + anti_inertia, 전체 pytest 1회)·checks hard 0·provenance(features_used·user_feedback_guards·private_only_assets)·컨택트 시트·육안 컷 6개 이상·**차단 호스트 표·미포함 사유 표**·길이·md5.
- 사용자에게 직접 보내지 않는다 — 감독이 보낸다(UF-144: 나오는 즉시).

## 8. 금지
- 사용자에게 묻기, 구글맵 화면, AI 생성·합성 이미지, 권리 미확인 사진·초상, 민감 지역 지도 지어내기, 발음 텍스트 숫자·라틴 약어, banned_phrases, force push, PR, main 푸시, 모델 식별자(산출물), D 파일 수정, 대용량 미추적 파일 커밋(tts/·out/·prev/·media/ 는 .gitignore 확인), yt-dlp 봇 우회.

## 9. 폴백
- 1차 출처(MOFCOM 원문)를 도구로도 못 열면: 신화·CCTV·GT 등재본 + 로이터·SCMP 로 **독립 출처 2건 이상** 일치하는 수치만. 수치가 엇갈리면 수치를 뺀다.
- 클립 못 받으면 사진 액자. 초상 권리 미확인은 직함 카드. 한국 접점 출처 부족은 act3 축소(사유 기록).
- 계정 한도로 세션이 끊기면 감독이 새 세션을 띄운다 — 커밋·푸시를 작게 자주.

## 10. 보고
- 단계마다 짧은 R(progress) + **send_message(session_017Yuw8hTb2zPgG7PvjAbjyu)**. 결정이 필요하면 decision_request R + send_message, 막히지 않는 작업은 계속.
- 첫 R(ack)에 환경 복원 결과·호스트 표·조사 착수 보고. 둘째 R 에 sources/claims 초안 수. 셋째 R 에 게이트 ① 자료.
