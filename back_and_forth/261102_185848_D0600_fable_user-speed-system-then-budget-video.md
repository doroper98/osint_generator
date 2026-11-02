---
id: D-0600
from: user
to: opus
kind: directive
responds_to: []
phase: "S"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 결정 — 영상 제작 시간 단축 체계 전환(S0~S6) 먼저, 그 뒤 『2027년 예산안 분석』 영상(B)

사용자 원문(2026-11-02):
- UF-300: **"전반적으로 영상 제작에 소요되는 시간이 너무 길어. 거의 이틀이 걸려. 퇴고까지 포함해서. 어떻게 되어야 하는걸까"**
- UF-301: **"일단 시간을 줄이는 체계 전환을 지금 바로착수 하고 그 뒤에 예산안에 대한 분석 영상을 만들어."**

감독 = `session_017Yuw8kbxf9Vxri6LoH5Je4`(이 트랙만; 다른 트랙의 최종 감독은 session_017Yuw8jLMWscY9bdVXTvddr). 브랜치 `claude/speed-pipeline-2026`(sweet-galileo 935908fc 에서 분기). 번호: 이 트랙 D-0600~0649, DECISIONS D600~, UF-300~. R 은 R-0600~ 로 쓴다(다른 트랙 R 번호와 섞이지 않게 — check.py --next-name 이 내는 번호 대신 R-0600 부터 수동). artifacts `artifacts/speed-pipeline-v7.4.0`.

## 0. 근거 — 이란 휴전안 영상 실측(back_and_forth 파일 시각, KST)
| 구간 | 시간 |
|---|---|
| 착수 → 게이트 ① | 약 2시간 |
| 게이트 ① → 콘티 판 v1 | 약 3시간 50분(콘티 판 렌더 1104초, 4코어) |
| 콘티 판 검토 2회 → 게이트 ② | 약 3시간 |
| 게이트 ② → 1차 완성본 | 약 1시간 40분 |
| 퇴고 1차(UF-171 노출 0.8초) | 약 3시간 10분 |
| 퇴고 2차(UF-173 사진이 지도 사건을 덮음) | 4시간 이상 |
원인 셋: ① 탈락 결함 둘 다 숫자로 잴 수 있었는데 검사가 없거나 경고였다, 감독은 표만 보고 통과(D-0463). ② 문장 하나 고쳐도 콘티 판·720p 전체를 다시 그린다. `rules.load_rules()` 에 캐시가 없어 이벤트·패널 코드가 부를 때마다 규칙 YAML 전체를 다시 읽고 검증한다(R-0318 §4: check_series_label_overlap 1초 프레임에 45~60초). ③ 감독·구현 왕복과 AI 연출 초안의 출처 없는 좌표 수작업 제거.
**목표: 1차 완성본 4시간 이내, 퇴고 1회 1시간 이내, 탈락 0회.** 게이트·콘티 판은 빼지 않는다(C8-6). 빨라지는 곳은 검출·재렌더 단위·왕복이다.

## S0. 측정 먼저 — 단계별 시간 기록
- 새 모듈 `engine/timing.py`(또는 orchestrator 공용 위치) — `with stage_timer(proj, "render.animatic.frames"):` 컨텍스트 관리자. `projects/{pid}/out/timings.jsonl` 에 한 줄 1이벤트 `{"schema_version":1,"stage":…,"start_utc":…,"end_utc":…,"sec":…,"args":{…}}`.
- 감쌀 지점(최소): 원고 린트, TTS 합성(`script/tts`), 정렬(MMS), `audio.mix`, 연출 LLM 호출, `engine.render` 의 preview·animatic·final 각각을 **프레임 그리기 / 검사(run_checks) / 인코딩·concat** 세 칸으로 나눠서, contact sheet, 전달본 재인코딩.
- provenance 에 `timings` 요약(단계별 합계). 돌지 않은 단계는 기록하지 않는다(P5).
- 시험: `tests/anti_inertia/test_stage_timings.py` — 위 지점 함수가 stage_timer 를 쓰는지(소스 검사) + 짧은 픽스처 렌더 뒤 timings.jsonl 에 render 세 칸이 있는지.

