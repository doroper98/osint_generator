<!--
tier: 3
last_synced_with: v7.2.0
kind: decision_and_plan
from: fable
to: opus
status: awaiting_user_decisions(§0) → then execute
depends_on: [CLAUDE.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md, docs/handoff/22_SKETCH_TRACK.md §7, rules/video_rules.yaml registries, engine/registry.py, engine/layers/effects.py, engine/layers/media.py]
-->

# D-0206 (Fable) — 새 이벤트 `flight`(드론·미사일·전투기 비행 + 꼬리선 + 착탄 링) · 위성 인셋(`inset`) 등록 계획

사용자 요청(2026-10-17, 원문 요지): "드론 타격 애니메이션 신에서 타격받은 정유소·생산 시설의 실제 이미지를 작게(구글맵 같은 위성 사진) 보여 주면 몰입이 좋겠다.
정확한 경로는 필요 없다. 어떤 국가의 대략적인 위치에서 표적으로 날아가는 애니메이션(경로 선이 뒤에 남는), 드론·미사일·전투기의 대략적인 형태만 있으면 된다."

대상 영상(가제) 「경유의 길 — 사흘에 한 번」: 한국산 경유 → 블라디보스토크 + 네 전장(우크라→러 정유소, 미·이스라엘→이란, 이란→걸프, 러→우크라 가스)의 타격 비교. 4막 구성은 Fable 분석(2026-10-17 채팅)대로.

---

## 0. 사용자 결정이 필요한 것 (구현 전 확인 — 이 셋이 정해지기 전에는 코드 착수 금지)

| # | 질문 | Fable 권고 | 근거 |
|---|---|---|---|
| U1 | 위성 이미지 출처. **구글맵·구글어스 화면은 쓸 수 없다**(재배포 라이선스 없음, `media_beats` 권리 목록 밖, C9). 대신 **Copernicus Sentinel-2**(10 m, 무료·공개, 표기 "Contains modified Copernicus Sentinel data 2026")와 **NASA FIRMS 열점**(공공 저작물)을 쓸지 | 쓴다. 두 출처를 `media_beats.licenses`/권리 레지스트리 허용 목록에 추가(규칙 개정 = 사람 승인, C11 P11) | 정유소 화재는 Sentinel-2 로 연기·그을음이 보이는 사례가 많다(OSINT 관행). FIRMS 열점은 "맞았다"의 독립 증거다. 둘 다 재배포 가능 |
| U2 | 인셋 밀도. 현 규칙은 미디어 비트 장면당 1개·40~60초당 1개(`media.density`). 1막 70초에 정유소 5곳을 보여 주려면 새 종류 `inset`(작고 짧은 지도 고정 썸네일)을 밀도 상한에서 **분리**해야 한다 | 분리한다. 제안값: `inset_show_sec: [2.5, 4.0]`, `inset_per_scene_max: 4`, `inset_min_gap_sec: 8` | 기사 카드를 분리한 선례(D-0163·D-0173, `total_exempt_kinds`)와 같은 방식. 값은 콘티 판에서 사용자 검토 |
| U3 | 출발 위치의 표현. 발사 지점은 어느 쪽도 공개하지 않는다. (a) 공격국 영토 안 **부드러운 발광 영역**(점 없음) + 꼬리선은 **점선**, 엔딩 카드에 "비행 경로는 개략 표현" 한 줄 (b) 공격국 수도·기지에 점 마커 | **(a)**. (b)는 사실 없는 좌표를 사실처럼 그린다(C0 경계, G4) | 본문에 `<미검증>`류 라벨은 금지(D85)이므로 "개략"은 선 스타일(점선)과 엔딩 한 줄로만 말한다 |

U1·U2 는 규칙 파일 개정이므로 사용자 승인 뒤 `docs/handoff/DECISIONS.md` 에 D 번호로 append.

---

## 1. 결정(Fable, 되돌릴 수 있는 선택 우선)

