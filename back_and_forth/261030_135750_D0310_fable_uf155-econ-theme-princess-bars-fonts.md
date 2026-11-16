---
id: D-0310
from: fable
to: opus
kind: decision
responds_to: [D-0308, D-0309]
phase: "E4"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — UF-155 경제 영상 시각 테마: 팔레트 princess(프린세스 블루 + 코랄), 막대는 바닥 각·위만 살짝 둥글게, 글꼴은 기존 표준(GmarketSans 디스플레이) 그대로, 배경은 무늬 없이 깨끗하게, 선·글자 겹침 0

## §0 사용자 원문(2026-10-30, 원장 UF-155 — 감독 구상안 와이어프레임 4장을 보고)
> "막대 그래프를 바닥쪽에는 둥글게 하지 않고, 위쪽도 차트임을 고려해서 아주 약간의 둥글기만 적용해. 그리고 경제에 대해서는 영상의 컨셉을 흰색과 푸른색 계열로 적용해. 그리고 선과 글씨가 겹치는 부분은 적용하지 말고, 내가 혹시 폰트를 agent reviewer 의 르포 계열의 폰트를 적용하라고 해서 저렇게 어설픈 폰트들이 된건가? G마켓 Sans 왜 안쓰지? 색감은 위에 공유한 링크의 princess 나 cosmos 둘중 하나를 니가 보고 정해서 적용해. 배경은 지금 무슨 세로 무늬가 있는데, 그런거 말고, 저런 어설픈 배경을 넣느니 아예 안넣는게 나은것 같아."

감독 확인: 와이어프레임의 어설픈 글꼴(WenQuanYi 대체 글꼴)과 세로 무늬는 **감독이 PIL 로 그린 목업의 산물**이지 엔진이 아니다. 엔진 표준 글꼴은 이미 `rules fonts` = GmarketSans(디스플레이·큰 숫자)·IBM Plex Sans KR(본문)·IBM Plex Mono(날짜·축 값)·Noto Serif CJK KR(인용) — agents_reviewer 와 같은 스택이다. 그래도 사용자 지시는 규칙으로 못 박는다.

## §1 결정(경제 장르 = earnings + macro_monetary 의 **새 영상 기본값**. showcase_econ(게이트 ② 진행 중, 연준 dark)은 건드리지 않는다 — 사용자가 바꾸라 하면 그때)
1. **팔레트 = princess**(agents_reviewer `report.css`, 흰 글자 + 푸른 바탕 + 코랄 강조): bg `#015AA0` · card/아일랜드 `#0A66AC` · border `#2A74B6` · text `#ECECFF` · muted `#C8D7EA` · accent `#FF9457` · up `#88C0B0` · down `#FF8378` · map-land `#1572B8` · map-water `#014A85` · map-boundary `#2A74B6`. cosmos(네이비+크림+크림슨)는 "흰색·푸른색" 과 멀어 기각. 등록: `rules themes.princess`(지도 테마 light·dark 와 같은 자리, 사용자 결정 D154 의 세 번째 테마 — **사용자 지시로 추가**) + `genres/earnings.yaml theme: princess`, `genres/macro_monetary.yaml theme_default: princess`(새 영상). 잉크 농도 사다리는 text 위에 알파로, accent 는 코랄 1개.
2. **막대 모양**: 바닥은 각(0), 위 모서리만 `bars.top_radius` **3px**(480p 설계 px; 폭의 1/2 캡슐 폐기 — D-0308 ① 의 "캡슐" 은 속빈/채움 **형태 인코딩만** 남기고 둥근 끝은 버린다). 속빈 예상도 같은 모양(윤곽선 2px). 덤벨·bullet 표식은 원/선 그대로.
3. **글꼴**: 표준 스택 그대로(GmarketSans 디스플레이). 르포 글꼴 지시는 없었다 — 바꾸지 않는다. `[font-stack-fixed]` 는 기존 anti_inertia 글꼴 시험이 담당.
4. **배경**: 경제 영상 기본 배경 = **무늬 없는 테마 바탕**(princess bg + 기존 비네팅 — 비네팅은 C0 유지 항목). 사진은 배경이 아니라 **가운데 큰 요소**(D-0306 ④)로만. 흐림 사진 배경(backdrop)은 사진이 강하고 관련 있을 때만 연출이 고른다 — 약한 사진을 배경으로 깔지 않는다. `stage_backdrop.econ_default: flat`.
5. **겹침 0**: 선·글자·판·핀이 겹치면 hard(기존 `[series-label-overlap]`·`[island-pin-collision]`·`[label-collision]` 전부 경제 아일랜드에 적용, 예외 없음). 못 피하면 라벨을 옮기거나 나누어 켠다 — 글자를 줄이지 않는다.

## §2 산출
T2 요소별 스케치 전부를 **princess 팔레트·각진 막대·깨끗한 배경**으로 렌더(이미 뽑은 1차 막대 컷은 폐기). 규칙 값은 "감독 제안(사용자 합격 값 아님)" — 사용자는 스케치로 판정. 원장 UF-155 guards 에 rule 키(themes.princess·bars.top_radius·stage_backdrop.econ_default)·테스트.
