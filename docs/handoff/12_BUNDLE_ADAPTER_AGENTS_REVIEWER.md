<!--
tier: 2
last_synced_with: v0.43.4
ssot_for: [v2-bundle-adapter]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 12. agents_reviewer 번들 어댑터

참조 코드: `v2_bundle_ratcliffe/plan.py` (어댑터), `render2.py` (연출층), 입력 예: `https://analysis-reports.pages.dev/analysis_20260829_115457_ec53e620b2.bundle.json` (agents_reviewer v8.5.9 생성, 264KB)

---

## 1. 번들 구조 (관찰된 필드)

```jsonc
{
  "generated_at": "2026-08-29T...",
  "report": {
    "report_id": "...", "headline": "모스크바에 내린 수송기 한 대, 그 안에서 무엇이 오갔나", "deck": "...",
    "video": { "intro_narration": [2문장], "intro_narration_tts": [선택], "outro_narration": [2문장] },
    "theme": { ...토큰 }
  },
  "sections": [ {                                   // 12개
    "section_id": "s1", "heading": "활주로를 떠난 한 대",
    "video": { "narration": [4문장], "narration_tts": [4 또는 빈 배열], "emphasis": [구절...], "highlights": [인용...] },
    "chart_refs": ["ch-1"], "claim_refs": [], "map_ref": null, "image_refs": []
  } ],
  "charts": [ {
    "chart_id": "ch-1", "type": "stakeholder_map" | "dot_matrix" | "gantt" | "dual_line",
    "title": "...", "data": {...},
    "provenance": { "verification": "inferred", "sources": [], "origin": "narrative_inference", "confidence": "medium" }
  } ],
  "map": {
    "markers": [ {"id": "moscow", "name": "모스크바", "lng": 37.62, "lat": 55.75, "value": "8월 25일 도착", "kind": "...", "highlight": true, "label_side": "right"} ],
    "arcs":    [ {"from_id": "andrews", "to_id": "riga", "kind": "flow" | "tension", "label": "...", "label_t": 0.5} ],
    "legend": [...], "prerendered_svg": "..."
  }
}
```
`stakeholder_map.data`: `nodes[{id, label, col(left|center|right), kind(person?), flag(ISO2?), logo(도메인?), role, accent?}]`, `edges[{source, target, type(영향|연관|대립|동맹), label}]`.

---

## 2. v2 매핑 (실제 사용)

| 번들 | 영상 |
|---|---|
| `report.video.intro_narration` | 프롤로그 문장(`intro_0..`) |
| `sections[].video.narration` | 섹션 문장(`s1_0..`) |
| `narration_tts[i]` (비어 있으면 저장소 `tts_of(narration[i])`) | 발음 텍스트 |
| `emphasis` | 자막 강조(`em_segments_line`) |
| `highlights` | 인용 카드 |
| `chart_refs` → `charts` | 패널(network, dots, gantt, dual_line) |
| `map.markers` / `arcs` | 마커 / 호(비행 경로 plane=True) |
| stakeholder `nodes` (kind/flag/logo) | 인물·국기·기관 뱃지 |
| `report.headline` / `deck` | 타이틀 카드 |
| `provenance` | "추정 · 출처 미기재" 태그 |

연출(어느 섹션을 지도/패널로, 카메라 위치)은 약 120줄의 수작업 표였다(저장소 `art_direction.json`에 해당).

---

## 3. 저장소에서 계승한 함수 (import 방식으로 사용)

```python
sys.path.insert(0, 'osint_generator/hyperframes/scripts'); import bundle_to_video as B
B.tts_of(text)                   # 발음 정규화(날짜·소수·고유어 수사·조사)
B.em_segments_line(text, emph)   # [[구간, 0|1], ...]
B.build_corpus(bundle); B.sentence_grounded(sent, corpus)   # 근거 검사 — v2 52문장 전부 통과
B.norm_gantt(chart, today)       # {'tasks': [{label,start,end,phase}], 'today'}
```

### 3.1 발견한 버그 (Claude Code가 수정)
| 함수 | 입력 | 출력(현재) | 올바른 출력 |
|---|---|---|---|
| `tts_of` | "18개월" | "열여덟 개월" | "십팔 개월" (개월=한자어 수사) |
| `tts_of` | "83.90달러" | "팔십삼쩜구영딸러" | "팔십삼 점 구 달러"(된소리 표기 섞지 말 것, 불필요한 0 생략) |
| `norm_network` | `type: stakeholder_map` | `None` | nodes/edges 정규화 결과 |

