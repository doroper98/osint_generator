<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-render-pipeline, v2-qa-checklist]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 11. 렌더 파이프라인 · QA · 성능

참조 코드: `v3/render3.py` (`render_frame`, `__main__`)

---

## 0. 한 편을 만드는 실제 순서 (채팅에서 v3를 만든 런북)

| # | 단계 | 한 일 | 산출물 | 검수 |
|---|---|---|---|---|
| 1 | 주제·리서치 | 웹 검색으로 최신 사실 확인(최근 사안은 반드시), 사실마다 매체·날짜 | 사실 목록 | 교차 확인, 논쟁 사안 양측 |
| 2 | 원고 | 장면 자유 구성, 문장 = 주장 1개, 자막/발음 분리, 강조어, 날짜 | `plan3.py SCRIPT` | 린트(금지 문구·발음 기호·강조어) |
| 3 | 음성·타임라인 | TTS → 무음 트림 → 문장 t0/t1, 장면 간격, 타이틀/엔딩 | `plan.json`, `tts/` | 총 길이 확인 |
| 4 | 자산 | 폰트 설치, 지오메트리(재귀 평탄화), 지형 티어 3개, 인물(라이브러리+위키미디어+rembg), 휘장, 국기 | `assets/` | 커버리지 검사, 인물·국기 시트 육안 확인 |
| 5 | 미디어 | 후보 검색(라이선스 필터) → 영상 12장 썸네일 시트 → 구간·사진 선택 → 가공 | `media/`, 레지스트리 | 관련성 없는 자료 탈락(유조선 사진 사례) |
| 6 | 연출 | 장면별 숏(카메라)·이벤트를 문장 앵커로 작성 | `render3.py` 상단 연출층 | — |
| 7 | 프리뷰 | 장면당 1~3컷, 약 22컷 컨택트 시트 | `prev/sheet.jpg` | 가림·잘림·글리프·밀도·색 — 문제 있으면 6으로 |
| 8 | 전환 확인 | 타이틀·암전 구간 0.3~1초 간격 연속 8컷 | `prev/title_check.jpg` | 타이틀 중복 같은 전환 버그 |
| 9 | 전체 렌더 | 청크 렌더 → concat | `video_full.mp4` | — |
| 10 | 오디오 | 내레이션 배치·더킹·BGM 강도·효과음 | `mix.f32` | 음악이 들리는지 |
| 11 | 먹싱·전달 | loudnorm −14 LUFS, SRT, 설명문(챕터·출처) | 최종 mp4 | 최종본에서 6컷 재확인 |
| 12 | 피드백 반영 | 사용자 지적 → 원인 진단 → 해당 단계부터 재실행 | — | `01`에 원문과 해결 기록 |

자동화(`16`, `17`)는 이 표의 6~8단계를 AI 연출가와 시각 검수 루프로 바꾸는 것이다. 7~8단계를 건너뛰면 품질이 무너진다.

## 1. 프레임 루프 (`render_frame(i)`)

```python
t = i / FPS; view = View(i); RESERVED.clear()
im  = view.base()                                          # PIL RGB 854×480 (티어 크롭·블렌딩)
buf = bytearray(im.tobytes('raw', 'BGRX'))
surf = cairo.ImageSurface.create_for_data(buf, FORMAT_RGB24, W, H, W*4)
ctx = cairo.Context(surf)
act = [e for e in EV if e.t0 − 0.05 ≤ t ≤ e.t1 + 0.05]     # 활성 이벤트
panel_a = max(패널 알파들, 0)
draw_borders(ctx, view)                                    # 국경·행정구역
for L in ['country','ships','route','tanker_loop','barrier','boom','marker','badge']: 해당 이벤트 그림
if panel_a < 0.99: draw_labels(ctx, view, t, 1 − panel_a)  # LOD 라벨(충돌 회피)
# (비네트 없음 — 라운드 6)
dip(under=True) → panel → photo/clip → card → draw_date → draw_fullcards → draw_subtitle → dip(under=False) → 전체 페이드
surf.flush(); return surf, buf                             # buf를 그대로 ffmpeg stdin에
```

