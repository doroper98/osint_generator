---
id: D-0450
from: fable
to: opus
kind: directive
responds_to: [D-0334]
phase: "IR1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 새 영상 『미국·이란 휴전안 — 정리와 가능성 타진』(iran_ceasefire_2026) — 묻지 않고 완성본까지

## 0. 권한·사용자 원문(D-0334, UF-205)
- 사용자 원문(2026-11-01): **"새로운 감독 세션을 띄워서 휴전안에 대해 정리하는, 그리고 휴전가능성이 있는지 타진해보는 영상 제작을 시작해 완성본으로 바로 받을 수 있도록 하고"**. 선례 D-0282·D-0283(중국 수출통제 — 같은 방식, 사용자 판정 95점).
- 감독 세션(이 D 의 작성자) = `session_017Yuw8hAgYiuiC4hYCHXB27`. **모든 R 은 이 세션 id 로 `send_message`** 한다(다른 감독 세션에는 보내지 않는다).
- 게이트 ①·② 는 **감독이 사용자 위임으로 승인**한다(`--by fable`, comment "사용자 위임 D-0334"). Opus 는 승인 명령을 치지 않는다 — 자료를 R 로 올리고 감독 판정을 기다리되, 막히지 않는 작업은 계속한다.
- 사용자에게 질문 금지(사용자는 이 세션을 보지 않는다). 결정이 필요하면 decision_request R + send_message.

## 1. 범위 — 코드 게이트는 그대로(D-0283 §1 과 같다)
- 단계: 소스 → claims → 원고 → 게이트 ①(감독) → 음성(표준 음성 C0.2, 묻지 않는다) → 미디어 등록 → 연출 → `audio.mix` → 콘티 판(require_animatic) → 프리뷰 → 게이트 ②(감독) → 전편 720p → 전달본.
- C12 장치(앞선 영상 UF 전부 guarded)·검사 hard 0·권리 기록·AI 생성 금지·발음 텍스트 숫자 금지·banned_phrases 0(UF-145·UF-202 — `python tools/slop_check.py projects/{pid}` 도 0) 그대로.
- 이 브랜치에는 D-0325~D-0333 이 전부 들어 있다: 전환 ×1.5·사진 주된 피사체(레지스트리 `subject` 기록)·배지 덮임 [badge-covered]·라벨 덮임 [label-under-media]·캡션 넘침 [caption-overflow]. 전부 적용 대상.

## 2. 브랜치·환경
- `git fetch origin && git checkout claude/iran-ceasefire-2026 && git pull --rebase origin claude/iran-ceasefire-2026`. 작업·교신 브랜치 = **이 브랜치**(sweet-galileo 41e00a99 에서 분기). 커밋 첫 줄 `v7.4.0: …`, `git config core.hooksPath .githooks`. 커밋마다 푸시(거부 시 pull --rebase, force 금지).
- 번호: R 은 `check.py --me opus --next-name` 출력 그대로. D 는 감독이 D-0450~ 로 쓴다. DECISIONS 행은 감독이 D550~ 로 붙인다(Opus 는 붙이지 않는다). UF 는 UF-170~199(사용자 의견이 오면 감독이 기록).
- 환경 복원 = R-0284 §환경 그대로: pip(requirements·requirements-engine) + pycairo·numpy·scipy·shapely·librosa·onnxruntime·cairosvg·yt-dlp·torch cpu·torchaudio·pyworld·uroman·rembg·`setuptools<81`; apt ffmpeg·fonts-noto-cjk; FONTCONFIG(12-unhinted-grayscale 제외); `python tools/fetch_data.py fonts ne tiles flags supertonic mms_fa bgm people`. 환경 복원은 백그라운드로 돌리고 §3 조사를 병행한다.
- **네트워크 실측(감독 컨테이너, 같은 env 2026-11-01 00:14Z)**: 컨테이너 curl 로 열린 호스트 = commons.wikimedia.org·upload.wikimedia.org(·pypi·huggingface). **막힌 호스트** = en.wikipedia.org·www.aljazeera.com·www.cbsnews.com·apnews.com·fred.stlouisfed.org(403 CONNECT). 첫 R 에 네 컨테이너의 실측 표를 올린다(세션마다 정책이 다를 수 있다).
  → 출처 대조는 **WebSearch**(세션 도구)로 한다. D-0284 §1 실측: WebFetch 는 허용 도메인 밖 DNS 실패, WebSearch 는 `allowed_domains` 로 좁히면 본문 발췌가 돌아온다. 크롤러 차단 도메인(mk.co.kr·yna.co.kr·chosun.com)은 검색에 넣지 않는다. sources.json `verification.notes` 에 "컨테이너·WebFetch 차단 — WebSearch 본문 발췌 대조, 독립 보도 N건 일치" 라고 적는다.

