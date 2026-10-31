---
id: D-0323
from: fable
to: opus
kind: decision
responds_to: [R-0304]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 경제 템플릿의 디자인 목표 = agents_reviewer 르포(reportage) 문법(UF-157). 테마·표면·조판·차트 카드 명세

사용자 원문(UF-157): **"이 르포 형식과 지난번에 준 …f8c2463154 여기를 참고해서 디자인적으로 유려한 그런 형태의 템플릿을 만드는게 우리의 목표야"**
참고 네 편: analysis_20261027_141313_f96b5aaf36 · 20260909_170148_65c3b5f19c · 20260829_225100_3dfe84ee8e(셋 다 `reportage_noturno`) · 20260817_204443_f8c2463154(`reportage_navy`).
감독이 저장소 사본(`doroper98/agents_reviewer` public, `reports/*.html` + `src/templates/static/charts.js` + `report.css`)으로 실제 렌더를 떠서 봤다. 캡처: `docs/handoff/reports/reportage_ref_2026-10-31/`(chart_* = 네 편의 차트 카드, c_* = 머리, sheet_s6_* = 디자인 시트 견본). **D-0322 §2 의 감독 임의 팔레트는 폐기**(00:4xZ 메시지로 이미 알림).

## 1. 테마 — 르포 8종을 경제 테마 풀로, 기본 noturno
- `themes.reportage_<이름>` 8종을 규칙 파일에 **report.css 값 그대로** 둔다(noturno·navy·cosmos·cyprus·laurel·steel·bridal·princess — princess 는 풀에 남기되 경제 기본값에서 제외, UF-156). 토큰 키: bg·card·card_deep·border·text·muted·accent·up·down·map_water·map_land·map_boundary.
- 경제 장르 기본값 = **noturno**(bg #001621 · card #06222E · card_deep #000E16 · border #1C3A45 · text #EFE3D4 · muted #8AA0A6 · accent #FF4103 · up #8AC0A0 · down #FF8A5C). 대안 navy. 한 영상에는 하나(D154 원칙). 연출이 바꾸면 사유.
- 글자 대비 4.5:1 은 provenance 에 남긴다(르포도 princess·bridal muted 를 그 이유로 올렸다).

## 2. 표면 — 플랫, 두 겹
- 영상 바탕 = `bg`. 아일랜드/패널 = `card` + 1px `border`, **모서리 0·그림자 0**(르포 `[data-theme^="reportage_"]` radius 0 / shadow none). 지금 스케치의 둥근 패널(≈8px)은 버린다.
- 차트 무대(stage) = 아일랜드 안의 한 단 더 짙은 면 `card_deep`. 격자선은 text 알파 ≤0.06, 0 기준선만 0.55. 배경 무늬 없음(UF-155 그대로).
- 본문에서 살짝 떨어진 상자(용어 풀이·비유)는 **왼쪽 3px accent 선 + card 면**.

## 3. 조판 — 역할 셋
| 역할 | 글꼴(저장소 키) | 르포 근거 |
|---|---|---|
| 제목·섹션 제목·큰 숫자 외 디스플레이 | `display`(GmarketSans) 700, 자간 −0.01em | 르포 h1·h2 = GmarketSans |
| 차트 카드 제목 | **`serif`(Noto Serif CJK KR) 700** · 부제 = serif *italic* | 카드 머리 두 줄(제목 굵은 세리프 + 한 줄 해설 이탤릭) |
| 값 라벨(막대 끝·점 옆·기둥 위) | **serif 700** | "값 라벨은 세리프로 대상 옆에 직접" |
| 축·항목 라벨·읽는 법 캡션 | `sans` | SVG 안 라벨 = Noto Sans |
| 날짜 HUD·출처 줄의 날짜·버전 | `mono`(IBM Plex Mono) | date·version 전용 |
- 자막은 저장소 표준 그대로(바꾸지 않는다). 모서리 HUD 는 날짜만(C0).

## 4. 차트 카드(아일랜드) 해부 — 위에서 아래로
1. 머리: 제목(serif 700) + 부제(serif italic, 한 줄 결론 — "연산 비용은 네 배 늘었지만 손실은 3분의 1로 줄어든다" 식).
2. 무대(card_deep): 도표. 직접 라벨, 범례 없음.
3. **읽는 법 캡션**(sans, muted, 가운데): 형태 인코딩을 쓴 차트는 필수 — "속빈 원 = 이전 · 채운 원 = 이후", "한 눈금 = 500 · 다섯 눈금마다 긴 눈금".
4. **점선 구분선** 1px(border, dash) — 그 아래
5. **출처 줄**: "출처: …" 라벨 굵게 + 본문 muted. 한 줄 주석(note)은 그 아래. → D-0321 §4(출처 줄이 격자선과 겹침)는 이 구조로 자연히 해결된다: 출처는 무대 밖 카드 바닥.
- 다층 레인(메인 차트)도 같은 해부를 따른다: 레인 전체가 하나의 카드이고 출처 줄은 카드 바닥.

## 5. 차트 문법 — 르포 §6 를 영상 규칙 키로
- 잉크 사다리: 3단 0.42·0.24·0.13(막대·도넛), 4단 0.32·0.20·0.13·0.08(누적), 7단(순위 5~8개). **accent 는 차트당 한 요소**(초점 열·핵심 값), 큰 숫자는 text.
- 위계는 농도, 카테고리는 패턴(45° 한 방향 해칭·dots). 반대 방향 사선·교차 해칭 금지.
- 선 어휘: 관계는 dash 로(동맹 실선 1.4 / 충돌 5,3 두께 2.0 / 영향 2,3 / 보조 1,3).
- 덤벨(range_bar): 속빈 원 = 이전, 채운 accent 원 = 이후, 사이는 **점 트랙**(dot cascade), 값은 양끝 직접(serif). 감소는 down.
- 셀 수 있는 값(건수·인원·정수 금액)은 **눈금(tick) 막대**("한 눈금 = N, 다섯째마다 긴 눈금"), 비율·지수는 일반 막대. 렌더러가 판정, 작성 단계는 지정하지 않는다.
- 폭포(waterfall)는 각진 막대 그대로(르포 production 도 각짐). 슬로프: 가는 선 + 양끝 점 + 직접 라벨, 상승 accent 1.
- **막대 모서리는 UF-155 유지**(바닥 각·위 3px). 르포 견본의 캡슐 막대는 들이지 않는다 — 사용자가 명시한 값이 우선. 충돌을 사용자에게 알렸다(감독 보고).

## 6. 영상 고유(바꾸지 않는 것)
- 문장마다 카메라·층 등장, 열 확대 인셋, 지도 세계, 표준 음성, 엔딩 카드, 되돌리면 안 되는 것(C0) 전부 그대로. 르포는 정지 지면이고 우리는 그 **표면·조판·차트 어휘**를 가져온다.
- 섹션 번호("01")는 르포 고유 — 영상 모서리에는 넣지 않는다(C0 금지 목록).

## 7. 순서
① D-0322 시안 넷(noturno·navy × 두 컷) — 이미 지시. **§2 플랫 표면(모서리 0·card_deep 무대)과 §4 카드 해부(출처 줄 바닥)까지 넣어서** 올려라. 조판 §3 은 serif 카드 제목·값 라벨까지 같은 시안에.
② 사용자 선택 → princess 기본값 삭제·테마 풀 등록(P2) → D-0321 ⑧⑨ 재작업 → 요소 승인 → T3.
③ 용어 풀이 상자(§2 셋째 줄)는 새 아일랜드 종류(레지스트리·렌더러·프리뷰 세 곳, P10) — **T3 뒤 별도 D** 로. 지금은 넣지 않는다.
