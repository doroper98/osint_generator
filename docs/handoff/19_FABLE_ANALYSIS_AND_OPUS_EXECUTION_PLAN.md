<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-overhaul-execution-plan, phase0-spec, overhaul-decisions]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/13_IMPLEMENTATION_PLAN_FOR_CLAUDE_CODE.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md, docs/handoff/16_ORCHESTRATOR_INTEGRATION.md, docs/handoff/KICKOFF_PROMPT.md]
last_review: 2026-09-27
author: Claude Fable 5.1 (분석·계획 세션, 2026-09-27) — 실행 주체는 Claude Opus 5.5 세션
-->

# 19. Fable 분석 보고 + Opus 실행 계획 (v2 전면 개편)

> **역할 분담(사용자 지시)**: 분석·계획 = 본 문서(Fable). 실제 개발 = Opus 5.5 세션.
> Opus 세션은 이 문서를 `KICKOFF_PROMPT.md` → `00_INDEX.md` → `15` 다음에 읽고, **§5 Phase 0 명세를
> 그대로 실행**한다. 이 문서가 `13`과 다르게 말하는 곳은 §3에 근거를 적어 두었다. 근거 없이 다르면
> `13`이 옳다.

---

## 0. 요약 보고 (KICKOFF §8.1 — 10줄)

1. 취지: 기존 롱폼 영상 문법(섹션=장면 슬라이드, 고정 12막, 작은 글씨, 평면 배경, 정적 지도, 모서리 HUD)을 폐기하고, 채팅 v3『호르무즈와 한국』의 **지도 중심 다큐 문법**으로 교체한다.
2. 완료 정의: (a) 새 엔진으로 v3 골든 재현 (b) 사용자 명령→오케스트레이터→`claude -p` 워커→엔진 e2e (c) 레거시 통로 0 + 관성 방지 테스트 8종 (d) ElevenLabs 목소리 교체 시 연출 무수정 싱크 (e) 해상도 독립 (f) provenance로 "이번 영상에 쓰였다" 증명.
3. 최우선 원칙: **주입하지 말고 교체·삭제**(`15` P1·P2). 옛 경로는 플래그가 아니라 archive 브랜치 후 삭제.
4. 규칙 SSOT는 `rules/video_rules.yaml` 하나. 워커 프롬프트는 파일 템플릿 + 규칙에서 생성. 코드 상수 프롬프트 금지(P3).
5. 프롬프트가 예시로 보여 주는 출력은 스키마를 통과해야 하며 테스트로 강제(P4). 드롭·폴백은 숨기지 않고 실패(P6).
6. 권한 분리: 장면 구성·연출은 LLM+사용자, 렌더 수치·검증·권리는 코드. 코드가 "정규화"로 LLM 구성을 옛 모양으로 되돌리지 않는다(P8).
7. v3 수치(두께·알파·타이밍·색·글자 크기)는 사용자 합격 값이라 근거 없이 바꾸지 않는다. 비네팅·도장·모서리 브랜드/섹션·줌 범프·동시 관계선·AI 상투 문구·발음 텍스트 숫자 기호는 되돌리지 않는다.
8. 사실·권리·검증 원칙(GOAL G4, CLAUDE C9)은 계승. 출처 없는 수치 금지, 논쟁 양측 병기, 자료사진 표기, 사실 장면 AI 생성 금지, 엔딩 크레딧 유지.
9. 범위 밖: 텔레그램 봇 인테이크, 유튜브 자동 업로드, 쇼츠(collage) 트랙(보관만).
10. 작업 방식: Phase 0(관성 차단)→Phase 1(골든 재현)→… 각 Phase 끝에 멈추고 5항목 보고, 사용자 승인 후 진행. 커밋 `vX.Y.Z:` + VERSION 일치, 한 커밋 한 의도, **PR 생성 금지**, 개편은 v2.0.0부터.

---

## 1. 저장소 현황 (2026-09-27 실측 — 추측 없음)

### 1.1 브랜치
| 브랜치 | VERSION | 최종 커밋 | 관계 |
|---|---|---|---|
| `origin/main` | 0.43.4 | 2026-07-12 `8586941` | — |
| `origin/collage` | 1.2.1 | 2026-08-15 `9dcda27` | **main + 35 commits, main에 없는 것 0** (fast-forward 가능) |
| `origin/local-audio` | 0.38.1 | 2026-06-12 | main·collage 어디에도 미병합(19 commits). 내용은 HyperFrames 음성 산출물 — 개편에 불필요 |
| `origin/data/agents-reviewer-v8-bundle-backfill` | — | 2026-07-12 | main 대비 1 commit(`json/` 63건 백필). Phase 9 테스트 코퍼스로만 |
| `archive/*`, `overhaul/*` | — | — | **없음** (Phase 0에서 생성) |
| `claude/laughing-rubin-rujpp2` | 0.43.5 | main + 문서 묶음·모델 고정 커밋(2d2e1e6, 2c4c642, e025510) | Fable 세션 1차 작업 브랜치(보관) |
| **`overhaul/v2-map-engine`** | **1.2.2** | collage tip + 위 커밋을 collage 버전 체계로 재적용 | **개편 작업 브랜치(사용자 승인 2026-09-27, D1 확정)** |

→ **collage는 main의 상위집합**이다. collage에서 분기하면 main의 어떤 것도 잃지 않는다(§4 D1).

### 1.2 collage에만 있는 자산 (개편이 계승할 것)
- `assets/library/people/` 24인 `{pid}_mono_v01.png` (altman, audrey_tang, bezos, chey_tae_won, curtis_yarvin, dario_amodei, daron_acemoglu, helene_landemore, jensen_huang, **khamenei**, lagarde, macron, michael_sandel, musk, netanyahu, peter_thiel, powell, **putin**, tim_cook, **trump**, warsh, xi_jinping, **zelensky**, zuckerberg) + `library_manifest.json`(AssetLibraryManifest 스키마: person_id, name_ko, aliases, accent_hint, source{license, rights_status, credit}, variants[]).
- `assets/library/workshop/` codex `$imagegen` 공방: AGENTS.md, collect_portraits.py, make_prompts.py, promote_to_library.py, prompts/portrait_panel.md, references/RIGHTS.md + photo_manifest.json(26인 원본 사진, 이재용·이창용은 사진만).
- `workers/engraving_stylizer.py`(1,673줄, `stylize_mono`/`background_mask` 등 — 인물 흑백화 폴백) + 테스트 38건.
- `schemas/models.py` +373줄: Bundle video 블록, AssetLibrary 6종, DesignSheet/ArtDirection.
- `config.yaml` `render.profiles`, `tts.profiles` (briefing/shorts).
- GOAL G4-10 개정본(AI 이미지 **가공** 허용, 무입력 사실 생성 금지) — `14` §2.2와 모순 없음(§3.7).
- 쇼츠 트랙: `hyperframes/shorts/`, `docs/17_COLLAGE_DESIGN_SHEET.md`, `docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md`, `design_sheets/` → **보관 대상**.
- v3가 쓴 인물 4인 중 이재명·노무현은 라이브러리에 없다(위키미디어 재수집 필요, Phase 1).

### 1.3 레거시 표면 (Phase 0 삭제 대상, main 기준 실측)
| 대상 | 규모 | 의존 관계 |
|---|---|---|
| `hyperframes/` | 175 files, 53MB (briefing/, demo/, scripts/ 5 py 2,734줄, shorts/는 collage) | `orchestrator/tts_pronounce.py:15`가 `hyperframes/demo/assets/pronounce.json` 경로를 문서화(기본 경로) |
| `remotion/` | 28 files, 2.3MB (TSX) | `orchestrator/main.py:1030~1081` render-debug가 `npx remotion render` 호출, `config.paths.remotion_root` |
| `orchestrator/scene_builder.py` (76줄) | 세그먼트→장면 1:1, `DEFAULT_SEGMENT_SEC=8.0`, 기본 `text_slide` | `scene_io.py:15` import, `main.py:838` build-scene, `tests/test_scene_flow.py`, `tests/test_render_flow.py` |
| `orchestrator/scene_io.py` (106줄) | scene_manifest I/O | `render_io.py:20` |
| `orchestrator/render_io.py` (420줄) | Remotion props 생성, `split_subtitle_cues`(글자수 비례 자막) | `main.py:1003` render-debug, `subtitle_align.py`, `tests/test_render_flow.py` |
| `orchestrator/subtitle_align.py` (110줄) | whisper 정렬 옵션 | `render_io.py:399` |
| `orchestrator/audio_service.py`, `audio_io.py`, `audio_demo.py` (276줄) | 세그먼트별 TTS 합성·데모 props | `main.py:900/958` build-audio, build-audio-demo; `tests/test_audio_flow.py`, `test_audio_demo.py` |
| `orchestrator/main.py` 핸들러 | `_cmd_build_scene`(830), `_cmd_build_audio`(893), `_cmd_build_audio_demo`(958), `_cmd_render_debug`(987) | 위 모듈 import |
| `schemas/models.py` | `SceneProvenance`, `SceneEntry`, `SceneManifest`, `DebugLayerSpec`, `RemotionJob`(799), `RenderMapMarker/Arc`, `RenderMap`, `RenderChart`, `RenderSceneProps`, `RenderProps`, `AudioSegment`, `AudioManifest`, `SubtitleCue` | 레거시 모듈 외 참조 **0**(orchestrator/workers/web grep 결과) |
| `docs/PROFESSIONAL_REBUILD_PLAN.md`, `docs/07/08/09` 영상 기준 | 옛 문법 | Phase 0에서 폐기 배너, Phase 11에서 재작성 |
| `tests/` | `test_scene_flow.py`(83), `test_render_flow.py`(332), `test_audio_flow.py`(406), `test_audio_demo.py`(99), `test_subtitle_align.py`(58) | 삭제 대상 모듈만 검사 |

