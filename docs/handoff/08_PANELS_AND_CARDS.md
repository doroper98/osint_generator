<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-panels, v2-cards]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 08. 패널과 카드

참조 코드: `v3/render3.py` (`draw_panel`, `panel_title`, `P_refusal`, `P_statement`, `P_timeline`, `P_precedent`, `P_versus`, `draw_card`, `edge_curve`), `v2/render2.py` (`P_network`, `P_dots`, `P_gantt`, `P_dual`, `P_versus`, `P_fork`, `P_check`, `prov_tag`)

---

## 1. 언제 패널을 쓰는가

지도로 말할 수 없는 정보에만 쓴다.
| 정보 유형 | 패널 |
|---|---|
| 누가 누구에게 무엇을(요구·거절·영향) | 관계 패널(refusal/network) |
| 여러 나라의 공동 행동 | 국기 행 패널(statement) |
| 시간 순서 | 연표 패널(timeline) |
| 전례 비교 | 카드 행 패널(precedent) |
| 찬반·주장 대립 | 대비 패널(versus) |
| 비율·규모 | 도트 매트릭스(dots), 막대 |
| 기간 겹침 | 간트(gantt) |
| 추세 | 선 그래프(dual_line) |
| 시나리오 | 분기(fork) |
| 확인된 사실 | 체크리스트(checklist) |

장소가 핵심이면 패널 대신 지도 + 마커 + 카드로.

---

## 2. 패널 공통

```python
a = window(t, t0, t1, 0.6, 0.6)
ctx.paint(rgba(0.025, 0.03, 0.045, 0.8a))      # 지도를 어둡게 덮음(지도는 뒤에서 드리프트 계속)
panel_title(ctx, a, 제목, 부제)                # 화면 중앙 상단: Noto Serif Bold 19px @ y=74, 부제 Medium 11px muted @ y=96
```
- **제목은 중앙 상단**. 좌상단 모서리에 킥커+제목을 두던 v2 방식은 "모서리엔 날짜만" 규칙(지적 3)과 충돌하므로 폐기.
- 패널이 떠 있는 동안 지도 라벨 알파 = 1 − 패널 알파.
- 패널 내용은 화면의 70% 이상을 쓴다(저장소 롱폼의 "넓은 빈 공간" 문제 회피).
- 패널 안 모든 요소는 **문장/단어 앵커**로 등장한다. 한꺼번에 뜨지 않는다.

---

## 3. 관계 패널 — `P_refusal` (v3, 지적 2 해결)

화면: "3월 15일의 요구, 다음 날의 거절"
```
요구자: 트럼프 뱃지 (235, 262) R36, label '도널드 트럼프', role '미국 대통령', accent us, 패널 시작 +0.4초 팝인
대상:   독일·영국·일본·호주·한국 국기 뱃지 x=590, y=138+62i, R19, side='right'(이름 오른쪽), 패널 시작 +1.0+0.2i초
선:     edge_curve(요구자 오른쪽(ux+40, uy) → 국기 왼쪽(fx−26, fy))
        수평 접선 3차 베지어: P0=(x0,y0), P1=(cx,y0), P2=(cx,y1), P3=(x1,y1), cx=(x0+x1)/2  → 모든 선 곡률 통일
        선 i 시작 = 패널 시작 + 2.2 + 0.75i 초, 1.3초 동안 ease_io로 자람 (동시에 두 선 이상 성장 최소화)
        색 금색(요구) → 단어 앵커 at_word('ask_1', 국가명) 시점부터 0.5초 동안 붉은색으로, 절반 넘으면 점선 [4,4], 알파 0.8→0.55
        '거절' SemiBold 12 붉은색 — 국기 이름 오른쪽(fx+78)
라벨:   '해협 방어 참여 요구' 금색 11px @ (400,150), +3.2초 페이드
인용:   ask_2 동안 하단 중앙 y=414 "“우리가 시작한 전쟁이 아니다” — 보리스 피스토리우스 독일 국방장관" (Noto Serif Bold 13)
        ask_3 동안 트럼프 아래 "“매우 어리석은 실수” — 트럼프 대통령" (us 색)
```
**v2 관계도가 실패한 이유**(사용자 지적 "너무 빨랐고 정돈되지 않음"): 간선 12개가 0.18초 간격·0.8초 지속으로 사실상 동시에 튀어나옴, 2차 곡선의 부호가 방향마다 달라 곡률이 제각각, 라벨이 선과 동시에 나타남.

