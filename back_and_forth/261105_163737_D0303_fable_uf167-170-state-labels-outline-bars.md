---
id: D-0303
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-167~170(콘티 판 v1 메인 장면 캡처) — 이 영상 먼저 반영 뒤 프리뷰 → 게이트 ②

## 0. 사용자 원문(2026-11-05 16:40 KST, 첨부 캡처 = 약 288초 메인 장면)
> "이번에는 도시 이름들 보다 주 이름이 표기 되면 좋겠어. 그리고 흰색 테두리가 너무 작은 글씨에는 맞지 않는거 같아. 그리고 주를 나타내는 테두리 라인의 두께를 좀 얇게 해. 너무 투박해. 그리고 주별 선거 결과를 보여줄때 막대그래프로 직관적으로 인지할 수 있도록 보완해."
- 원장 UF-167(주 이름)·UF-168(작은 글자 halo)·UF-169(외곽선 두께)·UF-170(막대그래프), DECISIONS D525. 게이트 ② 전에 넷 다 반영한다(C12-2). D-0302 의 프리뷰 작업은 이 지시와 합친다.

## 1. UF-167·168 — 주 이름 라벨 모드(골든 불변 — 모드 선택식, theme D154 패턴)
- 지금: `engine/layers/labels.py` admin-1 이름은 `view.w < LOD["admin_names_below_w"]` 이고 `labels.yaml province_countries` 에 있을 때만, 9.5px·alpha 0.42·halo 1.8 — 메인 장면에서 안 보이고 도시(외국 도시 포함)만 보인다.
- 새 규칙 `rules labels.admin1_modes` 두 벌: `subtle`(= 현재 값 그대로, 기본 — 골든·옛 영상 불변) · **`prominent`**(이 영상): 주 이름 **size 13·sansb·alpha 0.9**, halo 는 글자 크기 비례 **얇게**(예 halo 0.9·halo_a 0.5 — light 테마 흰 테두리 최소화), 등장 폭 `below_w` 를 본토 전체(w 60)까지 올려 **w ≤ 60 에서 주 이름 표시**(겹치면 free() 판정으로 건너뜀 — 지금 로직 그대로). 도시: `cities: {max_per_frame: 6, foreign: false(지도 초점 나라 밖 도시 제외), capitals_only_below_w: 40, size: 9.5, halo: 0.6}` — 작은 글자 흰 halo 는 **얇게**(UF-168). 선택 = direction `stage_config.mercator.admin1_labels: prominent`(없으면 subtle). `labels.yaml province_countries: [US]`, 주 이름 한글(NE name_ko 없으면 labels.yaml ko 표에 50개 — 지명 사전 대조).
- 검사: 모드 prominent 인데 화면에 주 이름이 0 인 컷이 있으면 warning `[admin1-label-missing]`(투어 구간 w ≤ 20). 골든 dark·light 25/25 불변 확인(subtle 기본값).

## 2. UF-169 — area 외곽선
- `rules area.outline` [[5.0,0.08],[2.2,0.22],[0.9,0.85]] → **[[2.4,0.05],[1.1,0.16],[0.55,0.8]]**(글로우 반, 선 0.55 px·alpha 0.8). 주 경계 기본 선(테마 map admin1 선)이 그 위에 또 굵게 보이면 함께 확인. 컷 2장(메인 w≈8·텍사스 w16) 을 gate2 R 에 — 감독이 확정(D518 보정).