### 1.4 `15` §2가 지목한 관성 씨앗 — 실측 위치
| 씨앗 | 위치(실측) | 패턴 |
|---|---|---|
| 프롬프트 코드 상수 | `workers/intake_planner_worker.py:48-100`(CATEGORY_GUIDANCE), `:108-174`(_SYSTEM_PROMPT_TEMPLATE) / `research_worker.py:49-129` / `script_worker.py:41-130` / `source_collector_worker.py:55-143` / `dummy_llm_worker.py:38-41` — 합계 약 330줄 | C |
| 15단계 직선 상태 머신 | `orchestrator/state_machine.py:20-45` `LINEAR_SEQUENCE` 24상태, 전이표 없이 `idx+1 ∪ ARCHIVED` | A |
| 손상 manifest → created 폴백 | `orchestrator/command_center.py:31-41` | D |
| 세그먼트→장면 1:1 | `orchestrator/scene_builder.py` | E·F |
| 정규화기가 데이터 모양 강제 | `hyperframes/scripts/bundle_to_video.py`(55 함수, 1,703줄) | B·E |
| 스크립트 워커가 길이 강제 | `workers/script_worker.py` 프롬프트 "영상 길이는 4~6분으로 제한" | F(고정 구성의 뿌리) |
| 모델명 상수 | **없음** — 백엔드는 `claude`/`codex` 이름뿐(`base_llm_worker.py:71-100` CLI_INVOCATION). v0.43.4까지 `claude -p`에 `--model`이 없어 **사용자 머신 CLI 기본 모델이 쓰였고 저장소에 기록되지 않았다** → v0.43.5에서 `config.yaml llm.model = claude-opus-5-5`로 고정(SSOT). ElevenLabs 모델명 기본값 `tts_backends.py:242`, whisper `subtitle_align.py:77` | C(경미) |

