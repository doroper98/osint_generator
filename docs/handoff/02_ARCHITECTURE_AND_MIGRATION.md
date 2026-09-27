<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-architecture, migration-verdicts]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 02. 아키텍처, 데이터 계약, 저장소 이관 판정

---

## 1. 새 파이프라인 전체 흐름

```
[주제/리서치] ──► [원고 plan] ──► [자산 prep] ──► [연출 direction] ──► [렌더 render] ──► [오디오 mix] ──► [먹싱 mux] ──► 산출물
   (사람+AI)      문장·날짜·강조     지형 티어·지오       카메라·이벤트         프레임 루프        내레이션·음악        ffmpeg        mp4/srt/설명/권리
                  발음텍스트·TTS     라벨데이터·인물      (문장 앵커)           cairo+PIL          효과음·더킹          loudnorm
                  타임라인           국기·휘장·폰트
```

| 단계 | v3 파일 | 입력 | 출력 | 결정성 |
|---|---|---|---|---|
| 원고 | `plan3.py` | `SCRIPT` 리스트(사람이 작성) | `plan.json`, `tts/*.mp3|npy` | 음성 캐시 해시로 결정적 |
| 자산 | `prep3.py` | Natural Earth, 지형 타일, 위키미디어, 저장소 라이브러리, flag-icons | `assets/base_*.png`, `geo3.pkl`, `tiers.pkl`, `portraits/`, `flags/`, `emblems/`, `rights_registry.json` | 입력 고정 시 결정적 |
| 연출 | `render3.py` 상단 "direction layer" | `plan.json` | 메모리 내 `CAM`, `EV` 리스트 | 결정적 |
| 렌더 | `render3.py` 하단 | 연출 + 자산 | `partX.mp4` (무음) | 결정적(난수 시드 고정) |
| 오디오 | `mix3.py` | `plan.json`, 음성 npy, BGM | `mix.f32` (44.1kHz 스테레오 float32) | 결정적(시드 3) |
| 먹싱 | ffmpeg | 영상 + mix | 최종 mp4 (loudnorm -14 LUFS) | — |

**핵심 설계 결정 세 가지**
1. **문장 앵커**: 모든 연출 시각은 `S(sid, off)`, `E(sid, off)`, `SC(scene)`, `at_word(sid, word)`로만 지정한다. 절대 초를 하드코딩하지 않는다. 음성·목소리·원고 수정이 연출을 깨지 않는다.
2. **지도 = 연속 세계 + 카메라**: 장면은 카메라 키프레임으로 표현된다. 지도를 장면마다 새로 만들지 않는다.
3. **레이어 순서 고정**: 베이스 래스터 → 국경/행정구역 → 지도 오버레이(국가강조, 선박, 경로, 봉쇄선, 폭발, 컷아웃, 마커, 뱃지) → 라벨(LOD, 충돌회피) → 하부 암전 → 패널 → 사진·영상 → 카드 → 날짜 → 전면카드(타이틀/엔딩) → 자막 → 상부 암전 → 전체 페이드. (비네트 없음 — 라운드 6)

---

## 2. 데이터 계약 (Claude Code는 Pydantic 모델로 옮길 것)

### 2.1 원고 입력 `SCRIPT` (v3: 파이썬 리스트 → 권장: YAML)

```yaml
title: 호르무즈와 한국
subtitle: 한국은 왜 파병하지 않았나
date: "2026.09.26"            # 타이틀 카드용 제작 기준일
scenes:
  - id: open
    sentences:
      - date: "2026.09.18"    # 우상단 날짜 배지 (YYYY, YYYY.MM, YYYY.MM.DD 허용)
        text: "9월 18일, 이재명 대통령이 기자회견을 열었습니다."           # 자막
        tts:  "구월 십팔일, 이재명 대통령이 기자회견을 열었습니다."         # 발음 (없으면 text 사용)
        emphasis: []          # 자막 금색 강조어 (text의 부분문자열이어야 함)
        sources: ["Reuters 2026-09-18", "ZeroHedge/AFP"]   # 권장 추가 필드: 사실 출처
        media: {kind: clip, asset: niovi, at: "닫았습니다", dur: 5.0}   # 선택: 미디어 비트(14 §10)
```