v2에서는 `fix_tts()`로 "열여덟 개월"만 치환하는 임시 패치를 썼다.

---

## 4. 엔티티 언급 탐지 (v2 `plan.py mentions()`)
```python
ALIAS[nid] = {라벨, 라벨의 마지막 어절(성)} + 수동 별칭('트럼프 대통령', 'CIA', '이란' 등)
for 문장: 각 노드 별칭이 처음 나타나는 글자 위치 i → (nid, i/len(text))
시각 = t0 + 비율 × dur
```
관계 패널에서 해당 노드를 금색 펄스로 강조하는 데 썼다. 한계: 호칭이 바뀌면("CIA 수장", "랫클리프 국장") 누락 → 번들이 문장별 `entity_refs`를 주는 것이 정확(§6).

---

## 5. 12막 문제 — 섹션을 장면으로 1:1 매핑하지 말 것 (지적 4)

v2가 사용자에게 "12막에 우겨넣은" 인상을 준 원인은 번들의 12개 섹션을 그대로 12개 장면으로 만들고, 섹션마다 제목·번호를 띄운 것이다.

새 어댑터 규칙:
1. 번들은 **원고 재료**다. 문장·사실·지도·차트를 가져오되 장면 구성은 새로 한다.
2. 섹션 경계가 아니라 **공간(map_ref/마커 집합)과 정보 유형(차트 종류)**이 바뀔 때 장면을 나눈다. 같은 공간을 쓰는 섹션은 합친다.
3. 섹션 제목(heading)은 화면에 띄우지 않는다. 필요하면 유튜브 챕터명으로만.
4. 번들 문장이 금지 문구 린트에 걸리면 **다시 쓴다**(번들 원문도 예외 아님). 발음 텍스트는 `03` §4 규칙으로 재작성.
5. 번들 수치는 가능하면 외부 실측과 교차 검증(v2: DeepState로 "18개월간 약 1%" 확인 → 18.5%→19.3%, +0.8%p를 화면에 병기).
6. 번들 핵심 전제는 웹 검색으로 사실 확인(v2: 랫클리프 8월 25일 방러, 나리시킨·보르트니코프 면담은 NYT·Axios·Moscow Times 등으로 확인. 단 "푸틴이 만나지 않은 것은 계산된 선택"이라는 번들 해석과 "예정된 만남을 푸틴이 취소"라는 러시아 독립매체 보도 사이 뉘앙스 차이를 사용자에게 고지).

---

## 6. agents_reviewer 번들 스키마 개선 요청안 (사용자 승인 후 agents_reviewer에 반영)

| 필드 | 위치 | 목적 |
|---|---|---|
| `date` | 문장 단위 | 우상단 날짜 배지(사건일) |
| `entity_refs: [id]` | 문장 단위 | 뱃지 등장 시점을 정확히(별칭 매칭 불필요) |
| `map_refs: [marker_id]` | 문장 단위 | 카메라 자동 프레이밍 입력 |
| `sources: [{publisher, date, url}]` | 문장/주장 단위 | 카드 출처 줄, 검증 |
| `narration_tts` | 문장 단위, 항상 채움 | `03` §4 규칙 준수(숫자·기호 금지) |
| `entities` 사전 | 번들 최상위 | `{id: {kind: person|org|country, names[], iso2, org_domain, role}}` → 엔티티 레지스트리와 조인 |
| `shot_hint` | 문장/섹션 선택 | "map:gulf", "panel:timeline" 같은 연출 힌트(강제 아님) |
| 세계 좌표 커버리지 | map.markers | 권역 밖 좌표도 허용(엔진이 광역 티어로 처리) |
| 금지 문구 | 생성 단계 | agents_reviewer 원고 생성 프롬프트에 `03` §2 목록 주입 |

---

## 7. 어댑터 모듈 설계 (Claude Code)

```
bundle/
├─ load.py          # 번들 로드·스키마 검증(Pydantic, 버전별 관용 처리)
├─ text.py          # tts_of(수정본), em_segments_line, grounding
├─ charts.py        # 정규화기 모음 (bundle_to_video.py에서 이관, norm_network 확장)
├─ entities.py      # 노드/entities → 엔티티 레지스트리 매핑, 언급 탐지(폴백)
├─ to_script.py     # 번들 → script.yaml 초안 (장면 묶음 제안, 린트 결과 주석)
└─ to_direction.py  # 번들 map/charts → direction.py 초안 (카메라·패널 제안)
```
출력은 **초안**이다. 사람(또는 Claude)이 장면 구성과 문장을 다듬은 뒤 plan 단계로 넘긴다.
