<!--
tier: 2
last_synced_with: v0.43.4
ssot_for: [v2-phase-plan]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 13. Claude Code 구현 계획

목표: osint_generator를 **채팅 v3 파이프라인 기반의 지도 중심 롱폼 다큐 제작 시스템**으로 전면 개편한다. 첫 번째 합격선은 "v3 『호르무즈와 한국』을 새 모듈 구조로 동일하게 재현"이다.

---

## 0. 저장소 규칙 (기존 CLAUDE.md/HANDOFF에서 계승)
- 커밋 메시지 `vX.Y.Z: …` + `VERSION` 파일 일치. 한 커밋 = 한 의도.
- PR 생성 금지(사용자 규칙). 사용자가 병합.
- 이번 개편은 **MAJOR**: `v2.0.0`부터 시작.
- 서브에이전트 산출물은 육안 검수(프리뷰 컨택트 시트) 없이 통과시키지 않는다. 기준: "프로 다큐로 보이는가".

## 0.1 기준 브랜치 선택 (중요)
- 인물 라이브러리(`assets/library/`)와 공방은 **`collage` 브랜치에만** 있다(main에는 없음).
- 권장: `collage`에서 `overhaul/v2-map-engine` 분기 → 쇼츠·HyperFrames·Remotion을 `archive/*` 브랜치로 보존한 뒤 삭제 → 새 엔진 추가.
- 대안: main에서 분기 후 `collage`의 `assets/library/`, `workers/engraving_stylizer.py`, 스키마 변경분을 체리픽.

---

## Phase 0 — 관성 차단 (v2.0.0) ★ 가장 먼저
`15` 전체를 적용한다. 새 기능보다 **옛 관점이 되돌아올 통로를 먼저 막는다.**
1. `CLAUDE.md`/`GOAL.md` 개정: 영상 기준 조항을 이 문서 묶음 참조로 교체, "byte-equal 레거시 보존은 이번 개편에 적용하지 않음, 기준은 v3 골든" 명시, 필독 목록 최상단에 `15`.
2. 레거시 삭제: `scene_builder.py`, `hyperframes/`, `remotion/`, 섹션=장면 로직 → `archive/*` 브랜치 보존 후 main에서 삭제.
3. `rules/video_rules.yaml`(SSOT) 신설, 워커 `system_prompt` 상수를 템플릿 파일 로드로 교체.
4. 관성 방지 테스트 8종(`15` §5) 먼저 작성(처음엔 일부 실패가 정상 — 이후 Phase에서 통과시킴).
**합격 기준**: `test_no_legacy_imports`, `test_prompts_from_files`, `test_constitution`, `test_single_config` 통과.

## Phase 1 — 골든 재현 (v2.0.x)

**작업**
1. `docs/handoff/`에 이 문서 묶음 전체를 커밋.
2. `reference_code/v3_hormuz_korea/*.py`를 `legacy_v3/`로 복사해 **경로만 저장소 기준으로 수정**하고 그대로 실행한다.
3. 데이터 준비 스크립트로 Natural Earth, 지형 타일, flag-icons, 폰트를 받는다(`prep3.py` 로직).
4. `python legacy_v3/plan3.py` → `prep3.py` → `render3.py --preview` → 전체 렌더 → `mix3.py` → 먹싱.

**합격 기준**
- 4분 52초 ±1초, 854×480, 24fps 영상 생성.
- `11` §5의 22개 프리뷰 시각에서 채팅 결과와 육안상 동일(라벨·뱃지·패널·카드 위치).
- `prep` 로그에 `land-miss`가 몰디브 외 없음.
- 린트 통과, 음성 45문장 생성.

## Phase 2 — 모듈 분해와 계약 (v2.1.0)