### 1.5 계승 자산 (건드리지 않거나 개조만)
- `workers/base_llm_worker.py`(819줄): `claude -p --output-format json` 브리지, `_compose_full_prompt`(:589), 스키마 검증·재시도, 샌드박스 격리. **유지·확장**(프롬프트 파일 로드, 이미지 입력).
- `workers/prompt_safety.py`, `intake_planner_worker.py`, `research_worker.py`, `script_worker.py`, `source_collector_worker.py` — 프롬프트만 파일로 분리.
- `orchestrator/tts_lint.py`(순수 함수, 12 테스트), `tts_pronounce.py`(사전+한자어 숫자), `workers/tts_backends.py`(ElevenLabs·stub·local·voicebox).
- `orchestrator/intake_service.py`, `source_*`, `research_*`, `script_*`, `bundle_io.py`(305줄), `project_manager.py`, `worker_slot_manager.py`, `tui_app.py`, `log_router.py`, `web/intake_page_app.py`.
- `hyperframes/briefing/assets/audio/bgm/` (Zabriskie CC BY 4.0 + RIGHTS.md) → `assets/audio/bgm/`로 **이동**(삭제 아님). `hyperframes/briefing/assets/flags/` 9종 SVG → `assets/flags/`로 이동 후 flag-icons로 보충.
- `samples/*.bundle.json`, `json/`(백필 브랜치) — Phase 9 코퍼스.
- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md`(TTS-AP-001~**063** 존재), `LLM_ANTIPATTERNS.md`(LLM-AP-001~005).

### 1.6 골든 기준
- `docs/handoff/golden/frame_*.png` 25장 = 사용자 제공 `hormuz_korea_480p.mp4`(4:52.44, 854×480, 24fps)와 **픽셀 단위 동일**(7개 시각 대조, 평균 절대차 0.00/255). mp4는 커밋하지 않는다(`.gitignore`), PNG만으로 Phase 1·2 비교가 가능하다.
- 골든 자막 SRT 45문장, 설명문(챕터 12개 시각) 포함.

### 1.7 실행 환경 실측
- 이 클라우드 컨테이너: Python 3.11.15, **ffmpeg 없음, numpy/PIL/cairo/shapely 없음**, fc-list 있음. `pip install imageio-ffmpeg`로 ffmpeg 바이너리 확보 가능(검증됨). pycairo는 `libcairo2-dev` 필요 — apt 가능 여부는 Opus 세션이 첫 작업에서 확인한다.
- 사용자 실행 환경은 **Windows**(run_pipeline.bat, cp949 주의 이력). cairo toy font API의 폰트 이름 해석은 fontconfig(Linux)와 Win32(Windows)가 다르다 → §8 R1.
- git hook은 clone마다 `git config core.hooksPath .githooks`로 켜야 한다(현재 미설정).

---

## 2. 골든 영상에서 확인한 문법 (컨택트 시트 25컷 육안 검수 결과)

Opus는 "프로 다큐로 보이는가" 판정 시 아래를 기준으로 삼는다. 전부 골든 PNG에서 직접 확인했다.
- 모서리에는 **우상단 날짜 배지 하나**(Mono, 금색 밑줄). 브랜드·섹션 번호·제목 없음. 전면 카드(타이틀·엔딩) 중에는 날짜 숨김.
- 자막은 하단 중앙 1~2줄, 강조어만 금색, 헤일로로 가독성 확보. 비네팅 없음.
- 지도는 한 좌표계를 이어 쓴다. 확대 컷(한반도 w=6.4, 서울 w=3.4)에서 도(道)·도시 라벨이 늘고, 광역(w=90)에서는 국가명·해역명만. 라벨 겹침 없음.
- 인물 뱃지: 원 안 국기 펄럭임 + 흑백 컷아웃, 머리가 원 위로 나옴, 아래 검은 라벨 박스(이름) + 직함(강조색).
- 패널(관계·공동성명·연표·전례·찬반)은 지도를 80% 어둡게 덮고 **제목은 중앙 상단**. 관계선은 수평 접선 3차 베지어로 통일, 거절 시 붉은 점선.
- 카드는 우상단 슬라이드 인, 태그(강조색)+큰 수치(GmarketSans)+출처 줄. 기사 클리핑은 종이색 카드에 매체명·날짜·번역 헤드라인·형광펜.
- 미디어: 영상 클립(좌측 또는 패널 위 중앙, PHOTO/VIDEO 칩 + 캡션·출처 바), 사진 카드(우하단), 지도 컷아웃(P-8A, 라벨+출처), 총 7개 / 292초.
- 엔딩 카드: 2단 에디토리얼, 작은 글씨(Sans 9.2 / Mono 7.8), 섹션 5개, 하단 기준일·고지.

---

## 3. 문서 간 불일치·공백 (Opus가 추측하지 않도록 미리 판정)

| # | 발견 | 판정 |
|---|---|---|
| 3.1 | `13` Phase 0은 `scene_builder.py`만 지목하나, `scene_io`·`render_io`·`subtitle_align`·`audio_service`·`audio_io`·`audio_demo`와 `main.py` 핸들러 4개가 연쇄 의존한다(§1.3). `16`은 이들을 Phase 6.8에서 "대체"라고 했다. | 옛 경로를 Phase 6.8까지 남기면 P2 위반이다. **Phase 0에서 연쇄 전부 삭제**하고 `main.py` 핸들러는 `LegacyRemovedError`로 시끄럽게 실패시킨다(§5.3). 새 경로는 Phase 6.8에서 `engine_service.py`로 들어온다. |
| 3.2 | 계승 대상 순수 함수(`tts_of`, `to_polite`, `josa`, `native_count`, `em_segments_line`, `sentence_grounded`, `build_corpus`, `norm_*`, `build_*`)가 삭제 대상 `bundle_to_video.py` 안에 있다. `13`은 분리를 Phase 9로 둔다. | 삭제 시 유실되므로 **Phase 0에서 HTML 생성부를 뺀 순수 함수만 `bundle/` 패키지로 이동**(코드 무변경 이동). 버그 수정(개월·소수)은 Phase 4, 번들→원고 어댑터는 Phase 9 그대로. |
| 3.3 | `03` §5.4가 "TTS-AP-059~061 신규"라 했으나 저장소에는 **TTS-AP-058~063이 이미 존재**(v0.43.4: 059=소수점 공백, 060=절단 표식, 061=경어체 순서). | 신규 항목은 **TTS-AP-064(개월 한자어), 065(유월·시월), 066(소수 표기)**로 번호를 옮긴다. 과거 항목 수정 금지(C6). |
| 3.4 | 소수점 발음: 저장소 v0.43.4는 "13.1%"→"십삼쩜일 퍼센트"(쩜, 무공백)로 **의도적으로** 결정했고(TTS-AP-059), 핸드오프 `03`/`12`는 "팔십삼 점 구 달러"(표준 표기, 된소리는 엔진에 맡김)를 요구한다. 서로 반대다. | **사용자 결정(§4 D6)**. 결정 전까지 원고 발음 텍스트는 사람이 직접 쓰므로 충돌하지 않는다. `tts_of` 수정(Phase 4) 전에 답이 필요하다. |
| 3.5 | GOAL G3(34개 합격 기준)는 `13` Phase 11에서 "사용자 승인 필요"로 개정하되, KICKOFF Phase 0은 "GOAL.md 개정"을 요구한다. | Phase 0은 G0·G1·G4·G5·신설 G7만 개정하고, **G3는 삭제하지 않고 `[legacy — v2 개정안은 부록 C, 승인 대기]` 배너**를 붙인다(DOCS_GOVERNANCE §6.4 삭제 금지). 개정안은 부록 C에 두고 사용자 승인 후 Phase 11에서 반영. |
| 3.6 | `16` §2 새 상태 14개는 `schemas/models.py:40-66` `ProjectState`(24개 값)를 바꾼다. 값이 `project_manifest.json`에 저장되므로 **호환 불가** → `schema_version` 2. | Phase 6.8에서 `schema_version=2`로 올리고, 옛 manifest는 조용히 변환하지 않고 "v1 manifest — 재생성 필요" 오류(P6). 기존 `projects/demo`는 task_queue.json만 있어 영향 없음. |
| 3.7 | collage GOAL G4-10(AI 이미지 가공 허용, 실사 입력 의무)과 `14` §2.2(사실 장면 AI 생성 금지) | 모순 없음. 둘 다 "실사 입력 없는 사실 생성 금지"가 핵심. Phase 0 GOAL 개정 시 collage 문안을 유지하고 `14` §2.2의 세 금지(생성 이미지로 사실 대체, 사상자 식별, 출처 불명)를 G4-13~15로 추가. |
| 3.8 | zip에는 golden mp4·TTS 캐시(`tts/*.mp3`)·`commons_v3.json`·미디어 원본(niovi.webm, strikes.webm, 사진 3장)·Natural Earth·지형 타일·폰트가 **없다**. | mp4는 사용자가 별도 제공(§1.6). 나머지는 Phase 1에서 `prep3.py`·`media3.py` 로직으로 재수집. TTS는 edge-tts 재합성이라 문장 길이가 수십 ms 달라질 수 있다 → 총 길이 ±1초 허용(`13` Phase 1), 프레임 비교는 **앵커 기준**. |
| 3.9 | reference_code는 `/home/claude/v3`, `/home/claude/og` 절대 경로 하드코딩. | Phase 1 `legacy_v3/`는 `V3_ROOT`(기본 `projects/hormuz_korea_legacy`)와 `OG_ROOT`(저장소 루트) 환경변수만 치환하고 **나머지 코드는 손대지 않는다**. |
| 3.10 | `05` §3: `CUT_TARGET` 큐 방식은 순서 실수 위험. `11` §7도 인자형 권고. | Phase 2에서 `dip(t, lon, lat, w)`로 바꾼다. Phase 1은 원본 그대로(골든 재현이 목적). |
| 3.11 | `03` §6.3 단어 앵커: ElevenLabs 정렬 사용 시 `trim_offset` 기록이 필요하나 plan.json에 없다. | Phase 4에서 `Plan.sentences[].trim_offset` 필드 추가(optional, C3 호환 방향). |
| 3.12 | `17` §2 `direction.yaml`의 `place:` 배치 슬롯과 `entity:` 참조는 레지스트리(Phase 5·6.9)가 있어야 동작한다. Phase 2의 `direction.py`는 v3 파이썬 연출층을 그대로 옮긴 것이다. | Phase 2 = `direction.py`(코드), Phase 6.9 = `direction.yaml`(선언형) + 변환기 `direction.py → yaml`(예시 파일 `prompts/examples/hormuz_direction.yaml` 생성용). 두 형식이 공존하는 기간에도 **렌더러 입력은 하나(이벤트 리스트 Pydantic 모델)**다. |
| 3.13 | `09` §1.1 GmarketSans woff→otf 변환본은 공백 글리프가 깨진다(실제 발생). | Phase 1 `prep`이 같은 변환을 재현하되, `text()`의 disp 폰트 공백 특례를 그대로 유지. 폰트 커밋 여부는 §4 D3. |
| 3.14 | `00` §4 번호가 15→16→17→18→19→15 순으로 어긋남 | 내용 문제 아님. 무시. |
| 3.15 | 핸드오프 문서에 DOCS_GOVERNANCE §2 YAML 헤더가 없었다. | 본 세션에서 19개 문서에 `tier: 2` 헤더를 붙였다(원문 무수정, `origin:` 필드로 표시). |

---

## 4. 사용자 결정 요청 (Opus는 답 없이 추측하지 않는다)

| ID | 결정 | Fable 권고 | 필요 시점 |
|---|---|---|---|
| **D1 ✅ 확정** | 기준 브랜치 — `overhaul/v2-map-engine`을 `origin/collage`에서 분기했다(본 세션). 개발 완료 후 main 머지(§4.1) | **`origin/collage`에서 `overhaul/v2-map-engine` 분기.** collage ⊇ main이라 손실 0, 인물 라이브러리·공방·engraving_stylizer·AssetLibrary 스키마가 곧바로 있다. 대안(main 분기 + 체리픽)은 `assets/library` 125 파일과 스키마 373줄을 옮겨야 해 위험만 크다. Fable 세션의 문서 묶음 커밋(`claude/laughing-rubin-rujpp2`)은 `SKIP_VERSION_CHECK=1 git cherry-pick`으로 가져온다(허용 규정 C5.3). | Phase 0 착수 전 |
| **D2 ✅ 확정(Fable 위임)** | 골든 mp4 보관 — 미커밋·로컬 복사(DECISIONS.md) | git에 넣지 않는다(30MB, BGM RIGHTS.md의 대용량 커밋 교훈). 사용자가 `docs/handoff/golden/`에 로컬 복사. 프레임 비교는 PNG로 충분. | Phase 1 |
| **D3 ✅ 확정(Fable 위임)** | 폰트 미커밋, fetch 스크립트 캐시(DECISIONS.md) | 커밋하지 않고 `geo.prep fonts`가 다운로드·변환·캐시(`assets/fonts/.cache`, gitignore). 지마켓 무료 폰트 약관(재배포 조건) 확인 후 커밋 여부 재결정. IBM Plex·Noto(OFL)는 커밋 가능하나 용량상 동일하게 캐시 권장. | Phase 1 |
| **D4** | GOAL G3 개정안(부록 C) 승인 | 부록 C 초안 승인 → Phase 11 반영. 승인 전 G3는 `[legacy]` 배너. | Phase 0 보고 시 |
| **D5** | 사용 제한 휘장(CIA·대통령 문장·IRGC 등) | `assets/emblems/registry.json`의 `decision` 필드에 사용자가 직접 `use`/`flag_fallback`을 기입. 기본값 `user_decision`이면 렌더 전 오류(P6). | Phase 5 |
| **D6 ✅ 확정(사용자)** | 소수점 발음 — 저장소 정책(쩜) 유지, ElevenLabs 연결 후 사용자 청취로 최종 확정 | 저장소 실청취 결과(v0.43.4)가 "쩜 무공백"이므로 **저장소 결정 유지 권고**. 단 자막은 "83.9달러" 원문. 핸드오프 TTS-AP-066은 "표준 표기 강제"가 아니라 "자막≠발음 분리 유지"로 문안 조정. | Phase 4 |
| **D7** | agents_reviewer 번들 스키마 개선안(`12` §6) 제출 | Phase 9에서 문서로 제출, 사용자가 agents_reviewer에 반영. | Phase 9 |
| **D8 ✅ 확정(Fable 위임)** | archive 브랜치 = `archive/hyperframes-briefing` 하나(02 §4.3 이름, 모든 레거시 포함) | `archive/hyperframes-briefing` **하나**(hyperframes·remotion·쇼츠·scene_builder 전부 포함, 분기점 = collage tip). 여러 개로 나누면 복원이 번거롭다. | Phase 0 |
| **D9** | Opus 세션 실행 위치 | 코드 작업(Phase 0)은 클라우드 가능. **Phase 1부터는 렌더·폰트·ffmpeg가 필요**하므로 사용자 로컬(WSL2 권장) 또는 apt 가능한 클라우드 환경. Windows 네이티브 cairo는 §8 R1 위험. | Phase 1 |

### 4.1 main 머지 전략 (사용자 제안 "개발 완료 후 main 머지" — Fable 의견)
- 방향은 맞다. `overhaul/v2-map-engine` ⊇ collage ⊇ main 이므로 main 머지는 **fast-forward**로 끝나고 충돌이 없다. 쇼츠 트랙 35커밋도 함께 main에 들어가지만, Phase 0에서 archive 브랜치 보존 후 삭제되므로 main에는 이력만 남는다.
- **확정(사용자 지시)**: main 첫 머지는 **Phase 1(골든 재현) 통과 후**. 그다음부터는 **사용자가 Phase 보고를 승인할 때마다 main으로 fast-forward**한다(Fable 권고, DECISIONS M1). 이유 ① main이 7월(v0.43.4)에 멈춘 채 collage가 8월까지 독주한 일이 다시 생기지 않는다 ② `docs/branches.html`이 main 기준 VERSION을 보여 준다 ③ 되돌릴 일이 생겨도 Phase 단위 태그(`v2.0.0`, `v2.1.0` …)로 돌아갈 수 있다.
- 절차(사용자 또는 Opus, 승인 직후): `git checkout main && git merge --ff-only overhaul/v2-map-engine && git tag vX.Y.Z && git push origin main --tags`. ff-only가 실패하면 main에 다른 커밋이 들어온 것이므로 멈추고 보고한다.
- 최종 완료(Phase 11, v3.0.0) 후에도 `overhaul/v2-map-engine`은 삭제하지 말고 태그로 남긴다(이력 추적).

---

## 5. Phase 0 정밀 명세 (v2.0.0) — Opus가 그대로 실행

원칙: 커밋 7개, 전부 `v2.0.0:` prefix(같은 버전 다중 커밋은 v0.43.4 이력에 선례 있음). 각 커밋 후 `python -m py_compile`(변경 파일) + `python -c "import orchestrator, workers, schemas, web"` + `pytest -q` 통과. **실패한 채로 다음 커밋으로 넘어가지 않는다.**

### 5.0 준비 (커밋 없음)
```bash
git fetch origin
git checkout overhaul/v2-map-engine && git pull origin overhaul/v2-map-engine   # 이미 존재(v1.2.2, 문서 묶음·모델 고정 포함). 체리픽 불필요
git config core.hooksPath .githooks
pip install -r requirements.txt && pytest -q 2>&1 | tail -3      # 기준선 기록(통과 개수)
python tools/check_env.py                                        # 5.1에서 만든 뒤 실행
```
기준선(통과 개수·실패 목록)을 Phase 0 보고서에 적는다. collage 기준 테스트는 355+38+…건이다.

### 5.1 커밋 ① `v2.0.0: 헌법 개정 — 영상 기준을 docs/handoff로 교체, 관성 방지 원칙 편입`
변경 파일: `VERSION`(→`2.0.0`), `CLAUDE.md`, `GOAL.md`, `HANDOFF.md`, `README.md`, `CHANGELOG.md`, `DEVLOG.md`, `tools/check_env.py`(신설).

**CLAUDE.md** — 다음을 정확히 수행한다.
1. C0 본문을 교체: "영상 기준의 정본은 `docs/handoff/`(01·02·04~11·14)이다. 기준 작품은 v3『호르무즈와 한국』(`docs/handoff/golden/`). 이전 영상 기준(섹션=장면, 고정 막, HyperFrames/Remotion 문법, `docs/07/08/09` 구판)은 v2.0.0에서 폐기됐다." + 되돌리면 안 되는 목록(KICKOFF §5) 그대로. 경계 문단(사실·권리·검증 우선)은 유지.
2. **C0.1 신설 "byte-equal 비적용"**: "이번 개편에는 '기존 출력 불변(byte-equal)' 원칙을 적용하지 않는다. 기준은 v3 골든 재현이다(`15` §3 P7)."
3. **C11 신설 "관성 방지 규칙(필독 `docs/handoff/15`)"**: P1~P12를 한 줄씩 규칙화. 특히 ① 프롬프트 코드 상수 금지 → `prompts/*.md` ② 규칙 SSOT `rules/video_rules.yaml` ③ 레지스트리 미등재 이벤트 = 오류 ④ 폴백으로 옛 스타일 출력 금지 ⑤ 영상마다 `provenance.json` ⑥ 코드가 LLM 구성을 정규화로 되돌리지 않음 ⑦ 검수 결과를 live 프롬프트에 자동 편입 금지.
4. C7 표에 행 추가: `rules/video_rules.yaml` 변경 → `prompts/` 재생성 확인 + `tests/anti_inertia` / 새 이벤트 타입 → 스키마·렌더러·프리뷰 예제 세 곳 / `docs/handoff/*` 변경 → 본 문서 §3.
5. C8에 "0. `docs/handoff/15`를 읽지 않고 오케스트레이터·워커·엔진을 수정하지 않는다." 추가. C8.5(PR 금지) 유지.
6. C10(폐지)은 그대로 둔다.
7. YAML 헤더 `last_synced_with: v2.0.0`.

**GOAL.md**
1. G0: 구체 기준 문장을 `docs/handoff` 참조로 교체(C0과 같은 문안, 중복 대신 링크 — DOCS_GOVERNANCE §3).
2. G1 산출물 표를 새 것으로 교체(`16` §6): `out/final.mp4`, `out/final.srt`, `out/description.txt`, `out/thumbnail_candidates/`, `out/provenance.json`, `script.yaml`(approved_at 포함), `plan.json`, `direction.yaml`, `assets.lock.json`, `prev/sheet.jpg`+`checks.json`+`qa_verdict.v*.json`, `intake/sources.json`+`claims.json`, `project_manifest.json`, `approval_log.json`(게이트 2개). 옛 항목(`draft_debug.mp4`, `remotion_job`, `render_report.json`)은 `[deprecated v2.0.0]`.
3. G3: 제목 아래 배너 `> [legacy — v1 MVP 기준. v2 개정안: docs/handoff/19 부록 C, 사용자 승인 대기. 승인 전까지 합격 판정에 쓰지 않는다.]` 항목 19·20·26·27은 `[deprecated v2.0.0]` 마킹.
4. G4에 추가(13~20): 13 고정 막·섹션=장면 1:1 구성 금지 / 14 모서리에 날짜 외 요소(브랜드·섹션 번호·제목) 금지 / 15 도장·비네팅 금지 / 16 문장마다 카메라 이동·줌 범프 금지 / 17 관계선 동시 등장 금지 / 18 AI 상투 문구(`rules/video_rules.yaml banned_phrases`) 금지 / 19 발음 텍스트에 숫자·기호 금지 / 20 실패 시 옛 스타일 폴백 출력 금지(중단·보고). G4-10은 collage 문안 유지 + `14` §2.2(생성 이미지로 사실 대체, 사상자 식별, 출처 불명) 추가.
5. G5 비목표에 "쇼츠·콜라주 트랙(보관)", "텔레그램 봇, 유튜브 자동 업로드(엔진 안정화 후 별도 계획)" 추가.
6. **G7 신설 "영상 기준 정본"**: `docs/handoff/` 목록과 읽는 순서, 골든 위치.
7. 헤더 `last_synced_with: v2.0.0`.

**HANDOFF.md**: 상단 "다음 할 일" 블록 전체를 교체 → "v2 전면 개편 진행 중. 착수 문서 `docs/handoff/KICKOFF_PROMPT.md`, 실행 계획 `docs/handoff/19`. 현재 Phase: 0. 결정 대기: D1~D9." 쇼츠 핸드오프 블록은 `## [보관] 쇼츠 콜라주 핸드오프(v1.0.5~1.2.1, archive 브랜치)`로 이동(삭제 아님).

**README.md**: 소개 문단의 "Remotion 렌더"를 "지도 중심 다큐 엔진(engine/)"으로, 문서 진입점 표에 `docs/handoff/00_INDEX.md` 행 추가.

**CHANGELOG.md**: `## [v2.0.0] — 2026-xx-xx` "Changed: 영상 기준 전면 교체…, Removed: hyperframes/remotion/scene_builder…(커밋 ②에서 채움)". **DEVLOG.md**: 엔트리 1개(무엇을/왜/어떻게/결과/연관 = docs/handoff/15).

**tools/check_env.py**(신설, 표준 라이브러리만): python≥3.11, `ffmpeg`(PATH 또는 imageio-ffmpeg), `fc-list`, import 가능 여부(cairo, numpy, PIL, shapely, scipy, yaml, pydantic, edge_tts, requests, cairosvg, fontTools, rembg), 필수 폰트 4종(`fc-list : family`), 디스크 여유. 결과를 표로 출력하고 누락 시 exit 1. Phase 1의 첫 관문.

### 5.2 커밋 ② `v2.0.0: 레거시 archive 브랜치 보존 후 삭제 (hyperframes·remotion·scene_builder·render_io·audio_service)`
**순서가 중요하다.**
```bash
git branch archive/hyperframes-briefing origin/collage      # D8
git push -u origin archive/hyperframes-briefing
```
그다음 삭제/이동:
| 조치 | 대상 |
|---|---|
| `git mv` | `hyperframes/briefing/assets/audio/bgm/` → `assets/audio/bgm/` (RIGHTS.md 포함) / `hyperframes/briefing/assets/flags/` → `assets/flags/legacy_svg/` / `hyperframes/demo/assets/pronounce.json` → `assets/pronounce/pronounce_ko.json` (`orchestrator/tts_pronounce.py` 기본 경로·docstring 갱신) |
| 커밋 ③으로 **먼저 이관** | `hyperframes/scripts/bundle_to_video.py`의 순수 함수(§5.3) — 이관 커밋을 ②보다 앞에 두거나, ②와 ③을 같은 작업 트리에서 순서대로 만든다. 어느 쪽이든 **함수 유실 상태의 커밋을 만들지 않는다** |
| `git rm -r` | `hyperframes/`, `remotion/`, `design_sheets/`, `docs/17_COLLAGE_DESIGN_SHEET.md`, `docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md`, `docs/PROFESSIONAL_REBUILD_PLAN.md` |
| `git rm` | `orchestrator/scene_builder.py`, `scene_io.py`, `render_io.py`, `subtitle_align.py`, `audio_service.py`, `audio_io.py`, `audio_demo.py` |
| `git rm` | `tests/test_scene_flow.py`, `test_render_flow.py`, `test_audio_flow.py`, `test_audio_demo.py`, `test_subtitle_align.py`, `tests/test_collage_models.py`, `tests/test_design_sheet_naming.py` (collage 스키마 삭제 시) |
| `orchestrator/main.py` | `build-scene`, `build-audio`, `build-audio-demo`, `render-debug` 서브커맨드 핸들러 본문을 `raise LegacyRemovedError("<cmd>는 v2.0.0에서 삭제됨 — 대체 경로는 docs/handoff/16 §4 engine_service (Phase 6.8). archive/hyperframes-briefing 참조")`로 교체. `LegacyRemovedError`는 `orchestrator/errors.py` 신설. 서브커맨드 자체는 남겨 **시끄럽게** 실패하게 한다(P6). import 문(`:838, :900, :1003`) 제거. |
| `orchestrator/config.py`, `config.yaml` | `paths.remotion_root` 삭제, `render.default_resolution/default_fps/profiles.briefing/shorts` 삭제(커밋 ④에서 `engine:`로 대체) |
| `schemas/models.py` | §1.3의 렌더/장면/오디오 모델 13종 + collage `DesignSheet`, `SafeArea`, `CastEntry`, `ArtDirection`, `RenderMode`(다른 참조 없으면) 삭제. **삭제 전 `grep -rn <ClassName> --include=*.py`로 참조 0 확인. 참조가 남으면 삭제하지 말고 목록을 보고서에 적는다.** `AssetLibrary*`, `Bundle*`는 유지. |
| `pyproject.toml` | `keywords`의 "remotion" 제거 |
| `docs/07_VIDEO_STYLE_GUIDE.md`, `08_AUDIO_AND_TTS_SPEC.md`, `09_MAP_AND_GEO_SPEC.md`, `10_RENDERING_PIPELINE_SPEC.md`, `ADDENDUM_02_PRE_PRODUCTION_DEBUG_LAYER.md` | 첫 줄 아래 배너: `> [deprecated v2.0.0] 본 문서의 영상 기준은 폐기됐다. 정본: docs/handoff/{05,08,09 / 03,10 / 04 / 11}. Phase 11에서 재작성.` (내용 삭제 금지) |
| `.gitignore` | `remotion/`, `hyperframes/` 항목을 `# (v2.0.0 삭제)` 주석으로 정리 |
| `run_pipeline.bat` | 그대로(Command Center 진입) |

검증: `pytest -q` 전부 통과(삭제한 테스트 제외), `python -m orchestrator.main build-scene demo` 실행 시 `LegacyRemovedError` 메시지가 뜨고 exit≠0, `grep -rn "hyperframes\|remotion\|scene_builder" --include=*.py . | grep -v docs/handoff` 결과 0.

### 5.3 커밋 ③ `v2.0.0: bundle/ 패키지 — bundle_to_video 순수 함수 무변경 이관`
`hyperframes/scripts/bundle_to_video.py`에서 **HTML·파일 I/O 없는 함수만** 옮긴다(함수 본문 무수정, docstring에 `# moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)` 한 줄).
- `bundle/__init__.py`
- `bundle/text.py`: `char_units, est_units, clip, sentences, wrap_units, date_kr, native_count, josa, normalize_display, iso_to_kr, _date_kr_tts, _native_unit, _iso_date_tts, _slash_date_tts, _decimal_tts, tts_of, to_polite, build_corpus, sentence_grounded, em_segments_line, fix_phrasing, quote_segments`
- `bundle/charts.py`: `split_unit, build_candle, build_bar_panels, norm_stacked, norm_waterfall, norm_scatter, norm_heatmap, _full_date, norm_gantt, norm_sankey, _strip_lead_date, build_signals, build_slopes, build_tables, norm_map, norm_network, _load_map_metas, _project_merc, section_for_chart, build_versus, build_markets`
- 이관하지 않는 것(HTML·장면 문법): `build_title, pick_timeline_steps, build_ladder, section_videos, timeline_kind, fetch_photos, build_closing, find_section, convert, emit_html, preview_charts, main` — archive에만 남긴다. `fetch_photos`는 Phase 6.5의 참고용이므로 `docs/handoff/reference_code/repo_legacy/fetch_photos.py`로 복사해 둔다.
- 테스트: `tests/test_tts_pronounce.py` 등 기존 테스트가 `bundle_to_video`를 import하면 경로만 바꾼다. `tests/test_bundle_text.py` 신설: `tts_of('18개월')` 현재 출력을 **있는 그대로** 고정(버그 수정은 Phase 4에서 테스트를 바꾸며 함께).

### 5.4 커밋 ④ `v2.0.0: rules/video_rules.yaml SSOT + config 단일화`
- `rules/video_rules.yaml` = **부록 A** 그대로. `rules/__init__.py`에 `load_rules() -> VideoRules`(Pydantic, `extra="forbid"`)와 `rules_hash() -> str`(sha1 of file bytes) 구현. `schemas/rules_models.py`에 모델.
- `config.yaml`에 추가: `engine: {trial: {width: 854, height: 480, fps: 24}, final: {width: 1920, height: 1080, fps: 24}, jobs: 4, crf: 19}`, `llm: {model: claude-opus-5-5 (v0.43.5에서 이미 추가됨 — `claude -p --model` 로 전달), backend_default: claude, mode_default: response, invoke_timeout_sec: 600, script_timeout_sec: 1200}`, `tts: {backend_default: elevenlabs, edge_voice: ko-KR-InJoonNeural, edge_rate: "-3%", edge_pitch: "-2Hz", eleven_model_env: ELEVENLABS_MODEL_ID, eleven_model_default: eleven_multilingual_v2, voice_settings: {stability: 0.65, similarity_boost: 0.8, style: 0.1}}`. `orchestrator/config.py`에 `EngineConfig`, `LLMConfig`, `TTSConfig` Pydantic 모델(`extra="forbid"`).
- `workers/tts_backends.py:242`의 `"eleven_multilingual_v2"` 기본값과 `script_worker.py:148`의 `1200`은 config에서 읽도록 교체(모듈 상수 override 금지, P3).
- 시작 시 유효 설정 덤프: `orchestrator/main.py`의 모든 서브커맨드 진입에서 `log.info("effective_config", cfg.model_dump())` 1줄(V5_ACTIVATION §4 교훈).

### 5.5 커밋 ⑤ `v2.0.0: 워커 프롬프트를 prompts/ 템플릿 파일로 분리 (코드 상수 금지)`
- `prompts/intake_planner.md`, `prompts/intake_planner_category_guidance.yaml`(CATEGORY_GUIDANCE dict), `prompts/research.md`, `prompts/script.md`, `prompts/source_collector.md`, `prompts/dummy.md`. **Phase 0에서는 내용을 옮기기만 한다**(문안 개정은 Phase 6.9). 단 `prompts/script.md`의 "영상 길이 4~6분 제한" 문단은 삭제한다(고정 구성의 뿌리, G4-13). 삭제 사실을 DEVLOG에 적는다.
- `workers/prompt_loader.py`: `load_prompt(name: str, rules: VideoRules) -> str`. 템플릿의 `{{RULES.banned_phrases}}`, `{{RULES.balance_principles}}`, `{{RULES.tts_rules}}` 자리표시를 `.replace()`로 치환(C2, `.format()` 금지). 치환 안 된 `{{`가 남으면 `PromptTemplateError`.
- `BaseLLMWorker`: `system_prompt: ClassVar[str]` 제거 → `prompt_name: ClassVar[str]` + `def system_prompt(self) -> str: return load_prompt(self.prompt_name, self.rules)`. `_compose_full_prompt`는 그대로.
- 프롬프트 해시를 `task_result.json`의 `worker_provenance.prompt_sha1`에 기록(P5 준비).
- 기존 테스트(`test_base_llm_worker*.py`, `test_intake_planner_worker.py`, `test_source_collector_worker.py`, `test_research_flow.py`, `test_script_flow.py`)가 `system_prompt` 문자열을 검사하면 파일 로드 결과로 바꿔 통과시킨다.

### 5.6 커밋 ⑥ `v2.0.0: 관성 방지 테스트 8종 (4 통과 · 4 strict xfail)`
`tests/anti_inertia/` 8파일 — **부록 B** 명세대로. Phase 0 통과 4종: `test_no_legacy_imports`, `test_prompts_from_files`, `test_constitution`, `test_single_config`. 나머지 4종은 `@pytest.mark.xfail(strict=True, reason="Phase N — …")`로 둔다. strict라 구현이 끝나면 XPASS가 **실패**로 잡혀 마커 제거를 강제한다.

### 5.7 커밋 ⑦ `v2.0.0: Phase 0 보고서`
`docs/handoff/reports/PHASE0_REPORT.md`: 변경 요약 / **이번 Phase의 결정 요약(DECISIONS.md 새 행)** / 테스트 결과(기준선 대비) / 프리뷰(해당 없음 — Phase 0은 영상 영향 없음, 명시) / provenance(해당 없음, 명시) / 다음 Phase 계획 / 결정 대기 목록(D2~D9). DEVLOG 한 줄. 여기서 **멈추고 사용자에게 보고**한다.

### 5.8 Phase 0 합격 기준(자동 검증)
```bash
pytest -q tests/anti_inertia -k "no_legacy_imports or prompts_from_files or constitution or single_config"   # 4 passed
pytest -q                                                             # 나머지 전부 passed, xfail 4
python -m orchestrator.main version                                   # 2.0.0
git ls-remote --heads origin archive/hyperframes-briefing              # 존재
test ! -d hyperframes && test ! -d remotion                           # 삭제 확인
```

---

## 6. Phase 1~11 실행 요강 (`13`의 합격 기준 + 이 문서의 보정)

버전: Phase 1 = v2.0.1~, Phase 2 = v2.1.0, 3 = v2.2.0, 4 = v2.3.0, 5 = v2.4.0, 6 = v2.5.0, 6.5 = v2.5.5, 6.8 = v2.5.8, 6.9 = v2.5.9, 6.95 = v2.5.95 → **주의**: PATCH가 두 자리(95)면 정렬이 어긋나므로 **6.95는 v2.6.0, Phase 7은 v2.6.1, 8은 v2.7.0, 9는 v2.8.0, 10은 v2.9.0, 11은 v3.0.0**으로 정한다(`13`의 번호를 이 문서가 보정). **[D39 재보정 2026-09-28: Phase 6.8은 manifest schema_version 2(C3·C5.4 MAJOR)라 v3.0.0. 이후 6.9 v3.1.0, 6.95 v3.2.0, 7 v3.3.0, 8 v3.4.0, 9 v3.5.0, 10 v3.6.0, 11 v3.7.0, G v3.8.0~. DECISIONS D39.]**

| Phase | 핵심 산출물 | 합격 기준(요약) | 이 문서의 보정·함정 |
|---|---|---|---|
| **1 골든 재현** (v2.0.1+) | `legacy_v3/`(reference_code 복사, 경로만 환경변수화), `tools/fetch_data.py`(Natural Earth 3종, terrarium 타일 135장, flag-icons, 폰트 4종, Commons 인물·휘장·미디어), `projects/hormuz_korea_legacy/` 산출물, `prev/sheet.jpg` | 4:52±1초, 854×480@24, 22컷 육안 동일, `land-miss=['MV']`만, 린트 통과, 45문장 | `check_env.py` 먼저. TTS는 edge-tts 재합성(캐시 없음) → 절대 시각 편차 허용, **골든 비교는 `tools/golden_compare.py`가 앵커(sid+offset)로 시각을 재계산**해 25장 MAD를 표로 출력(임계 2/255는 Phase 2용, Phase 1은 참고). Commons 429 대책(`14` §10.4). 사상자 식별 구간 배제. |
| **2 모듈 분해·계약** (v2.1.0) | `engine/`, `script/`, `audio/`, `projects/hormuz_korea/{script.yaml, direction.py}`, Pydantic(`Script/Scene/Sentence/Plan/CamKey/Event*/Tier/RightsRegistry`), CLI 4종 | Phase 1 대비 25장 MAD<2/255(폰트 차 허용), 스키마 오류가 렌더 전 발생, pytest(timebase·ym 왕복·카메라·강조 분할) | 부록 D 매핑표를 그대로 따른다. `dip(t,lon,lat,w)` 인자형. `style.px()` 도입은 Phase 10이지만 **상수는 Phase 2에서 `engine/style.py` 한 곳에 모아 둔다**. 이벤트 레지스트리(`engine/registry.py`) 신설: type→(모델, 렌더러) — 미등재 = 오류(P10). `test_registry_complete` xfail 해제 후보. |
| **3 지오 일반화** (v2.2.0) | `geo/prep_geometry.py --bbox`, `geo/prep_tiers.py --tier`, 프로젝트별 `labels.yaml` | 대만해협 권역 1줄 준비, 커버리지 테스트, 프랑스 회귀 | 재귀 `polys()`·박스 클램프·크림 재분류 옵션. 타일 캐시 gitignore. |
| **4 원고·음성** (v2.3.0) | `script/lint.py`, `script/tts/{edge,elevenlabs,cache,trim}.py`, `trim_offset`, `at_word` 정렬, TTS-AP-**064~066** | ElevenLabs 목소리로 전편 재생성 시 연출 무수정 싱크, "거절" 전환 ±0.15초, 금지 문구 12개 검출 | D6 답 필요. 캐시 키에 voice_id. `.env`만. `tests/test_prompt_schema_parity` 대상에 script 프롬프트 예시 포함. |
| **5 뱃지·엔티티·권리** (v2.4.0) | `assets/entities.yaml`, `assets/emblems/registry.json`, `tools/commons_fetch.py`, `tools/portrait_fallback.py`(engraving_stylizer 재사용), `engine/mux.py` 크레딧 | 이름→뱃지 자동 제안, 제한 휘장 국기 대체+사유, 엔딩 크레딧 전 자산 | D5. 라이브러리 24인 `library_manifest.json`을 엔티티 레지스트리의 1차 소스로 조인. **삭제: `tools/bootstrap_assets/prep_people_flags.py`(people·flags 부트스트랩, D32).** |
| **6 패널·카드 데이터화** (v2.5.0) | 관계 패널 nodes/edges/state_changes, 연표 자동 층, 카드 RESERVED, v2 차트 5종 이식 | 부산 뱃지 미가림, 관계선 7개 초과 경고 | 정돈 규칙(`08` §3) 코드 내장. |
| **6.5 미디어** (v2.5.5) | `engine/layers/media.py`, `tools/media_fetch.py`, `assets/media/media_registry.json` | v3 미디어 7종 재현, 밀도 린트, 출처 줄 누락 시 오류 | `post` 카드는 6.95. 긴 클립 ffmpeg 스트리밍. **삭제: `tools/bootstrap_assets/media_first_pass.py` — 두 파일 모두 사라지면 `tools/bootstrap_assets/` 폴더째(D32).** |
| **6.8 오케스트레이터 통합** (v2.5.8) | 새 `ProjectState`(schema_version 2), `engine_service.py`(StageResult), 승인 게이트 2개 UI, provenance | Command Center CREATED→DONE, 반려→되돌림, `test_provenance_e2e` | §3.6. `command_center.py` 폴백 제거(손상 manifest = 오류). `review_gates.require_human_approval`을 2개로. |
| **6.9 AI 연출가·시각 검수** (v2.5.9) | `direction.yaml` 스키마·검증기, 배치 슬롯, `checks.json`, 시각 검수 워커(이미지 입력), 루프≤2, 프롬프트 5종 | 원고만 주고 연출 자동 생성 → hard 0 → 사용자 판정 | `prompts/examples/hormuz_direction.yaml`은 Phase 2 `direction.py`에서 변환기로 생성. 루프 상한은 코드. |
| **6.95 소스 인테이크** (**v2.6.0**) | 소스 레코드, 캡처 판독, claims.json, `post` 카드, claim id 강제 | X 캡처 3 + 기사 2 → 원고 초안 | `rules/official_accounts.yaml`. 스크래핑 금지. |
| **7 카메라 자동화** (v2.6.1) | `frame_points`, move/dip 자동, 숏 린트 | v3 연출을 자동값으로 바꿔도 동등 | 옵션이지 강제 아님(P8). |
| **8 오디오** (v2.7.0) | BGM 레지스트리, `music_intensity`, 교차 페이드, 오디오 QA | −14 LUFS, 음악 −14~−18dB | `assets/audio/bgm/RIGHTS.md` 크레딧 문구 그대로. |
| **9 번들 어댑터** (v2.8.0) | `bundle/{load,entities,to_script,to_direction}.py`, 스키마 개선안 문서 | 랫클리프 번들 자유 구성 초안 | D7. `json/` 63건은 백필 브랜치에서 가져온다. |
| **10 해상도·성능** (v2.9.0) | `style.px()`, 1080p, 청크 병렬 | 1080p 전편, 비율 동일 | 티어 ppd 2.25배 또는 w 하한. |
| **11 문서·정리** (v3.0.0) | docs 07/08/09/10 재작성, G3 개정(부록 C 승인본), 폐기 확인 | — | D4. |

---

## 7. 검수 루틴 (모든 Phase 공통)

1. `python -m engine.render <proj> --preview auto` → `prev/sheet.jpg`(4열, 427×240, 컷마다 앵커·시각 라벨). Phase 1은 `legacy_v3/render3.py --preview` + `tools/contact_sheet.py`.
2. `tools/golden_compare.py <proj>`: `golden_frames.json`의 25 앵커를 현재 plan.json으로 재계산 → 렌더 → MAD 표(+ 차이 히트맵 PNG). 임계 초과 컷은 목록으로.
3. 전환 구간(타이틀·dip 3회) 0.3초 간격 8컷 시트.
4. 사용자 보고 5항목(KICKOFF §7). 코드 리뷰만으로 "적용됨" 판정 금지.

---

## 8. 위험 요소와 대책

| ID | 위험 | 대책 |
|---|---|---|
| R1 | **Windows cairo 폰트 이름**: `select_font_face('IBM Plex Sans KR Medium')`은 fontconfig 기준. Win32 백엔드는 family/weight 해석이 달라 폰트가 폴백될 수 있다(확인 안 됨, 가능성) | Phase 1 첫 렌더를 사용자 환경에서 하고 `prev/font_check.png`(폰트 10종 샘플)로 확인. 문제 시 WSL2 권장 또는 `engine/typography.py`에 OS별 이름 표를 둔다. |
| R2 | edge-tts 서비스 변동, 목소리 변경 | ElevenLabs가 목표 기본값. 앵커 기반 연출이라 싱크는 유지. |
| R3 | Commons 429, 타일 서버 지연 | 요청 간격 15초, 원본 URL, 캐시 재사용, 검증(`PIL.verify`). |
| R4 | rembg 모델(170MB) 다운로드 차단 환경 | 1순위는 라이브러리·공방. rembg는 폴백. |
| R5 | 1 vCPU 클라우드에서 전편 렌더 20분+ | 청크 병렬(Phase 10 전에도 `--jobs`는 Phase 2에서 단순 구현 가능). |
| R6 | GmarketSans 재배포 조건 | D3. 캐시 방식이면 저장소 무관. |
| R7 | 삭제 커밋이 다른 브랜치 작업(local-audio)과 충돌 | local-audio는 미병합 이력이며 개편과 무관. 병합하지 않는다. |
| R8 | 큰 바이너리(골든 PNG 7MB, 향후 티어 PNG) | 티어·타일·TTS·미디어 원본은 gitignore. 골든 PNG만 커밋(이미 반영). |
| R9 | Opus가 `13` Phase 0 문면대로 `scene_builder.py`만 지우고 나머지를 남김 | §3.1·§5.2 목록이 정본. `test_no_legacy_imports`가 잡는다. |

---

## 부록 A. `rules/video_rules.yaml` 초안 (Phase 0 커밋 ④에서 그대로 생성)

```yaml
# rules/video_rules.yaml — 영상 규칙 SSOT (docs/handoff/15 §3 P3). 코드·프롬프트·린트·검증기가 모두 이 파일을 읽는다.
# 수치의 출처는 docs/handoff/{03,05,08,09,14}. 사용자 합격 값이므로 근거 없이 바꾸지 않는다.
schema_version: 1
rules_version: "2.0.0"