## 3. 사실·출처(G4·C9) — 1차 출처 대조 의무
- 감독 조사표 **D-0451 이 뒤따른다**(감독이 지금 조사 중 — 연표·양측 조건·호르무즈 주장·한국 접점·시나리오 신호·금지 항목). D-0451 전에도 독자 조사를 시작하되, claims 확정은 두 조사가 맞는 것만. 어긋나면 사실 쪽으로 쓰고 R 에 "지시와 다른 사실" 표(R-0286 선례).
- **1차 출처 우선순위**: ① 당사자 발언 원문(이란 외무부·정부 대변인, 백악관·국무부·중부사령부, 카타르 외무부, 파키스탄 총리실) ② 통신사·주요 매체(AP·로이터·알자지라·CBS·BBC·CNBC·Dawn) ③ 한국 보도(한국경제TV·파이낸셜뉴스·아주경제·매일신문·서울경제 등 — 한국 접점용). 수치(동결 자산 액수·통항 건수·유가·보험료·수입 비중)는 **독립 출처 2건 이상 일치**하거나 당사자 원문이 있을 때만. 엇갈리면 **매체별 귀속 병기**(예: "알자지라는 약 120억 달러, 다른 보도는 약 60억 달러") 또는 수치를 뺀다. "약 ~안팎" 으로 얼버무리지 않는다.
- **논쟁 사안은 양측 같은 무게(G4)**: 양해각서 파기 책임(미국 "이란이 상선 발포" ↔ 이란 "레바논 공격 못 막은 미국"), 호르무즈 상태(이란 "폐쇄 유지·10/30 유조선 4척 기뢰 접촉" ↔ 미 중부사령부 "남쪽 항로 개방·기뢰 제거") — **둘 다 미검증**으로 claims 에 기록, 본문에는 라벨을 넣지 않고(D85) 귀속 문장으로 쓴다. 엔딩 표기 행에 "호르무즈 통항·기뢰 주장은 양측 발표로 독립 확인되지 않음" 한 줄.
- **가능성 타진 = 예언 금지.** 결론은 **조건부 시나리오·신호 목록**으로만 쓴다: "A 가 먼저 풀리면 B 가 열린다" 꼴. 신호 후보(출처 있는 것만): 봉쇄 해제·동결 자산 집행·오만/카타르 중재 일정·호르무즈 통항 건수·전쟁 보험료·유가·11/3 중간선거 뒤 군사 옵션 발언·레바논 전선. 전망 수치(유가 등)는 **기관·날짜 귀속 + "참가자별 전망이며 약속이 아님"** 방식(diesel v2 선례). 수렴 은유·승부 은유·"남는다/올라온다" 마무리 금지(banned_phrases 린트가 잡는다 — `rules/video_rules.yaml banned_phrases.patterns` 읽고 쓴다).
- 한국 접점(act 한 막)은 **출처 있는 것만**: 원유 수입 호르무즈 경유 비중·중동 비중, 울산 정유·입항, 전쟁 보험료, 국내 유가, 정부 조치(비축유·상한제). 출처 없는 항목은 뺀다. "한국도 영향" 같은 무출처 일반화 금지.
- 인물 오인 금지: 현 최고지도자는 **모즈타바 하메네이**. 공용 초상 `khamenei_mono_v01`(알리 하메네이)을 모즈타바 문장에 쓰지 않는다(hormuz-talks-2026 order.yaml 지시와 같다).