**작업**: `02` §5 구조로 `render3.py`를 분해.
- `engine/timebase.py`(S/E/SC/SC_END/at_word, easing, window), `projection.py`(View, 티어), `camera.py`, `layers/*`, `panels/*`, `cards.py`, `hud.py`, `subtitles.py`, `fullcards.py`, `typography.py`, `style.py`, `render.py`.
- `projects/hormuz_korea/script.yaml`(원고) + `direction.py`(v3 direction layer를 그대로 옮김).
- Pydantic: `Script`, `Scene`, `Sentence`, `Plan`, `CamKey`, 이벤트 타입별 모델(`02` §2.4), `Tier`, `RightsRegistry`.
- CLI: `python -m script.plan`, `python -m engine.render`, `python -m audio.mix`, `python -m engine.mux`.

**합격 기준**
- Phase 1 결과와 프레임 비교(동일 시각 PNG의 평균 절대 차이 < 2/255, 폰트 렌더 차이 허용).
- 이벤트 스키마 검증 실패 시 렌더 전에 명확한 오류.
- `pytest`: timebase, projection 왕복(ym↔lat), 카메라 보간(로그 줌, cut), 강조 구간 분할.

## Phase 3 — 지오 일반화 (v2.2.0)

**작업**
- `geo/prep_geometry.py`: 작업 bbox 인자, 재귀 `polys()`, 크림 재분류 옵션, coarse/fine/admin1/places/meta 생성.
- `geo/prep_tiers.py`: `--tier NAME:ppd:z:lon0,lat0,lon1,lat1` 인자, 타일 범위 자동 계산·병렬 다운로드·캐시, v3 팔레트, 3단 피라미드, **커버리지 테스트**.
- 라벨 설정을 프로젝트별 YAML로(해역 목록, 행정구역 대상국, KO 관용명 오버라이드).

**합격 기준**
- 새 권역(예: 대만해협 lon 115~125, lat 20~28)을 명령 한 줄로 준비하고 프리뷰에서 육지/바다·라벨 정상.
- 커버리지 테스트: 작은 섬 국가(면적 임계 이하) 외 누락 시 실패.
- 프랑스 회귀 테스트: 유럽 bbox에서 FR 대표점이 육지.

## Phase 4 — 원고·음성 (v2.3.0)

**작업**
- `script/lint.py`: 금지 문구(`03` §2) + `LLM_ANTIPATTERNS.md` 병합, 발음 텍스트 숫자·기호 금지, 강조어 포함 검사, **출처 누락 경고**, 문장 길이(자막 2줄) 경고.
- `script/tts/edge.py`, `script/tts/elevenlabs.py`(with-timestamps, previous/next_text, voice_settings 0.65/0.8/0.1, 정렬 JSON 저장), 캐시 키에 목소리 id 포함.
- 트림 오프셋 기록(`trim_offset`) → `at_word()`가 정렬 데이터로 정확한 시각 계산(`03` §6.3), 없으면 비율 폴백.
- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md`에 TTS-AP-059~061 추가(`03` §5.4).
- 저장소 `tts_of()` 수정(개월, 소수 표기) — 번들 경로용.

**합격 기준**
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` 설정 시 사용자 커스텀 목소리로 v3 전편 재생성, 연출 수정 없이 싱크 유지.
- ask 패널의 "거절" 전환이 국가명 발음 시작 ±0.15초 안.
- 린트가 금지 문구 샘플 12개를 모두 잡고, 정상 v3 원고는 통과.

## Phase 5 — 뱃지·엔티티·권리 (v2.4.0)

**작업**
- `assets/entities.yaml`(`07` §6): 인물·기관·국가, 이름 별칭, 국기, 초상/휘장 경로, 기본 직함·강조색.
- `assets/emblems/registry.json`: 기관별 `{file, license, restrictions, decision, reason}`; 렌더러가 decision=flag_fallback이면 국기로.
- `tools/commons_fetch.py`: 검색→라이선스/제한 필터→표준 폭(960)/원본 다운로드→검증→레지스트리 기록.
- `tools/portrait_fallback.py`: rembg(u2net_human_seg)+`mono()`+`normalize_portrait()`. 기본 경로는 저장소 codex 공방 안내.
- 크레딧·설명문 자동 생성(`engine/mux.py`).

