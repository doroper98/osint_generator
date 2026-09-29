---
id: R-0112
from: opus
to: fable
kind: progress
responds_to: []
phase: "-"
version: v4.4.0
commit: 519bd3e
status: awaiting_decision
---

# dmz_mine_2026 추가 보완 기록 — 벡터 개념도·폭발 애니메이션·임의 경로 삭제 (R-0111 후속)

R-0111(같은 영상의 U1~U7·M1~M7·S1~S7·D1~D4)에 이어지는 기록이다.
사용자 지시(2026-09-29): **"이것도 Fable 이 볼 수 있도록 기록해."**
커밋 칸의 `이 커밋`은 이 파일을 올린 커밋이다.

## 1. 사용자 보완 요청 (U8~U13)

| # | 사용자 요청(원문 요지) | 처리 |
|---|---|---|
| U8 | 회색 점선 화살표는 뭐냐 | AI 연출의 `route` 3개다. 이름은 "군사분계선"이고 경로 `mdl` 은 연출가가 어림한 좌표 7개다. 지도 경계선(NE KR/KP ≈ MDL)과 어긋난다(경도 126.78°에서 점선 38.00°, 경계선 약 38.02°). `route` 라서 화살표 머리가 붙어 이동처럼 보였다(M8). |
| U9 | 회색 화살표를 지워라 | route 3개와 `paths.mdl` 을 삭제했다. 지도의 붉은 경계선이 이미 군사분계선을 보여 준다. |
| U10 | 하늘색 "새 수색로" 글씨와 화살표도 지워라 | route `new_trail`(임의 좌표 3점)과 `paths.new_trail` 을 삭제했다. |
| U11 | 개념도 해상도가 나쁘다 → SVG 같은 벡터로 조판하면 좋지 않냐 | 원인은 두 겹이었다. ① 사진 가공 기본값이 1440×900 원본을 720×450 JPEG로 줄였다(내 실수). ② 480p 출력이었다. 조치: **새 프리미티브 `site_diagram`**(cairo 벡터, `engine/primitives/site_diagram.py`)으로 바꾸고, 최종본은 1080p 로 렌더했다. |
| U12 | 첫 폭발 후 두 번째 폭발도 화면을 유지하고 폭발 아이콘만 추가하는 애니메이션 | 개념도 한 장이 `operation_1` 부터 `two_blasts_3` 초반까지 계속 떠 있다. 폭발 ①은 단어 앵커 `"첫 폭발"`(43.85초), ②는 `"두 번째 폭발"`(49.1초)에 튀어나온다(배율 1.9→1 + 번쩍임 고리 + 라벨 페이드). 네 번째 지뢰 장면에서 같은 개념도가 다시 뜬다. 이때 ①② 는 이미 있고 미폭발 지뢰·9.29 추가 발견이 차례로 더해진다. 폭발 전에도 사고 지점(금색 점)이 보인다. |
| U13 | 개념도의 확대 애니메이션이 끊긴다 → 부드럽게 | 측정 결과 지도 카메라(w 6.4→0.8)는 연속이었다(프레임별 w 단조 감소). 끊김의 원인은 **사진 레이어 켄 번스**였다(S8). 벡터 프리미티브는 등장 배율(0.97→1)을 cairo 변환으로 연속 적용한다. 켄 번스는 없다. |

## 2. 새 요소 `site_diagram` (프리미티브, 20 §4.2 계약)

- **계약**
  - SCHEMA(extra forbid): header·north·south·nll·mdl·sll·width_note·distance·distance_src·marks[kind burst|mine|note, label, t]·footnote·source·date
  - COLOR_KEYS: confrontation·explosion_opposition·emphasis·neutral
  - draw: 예약 상자는 고정이다.
  - PREVIEW_FIXTURE: 예시 문구이며 실제 사건이 아니다.
- **불변 층:** 출처·날짜 필수. `footnote`(축척·실제 지형 아님) 필수. 글자는 min_font_px 이상이다.
- **표시 자리:** 폭발 자리는 규칙 `burst_offsets`(3개)로 둔다. 초과하면 스키마 오류다.
- **토큰:** `rules primitives.site_diagram` 50여 개. 모듈에 숫자 0·1·2 외 리터럴이 없다(AST 검사 통과).
- **등록 위치**
  - `rules registries.primitives`
  - `genres/geopolitics.yaml primitives.new: [site_diagram]` — 지정학 프로필에 새 요소가 생긴 첫 사례다.
  - `schemas/rules_models.py SiteDiagramLayout`
  - 테스트 `tests/test_primitive_site_diagram.py` 4건: 스키마, 불변 층, 표시 순서, 상자 고정
  - `tests/test_genre_profiles_files.py` 기대값을 `[] → ["site_diagram"]` 로 바꿨다(주석 근거).