1. **새 이벤트 타입 `flight`** 하나로 "출발 영역 → 표적 비행 + 꼬리선 + 착탄 링"을 처리한다. 문장 앵커 하나 = 이벤트 하나(05 "요소는 하나씩"). 착탄 링은 기존 `draw_boom` 을 재사용(새 모양 금지, v3 합격 문법 유지).
2. `registries.event_types_planned` 의 `movers` 는 `flight` 로 **대체**(목록에서 제거하고 주석에 "v7.3.0 flight 로 대체"). `arc`(탄도 궤적·고도 단면, 미사일 스킬용)는 그대로 planned 로 둔다 — `flight` 는 평면 비행 표현이고 고도·발표값이 없다.
3. **위성 인셋은 새 이벤트가 아니라 `flight.inset: <mid>`(선택 필드)** 로 단다. 표적 옆에 작은 상자(폭 `flight.inset.w_px`)로 뜨고, 착탄 링 뒤 `inset.hold_sec` 동안 남았다가 사라진다. 미디어 레지스트리 kind 는 새 값 **`inset`**(U2 승인 시) — `photo` 와 분리해 밀도 검사에서 따로 센다. 출처 줄 포맷 `credit_formats.inset: "{file_note} · {credit_author}"`(file_note 예: "위성 · 2026. 08").
   - 단독 인셋(비행 없이 사진만)이 필요하면 기존 `cutout` 을 그대로 쓴다(kind inset 미디어도 cutout 에 허용). 새 렌더러를 둘 만들지 않는다.
4. **아이콘은 코드 벡터(cairo path) 3종**: `drone`(삼각 델타익 + 짧은 동체, 샤헤드형 실루엣), `missile`(가는 동체 + 꼬리 핀 4개), `jet`(후퇴익 + 수직 꼬리). 사진·AI 이미지 금지(G4-10). 크기·색은 토큰만(`flight.icon.*`), 진행 방향으로 회전.
5. **경로는 2차 베지어 한 가닥**(출발 → 표적, 수직 방향으로 `bulge_ratio` 만큼 휨). 직선 `route`(관계선)와 모양으로 구별된다. 꼬리선은 아이콘 뒤에서 **자라고**(progress 0→1) 착탄 뒤 `trail_fade_sec` 에 걸쳐 사라진다. 출발 영역은 반지름 `origin.r_px` 의 방사형 발광(알파 `origin.alpha`), 점·라벨 없음(U3-a).
6. **비행 시간은 거리와 무관하게 고정**(`dur_sec`, 기본 2.4). 개략 표현이므로 속도에서 사실 정보를 읽지 못하게 한다. 이벤트 `t1 − t0` 가 `dur_sec + boom 1.6 + inset.hold_sec` 보다 짧으면 검증 오류(조용한 잘림 금지, P6).
7. **효과음은 연출이 `sound.cues` 로 단다**(기존 boom cue, 자동 트리거 추가 안 함 — sfx_policy 유지). 출발 순간 whoosh cue 를 쓸지는 연출 재량(기존 kind whoosh 있음).
8. **카메라**: `flight` 의 출발 영역 중심과 표적 둘 다 `frame_points` 앵커로 넣는다(카메라 제안이 두 점을 한 화면에 담도록). `pacing.static_window.change_kinds` 에 `flight` 추가.
9. **콘티 판(animatic)**: `engine/layers/animatic.py` 에 같은 기하(발광·점선·아이콘·링)를 그린다. 인셋은 자리표시 상자 + `[인셋: mid]`(사진 미로드, 기존 cutout 콘티 방식과 같게).
10. 버전 **v7.3.0**(새 이벤트 타입 = MINOR, `quote` v5.4.0 선례). 한 커밋 = 한 의도: (a) 규칙·스키마·렌더러·프리뷰 예제·테스트 한 커밋 (b) U1 권리 목록 개정 한 커밋 (c) U2 밀도 규칙 한 커밋 (d) 문서 동기화 한 커밋.

---

## 2. 스키마 (`engine/events.py`)