**합격 기준**
- 원고에 "이재명 대통령"이 나오면 엔티티 레지스트리에서 뱃지 구성이 자동 제안됨.
- 제한 태그 있는 휘장은 사람 승인 전 국기로 대체되고 사유가 기록됨.
- 엔딩 크레딧에 모든 사용 자산의 라이선스 표기.

## Phase 6 — 패널·카드 데이터화 (v2.5.0)

**작업**
- 관계 패널: `nodes`, `edges`, `state_changes=[(anchor, new_style)]` 데이터 주도, `08` §3 정돈 규칙 내장(순차, 1.0~1.3초, 동일 곡률).
- 연표 자동 층 배치(겹침 계산).
- 카드 영역을 RESERVED로 등록, 지도 뱃지 자동 회피(알려진 결함 해소).
- v2 번들 차트(dots, gantt, dual_line, fork, checklist)를 새 패널 모듈로 이식, `prov_tag` 공통화.

**합격 기준**: v3 review 장면에서 부산 뱃지가 가려지지 않음. 관계선 7개 초과 시 경고.

## Phase 6.5 — 사진·영상·컷아웃 (v2.5.5)
`14` 전체. `engine/layers/media.py`(photo, clip, cutout, article), `tools/media_fetch.py`(위키미디어/DVIDS 검색·라이선스 필터·구간 추출·썸네일 시트), `assets/media/media_registry.json`, 엔딩 카드·설명란 자동 크레딧 연동. 긴 클립은 ffmpeg 스트리밍.
**합격 기준**: v3의 사진 2·클립 2·컷아웃 1·기사 2 재현, 미디어 비트 밀도 린트(40~60초당 1개, 장면당 1개) 통과, 문장 `media` 필드 → 자동 배치, 자료사진 표기·출처 줄 누락 시 렌더 전 오류, 사상자 식별 구간 사용 금지 체크리스트 통과.

## Phase 6.8 — 오케스트레이터 통합 (v2.5.8)
`16` 전체: 새 상태 머신·역전이, `engine_service.py` 어댑터(StageResult), 두 승인 게이트 UI(Command Center), 모듈 삭제/병합/대체표 이행, provenance 기록.
**합격 기준**: Command Center에서 한 프로젝트를 CREATED→DONE까지 진행, 두 게이트에서 반려→되돌림 동작, `test_provenance_e2e` 통과.

## Phase 6.9 — AI 연출가·시각 검수·프롬프트 (v2.5.9)
`17` 전체: `direction.yaml` 스키마·검증기, 배치 슬롯 계산, 결정적 사전 검사(`checks.json`), 시각 검수 워커(이미지 입력), 수정 루프(≤2), 프롬프트 5종 템플릿.
**합격 기준**: 호르무즈 원고만 주고 연출을 자동 생성 → 결정적 검사 hard 0 → 프리뷰가 v3 수동 연출과 동등 이상(사용자 판정).

## Phase 6.95 — 소스 인테이크 (v2.5.95)
`18` 전체: 소스 레코드, 캡처 판독, 검증·교차확인, claims.json, 게시물 카드(`post`), 원고의 claim id 강제.
**합격 기준**: X 캡처 3건 + 기사 URL 2건으로 원고 초안까지 생성, 미확인 주장은 귀속 표현·카드 표기 확인.

## Phase 7 — 카메라 자동화 보조 (v2.6.0)

**작업**: `frame_points(points, reserve)` 자동 프레이밍, move/dip 자동 선택(`05` §7), 숏 머무름 린트(6초 미만 경고), `dip(t, lon, lat, w)` 인자형.
**합격 기준**: v3 direction을 자동 제안값으로 바꿔도 프리뷰가 동등하거나 나음(사용자 검수).

## Phase 8 — 오디오 (v2.7.0)
BGM 레지스트리, 장면별 `music_intensity`, 곡 교체 교차 페이드, 오디오 QA(내레이션 대비 음악 −14~−18dB, 최종 −14 LUFS).