banned_phrases:            # 03 §2 — 정규식, 자막 텍스트에 적용. 하나라도 맞으면 린트 실패
  patterns:
    - '가지.{0,8}(화살|문제|흐름).{0,12}모인다'
    - '한\s?번에 흔들'
    - '세\s?겹'
    - '방향을 정한다'
    - '같은 자리로 돌아'
    - '로 읽으면'
    - '승부는'
    - '진짜 뉴스'
    - '계약서에'
    - '서 있는 자리'
    - '만 보면'
    - '로 읽힌다'
    - '말하지 않는 것'
    - '이것이 바로'
    - '핵심은 .{0,10}(이다|입니다)$'
  candidates:              # 03 §2.1 추가 후보 — 사람 승인 후 patterns로 승격
    - '결국 .{0,12}의 문제다'
    - '의 시대가 열렸다'
    - '판이 바뀌었다'
    - '게임 체인저'
    - '라는 질문이 남는다'
  defect_classes:          # 새 문구 판단 기준(프롬프트 머리말에 삽입)
    - 수렴 은유
    - 과장된 동시성
    - 숫자 겹 은유
    - 예언형 결론
    - 회귀 수사
    - 해석 강요
    - 가짜 대구
    - 진짜 이유류 메타 발언

balance_principles:        # 03 §3 — 프롬프트 공통 머리말
  - 모든 수치에 출처(매체·날짜). 화면 카드에는 src 줄.
  - 주장은 귀속한다(밝혔습니다/보도했습니다).
  - 논쟁 사안은 양쪽을 같은 무게로, 출처와 함께.
  - 추정은 "추정"으로 표시. 출처 없는 차트는 "추정 · 출처 미기재" 태그.
  - 마무리는 예언 대신 미정 사실.