## 4. 프로젝트·원고
- pid `iran_ceasefire_2026`, `new-project --category geopolitics`. `order.yaml`: genre geopolitics, tempo breath, attribution_mode credits(D243 — 보도 귀속은 엔딩 크레딧, 당사자 발언·논쟁 해석은 본문 귀속), length "내용이 정한다"(목표 5~7분 ≈ 문장 55~80, 길이 상한 해제 D501 선례), map_theme **light**(D154 장르 기본, 감독 결정 D550), bgm `audio.bgm_default` 첫 곡(기준 작품과 같다), resolution 720p, decisions.gates "게이트 ①·② 감독 위임(D-0334)". credits.yaml 음악 행.
- 제목(안): 『휴전안 — 미국과 이란, 무엇이 먼저 풀려야 하나』. 부제: "7일 휴전안의 조건, 호르무즈, 그리고 11월". 타이틀 카드 한 컷으로 길이 확인(W1.1 M3). 감독이 D-0451 에서 확정할 수 있다.
- 막 구성(감독 설계 — 연출 LLM 이 다듬되 뼈대 유지):
  - **cold**(3~4): 10월 31일 도하 — 이란 대표단, 아라그치 "긍정적 조치", 같은 날 루비오 "대통령은 군사 행동 재개를 아직 결정하지 않았다". 여덟 달 전쟁에 7일 휴전안이 올라와 있다. 11월 3일 중간선거가 사흘 뒤.
  - **act1 "여덟 달"**(10~14): 2/28 개전 → 호르무즈 봉쇄 → 4월 파키스탄 중재 2주 휴전(연장) → 6월 이슬라마바드 양해각서 → 7월 붕괴·전쟁 재개·미국의 이란 항만 봉쇄. **지도 위 사건 따라가기**(테헤란·이슬라마바드·호르무즈·반다르아바스·워싱턴) + 날짜 카드. 양해각서 파기 책임은 양측 귀속 한 문장씩.
  - **act2 "휴전안의 한 달"**(14~18): 9월 말 이란 7일안 → 9/26 트럼프 거부 → 9/30 미 역제안(카타르) → 10/7 미 새 요구 → 10/11 이란 "불충분" → 10/25 카타르 "7일 신뢰 구축" 초안(이란 "아이디어일 뿐") → 10/29 밴스 서한(트럼프 "의료 물품") → 10/30 카타르 테헤란 12시간 → 10/31 도하. **보조 무대 timeline 한 세계**(§6) + 지도(도하·테헤란·뉴욕·워싱턴·무스카트).
  - **act3 "조건 대조"**(8~12): **versus 패널 양측 같은 무게** — 이란(봉쇄 해제·동결 자산·제재·레바논 포함 전 전선 휴전·미 해군 축소 → 조건 충족 시 이틀 안 호르무즈 개방) ↔ 미국(농축·사찰 등 핵 문제·해협 먼저·…, D-0451 확정값). 쟁점은 조건 자체보다 **이행 순서**(hormuz-talks-2026 선례).
  - **act4 "호르무즈 지금"**(6~8): 이란 폐쇄 선언 유지, 10/30 기뢰 주장 ↔ 중부사령부 남쪽 항로 주장(양측 귀속, 미검증), 통항 건수·유가(출처·날짜). 위성 인셋 1곳(호르무즈 — showcase_geo 등재본 MODIS 사진 재사용 가능).
  - **act5 "가능성 — 신호"**(8~12): 조건부 시나리오 2~3개("봉쇄 해제가 먼저면 → 이란 이틀 개방 약속이 시험대" / "핵 문제 선결이면 → 7일안은 멈춘다" / "중간선거 뒤 군사 옵션 발언이 나오면 → …")와 **지켜볼 신호 목록**(dots 또는 카드 — 통항 건수·보험료·동결 자산 집행·오만/카타르 일정·레바논). 전망 수치는 기관 귀속만.
  - **act6 "한국"**(5~8): 출처 있는 접점만(§3). 울산 1곳 지도 핀.
  - **ending**(2~3): 사실 한 줄 정리("확인된 것 / 확인되지 않은 것") + 엔딩 카드(출처·권리·보도 출처 장면별, 맨 아래 가장 작은 글씨 미검증 표기 D85).
- 원고 규칙: 발음 텍스트 숫자·기호·라틴 약어 금지(MoU → "양해각서", CENTCOM → "미 중부사령부", UAE → "아랍에미리트"). 문장 끝 "~니다". 인물 발언마다 quote 후보, 보도 문장마다 기사 카드 후보. `lint-script` 0 + `slop_check` 0. **gate-view 자료 + `gate1_elements.md`(막마다 요소 한 줄, showcase_geo 형식) + 미디어 계획 표**를 R 로 올리고 감독 호출.

