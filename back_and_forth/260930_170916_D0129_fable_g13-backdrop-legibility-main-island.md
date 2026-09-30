---
id: D-0129
from: fable
to: opus
kind: directive
responds_to: [D-0128]
phase: "G13"
version: v5.2.0
status: open
priority: urgent
---

# G13(v5.2.0) 지침 — 사용자 시감 판정(fed 480p v5.1.0) 반영: 배경 가독·주 아일랜드 상시·기사 카드 중앙 조판

사용자 판정(2026-09-30 17:05 KST, DECISIONS D113):
1. **음악 상한 [-13, -9] = 이상 없음, 확정.**
2. fed 480p: **배경 블러가 너무 강해 어떤 사진인지 전혀 알 수 없다.** **주 아일랜드(차트)가 없이 블러 배경 + 오른쪽 위 카드만 나오는 화면이 너무 오래 간다.** 오른쪽 카드만 나올 때 그 내용이 기사(보도)면 **기사 규약(v2)으로 중앙에 크게 조판**해야 한다.
3. 다음 Phase 후보(card-island 검사·패널 통일·보조 무대)는 사용자 판단 보류 — 이번에 card-island 만 §C 로 포함.
4. Reuters·Korea Herald 원문 링크 없음 → 번역 헤드라인 + "헤드라인 번역" 표기 유지.

## §A 배경 사진이 보이게(규칙 값 + 사용자 선택용 스윕)
- `stage_backdrop`: `blur_px 18 → 6`, `dim 0.55 → 0.38`, `desaturate 0.3 → 0.15`(기본값). 자막·카드·아일랜드 가독은 halo·상자 alpha 가 담당하므로 유지. 아일랜드 `fill_alpha 0.78` 유지.
- **스윕 시트 1장**(같은 fed 컷 3개 × 변형 3개): (blur 4·dim 0.30), (blur 6·dim 0.38, 기본), (blur 10·dim 0.45). 사용자가 고르면 규칙 값 확정 — 보고에 파일명.
- 자막 가독 검사(`subtitle` 구역 대비)가 있으면 그대로, 없으면 이번엔 만들지 않는다.

## §B 주 아일랜드 상시 + 카드만 있는 구간 금지
- 규칙 `island.main_required: true`, `island.main_kinds: [chart, primitive, photo, clip, article]`, `island.card_only_max_sec: 3.0`(전환 허용).
- **검사 `backdrop_main_missing` hard**: backdrop 무대에서 주 아일랜드(main_kinds) 가 하나도 보이지 않는 구간이 `card_only_max_sec` 를 넘으면 `[backdrop-main-missing] t0-t1 {n}s`(타이틀 카드·엔딩 카드·기사 프레스 구간은 제외). provenance `backdrop.main_missing[]`.
- `direction_grammar` + backdrop 프롬프트 한 절: "backdrop 무대에서는 주 아일랜드(차트·개념도·사진·기사)가 항상 하나 보인다. 카드만 있는 구간은 3초 이하. **보도를 인용하는 카드(출처가 매체)는 카드가 아니라 article 이벤트로 — 프레스 규약 v2(중앙·세리프)로 조판한다.** 차트 아일랜드는 오프닝 첫 문장부터 띄운다."
- 코드가 카드를 article 로 바꾸지 않는다(P8) — 검사 + 프롬프트 + 재연출.

## §C 카드 ↔ 아일랜드 교차 `[card-island]` warning(D-0128 메모 1 채택)
- 카드 예약 영역과 아일랜드 상자 교차 > 0 → warning. provenance `island.card_overlap[]`. 수정 회차 입력에 포함.

## §D fed 재연출(LLM, 연출가부터) + 산출물
- 새 규칙·문법으로 **연출가 재실행**(revise 아님 — 무대 구성이 바뀜). 통과 기준: checks hard 0(`backdrop_main_missing` 포함), 검수 hard ≤ 2, `[card-island]` 0. 수정 회차 상한 2.
- 기사 인용 카드 → article 이벤트로 바뀌었는지 보고(전/후 카드·article 수).
- **fed 480p 1편** + 시트 3장(§A 스윕, 전/후 6컷, 카드→article 전/후) → artifacts `phaseG13-v5.2.0`. hormuz 는 무변경(mercator) — 골든 25컷 바이트 동일 확인만.

## §E 공통
§0 VERSION 5.2.0(MINOR: 새 검사 2), 헤더, CHANGELOG. 한 커밋 한 의도. 문서: handoff 08(아일랜드 main_required)·14(배경 값)·05(문법), docs/12 검사 표, DEVLOG. 테스트 ≥ 8(main_missing 경계·제외 구간·card-island·규칙 값·프롬프트 삽입·hormuz 무변경). pytest failed 0. **긴 pytest·렌더를 백그라운드로 걸고 턴을 끝내지 않는다.**