script_schema:             # 02 §2.1 요약 — 프롬프트 예시는 tests/anti_inertia/test_prompt_schema_parity 로 검증
  sentence_fields: [date, text, tts, emphasis, sources, media]
  date_formats: ["YYYY", "YYYY.MM", "YYYY.MM.DD"]
  subtitle_max_lines: 2
  subtitle_wrap_px_480p: 700
  scene_count: free        # 고정 막 금지(G4-13)
  duration_limit_sec: null # 길이 제한 없음

tts_rules:                 # 03 §4·§5
  forbidden_chars_regex: '[0-9%~/:→()\[\]]'
  sino_numbers_no_inner_space: true       # TTS-AP-058
  native_count_units: [개, 명, 번, 살, 회]  # 고유어 수사
  sino_count_units: [개월, 건, 년, 원, 달러, 배럴, 척, 퍼센트]
  month_readings: {"6월": "유월", "10월": "시월"}
  abbreviation_policy: korean_expansion   # CENTCOM → 미군 중부사령부
  decimal_policy: user_decision_D6        # docs/handoff/19 §4 D6 — 결정 전 원고에서 직접 기입
  emphasis_must_be_substring: true

shot_grammar:              # 05 §2
  camera_moves_per_scene_max: 1
  shot_min_hold_sec: 6.0
  move_dur_sec: [2.6, 3.4]
  move_lead_sec: [0.6, 1.2]
  dip_total_sec: 1.0
  dip_max_per_sec: 90      # 90초당 1회 이하
  dip_alpha_peak: 0.93
  zoom_bump: false
  drift: {amount: 0.03, tau_sec: 9.0}
  ending_pullback: {w_from: 88, w_to: 96, dur_sec: 9.0}
  auto_transition: {dip_if_dist_over_w: 2.5, dip_if_w_ratio_over: 6.0}
  w_guide: {continental_route: [88, 96], ocean: [60, 72], region: [20, 30], strait: [12, 16], country: [6, 8], metro: [3, 5], city: 2.5}

