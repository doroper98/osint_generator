<!--
tier: 2
last_synced_with: v5.10.0
ssot_for: [quality-guide-2026-10-10]
depends_on: [CLAUDE.md, rules/video_rules.yaml]
last_review: 2026-10-10
-->

> 사용자 제공 구현 브리프(2026-10-10, codex 공동 작성) 원문. 저장소 규칙과 충돌하는 부분의 판정은 back_and_forth D-0153 §2 와 DECISIONS D148·D149 를 따른다. 원문은 수정하지 않는다.

# OSINT Generator 영상 품질 개선 통합 구현 지침

수신: Claude Fable  
작성 기준: 2026-10-10, `doroper98/osint_generator` `95a0b917afac00b598116698e494d57dc288cc1b`  
목적: 인물부터 무기 벡터, 전 세계 지도, cascade·연결선, 추가 과금 없는 TTS까지 논의한 개선을 하나의 구현 계획으로 정리한다. 기존 영상 문법·데이터 정확성·권리·비용 조건을 지키면서 읽기 쉽고 일관된 영상으로 완성한다.

## 빠른 찾기

처음에는 범위·승인 상태를 확인하고, 필요한 기능 절을 읽은 뒤 구현 순서와 합격 기준으로 마무리한다.

- [범위와 승인 상태](#1-이번-문서의-범위와-승인-상태) · [실제 통합 경로](#3-실제-코드의-통합-지점)
- [원형 인물과 흔들리는 국기](#10-원형-인물과-흔들리는-국기)
- [자체 재사용 영상 자산 스킬과 F-35 검증 예시](#11-hairline에서-필요한-부분만-추출한-자체-재사용-영상-자산-스킬)
- [전 세계 지도](#12-전-세계-지도-구조) · [국경과 해안 의미](#14-국경과-행정구역) · [최신 선·수계 스타일](#15-강과-도로의-구별)
- [승인된 cascade V2](#6-cascade-to-be-구현-방향) · [관계선과 주변 UI](#8-경로와-패널의-연결선)
- [추가 과금 없는 TTS 개선](#19-추가-과금-없는-tts-개선)
- [자산과 코드 이용 가능 범위](#20-제작한-자산과-코드의-이용-가능-범위) · [비용·라이선스·성능](#21-비용과-라이선스와-성능)
- [단계별 구현·PR 검수](#22-하위-호환-구현-순서) · [테스트와 합격 기준](#23-테스트와-합격-기준) · [최종 전달물](#24-최종-전달물)
- [과학기술 확장에 대한 선택 부록](#부록-과학기술-영상으로-확장할-때의-판단)

## 1 이번 문서의 범위와 승인 상태

- 전체 목표는 인물·벡터·지도·UI·음성의 품질을 함께 높이는 것이다. 핵심은 원본 정체성, 정확한 geometry와 가림, 명확한 정보 위계, 자연스러운 내레이션이며 아래 기능별 범위를 모두 포함한다.
- 최신 사용자 피드백: 옅은 바탕색·강조색은 허용된다. 뒤쪽 ‘발표’ 카드의 선 단절을 고치고, `발표→협의→조치`를 매번 일정하게 오른쪽 아래로 쌓는다. ‘협의’는 위, ‘조치’는 아래로 어긋나는 배치를 원하지 않는다. 현재 요청에 따라 후보 geometry를 바꾼다.
- 원형 인물 사진과 뒤에서 흔들리는 국기를 유지하는 개선 방향, 지형·해저 음영과 확대에 따른 정보 증가는 사용자가 긍정적으로 검토한 방향이다.
- 수정 cascade V2의 오른쪽 아래 정렬·외곽선·절제된 색상 방향은 사용자가 확인했다. F-35 V2와 지도 V4는 별도 검토 대상이다. 시각 승인만으로 저장소 수정이나 기본값 교체를 수행하지 않는다.
- 최신 지도 요청: 국경은 짙은 실선, 도로는 얇은 실선, 행정구역은 얇은 회색선, 강은 얇고 옅은 하늘색선, 바다는 푸른색 계열이다. 이전 회색조·굵은 강·성긴 행정 점선 시안보다 이 요청을 우선한다.
- 이 문서는 실제 Markdown 구현 브리프다. 현재 저장소 수정·커밋·PR·배포·유료 API 사용을 실행하거나 승인하는 문서가 아니다.
- 후속 구현을 시작할 때 현재 브랜치의 지침과 변경사항을 먼저 확인한다. 아래 핀보다 새 코드가 있으면 차이를 기록하고 사용자 작업을 보존한다.
- 지도는 지리적 맥락을 보여준다. 우크라이나 예시를 전선·점령·통행 가능 여부의 최신 자료로 취급하지 않는다.

### 기능별 범위와 현재 상태

| 기능 | 구현해야 할 결과 | 현재 상태 |
| --- | --- | --- |
| 인물 | 원형 사진·국기 물결 유지, 얼굴 비율·선·그림자 개선, 기존 픽셀 보존 | 방향 확인, 독립 비교 완료; 엔진 통합·성능 검증 남음 |
| 재사용 선화 스킬 | Hairline의 영상 자산용 방법을 추출한 자체 skill, 여러 대상의 정확한 윤곽·가림·크기별 변형 | 설계·구현 지침 단계; F-35 V2는 검증 예시이며 skill은 미설치 |
| 전 세계 지도 | 지형·해저 음영, 줌별 행정·도시·도로, 최신 얇은 선과 푸른 수계 | 한국·우크라이나 독립 검증; V4는 최신 선형·수계와 국경 의미 수정안 |
| Cascade | 일정한 오른쪽 아래 배열, 실제 외곽 가림, 온전한 테두리 | 수정 V2를 사용자 확인; 실제 엔진 적용은 별도 |
| 관계선·주변 UI | 의미별 연결, 명확한 접점·상태·강조, 겹침·잘림 제거 | 최초 24초 비교의 relation 부분이 참고; 전 패널 합격 아님 |
| TTS | 추가 과금 경로를 막고 기존 음성의 발음·분절·레벨·싱크 개선 | 코드 조사 기반 구현 계획; 새 음성 비교는 미실행 |

### Claude Fable의 시작 체크리스트

1. 현재 저장소 지침·브랜치·변경 내용을 읽고 기준 커밋과 차이를 정리한다. 기존 변경을 덮어쓰지 않는다.
2. 이 문서의 승인 상태와 최신 요청을 먼저 읽는다. 과거 시안의 수치를 최종안으로 되돌리지 않는다.
3. `rules/video_rules.yaml`, `engine/style.py`, 관련 schema를 읽어 single source of truth와 출력 스케일을 확인한다.
4. 인물·미디어 registry와 rights/credits, 지도 준비·캐시, TTS 설정·plan·audio 경로를 각각 확인한다.
5. 구현 요청을 받은 범위에서 작은 변경 단위로 시작하고, 각 단계의 회귀·시각·음성 검수를 통과한 뒤 연결한다.
6. 유료 API, 새 서비스 가입, 공개 배포나 기존 기본값 교체가 필요해지면 기존 범위를 넘는지 확인하고 먼저 판단을 요청한다.

## 2 기준선과 비교 영상의 증거

[기준 커밋](https://github.com/doroper98/osint_generator/tree/95a0b917afac00b598116698e494d57dc288cc1b)의 실제 함수와 규칙을 As-is 기준으로 삼는다.
비교용 테스트는 저장소 바깥에서 만든 독립 렌더다. 완성된 기존 프로젝트 영상을 캡처한 결과 또는 엔진에 통합된 새 기능으로 설명하지 않는다.

- Cascade As-is: 핀의 `engine/cascade.py`와 `rules/video_rules.yaml`을 사용한 통제된 컴포넌트 비교. 정확한 데모 기록은 아래 별도 항목을 따른다.
- 인물 As-is: 기존 `badge_at` 계열 함수 본문을 그대로 사용했다. 양쪽 모두 기존 `assets/library/people/tusk_mono_v01.png`의 동일한 얼굴 픽셀이다.
- 인물 비교 영상: `portrait_flag_comparison.mp4`, 1280×720, 30 fps, 72프레임, 2.4초. 실제 제작 영상 전체 테스트는 아니다.
- F-35 As-is: 기준 저장소에는 F-35 등록 자산이 없다. 사진에서 준비한 테스트 컷아웃을 기존 `draw_cutout`에 넣은 결과다. 기존 F-35 운영 장면이라고 쓰지 않는다.
- F-35 V1 사진 컷아웃은 AI 보조 배경 제거를 거쳤다. V2는 별도로 작성한 SVG이며 래스터 기체나 이미지 생성 출력을 포함하지 않는다.
- 지도: 한국과 우크라이나는 독립 제안 렌더다. 두 지역의 성공으로 전 세계 데이터·투영·행정체계가 구현됐다고 주장하지 않는다.
- 후속 구현자는 입력, 폰트, 소스 해시, 버전, 라이선스, 실행 명령, 검증 결과를 보존한다. 이 문서에서 언급한 소스·harness 전체가 첨부된 것으로 가정하지 않는다.

## 3 실제 코드의 통합 지점

아래는 기준 커밋에 존재하는 경로다. 변경 전에 각 파일의 최신 구현과 호출 관계를 다시 읽는다.

| 실제 경로 | 역할과 변경 경계 |
| --- | --- |
| `engine/cascade.py` | `layout`, `cascade_boxes`, `check_text`, `draw_cascade`; 배치와 검사가 같은 계산을 유지해야 한다 |
| `engine/style.py` | 규칙을 스타일 토큰으로 푸는 공통 경로; 별도 하드코딩 색상 테이블을 흩뿌리지 않는다 |
| `rules/video_rules.yaml` | cascade, island, 색상, 폰트, 480p 설계 규칙의 원본 |
| `engine/island.py` | `draw_frame`을 여러 컴포넌트가 공유한다. cascade 개선이 모든 island를 바꾸지 않도록 선택형 스타일을 전달한다 |
| `engine/layers/badges.py` | 원형 인물·국기 렌더; 인물 종류와 국기만 있는 cascade 배지를 혼동하지 않는다 |
| `engine/layers/media.py` | `draw_cutout`; 무기 자산 교체와 기존 위치·캡션·그림자 동작을 분리한다 |
| `tools/portrait_fallback.py`, `tools/media_fetch.py` | 기존 인물 fallback·원본 수집·검증·정규화 |
| `assets/library/library_manifest.json`, `assets/media/media_registry.json`, `assets/entities.yaml` | 기존 자산·미디어·인물 식별 registry |
| `engine/media_registry.py`, `schemas/media_models.py`, `engine/credits.py` | 자산 schema와 출처·권리·credit 연결 |
| `engine/layers/routes.py` | 경로·봉쇄선; 현재 glow·점선·화살촉에 담긴 의미를 보존한다 |
| `engine/panels/network.py`, `timeline.py`, `relation.py`, `fork.py` | 연결선·시간축·관계·분기를 각자의 데이터 의미에 맞게 처리한다 |
| `engine/typography.py`, `engine/timebase.py` | 글자 실측, 경로, easing 재사용 |
| `engine/context.py`, `engine/assets.py` | 렌더 컨텍스트와 자산 준비의 기존 경로 재사용 |
| `engine/stage.py`, `engine/projection.py` | MercatorStage·Mercator 계산·기반 지도는 stage, world→screen의 View는 projection |
| `engine/layers/borders.py`, `engine/layers/labels.py` | 국경·ADM1·지명 및 기존 LOD |
| `geo/prep.py`, `geo/prep_geometry.py`, `geo/prep_tiers.py` | 프로젝트 지리자료 준비·geometry·terrain tier/hillshade; 프로젝트 `geo.yaml`·`labels.yaml` 연결 |
| `tests/test_cascade.py`, `tests/test_g14_cascade.py` | 기존 폭·개수·전환·검사 계약 보존 |
| `config.yaml`, `script/plan.py`, `script/tts/`, `script/timeline.py`, `audio/mix.py`, `audio/qa.py` | 기존 TTS 설정·합성·cache·타이밍·믹싱; §19의 세부 경로 참고 |

추가 실제 경로: `engine/events.py:226–256`는 cascade 입력·순서·간격, `schemas/rules_models.py:1542–1568`는 폭과 step 제약, `engine/render.py:76–91`와 `engine/reserved.py:61–66`는 카드 예약영역을 연결한다. 새 모듈 이름을 기존 파일처럼 제시하지 않는다.
`visual_profiles`, `map_data_manifest`, `prepare_map_cache` 등의 이름은 아래에서 제안하는 인터페이스 개념이며 현재 API라고 가정하면 안 된다.

## 4 Cascade에서 반드시 보존할 의미

[채택 지시 D-0139](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/back_and_forth/261002_134459_D0139_fable_cascade-adopt.md)는 D116·D117의 합격 문법과 고정값을 명시한다.

1. 고정 지도 위에 사건 카드가 겹쳐 쌓인다. 현재 사건이 맨 앞인 의미는 유지하되, 후보는 최신 요청에 따라 시간 순서대로 일정한 오른쪽 아래 방향을 따른다.
2. 카드 사이에 레일이 없다. node graph나 세로 타임라인으로 재설계하지 않는다.
3. 날짜·등장 순서는 연대기다. 인과관계·지휘관계·영향의 증거가 없으면 연결선이나 화살표를 추가하지 않는다.
4. 뒤 카드의 국기 원, 날짜, 제목 앞부분과 경계 페이드가 남는다. 다음 카드에 덮인 배경은 그리지 않아 투명 카드가 중첩되어 비치지 않는다.
5. 깊이는 겹침·절제된 명암으로 구분한다. 이전 카드의 scale·높이·depth 변화 때문에 시간 순서의 오른쪽 아래 정렬이 뒤집히지 않게 한다.
6. 물러나는 글자는 전환 앞 절반에 지우고 새 글자는 뒤 절반에 보여 겹친 글자가 동시에 비치지 않게 한다.
7. 글자 넘침은 오류다. 조용한 clipping, 말줄임, 지나친 자동 축소로 오류를 숨기지 않는다.
8. 같은 순간 cascade는 하나이며 일반 카드와의 기존 동시 사용 금지 및 예약영역 검사를 유지한다.

## 5 기존 Cascade 배치와 타이밍

단위는 854×480 설계 좌표다. 아래는 새 권장값이 아니라 현재 채택된 값이다.

| 항목 | 기존 값 |
| --- | --- |
| 위치와 노출 폭 | `x0=22`, `y=60`, `step=68`, `flag_R=12` |
| 앞 카드 | `214×82`, `pad_x=13`, 날짜 `10.5`, 제목 `13`, 부제 `10`, 강조선 `3` |
| 뒤 카드 | `back_scale=.86`, `back_text_alpha=.5`, `back_fade_px=12` |
| 깊이 | `back_dy=5`, `back_dim=.06`, `max_back=4` |
| 전환 | `focus_sec=.5`, `shift_sec=.6`, `width_cap=560` |

- 정상 최대 폭은 `4×68+214=486`, 밀려나는 순간 최대 계산은 `5×68+214=554≤560`이다.
- 밀기 없는 새 글자 등장 구간은 앵커 이후 `.25–.50초`; 밀기 있는 구간은 `.30–.60초`다.
- `text_sec(k)`는 밀기 시 `max(focus_sec, shift_sec)`를 사용한다. 단순히 모든 항목을 `.5초`로 바꾸지 않는다.
- 과거 D117의 고정값은 기존 프로필의 호환성 기준이다. 최신 개선 요청에 따라 크기·간격·타이밍을 제안할 수 있지만 별도 opt-in 후보로 구분하고 변경량을 공개한다.
- 실제 내레이션의 문장·단어 타임코드에서 `items[].at`를 정한다. 데모의 일정 간격을 운영 장면의 자동 규칙으로 복사하지 않는다.
- 기존 생성·검사 계약에서 요구하는 최소 항목 간격과 `t0/t1` 여유를 지킨다. 음성에 비해 카드가 너무 빨리 지나가면 문구나 연출을 조정한다.

## 6 Cascade To-be 구현 방향

초기 후보는 카드와 글자를 키웠다. 최종 수정의 우선 과제는 일정한 오른쪽 아래 정렬과 온전한 frame 가림이다. 후보 geometry와 draw·reserved·overflow 검사에 같은 토큰을 공급한다.
- 논리적 slot `s`의 anchor는 `x=x0+s×dx`, `y=y0+s×dy`, `dx>0`, `dy>0`으로 둔다. 이전 카드 축소는 이 anchor 기준으로 처리하고 별도 depth Y를 더해 정렬을 뒤집지 않는다.
- oldest-card shift는 모든 카드에 같은 slot offset을 적용해 방향과 간격을 유지한다. 등장·축소·이동 중에도 논리 anchor 순서가 역전되지 않는지 검사한다.

- 밝은 회색 지형 위에서는 어두운 중성 카드로 본문 대비를 확보한다. 뒤 카드는 더 차분하고 앞 카드가 가장 읽기 쉬워야 한다.
- actor accent의 기존 의미와 키를 유지한다. 국기, 날짜, 텍스트 역할도 유지해 색만으로 사건을 구별하지 않게 한다.
- 카드 테두리는 겹침·clip·rounded corner에서도 의도한 visible contour가 이어져야 한다. 얇게 만드는 것만으로 품질을 판단하지 않는다. 그림자·옅은 표면색·강조색은 읽기와 깊이 표현에 맞춰 사용한다.
- 후보의 텍스트 위치·크기와 카드 높이를 반영해 `check_text` 및 예약영역도 동시에 갱신한다. 그림만 넓히고 검사·회피 상자는 예전 크기로 남기는 구현은 금지한다.
- `draw_frame` 전역값을 교체해 다른 패널까지 바꾸지 않는다. 기존 호출의 기본 출력은 동일해야 한다.
- 국기 원의 변형이나 국기 띠 경계 뭉개짐이 없는지 작은 크기에서 확인한다.
- 아래는 사용자가 확인한 독립 cascade V2의 값이다. 운영 엔진 통합·전체 회귀 검증·기본값 채택은 별도 단계다.

### 확인된 뒤 카드 테두리 단절

- 원인은 [cascade.py 162–164행](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/cascade.py#L162)의 전체 높이 세로 clip이 `draw_frame`에도 적용되는 것이다. 다음 카드의 실제 사각형 아래로 노출되는 부분까지 잘라낸다.
- 초기 입력 `t=5.8초`에서 ‘발표’ 아래끝은140.52, 뒤의 ‘협의’ 아래끝은135.52다. `x90–158/y135.52–140.52`는 보여야 하지만 첫 카드의 `x≥90`가 통째로 제거되어 하단선이 중간에서 끝난다. 두 카드에서는 앞 카드가 덮어 문제가 덜 드러나며 3개 이상에서 확인된다.
- 초기 To-be도 같은 clip을 재사용했다. baseline의 노출 하단 높이 차는 5px, 초기 후보는 8px였다. 색이나 선폭만 바꾸어서는 이 원인을 해결할 수 없다.
- frame/fill/stroke는 모든 앞쪽 카드의 실제 rounded-rectangle coverage로 가린다. 배경 투명도를 고려해 가려진 뒤 fill·선이 앞 카드에 비치지 않도록 한다. 전체 frame clip을 무작정 제거하지 않는다.
- 여러 occluder는 합집합 또는 순차 complement clip으로 처리한다. 단일 EVEN_ODD compound mask는 겹친 occluder 영역을 XOR로 열어 뒤 선을 다시 드러낼 수 있다.
- `cascade_boxes():132–135`의 기존 세로 clip 기반 상자도 함께 수정한다. 복원된 하단 strip이 라벨 충돌 검사에서 누락되지 않도록 shared visibility mask 또는 보수적인 사각형 분해를 사용한다.
- 글자는 기존 step clip·경계 fade·시간차를 별도 유지한다. frame 가림과 glyph 노출을 한 clip에 묶지 않는다. 국기 원·그림자·모서리와 이동·fade·oldest-card shift도 실제 노출 geometry로 검사한다.

### 수정 Cascade V2 구현값과 검증

- 파일: `cascade_alignment_continuity_v2_1080p.mp4`, 1920×1080, 30 fps, 18.000초·540프레임, 무음. 위 As-is/아래 To-be에 동일 입력·동일2.35배를 적용했다. 전체 decode 오류0이며 전환·shift를 포함한13개 decode 시점을 확인했다.
- 가상 기관8항목 앵커: `.5/2.6/4.7/6.8/8.9/11/13.1/15.2초`. `발표→협의→조치→후속 대응→재협의→추가 조치→재검토→후속 발표`이며 실제 사건·국기가 아니다.
- As-is는 핀의 `cascade.draw_cascade`, `island.draw_frame`, `badges.badge_at` 원본 함수를 별도 테스트 컨텍스트에서 실행한다. 확인된 기존 clip 현상도 그대로 보여준다.
- 후보는 복제 토큰의 독립 namespace에서 원본 layout의 x-window·fade·focus를 재사용하고 y를 일정한 slot 식으로 바꾼다. 기존 규칙이나 함수 본문을 수정하지 않았다.
- 비교판 배율은 출력 profile과 별개다. 아래 수치는 480p 설계 px이며 1080p 파일이 운영480/720/1080 실제 크기 QA를 대신하지 않는다.

| 항목 | 기준선 → 수정 후보 V2 |
| --- | --- |
| 앞 카드·타이포그래피 | `214×82→230×108`; 제목 `13→18` Plex Sans KR Bold, 부제 `10→11.5`, 날짜 `10.5` Plex Mono Medium |
| slot 위치 | `dx 68→64`, `x=22+64s`, `y=60+12s`; 좌상단 pivot 고정; 개별 Y slide와 depth Y 제거 |
| 뒤 카드 | scale `.86`; 높이 `(108−20×back)×scale`, 완전히 뒤일 때 `88×.86` |
| 여백·세로 위치 | pad `13→14`; date/title/detail Y `16/41/61→19/56/82`; date X `18` |
| frame·강조 | radius `10→3`, edge `1→.65`, top accent `3→1.8`; foreground occluder에는 stroke half `.325` 여유 포함 |
| 타이밍 | focus `.5초`, shift `.6초`, 글자 앞/뒤 절반 순서와 경계 fade `12` 유지 |
| 표면·글자 | 바탕 `#111514`, 앞/뒤 표면 `#1B211D`/`#171C19`, 본문 `#EDF0E9`, 보조 `#A2AAA5`, 테두리 `#4D5851` |
| 절제된 강조색 | gold `#BFB18F`, blue `#93A8B5`, rose `#B79895`; 가상 기관용 후보이며 실제 국가 identity palette와 분리 |

첫 window exit 전까지 기존 anchor는 제자리에 있고, 이후 전체가 같은 offset으로 왼쪽 위로 이동한다. 카드마다 다른 depth 이동으로 위아래가 바뀌지 않는다.
8항목·18초·120Hz의 2,160시점 검사: 최대폭549.429<560, 뒤 카드 최대4, dx64/dy12 오차≤5.7e−14, anchor 오차0. 겹친 occluder 영역 alpha0과 노출 테두리4개 표본을 확인했고, 별도15시점·코드·decode 프레임 검토에서도 방향과 테두리 연속성을 확인했다.
기준선 별도7항목·4,521시점 검사는 최대폭553.507≤560, 뒤 카드 최대4와 글자 지연을 확인했다. 양쪽 모두 집중 검사이며 저장소 전체 pytest·실제 프로젝트·예약영역 통합 QA는 아직 수행하지 않았다.
최초 `cascade_lines_as_is_to_be_1080p.mp4`의 relation 시안은 §8의 참고다. 그 영상의 depth Y8·4항목 cascade 배치를 최종 규칙으로 복사하지 않는다.

## 7 공통 선과 색상 체계

선의 굵기만 줄여서 Hairline 스타일이라고 부르지 않는다. 정보의 중요도, 실제 출력 크기, 가림 경계의 연속성, 배경 대비를 함께 설계한다. 옅은 색과 강조색은 사용해도 된다.

- 육지는 밝은 회색·흰색, 바다는 푸른색 계열, 강은 얇은 옅은 하늘색이다. 행위자·범주별 절제된 구분색과 의미 있는 강조색도 일관된 토큰으로 허용한다.
- 기존 의미 색은 `ru=#ff5566`, `us=#5aa9ff`, `gold=#e8b860`, `teal=#5cc8da`, `green=#8fd08a`, `muted=#a9b0bd`다. 의미를 재배정하지 않는다.
- 상태를 색 하나에만 맡기지 않는다. 레이블·선 형태·방향 또는 강조 위치를 함께 쓴다. 데모의 sage 단색은 가상 기관에만 적용했으며 실제 국가·행위자 identity palette를 전역 삭제하지 않는다.
- `structural`, `secondary`, `context`, `emphasis`처럼 역할 토큰을 두되 실제 스키마와 명명 관례에 맞춘다. 이 이름들은 제안이다.
- 본문·날짜·필수 라벨은 합성된 실제 배경에서 대비 4.5:1을 목표로 한다. 지도 지형처럼 보조적인 질감까지 같은 대비로 올리지 않는다.
- 필수 도형의 경계·상태 표시는 주변과 3:1을 목표로 하고 실제 인코딩 프레임에서 확인한다. 색상 코드끼리 비교하는 것으로 끝내지 않는다.
- 480p에서 핵심 실선은 최종 출력 최소 약 1px을 출발점으로 시험한다. 보조 선은 얇을 수 있지만 인코딩 후 사라지면 LOD에서 제거하거나 광학 보정한다.
- 픽셀 최소폭 보정은 장치 스케일 변환 지점에 모은다. 각 레이어에서 별도로 720p 배율을 곱하지 않는다.
- 그림자, halo, dash 길이, cap/join은 같은 계열의 컴포넌트끼리 통일한다. 국경·강·도로·서사 경로는 서로 구별된다.

## 8 경로와 패널의 연결선

기존 relation도 1.3초 드로잉과 .75초 간격, 경계 밖 연결, 상태별 실선·점선 및 글자 표기를 이미 제공한다. 현재 기능이 없거나 고장났다는 설명으로 후보를 정당화하지 않는다.

- 후보 relation은 원본 node 위치·edge 시작·상태 앵커를 유지한다. source `R36@(235,262)`, targets `R19@(590,231)/(590,293)`.
- 노드 delay `.4/1.0/1.2초`, edge 시작 `1.6/2.35초`, draw `1.3초`; 거절은 relation local `9.5초` 즉 영상 `18.1초`, fade `.5초`다.
- source port는 `y±12`, `x=sx+sqrt(sr²−12²)+5`; target은 `(dx−dr−6,dy)`. 동일한 수평 접선 cubic, 화살촉 없음.
- 선폭 `1.5→1.6`, port R `2.1`, 거절 dash `[5,4]`. 드로잉 후 `.45초`에 강조가 낮아지고 해당 대상 언급은 local `8.4초`부터 `.4초`간 강조한다.
- 후보 배지는 `.32초` fade로 등장하며 bounce를 제거했다. 실제 연출에서는 고정 데모 시간이 아닌 원래 발화 앵커로 연결한다.

- `routes.py`의 실제 지리 경로와 패널의 관계선을 서로 대체하지 않는다. 위치가 없는 관계를 지도상의 실재 도로로 그리지 않는다.
- 현재 서사 경로의 glow는 축소 후보로 따로 비교한다. 방향, dash, 화살촉, grow, ship, label의 기존 계약은 유지한다.
- Network는 데이터가 지시하는 유향·무향 여부를 따른다. Relation과 Fork도 각각 관계와 대안을 보존한다.
- 선은 노드·배지·텍스트 경계에서 끝난다. 얼굴·글자를 관통하거나 halo가 작은 글자를 덮지 않게 한다.
- 크로싱은 가능한 한 줄이고 정렬된 anchor를 쓴다. 데이터 연결을 삭제·재배열해 의미를 바꾸지 않는다.
- 정적인 구조선은 고정한다. 움직임은 실제 사건 등장·내레이션 강조에 연결하고 불필요한 반복 점멸이나 dash 이동을 피한다.
- 해당 패널의 현재 프리뷰 fixture로 As-is/To-be를 만든다. cascade 한 장면의 성공을 모든 패널 검증으로 보고하지 않는다.

## 9 레이아웃과 충돌 처리

- cascade의 실제 노출 frame·국기 원 geometry를 지도 라벨·배지 회피와 공유한다. 수정 후보에서는 복원된 하단 strip까지 반영해 기존 `cascade_boxes`의 잘린 상자를 그대로 재사용하지 않는다.
- 겹친 카드 전체 원래 사각형을 모두 예약하면 지도가 과도하게 비므로 clip 이후 보이는 영역을 사용한다.
- 문장이 말하는 장소·마커·경로 이름표가 카드 아래에 숨는 경우는 hard 오류를 유지한다.
- 중요하지 않은 배경 지명은 우선순위에 따라 숨길 수 있지만 warning과 provenance에 숨긴 ID·이유를 남긴다.
- 지도 라벨은 stable feature ID, 결정적인 priority, 고정 anchor 후보 순서로 배치한다.
- viewport가 바뀔 때 지난 라벨을 무조건 유지하지 않는다. 짧은 opacity 전환과 진입·이탈 hysteresis를 사용하되 현재 영역 밖은 제거한다.
- 지도 확대 시 지리 좌표는 재투영하고 글자·marker·halo·dash는 화면 기준 크기로 유지한다.
- 모든 이동 프레임에서 실제 글자 extents·halo·여백을 포함한 bbox를 화면 경계와 대조한다. 좌표점이 화면 안이라는 사실만으로 긴 라벨을 허용하지 않는다. anchor 변경·숨김에도 위 안정화 규칙을 적용한다.
- 자막, 날짜 HUD, 출처, 패널과의 충돌을 480/720/1080 모두 검사한다. 지도 제목·stage 설명·범례 같은 고정 UI도 각 상자의 실제 text bounds를 검증한다. 과밀한 정보를 유지하려고 글자만 축소하지 않는다.

## 10 원형 인물과 흔들리는 국기

승인 방향은 사진의 정체성을 유지하면서 얼굴의 크기·여백·국기의 움직임을 정돈하는 것이다.

- 원형 프레임, 인물 사진, 뒤쪽 국기, 파란 accent를 유지한다. 얼굴을 새로 생성하거나 인물을 도형으로 바꾸지 않는다.
- 기존도 `head_popout=false`, `head_inside_max=.9`로 원 안에 들어간다. 후보를 “원형 clipping 신규 구현”이라고 설명하지 않는다.
- 독립 후보는 사진 폭을 `1.72R→2.04R`, 실제 alpha-top을 `−.83R`로 조정했다. 동일 인물의 픽셀을 확대·배치한 것이다.
- 국기는 기존 14 strip, 진폭 `.032×width`에서 후보 96 strip, `.018×width`로 부드럽게 했다. strip 중복이나 빈 줄이 없어야 한다.
- 96 strip은 약 6.9배의 strip 수이며 성능 벤치마크 전이다. 출력 크기 기반 strip 수, 재사용 surface, 준비 단계 캐시를 검토한다.
- 국기 모양·색 영역은 원본을 보존한다. 흔들림이 얼굴 앞을 가리거나 작은 국기 띠를 왜곡하지 않게 한다.
- solo `R=56`, group `R=30–34`의 기존 설계 크기로 각각 확인한다. 큰 시안 하나만 합격시키지 않는다.
- 국장은 별도 badge 종류다. 국기를 흔들 수 있다는 사실로 인물 뒤의 모든 국장 애니메이션이 구현됐다고 주장하지 않는다.
- 기존 자산 credit과 국기 MIT notice를 유지한다. 배경 제거·사진 처리 이력이 있으면 별도로 기록한다.

### 인물 후보의 구체적인 조합

- 국기 중심은 `(0.16R,−0.05R)`, 폭은 `2.3R`; 원 내부로 clip한다. 96 strip의 위상은 `t×2.6+(i/96)×7`, 진폭은 `.018×width`다.
- strip 경계는 겹치거나 비지 않게 나눈다. 원본 국기는 변형 surface를 캐시하고 시간만 바꾸며, face surface를 매 프레임 다시 처리하지 않는다.
- 얼굴 배치는 원본 alpha>20인 최상단 행을 기준으로 계산한다. 정규화의 alpha>40 bbox와 목적이 다르므로 하나의 threshold로 합치지 않는다.
- 후보의 링은 어두운 외곽 `2.4`와 파란 안쪽 `.8` 설계px, 얼굴 분리용 shadow alpha `.16`이다. 최종 출력에서 과한 테두리·흰 머리 주변 halo가 없는지 확인한다.
- 사진은 확대·배치만 바꾸었다. resize에 따른 보간과 인물의 얼굴·정체성 재생성은 구분한다. 대체 사진을 쓰면 비교 양쪽의 출처가 달라진 사실을 표시한다.
- 위 값은 인물용이다. 작은 국기-only cascade 배지에 얼굴용 레이아웃을 통째로 복사하지 않는다.

### 인물이 없을 때의 현실적인 fallback

1. 먼저 기존 library와 entity ID를 찾는다. 이미 준비된 동일 인물 자산을 우선 재사용한다.
2. 없으면 공식기관·라이선스가 확인된 사진을 확보하고 원본 URL·저자·날짜·hash·사용 조건을 보존한다. 닮은 다른 인물을 대신 쓰지 않는다.
3. 기존 [portrait_fallback.py](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/tools/portrait_fallback.py)는 `rembg u2net_human_seg`, alpha blur `.8`, 흑백화, alpha bbox 기준 머리·어깨 정규화를 제공한다.
4. 기존 정규화는 출력 폭420, 높이≤폭×1.22, alpha threshold40이다. 빈 alpha는 오류로 처리하며 정수리·턱·어깨가 과도하게 잘리지 않는지 확인한다.
5. 기존 `v3`와 `engraving` 처리를 비교할 수 있지만 원본 얼굴 구조를 임의로 재해석하지 않는다. hair/eyeglasses·국기 경계·반투명 halo를 실크기로 검수한다.
6. 라이브러리도 없고 처리 결과가 불량하면 검증된 원사진의 원형 crop 또는 명시적인 사진 미확보 표기를 사용한다. 자동 생성된 닮은 얼굴로 사실 자료를 대체하지 않는다.
7. 새 처리의 도구·모델·버전·파라미터를 processing 기록과 credit에 연결한다. 모델 최초 다운로드·로컬 메모리 비용도 계획에 포함한다.

비교에 쓴 투스크 사진은 KPRM의 [원본 사진](https://commons.wikimedia.org/wiki/File:Donald_Tusk_KPRM_(cropped).jpg), CC BY 3.0 PL 기반이다. 폴란드 국기는 [flag-icons](https://github.com/lipis/flag-icons/blob/main/flags/4x3/pl.svg)의 MIT 자산이다. 실제 영상 credit에도 저자·출처·라이선스를 유지한다.

## 11 Hairline에서 필요한 부분만 추출한 자체 재사용 영상 자산 스킬

### 11.1 목표와 원본 확인

목표는 F-35 한 장이나 Hairline 데모 페이지의 복제가 아니다. [Hairline `hairline-create`](https://github.com/lucasmarkes/hairline/tree/main/skills/hairline-create)에서 **영상에 들어갈 그림 자산 제작에 필요한 방법만 선별**하여, `doroper98/osint_generator`의 자체 네이티브 스킬로 만든다. 항공기·방공 장비·함정·시설·일반 장비에 재사용하고 F-35 V2는 그중 한 검증 예시로 둔다.

2026-10-10 읽기 전용으로 확인한 upstream 기준은 [`a2217852fed6d1a4f20bc7d43d4fad1a3de117b8`](https://github.com/lucasmarkes/hairline/commit/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8)이다. 다음 사실과 아래 자체 제안을 구분한다.

- 원본 [`SKILL.md`](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/SKILL.md)는 코드로 pointer 반응형 isometric 선화를 만들고, 고정 kernel·bench를 조합한 단일 HTML로 전달하는 스킬이다. 사진을 정밀 도면으로 변환하는 모델이나 무기 식별 서비스가 아니다.
- 원본 폴더에는 `SKILL.md`, `concepts.md`, `rules.md`, `kernel.js`, `bench.html`, `build.mjs`, `validate.mjs`, `look.md`, `look.mjs`와 `examples/terrain.js`, `examples/riffle.js`가 있다. 별도의 `references/`·`assets/` 폴더, 항공기·무기 도면 라이브러리는 확인되지 않았다. 아래 제안의 `references/` 등은 우리 쪽에서 새로 설계하는 구조다.
- [`kernel.js`의 공개 API 설명](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/kernel.js)은 투영·rounded solid·path·spring/tween·공유 frame loop 등을 제공한다. 이것이 실물 비율·형상·부품 구성을 검증해 주지는 않는다.
- [`validate.mjs`](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/validate.mjs)는 원본 HTML/kernel 계약, 허용된 코드·스타일·입력·시간 처리 등을 검사한다. SVG의 실제 기종 식별 정확도, 라이선스 적합성, 우리 영상 엔진 통합을 판정하는 검증기가 아니다.
- [`look.mjs`](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/look.mjs)는 원본의 8개 상태 이미지 외에 이름을 가린 240px 비교와 motion strip을 만든다. 브라우저용 QA 구현이며 최초 실행 시 `playwright-core`를 캐시에 설치할 수 있다. 이번 조사에서는 설치·실행하지 않았다.
- [`LICENSE`](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/LICENSE)는 MIT, `Copyright (c) 2026 Lucas Marques`다. 출처 자료의 사진·도면·상표 권리는 이 MIT와 별개다.

### 11.2 원본 파일 → 채택·변형·제외 매트릭스

아래는 모두 위 commit의 파일을 기준으로 한다. `채택`은 제작 원칙을 우리 계약에 반영한다는 뜻이며 원본 전체를 복사·설치한다는 뜻이 아니다.

| 원본 파일·규칙 | 결정 | 우리 영상 자산 스킬에서의 처리 |
| --- | --- | --- |
| `concepts.md`의 대상별 2–3개 식별 특징 찾기 | 채택 | 실물 참고자료에서 대상·형식·변형을 확인하고 최소 식별 특징을 먼저 기록한다. 임의의 둥근 상자를 특정 장비라고 부르지 않는다. |
| `concepts.md`의 한 도형·한 아이디어, rest 검토 | 변형 | 영상의 한 shot이 전달할 정보와 정지 상태를 먼저 설계한다. 복합 체계는 단일 장비·여러 구성품을 구분하고 필요한 경우 개별 자산으로 분리한다. |
| `rules.md` 03의 범위 제한·최대 상태 framing | 채택 | 모든 motion keyframe·중간 시점의 실제 stroke bbox가 출력 safe area 안에 있어야 한다. |
| `rules.md` 04의 외곽·강조 선 위계 | 변형 | 공통 영상 토큰으로 outline/structure/detail/focus를 분리한다. 밝은 강조와 옅은 면색은 정보 목적에 따라 허용하되 의미 없는 glow·그림자로 형상을 덮지 않는다. |
| `rules.md` 05의 정지 상태 품질 | 변형 | 정지 화면에서도 바로 식별 가능해야 한다. 원본의 비대칭·기울기 권장을 실물의 대칭·정렬까지 바꾸라는 규칙으로 옮기지 않는다. |
| `rules.md` 06의 불투명 면·뒤에서 앞으로 그리기 | 채택 | 후면 선이 전면 형상을 관통하지 않게 mask/clip/occlusion을 계산한다. 단순 투명 wireframe을 기본으로 쓰지 않는다. |
| `rules.md` 09의 적게 그리기·외곽/내부 선 위계 | 변형 | 불필요한 panel·rivet는 줄인다. 다만 모든 모서리를 둥글게 하거나 모든 물체를 rounded prism·convex hull로 만드는 규칙은 제외한다. 기체 날개, 선박 형상, 건물 모서리 등 실제 식별 특징을 보존한다. |
| `rules.md` 10의 도형 안 과도한 글자 금지 | 변형 | 대상 그림과 caption/callout 레이어를 분리한다. 영상 설명에 필요한 라벨·화살표·체계도 자체를 금지하지 않는다. 존재하지 않는 문자·문양을 장식으로 넣지 않는다. |
| `rules.md` 01·02·08의 pointer hit-test·stagger·두 clock | 변형/제외 | pointer·hover·slider는 기본 산출물에서 제외한다. 필요할 때만 거리/의미에 따른 순차 강조를 timeline으로 옮기고 프레임 시간으로 재현한다. 700ms·spring 상수는 전역 의무값으로 옮기지 않는다. |
| `rules.md` 07의 불필요한 반복 작업 방지 | 변형 | 준비 단계에서 한 번 생성·검사·캐시하고 영상 렌더는 이미 준비된 자산을 읽는다. 매 프레임 모델·네트워크·SVG 재생성 호출을 금지한다. |
| `rules.md`의 400×320, 2:1 camera, 200줄 상한 | 제외 | 영상의 실제 예약영역·시점·출력 해상도에 맞춘다. 모든 대상에 isometric이나 좌우 mirror를 강제하지 않는다. |
| `look.md`·`look.mjs`의 실제 작은 크기·가림·프레임·명암 QA | 변형 | 최종 장면 crop, 240px 및 실제 최소 표시 폭, 밝고 어두운 지도, compact, motion 중간 프레임을 검수한다. 텍스트 코드 검사와 눈으로 보는 검수를 분리한다. |
| `examples/terrain.js`·`examples/riffle.js` | 참고만 | 연속형/분리형 geometry와 paint order의 예다. 실물 장비의 정확한 형상·동작 근거로 사용하지 않는다. |
| `kernel.js`·`bench.html`·`build.mjs`와 React/HTML 배포 계약 | 기본 제외 | 전체 Hairline 런타임을 엔진에 의존성으로 넣지 않는다. 필요한 순수 기하 보조 함수가 실제로 있을 때만 별도 검토 후 최소 단위로 가져오고 출처·MIT 고지를 남긴다. |
| 원본 `validate.mjs` | 대체 | 우리 SVG/manifest/time/render 계약용 검사를 작성한다. 자체 검사 통과를 Hairline 원본 검증기 통과라고 보고하지 않는다. |

원칙의 출처: [concepts.md](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/concepts.md), [rules.md](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/rules.md), [look.md](https://github.com/lucasmarkes/hairline/blob/a2217852fed6d1a4f20bc7d43d4fad1a3de117b8/skills/hairline-create/look.md). 아래 계약·schema·경로는 이 원칙을 영상에 맞게 새로 설계한 제안이며 upstream 기능 목록이 아니다.

### 11.3 제안 경로와 네이티브 SKILL 계약

기준 저장소의 [`.claude/skills/`](https://github.com/doroper98/osint_generator/tree/95a0b917afac00b598116698e494d57dc288cc1b/.claude/skills)에는 `campaign-front-map`, `missile-event-map`이 있다. 이 관례를 따라 다음을 **후속 구현 제안**으로 둔다. 이 문서만 작성한 현재 상태에서는 새 스킬·폴더를 설치하거나 저장소에 생성한 것이 아니다.

```text
.claude/skills/osint-visual-asset-create/
  SKILL.md
  references/source-policy.md
  references/geometry-and-occlusion.md
  references/subject-profiles.md
  references/video-asset-contract.md
  references/qa-and-failures.md
  references/upstream-hairline.md
  templates/asset-manifest.example.json
  templates/geometry-review.example.json
```

- SKILL에는 실행 조건·입출력·필수 순서를 짧게 두고 긴 대상별 기준은 reference 파일로 분리한다.
- 실행 코드는 스킬마다 복제하지 않고 기존 `tools/`·`schemas/`·`tests/` 관례를 확인한 뒤 공용 구현으로 둔다. `references/upstream-hairline.md`는 출처와 변형 이유를 기록하는 문서이며 원본 자동 실행 지시가 아니다.
- 생성된 대상별 그림은 기존 library/media registry 흐름에 넣는다. 스킬 폴더를 대용량 사진·렌더 캐시 저장소로 사용하지 않는다.

제안 `SKILL.md` 골격:

```markdown
---
name: osint-visual-asset-create
description: 공개 출처를 확인하여 OSINT 영상용 장비·시설의 선화 자산을 제작하거나 수정할 때 사용한다. 항공기, 차량·복합 체계의 구성품, 함정, 시설, 일반 장비에 대해 검증 가능한 형상, 가림, 크기별 정지·선택형 애니메이션 자산과 출처 기록을 만든다.
argument-hint: "[subject/variant] [view] [target-size] [static|animated]"
---

# OSINT visual asset create

## Trigger and scope
실물 기반 설명용 그림의 신규 제작·수정·크기별 변형 요청에 사용한다.
사진의 인물 정체성 편집, 지리 데이터 생성, 관계 증거 추론, 무기 운용·제작 설계에는 사용하지 않는다.
F-35 예시 geometry를 다른 종류의 대상에 재사용하지 않는다.

## Required input
대상 ID·정확한 형식, 출처와 권리, 시점·상태, 표시 크기·배경,
식별 특징, 정확도 등급, 정지/동작 범위, 출력 위치를 확인한다.
알 수 없는 값은 unknown으로 남기고 영향이 큰 항목만 질문한다.

## Read only what is needed
source-policy → 해당 subject profile → geometry-and-occlusion →
video-asset-contract → qa-and-failures 순으로 필요한 문서를 읽는다.

## Workflow
1. 공개 원자료·형식·촬영/작성 시점·권리를 확인한다.
2. 특징과 비율을 먼저 정하고 검토 가능한 geometry를 만든다.
3. 가림·접합부·빈 공간·부품 순서를 검증한다.
4. 영상 토큰으로 선/면을 적용하고 크기별 LOD를 만든다.
5. 정지 자산을 먼저 통과시킨 뒤 요청된 동작만 추가한다.
6. 실크기·배경·시간 중간 상태를 검사하고 registry/credits로 전달한다.

## Output and stop conditions
SVG master, 필요한 PNG/compact/theme 변형, manifest, QA 결과를 제공한다.
애니메이션 요청 시 motion contract와 확인용 영상/프레임을 추가한다.
형식 불명, 권리 미확인, 식별 특징 오류, 가림 오류, 재현성 실패는 완료로 보고하지 않는다.
출처 기반 편집용 그림과 정밀 도면을 구분하고 미확인 부분을 명시한다.
```

### 11.4 입력·출력 데이터 계약

아래 필드는 **새 계약 제안**이다. 기존 `schemas/media_models.py`·registry 필드를 조사한 뒤 중복 여부를 검토하고 실제 schema와 연결한다. 현재 함수가 이미 받는 인자처럼 사용하지 않는다.

| 입력 | 계약 |
| --- | --- |
| `subject` | `entity_id`, `class`, `name`, `variant`, `configuration`, `reference_date`; 형식·구성 미확인은 명시한다 |
| `sources[]` | 원문 URL, 발행자/저자, 자료 시점, 확인일, 파일 hash, 권리·허용 용도, 어떤 특징을 뒷받침하는지 |
| `view` | top/side/front/oblique/isometric 중 목적에 맞는 시점, 좌표계, 투영 방법, 카메라 방향; 한 장의 사진만으로 숨은 면을 확정하지 않는다 |
| `geometry` | 기준 길이·비율과 출처, 식별 특징 2–3개 이상, 생략 가능한 세부, symmetry 적용 가능한 부품, 알려지지 않은 부분 |
| `presentation` | 실제 `target_width_px`·height/bbox·safe area, 최소 표시 폭, 배경별 profile, 기존 스타일 토큰 ID, caption 공간 |
| `motion` | `none` 또는 허용된 reveal/emphasis/camera/part 동작, duration, fps, cue ID, 시작·종료 상태; 기계적으로 검증되지 않은 동작을 실물 동작처럼 보이지 않게 한다 |
| `accuracy` | `generic` 또는 `reference-audited-editorial`; 생성 방식과 정확도는 별개다. 두 등급 모두 engineering-grade를 뜻하지 않는다 |

필수 출력:

- 수정 가능한 SVG master와 geometry 작성 원본. SVG 안에는 외부 네트워크 리소스·스크립트·불필요한 래스터 그림을 포함하지 않는다. 래스터를 의도적으로 포함한 별도 경우는 manifest에 공개한다.
- 필요한 투명 PNG, compact, dark/light 변형. PNG는 SVG에서 파생되며 수정 원본 역할을 하지 않는다.
- manifest와 geometry review: 대상·시점·source hash·생성기 버전·스타일/LOD·bbox/anchor·정확도 한계·권리·수정 이력을 기록한다.
- QA: 최종 크기·실제 장면 crop·이름을 가린 식별 확인·가림 확대 이미지와 `pass/fail/not_run` 결과. 동작이 있을 때는 주요 시점 contact sheet와 decode한 검토 영상을 추가한다.

제안 manifest의 최소 구조:

```json
{
  "schema_version": "osint.visual-asset.v1-proposal",
  "asset_id": "<entity>-<variant>-<view>-v001",
  "subject": {"entity_id": "<id>", "class": "equipment", "variant": "unknown"},
  "source_refs": [{"url": "<verified URL>", "sha256": "<hash>", "rights": "<verified terms>", "supports": ["silhouette"]}],
  "view": {"projection": "orthographic", "orientation": "side"},
  "accuracy": {"grade": "generic", "unknowns": ["awaiting reference review"], "review_record": "geometry-review.json"},
  "geometry": {"source": "geometry-source", "sha256": "<hash>", "symmetry_scope": []},
  "style": {"profile": "<existing-token-profile>", "version": "<version>"},
  "variants": [{"lod": "compact", "theme": "dark", "file": "master-compact-dark.svg", "min_tested_width_px": 240}],
  "placement": {"anchor": [0.5, 0.5], "safe_bbox": [0, 0, 1, 1]},
  "motion": null,
  "provenance": {
    "skill_version": "<version>",
    "renderer_version": "<version>",
    "hairline_upstream_commit": "a2217852fed6d1a4f20bc7d43d4fad1a3de117b8",
    "adopted_source_rules": ["concepts:identity-features", "rules:06", "look:small-size"],
    "generation_method": "authored-vector"
  },
  "qa": {"mechanical": "not_run", "reference_review": "not_run", "visual": "not_run", "video_decode": "not_applicable"}
}
```

예시의 240px는 Hairline에서 가져온 보조 검사 폭이다. 실제 영상에서 더 작게 표시하면 그 폭도 검사하고 `min_tested_width_px`에 실제 최솟값을 기록한다. `reference-audited-editorial`은 geometry review가 실제로 통과한 뒤에만 설정한다.

### 11.5 공통 제작 순서: 출처 → geometry → 가림 → 스타일 → 자산 → 실크기 QA

1. **참고자료 확인:** 공식기관·제조사·신뢰할 수 있는 공개 자료를 우선한다. 정확한 variant와 시점·장비 상태를 맞추고, 가능하면 서로 다른 각도의 자료를 교차 확인한다. 치수 수치와 해당 수치의 기종·구성을 함께 묶는다. 출처 없는 검색 미리보기·생성 이미지는 실물 geometry의 근거가 아니다.
2. **형상 설계:** silhouette와 주요 비율을 먼저 승인 가능한 그림으로 만든다. 특징마다 근거를 기록하고 불확실한 panel·개구부를 꾸며 넣지 않는다. 선 굵기·색·광택을 조정하기 전에 형태를 확인한다. 투영이 다른 사진의 픽셀 비율을 그대로 실제 제원 비율로 쓰지 않는다.
3. **가림·접합:** part graph와 앞뒤 순서를 작성한다. 가려진 선을 mask/clip하거나 노출 구간만 그린다. concave 형상을 임의의 convex hull로 바꾸지 않는다. 회전·부품 이동으로 깊이가 바뀌면 해당 시간의 가림도 갱신한다.
4. **스타일 적용:** 외곽은 가장 명확하게, 구조선은 낮게, 세부선은 제한적으로 쓴다. 강조색과 옅은 면색은 장면의 의미에 묶는다. 작은 출력에서는 선을 단순 축소하는 대신 detail을 줄이고 필요한 stroke를 보정한다. 인식에 필요한 sharp corner는 보존한다.
5. **정지/동작 출력:** 정지 master를 먼저 통과시킨다. 정지 그림이면 불필요한 움직임을 넣지 않는다. 요청된 reveal·부품 강조·카메라 움직임만 발화 cue와 연결하고, 이미 검증된 geometry를 시간에 따라 보이게 한다.
6. **실크기 확인:** master 확대 화면만 보고 끝내지 않는다. 실제 지도/카드에 합성한 최종 크기, compact, 명암 변형, 작은 투명 경계, decode된 동작 중간 프레임을 확인한다. 중요한 silhouette를 알아보지 못하면 세부를 더 추가하기보다 비율·시점·LOD를 수정한다.

**투명 외곽과 내부 가림은 별개다.** 배경색 면으로 후면 선을 덮은 SVG는 같은 색의 배경에만 자연스럽게 맞는다. 임의의 지도에 얹는 변형은 후면 stroke를 실제로 clip/mask해 숨기거나 의도된 재질 면을 사용한다. light/dark 면색 변경만으로 완전한 범용 투명 합성이 해결됐다고 가정하지 않는다.

### 11.6 대상별 profile과 일반화 경계

| 대상 | 식별·구성 확인 | 시점/geometry 규칙 |
| --- | --- | --- |
| 항공기 | 정확한 기종·variant, 날개·꼬리·흡입구/캐노피 등 핵심 특징, 외부 장착 상태 | top/side/oblique 중 목적에 맞게 선택한다. 실제로 대칭인 부품만 공통 master에서 반사한다. perspective·안테나·급유 장치·비대칭 장착물을 무조건 반사하지 않는다. |
| S-400 등 복합 체계 | 전체 체계인지 특정 발사차·레이더·지휘 차량인지 먼저 구분한다. 서로 다른 구성품 사진을 한 장비의 부품처럼 합치지 않는다. | 검증된 개별 구성품부터 만든다. 포대 전체를 표현해야 하면 별도 자산과 설명 레이아웃으로 구성한다. 보유 수량·차량 배치·전개 상태를 사진 하나에서 추정해 사실처럼 고정하지 않는다. |
| 함정 | 함급·개별 함정·개장 시점, 선체·상부구조·마스트 등 식별 특징 | 측면/상면/사선 중 선택한다. 좌현/우현 장비·갑판 배치가 다를 수 있어 전체 mirror 금지다. 작은 크기의 창문·해치보다 선체 비율과 주요 상부구조를 우선한다. |
| 시설 | 특정 시설의 공개 외관인지 일반적 시설 유형인지 구분, 건물군·지붕·주요 설비 확인 | 실제 시설은 확인된 공개 외관만 반영한다. 알 수 없는 내부 구조·지하 공간은 만들지 않는다. 실측 배치도와 설명용 axonometric 그림을 구분한다. |
| 비군사 일반 장비 | 차종·제품형·기계 상태, 차대·차륜·암·패널 등 주요 구조 | 굴착기·크레인·화물차·레이더와 무관한 산업설비 등에도 같은 출처/geometry/가림/QA 절차를 적용한다. 원형·유기형·비대칭 구조에 rounded-box 문법을 강제하지 않는다. |

위 표는 새로운 대상별 검토 기준 제안이다. 이번 조사에서 해당 모든 대상의 자료를 수집하거나 자산을 제작·검증한 것으로 표현하지 않는다. F-35의 좌우 mirror·top-view·날개비 수치를 이 공통 profile의 기본값으로 올리지 않는다.

### 11.7 모델·프롬프트와 결정적 SVG의 역할

- 좋은 프롬프트는 실물 정확성을 보증하지 않는다. 이미지 모델이 그럴듯한 날개·발사관·장비 수를 만들거나 서로 다른 variant를 합성할 수 있다. 생성 결과의 vector tracing도 그 오류를 그대로 보존할 수 있다.
- 코드로 작성한 SVG는 좌표·선·가림·수정 이력과 재현성을 통제하기 쉽다. **결정적이라는 사실은 정확하다는 뜻이 아니다.** 틀린 비율도 항상 똑같이 렌더될 수 있으므로 출처 기반 검토가 별도로 필요하다.
- 기본 경로는 유료 이미지 API 없는 수작업/코드 기반 vector master다. 이미 사용할 수 있는 이미지 모델을 rough style 탐색에 쓰더라도 출처·변형·geometry 검토를 대체하지 않는다. 요청에 없는 유료 API 호출·서비스 가입·모델 설치를 전제하지 않는다.
- 프롬프트나 모델이 사용됐다면 도구·모델 버전·입력 자료·prompt hash/내용의 보관 위치·수정 이력을 provenance에 기록한다. API가 seed를 지원하지 않으면 seed 재현을 약속하지 않는다. 최종 채택 geometry를 파일과 hash로 고정한다.
- 정확한 variant를 확인할 수 없으면 `generic`으로 표시하거나 제작을 보류한다. 일반적 그림을 특정 실물의 검증된 도해라고 등록하지 않는다.

### 11.8 영상 시간 계약·캐시·기존 렌더 통합

- `render_at(t)` 또는 `frame_index/fps` 기반의 순수 시간 평가를 **제안 계약**으로 둔다. 같은 입력·t·버전이면 같은 geometry·alpha·transform을 내며 frame 순서, wall-clock, pointer, RAF, 이전 프레임 누적 상태에 의존하지 않는다.
- spring이 필요하면 해석적 시간 함수 또는 고정 timestep의 사전 계산·저장 결과를 쓴다. 영상 encoder가 프레임을 건너뛰거나 병렬 계산해도 다른 결과가 나오지 않아야 한다. Hairline의 DOM 공유 loop를 그대로 영상 시간축으로 쓰지 않는다.
- SVG authoring과 영상 render를 분리한다. 준비 단계에서 자료 확인 → geometry/변형 생성 → QA → 고정된 registry 자산을 만든다. 실제 프레임에서는 캐시된 surface 또는 사전 준비된 time geometry만 합성한다.
- 캐시 키에는 source hash, geometry hash, skill/generator version, style version, view, LOD, theme, 출력 크기·scale, motion 버전을 포함한다. geometry·권리·스타일이 바뀌면 관련 캐시와 QA를 무효화한다. `asset_id`만으로 오래된 결과를 재사용하지 않는다.
- 기존 `assets/library/library_manifest.json`, `assets/media/media_registry.json`, `assets/entities.yaml`의 역할을 유지하고 `engine/media_registry.py`, `schemas/media_models.py`, `engine/credits.py`와 연결한다. 새로운 독립 registry를 먼저 만들지 않는다.
- `engine/layers/media.py`의 `draw_cutout`이 현재 지원하는 형식·bbox·배치·shadow를 확인한다. SVG 직접 지원이 없으면 준비 단계에서 변형별 PNG로 rasterize하여 기존 정적 경로를 우선 이용한다. SVG 이름만 넣어서 작동한다고 가정하지 않는다.
- 애니메이션은 실제 엔진의 시간·예약영역 계약을 따르는 선택형 adapter로 연결한다. 기존 caption·scale·position·safe area를 깨지 않는다. outline reveal은 모든 장비 등장에 자동 반복하지 않고 발화와 정보 필요에 따라 사용한다.
- 준비된 자산의 오프라인 렌더를 기본 합격 조건으로 둔다. 최초 도구·폰트·rasterizer 다운로드 여부와 저장공간/렌더 시간을 분리해 기록한다. 외부 서비스 요금이 없다는 것과 로컬 연산 비용이 없다는 것을 혼동하지 않는다.

### 11.9 검증·실패 처리·라이선스·업데이트

필수 검증은 한 묶음으로 정의하되 각각 결과를 따로 남긴다.

1. **구조 검사:** schema 필수 필드, 파일/hash 일치, SVG 유효성, NaN/빈 path/예상 밖 외부 URI, 유효 alpha bbox, clipping·anchor·safe area, registry·credit 연결을 검사한다.
2. **출처/형상 검사:** 대상·variant·자료 시점·권리와 2–3개 식별 특징을 교차 확인한다. 치수 비율의 허용 오차는 출처 신뢰도·투영·그림 목적에 따라 리뷰에 정의한다. 근거 없는 전 대상 공통 정밀도 수치나 자동 합격 점수를 만들지 않는다.
3. **시각 검사:** 전체/compact, 실제 최소 표시 폭 및 240px, dark/light와 실제 지도 배경, 이름을 가린 silhouette, 날카로운 각·교차선·접합부·가림·alpha halo를 확인한다. 텍스트 validator 통과만으로 시각 합격을 선언하지 않는다.
4. **동작 검사:** 시작·끝·keyframe과 동작 중간에서 bbox/가림/연결 상태를 확인한다. reveal 중 내부 선이 먼저 떠다니거나 선이 깜빡이는지 본다. 같은 t를 순차·역순·임의 순서로 렌더해 동일 결과인지 검사한다.
5. **회귀 검사:** F-35 하나 외에 차량/복합 체계 구성품, 함정, 시설, 비군사 비대칭 장비 fixture를 추가한다. 서로 다른 profile이 동일한 kernel 규칙으로 뭉개지지 않는지 검증한다. 아직 없는 fixture는 `not_run`으로 둔다.
6. **최종 영상 검사:** 실제 출력 해상도·fps로 짧게 렌더하고 인코딩 후 decode해 선 소실·압축 떨림·caption 충돌을 확인한다. SVG QA, 독립 preview QA, 본 엔진 통합 QA를 분리해 보고한다.

실패 시에는 권리·variant 불명, 형상 오류, 가림 오류, 작은 크기 식별 실패, 재현성 실패를 각각 기록하고 해당 단계로 돌아간다. 얇은 선을 무조건 굵게 만들거나 생성 재시도를 반복해 형태 오류를 감추지 않는다. 시간 제한으로 검수를 못 했으면 미검증 preview로 남기고 승인된 production asset을 덮어쓰지 않는다. 이전 승인 버전으로 되돌릴 수 있도록 버전·hash를 보존한다.

Upstream 및 권리 관리:

- `references/upstream-hairline.md`에 commit, 원본 파일 목록, 채택 규칙, 변형 이유, 제외 항목과 확인 날짜를 기록한다. 내용을 복사한 파일·함수·상당한 문서 부분은 경로별로 추적한다.
- Hairline의 코드·문서를 복사하거나 상당 부분을 변형해 배포한다면 저장소의 기존 notice 관례에 맞춰 원본 MIT 저작권·허가 고지 전문을 동봉한다. `THIRD_PARTY_NOTICES.md` 및 license 파일 추가는 기존 구조 확인 후 정하는 **제안**이다. 단순 링크만으로 고지 의무를 대신했다고 가정하지 않는다.
- 참고 사진·도면·폰트·상표의 권리는 각자 확인한다. Hairline의 MIT가 해당 자산의 사용권·사진 재배포·상표 사용을 허용하는 것은 아니다. 원자료 credit과 코드 notice를 분리해 유지한다.
- 버전은 commit에 고정하고 `main`을 자동으로 따라가지 않는다. 변경을 도입할 때 원본 diff·라이선스·필요한 규칙만 검토하고 자체 fixture 회귀와 캐시 무효화 후 갱신한다. upstream skill을 자동 설치·자동 실행하는 updater를 만들지 않는다.
- 검토한 Hairline 문서와 코드 사이의 세부 차이도 기록한다. 예를 들어 현재 `look.mjs`에는 `look.md`의 8개 상태에 더해 blind/motion 출력이 있다. 문서 설명만으로 실제 실행 기능을 단정하지 않는다.

### 11.10 기존 F-35 결과의 위치

F-35 V2는 이 스킬의 형태·가림·compact·명암 QA를 점검할 **하나의 acceptance fixture**다. 기존의 V1/V2 시점 차이, 공개 제원 근거, 대칭 적용 범위, 실제 출력 stroke와 검증 상태를 다음 하위 항목에 보존한다. 이 예시가 완성됐다고 재사용 스킬·다른 대상 profile·원본 Hairline 검증·엔진 통합·V2 애니메이션까지 완료됐다고 보고하지 않는다.

### 11.11 F-35 V2 geometry와 크기별 광학 보정

- V2는 V1의 비스듬한 시점에서 대칭적인 top-view로 바꾼 편집용 그림이다. 같은 각도의 단순 수정이나 정밀 설계도라고 설명하지 않는다.
- 날개·수평꼬리·기울어진 수직꼬리는 한쪽 master를 중심선에 정확히 반사한다. 좌우를 따로 눈대중으로 그려 비대칭 오차를 만들지 않는다.
- 날개 leading/trailing edge는 참고자료에 맞는 직선이며, forebody·canopy는 접선이 자연스럽게 이어지는 cubic Bézier다. 전투기의 특징적인 각을 둥글게 덮지 않는다.
- 길이1000 drawing units 기준 span은 `1000×10.7/15.7≈681.529`이다. 수평꼬리 span은 공식6.86m 자료를 참고한다. 참고자료가 초기 render임을 함께 적고 정밀 도면으로 주장하지 않는다.
- 날개 root·꼬리 연결부는 opaque 면으로 가리고 노출 edge를 한 번만 그린다. 캐노피 highlight 중복·부유한 panel·가짜 rivet은 제거한다.
- 기본 stroke는 outline1.65, structure1.05, detail.8, focus1.85 drawing units다. compact는 detail을 숨기고 outline3, structure1.65, focus3.2로 보정했다. 최종 출력px와 같은 단위가 아니다.
- V2 SVG intrinsic size는1600×1100이며, 사용 예의225px 또는 검토용240px 기체 폭에서 읽힘을 확인한다. 단순 SVG 축소가 compact 검증을 대신하지 않는다.
- dark와 ivory는 occlusion 면 색도 함께 바꾼다. 투명 외곽 SVG에 어두운 내부 면이 있다는 이유로 밝은 지도에 그대로 얹으면 검은 덩어리가 될 수 있다.
- V1의5초 선 reveal은 outline→crease→canopy 순서의 참고 영상이다. V2 기체에 맞춰 다시 만들지 않았으므로 V2 애니메이션으로 재사용했다고 보고하지 않는다.
- 실제 공개 제원 출처: [USAF](https://www.af.mil/About-Us/Fact-Sheets/Display/Article/478441/f-35a-lightning-ii-conventional-takeoff-and-landing-variant/sf2589626/f-35a-lightning-ii/), [Lockheed Martin Fast Facts 2020](https://www.lockheedmartin.com/content/dam/lockheed-martin/aero/documents/F-35/Fast_Facts_May_2020.pdf). 사진 교차 확인: [DVIDS 4177004](https://www.dvidshub.net/image/4177004).

## 12 전 세계 지도 구조

카메라·스타일·데이터 공급자를 분리한다. 한국과 우크라이나를 하드코딩한 하나의 함수로 확장하지 않는다.
기존 [MercatorStage](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/stage.py#L98)에도 ADM1·도시 LOD가 있다. 현재는 경도 폭 기준 ADM1 24→14°, 이름<8.5°, 도시60/25/12/5°·최대18개다. 새 작업은 이를 국가 독립적인 m/px 기반·연속 확대 체계로 개선하는 것이다.
`geo/prep.py`·`geo/prep_geometry.py`·`geo/prep_tiers.py`의 기존 프로젝트별 데이터 준비·terrain tier를 확장한다. 일반 도로 자동 레이어와 강·호수 렌더 통합은 추가 범위이며 `routes.py`의 사건 경로가 이를 대신하지 않는다.

1. 준비 단계에서 카메라 전체 이동 경로의 가시 영역과 여유분을 계산한다.
2. 공급자·국가별 어댑터로 데이터와 출처를 확보하고 schema·coverage·geometry를 검증한다.
3. 원본과 렌더용 단순화 geometry를 분리해 저장하고 immutable manifest와 content hash를 만든다.
4. 렌더 단계는 준비된 캐시만 사용한다. 프레임마다 네트워크 API·공개 타일 서버를 호출하지 않는다.
5. terrain·bathymetry → coast·hydrography → admin → roads → national borders → labels → events/UI를 기본으로 검토한다. 국경을 도로·행정선보다 위에 그려 지워지지 않게 하고, 실제 합류·해안 접점의 선 중복을 명시적으로 처리한다.
6. 상세도가 부족하면 확인된 낮은 LOD를 유지하고 한계를 드러낸다. 존재하지 않는 경계·도로·고주파 지형을 생성하지 않는다.

## 13 지형과 해저 해상도

- [Natural Earth](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/)의 `10m`은 1:10,000,000 지도 축척이다. 지상 10m 해상도가 아니다.
- [ETOPO 2022](https://www.ncei.noaa.gov/products/etopo-global-relief-model)는 15/30/60 arc-second 제품이 있다. 이번 지역 데모는 30 arc-second다.
- [GEBCO](https://www.gebco.net/data-products/gridded-bathymetry-data)는 대안인 전 지구 15 arc-second 격자를 제공한다. 데모에서 사용한 것으로 쓰지 않는다.
- 15 arc-second는 적도 남북 방향 약 463m 간격이며 경도 방향은 위도에 따라 달라진다. 격자 간격을 균일한 실측 정확도로 표현하지 않는다.
- [Mapzen Terrain Tiles](https://registry.opendata.aws/terrain-tiles/)는 지역별 원천 DEM이 섞인다. tile zoom·표본 간격·원천 해상도를 각각 기록한다.
- Terrarium 해독은 `R×256+G+B/256−32768m`다. z를 높여도 원천 데이터가 더 정밀해지는 것은 아니다.
- DEM을 현재 viewport에 재표본화하고 현재 지상 pixel spacing에 맞춰 음영을 계산한다. 완성된 넓은 지도 PNG만 확대하지 않는다.
- 육지는 밝은 회색 높이 톤, 해저는 푸른색 깊이 톤과 별도 hillshade를 쓴다. 지형 대비를 낮게 유지해 선·라벨을 읽을 수 있게 한다.
- 데모 광원은 방위각 315°, 고도 42°, 육지 exaggeration 2.7→1.7이다. 실제 지형에 없는 산을 추가해 지역 간 인상을 맞추지 않는다.
- 각 DEM의 vertical datum, nodata, coastline mask, 육지/바다 경계 이음새를 기록·검사한다. 항해·수심 측정용이 아니다.

## 14 국경과 행정구역

- 주 대상 국가뿐 아니라 viewport에 들어오는 주변 국가의 검증된 국경을 계속 보이게 한다.
- 국가 경계는 짙은 실선으로 행정경계·도로보다 분명해야 한다. 확대 중 갑자기 사라지거나 대상국만 고립되지 않게 한다.
- 육지 마스크, 국가별 관할 경계, 분쟁·주장 경계, 군사 통제선을 서로 다른 자료와 의미로 관리한다.
- Natural Earth의 de facto 속성을 국제적으로 인정된 경계나 현재 점령선으로 조용히 대체하지 않는다.
- [geoBoundaries](https://www.geoboundaries.org/index.html) `gbOpen`은 국가별 제공 단계·원본 연도·경계 의미·개별 출처를 확인한 뒤 사용한다. 전 국가 ADM2의 동일한 품질·최신성을 가정하지 않는다.
- `source_admin_level`과 표시에 쓰는 `display_level`을 분리한다. OSM admin_level, 군·구·시, raion을 세계 공통의 동일 단위로 취급하지 않는다.
- 최신 공식 공개자료나 OCHA COD-AB가 적합하면 지역 어댑터에서 우선한다. 예를 들어 우크라이나는 개편 이전 2006 ADM2 대신 OCHA 2025 자료를 사용했다.
- 화면 출처와 manifest에 기준 연도를 표시한다. 한국 데모의 2018 행정자료를 최신 경계라고 부르지 않는다.
- 공통 경계의 중복 stroke, 단순화로 생긴 틈·교차·섬 소실을 검사한다. 원본 geometry는 보존한다.

### 해안선과 국가 사이 경계를 분리하기

- 우크라이나 V3에서 확인한 오류: OCHA ADM0 polygon의 내부 ring인 시바시 수면 경계와 일부 외곽 해안이 짙은 국제국경 stroke로 처리됐고, 물 구멍 안에 Natural Earth의 잘못된 크림 분할선 조각도 남았다.
- 일반화된 Natural Earth 해안과의 `.08°` 거리 비교로 상세 OCHA 해안을 제거하려 했으나 복잡한 내부 해안·석호를 충분히 분류하지 못했다. 단순히 buffer를 더 넓혀 선을 지우는 방식으로 해결하지 않는다.
- land mask의 polygon boundary 전체를 국가 사이 경계로 사용하지 않는다. outer ring·hole에는 해안·호수·석호뿐 아니라 enclave나 제외 관할도 있을 수 있다. 모든 hole을 물로 보거나 국경이 될 수 없다고 일반화하지 않는다.
- 운영 데이터는 `international_land_boundary`, `administrative_boundary`, `coastline`, `inland_water_shore`, `inland_water`, `disputed_claim`, `operational_control`처럼 의미를 분리한다. 마지막 두 범주는 자동으로 그리지 않는다. 강을 따라가는 실제 국경은 출처가 지시한 경계로 보존한다.
- 가능한 경우 검증된 경계 line layer·이웃 국가 관계를 사용한다. 서로 다른 해상도의 polygon 두 개를 근접도만으로 붙여 정치적 경계를 새로 만들지 않는다.
- 해안·섬·석호는 실제 수계 geometry로 계속 보존하고, 밝고 얇은 coast/water 스타일로 표현한다. 잘못된 국경을 지운다는 이유로 실제 지형을 빈 공간으로 만들지 않는다.
- 시바시·페레코프·크림의 regression crop과 다른 군도·삼각주·석호·복잡한 해안 지역을 확인한다. 우크라이나 내부의 잘못된 분할선, 새로 생긴 틈, 실제 국제 경계 누락을 함께 검사한다.
- V3 진단 bbox `[32.4,44.2,37.5,47]`에서 짙은 선 길이13.784 coordinate-degree 중13.612가 OCHA outline, .172가 NE 잔여선이었다. 이 수치는 좌표계 진단량이며 km 단위 거리로 읽지 않는다.
- V4는 우크라이나 관련 NE 선을 교체하고, 실제 국경의 양 끝을 대응시킨 OCHA 북쪽 exterior arc를 사용한다. 다른 국가들은 명시적인 양국 공통 육상경계를 쓴다. 해안 거리 buffer로 국경 여부를 분류하지 않는다.
- 이 데이터의 시바시 ring은 feature crosswalk로 확인한 뒤 inland_water와 inland_water_shore로 분리한다. NE feature `Syvash`, `Alkaline Lake`, `ne_id=1159126643`와 교차 확인했다. [NASA의 시바시 설명](https://science.nasa.gov/earth/earth-observatory/sivash-ukraine-47117/)도 지역 식별 근거다.
- V4 수면에는 실제 섬 polygon 132개를 hole로 보존해 authoritative 우크라이나 육지와의 fill 교차를0으로 확인했다. 수면·섬 topology를 보존하며 국경이 아닌 선만 올바른 스타일로 바꾼다.
- 이 northern-arc 추출은 해당 OCHA/NE 버전에 맞춘 우크라이나 adapter다. 세계 모든 국가를 북쪽 arc로 처리하는 규칙으로 일반화하지 않는다. 두 자료의 끝점 차이는 서쪽 약1.08km·동쪽 약.70km로 남아 있어 원천 일반화 한계를 표시한다.

## 15 강과 도로의 구별

- 강은 검증된 centerline·수면 polygon을 쓴다. 소스가 centerline이면 임의의 실제 강폭을 암시하는 수면 polygon을 만들어내지 않는다.
- 넓은 화면에서는 큰 강만, 가까이서는 검증된 지류·호수·저수지를 늘린다. 합류점과 해안 연결을 가능한 한 연속되게 유지한다.
- 도로는 얇은 실선, 행정경계는 얇은 회색선, 강은 얇고 옅은 하늘색선이다. 국가 경계가 가장 분명하다. 강을 굵은 이중 채널로 강조해 복잡하게 보이게 하지 않는다.
- 지도 도로와 강은 단일 stroke로 그린다. 최신 시안처럼 흰 casing·이중 band를 없애고, 굵은 선이나 glow 때문에 지도가 복잡해지지 않게 한다.
- 지역에 맞게 motorway/trunk/primary 등의 display class를 정한다. 한국의 고속도로 중심 설정을 다른 지역에 그대로 복사하지 않는다.
- 공개 [OSM 타일 서버](https://operations.osmfoundation.org/policies/tiles/)를 영상용으로 bulk download하지 않는다. 장기 구현은 허용된 지역 PBF 추출물·자체 캐시를 사용한다.
- 소규모 탐색용 Overpass 결과를 전 세계 운영 데이터 파이프라인으로 취급하지 않는다. 스냅샷·coverage·요청 정책·rate limit을 기록한다.
- [OSM attribution과 ODbL](https://www.openstreetmap.org/copyright)을 화면 credit과 배포 데이터에 반영한다. 렌더 영상과 파생 데이터베이스 의무를 구별한다.
- 도로 geometry는 존재·통행·안전을 보증하지 않는다. 도시끼리 임의로 연결한 선을 도로처럼 표시하지 않는다.

### 우크라이나 V4의 스타일과 검증

- 파일: `ukraine_east_zoom_demo_v4.mp4`, 1280×720, 30 fps, 20초 무음 독립 시안. V3의 얇은 선·푸른 수계 스타일은 유지하고 위의 국경·해안 의미 오류를 수정한다. V2의 굵은 수계와 점선 경계를 되살리지 않는다.
- 선폭은 720p의 명목상 screen px이며 RGB·alpha는 0–255다. 2배 supersampling에서 선폭이 반 픽셀 단위로 반올림된 뒤 축소되므로 실제 소형 표현을 확인한다. 480 설계 좌표에 그대로 복사하지 않는다.
- 국경: 실선 `1.15px`, RGB54/54/54, alpha230. ADM1: 실선 `.55px`, gray151/alpha108; ADM2: 실선 `.45px`, gray170/alpha76.
- 행정 LOD: ADM1 m/px `1600에서 없음→900에서 완전`, ADM2 `430에서 없음→325에서 완전`. 좁은 화면에 경계를 한꺼번에 쏟아 넣지 않는다.
- 도로: casing 없는 얇은 실선. primary `.50px` gray119/alpha150, trunk `.65px` gray91/alpha185, motorway `.80px` gray73/alpha205.
- 강: casing 없는 단일 하늘색 RGB135/183/208. major `.70+.15×ADM1_LOD px`/alpha225; secondary `.60px`/alpha`185×ADM1_LOD`; minor `.50px`/alpha`145×ADM2_LOD×.65`.
- 바다: 기존 해저 음영 밝기 `g`를 RGB`(g−21,g−5,g+8)`로 바꾸고0–255로 제한한다. 예를 들어g190은RGB169/185/198이다. 육지에는 이 변환을 적용하지 않는다.
- source geometry·카메라·인정 국경 정책을 보존하되 국경선 추출 오류는 별도로 수정한다. 이전 V3의 광범위한 거리 buffer로 해안을 제거하는 방법은 전 세계 운영 정책으로 채택하지 않는다. 아래의 해안·국경 의미 구분을 우선한다.
- 행정 shared edge는 원본 union·merge 후 `.0005°`로 단순화한다. ADM1 65개·ADM2 233개는 merged line 개수다. 강은 실제 일반화 centerline의 두 번 Chaikin smoothing이며 실측 강폭·최신 저수지 면적을 표현하지 않는다.
- 도로는 OSM bbox `[34.8,46.4,41,49.5]` 전체 viewport coverage gate를 유지한다. 지역별 degree gate는 운영에서 지상·화면 단위로 정규화한다.
- 국가 라벨은 이 장면의 주요 5개이며 6px text-bounds guard를 유지한다. 최종20.000초·600프레임 전체 decode 오류0, 지리 라벨7,471개 bounds 위반0, 도로 표시152프레임 coverage 누락0을 확인했다.
- V4 의미 검사: 국경 feature73개(다른 국가의 양국 경계72개+OCHA 육상경계 arc1개), 시바시 수면1개와 섬 hole132개, multipart shore1개다. 시바시 shore와 국경의 교차0, 진단 Crimea/Azov bbox 안 잘못된 국경 길이0, 수면과 OCHA 육지 교차0을 확인했다. 끝점과 최종 decode 프레임도 시각 검수했다.

## 16 확대와 정보량 제어

- LOD 기준은 위도·viewport를 반영한 meters per pixel 또는 동등한 명시적 zoom metric이다. 고정 longitude span만으로 전 세계를 처리하지 않는다.
- 넓은 화면은 국가·주요 도시·큰 강, 중간은 ADM1·중요 도시, 가까운 화면은 검증된 ADM2·주요 도로 순으로 늘린다.
- layer fade는 geometry가 전체 가시 영역을 덮는 시점부터 허용한다. 최종 카메라 한 장만 검사하지 않는다.
- 움직이는 모든 프레임의 viewport를 검사해 DEM clamp, roads의 갑작스러운 절단, admin 데이터 구멍을 차단한다.
- 진입·이탈 임계값을 분리하거나 짧은 fade를 넣어 경계에서 깜빡이지 않게 한다. 도시 우선순위와 anchor도 안정화한다.
- 카메라는 projected center 보간과 log scale 보간을 사용하고 hold 구간 속도를 0으로 한다. 실제 운영 타이밍은 내레이션에 맞춘다.
- 두 지도 데모의 20초 구조는 `hold 0–3`, `zoom 3–7.2`, `hold 7.2–10.4`, `zoom 10.4–15.8`, `hold 15.8–20초`다. 범용 문법으로 고정하지 않는다.
- 한국의 최종 표본 간격 약 121m/표시 약 145m, 우크라이나 약 204m/표시 약 325m는 각 데모의 값이다. 세계 전체 성능·해상도 주장으로 확장하지 않는다.

### 지역 예시를 전 세계 기능으로 옮기는 조건

- 한국20초 예시는 동아시아→한반도→서울·인천이다. 중심/경도 폭은 `(132.5,38,37)`, `(127.85,37.95,20.5)`, `(126.98,37.52,2.1)`이었다.
- 우크라이나20초 예시는 유럽 동부→우크라이나 동부→도네츠크주 주변이다. 중심/폭은 `(30,49.8,42)`, `(33.9,48.6,20.2)`, `(37.85,48.2,5.6)`이다.
- 좌표·국가 whitelist·도시명·source filename·언어 예외·상세 coastline 교체를 renderer 본문에 넣지 않는다. scene/config와 provider adapter로 분리한다.
- 한국은 KOSTAT 2018 자료, 우크라이나는 OCHA 2025 자료를 썼다. 원천 연도·개편·단계 의미를 비교한 선택이며 특정 국가 공급자를 전 세계 기본으로 강제하지 않는다.
- 지역별 주요 도로 class도 조정한다. 우크라이나에 한국의 motorway-only 구성을 복사하면 실제 주요 연결망을 과소표현할 수 있다.
- DEM을 쓸 수 있어도 더 가까운 도로·행정·수계가 자동으로 생기지는 않는다. layer별 지원범위와 최대 의미 있는 zoom을 따로 관리한다.
- 데이터셋 없는 지역, 섬·해협, 여러 나라가 걸친 화면, 날짜변경선, 고위도를 테스트 fixture에 포함한다. 한국·우크라이나만 성공한 상태를 글로벌 완료로 보고하지 않는다.

## 17 지명과 지리적 예외

- 라벨 우선순위는 검증된 한국어 → 검증된 영어 → 원어다. 한국어 표기가 없다는 이유로 도시 자체를 지우지 않는다.
- 임의 음역을 확정 표기처럼 만들지 않는다. 선택된 이름의 언어·출처와 stable ID를 기록하고 동명이인을 좌표·상위 행정구역으로 구별한다.
- 수도·주요 도시·현재 문장에 등장한 장소를 우선한다. 인구값이 있으면 조사 연도를 함께 보존한다.
- 지역·국가 경계를 넘는 viewport를 지원한다. 자원 요청과 클리핑을 ISO 국가 코드 하나에 묶지 않는다.
- 날짜변경선 통과는 bbox를 ±180°에서 나누고 geometry unwrap 및 재결합을 시험한다. 지구 반대편으로 긴 선을 잇지 않는다.
- Mercator는 약 ±85.0511°로 제한한다. 극지방은 별도 지원 투영을 명시하거나 지원 한계를 알려야 한다.
- 스케일바는 현재 중심 위도에서 계산한다. 위도에 따라 변하는 Mercator 축척을 화면 전체의 동일 지상 거리로 주장하지 않는다.

## 18 캐시와 재현성 계약

권장 manifest 필드: `provider`, `source_url`, `dataset_version`, `retrieved_at`, `valid_at`, `license`, `attribution`, `source_hash`, `bounds`, `crs`, `vertical_datum`, `native_resolution`, `sample_spacing`, `lod`, `transform_version`, `coverage_status`.

- 원본 다운로드, geometry 정리·단순화, raster 준비, 최종 렌더의 해시를 분리한다.
- 폰트 파일·renderer 버전·rules hash·출력 profile·seed·카메라 입력을 기록한다. frame time은 `frame_index/fps`로 결정한다.
- 고정 입력이면 프레임 순서·병렬 실행 여부와 무관하게 같은 결과가 나와야 한다. wall clock이나 호출 순서에 따라 물결·라벨이 달라지지 않게 한다.
- 다운로드 실패 시 부분 파일을 정상 캐시로 등록하지 않는다. 임시 파일 검증 후 atomic replace하고 원본을 삭제하지 않는다.
- 자료 부족 시 확인된 global country/admin1/city·terrain으로 fallback하고 누락을 provenance에 남긴다. 필요하면 최대 확대를 제한한다.
- 해상도가 부족한 지형의 인공 sharpening, 가짜 도로·경계·강 생성으로 빈 곳을 채우지 않는다.
- 다운로드한 모든 자료의 출처·연도·배포 의무를 credit 생성 경로에 연결한다. 새 라이선스는 실제 사용 전에 검토한다.

## 19 추가 과금 없는 TTS 개선

기존 Edge 음성을 활용해 발음·호흡·음량·영상 싱크를 개선한다. 아래 기존 동작과 문제는 핀의 소스로 확인했다. 이번에 음성 합성·청취·오디오 테스트를 실행하지는 않았으며 청감 개선량은 아직 검증되지 않았다.

### 현재 비용 경계와 직접 호출 우회부터 막기

- [config.yaml](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/config.yaml#L44-L54)은 `backend_default=edge`, `edge_voice=ko-KR-InJoonNeural`, `edge_rate=-3%`, `edge_pitch=-2Hz`, `elevenlabs_allowed=false`다. `orchestrator/config.py:TTSConfig`도 같은 기본값이다.
- [script/plan.py:build](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/script/plan.py#L31-L74)는 ElevenLabs 요청을 린트·합성보다 먼저 거부한다. 이 제한을 해제하지 않는다.
- 오래된 `docs/handoff/03_SCRIPT_NARRATION_TTS.md §6.2`의 ElevenLabs 목표 기본값·환경변수 자동선택 설명은 현 코드와 충돌한다. 현 설정·코드를 기준으로 문서도 바로잡는다.
- **확인한 우회:** [tools/tts_align_probe.py](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/tools/tts_align_probe.py#L41-L65)는 key 존재 확인 뒤 `elevenlabs.eleven_one()`을 직접 호출한다. 실제 과금 가능 경로이므로 이번 개선의 baseline 수집 도구로 실행하지 않는다.
- **변경 제안:** [script/tts/elevenlabs.py:eleven_one](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/script/tts/elevenlabs.py#L47-L59)의 요청 직전에 공통 금지 검사를 두고 probe도 파일 생성·key 접근·합성 전에 같은 검사를 하게 한다.
- 환경에 key가 있어도 자동 유료 전환하지 않는다. 무료 경로 장애 시 유료 fallback·새 구독·GPU 임대·유료 모델로 넘어가지 않는다.
- `requests.post` 등을 mock한 테스트로 plan 진입, 직접 provider 호출, probe CLI 모두 외부 과금 호출0을 확인한다. 테스트를 통과시키려고 실제 과금 요청을 보내지 않는다.
- Edge는 온라인 서비스이며 합성 문자열을 외부로 보낸다. 추가 유료 API를 쓰지 않는 조건을 완전 오프라인·총비용0·무제한·영구 무료 보장으로 설명하지 않는다.
- [edge-tts 공식 프로젝트](https://github.com/rany2/edge-tts#custom-ssml)는 custom SSML을 지원하지 않는다. 임의 `<break>`·phoneme·emotion/style 태그를 넣는 구현을 제안하지 않는다.

### 기존 파이프라인을 재사용하기

| 실제 코드 | 현재 역할 |
| --- | --- |
| `script/schema.py:Sentence` | `text`, 선택 `tts`, `emphasis`, `sources`, 선택 `media`; strict schema |
| `script/timeline.py:sentence_rows` | stable sid와 표시 text, `tts or text`, 강조 segments 생성 |
| `script/plan.py:build` | 린트 후 `pronounce_tts` 적용, 발화문 기준 cache·합성·plan 연결 |
| `script/tts/edge.py` | voice/rate/pitch, WordBoundary 합성, MP3와 alignment 저장; concurrency5, 최대4회·실패 후2초 대기 |
| `script/tts/cache.py`, `script/tts/align.py` | 현재 합성 cache와 정렬 읽기 |
| `script/tts/trim.py` | 44.1kHz mono, threshold.012, 앞30ms/뒤120ms 여유,10ms fade, dur·trim_offset |
| `script/timeline.py:layout` | 실측 길이와 문장.5초·장면1초·lead1.2초로 t0/t1 재계산 |
| `engine/timebase.py:Timebase.at_word` | 정렬 시작−trim_offset+문장t0; 미일치 시 ratio fallback와 mode/note |
| `audio/mix.py` | 문장 peak.8 정규화와 배치, 기존 music ducking |
| `audio/qa.py`, `engine/mux.py` | 기존2-pass loudnorm, limiter, 최종 MP4 재측정 |

발음 사전, 문장별 합성, WordBoundary, trim, ducking, loudnorm는 이미 있다. 같은 기능을 다른 경로에 다시 만드는 대신 실제 부족한 지점을 보완한다.

### P0 캐시가 바뀐 음성 설정을 정확히 반영하게 하기

기존 [cache_key](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/script/tts/cache.py)는 발음 문자열과 일부 voice salt를 SHA-1의10자리로 해시한다. rate/pitch가 빠지고 기본 Edge voice는 salt가 없다. plan은 지정 voice가 config 기본과 같으면 None으로 바꾼다. 따라서 default voice·rate·pitch만 바꾸면 옛 MP3가 재사용될 수 있다.

- 내부 `SynthesisSpec`, `cache_key_v2(spec)`를 제안한다. 아직 없는 API다. 실제 resolved provider·voice·발화 문자열·rate·pitch·사용된 model/settings·adapter version을 canonical JSON으로 만들어 충분히 긴 hash를 쓴다.
- Edge에 없는 previous/next context를 만들어 전송하지 않는다. 실제로 provider에 전달하는 인자만 합성 정체성을 결정한다.
- 사전 전체 hash만 바뀌었다고 전편을 재합성하지 않는다. 최종 spoken text가 같은 문장은 원본 합성 cache hit을 유지하고, 사전 버전은 provenance로 남긴다.
- 원본 MP3+정렬의 synthesis cache와 npy 후처리 cache를 분리한다. 후처리 키는 원본 hash+trim/postprocess 설정+sample rate다. trim·gain만 바뀌면 로컬 재처리하고 재합성하지 않는다.
- sid는 연출 계약으로 유지한다. 재사용을 위한 content-addressed 저장소와 sid→artifact 매핑은 제안이며 기존 `{sid}_{key}.mp3` 참조·provenance를 함께 이행한다.
- 임시 MP3·alignment를 모두 검증한 뒤 manifest를 마지막에 atomic rename한다. 파일이 존재하거나1000byte를 넘는 것만으로 cache hit을 인정하지 않는다.
- manifest·MP3·alignment hash, decode 가능 여부, 원문 일치, 배열 길이·finite·단조 증가·duration 범위를 확인한다. 설정을 입증 못 하는 옛 캐시는 legacy unknown으로 표시하고 삭제 없이 단계적으로 이행한다.
- 회귀 테스트: 동일 입력 합성0회; rate/pitch/default voice별 miss; 발음 결과가 같은 사전 수정은 hit; 실제 발음 변경은 해당 문장만 miss; trim 변경은 원본 hit/후처리 miss; 손상·중단·동시 요청은 잘못된 hit이 없어야 한다.

### P1 발음과 숫자 처리

- 실제 위치는 `assets/pronounce/pronounce_ko.json`, `script/lint.py:apply_dict/pronounce_tts/apply_pronunciation/spoken_risks`, `bundle/text.py:tts_of`, rules의 `tts_rules/tts_risk/pronounce`다.
- 기존 최장 일치·단일 패스·합성 직전 적용·멱등성을 유지한다. 명시적인 `tts`도 사전을 거친다.
- 자막 `text`는 유지하고 검증된 읽기만 spoken `tts`에 반영한다. 인명·수치·인과·주장을 바꾸는 자동 교정을 하지 않는다. 불확실한 표기는 경고와 후보로 남긴다.
- 현재 음성에서 실제 오독이 확인된 표현만 추가한다. 모든 한글을 잘게 띄우거나 단어마다 쉼표를 넣어 운율을 망치지 않는다.
- 과거 사전의 `유가→유까`, `달러→딸러`를 무작정 확장하지 않는다. `브렌트유가` 같은 반례와 재적용 멱등성을 검사하고 자연스러움은 청취로 판정한다.
- `bundle/text.py`의 native unit과 rules의 sino unit에 건·척처럼 상충하는 항목이 있다. 새 수사 변환기를 덧붙이기 전에 기대 결과와 single source of truth를 테스트로 확정한다.
- 회귀 원고에6월/10월,18개월,46건,3,000명, 소수·퍼센트, 날짜·비율·분기, 영문 약어, 반복 인명, 긴 기관명을 넣는다. expected spoken·자막 불변·위험 경고를 함께 검사한다.
- 표시 token↔spoken span의 명시 매핑은 새 설계다. `2020→이천이십`, `유가→유까`와 반복 단어를 포함해 occurrence/span을 식별하고 단순 substring find에 의존하지 않는다.

### P1 호흡과 정렬과 영상 앵커

- 현재도 문장별 합성이다. 긴 복문을 읽기 쉽게 다듬는 것부터 하고, 무조건 짧게 분할해 억양이 반복 시작되는 현상을 만들지 않는다.
- 필요한 긴 문장만 내부 chunk로 나누되 원래 sid/text/emphasis는 유지한다. chunk별 trim·삽입 pause·누적 offset을 합쳐 문장 오디오와 alignment를 복원한 뒤 layout을 재계산한다.
- `Sentence.after_gap_sec` 같은 선택형 pause 필드는 제안이다. strict schema·전달 경로·문서·테스트를 함께 만들고 미지정 시 기존 문장.5초를 유지한다. scene/title/end gap과 중복 적용하지 않는다.
- trim의 고정 threshold.012가 작은 시작·끝 음소를 자르는지 deterministic fixture부터 검사한다.10ms 미만 입력은 fade 길이를 실제 sample 수로 clamp하고 빈·무음·비정상 입력을 명시 처리한다.
- `align.py:read`의 기존 characters/start 길이 확인을 ends 길이·finite·단조 증가·start≤end·text·duration 검증까지 보완한다.
- voice·발음·trim·chunk·pause가 바뀌면 dur/trim_offset과 plan/subtitle/cascade·지도 event anchor를 다시 검증한다. 볼륨만 바꿨더라도 실제 길이가 같다는 확인 없이 단정하지 않는다.
- Edge WordBoundary의 단어 시작과 보간한 글자 시각을 구별해 기록한다. 글자 시각을 음소 수준 실측이라고 부르지 않는다.
- 기존 `tools/voice_swap_report.py`는 이미 있는 plan·정렬 비교에 쓸 수 있다. `--eleven`의 기존 fixture 읽기와 유료 합성 probe를 혼동하지 않는다.1ms 계산 일치는 청감 싱크 정확도 보장이 아니다.

### P1 음량은 실제 믹서와 QA의 공통 경로로

- 기존 목표는 I=−14, TP=−1.5, LRA=11, 후단 sample limiter=−2dBFS다. 최종 MP4에서 I±1LU, TP 코덱 여유.15dB, 문장 RMS 편차3dB 경고가 이미 있다. 목표를 바꿔 QA만 통과시키지 않는다.
- 문장 peak 정규화는 지각 음량을 같게 보장하지 않는다. 먼저 기존 경고·outlier·청취로 문제 문장을 찾고, loudnorm·limiter를 겹겹이 추가하지 않는다.
- optional narration leveling은 active-speech RMS 또는 충분히 긴 창의 loudness와 gain cap·peak ceiling·무음 처리를 쓰는 제안이다. 짧은 절마다 LUFS를 강제하거나 과압축하지 않는다.
- npy에 gain만 곱하면 현재 `audio/mix.py`의 peak 정규화가 차이를 다시 지운다. `prepare_narration()` 같은 신규 공통 처리로 믹서와 `audio/qa.py:stems/sentence_rms`가 같은 waveform을 사용하게 해야 한다.
- 음악/효과음 상대 레벨·ducking·최종 encode 후 true peak까지 검사한다. loudness가 맞는 것과 발음·억양이 자연스러운 것은 각각 검수한다.

### 검증과 완료 판정

1. 기존 `tests/test_script_tts.py`, `test_tts_pronounce.py`, `test_tts_lint.py`, `test_v560_script_review.py`, `test_timebase_align.py` 및 audio QA/rules/f1/crossfade 테스트를 mock·기존 cache 환경에서 실행한다.
2. 금지 gate, cache 변경, 정렬·trim·gain synthetic fixture를 보강한다. 제안 이름 `test_tts_cache_v2.py`, `test_tts_provider_guard.py`, `test_tts_chunk_alignment.py`, `test_narration_leveling.py`를 기존 파일로 착각하지 않는다.
3. 원본 cache가 있으면 네트워크 없이 전/후를 만든다. 파일·환경이 없거나 실제 합성을 안 했으면 미실행이라고 적는다.
4. 실제 사용이 허용된 Edge 경로로 고정30–60초 원고를 소수 후보만 비교한다. 기본 voice/rate/pitch를 기준선으로 한 요소씩 바꾸며 캐시된 결과를 재사용한다. 이 길이는 시험 설계 제안이다.
5. 최종 음량을 맞춘 A/B로 발음, 호흡, 반복 억양, 끝 음절, 배경음 위 명료도, 시각 앵커를 듣는다. 자동 지표만으로 자연스러움 합격을 선언하지 않는다.
6. source SHA·dependency·effective settings·cache hit/miss/resynthesis·alignment source·trim offset·audio QA·합성/청취 여부를 보고한다. 기대 개선과 실제로 확인한 개선을 구별한다.

특정 로컬 한국어 TTS로 즉시 바꾸는 것은 이번 기본 계획에 없다. 별도 요청이 있을 때 음성·모델 라이선스, 상업 이용, 실제 RAM/VRAM, 설치·추론 시간과 청감 품질을 검증한다.

## 20 제작한 자산과 코드의 이용 가능 범위

아래 파일은 독립 시안 작업에서 생성·확인한 자산이다. 표의 존재가 모두 이번 메시지에 첨부됐거나 저장소에 들어갔다는 뜻은 아니다. 구현 환경에 파일이 없으면 필요한 원본과 사용 권한을 확인하고 확보한 뒤 사용한다.

| 자산 또는 파일 | 용도와 주의점 |
| --- | --- |
| `portrait_as_is_to_be.png`, `portrait_flag_comparison.mp4` | 동일 인물 원본의 정적·모션 비교; `render_portrait_test.py`가 독립 제작 스크립트 |
| `f35_as_is_to_be.png`, `f35-tobe.svg`, `f35-tobe-line-reveal.mp4` | 초기 사선 시점 비교와5초 reveal; V2 top-view와 같은 geometry가 아님 |
| `f35-refined-v2.svg`, `f35-refined-v2-compact.svg` | 후속 top-view 원본과 소형 변형; `build_f35_v2.py`가 제작 코드 |
| `f35-refined-v2-ivory.svg`, `f35-refined-v2-transparent.png`, `f35-v1-v2-comparison.png` | 밝은 배경·raster 대안·시점 변경 비교 |
| `east_asia_grayscale_map.png`, `osint_map_zoom_demo.mp4` | 초기 동아시아 정적 지도와 한국 확대 예시; 최신 푸른 바다·얇은 수계 스타일로 대체할 부분 구분 |
| `ukraine_east_zoom_demo.mp4`, `ukraine_east_zoom_demo_v2.mp4` | 이전 검토본; V1 도로 coverage·V2 수계 두께·선형을 최종값으로 되돌리지 않는다 |
| `ukraine_east_zoom_demo_v3.mp4` | 얇은 선·푸른 수계 검토본; 시바시 해안의 국경 오분류 때문에 V4로 대체 |
| `ukraine_east_zoom_demo_v4.mp4` | 같은 스타일을 유지한 국경·해안 의미 수정본; 우크라이나 source adapter의 한계도 명시 |
| `cascade_lines_as_is_to_be_1080p.mp4` | 최초24초 통합 비교; relation 참고용이며 cascade 배치는 수정 V2로 대체 |
| `cascade_alignment_continuity_v2_1080p.mp4` | 사용자 확인한18초8사건 비교; 실제 외곽 가림·dx64/dy12 검증 |
| `render_comparison.py`, `render_cascade_v2.py`, 지역별 `render_zoom.py` | 독립 harness·시안 코드. 그대로 저장소 전체 renderer로 교체하지 않는다 |

- 기존 엔진 자산은 기존 registry ID와 source hash를 유지하며 새 variant로 확장한다. 원본과 기존 승인 자산을 덮어쓰지 않는다.
- source PNG/JPEG, editable SVG, compact variant, render-ready PNG, preview, license/credit, builder·recipe를 묶어 자산의 이력을 남긴다.
- media schema가 SVG를 직접 지원하는지 확인한다. 지원하지 않으면 준비 단계에서 검증된 raster로 변환하고 editable SVG를 원본으로 보존한다. 런타임이 SVG를 이미 지원한다고 가정하지 않는다.
- 외부 URL의 파일은 변할 수 있다. 다운로드 날짜·hash·허가 조건을 기록하고 프로젝트가 참조하는 snapshot을 재현 가능하게 만든다.
- 새 TTS 음성 비교 파일은 이번 작업에서 생성하지 않았다. 기존 코드 조사와 시각 데모를 음성 품질 검증으로 보고하지 않는다.

## 21 비용과 라이선스와 성능

| 항목 | 기본 접근 | 별도 확인할 비용과 제한 |
| --- | --- | --- |
| 인물·컷아웃 | 기존 자산·로컬 처리 우선 | 사진 라이선스, 모델 다운로드, 메모리·처리 시간; 외부 이미지 API 자동 사용 없음 |
| Hairline식 SVG | 코드-native geometry와 로컬 rasterization | 별도 이미지 API 요금은 필요하지 않으나 제작·검수·계산 비용은 발생; 복사한 MIT 고지 유지 |
| 지도 | 공개 데이터의 준비·cache·offline render | 데이터별 라이선스·storage·다운로드 용량·준비 시간; 공개 타일 무단 bulk 수집 금지 |
| TTS | 기존 Edge와 유효 캐시 유지 | 유료 backend·유료 probe·자동 fallback 금지, 외부 무료 서비스 가용성 보증 불가 |
| 배포 | 검증된 파일을 요청 범위에서 전달 | 새 hosting·유료 계정·공개 게시·외부 공유는 별도 범위 |

- 인물96-strip, 벡터 path 수, map vertex 수, raster 해상도, multi-layer hillshade 각각의 비용을 따로 측정한다. 화질과 무관한 중복 계산부터 줄인다.
- 불변 준비 결과를 캐시하고 화면 밖 geometry를 먼저 제외한다. hold 프레임은 동일 결과를 재사용하되 움직이는 화면의 새 정보는 재표본화한다.
- 선 단순화는 지상·화면 허용오차와 topology를 지킨다. 국경·coast·강·도로를 무작정 같은 tolerance로 줄이지 않는다.
- 기존 대비 준비 시간, 평균·상위 프레임 시간, 최대 메모리, cache 크기, 네트워크 요청 수, 외부 과금 호출 수를 보고한다. 근거 없이 실시간 성능을 약속하지 않는다.
- credit 경로는 `engine/credits.py`와 기존 registry 검증을 따른다. 원천 자료·가공 코드·렌더 영상의 라이선스가 같다고 가정하지 않는다.
- 권리·자료 누락은 조용한 성공으로 처리하지 않는다. source 미확인·사용 불가 자산을 별도 목록으로 보고하고 대체 범위를 제시한다.

## 22 하위 호환 구현 순서

1. 기준 커밋과 현재 브랜치를 비교하고 기존 테스트·대표 프레임·provenance를 저장한다.
2. TTS의 직접 유료 호출 차단과 cache 설정 누락을 먼저 별도 변경 묶음으로 해결한다. 네트워크 없는 회귀 테스트와 기존 음성 재사용을 확인한다.
3. 기존 schema 관례를 따른 선택형 visual profile을 추가한다. 기본값은 기존 출력이며 필드가 없는 프로젝트도 같은 결과여야 한다.
4. `engine/style.py`를 통해 토큰을 공급한다. renderer에 중복 리터럴을 추가하지 않고 schema·문서·예시·lint를 함께 갱신한다.
5. cascade의 시각 의미를 유지하며 후보 크기·타이포그래피·표면을 구현한다. shared island 기본 동작은 유지하고 geometry 변경은 후보 전용 검사까지 함께 반영한다.
6. 인물·vector asset·routes·패널을 각각 작은 변경 묶음으로 연결한다. TTS 변경도 별도 묶음으로 검증하고, 음성 길이가 달라졌으면 최종 화면 연출 전에 timing·plan을 재계산한다.
7. 지도 공급자·캐시·coverage 검사를 먼저 구현하고 이후 지형·국경·강·행정·도로·지명 LOD를 연결한다.
8. 한국·우크라이나 외 지역과 날짜변경선·고위도·자료 부족 fixture를 포함해 범용성을 검증한다.
9. 후보 프로필의 검토 자료와 실제 구현 범위를 전달한다. 시각 승인과 저장소 적용 요청을 구분하고, 기존 프로필의 기본값 교체·adopted 승격 범위를 확인한다.


### 변경 묶음과 PR 검수 단위

저장소 작업이 별도로 요청되면 현재 저장소의 commit·PR 정책에 맞춰 아래 묶음을 독립 검토한다. 이 문서 작성 단계에서는 브랜치·commit·PR을 만들지 않는다.

1. 비용·재현성: TTS paid gate와 cache 이행, mock 회귀 테스트, migration 설명.
2. 공통 스타일·geometry: 선택형 token schema, cascade 일정한 slot, silhouette/text 분리, 예약영역·오버플로.
3. 인물·재사용 자산 스킬: 사진 원본·국기 비용 검증, `.claude/skills/osint-visual-asset-create/` 계약·reference·공용 도구·fixture, SVG/compact/theme와 registry·credit을 묶는다.
4. 지도 데이터: provider·coverage·source/version/license, 국경과 coast 의미 분리, 캐시·지역 adapter.
5. 지도 표현·UI: 지형·해저·얇은 선·LOD·라벨·고정 UI, 국가별 fixture, moving-frame 검수.
6. 음성 품질·통합: 발음·trim·정렬·mix 공통 처리, 실제 A/B, plan·자막·event anchor 재검증.
7. 최종 회귀·승격: 기존/후보 비교, 비용·성능·미실행 항목, rollback과 적용 범위 확인.

각 묶음은 관련 schema·코드·test·문서·fixture가 함께 있어야 한다. UI만 바꾸고 검사·reserved·credit을 다음 변경으로 미루지 않는다.

## 23 테스트와 합격 기준

저장소의 준비된 개발환경에서 후속 구현 후 실행할 실제 테스트 경로다. 아래 명령을 이번 독립 데모에서 실행한 것으로 보고하지 않는다.

- `python -m pytest tests/test_cascade.py tests/test_g14_cascade.py`
- `python -m pytest tests/test_relation_panel_phase6.py tests/anti_inertia`
- `python -m pytest tests/test_geo_phase3.py tests/test_geo_key_collision.py tests/test_stage.py tests/test_stage_continuity.py tests/test_stage_direction.py`
- `python -m pytest tests/test_script_tts.py tests/test_tts_pronounce.py tests/test_tts_lint.py tests/test_timebase_align.py tests/test_audio_qa.py tests/test_audio_rules.py`를 네트워크 mock·차단 조건에서 실행한다.
- 위 집중 검사 뒤 `python -m pytest`로 전체 회귀 검사. 실제 프로젝트 preview는 필요한 입력 자산을 확인한 뒤 기존 렌더 CLI로 실행한다.

- [ ] 기존 cascade 테스트, G14 회귀, schema 검증, 기존 프로젝트 preview가 통과한다. 수행한 명령과 결과를 남긴다.
- [ ] 기존 프로필의 회귀를 확인한다. 승인한 bug fix로 달라지는 golden은 변경 이유와 pixel diff를 남기며, 환경·폰트 차이를 스타일 변화로 오인하지 않는다.
- [ ] 3항목뿐 아니라 5/6개 이상 항목, oldest-card shift, 아주 긴 날짜·제목, 빈 부제, 누락 국기, 촘촘한 앵커를 시험한다.
- [ ] 앞 카드/뒤 카드의 글자가 동시에 비치지 않고, 뒤 카드의 제목·날짜와 boundary fade가 의도대로 남는다.
- [ ] 모든 프레임에서 사건 순서별 인접 anchor의 dx>0·dy>0가 유지되며, shift는 전체에 같은 변위를 적용한다. ‘조치’ 진입 전후 뒤 카드의 노출 테두리·모서리를 확대·실제 크기로 비교해 불필요한 단절·hidden-edge bleed·이중 선이 없는지 확인한다.
- [ ] 카드 수·폭·예약영역·자막 충돌 hard 오류 0. 배경 라벨 warning은 ID·사유·개수를 보고한다.
- [ ] 인물 원본·정체성과 국기 도안이 보존되며 solo/group 모두 얼굴·모서리·strip seam·halo가 정상이다.
- [ ] 재사용 자산 스킬의 입력·산출물·오류·캐시 계약을 검증한다. F-35 외 profile fixture의 수행 여부도 구분하며 upstream Hairline 검사와 자체 검사를 혼동하지 않는다.
- [ ] SVG는 XML·적용 가능한 mirror·비율·가림·클리핑을 검사하고 실제 최소 표시 폭 및240px, 밝고 어두운 배경에서 읽힌다. 시점 변경·편집용 그림 표기를 유지한다.
- [ ] 854×480, 1280×720, 1920×1080 각각의 인코딩 결과에서 글자·국기·선·SVG를 실제 크기로 검사한다.
- [ ] 480 설계 좌표와 `Output.k`, `pad_x`를 사용한다. 1080p의 854×2.25=1921.5에 따른 좌우 패딩 차이를 무시하지 않는다.
- [ ] 대표 전환은 시작/¼/½/¾/끝 프레임과 ±1프레임을 확인하고 fps를 바꿔 타이밍 오류를 숨기지 않는다.
- [ ] full decode와 ffprobe로 프레임 수·길이·코덱·픽셀 포맷을 검사한다. 무음 시안과 실제 음성 싱크 검증을 구분한다.
- [ ] 움직이는 모든 viewport에서 활성 레이어의 coverage가 완전하다. DEM clamp·경계 절단·도로 잘림은 허용하지 않는다.
- [ ] 시바시·크림 같은 복잡한 해안을 국제국경으로 오분류하지 않는다. 실제 섬·석호·coast는 남기고, 인정 경계와 내부 분할선의 의미를 source-based 검사로 확인한다.
- [ ] 국경·행정·강·도로를 작은 화면과 회색조에서 구분할 수 있고, 필수 이름이 카드·배지 아래 숨지 않는다. 정지 keyframe뿐 아니라 모든 이동 viewport에서 라벨·halo의 화면 밖 잘림을 검사한다.
- [ ] 네트워크를 끊은 준비 완료 캐시로 재렌더된다. 소스·라이선스·vintage가 없는 레이어는 무조건 성공으로 처리하지 않는다.
- [ ] 변경 전후 준비 시간·프레임 시간·최대 메모리를 같은 장면으로 기록한다. 96-strip 국기 비용을 별도로 측정한다.
- [ ] TTS의 plan·직접 provider·probe 세 경로에서 금지 상태의 유료 호출이0이며, voice/rate/pitch 변경과 후처리 변경의 cache 행동이 구분된다.
- [ ] 발음·정렬·trim·음량 변경 후 자막 의미·문장 ID·시각 앵커가 유지되고, 합성·청취·오디오 QA를 실제 수행한 범위를 명시한다.
- [ ] 자산·지도·폰트·음성의 source/version/license·processing·credit이 실제 사용 목록과 일치한다.
- [ ] 실제 완료 항목, 미구현 항목, 검증하지 못한 항목과 후속 판단을 분리한 짧은 보고서를 제공한다.

## 24 최종 전달물

실제 구현을 마친 뒤 자체 SKILL.md와 reference·공용 도구·fixture, 선택형 변경 diff와 rollback, rules/schema 변경표, 인물·무기·지도·UI의 전후 비교, 실제 TTS 청취 비교와 측정값, 480/720/1080 검토판, 테스트 결과, 성능·비용 수치, 데이터·자산 manifest 및 credits를 전달한다.
As-is/To-be의 입력·카메라·문구·시간이 달라졌다면 차이를 명시한다. 미검증 기능을 구현 완료로 보고하지 않는다.

## 25 추가 원문 근거

- [Cascade 실제 renderer](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/cascade.py), [스타일·출력 좌표](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/style.py)
- [인물 renderer](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/layers/badges.py), [media renderer](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/layers/media.py)
- [F-35A USAF 제원](https://www.af.mil/About-Us/Fact-Sheets/Display/Article/478441/f-35a-lightning-ii-conventional-takeoff-and-landing-variant/sf2589626/f-35a-lightning-ii/), [공식 JSF top-view 원출처를 보존한 이미지](https://commons.wikimedia.org/wiki/File:F-35A_Top.jpg)
- [OCHA Ukraine COD-AB](https://data.humdata.org/dataset/cod-ab-ukr), [CC BY 3.0 IGO](https://creativecommons.org/licenses/by/3.0/igo/)
- [Mapzen의 지역별 원천자료·attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md), [Natural Earth 사용조건](https://www.naturalearthdata.com/about/terms-of-use/)
- [Edge 합성과 WordBoundary](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/script/tts/edge.py), [발음 처리](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/script/lint.py#L177-L255), [발음 사전](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/assets/pronounce/pronounce_ko.json)
- [오디오 믹서](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/audio/mix.py#L228-L283), [오디오 QA](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/audio/qa.py#L164-L220), [오디오 규칙](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/rules/video_rules.yaml#L811-L850)

## 부록 과학기술 영상으로 확장할 때의 판단

이 부록은 향후 선택할 수 있는 평가다. 이번 인물·지도·UI·TTS·재사용 자산 스킬의 구현 범위를 자동으로 넓히는 지시가 아니다.

- 현재 본편 무대는 mercator/timeline/backdrop이며 flow/structure는 [rules에 planned로 명시](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/rules/video_rules.yaml#L796-L809)되어 있다. 이미 작동하는 stage로 소개하지 않는다.
- 기존11종 패널, photo/clip/cutout과 [primitive 확장 계약](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/primitives/__init__.py)은 재사용할 수 있다. statement_diff/dot_plot/site_diagram도 있다.
- 구조도·분해도·단면 확대·공정 애니메이션의 tech_explainer는 [참고 초안](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md#L151-L158)이다. 보기 좋은 단일 자산을 만드는 skill과 작동 원리를 정확히 설명하는 renderer·데이터 모델은 별개다.
- 첫 후보는 structure 계열이다. 배터리 셀·반도체 층처럼 부품 ID를 유지한 채 단면·분해·층간 관계를 설명한다.
- 둘째는 process 계열이다. 물질·에너지·신호의 상태·순서를 유지하고 실제 흐름·변환과 단순 강조선을 구별한다.
- 셋째는 quantitative 계열이다. 물리 단위·축·크기 비교·변수와 그래프를 연결하되 개념도, 계산값, 실측값을 구분한다.
- 현재 [시리즈 데이터 규칙](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/rules/video_rules.yaml#L1130-L1140)은 경제 중심 단위와 FRED/Federal Reserve, monthly/release를 허용한다. 이 경로의 제약이며 전체 지도·미디어 출처 제한이라는 뜻은 아니다.
- 기존 [차트 honesty 검사](https://github.com/doroper98/osint_generator/blob/95a0b917afac00b598116698e494d57dc288cc1b/engine/honesty.py#L63-L91)의 단위 일치·%/%p 구분·로그 척도·기준시점·출처는 보존한다. 과학 단위·가정·불확실성·모델 검증은 별도로 확장해야 한다.
- 우선 기존 Cairo 벡터·자산·primitive 계약으로 한 주제를 end-to-end 검증한다. 새3D·시뮬레이션 의존성은 필요성이 확인된 뒤 별도 결정한다. 기존 별도3D 지구본·기하 스케치가 있으므로 “3D 기능이 전혀 없다”고 단정하지 않는다.
- SKILL 문서가 물리 계산이나 근거를 대신하지 않는다. 기하적 개념도를 실제 성능·정밀 시뮬레이션처럼 표현하지 않는 것이 확장 판단의 핵심이다.