## 5. 미디어(UF-139 밀도 `media_beats.min_density_per_min` hard, Commons 탐색 의무, 등재 0 금지)
- **기사 카드**(`article_register.py`, headline_ko 채움, 60초당 ≤2): 10월 휴전안 보도(알자지라 10/31·10/25·10/7, AP, 로이터, CBS, CNBC 10/31), 한국 접점 보도(한국경제TV·파이낸셜뉴스·아주경제·매일신문·서울경제).
- **사진**(Commons·미 정부 PD, 라이선스·피사체·시기 대조, `subject` 기록 D-0327): 호르무즈 해협 위성(NASA), 유조선(해협·걸프), 도하 스카이라인·카타르 외무부, 이슬라마바드, 테헤란, 반다르아바스 항, 미 해군 함정(걸프 — 미 해군 PD), 울산 정유·울산항, 기뢰 소해 작업(미 해군 PD). 사진의 **주된 피사체가 문장과 맞아야 한다**(UF-201). 자료사진 표기.
- **클립 액자(UF-141)**: 감독 결정 D551 — 이 영상에 한해 `config.yaml media.video_fetch.allowed_domains` 에 `youtube.com`·`youtu.be`·`googlevideo.com` 추가 허용(D500 선례, 되돌릴 수 있음). 대상 = 공식 채널(Al Jazeera English·AP·CBS News·백악관·국무부) 10월 말 휴전 관련 클립. 봇 검사 우회 옵션 금지 — 안 받아지면 사진 액자. 권리 `scope: private_only`(D264). broll 은 구석 자리(D-0332) — 지도 위 사건 자리를 덮지 않는다.
- **인물 뱃지**: 공용 라이브러리 먼저(`assets/library/people` — trump·netanyahu 있음, khamenei 는 알리). 새로 필요: 아라그치·페제시키안·밴스(미 정부 PD)·루비오(PD)·위트코프·카타르 총리(무함마드 빈 압둘라흐만)·파키스탄 샤리프/무니르·레자이. Commons/정부 공개 초상 권리 확인된 것만 `portrait_fallback.py cutout` → promote. 권리 미확인은 직함 quote.
- **국기**: ir·us·qa·pk·om·il·lb·kr. **휘장**: navcent 는 있음. 중부사령부 등 Commons `Restrictions`(insignia) 있으면 쓰지 않고 국기(README §7.2).
- **위성 인셋**: 호르무즈 1곳(원형 UF-103, 자리 고정 UF-146). 타격 지점은 출처 좌표가 있을 때만.
- 콘티 판 전 `python tools/asset_library.py promote` → `check` = 0(C8.7).

## 6. 연출(기준 작품 diesel v2 문법 — 카메라 밀도·이야기 안의 데이터 패널)
- 주 무대 mercator **light**(`theme_reason: "지정학 — 장르 기본 D154, 감독 결정 D550"`). 권역: 걸프(테헤란·도하·무스카트·반다르아바스·호르무즈) ↔ 이슬라마바드 ↔ 워싱턴·뉴욕 ↔ 한반도(울산). hormuz-talks-2026 `geo.yaml` 티어(W·G·K) 참고 가능(R 티어 홍해는 이번에 없음). 핀은 선 위(UF-142), 한꺼번에 튀어나오는 관계선 금지, 문장마다 요소 2~3개, 카메라 이동은 문장 사유 있을 때만.
- **보조 무대 timeline(한 세계, UF-135·138, 감독 결정 D550)**: 축 범위 **2026-09-15 → 2026-11-15 고정**(w_changes 0). 핀 = 9/25(이란 7일안)·9/26·9/30·10/7·10/11·10/25·10/29·10/30·10/31·**11/3 중간선거**. 2월~7월 전쟁 경과는 축에 올리지 않고 **지도 + 날짜 카드**로(축 고정 때문). timeline 은 act2 한 번(필요하면 act5 에 같은 축·같은 자리로 한 번 더) 진입·복귀(암전 dip), 안의 카메라 이동만. mercator 주 무대에 panel timeline 두 번 방식(D504 B안)을 그대로 쓴다.
- 데이터 패널: 수치가 출처로 확정될 때만 — 양측 조건 versus(같은 폭·같은 행 수), 통항 건수(전쟁 전 ↔ 지금, 출처 줄), 유가(날짜 두 점 이상이면 dual_line 금지·bars), 한국 원유 수입 비중(ratio). 축척 다른 독립 차트 번갈아 띄우기 금지. 차트만 보이는 구간 ≤ `qa_checks.chart_only_run.max_sec`.
- 카드: 날짜 카드(2/28·4월·6월·7월), "조건 충족 → 이틀 안 개방" 카드, 신호 목록 카드. 오른쪽 상단 아일랜드 카드 남발 금지(UF-148 — 밀려난 요소는 중앙으로 크게). AI 상투 문구 0.
- 밀도: 기사 60초당 ≤2, 사진+영상 ≥ 규칙 하한, static_window ladder 준수, [element-gap]·[badge-hold]·[badge-covered]·[label-under-media]·[caption-overflow] hard.
- `python -m script.plan`(표준 음성) → 미디어 등록 → direction → `python -m audio.mix` → `python -m engine.render … --animatic` → **콘티 판 mp4(30 MB 이하, `-c:a copy`) + gate-view 미디어 요약을 R + send_message**. 감독 판정 → 고칠 것 있으면 direction 수정 → 재콘티. 통과 → `--preview auto` 시트 R → 감독 게이트 ② 승인. **렌더 중 rules/·schemas/·engine/·audio/·config.yaml 변경 금지**(D-0284 사고).