## 3. UF-170 — 새 지도 이벤트 `bars`(후보별 득표율 막대) — 레지스트리 3곳·검사·테스트
- 설계(감독): 지도 위 **작은 막대 상자**(diesel 문법 "이야기 안에 박힌 데이터") — 마커 옆 슬롯에 2~3줄 가로 막대. 줄 = 후보 이름(한글 표기)·정당색(dem/rep/muted)·득표율 숫자(%). 막대 길이 = 득표율/100 × 상자 폭(같은 축척, 모든 주 동일 — UF-135·138 "한 세계"). 등장 = 막대 자라기(`bars.grow_sec`), 유지 ≥ 4초, 출처 줄 작게(`src` 필수 — "엔비씨 집계 · 11월 5일"). 개표 중 주는 막대 끝에 빗금/점선 + "개표 중" 작은 글자(status counting).
  ```yaml
  - type: bars
    t0: {sid: act2_3, off: 0.4}
    t1: {sid: act2_4, edge: end}
    lon: -99.0
    lat: 31.5
    side: right              # placement 슬롯(코드가 겹침 회피, 픽셀 금지)
    race: senate
    code: US-TX
    src: "엔비씨 집계 · 2026-11-05 09:30 KST"
    rows:                     # 2~3줄, 값은 data/state_results.yaml 과 같아야 한다
      - {name: 탈라리코, col: dem, pct: 55.1}
      - {name: 팩스턴, col: rep, pct: 43.0}
  ```
- 스키마 `engine/events.py BarsEvent`(_Event, lon·lat·side·race·code·src·rows[2..3]·status 는 데이터에서), 렌더 `engine/layers/bars.py draw_bars`(상자·막대·글자 = rules `bars` 블록: box_w·row_h·bar_h·pad·font·grow_sec·fade·hatch — 코드 리터럴 0), `engine/registry.py "bars": Entry(..., "map")` + MAP_LAYER_ORDER 에 `marker` 뒤·`badge` 앞, `rules registries.event_types` 에 bars, `direction_grammar` 한 줄("주별 득표 결과 문장에는 bars — 값은 데이터 파일, 축척 동일"), `prompts/director.md` 문법 줄, 파리티 예시 `tests/fixtures/direction/bars_minimal.yaml` 등록, 검사(hard): `[bars-data-mismatch]`(rows 의 이름·pct·col 이 데이터 파일의 그 주·레이스와 다름 — pct 소수 1자리 일치, col = winner/loser 당), `[bars-src-missing]`, `[bars-overlap]`(패널·사진·기사와 같은 시각 겹침 → reserved 영역 검사 재사용), `[bars-hold]`(< 4초), 경고 `[bars-no-camera]`(그 주에 카메라가 안 들어온 채 bars). provenance features_used.bars. 테스트 `tests/test_bars_event.py`(스키마·1프레임 렌더 막대 길이 비율·검사 4종·데이터 대조).
- 적용(연출): act2 뒤집힌 7곳 + GA·MI(상원) · act3 MS·AK 상원(counting)·KS 주지사(counting) · act4 TX·GA·OH·NV·IA·FL 주지사 = **16개 안팎**, 문장마다 카메라 도착 뒤 등장, 마커 라벨·사진 액자·패널과 겹치지 않게(사진이 있는 문장은 bars 를 사진 뒤 문장으로). 전국 54 대 44·242 대 151 은 versus 패널 그대로.
- bars 가 필요한 pct 는 data/state_results.yaml 에 이미 있다(pct 두 값) — 세 후보(KS 상원 무소속 3%)는 데이터에 세 번째 값이 있을 때만 3줄.

## 4. 순서·보고
1. §1·§2·§3 구현(한 커밋 한 의도) → 테스트(새 테스트 + anti_inertia + 골든 25/25 dark·light) → direction 갱신(admin1_labels prominent, bars 16, D-0301 2건·D-0302 "석" 포함) → 검증 hard 0.
2. `--preview auto` + **원크기 컷 6장**(메인 w≈8·텍사스 w16·캔자스·미시시피 counting bars·조지아 주지사·본토 전체 w60 주 이름) → artifacts `gate2/` → gate_request R + send_message. 재콘티는 하지 않는다(음성·원고 불변, 감독이 컷으로 판정 — D509·D523).
3. 감독 승인 → 720p 전편 → final_deliver → phase_report(D-0301 §3). 장치(UF-167~170 guards)는 전달 뒤 첫 작업.