## S1. 검사·렌더 성능 — 규칙 로딩 캐시
- `rules/__init__.py:load_rules(path)` 를 캐시한다. 키 = (resolve 한 경로, `st_mtime_ns`, `st_size`). 같은 키면 **같은 VideoRules 객체**를 돌려준다. 파일이 바뀌면 다시 읽는다(시험이 임시 규칙 파일을 쓰는 경우 그대로 동작).
- 공유 객체 변형 위험: `grep -rn` 으로 규칙 객체 속성에 대입하는 코드를 전수 확인하고, 있으면 고친다. 그다음 `VideoRules`(와 하위 모델)에 `model_config = ConfigDict(frozen=True)` 를 걸 수 있으면 건다 — 시험이 깨지면 frozen 은 보류하고 R 에 사유.
- 경제 트랙의 같은 종류 수정 `6299f295`(column_detail 규칙을 한 번만 읽기)를 cherry-pick 한다(충돌 시 이 S1 캐시가 상위 해결책이므로 S1 쪽으로 정리).
- 다른 매 호출 재읽기 지점도 확인: `load_rules_cached` 같은 별도 함수가 이미 있으면 하나로 합친다(SSOT).
- 검증: iran_ceasefire_2026(이란 브랜치에서 프로젝트 폴더를 가져와도 됨, 렌더 결과물은 커밋하지 않는다) 또는 showcase_geo 의 `--animatic` 검사 시간을 S1 전·후로 재고, **checks.json 은 바이트 동일**(시간 필드 제외)해야 한다. 골든 25컷 화소 동일.
- 목표: 8분 영상 콘티 판의 검사 ≤ 3분.

## S2. 부분 재렌더 — 조각 캐시
현재 `engine/render.py` 는 `--jobs N` 이면 프레임을 N 조각(chunk_ranges)으로 나눠 병렬 렌더 후 concat 한다. 조각 경계가 jobs 에 따라 바뀌므로 재사용할 수 없다.
1. **고정 격자**: 조각 길이 = config `engine.render.chunk_sec`(기본 10초, t=0 정렬). jobs 는 작업자 수일 뿐 조각 경계와 무관하게 큐에서 조각을 꺼내 그린다.
2. **조각 키**: 조각마다 탐침(probe) 서명을 만든다 — 조각 안의 시각 {probe_step_sec(0.5초) 간격} ∪ {조각 안에 있는 모든 이벤트의 시작·끝·at_word 시각과 그 ±1프레임}에서 `render_frame` 을 축소 배율 `engine.render.probe_scale`(0.25)로 그려 RGBA 바이트를 sha1 로 잇는다. 키 = sha1(탐침 서명 + 출력 프로파일(해상도·fps·인코더 인자) + `git rev-parse HEAD:engine` 트리 해시 + rules_hash). 엔진 코드가 바뀌면 전부 무효(보수적).
3. **재사용**: `out/chunks/<profile>/<idx>_<key>.mp4` 가 있으면 그리지 않고 쓴다. 없으면 그린다. 렌더 기록(render.json)에 조각마다 `reused|rendered` 와 시간. `--no-cache` 로 강제 전체.
4. 오디오 mux·전달본 재인코딩은 지금 그대로.
5. 원고·음성이 바뀌어 시간이 밀리면 그 뒤 조각은 키가 달라져 다시 그려진다 — 정상.
6. **정확성 시험**(필수, P6): 짧은 픽스처 프로젝트(60초 이하)를 전체 렌더 → 가운데 조각 하나에만 걸리는 이벤트 하나를 바꾼다 → 캐시 렌더 → 같은 입력을 `--no-cache` 로 렌더 → 두 결과를 디코드해 프레임별 비교. x264 결정성(스레드 고정)으로 프레임 md5 동일을 목표로 하고, 불가능하면 PSNR ≥ 55dB 를 기준으로 쓰고 R 에 사유. 바뀐 조각만 `rendered` 인지도 시험.
7. 탐침 비용은 전체 렌더 시간의 10% 이하여야 한다(측정해 R 에). 넘으면 probe_step_sec·probe_scale 을 조정.
- 목표: 문장 하나 범위 연출 수정 뒤 콘티 판 재렌더 ≤ 5분, 720p 재렌더 ≤ 15분.

