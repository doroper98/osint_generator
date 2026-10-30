---
id: D-0306
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — UF-148 오른쪽 위 카드 규약 폐지(P2 삭제). 내레이션을 되풀이하는 화면 글자 금지. 구석으로 밀려났던 요소는 가운데로 크게

## §0 사용자 원문(2026-10-30, 원장 UF-148 — 화면: showcase_geo 콘티 판 카드 "표적 / 원유를 캐는 유전이 아니라 경유·휘발유를 만드는 정유소")
> "이 오른쪽 상단에 뜨는 아일랜드 없애도 될거 같아. 어짜피 자막으로도, 음성으로도 그 이야기를 하는데 굳이 더 정신 사납게 오른쪽위에 카드인지 아일랜드까지 띄울 필요는 없을거 같아. 오히려 더 정신 없고, 저 오른쪽 상단의 카드 떔에 왼쪽 하단으로 억지로 옮겨져야 했던 요소들을 중앙으로 옮겨서 크게 보여주거나, 적절히 정돈하는게 좋을거 같아."
> 보충: "오른쪽 상단의 카드 자체의 규약을 없애라는 뜻이야."

## §1 결정(C0 되돌리면 안 되는 목록에 "카드" 는 없다 — 폐지 가능. 모든 트랙·스케치 포함, C12 ③)
1. **`card` 이벤트(오른쪽 위 구석 성명 카드) 폐지 — 플래그가 아니라 삭제(P2).** `registries.event_types` 에서 `card` 제거, `engine/cards.py` 구석 카드 렌더러·`layout_480p.card`·placement `card` 슬롯·`qa_checks.card_over_panel.cover_types` 의 card 삭제, `CardEvent` 모델 삭제(연출에 남아 있으면 P10 오류). 기사 카드(article)·게시물(post)·인용(quote, 가운데 덮개)·엔딩/타이틀 카드는 **대상이 아니다**(구석 성명 카드만).
2. **되풀이 금지 원칙**: 내레이션(자막)이 말하는 내용을 화면 글자로 다시 쓰지 않는다. 남는 글자 요소(panel statement·cascade·marker label·island 제목)에 검사 `[text-restates-narration]` hard — 요소 문장과 그 순간 원고 문장의 정규화 어절 겹침이 `qa_checks.restate_overlap_max`(제안 0.6) 이상이면 실패. 연출 프롬프트 한 줄: "자막이 말하는 것은 화면 글자로 되풀이하지 않는다. 화면 글자는 수치·이름·목록·출처처럼 자막에 없는 것만."
3. **숫자 카드의 대체**: 옛 `bigs`(큰 수치 "17만 6천 ton")는 ① 지도 위면 그 자리 marker `label/sub`(핀 라벨, 큰 글자 `marker.big_size` 신설 제안 26) ② 시간축이면 series 끝값/핀 ③ 어디에도 못 붙으면 **버린다**(원고가 말한다). 새 요소는 만들지 않는다(20 §4.3).
4. **구석이 비었으니 가운데로**: 사진·영상·컷아웃 기본 슬롯(`placement.auto_media`·`stage_slots`)을 구석(map_right_low 등)에서 **화면 가운데 큰 자리**로 바꾼다 — 사진 `media_box` 폭 ≈ 화면 54 %(제안; 액자 clip_frame 84 % 와 구별), 날짜 뱃지 아래·자막 위. 두 요소가 동시에 뜨면 좌우 2분할(각 44 %). 인셋은 표적을 따르므로 그대로. 값은 감독 제안 — 프리뷰로 본다.
5. **이식**: 기존 연출(hormuz 골든 74·diesel 74·showcase_geo 10·econ 4·china 트랙)에서 `card` 를 `tools/migrate_cards.py` 로 §3 규칙에 따라 변환·삭제(변환 표를 R 에). **hormuz 골든 25컷은 재기준**(C0.1, 근거 이 D) — 바뀐 컷 번호 기록. diesel v2 는 완성작이라 연출 파일만 이식(재렌더 없음).
6. 장치(C12): `[text-restates-narration]` hard, 레지스트리에 card 없음(P10 — 연출에 쓰면 로드 오류), 시험 3(이식 도구·되풀이 검사·골든 재기준). 원장 UF-148 guards 추가.

## §2 순서·범위
- **쇼케이스 세션 3**: D-0305 ①② 뒤 **곧바로**(게이트 ② 자료 전) §1 전부 → showcase_geo·econ 프리뷰 재생성 → 게이트 ② 자료에 "카드 없는" 컷 포함. 콘티 판 재렌더 없음.
- **중국 트랙 감독**: sweet-galileo 를 merge 해 같은 규칙으로(연출 전이면 처음부터 카드 없이).
- **경제 템플릿 세션**: 하루 1회 merge 로 따라온다. earnings 연출 예시에 card 없음.
