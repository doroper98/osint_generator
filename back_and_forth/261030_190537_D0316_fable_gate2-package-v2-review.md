---
id: D-0316
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 판정 — 게이트 ② 자료 v2(artifacts 3e5926b) 사용자에게 전달(승인·A/B 선택 대기). 결정: ① act1_0~1 드론 비행은 **특정 타격이 아니면 쓰지 않는다** → 출처 있는 정유소 타격 마커·boom 으로 교체 ② `[text-restates-narration]` 조사 떼기·패널 items 포함 ③ geo catalog.mp4 전달본 30 MB 이하

## §0 눈 확인(감독)
- geo 16컷: 카드 0, 12컷 OFAC 핀(로스네프트·루코일 · 미 재무부 제재 2025. 10. 22) 들어옴, 사진 가운데 큰 자리, 타이틀 부제 "쇼케이스 템플릿 · 지경학 · …", 엔딩 머리 줄 오른쪽 "쇼케이스 템플릿 · 지경학". 빈 구간 최장 2.3초(요약). hard 0.
- econ 12컷·A/B 시트(act1_2~5, 6시각 좌우)·카탈로그 2편(hard 0)·표·미디어 요약 — 형식 통과. econ 엔딩 표시 줄 확인.
- 전달: 시트 2·A/B·타이틀·엔딩 2 를 사용자에게 보냈다. catalog.mp4 는 econ 24.5 MB(전달 가능)·geo 55 MB(30 MB 초과 — 전달본 필요).

## §1 결정
1. **드론 비행(act1_0~1)**: 비행(flight) 이벤트는 **출처 있는 특정 타격**(날짜·장소·보도)에만 쓴다. "봄부터 이어진 타격" 같은 총괄 문장에 출발점(34.8°E 50.9°N)을 가정한 비행을 붙이면 특정 사건처럼 읽힌다(G4 — 지어낸 궤적). 교체: 그 문장 구간은 **정유소 타격 마커 + boom** 을 날짜순으로 하나씩(diesel_road_2026 의 타격 목록·출처 재사용), 비행은 랴잔 10월 15일(출처 있음)에만 남긴다. 엔딩 "비행 경로·출발 위치는 개략 표현" 문구는 랴잔 비행에만 걸리게 좁힌다. 검사 `[flight-unsourced]` hard: flight 이벤트에 `source`(claim id) 없으면 실패.
2. **`[text-restates-narration]` 개선 승인**: 어절 비교 전 조사(은/는/이/가/을/를/의/에/에서/으로/로/와/과/도/만) 떼기 + panel `items`·checklist 항목·cascade 줄까지 비교 대상에 포함. GL135 체크리스트 놓친 사례를 시험으로.
3. **geo catalog.mp4 전달본**: `-c:a copy` 재인코딩으로 30 MB 이하 한 벌 더(`catalog_deliver.mp4`) — 감독이 사용자에게 보낸다. econ 은 그대로.
4. 게이트 ② **승인·A/B 선택은 사용자** — 답이 오면 감독이 D(from: user)로. 승인 전 final·결합본 렌더 금지(콘티 판 기록 require_animatic 그대로).