## S3. 탈락 유형 hard 검사(UF-171·172·173, D-0462·D-0466 의 일반화)
모든 렌더 경로(프리뷰·콘티 판·전편·스케치)에 같은 규칙 키로 건다(C12 §3).
1. `[map-event-covered]` hard — 지도 무대 이벤트 중 자라나거나 나타나는 창이 있는 것(route grow, marker 등장, boom, badge popin, 카메라 이동 창)에 대해, 창 안 0.1초 표본마다 그 이벤트의 화면 상자 중 불투명 덮개(photo·clip 액자·article 전면·quote 덮개·island, 알파 ≥ 0.5)에 가린 비율 > `qa_checks.map_event_covered.max_ratio`(0.25, 감독 제안)이면 실패. broll 구석 자리는 상자가 겹칠 때만 센다.
2. `[media-date-cross]` hard — photo·clip·article·quote 의 보이는 구간(알파 ≥ 0.5)에 날짜 HUD 값이 바뀌는 순간이 들어 있으면 실패(그 요소는 다른 날짜 문장에 속한다). 날짜와 무관한 요소(backdrop 등)는 규칙 키 `qa_checks.media_date_cross.exempt_types` 로만 면제.
3. 매체 밀집을 hard 로: D-0466 이 인용한 밀집 경고("40초에 4개 > 2")가 어떤 검사 id 인지 이란 브랜치(`origin/claude/iran-ceasefire-2026`)와 이 브랜치에서 찾아(media.density 계열) **hard 로 올린다**. 추가 조건: 지도 무대에서 어떤 `window_sec`(40초) 창이든 지도가 덮인 시간 비율 ≤ `max_cover_ratio`(0.5).
4. 이미 있는 `[element-hold]`(최소 노출)·`[media-overlap]`·`[label-under-media]`·`[badge-covered]` 는 그대로.
5. 새 검사를 기존 프로젝트 여섯(showcase_geo·showcase_econ·china_tech_export_controls_2026·iran_ceasefire_2026(이란 브랜치 최신 direction)·hormuz_korea 골든·fed_timeline_demo)에 돌려 **건수 표**를 R 에. 골든이 걸리면 `regression_ref_checks` 면제(사유 기록), 다른 프로젝트는 고치지 말고 보고만(각 트랙 감독이 판단).
6. 시험: 검사마다 실패 픽스처 1·통과 픽스처 1. `tests/anti_inertia` 의 심각도 표 시험 갱신.