- **승인:** 사용자가 이 요소를 직접 요청했다. `projects/dmz_mine_2026/order.yaml decisions.elements_approval {value: "site_diagram approved", by: user}`.
  - 다만 **지정학 장르 프로필 자체에 새 요소를 넣는 것**은 장르 운영 결정이다 → **D5**.
- **데이터 출처:** 폭발·지뢰·발견 문구는 원고 claim(clm_0007·0008·0020·0026)과 합참 발표 거리(clm_0022)에서 왔다. GP·OP 거리와 좌표는 비공개라 넣지 않았다.
  - 사용자가 참고로 준 그림은 **2015년 목함지뢰 사건 보도 그래픽**(440m·GP 930m/750m)이다. 형식만 참고했다.
- **이전 판:** 사진 이벤트 `dmz_site_diagram_{1,2,3}`(코드 조판 PNG)은 연출에서 뺐다. 미디어 레지스트리 항목은 남아 있다(미사용). 정리할지는 D5 와 함께 판단해 달라.

## 3. 새로 찾은 누락·결함

| # | 내용 | 조치 |
|---|---|---|
| M8 | AI 연출이 **좌표 근거 없는 경로 두 개**를 그렸다. 하나는 "군사분계선"(지도 경계선과 어긋남)이고, 하나는 "새 수색로"(위치 비공개)다. 게다가 이동용 `route` 요소를 경계선 표현에 썼다. v1~v4 에 나갔다. R-0111 M5(임의 사고 지점 좌표)와 같은 계열이다. | 삭제(U9·U10). 구조 대책은 R-0111 **D2(b)** 에 "경로도 포함"으로 넓혀 달라 |
| M9 | 개념도 PNG 를 사진 기본 가공값(`crop [720,450]`)으로 줄였다. | 벡터 프리미티브로 대체(U11) |
| S8 | **사진 레이어 켄 번스가 계단식**이다(`engine/layers/media.py draw_photo`). 매 프레임 `raster(w*k)` 로 정수 픽셀 크기 이미지를 다시 만들기 때문에, 크기가 1px 단위로 튀고 글자가 많은 이미지에서 "끊김"으로 보인다. **모든 사진(호르무즈 골든 포함)에 해당**한다. | **미수정** — 골든 프레임이 바뀐다(RENDER-AP 후보). 고치려면 원본 해상도 표면 하나를 두고 cairo 변환(scale)으로 그리면 된다. → **D6** |
| S9 | `route` 요소는 이동(항로·경로)용인데 연출 프롬프트에 "경계선을 route 로 그리지 말 것"이 없다. | D2 와 함께 |

## 4. 결정 요청 (R-0111 D1~D4 에 더함)

- **D5 (장르·요소)** — 새 요소 처리 두 가지를 정해 달라.
  - `site_diagram` 을 지정학 프로필 `primitives.new` 에 계속 둘지, 아니면 이 프로젝트 전용으로 할지.
  - 미사용 미디어 항목 `dmz_site_diagram_{1,2,3}` 을 삭제할지.
  - 요소 승인은 이 프로젝트에서만 사용자 몫으로 기록돼 있다.
- **D6 (렌더 결함 S8)** — 사진 켄 번스를 연속 변환으로 고칠지 정해 달라. 고치면 골든 25컷 중 사진 컷의 MAD 가 바뀐다. 그래서 재등재나 사용자 확인 절차가 필요하다.

## 5. 결과 (이 커밋 기준)

- **렌더:** 1080p 전편(v5)은 이 보고를 쓰는 동안 렌더 중이다. 결과(md5·음량)는 다음 보고나 DEVLOG 에 적는다.
- **프리뷰:** 1080p 확인 컷 3장, 오류 0.
- **테스트:** 새 테스트 4건, anti_inertia 41건, 장르 테스트 통과.
- **변경 파일**
  - `engine/primitives/site_diagram.py`(신규)
  - `rules/video_rules.yaml`(primitives·registries)
  - `schemas/rules_models.py`
  - `genres/geopolitics.yaml`
  - `tests/test_primitive_site_diagram.py`(신규)
  - `tests/test_genre_profiles_files.py`
  - `projects/dmz_mine_2026/{direction,credits,order}.yaml`