```python
class FlightOrigin(BaseModel):
    lon: float
    lat: float            # 공격국 영토 안 개략 중심(연출이 country 중심·국경 근처로 고른다). 점·라벨로 그리지 않는다

class FlightInset(BaseModel):
    mid: str              # 미디어 레지스트리 id, kind == "inset"(U2) — 없으면 cutout 과 같은 kind 검사 오류
    side: Literal["left", "right", "up", "down"] = "right"   # 표적 기준 상자 위치(예약 상자 회피는 placement 가 맡음)

class FlightEvent(_Event):
    type: Literal["flight"]
    kind: Literal["drone", "missile", "jet"]
    origin: FlightOrigin
    lon: float            # 표적
    lat: float
    col: ColorName = "amber"      # accents 안 값만(ru·us·teal…). 기본 = boom 과 같은 amber
    impact: bool = True           # False 면 링 없음(요격·미확인 표적 — 그래도 꼬리선은 남지 않고 사라진다)
    inset: Optional[FlightInset] = None
```
- `t0` = 출발, 착탄 시각 = `t0 + rules.flight.dur_sec`(코드가 계산, 연출은 쓰지 않는다 — P8).
- 검증(`engine/validate.py`): `t1 - t0 >= dur_sec + boom_sec(effects 기존 1.6) + (inset.hold_sec if inset)` 아니면 `RegistryError`급 오류 메시지 `[flight-too-short]`.
- `DROP_NONE` 관례에 따라 `inset` 없으면 dict 에 남기지 않는다.

---

## 3. 규칙 토큰 (`rules/video_rules.yaml`, 설계 px 480p — 코드 리터럴 금지, `tests/anti_inertia/test_no_magic_numbers`)

```yaml
flight:                    # v7.3.0 D-0206 — 비행 이벤트(engine/layers/effects.py draw_flight). 개략 표현: 시간 고정·점선·출발 발광(사용자 결정 U3-a)
  dur_sec: 2.4             # 출발 → 착탄(거리 무관)
  ease: out_quad           # 진행률 보간(기존 ease_out 재사용)
  bulge_ratio: 0.18        # 베지어 제어점 = 중점 + 법선 × 거리 × 이 값(화면 px 기준)
  trail: {width: 1.6, dash: [6, 5], alpha: 0.85, fade_sec: 1.4}   # 점선 = 개략. 착탄 뒤 fade_sec 동안 알파 → 0
  origin: {r_px: 22, alpha: 0.28, pulse_sec: 1.6}                 # 방사형 발광(점·라벨 없음). 출발 전 pulse_sec 동안 숨 쉬고 출발과 함께 사라짐
  icon:
    size_px: {drone: 11, missile: 13, jet: 14}   # 긴 변
    halo: 2.0
    drone:   [[0,-6],[5,5],[0,2.5],[-5,5]]       # 델타익 다각형(머리가 −y, 진행 방향으로 회전)
    missile: {body_w: 2.6, body_l: 12, fin: 3}
    jet:     [[0,-7],[2,-2],[7,2],[2,3],[1.5,6],[3,7],[-3,7],[-1.5,6],[-2,3],[-7,2],[-2,-2]]
  inset:
    w_px: 118              # 상자 폭(높이 = media.cutout_h_ratio 재사용 — 정사각형에 가깝게 자른 위성 타일 권장)
    gap_px: 10             # 표적 점에서 상자까지
    hold_sec: 3.0          # 착탄 링 뒤 머무는 시간
    fade: [0.35, 0.45]     # in/out
    label_note: "위성"      # file_note 접두(예: "위성 · 2026. 08")
```
`accents` 에 새 색을 더하지 않는다(기존 amber·ru·us·teal 안에서 고른다).

U2 승인 시 `media.density` 에:
```yaml
    inset_show_sec: [2.5, 4.0]
    inset_per_scene_max: 4
    inset_min_gap_sec: 8
    total_exempt_kinds: [article, inset]     # 기존 article 에 inset 추가
    scene_exempt_kinds: [article, inset]
    window_exempt_kinds: [article, inset]
```
`media_beats.kinds` 에 `inset` 추가, `credit_formats.inset` 추가, `media.triggers.inset: [정유소, 정제소, 가스전, 터미널, 펌프장, 공장]` (제안만, P8).

U1 승인 시 권리 허용 목록(미디어 레지스트리 `license` 검증이 보는 곳 — Opus 가 `engine/media_registry.py`·`tools/asset_library.py` 에서 실제 검사 지점을 찾아 **한 곳**에 추가, 두 곳이면 SSOT 위반):
- `"Copernicus Sentinel data (free, full and open)"` — 표기 의무 문구를 `credit_author` 에: `Contains modified Copernicus Sentinel data 2026`
- `"NASA FIRMS (public domain)"` — `credit_author: NASA FIRMS`