## S4. 눈 검수 도구 — 감독이 "표만 보고 통과"하지 못하게
1. `tools/review_sheet.py <proj> [--src animatic|final|preview] [--every 3]` — 다시 렌더하지 않고 마지막 산출 mp4 에서 ffmpeg 로 3초 간격 프레임을 뽑아 한 장(또는 여러 장)으로. 칸마다 시각·문장 id·날짜 HUD 값. 둘째 장: provenance 기준 모든 미디어·배지·카드의 (시작, 끝, 노출 초, 그 동안 덮인 지도 이벤트 %) 표.
2. `tools/uf_checklist.py <proj>` — `rules/user_feedback.yaml` 의 의견 전부를 `out/uf_checklist.md` 로: 장치가 자동 검사면 provenance `user_feedback_guards` 결과(pass/fail), doc·눈 확인 항목은 "눈 확인" 칸과 볼 시각 후보(분류 낱말 사진·배지·지도·자막·전환·차트로 review_sheet 칸 연결).
3. 절차(back_and_forth/README §6 에 추가): 사용자에게 무엇이든 보내기 전 감독은 review_sheet 와 uf_checklist 를 R/D 에 붙이고 모든 줄을 채운다. 비어 있으면 보내지 않는다. D-0463(노출 표만 보고 통과) 사고를 `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 에 LLM-AP-023 으로 append.

## S5. 왕복 축소(절차 문서)
- `WORKFLOWS.md` 에 "단일 구현 모드" 추가: 일상 영상은 구현 세션 하나가 착수부터 전달본까지 간다. 감독 확인점은 셋 — (a) 게이트 ① 원고, (b) 콘티 판, (c) 사용자 전달 직전(S4 도구). R 은 이 셋과 막힘에만. 작은 판단은 구현 세션이 DECISIONS 에 "구현 전결" 표시로 적고 진행(decision_request 남발 금지).
- 사용자 확인점은 헌법 그대로(C8-6 원고·콘티 판). 바꾸지 않는다.
- 전체 pytest 는 전달 경로 밖(D187 재확인) — 변경마다 관련 시험 + anti_inertia + 골든, 전체는 병합 직전.
- 연출 LLM 초안의 출처 없는 좌표: 연출 프롬프트(prompts/*.md 템플릿 → 규칙에서 생성, P3)에 "좌표는 지명 사전·장소 키만, 새 좌표 금지"가 이미 있는지 확인하고, 없으면 규칙 키로 넣고 프롬프트를 재생성. 검사 `[geo-unsourced]` 를 연출 저장 시점에 돌려 초안 단계에서 걸리게 한다.

## S6. 검증·병합
- 같은 프로젝트(이란 또는 showcase_geo)로 전·후 표: ① 콘티 판 전체(그리기·검사·인코딩) ② 문장 하나 연출 수정 뒤 콘티 판 재렌더 ③ 같은 수정 뒤 720p 재렌더 ④ review_sheet·uf_checklist 생성 시간. R-0600 에 표 + 측정 명령.
- 병합 전: sweet-galileo 최신을 이 브랜치로 merge → 빠른 묶음(`-m "not slow"`) + anti_inertia + 골든 25컷(dark·light) 통과. 감독 승인(D) 뒤 `git checkout claude/sweet-galileo-7yok3b && git merge --no-ff claude/speed-pipeline-2026 && git push`. PR 금지.

## B. 『2027년 예산안 분석』 영상 — S 병합 뒤 착수
소재(감독 조사 2026-11-02): 정부안 총지출 820.9조 원(전년 대비 12.8%↑, 역대 최대), 국세수입 전망 584.4조 원, 추가 세수 162.3조 원을 재원으로 한 미래대응기금 신설(여야 쟁점). 헌법상 국회 의결 시한 12월 2일. 출처 후보: 머니투데이방송 2026-09-01, 세계일보 2026-09-01, 국회예산정책처 분석, 기획예산처 보도자료·예산안 개요(1차 출처로 대조).
- B0. 새 장르 프로필 `genres/fiscal.yaml`(status proposed): 막 = ① 콜드 오픈(총액·증가율) ② 어디에 쓰나(구성) ③ 무엇이 늘고 줄었나(증감) ④ 어디서 오나(세입·기금·국채) ⑤ 쟁점(여야 같은 무게, G4) ⑥ 일정(예결위·12월 2일). 용어 정의 한 번씩(총지출·총수입·관리재정수지·국가채무·미래대응기금). 데이터 필수 필드는 earnings 와 같게. 정부안·국회 확정 구분(as_of) 필수.
- B1. 새 무대 `structure`(registries.stages_planned → stages; 스키마·렌더러·프리뷰 예제 세 곳, P10) — **형태는 하나만: 순위 가로 막대**. 막대 = 2027 정부안 금액(바닥 조판 정본 D-0330: 테두리 0, 끝 3px, 잉크 사다리, 초점 accent 1), 막대 위 속빈 눈금 = 2026 본예산(같은 축척), 끝에 직접 라벨 "금액 · ±증감률". 금액과 변화 두 층이 한 그림(사용자 통섭 원칙 UF-153). 생키·트리맵은 이번에 만들지 않는다.
- B2. **구상 1프레임**(실제 엔진·실제 데이터 12대 분야)을 감독이 사용자에게 보내 판정받기 전에는 다른 컷을 만들지 않는다(UF-153·LLM-AP-022).
- B3. 그다음 S 체계로 제작: 소스·claims → 원고 → 사용자 게이트 ① → 음성(C0.2) → 연출 → 콘티 판 → 사용자 → 프리뷰·게이트 ② → 전편 → 전달본·자막·설명란·크레딧·유튜브 문안. 사용자 확인점은 1프레임·원고·콘티 판 셋.
- B 는 새 세션(새 컨테이너)에서 시작한다 — 사용자가 네트워크 허용 목록에 재정 출처 호스트를 넣은 뒤. 브랜치 `claude/budget-2027-video`, artifacts `artifacts/budget-2027-v7.4.0`.

## 공통
커밋 첫 줄 `v7.4.0: …`, 트레일러 Co-Authored-By 와 Claude-Session(구현 세션 URL). PR 금지·main 푸시 금지·모델 식별자 저장소 기록 금지. 보고문은 `python tools/slop_check.py` 통과. 렌더 도는 동안 규칙·엔진 편집 금지(W0 사고 재발 방지). 조용한 드롭·폴백 금지(P6).