**정돈된 관계선 규칙**
1. 노드가 모두 뜬 뒤에 선을 긋는다.
2. 선 하나 1.0~1.3초, 간격 0.6~0.75초.
3. 모든 선은 같은 형태(수평 접선 3차 베지어). 교차를 줄이도록 노드 배치(요구자 한쪽, 대상 세로 열).
4. 라벨은 첫 선이 자라기 시작한 뒤. (v2.5.5 정정, back_and_forth D-0035 NB6 — v3 합격 값 3.2초는 첫 선 시작 2.2초 뒤·완성 3.5초 전이다. "완성 뒤"는 v3 합격 화면과 맞지 않아 기준을 "첫 선 시작 뒤"로 고쳤다. 앞서면 lint 경고 `relation-label-before-edge`)
5. 상태 변화(요구→거절)는 내레이션이 그 이름을 부를 때.
6. 선이 7개를 넘으면 패널을 둘로 나눈다.

### 3.1 v2 관계도(`P_network`) — 이식 시 위 규칙으로 고칠 것
3열(left 150, center 427, right 704), 열 내 세로 간격 92px, 번들 `stakeholder_map` 노드(kind person/flag/logo)와 간선(type 영향/연관/대립/동맹). 간선 스타일: 영향=금색 화살, 연관=회색 1px, 대립=붉은 점선, 동맹=초록 실선. 언급 시 노드 금색 펄스(MENTION 목록). **휘장이 없는 기관을 문자 원으로 그린 것이 지적 1의 원인** → 엔티티 레지스트리로 휘장 사용.

---

## 4. 국기 행 패널 — `P_statement` (v3)
제목 "3월 21일 공동성명", 부제 "이란의 공격 규탄 · 항행의 자유 보장 촉구"
```
7개국 국기 R24, x = 110 + 92i, y = 230, 0.22초 간격 팝인 (영국 프랑스 독일 이탈리아 일본 네덜란드 캐나다)
대한민국 국기 R30 (W/2, 345), 등장 = max(패널+2.2초, at_word('ask_4','한국')), role '성명에 동참', accent gold
7개국 행 아래 금색 점선 (110→W−190, y=292)
```

---

## 5. 연표 패널 — `P_timeline` (v3)
제목 "해협의 일곱 달", 부제 "2026년 2월 – 9월"
```
축: x 80→774, y 262, 2026-02-01 ~ 2026-09-30 선형. 1.2초 동안 왼쪽부터 그어짐
월 눈금: 매월 1일, 라벨 '2월'… IBM Plex Sans KR Medium 10.5 (★ IBM Plex Mono에는 한글이 없어 '월'이 깨짐 — v3 초판 버그)
이벤트: (날짜, 라벨, 색, 층, 앵커문장)
  층: −1/+1 = 축 위/아래 44px, −2/+2 = 96px  → 가까운 날짜끼리 겹치지 않게 번갈아 배치
  2.28 개전·해협 봉쇄(ru,−1,사전표시) / 3.15 트럼프, 동맹에 요구(us,+1,사전표시)
  4.7 안보리 거부권(ru,−2,timeline_1) / 4.13 미국 해상 봉쇄(us,+2,timeline_2)
  6.17 양해각서 서명(green,−1,timeline_3) / 7.8 휴전 붕괴(ru,+1,timeline_4)
  8.25 기뢰 제거 발표(us,−2,timeline_5) / 9.18 한국, 파병 않기로(gold,+2, 패널 끝 3초 전, 알파 0.55)
  등장: 사전표시=패널+0.8초, 앵커=문장시작+0.1초, 0.5초 페이드. 점 r4.5, 줄기는 ease_out으로 자람
  날짜: IBM Plex Mono SemiBold 11 (숫자·점만) / 라벨: Sans SemiBold 11.5
휴전 띠: 4.8~7.8 초록 반투명 사각형(높이 14), timeline_3 시작 시 등장, '휴전 4.8 – 7.8'
커서: 가장 최근 이벤트 날짜에 금색 세로 점선
```

---

## 6. 전례 패널 — `P_precedent` (v3)
제목 "한국의 해외 파견 결정", 부제 "전례와 이번 결정"
```
카드 4장 172×212, x = 58 + 190i, y = 150 (등장 시 16px 위로 떠오름), 상단 3px 색띠
  연도 GmarketSans Bold 28 (2026은 금색, 나머지 teal) / 제목 Sans SemiBold 14 / 본문 Medium 11.5 muted, 20px 간격
  2004 이라크 자이툰 부대 [아르빌 파견 · 6자회담 속 대미 관계 · 국내 반대 여론] — past_1 시작, 노무현 뱃지 R24 카드 오른쪽 아래
  2009 청해부대 [소말리아 아덴만 · 해적 대응·상선 보호] — past_3 +0.2초
  2020 작전 구역 확대 [호르무즈까지 확대 · 지휘권은 한국군] — at_word('past_3','호르무즈')
  2026 이번 결정 [전쟁 개입 파병 없음 · 최소한의 활동만] — past_3 끝 −0.6초
```