### 2.2 `plan.json` (plan 단계 출력) — 실제 파일: `reference_code/v3_hormuz_korea/plan.json`

```jsonc
{
  "sentences": [{
    "sid": "war_2",               // "{scene}_{index}"
    "scene": "war",
    "date": "2026.03.02",
    "text": "이란은 곧바로 호르무즈 해협을 닫았습니다.",
    "tts": "이란은 곧바로 호르무즈 해협을 닫았습니다.",
    "segments": [["이란은 곧바로 호르무즈 ", 0], ["해협을 닫았습니다", 1], [".", 0]],  // 1=강조
    "mp3": ".../tts/war_2_<sha1[:10]>.mp3",
    "npy": ".../tts/war_2_<sha1[:10]>.npy",   // 무음 트림된 44.1k mono float32
    "dur": 2.93, "t0": 58.41, "t1": 61.34
  }],
  "cards": [{"kind": "title", "t0": 20.33, "t1": 25.93}, {"kind": "end", "t0": 281.0, "t1": 292.0}],
  "scene_start": {"open": 1.2, "route": 26.3, "war": 49.2, "...": 0},
  "total": 292.44,
  "voice": "edge-tts ko-KR-InJoonNeural",   // 또는 "elevenlabs"
  "title": "호르무즈와 한국", "subtitle": "한국은 왜 파병하지 않았나", "date": "2026.09.26"
}
```

### 2.3 카메라 키프레임

```python
cam(t, lon, lat, w, dur=3.0, mode='move')   # 내부 저장: (t, lon, ym(lat), w, dur, mode)
# w = 화면 가로 폭(경도 도). 854px / w = 필요 ppd
# mode: 'move'(ease-in-out 3차, 로그 줌) | 'cut'(즉시 이동; dip과 함께 사용)
```

### 2.4 이벤트 (모두 `t0`, `t1` 필수, 시각은 문장 앵커로 계산)

| type | 필드 | 설명 |
|---|---|---|
| `marker` | lon, lat, label, sub, side(right/left/top/bottom), hl(bool), icon(dot/boom) | 펄스 링 + 점 + 라벨. RESERVED 등록 |
| `route` | pts[(lon,lat)], grow(초), col, ship(bool), dashed, glow_only, label | Catmull-Rom 경로 점진 드로잉, 선두 유조선 |
| `tanker_loop` | pts | 경로 위 유조선 3척 순환(26초 주기) |
| `barrier` | p0, p1 | 붉은 봉쇄선 + "봉쇄" |
| `ships` | — | 걸프 내 선박 150개 입자 |
| `boom` | lon, lat | 확산 링 3개(폭발/타격) |
| `country` | codes[ISO2], col, a | 국가 채움 + 3중 글로우 테두리 |
| `badge` | lon, lat, kind(person/flag/emblem), pid/flag/img, R, label, role, accent, side | 원형 뱃지 |
| `card` | tag, lines[], bigs[(big,cap)], accent, src, quote(bool), y | 우상단 슬라이드 카드 |
| `panel` | kind(refusal/statement/timeline/precedent/versus/…) | 지도 위 정보 화면 |
| `dip` | under(bool) | 1초 암전(중간에 cut). under=True면 카드 아래 |
| `photo` | img, x, y, w, caption, credit, mid | 사진 카드(켄 번스, 캡션·출처 바) — `14` |
| `clip` | clip, x, y, w, caption, credit, mid | 영상 클립(프레임 배열/스트리밍) — `14` |
| `cutout` | img, lon, lat, w, label, sub, mid | 지도 위 무기·장비 컷아웃 — `14` |
| `article` | pub, date, headline, hl, sub, note | 기사 클리핑 카드(우상단 카드 자리, 헤드라인 번역·형광펜) — `14` §9 |
| `post` | source_id, account_name, handle, account_class, posted_at, text_ko, text_original?, hl?, verification | X 게시물 카드(자체 조판, 로고 없음, 일반인 계정 가림) — `18` §5 · **명세만 있고 레퍼런스 구현 없음** |