---

## 4. 렌더러 (`engine/layers/effects.py: draw_flight`)

```
p = clamp01((t - t0) / F.dur_sec); p = ease_out(p)
s = view.to_screen(origin); e = view.to_screen(target)
ctrl = mid(s, e) + normal(s→e) * |s−e| * F.bulge_ratio
pos(u) = bezier2(s, ctrl, e, u); heading = atan2(d bezier/du)
1) 출발 발광: t0 − origin.pulse_sec ~ t0 : 반지름 origin.r_px 방사 그라데이션(col, alpha × 숨쉬기), 출발 뒤 0.4초에 걸쳐 사라짐
2) 꼬리선: 점선(trail.dash) s → pos(p) 를 베지어 샘플(32 분할) 로 stroke. 착탄 뒤 alpha × (1 − (t − t_hit)/trail.fade_sec)
3) 아이콘: p < 1 일 때만. translate(pos) → rotate(heading) → 다각형/동체 fill(col) + halo stroke
4) 착탄: t >= t_hit 이고 impact 면 draw_boom(ctx, R, view, t, {"t0": t_hit, "t1": t_hit + 1.6, "world": target}) 그대로 호출(새 링 모양 금지)
5) 인셋: t_hit − 0.2 ~ t_hit + inset.hold_sec : 상자(media.draw_cutout 의 상자·캡션 함수 재사용, 흔들림·회전 없음 — 위성 타일은 정지), side 로 위치, R.reserved 에 예약 상자 등록
```
- `MAP_LAYER_ORDER`: `boom` 바로 뒤, `cutout` 앞에 `flight` 삽입(링 위·마커 아래).
- `engine/registry.py`: `"flight": Entry(ev.FlightEvent, draw_flight, "map")`.
- 콘티 판 `engine/layers/animatic.py: draw_flight`: 같은 기하, 인셋은 회색 상자 + `[인셋: mid]`.
- `engine/provenance.py features()` 가 `flight` 와 `inset` 사용 수를 기록하는지 확인(기록 안 되면 추가 — P5).
- 카메라 `engine/camera_suggest.py`/`framing.py` 의 앵커 수집에 `flight` 두 점(origin·target, `point_px` 여유) 추가.

---

## 5. 검사·테스트·예제 (레지스트리 세 곳 동시, P10)

| 항목 | 파일 | 내용 |
|---|---|---|
| 프리뷰 예제 | `tests/fixtures/preview/flight.yaml` | `source: projects/diesel_road_2026/direction.py (첫 사용 예)`; 랴잔 표적(39.74, 54.63), origin 우크라이나 북동부 개략(35.0, 50.5), kind drone, inset 없음 |
| 프리뷰 예제 2(인셋) | 같은 파일에 두 번째 event 허용되면 추가, 아니면 `flight_inset.yaml` 은 만들지 않는다(테스트는 `{key}.yaml` 하나만 본다 — 인셋 포함 예로 교체해도 됨) | |
| 레지스트리 양방향 | `tests/anti_inertia/test_registry_complete.py` | 자동. `movers` 제거 확인 |
| 프롬프트-스키마 동등 | `tests/anti_inertia/test_prompt_schema_parity.py` | 프롬프트의 `flight` 예시가 `FlightEvent` 를 통과해야 함(P4) |
| 매직 넘버 | `test_no_magic_numbers` | 아이콘 다각형은 규칙 토큰에서 읽는다(코드에 좌표 리터럴 금지) |
| 골든 | `docs/handoff/golden/` 25컷 md5 | **불변이어야 한다**(v3 에 flight 없음). 변하면 레이어 순서 삽입이 다른 레이어를 건드린 것 — 원인 수정 |
| 새 단위 테스트 | `tests/engine/test_flight.py` | (a) 착탄 시각 = t0 + dur_sec (b) `[flight-too-short]` 오류 (c) impact False 면 draw_boom 미호출 (d) inset mid 의 kind 가 inset 아니면 오류 (e) 렌더 1프레임 smoke(세 kind) |
| 밀도 검사 | `engine/checks.py` | U2 승인 시 `[inset-density]` warning(장면당 > inset_per_scene_max, 간격 < inset_min_gap_sec) |
| 검증 시간 규칙(D187) | 관련 테스트 + `tests/anti_inertia` + light·dark 골든 25컷만. 전체 pytest 는 main 병합 직전 1회 | |