---

## 7. 대비(찬반) 패널 — `P_versus` (v3)
제목 "파병을 둘러싼 두 입장"
```
두 칼럼 344×262, x=60(지지, teal) / 450(반대, amber), y=120, 상단 3px 색띠
칼럼 제목 Sans SemiBold 16 / 항목 Noto Serif Bold 13.5 + 앞 점 r3, 항목 간격 50px / 출처 Sans 10 muted @ y=366
지지(UPI 기고 · 9월 8일): '호르무즈는 곧 한국의 경제 안보'(debate_2+0.3) · '원유 61% · 나프타 54%가 이 해협 경유'(debate_2+1.6)
반대(Foreign Policy · 9월 10일): '비전투 부대도 표적이 될 수 있다'(debate_3+0.3) · '미국 방공 미사일 재고 감소'(debate_4+0.3) · '2004년 파병 당시의 국내 갈등'(debate_4+1.8)
칼럼 전체는 첫 항목 0.6초 전부터 페이드
```
균형 원칙: 항목 수가 달라도 칼럼 크기·타이포는 동일. 출처를 반드시 표기.

---

## 8. v2 번들 차트 (이식 명세)

| 패널 | 명세 |
|---|---|
| `dots` 도트 매트릭스 | 10×10, 원점 (250,135), 간격 25, 반경 7.5, 0.012초 간격 순차 채움. 강조 점 1개 붉은색 + 4Hz 방사 펄스. 오른쪽에 '1%' GmarketSans/Black 64 + 설명, 아래 "DeepState 실측 교차 확인 18.5% → 19.3%" |
| `gantt` | 축 2025.01~2030.01 (x 250→810, y 368), 연도 눈금. 막대 4개 y=130+56i, 높이 22, ease_out 1.1초, 0.5초 간격. 막대 왼쪽에 라벨(12.5)+노트(9.5). '오늘'(발행일) 금색 세로 점선 +3초 |
| `dual_line` | y 범위 80~96달러(4단위 격자), x 3점, 두 선(브렌트 금색·WTI 청색) 1.8초 드로잉(두 번째 0.5초 지연), 점마다 값 라벨, 끝에 계열명 |
| `fork` | 기점(150,250) '8월 25일' → 세 갈래 곡선 → 카드 3장(440, 150+100i, 340×60), 0.8초 간격 |
| `checklist` | 4항목(150+52i), 체크박스 채움 → 체크 표시 2획 애니메이션(0.35초), 0.7초 간격, 마지막에 '나머지는 전부 해석의 영역' |

모든 번들 차트는 provenance를 읽어 추정 태그를 붙인다(§9).

---

## 9. 추정/출처 태그 (`prov_tag`, v2)
```python
pv = chart.provenance
if pv.verification == 'verified' and pv.sources: 표시 안 함
else: 텍스트 = '추정 · 출처 미기재' if not sources else '추정'
      호박색 1px 둥근 테두리 + SemiBold 10px, 패널 우상단(W−40, 52)
```
v3 패널은 모두 출처가 있는 사실이라 태그 없음. 번들 기반 차트(출처 공란)는 반드시 표시(저장소 G4 원칙 계승).

---

## 10. 카드 (`draw_card`, v3)