v1/v2 전용 타입(필요 시 이식): `occupied`(DeepState 점령지), `arc`(2점 베지어+비행기), `channel`(왕복 점 흐름), `shield`(반경 원+일시정지), `tl`(타임랩스 카운터), `particles`, `flash`, `dots`, `movers`, `line`, `arrow`(성장/철수 화살표).

### 2.5 자산 계약

- `tiers.pkl`: `{name: {lon0, lon1, lat0, lat1, ppd, tiles, z, levels:[ppd, ppd/2, ppd/4]}}`
- `base_{name}_{ppd}.png`: RGB, 메르카토르 도 단위 격자. 픽셀 (x,y) ↔ lon = lon0 + x/ppd, v = ym(lat1) − y/ppd.
- `geo3.pkl`:
  - `coarse`/`fine`: `{ISO2|ADMIN: [ndarray(N,2) lon/lat ring, ...]}` (단순화 0.03° / 0.005°)
  - `meta`: `{key: {name, ko, lx, ly, minlab, rank}}` (NE LABEL_X/Y, LABELRANK)
  - `admin1`: `{ISO2: [{name(ko), lx, ly, rings}]}`
  - `places`: `[{ko, lon, lat, rank(SCALERANK), cap(bool), iso, pop}]`
- `rights_registry.json`: `{people: {pid: {src, license, artist, url, title?}}, emblems: {id: {license, url, title, restrictions}}}`

---

## 3. 기존 저장소 분석 요약 (collage 브랜치 v1.2.1, 2026-08-15 기준)

현황:
- main은 2026-07-12(v0.43.4)에서 멈춤. 최신 작업은 `collage` 브랜치(쇼츠 콜라주, v1.2.1). 롱폼 briefing은 v0.43.6부터 동결.
- 롱폼 렌더러: HyperFrames(HTML+GSAP, 헤드리스 크롬). `hyperframes/scripts/bundle_to_video.py`(약 1,700줄)가 번들을 장면 데이터로 바꾸고 `auto.html`을 생성.
- 지도: `hyperframes/briefing/assets/maps/{neasia,mideast}_map.js` — world-atlas 50m을 권역별로 **미리 투영한 SVG 경로**. 고정 viewBox, 카메라 없음.
- 글자: `scene_kit.js`/`auto.html`에서 11~17px 규칙 21개(1920×1080 캔버스). 휴대폰에서 판독 불가.
- 장점: 거버넌스 문서, 검수 게이트, 권리 기록(사진·BGM·국기), 인물 라이브러리 24인(codex imagegen 가공, 흑백 고대비 RGBA 컷아웃), TTS 안티패턴 문서, TTS 백엔드(ElevenLabs 포함), 발음 정규화 `tts_of`, 근거 검사 `sentence_grounded`, 차트 정규화기 15종 이상.

---

## 4. 계승 / 개조 / 폐기 판정표

### 4.1 그대로 계승 (KEEP)

| 경로 | 이유 | 비고 |
|---|---|---|
| `GOAL.md` G4(검증·미검증 라벨·권리·TTS QA), `CLAUDE.md` C9(권리) | 사용자 불만 대상이 아님. 새 파이프라인도 이 원칙 위에 선다 | G0/C0 "영상미" 조항은 유지하되 구체 기준은 이 문서 묶음으로 교체 |
| `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md` | 사용자가 명시적으로 따르라고 함 | "개월은 한자어 수사" 규칙 추가(`03` §5.4) |
| `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` | 원고 품질 | 금지 문구 목록(`03` §2) 병합 |
| `assets/library/people/*.png`, `library_manifest.json` | 뱃지 인물 소스로 직접 사용(v2·v3 검증) | `normalize_portrait()`로 머리-어깨 크롭 |
| `assets/library/workshop/` (codex 공방, `references/RIGHTS.md`, `photo_manifest.json`) | 인물 확장 경로. 권리 기록 정본 | 새 인물은 이 공방으로 가공해 질감 통일 |
| `hyperframes/briefing/assets/audio/bgm/` + `RIGHTS.md` | CC BY 4.0 곡(Zabriskie), 출처 표기 의무 기록 | 새 위치 `assets/audio/bgm/`로 이동 |
| `samples/*.bundle.json`, `json/`(63건 백필, `data/agents-reviewer-v8-bundle-backfill` 브랜치) | 번들 어댑터 테스트 코퍼스 | — |
| `schemas/models.py` (Pydantic) | 계약 중심 원칙 유지 | 새 모델(Script, Plan, Event, Tier, Rights) 추가 |
| `workers/tts_backends.py` | 백엔드 추상화 구조 | ElevenLabs를 with-timestamps로 업그레이드(`03` §6) |
| orchestrator/Command Center/프로젝트 매니저/검수 게이트 | 사용자 명령 → `claude -p` 워커 구조는 유지 | 모듈별 운명·새 상태 머신·게이트는 **`16`**, 통합 원칙은 **`15`** |