media_beats:               # 14 §10
  per_runtime_sec: [40, 60]
  per_scene_max: 1
  article_card_exempt: true
  no_consecutive_same_kind: true
  kinds: [photo, clip, cutout, article, post]
  photo_show_sec: [4, 8]
  clip_show_sec: [3, 6]
  file_photo_label_required: true         # "자료사진 · 연월"
  caption_credit_required: true
  ai_generated_forbidden: true            # G4-10, 14 §2.2
  casualty_identifiable_forbidden: true

hud:                       # 09 §5 — 모서리에는 날짜만
  allowed_corner_elements: [date_badge]
  forbidden_components: [brand_mark, section_number, section_title, stamp, vignette, scrubber, chapter_number]
  date_badge: {font: mono, size: 15, x_right: 26, y: 40, underline_y: 48, underline_w: 1.4, slide_px: 6, slide_sec: 0.45}

layout_480p:               # 09 §2·§4, 08 §10 — 기준 해상도 854×480. 다른 해상도는 k = H/480
  base: {w: 854, h: 480, fps: 24}
  subtitle: {size: 19, last_line_y: 452, line_gap: 26, halo: 5.0, halo_alpha: 0.92, emphasis_color: gold}
  min_font_px: 9.5         # 화면 높이 2% 규칙(엔딩 카드 예외)
  title_card: {dur_sec: 5.6, title_size: 46, subtitle_size: 18, rule_w: 220}
  end_card: {dur_sec: 11.0, item_size: 9.2, license_size: 7.8}
  card: {x_right_margin: 24, y: 70, min_w: 230, slide_px: 30, fade_sec: 0.45, big_size: 30, line_size: 13, tag_size: 10.5, src_size: 9.5}
  article_card: {w: 300, y: 68}
  panel: {cover_alpha: 0.8, fade_sec: 0.6, title_size: 19, title_y: 74, subtitle_size: 11, subtitle_y: 96, min_screen_use: 0.7}
  badge: {R_person_map: [30, 34], R_person_panel: 36, R_flag: [17, 24], reserve_top_factor: 2.2, reserve_bottom_px: 44, popin_sec: 0.55}
  timeline_gaps: {gap_sec: 0.5, scene_gap_sec: 1.0, lead_sec: 1.2, title_after_cold_open: true}
  fade: {in_sec: 1.2, out_sec: 1.6}
  reserved_zones: {card: {x_from_right: 260, y: [70, 200]}, subtitle: {y_from: 410}}