## 2. 인코딩
```bash
ffmpeg -y -v error -f rawvideo -pix_fmt bgr0 -s 854x480 -r 24 -i - \
       -c:v libx264 -preset faster -crf 19 -pix_fmt yuv420p -g 48 out.mp4
```
- cairo RGB24는 리틀엔디언에서 BGRX 바이트 순 → `-pix_fmt bgr0`.
- `-g 48`: 2초 GOP. 청크 경계를 GOP에 맞출 때 유리.

## 3. 청크 렌더와 이어 붙이기

`python render3.py START END out.mp4` 로 프레임 구간 렌더. 카메라는 전 구간을 미리 계산하므로 청크마다 결과가 동일하다(결정적).

```bash
printf "file 'partA.mp4'\nfile 'partB.mp4'\n" > parts.txt
ffmpeg -f concat -safe 0 -i parts.txt -c copy video_full.mp4
```

### 3.1 일부 구간만 고칠 때 (v3에서 두 번 사용)
- 접두부 재사용: `ffmpeg -i partA.mp4 -frames:v 2600 -c:v libx264 … partA0.mp4` (앞 2600프레임만 재인코딩, 약 16초) → 2600~ 구간만 새로 렌더 → concat.
- 앞부분 수정(타이틀 중복 수정): 0~1200 새로 렌더 → 기존 전체 영상에서 1200~ 잘라 concat 필터로 재인코딩:
```bash
ffmpeg -i fixA.mp4 -i video_full.mp4 -filter_complex \
  "[1:v]trim=start_frame=1200,setpts=PTS-STARTPTS[b];[0:v][b]concat=n=2:v=1:a=0[v]" -map "[v]" -c:v libx264 … video_full2.mp4
```
오디오는 영상과 독립(mix.f32)이라 영상만 고치면 먹싱만 다시 하면 된다. 원고가 바뀌면 plan → mix → render 전부 다시.

### 3.2 샌드박스 전용 사정 (로컬에서는 불필요할 수 있음)
- 채팅 샌드박스는 도구 호출 1회가 약 5분을 넘기면 위험하고, **호출이 끝나면 백그라운드 프로세스가 종료**되었다(nohup 렌더가 1,200프레임에서 죽음). 그래서 3,000프레임 내외로 청크를 나눠 전경에서 렌더했다.
- 로컬 Claude Code에서는 `multiprocessing`으로 청크를 병렬 렌더하고 concat하면 코어 수만큼 빨라진다.

## 4. 성능 (1 vCPU, 480p)
| 버전 | 속도 | 비고 |
|---|---|---|
| v1 | 31~33 fps | 단일 티어, 오버레이 적음 |
| v2 | 약 21 fps | 세계 티어 + 뱃지 + 패널 |
| v3 | 약 21.5 fps | 3티어 블렌딩 + 라벨 LOD(도시 3,013개 후보 numpy 필터) |
프리뷰 22프레임: 5~7초(로딩 포함). 메모리: 티어 이미지 합계 수백 MB 이하.

최적화 포인트(이미 적용): 스케일된 이미지 캐시(`scaled`), 링 bbox 컬링·1px 미만 생략, 도시 후보 numpy 벡터 필터, 선박 좌표 1회 생성, 영상 클립 프레임 mmap.
1080p 예상: 픽셀 5.06배 → 단일 코어 4~6 fps 수준 → 병렬 청크 필수.

## 5. 프리뷰 검수 워크플로 (필수)

1. `python render3.py --preview t1,t2,...` → `prev/p_{t}.png`
2. 장면마다 1~3컷(카메라 도착 후, 패널 절정, 카드 표시 중) 약 22컷 선택. v3 선택식:
```python
ts = [S('open_1')+2, title.t0+2, S('route_0')+2.5, S('route_2')+2, S('route_3')+3.5, S('war_1')+2, S('war_3')+3,
      S('ask_1')+4, S('ask_2')+2, S('ask_5')+1.5, S('timeline_2')+2, S('timeline_4')+4, S('cost_1')+1, S('review_0')+5,
      S('review_2')+2, S('past_3')+5, S('debate_1')+2.5, S('debate_4')+2, S('decision_0')+3, S('now_0')+3, S('now_3')+4, total−5]
```
3. 427×240으로 줄여 4열 컨택트 시트 → 육안 검수 → 수정 → 전체 렌더.
4. 최종 mp4에서 6컷 추출해 재확인(`ffmpeg -ss t -frames:v 1`).
5. 전환 구간(타이틀·암전)은 0.3~1초 간격 연속 8컷으로 따로 확인(타이틀 중복 버그는 이 방식으로 검증).

