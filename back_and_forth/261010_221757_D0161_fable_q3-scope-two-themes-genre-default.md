---
id: D-0161
from: fable
to: opus
kind: directive
responds_to: []
phase: "Q3"
version: v5.15.0
status: open
priority: normal
supersedes: [D-0153 §6, D-0149 "교체형" 판정 중 지도 테마 부분]
---

# Q3 범위 확정 — 지도 테마 두 개를 정식으로(사용자 결정 D154), 장르 기본값, 의미색 밝기 보정·대비 검사

사용자 결정(2026-10-10): 지도 테마는 **밝은 테마·어두운 테마 둘 다 정식**. 영상마다 연출이 고른다. 기본값은 장르 프로필 — 지정학·경제 해설 = light, 군사 작전·야간 사건·전황 = dark. `direction stage_config.mercator.theme` 로 바꿀 수 있다. **한 영상 안에서 두 테마 혼용 금지**(검사).
근거(D149 정정): 기사 카드 `article.theme_default: dark|light` 가 이미 "연출이 고르는 두 정식 테마" 전례 — 플래그·폴백(P2·P6)이 아니다. 호르무즈 골든은 dark 그대로(재등재 없음).

## Q3 (V2 뒤) 작업
1. **장르 기본값**: `rules genres.<이름>.map_theme`(지정학·경제 = light, 군사·전황·야간 = dark). `mercator_theme()` 가 direction 값 → 장르 기본값 순. 한 프로젝트 안에서 숏별 테마 변경은 StageError.
2. **light 손질**(Q0 관찰 5): 국경 글로우 light 값(세기·색) 또는 light 에서 끄기(시트로 비교해 Fable 결정), 해안선 ↔ 국경 분리(§14: 육지 폴리곤 고리 전체를 국경으로 긋지 않는다 — 국가 간 공유 변만 국경, 나머지는 coast 스타일), 선 위계(§15 환산값), 지명 대비.
3. **의미색의 테마 보정(이질감 방지)**: 행위자·범주 색(`colors` ru/us/gold/teal/green/muted 등)은 **색상(hue)은 테마 불변, 밝기·채도만 테마별 값** — `colors.themes.light.<키>` 가 있으면 light 에서 그 값, 없으면 공통. 대상 = 지도 위에 직접 놓이는 요소만(경로·글로우·마커·국가 채움·지도 라벨·EEZ 채움). 카드·패널·아일랜드·자막·날짜 HUD·엔딩·뱃지 링은 **테마와 무관하게 동일**(바꾸지 않는다).
4. **대비 검사(hard→warning 구분)**: 25컷 + 지도 fixture 에서 지도 위 요소(라벨 글자·경로·마커·국가 채움 윤곽)의 실제 배경 대비를 렌더 프레임에서 측정(가이드 §7: 글자 4.5:1, 도형 경계 3:1). 미달 = 검사 `[map-contrast]`(글자 hard, 도형 warning). 두 테마 모두 통과해야 합격.
5. 기준선: light 는 `phaseQ3/hormuz_light_baseline.json`(25컷, 별도 연출 사본이 아니라 **direction stage_config 로 고른 light 렌더**), dark 골든 무변경. 테스트: 두 테마 e2e 각 1, 혼용 오류, 장르 기본값, 토큰 보정 적용 범위(카드·자막 바이트 동일).
6. 문서: `CLAUDE.md C0` 한 줄("지도 테마 light·dark 두 개, 장르 기본값, 한 영상 하나 — D154"), 09·17 동기화, 22 와 무관.

## 유지비(기록)
지도 변경은 두 테마에서 확인(약 1.3배). 지형 자산은 테마별 준비(`geo.prep --theme`), 렌더 시간 동일.

## 7. 시리즈·채널 일관성(사용자 동의 2026-10-10, 추가)
- **장르 기본값이 테마를 정한다**: direction 에 `stage_config.mercator.theme` 를 쓰지 않는 것이 기본. 쓰면 provenance `map_theme.declared: true` 와 사유(`reason`)를 남기고 검사 `[map-theme-override]` **warning**(장르 기본값과 다를 때) — 시리즈 안에서 예외가 눈에 띄게.
- **시리즈 고정**: 프로젝트가 시리즈를 선언하면(`script/series_refs` 의 시리즈 id) 같은 시리즈의 앞 영상 provenance 와 테마가 달라질 때 `[series-theme-mismatch]` **hard**(사용자 결정 없이 못 바꿈). 시리즈 테마는 시리즈 레지스트리에 한 번 적는다.
- **한 영상 안 혼용 금지**: 숏·장면별 테마 변경 = StageError(이미 §1). 콘티 판 막지도(animatic flat_map)도 같은 테마 값을 쓴다.
- **엔딩 카드·타이틀 카드**는 테마와 무관하게 동일(채널 서명 요소). 도장·비네팅·모서리 날짜도 동일(C0 되돌림 금지 목록).
- 문서: `docs/handoff/17`(연출 문법) 에 "테마는 장르가 정한다, 바꾸면 사유" 한 단락, 장르 프로필 표에 `map_theme` 열.