colors:                    # 09 §7
  ru: "#ff5566"
  us: "#5aa9ff"
  gold: "#e8b860"
  teal: "#5cc8da"
  green: "#8fd08a"
  muted: "#a9b0bd"
  amber: "#ffb347"
  sea_label: "#9cc8e6"
  panel_cover: [0.025, 0.03, 0.045, 0.8]
  card_bg: [0.05, 0.06, 0.09, 0.86]
  panel_card_bg: [0.07, 0.08, 0.12, 0.92]

fonts:                     # 09 §1
  sans: "IBM Plex Sans KR"
  serif: "Noto Serif CJK KR"
  display: "GmarketSans"
  mono: "IBM Plex Mono"
  mono_hangul_fallback: sans
  display_space_advance: 0.3

labels:                    # 04 §6·§7
  border_lod_w: 22
  admin1_fade_w: [24, 14]
  province_w_max: 8.5
  city_max_per_frame: 18
  country_rank_thr: {60: 2, 30: 4, 12: 6, 0: 9}
  city_rank_thr: {60: 1, 25: 2, 12: 4, 5: 6, 0: 8}

registries:                # 15 §3 P10 — 여기 없는 타입을 연출이 쓰면 오류, 있는데 렌더러가 없으면 오류
  event_types: [marker, route, tanker_loop, barrier, ships, boom, country, badge, card, panel, dip, photo, clip, cutout, article, post]
  event_types_planned: [occupied, arc, channel, shield, tl, particles, flash, dots, movers, line, arrow]   # v1/v2 이식 후보(미구현 = 사용 불가)
  panel_kinds: [refusal, statement, timeline, precedent, versus]
  panel_kinds_planned: [dots, gantt, dual_line, fork, checklist, network]
  badge_kinds: [person, flag, emblem]
  accents: [gold, us, ru, teal, muted, green, amber]

audio:                     # 10
  bed_gain: 0.47
  duck_depth: 0.5
  duck_pre_sec: 0.25
  duck_post_sec: 0.3
  duck_smooth_sec: 0.35
  narration_peak: 0.8
  master_peak: 0.97
  loudnorm: {I: -14, TP: -1.5, LRA: 11}
  sfx_policy: events_and_scene_starts_only

qa_checks:                 # 17 §3 — 결정적 사전 검사 임계
  overlap_core_elements: 0
  offscreen_clip: 0
  missing_glyphs: 0
  labels_per_frame_max: 18
  subtitle_lines_max: 2
  rights_missing: 0
  forbidden_components: 0
  visual_qa_loop_max: 2

provenance:                # 15 §3 P5
  required_keys: [engine, rules_hash, prompts, features_used, qa, drops]
  fail_if_drops: true
