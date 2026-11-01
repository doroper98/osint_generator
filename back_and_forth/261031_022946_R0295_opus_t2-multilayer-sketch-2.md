---
id: R-0295
from: opus
to: fable
kind: progress
responds_to: [D-0310, R-0294]
phase: "E4"
version: v7.4.0
commit: ad225b60
status: awaiting_user
---

# T2 다층 아일랜드 스케치 2차(D-0310 princess·각진 막대·accent 이동) · merge · 답 둘

## 1. 스케치(artifacts `artifacts/econ-template-2026` 8c9c4b45, 폴더 `t2_multilayer_v2/`)
- 실제 엔진·실제 레코드. 7컷 — 감독이 말한 4층에 사진 컷과 accent 이동 컷을 더했다.
| 컷 | 층 · accent |
|---|---|
| `frames/p_0003.50.png` | 인텔 본사 사진 — 첫 문장의 가운데 요소 한 번(배경 아님) |
| `frames/p_0008.50.png` | 추이 막대, 최신 3분기만 accent |
| `frames/p_0013.00.png` | 부문 쌓임, 파운드리 accent, 부문 이름 |
| `frames/p_0017.00.png` | 같은 쌓임, DC accent(2분기부터 DC > PC) |
| `frames/p_0021.00.png` | 합계 점·선 켜짐, 합계 accent. 부문 이름은 접음 |
| `frames/p_0036.50.png` | 주가 일별 선(왼쪽 보조 축, muted) |
| `frames/p_0040.00.png` | 발표일 핀 + 세로 점선 |
- 지시 반영
  - ① accent 는 문장이 말하는 층·부문 하나. 같은 쌓임을 문장 경계에서 이어 붙이고 뒤 이벤트는 `grow: false` 다. 새 키 `series.accent`(latest·total·none·부문 이름), `series.total`(합계 층을 켜는 문장).
  - 손실 부문은 `bars.loss_color: ru` → down #FF8378. 나머지 부문은 잉크 사다리이고, 부문 사이는 1px 바탕색 틈이다.
  - 부문 이름은 칸 높이 ≥ 14px 이면 막대마다 안에 둔다. 작으면 최신 막대 오른쪽 지시선(13초 컷 "기타")으로 보낸다.
  - ② princess: `rules palettes.princess` + `genres/earnings.yaml palette: princess`. 막대는 0 쪽이 각이고 바깥 끝만 `bars.top_radius: 3` 이다. 속빈 윤곽 `hollow_w: 2` 는 키만 있다(estimate 스케치에서 씀). 바탕은 무늬 없다.
  - ③ 겹침: −3.1 라벨은 손실 부문 아래, 보조 축 "140" 은 레인 이름과 겹치면 접는다. ④ 0 기준선은 `bars.zero_alpha 0.7`·`zero_w 1.2` 다. ⑤ "자료 없음"은 그대로 두었다.
- 버린 판: 주가 장면만 w 150 으로 확대한 판(`rejected_zoom/sheet.jpg`)이다. 겹침은 풀리지만 `[timeline-rescale]` hard 에 걸리고 UF-138 위반이다.
- 미등록 패치는 `multilayer_sketch_v2.patch` 다(ad225b60 위, 13파일). 브랜치에는 넣지 않았다.

## 2. 남은 결함 — 감독 판단 요청(방향)
- **40초 컷 겹침이 남았다.** "92.07달러" 판과 "실적 발표일" 핀 라벨이 주가 선 위에 있다. 원인은 주가 레코드가 9/1~10/30 두 달뿐이라 분기 축척(w 600)에서 선이 약 70px 에 눌리는 것이다.
  - 안 A: 주가 레코드를 2025-07 부터로 늘린다. 선이 차트 전체를 지나가 참고 그림과 같아진다. 급변일(±10 %)마다 원문 인용 또는 missing 이 필요하다. 이 경우 핀 라벨을 레인 위 띠로 올린다.
  - 안 B: 주가 층에서 보조 계열 끝값 판을 접는다. 핀이 끝점을 가리키므로 값은 핀 두 단 라벨로 보낸다.
  - 안 A + B 를 권한다.
- 날짜 눈금("4분기")이 분기 시작일에 있어 막대 가운데와 어긋난다. 막대 아래 "3Q'25" 식 열 라벨로 바꾸자고 제안한다(T3).
- 정직성 검사(unit-mix·series-limit·units_visible·as_of_visible)가 hard 로 실패한다. 이어 붙인 쌓임 이벤트와 보조 축을 아직 모르기 때문이다. T3 에서 레인 단위 묶음으로 고친다. chart_only_run·media_density 는 영상 규칙이라 스케치에서는 걸린다.
- **비네팅이 충돌한다.** D-0310 §1-4 는 "기존 비네팅 유지"인데, CLAUDE.md C0 "되돌리면 안 되는 것"에 비네팅이 있다. 엔진에도 지금 비네팅이 없다. 그래서 넣지 않았다. 어느 쪽이 맞는지 정해 달라.
- **팔레트 자리.** `themes.princess` 를 지도 테마 자리(geo.themes)에 두려면 지형 래스터(geo.prep)가 필요하다. 그래서 스케치는 화면 팔레트 `palettes.princess` 로 했다. map_* 값만 기록했고, 지도 무대와 함께 쓰면 오류다(조용한 옛 지도 금지, P6).

## 3. 답 · 정정
- 삼성 DX 3Q'26 영업이익 부호: IR 자료 별첨 2(13쪽) "DX부문 3.5 (0.8) (0.8)", 6쪽 "DX 52.1조 -0.8조". 레코드 SSNLF_SEG_DX_Q = −0.8 은 맞다.
- R-0294 커밋 해시 정정: a317aea3 → **8acbbc27**(R-0294 보고 커밋).

## 4. merge · 시험
- sweet-galileo merge(ad225b60): checks HARD 에 template_label·invest_notice·scene_visual_void 를 모두 넣었다. 골든 검사 수는 102 다.
  - template_label 캐시는 감독 줄(연출 값 우선) 하나만 남겼다. 미디어 레지스트리와 DECISIONS(D292~D296 뒤 D400·D401)는 양쪽을 다 살렸다.
- 타깃 + anti_inertia(not slow): 113 passed, 1 failed.
  - 실패는 `test_doc_guards_only_for_process_items` 다. UF-150(설계 의견을 문서 장치로 guarded)이 process 항목이 아니라 걸린다. 감독 원장 분이라 이 트랙은 고치지 않았다.
- 오늘 전체 pytest 는 컨테이너 재시작(메모리 — 시험 둘 동시)으로 끊겼다. 밤에 혼자 다시 돌린다.

## 5. 다음
- §2 답을 받아 주가 층을 마무리한다. 이어서 bullet(컨센서스 레코드 있음)·덤벨·diverging·slope·가이던스 band 를 같은 princess 아일랜드로 그린다.
- 삼성 1컷은 SDC·Harman 부문 영업이익 레코드와 반올림 정밀도 기반 허용 오차가 필요하다.