## 6. QA 체크리스트

### 6.1 원고
- [ ] 금지 문구 린트 통과
- [ ] 발음 텍스트에 숫자·기호 없음
- [ ] 모든 수치·주장에 출처, 자체 발표는 귀속 동사
- [ ] 논쟁 사안 양쪽 논거·출처
- [ ] 문장당 자막 2줄 이하

### 6.2 화면
- [ ] 모서리에는 날짜만, 날짜가 문장 사건일과 일치
- [ ] 도장 없음
- [ ] 장면당 카메라 이동 1회, 숏 6초 이상, 암전 90초당 1회 이하
- [ ] 뱃지·마커가 화면 가장자리·카드·자막에 가리지 않음
- [ ] 확대 장면에 행정구역·도시 라벨이 보임, 라벨 겹침 없음
- [ ] 육지/바다 색 구분(커버리지 검사 통과, 누락은 작은 섬만)
- [ ] 관계선이 하나씩, 단어에 맞춰 상태 변화
- [ ] 전면 카드 위에 암전이 겹치지 않음
- [ ] 폰트 글리프 깨짐 없음(Gmarket 공백, Mono 한글)

### 6.2.1 미디어
- [ ] 사진·영상이 해당 문장 대상과 일치, 자료사진은 연월 표기
- [ ] 캡션·출처 줄 표시, 사상자 식별 장면 없음, AI 생성 사실 이미지 없음
- [ ] 장면당 미디어 1개 이하, 카드·자막·날짜 가림 없음
- [ ] 러닝타임 40~60초당 미디어 1개(미디어 비트), 형태가 연속 반복되지 않음
- [ ] 기사 클리핑: 매체·날짜가 원고 출처와 일치, 헤드라인은 번역/요지 표기, 로고 없음

### 6.3 권리
- [ ] 인물 사진 권리 레지스트리 기록, 제한 태그 확인
- [ ] 휘장 decision 기록(use/flag_fallback/user_decision)
- [ ] 엔딩 크레딧·설명란에 CC BY 표기

### 6.4 오디오
- [ ] 음악이 내레이션 중에도 들림(v3 이득)
- [ ] 최종 −14 LUFS
- [ ] 효과음은 사건·전환에만

## 7. 알려진 결함 (v3 최종본 기준)
| 결함 | 위치 | 해결 방향 |
|---|---|---|
| 부산 국기 뱃지와 카드 겹침 — 위치 이동으로 임시 회피(125.6E 22.3N) | review 장면 | 카드 영역 RESERVED 등록, 뱃지 자동 회피(근본 해결) |
| 게시물 카드(`post`)는 명세만 존재 | 18 §5 | Phase 6.95에서 구현 |
| 위키미디어 webm 원본 다운로드 시 'File ended prematurely' 경고 | media3 | 사용 구간 확인, 필요 시 재다운로드 |
| 새로 받은 인물(이재명·노무현) 흑백 질감이 라이브러리보다 거침 | open/decision/past | 저장소 codex 공방으로 재가공 |
| 단어 앵커가 글자 비율 추정 | ask 패널 등 | ElevenLabs 정렬로 대체(`03` §6.3) |
| `CUT_TARGET` 큐 방식 | direction | `dip(t, lon, lat, w)` 인자형으로 |
| 장면 이름(챕터명) 수동 매핑 | 설명문 | 원고 장면 `title` 필드 |

## 8. 의존성
```
python 3.11+
pycairo, numpy, pillow, shapely(2.x), scipy
edge-tts, requests (ElevenLabs)
rembg, onnxruntime   (인물 배경 제거, 모델 u2net_human_seg 자동 다운로드)
cairosvg             (국기 SVG → PNG)
fonttools            (woff → otf)
ffmpeg (시스템)
fontconfig (fc-cache, fc-list)
```
데이터 캐시(Natural Earth geojson ~60MB, 지형 타일, 티어 PNG)는 gitignore하고 `geo.prep`이 재생성하게 한다.

## 9. 콘티 판(animatic) — v4.9.0 (back_and_forth D-0108, 사용자 결정 D97) [저장소 실측 추가]