---

## 6. 프롬프트·문서 동기화 (C7)

- `rules/video_rules.yaml` 의 `{{RULES.event_types}}` 생성 블록에 `flight` 한 줄:
  `"비행: {\"type\": \"flight\", \"kind\": drone|missile|jet, \"origin\": {lon, lat}(공격국 영토 안 개략 중심 — 점·라벨로 그리지 않는다), \"lon\", \"lat\"(표적), \"col\"?, \"impact\"?: true, \"inset\"?: {mid(kind inset), side}} — 한 문장에 하나. 발사 지점이 발표된 사건에만 origin 을 정확히 두고, 아니면 국토 중심·국경 근처 개략값. 착탄 효과음은 sound.cues boom 으로 단다."`
- `prompts/` 재생성 → `tests/anti_inertia/test_prompts_from_files` 통과 확인.
- `docs/handoff/22_SKETCH_TRACK.md` §7 표: `movers`→`flight` 등록 완료 행 추가, `arc` 는 남김.
- `docs/handoff/06_OVERLAYS_AND_DATA_LAYERS.md`(지도 레이어 표) + `docs/handoff/14_MEDIA_PHOTO_VIDEO.md`(`inset` 종류·출처 줄·밀도) + `docs/05_DATA_SCHEMA_SPEC.md`(FlightEvent).
- `docs/handoff/DECISIONS.md` append: D-0206 Fable 결정(§1) + 사용자 결정 U1·U2·U3(승인 뒤).
- `CHANGELOG.md` v7.3.0, `VERSION`, `orchestrator/__init__.py`, Tier 1·2 YAML 헤더 `last_synced_with`.

---

## 7. 영상 적용 지침(연출 단계, 코드 아님)

- 1막(서부 러시아 region w 20~30, 카메라 고정): 정유소마다 `flight`(drone, origin = 우크라이나 북동부 개략 한 점으로 **통일** — 장면 안에서 출발 발광이 같은 자리에서 숨 쉬는 것이 리듬이 된다) + `inset`(Sentinel-2 타일, U1). 5곳 중 인셋은 위성에서 연기·그을음이 실제로 보이는 곳만(없으면 인셋 생략, "자료가 없으면 지어내지 않는다").
- 3막(걸프 strait): 이란 → 라스라판·푸자이라·펌프장은 `flight`(missile) origin = 이란 남부 해안 개략. 사우스파르스는 origin 을 **두지 못한다**(이스라엘·미국 귀속 논쟁) → `boom` 만 + `versus` 패널. 하르그섬은 `marker` 만(석유 시설 미타격).
- 4막: 러 → 하르키우·폴타바 `flight`(drone/missile 혼용 금지 — 보도가 '드론'이면 drone), origin = 러시아 벨고로드 방면 개략.
- 콤소몰스크: 보도 엇갈림 → `flight` 금지, 마커 + 카드.
- 엔딩 카드 맨 아래 한 줄(가장 작은 글씨, D85 방식): "비행 경로·출발 위치는 개략 표현 · 51%·31%는 우크라이나 측 발표로 독립 검증 전".
- 인셋 권리: `media/RIGHTS` 에 Sentinel-2 타일마다 촬영일·타일 id·"Contains modified Copernicus Sentinel data 2026". `tools/asset_library.py check` 0 뒤 콘티 판.

---

## 8. 보고 형식(Opus → R)

- 골든 25컷 md5 불변 증명(light·dark), 새 테스트 결과, `tests/anti_inertia` 결과.
- 프리뷰 컨택트 시트: `flight` 3종(drone·missile·jet) 각 1컷 + 인셋 1컷 + 콘티 판 1컷 — **사진으로 확인**(P12, 코드 리뷰만으로 '적용됨' 판정 금지).
- provenance `features_used` 에 flight·inset 수.

---

## 9. 추가(2026-10-17 저녁, 사용자 대화) — 데이터 시리즈 출처 · 인물·기사 적극 사용