### 4.2 개조해서 사용 (MODIFY)

| 경로 | 개조 내용 |
|---|---|
| `hyperframes/scripts/bundle_to_video.py` | HTML 생성부 제거. 텍스트 함수(`tts_of`, `to_polite`, `josa`, `native_count`, `em_segments_line`, `sentence_grounded`, `build_corpus`)와 차트 정규화기(`norm_gantt`, `norm_sankey`, `norm_waterfall`, `norm_stacked`, `norm_scatter`, `norm_heatmap`, `build_candle`, `build_bar_panels`, `build_slopes`, `build_tables`, `norm_network`, `build_markets`, `build_versus`, `build_signals`, `norm_map`)를 `bundle/` 패키지로 분리. `tts_of`의 개월 버그 수정. `norm_network`가 `stakeholder_map`을 처리하도록 확장 |
| `hyperframes/scripts/build_narration.py` / `cuesync.json` | "실제 음성 길이를 재서 누적 시점 계산" 원리는 plan 단계와 동일 → plan 단계로 흡수 |
| `workers/engraving_stylizer.py` | `stylize_mono`, `background_mask` 등은 인물 흑백화 폴백으로 유지 가능. 1순위는 codex 공방 |
| `hyperframes/briefing/assets/flags/*.svg` | 9종뿐. flag-icons(MIT) 전체로 교체/보충 |
| `docs/07_VIDEO_STYLE_GUIDE.md` | 이 문서 묶음(`05`, `08`, `09`) 기준으로 전면 재작성 |
| `docs/09_MAP_AND_GEO_SPEC.md` | `04`로 교체 |
| `docs/08_AUDIO_AND_TTS_SPEC.md` | `03`, `10`으로 교체 |

### 4.3 폐기/보관 (ARCHIVE — `archive/hyperframes-briefing` 브랜치로 이동 후 main에서 삭제)

| 경로 | 폐기 이유 |
|---|---|
| `hyperframes/briefing/assets/scene_kit.js`, `auto_builder.js`, `themes.js`, `auto.html`, `index.html`, `preview_charts.html` | 섹션=장면 1:1 슬라이드 문법, 소형 글자, 평면 배경. 사용자 불만의 직접 대상 |
| `hyperframes/briefing/assets/maps/*.js`, `mideast_map.js` | 미리 투영한 권역 SVG. 카메라·지형·LOD 불가 |
| `hyperframes/demo/`, `hyperframes/shorts/`(collage) | 쇼츠 트랙 폐기(사용자 결정) |
| `remotion/` | 사용하지 않는 이전 렌더러 |
| `docs/17_COLLAGE_DESIGN_SHEET.md`, `docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md`, `docs/PROFESSIONAL_REBUILD_PLAN.md` | 쇼츠/이전 재빌드 계획. 이력으로만 보존 |
| HUD 요소: "◆ OSINT BRIEFING", 섹션 번호, 섹션 제목 | 사용자 명시 폐기(지적 3) |
| 12막/섹션 고정 구성 로직 | 사용자 명시 폐기(지적 4) |
| 도장(stamp) 컴포넌트 | 사용자 명시 폐기(지적 11) |