**용어**: animatic = animation + -matic. 1930년대 디즈니가 스토리보드를 라이카 카메라로 찍어 음성과 함께 틀어 본 "Leica reel"이 원형이고,
광고·애니메이션 업계가 1970년대부터 animatic 이라 불렀다. 한국어 "콘티"는 일본어 コンテ(continuity 의 축약)에서 왔다. 본 저장소 용어 = **콘티 판**.

`python -m engine.render <proj> --animatic` → `out/animatic.mp4`. 목적은 흐름·호흡을 게이트 ② 전에 싸게 보는 것(WORKFLOWS W0).

| 항목 | 콘티 판 | 코드 |
|---|---|---|
| 진입 | `load_project(animatic=True)` **한 곳**에서 분기 — 프로파일 `rules animatic.profile`(480p, fps 24 그대로), 무대 모드, 레이어 선택 | `engine/project.py` |
| 프레임 루프 | 전편과 같은 순서. `render_frame` 은 `P.layers`(`engine.registry.LayerSet`)만 본다 — 전편 `FULL_LAYERS`, 콘티 판 `ANIMATIC_LAYERS` | `engine/render.py`·`engine/registry.py` |
| 지도 | `FlatMercatorStage`(MercatorStage 의 막지도 모드): 바다·육지 단색 + 국경선, 라벨 없음. 경계 = geo.yaml 티어 W bbox, 지오메트리 = NE 110m 추적 자료(`data/geo_flat/`, R-0135 A, `crimea_to_ua` 적용) | `engine/stage.py`·`tools/build_flat_map.py` |
| 자리표시 | badge·photo·clip·cutout·article·post·card·panel·primitive → 같은 자리·크기(G7)·타이밍의 상자 + `[뱃지: 이름]` 등. 상자는 전편 기하 함수를 그대로 부른다 | `engine/layers/animatic.py` 하나 |
| 그대로 | 자막·날짜·타이틀·엔딩 카드·마커·경로·타격 링·선박·국가 강조·시리즈·카메라·dip | — |
| 표식 | 전체 페이드 뒤 화면 위 가운데 띠(`rules animatic.band`), mp4 메타데이터 comment(`animatic.mp4_comment`), provenance `animatic: true`·`animatic_run` | — |
| 음성·음악 | 기존 `out/mix.f32`(edge-tts + BGM + bed_bass) 그대로, 2패스 loudnorm | `render_animatic` |
| 파일 | `out/animatic.mp4`·`animatic_checks.json`·`animatic_provenance.json`·`animatic_render.json`, 프리뷰는 `prev_animatic/` — 전편 산출물·`prev/` 를 덮지 않는다 | — |
| 자산 | 이미지·영상·지형 래스터·초상 실측·프로젝트 권리 점검을 쓰지 않는다 → 자산 없는 환경에서 렌더(plan.json·mix.f32 만 필요) | `tests/test_g8_animatic.py` |

검사 프로파일(`engine.checks.profile_skips`): `rules animatic.checks_skip`(글리프·글자 크기·권리·미디어 해상도·차트 정직성 4종·라벨 수)은
돌지 않고 `skipped` 로 남는다. 타이밍(shots)·자막·offscreen·stage_continuity·overlap·date·forbidden·genre_elements 는 돈다. hard 가 있으면 렌더 전에 실패한다(프리뷰와 같은 게이트).
`engine.mux`(deliver)는 `video_noaudio.mp4` 의 메타데이터 표식이 콘티 판이면 거부한다(`AnimaticDeliverError`).
비용 목표 = 5분 영상 4코어 3분(`rules animatic.cost_target_sec_per_300s`), 실측은 `reports/phaseG8/run_log.md`.

### v5.1.0 — 버전 도장·새 검사 (G12)
- 엔딩 카드 버전 도장은 G4-14 대상이 아니다(엔딩 카드 한정, 사용자 결정 D109 — `09` v5.1.0 절). provenance `end_card.version_stamp` = "v" + repo_version.
- 새 검사: `timeline_rescale`(hard, D-0121 §A) · `backdrop_rights`·`backdrop_repeat`(hard, D-0123 §3) · `island_overlap`(hard, D-0126 Q3) · `stage_choice`(warning, D-0123 §2). 검사 항목 23 → 28.