## 7. 전편·전달
- 720p 전편 → `artifacts/iran-ceasefire-v7.4.0` orphan 브랜치(D186 방식: `iran_ceasefire_2026/final/` 에 final_deliver.mp4·final_sheet.jpg·MD5SUMS·provenance.json·audio_qa.json·description.txt·credits.txt·final.srt·preview_checks.json; 콘티 판·시트는 `animatic_vN/`·`gate2_rNNNN/`). 전달본 = `final_deliver.mp4` ≤ 30 MB(x264 2-pass, `-c:a copy`).
- 최종 R(phase_report): 커밋 목록·테스트(관련 + anti_inertia, 전체 pytest 1회 — C8.3)·checks hard 0·provenance(features_used·user_feedback_guards·private_only_assets)·컨택트 시트·육안 컷 6개 이상·**차단 호스트 표·미포함 사유 표·지시와 다른 사실 표**·길이·md5.
- 사용자에게 직접 보내지 않는다 — 감독이 보낸다(UF-144: 나오는 즉시). 유튜브 문안은 감독이 쓴다(description·credits·srt 가 재료).

## 8. 금지
- 사용자에게 묻기, 구글맵 화면, AI 생성·합성 이미지, 권리 미확인 사진·초상, 출처 없는 지도 좌표(타격 지점·기뢰 위치 지어내기), 예언형 결론·수렴 은유·승부 은유, 발음 텍스트 숫자·라틴 약어, 화면 라벨 '개략·비공개'(UF-161), force push, PR, main 푸시, 모델 식별자(산출물), D 파일 수정, 대용량 미추적 파일 커밋(tts/·out/·prev/·media/ .gitignore 확인), yt-dlp 봇 우회, 렌더 중 규칙 변경.

## 9. 폴백
- 당사자 원문을 도구로도 못 열면: 통신사·주요 매체 **독립 출처 2건 이상** 일치하는 사실만. 엇갈리면 귀속 병기 또는 삭제.
- 클립 못 받으면 사진 액자. 초상 권리 미확인은 직함 quote. 한국 접점 출처 부족은 act6 축소(사유 기록). 위성 인셋 좌표 출처 없으면 해협 전경만.
- 계정 한도로 세션이 끊기면 감독이 새 세션을 띄운다 — 커밋·푸시를 작게 자주.

## 10. 보고
- 단계마다 짧은 R(progress) + **send_message(session_017Yuw8hAgYiuiC4hYCHXB27)**. 결정이 필요하면 decision_request R + send_message, 막히지 않는 작업은 계속.
- 첫 R(ack): 환경 복원 상태·호스트 실측 표·조사 착수. 둘째 R: sources/claims 초안 수 + 지시와 다른 사실. 셋째 R: 게이트 ① 자료(원고 전문·gate-view·gate1_elements·미디어 계획 표·script_sha1).