## Phase 9 — 번들 어댑터 (v2.8.0)
`bundle/` 패키지(`12` §7). 번들 → `script.yaml` 초안(장면 묶음 제안, 린트 결과 주석) + `direction.py` 초안. 테스트 코퍼스: `samples/*.bundle.json`, 백필 63건. agents_reviewer 스키마 개선안 문서(`12` §6)를 사용자에게 제출.
**합격 기준**: 랫클리프 번들로 12막이 아닌 자유 구성 초안 생성, 금지 문구 재작성 표시, 추정 차트 태그.

## Phase 10 — 해상도·성능 (v2.9.0)
`style.px()` 스케일(k = H/480), 1080p 프리뷰 검수(글자 최소 2% 규칙), `multiprocessing` 청크 병렬 렌더 + concat.
**합격 기준**: 1080p 전편 렌더 성공, 480p 대비 레이아웃 동일 비율.

## Phase 11 — 문서·정리 (v3.0.0)
`docs/07_VIDEO_STYLE_GUIDE.md`, `08_AUDIO_AND_TTS_SPEC.md`, `09_MAP_AND_GEO_SPEC.md`를 이 문서 묶음 기준으로 재작성. `GOAL.md` G3 합격 기준(34개)을 새 파이프라인에 맞게 개정(사용자 승인 필요). 폐기 대상 삭제 확인.

---

## 범위 밖 (사용자 결정, 라운드 8)
- **텔레그램 봇 인테이크, 유튜브 자동 업로드**는 이번 개편 범위에서 제외. 엔진·오케스트레이터 통합(Phase 0~10)이 안정된 뒤 별도 계획으로 다룬다.
- 그때의 권장 원칙(기록용): 자동 공개 금지, 원고·프리뷰 두 번의 승인 후 **비공개 업로드**, X 소스는 스크래핑 대신 사용자 전달(텍스트·캡처), 유튜브 API 쿼터·OAuth, 대량 반복 콘텐츠 수익화 정책 유의.

## 테스트 전략 요약
| 층 | 테스트 |
|---|---|
| 순수 함수 | ym 왕복, easing, window, 강조 분할, 린트 규칙, 타일 범위 계산 |
| 지오 | 재귀 평탄화(GeometryCollection 중첩 픽스처), 커버리지, 크림 재분류 |
| 렌더 | 골든 프레임 비교(시각 목록 고정), 이벤트 스키마 |
| 오디오 | 길이 일치, 피크 ≤ 0.97, loudnorm 후 −14±1 LUFS |
| 권리 | 모든 사용 자산이 레지스트리에 있음, 제한 태그 처리 |

---

## Claude Code 시작 프롬프트 (사용자가 붙여 넣을 문안)

> **정본은 `KICKOFF_PROMPT.md`**(취지·목표·원칙·범위·첫 작업 포함). 아래는 요약본이다.

```
docs/handoff/00_INDEX.md의 읽는 순서(00→01→15→02→16→13)를 따르라. 15(관성 방지 원칙)는 모든 작업의 전제다 — 새 기능을 오케스트레이터에 '주입'하지 말고 옛 경로를 '교체·삭제'하라.
reference_code/v3_hormuz_korea는 사용자가 합격 판정한 동작 프로토타입이다. 수치(타이밍·색·크기)를 근거 없이 바꾸지 마라.
Phase 0(관성 차단)부터 시작하고, 이어서 Phase 1(골든 재현)으로 간다. 각 Phase 끝에 프리뷰 컨택트 시트를 만들어 나에게 보여 주고, 내가 승인하면 다음 Phase로 간다.
커밋 규칙: vX.Y.Z prefix, VERSION 일치, 한 커밋 한 의도, PR 생성 금지. 이번 개편은 v2.0.0부터.
결정이 필요한 사항(휘장 사용, 저장소 기준 개정, agents_reviewer 스키마 변경)은 추측하지 말고 나에게 물어라.
```