```

## 부록 B. 관성 방지 테스트 8종 명세 (`tests/anti_inertia/`)

| 파일 | 검사 | 통과 조건 | Phase 0 상태 |
|---|---|---|---|
| `test_no_legacy_imports.py` | 저장소 `*.py`(docs/handoff/, archive 제외)를 AST로 파싱해 import·문자열에 `hyperframes`, `remotion`, `scene_builder`, `scene_io`, `render_io`, `audio_service`, `subtitle_align`이 없음 | 위반 0 | **통과** |
| `test_prompts_from_files.py` | `workers/*.py`에 `system_prompt: ClassVar[str] = "..."` 또는 200자 이상 삼중따옴표 상수 없음; `BaseLLMWorker` 하위 클래스마다 `prompt_name`이 있고 `prompts/{name}.md`가 존재 | 위반 0 | **통과** |
| `test_constitution.py` | `CLAUDE.md`에 "docs/handoff/15", "byte-equal", "C11"; `GOAL.md`에 "G7", "docs/handoff", G4-13~20; `HANDOFF.md`에 "docs/handoff/KICKOFF_PROMPT.md" | 문자열 존재 | **통과** |
| `test_single_config.py` | `workers/`, `orchestrator/`, `engine/`, `script/`, `audio/`에 `eleven_multilingual`, 해상도 튜플 `(854, 480)`/`(1920, 1080)`, `fps = 24/30`, `invoke_timeout_sec = 숫자`, 색 hex `#e8b860` 등 규칙 파일 값의 **리터럴 재정의** 없음(허용 목록: `orchestrator/config.py`, `rules/`, `engine/style.py`의 규칙 로더) | 위반 0 | **통과** |
| `test_prompt_schema_parity.py` | `prompts/*.md` 안의 ```yaml/```json 예시 블록을 추출해 **그 프롬프트를 쓰는 워커가 실제로 검증하는** Pydantic 모델로 파싱. script = `FullScript`(v2.3.0, D33 — Phase 6.8 ScriptWorker→Script 전환 시 `script.schema:Script`로 바꾼다), `Direction`·`QAVerdict`·`Facts`는 Phase 6.9 | 전부 통과 | script 통과(v2.3.0), 나머지는 6.9 에 추가 |
| `test_registry_complete.py` | `rules.registries.event_types` ∪ `panel_kinds` 각각에 대해 `engine/registry.py`에 모델·렌더러가 있고 `tests/fixtures/preview/{type}.yaml` 예제가 있음; 역으로 코드에만 있는 타입 없음 | 양방향 일치 | xfail(strict, Phase 2) |
| `test_provenance_e2e.py` | `projects/hormuz_korea`를 `--preview` 모드(전편 렌더 없이 25 앵커 프레임)로 돌려 `out/provenance.json`의 `features_used`가 기대값(카메라 이동 5, dip 4, 뱃지 9, 패널 5종, 미디어 clip2/photo2/cutout1/article2, label_lod true)과 일치하고 `drops == []` | 일치 | xfail(strict, Phase 6.8) |
| `test_no_silent_fallback.py` | (a) 미등재 이벤트 타입 → `RegistryError` (b) 권리 필드 없는 미디어 → `RightsError` (c) 손상 manifest → 오류(created 폴백 아님) (d) `main.py build-scene` → `LegacyRemovedError` | 예외 발생, 산출물 없음 | (d)만 Phase 0 통과 가능 → 파일은 하나로 두고 (a)(b)(c)는 xfail(strict, Phase 2/6.5/6.8) |

> [정정 D-0041: 실물 8, relation] `test_provenance_e2e` 행의 "뱃지 9"는 실물 **8**, 경로는 `--preview golden` → `prev/provenance.json`(stages 의 render·mix·mux = false 명시)이다. 정본은 테스트 파일.

## 부록 C. GOAL G3 개정안 초안 (D4 — 사용자 승인 대기, Phase 11 반영)

v2 MVP 합격 기준(초안 16개):
1. `python -m orchestrator.main command-center`가 새 상태 머신(`16` §2)으로 프로젝트를 CREATED→DONE까지 진행한다.
2. SCRIPT_APPROVAL·PREVIEW_APPROVAL 두 게이트에서 승인·반려(되돌림)가 동작하고 `approval_log.json`에 남는다.
3. `script.yaml`이 `Script` 스키마를 통과하고 린트(금지 문구·발음 기호·강조어·출처)를 통과한다. 장면 수·길이는 고정되지 않는다.
4. `plan.json`이 실제 음성 길이로 계산되고, 목소리(edge/ElevenLabs)를 바꿔도 `direction`을 수정하지 않는다.
5. `direction.yaml`이 레지스트리·스키마·예약 영역 검사를 통과한다.
6. `prev/sheet.jpg`와 `checks.json`(hard 0)이 생성되고 시각 검수 루프가 2회 이내에 끝난다.
7. `out/final.mp4`(트라이얼 480p 또는 최종 1080p), `final.srt`, `description.txt`(챕터·출처·크레딧)가 생성된다.
8. `out/provenance.json`의 `features_used`가 실제 사용 기능과 일치하고 `drops`가 비어 있다.
9. 화면 모서리에는 날짜 배지만 있고 도장·비네팅·브랜드·섹션 표기가 없다(결정적 검사).
10. 확대 장면에 행정구역·도시 라벨이 표시되고 라벨 겹침이 없다.
11. 모든 사용 자산(인물·휘장·국기·지도·지형·미디어·음악)이 권리 레지스트리에 있고 엔딩 카드·설명문에 크레딧이 나온다.
12. 미디어 비트 밀도(40~60초당 1)와 자료사진 표기·출처 줄이 검사에서 통과한다.
13. 오디오가 −14 LUFS(±1), 내레이션 중 음악 −14~−18dB이다.
14. 모든 JSON/YAML 산출물이 `schema_version`을 갖고 Pydantic으로 검증된다.
15. 관성 방지 테스트 8종이 전부 통과한다(xfail 0).
16. 실패 시 옛 스타일로 폴백하지 않고 해당 상태에 멈춰 사용자에게 보고한다.

## 부록 D. v3 함수 → 새 모듈 매핑 (Phase 2 분해 기준, 각 함수는 정확히 한 곳)

| v3 (render3.py 등) | 새 위치 |
|---|---|
| `S, E, SC, SC_END, at_word`(:14-21), `clamp01, smooth, ease_io, ease_out, ease_back, window`(:25-32) | `engine/timebase.py` |
| `ym, ymv`(:23-24), `View`(:292-319), `to_uv`(:120) | `engine/projection.py` |
| `CAM, cam, dip, build_camera`(:176-289) | `engine/camera.py` (+ `dip(t,lon,lat,w)` 인자형) |
| `hexc, C`(:33-37), `FONT`(:41-43), 크기·두께·알파 상수 전부 | `engine/style.py` (규칙 파일에서 로드) |
| `font, mixed_runs, text, tw, rrect, wrap`(:45-110) | `engine/typography.py` |
| `TIERS, BASE, GEO, BORD, ADM, PLC*, KO, SEAS`(:113-136), `surf_from_pil, scaled, PIL_IMG, _SC`(:142-165) | `engine/assets.py`(로더·캐시) — 프로젝트 `labels.yaml`이 `KO/SEAS` 공급 |
| `path_rings, draw_borders`(:322-347) | `engine/layers/borders.py` |
| `draw_labels`(:349), `RESERVED` | `engine/layers/labels.py` |
| `draw_country`(:398) | `engine/layers/areas.py` |
| `catmull, route_uv, glow_line, tanker, draw_route, draw_tanker_loop, draw_barrier`(:410-476) | `engine/layers/routes.py` |
| `draw_ships, draw_boom`(:478, :526) | `engine/layers/effects.py` |
| `icon, draw_marker`(:497-524) | `engine/layers/markers.py` |
| `media_frame, media_caption, media_tag, draw_photo, draw_clip, draw_article, draw_cutout`(:534-619) | `engine/layers/media.py` (article는 `engine/cards.py`와 슬롯 공유) |
| `flag_wave, badge_at, draw_badge`(:621-667) | `engine/layers/badges.py` |
| `draw_card`(:669) | `engine/cards.py` |
| `panel_title, edge_curve, P_refusal, P_statement, P_timeline, P_precedent, P_versus, draw_panel`(:699-829) | `engine/panels/{base,refusal,statement,timeline,precedent,versus}.py` |
| `cur_sentence, in_fullcard, draw_date`(:831-852) | `engine/hud.py` |
| `draw_subtitle`(:854) | `engine/subtitles.py` |
| `credit_sections, credits, draw_endcard, draw_fullcards`(:873-936) | `engine/fullcards.py` (크레딧 데이터는 `assets/rights`에서) |
| `build_vignette`(:938) | **이식하지 않음**(라운드 6 폐기) |
| `render_frame, __main__`(:953-997), `LAYER`, `MAPDRAW` | `engine/render.py` + `engine/registry.py` |
| plan3 `SCRIPT` | `projects/hormuz_korea/script.yaml` |
| plan3 `BANNED, lint()` | `script/lint.py` (규칙 파일에서 패턴 로드) |
| plan3 `edge_one, eleven_one`, 캐시 키, 트림·페이드 | `script/tts/{edge,elevenlabs,cache,trim}.py` |
| plan3 `build()` 후반(GAP/SCENE_GAP/TITLE/END/LEAD, t0/t1) | `script/timeline.py` |
| prep3 `fonts()` | `geo/prep_fonts.py` 또는 `tools/fetch_data.py fonts` |
| prep3 `polys, rings, geo()`(NE 로드·크림·admin1·places·meta) | `geo/prep_geometry.py` |
| prep3 `build_tier`(타일 모자이크·힐셰이드·팔레트·마스크·커버리지) | `geo/prep_tiers.py` |
| prep3 `portraits_emblems, commons_get, mono, normalize_portrait, flags()` | `tools/commons_fetch.py`, `tools/portrait_fallback.py`, `assets/flags` 빌더 |
| mix3 전체 | `audio/mix.py` |
| media3 전체 | `tools/media_fetch.py` + `assets/media/` |
| render3 상단 연출층(cam/ev 호출 약 60줄) | `projects/hormuz_korea/direction.py` (Phase 6.9에서 `direction.yaml`로 변환) |

> 이 표는 `grep '^def '` 실측(render3.py 61개 정의)과 `02` §5 목표 구조를 대조해 만들었다. Phase 2 착수 시 Opus는 이 표를 체크리스트로 쓰고, 표에 없는 함수를 발견하면 표를 먼저 갱신한다.