### 9.1 사용자 결정 추가 U4 — 데이터 시리즈 출처 확장
| # | 질문 | Fable 권고 |
|---|---|---|
| U4 | 그래프(러시아 정제 처리량·경유 수출, 걸프 경유 순수출)를 본편 `series` 로 올리려면 `data.sources_allowed`(현재 FRED·연준) 와 `data.licenses_allowed` 에 IEA(보고서 인용)·Vortexa·Kpler·LSEG(2차 보도 인용값) 를 더해야 한다. 1차 표를 열지 못한 값은 `transform.formula` 에 "보도 인용(매체·날짜)" 를 적고 화면에 출처 줄을 단다 | 허용하되 **인용 출처 종류 `press_cited`** 를 새로 두어 FRED 처럼 코드가 받는 값과 구분한다. 추정치 없는 달은 비운다(보간 금지, 정직성 §5.3) |

분석·그래프 초안: 감독 세션 scratch `charts/diesel_trend_2026.png`(4패널: A 정제 처리량 3·4·6·7·9월, B 해상 경유 수출 1·2·5·7·8·9·10월, C 경유 생산 3~5월, D 걸프 순수출 2·8·9월). 값과 출처는 그 그림의 각주가 정본.

### 9.2 사용자 지시(원문, UF-101·UF-102 로 원장 기록)
- "영상에 인물이 필요하면 인물 등장씬을 적극적으로 작동시켜."
- "기사도 적극적으로 조판하고."
- "이번에는 좀 방대한 영상이 될 수 있겠다?"

연출 지침: 인물 발언·결정 문장마다 `badge(person)` + `quote`, 기사 출처 문장마다 `article`(60초당 상한 2 는 유지, 후보가 있는데 안 쓰면 [article-unused]). 장치(UF-101 [person-unused], UF-102 article_per_min_min)는 영상 전달 뒤 첫 작업.

### 9.3 인물 명단 — 공용 자산 유무
| 인물 | 역할(영상) | 공용 자산 | 조치 |
|---|---|---|---|
| 트럼프 · 푸틴 · 젤렌스키 · 이재명 · 네타냐후 · 하메네이 | 4막 발언·결정 | 있음(`assets/library/people/*_mono_v01`) | 그대로 |
| 스콧 베선트(미 재무장관) | 러시아 경유 일반허가(10월) | **없음** | 미 재무부 공식 초상(공공 저작물) → `tools/portrait_fallback.py cutout`(engraving) → `asset_library.py promote` |
| 올레크 코제먀코(연해주 지사) | 극동 연료난 현장 발언 | **없음** | kremlin.ru 사진(CC BY 4.0) 또는 Commons 확인 → 같은 경로. "블라디보스토크 주 총리" 는 공식 직함이 **연해주 지사(губернатор Приморского края)** |
| 알렉산드르 노박(부총리) | 수출 금지·수출 목표 발언 | 없음 | kremlin.ru/government.ru(CC BY 4.0) |
| 블라디슬라프 블라시우크(우크라 제재 담당) | 10월 6일 비판 | 없음 | president.gov.ua(CC BY 4.0) 확인 |
| 강유정(청와대 대변인) · 김정관(산업부 장관) | 한국 입장·수출 관리 | 없음 | 정부 공식 사진(KOGL 1유형) 확인 |
| 에두아르트 후다이나토프(NNK 소유주) | 구매자 | 없음 | 권리 확인 사진이 없으면 뱃지 없이 회사명 카드만 |
새 초상은 Commons·정부 사이트 접근이 필요 → 새 세션 환경 허용 도메인에 `commons.wikimedia.org`·`upload.wikimedia.org` 추가 필요(현 허용: gibs·raw.githubusercontent·jsdelivr).

### 9.4 규모 판정
4막 + 데이터 패널 + 인물·기사 적극 사용이면 원고 기준 **7~9분**(문장 90~110개). 전작(호르무즈 292초·걸프 무기 257초)의 두 배. 무대 연속성(주 1 + 보조 1, 전환 2회)은 그대로 적용되므로 길이가 늘어도 무대를 늘리지 않는다. 9분을 넘기면 2부작(①타격과 경유 ②울산의 기름) 분할을 사용자에게 제안.