지도 위 우상단에 슬라이드 인하는 작은 정보 상자.
```python
위치: x = W − 폭 − 24 (+ 슬라이드 30px → 0, ease_out 0.55초), y = 70(기본)
폭:   max(230, 줄 폭+44, 태그 폭+44, bigs 폭합+20, src 폭+40)
높이: 42 + (bigs 있으면 62) + 21×줄수 + (src 있으면 18)
바탕: 둥근 사각형 r5, rgba(0.05,0.06,0.09,0.86a) / 왼쪽 강조 막대 3px (y+10 ~ y+h−10)
태그: SemiBold 10.5, 강조색, 자간 0.4 @ (x+18, y+23)
bigs: [(큰 값, 캡션)] 가로 배치 — 값 GmarketSans Bold 30 흰색, 캡션 Medium 11 muted, 항목 간 26px
줄:   Medium 13 (quote=True면 Noto Serif Bold 13), 21px 간격
src:  Regular 9.5 muted, 카드 하단
페이드 인/아웃 0.45초
```
v3 카드 목록:
| 장면 | 태그 | 내용 |
|---|---|---|
| open | 기자회견 · 9월 18일 | 전쟁에 개입하는 파병은 없다 / 한국 선박·국민 보호는 최소한으로 계속 |
| route | 2025년 수입 중 호르무즈 경유 비중 | bigs 61% 원유 · 54% 나프타 / src 로이터 · 대통령실 인용 수치 |
| cost | 국제해사기구 · 6월 11일 기준 | 선박 공격 46건 / 선원 사망 14명 / 발 묶인 배 약 1,000척 · 선원 2만 명 |
| review | 거론된 선택지 | 해상초계기 / 군수지원함 / src JTBC·MBC 보도 · 대통령실 “결정된 것 없다” |
| debate | 코리아헤럴드 · 9월 7일 | 전투 격화 · 반대 여론 확산 / 정부, 파병 계획 재조정 |
| decision | 이재명 대통령 · 발언 요지 | “전쟁에 관여하거나 들어가는 / 파병은 없다” (quote) |
| now | 미 중부사령부 발표 | bigs 10억 배럴 호위 작전으로 반출된 원유 |
| now | 2025년 기준 | bigs 61% 원유 수입의 호르무즈 경유 비중 |

**알려진 결함(임시 조치됨)**: review 장면에서 부산 국기 뱃지가 우상단 카드·기사 카드 뒤에 가려졌다 → v3 최종본은 뱃지를 125.6E 22.3N('부산에서 출항')으로 옮겨 회피. **근본 해결**은 카드 영역을 RESERVED로 등록하고 뱃지 배치가 이를 자동으로 피하게 하는 것(Phase 6).

---

## 11. Claude Code 개선 과제
1. 패널을 `panels/` 모듈로 분리하고 레이아웃 좌표를 해상도 스케일 함수로 감싼다(`09` §2).
2. 관계 패널을 데이터 주도로: `nodes`, `edges(from, to, type, state_changes=[(anchor, new_type)])`.
3. 연표 패널 자동 층 배치: 날짜 간격 × 픽셀폭으로 겹침을 계산해 ±1/±2/±3 층 선택.
4. 카드와 지도 뱃지 충돌 검사(카드 영역 RESERVED 등록 후 뱃지 자동 오프셋).

---

## 12. v4.8.0 — 기사 카드 조판 확대 (G7, back_and_forth D-0101 §2, 사용자 결정 D89)

사용자 지시: "기사가 나올 때는 기사를 조판해서 좀 크게". 옛 카드(w 300, 헤드라인 13.5)는 자막(19)보다 글자가 작았다.

- 수치는 전부 `rules layout_480p.article_card`(draw_article·article_geom 리터럴 0): w 440, 매체 15, 날짜 10, 헤드라인 18(줄 간격 26), 부제 12(17), ARTICLE·메모 9, 안쪽 여백 20.
- 헤드라인·부제 **최대 3줄** — 넘치면 `ArticleOverflowError`(렌더 전 preflight, 조용한 잘림 금지).
- 자리: 기본 오른쪽 카드 자리. 연출 `place: center`(슬롯 `center`, `align: center`) = 무대 가운데(세로는 자막 구역 위 공간의 가운데), 그 동안 아래 무대를 `center_dim` 0.93(암전 최대 어둡기)으로 덮는다. fed_policy 기사 2건은 center.
- 전/후: `docs/handoff/reports/phaseG7/article_before_after.jpg`.
- 카드·패널 글자(D-0113 A): 오른쪽 카드 line 13 → 15·tag 12·src 11(줄 간격 24·출처 간격 20), 패널 부제 12.5, 관계선 라벨·연표·차트 글자 ≥ 12, 네트워크 라벨 11 — 전체 표는 09 §9, 수치 정본은 `rules/video_rules.yaml`.

## 13. v5.1.0 — 아일랜드 공통 규약 (G12, back_and_forth D-0123 §1·D-0126 Q1~Q4 A, 사용자 결정 D106·D108)

backdrop 무대 위에 놓이는 내용물은 전부 **아일랜드 상자** 한 규칙(`rules:island`, `engine/island.py`)이다.
- 상자: 둥근 모서리 `radius`, 바탕 = `stage_timeline.bg_rgb × fill_alpha`(배경 사진이 비친다), 흰 테두리 `edge_alpha`, 그림자. 등장 = 카드 규칙(슬라이드 `card.slide_px`·페이드 `card.fade_sec`).
- 차트 아일랜드: `{type: island, kind: chart, box: center|left|right}` — 연출은 이름만 고른다(픽셀 금지). 상자 높이는 모두 같다.
  레인 세로 척도 = min(`stage_timeline.lane_h`, 레인 영역 ÷ 레인 수)(Q2 A, provenance `island.lane_h_effective`). series·date 핀은 차트 아일랜드가 떠 있는 동안에만(밖이면 렌더 전 오류).