**HyperFrames를 버리는 이유(요약)**: (1) 지형 래스터 위 카메라 이동·줌 LOD를 DOM으로 다루기 무겁다, (2) 기존 코드 자산 대부분이 폐기 대상 문법에 묶여 있다, (3) cairo 엔진이 이미 사용자 합격 판정을 받았고 480p 1 vCPU에서 초당 21~33프레임이 나온다. 타이포 품질은 cairo+fontconfig로 르포 폰트를 그대로 쓸 수 있어 손실이 없다.

---

## 5. 목표 디렉터리 구조 (제안)

```
osint_generator/
├─ engine/                       # 새 렌더 엔진 (v3 render3.py 분해)
│  ├─ __init__.py
│  ├─ timebase.py                # S/E/SC/SC_END/at_word, easing, window
│  ├─ projection.py              # ym/ymv, View(카메라 → 화면 변환, 티어 선택/블렌딩)
│  ├─ camera.py                  # 키프레임, build_camera, dip
│  ├─ layers/
│  │  ├─ base.py                 # 티어 크롭/리사이즈
│  │  ├─ borders.py              # 국경·행정구역
│  │  ├─ labels.py               # 해역·국가·도·도시 LOD + 충돌
│  │  ├─ markers.py routes.py areas.py effects.py badges.py
│  ├─ panels/                    # refusal.py statement.py timeline.py precedent.py versus.py dots.py gantt.py dual_line.py fork.py checklist.py network.py
│  ├─ cards.py hud.py subtitles.py fullcards.py
│  ├─ typography.py              # FONT, text(), tw(), wrap(), rrect()
│  ├─ style.py                   # 색 토큰, 크기 스케일(해상도 독립)
│  └─ render.py                  # 프레임 루프, ffmpeg 파이프, 청크/병렬, 프리뷰
├─ geo/
│  ├─ prep_tiers.py              # 지형 타일 다운로드·모자이크·힐셰이드·티어 피라미드
│  ├─ prep_geometry.py           # NE 국가/행정구역/도시, 재귀 평탄화, 커버리지 검사
│  └─ cache/                     # tiers.pkl, base_*.png, geo.pkl (gitignore)
├─ script/
│  ├─ schema.py                  # Script/Scene/Sentence Pydantic
│  ├─ lint.py                    # 금지 문구, 발음 기호, 강조어, 출처 누락
│  ├─ tts/                       # edge.py elevenlabs.py (with-timestamps) cache.py trim.py
│  └─ timeline.py                # t0/t1, 장면 간격, 타이틀/엔딩 카드
├─ audio/mix.py                  # 베드·더킹·효과음·페이드·라우드니스
├─ assets/
│  ├─ media/                     # 사진·영상·컷아웃 원본/가공본 + media_registry.json (14)
│  ├─ library/                   # (기존) 인물 라이브러리·공방
│  ├─ flags/ emblems/ fonts/ audio/bgm/
│  └─ rights/registry.json
├─ bundle/                       # agents_reviewer 번들 어댑터 (bundle_to_video.py에서 분리)
├─ projects/<slug>/
│  ├─ script.yaml                # 원고
│  ├─ direction.py               # 연출(카메라·이벤트) — v3 direction layer와 동일 형식
│  ├─ plan.json  tts/  out/
└─ docs/handoff/                 # 이 문서 묶음
```

### 5.1 CLI 제안

```
python -m script.plan   projects/hormuz_korea        # 린트 → TTS → plan.json
python -m geo.prep      --bbox 20,-20,150,60 --tiers W:24:z5,G:96:z7:46,20.5,62,32.5,K:96:z7:122.5,32.3,131.8,39.8
python -m engine.render projects/hormuz_korea --preview auto      # 장면별 자동 프리뷰 컨택트 시트
python -m engine.render projects/hormuz_korea --jobs 4            # 청크 병렬 렌더 + concat
python -m audio.mix     projects/hormuz_korea
python -m engine.mux    projects/hormuz_korea                     # loudnorm, srt, 설명문, 크레딧
```