- 겹침(Q3 A): 같은 순간 보이는 아일랜드(차트·사진·영상·프리미티브·패널) 제자리 상자 교차 > 0, 자막 구역 교차, 동시 수 > `max_concurrent` = checks `island_overlap` hard. 카드·뱃지는 기존 예약 영역 규칙.
- 패널(Q4 A): backdrop 무대 위 패널만 덮개 대신 `island.panel_box` 상자. 지도·시간축 무대 패널 수치 무변경(골든 무변경). 전 무대 통일은 후보(DECISIONS 메모).
- 뱃지: backdrop 무대에서는 화면 슬롯(map_*) 점에 화면 고정(시간축·지도 앵커 없음).
- **주 아일랜드 상시(v5.2.0 D-0129 §B, 사용자 판정 D113)**: `island.main_required` — backdrop 무대에서 주 아일랜드(`main_kinds`: 차트 아일랜드·프리미티브·사진·영상·기사)가 하나도 보이지 않는 구간이 `card_only_max_sec`(3초, 전환 허용)를 넘으면 checks `backdrop_main_missing` hard `[backdrop-main-missing] t0-t1 {n}s`(타이틀·엔딩 카드·기사 구간 제외, provenance `backdrop.main_missing[]`). 카드는 주 아일랜드가 아니다. 연출 문법: 차트 아일랜드는 오프닝 첫 문장부터, 보도를 인용하는 카드는 article 이벤트로(§14). 코드는 카드를 기사로 바꾸지 않는다(P8 — 검사 + 문법 + 재연출).
- **카드 ↔ 아일랜드 교차(v5.2.0 D-0129 §C)**: 카드·게시물 카드 제자리 상자와 같은 순간 보이는 아일랜드 상자 교차 > 0 = checks `card_island` warning `[card-island]`(provenance `island.card_overlap[]`, 수정 회차 입력 checks.json 에 들어간다).

## 14. v5.1.0 — 기사 프레스 규약 v2 (G12, back_and_forth D-0121 §C·D-0126 Q5·Q6 A, 사용자 결정 D107) — §12 를 대체

옛 오른쪽·가운데 기사 카드(§12, v4.8.0)는 삭제했다(P2 — `article_geom`·슬롯 `center`·`align`·옛 조판 키 없음).
- 순서: 프레스 사진 단독 `press_lead_sec` → 덮개(theme overlay × `overlay_alpha`) + 글자 → 끝에서 `overlay_fade_sec` 페이드.
- 프레스 사진 = 이벤트 `press`(미디어 레지스트리 photo·rights_clear 공식 사진). 없으면 **지금 무대를 블러**(`article_card.press_fallback.blur_px`·`dim` — v5.2.0 D-0129 §A 에서 배경 사진 값과 분리, G12 값 18·0.55 그대로) — 사진을 지어내지 않는다(G4-10·P6, provenance `article[].press: none`).
- 글자 블록: 자막 구역 위 공간의 세로 가운데, 왼쪽 정렬(x = 화면 폭 × `x_left_ratio`), 폭 ≤ `max_w_ratio`. 왼쪽 세로 선(헤드라인 높이, theme rule 색).
  세리프 헤드라인 = 레지스트리 `headline_original`(원문 언어, 인용 부호, `verification.quote_max_chars` 이하) — 없으면 한국어 번역 헤드라인(부호 없음) + source 줄 끝 `translated_note`(Q6 A, provenance `headline: translated`).
  산세리프 부제 = 번역 헤드라인(원문이 있을 때) 또는 요지. source 줄 = `"— {publisher}, {date}"`(날짜 2026.9.24 형식).
- theme dark(검정 덮개·흰 글자)·light(흰 덮개·검은 글자) — 연출이 고른다(P8), 기본 `theme_default`. 줄 수·인용 상한 초과 = `ArticleOverflowError`(렌더 전).
- 콘티 판: 프레스 사진 = 회색 판 + `[프레스: id]`, 덮개·글자는 전편과 같다.
- hormuz 골든 기사 두 컷(15_review_0 164.59·19_debate_0 214.46)은 원문 헤드라인이 저장소에 없어 번역 헤드라인 + "헤드라인 번역" — expected_deltas `g12_article_d0121`. Reuters·Korea Herald 원문 확보는 사용자 몫.
