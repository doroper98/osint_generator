<!--
tier: 2
last_synced_with: v3.5.0
ssot_for: [prompt-director_bundle]
depends_on: [prompts/director_user.md, workers/director_worker.py, bundle/to_direction.py]
last_review: 2026-09-29
note: DirectorWorker user prompt 의 선택 블록 `{bundle_materials}` — intake/bundle_materials.json(번들 어댑터 재료)이 있을 때만 들어간다(D-0063 작업 4). 자리표시 {materials} 는 워커가 .replace() 로 채운다(C2). 이 주석은 로더가 떼어 낸다.
-->
번들 재료 (intake/bundle_materials.json — 제안·재료일 뿐, 강제 아님)
------------------------------------------------------------------
분석 번들의 지도·차트에서 뽑은 재료다. 쓸지·어떻게 쓸지는 연출 의도로 정한다.
- places: 장소 좌표·종류·값. 쓰려면 direction 의 places 에 옮기고 marker 이벤트로 띄운다.
- paths: kind flow = 이동 경로(route 후보), tension = 긴장선. 쓰려면 paths 에 옮긴다.
- panels: 엔진 패널 모델을 이미 통과한 데이터(kind·title·provenance 포함). 그대로 panel 이벤트의 data 로 쓸 수 있다.
  provenance 는 바꾸지 않는다(추정 태그는 엔진이 그린다).
- scene 은 번들 초안의 장면 id 다. 최종 원고 장면과 다를 수 있으니 원고 문장에 맞춰 시각을 정한다.
- badges 는 엔티티 레지스트리에 있는 것만이다. unmatched 는 뱃지로 쓰지 않는다.
- media 는 usable true 만 쓴다(권리 확인된 것).
- versus 는 논쟁 양측이다. 쓸 때는 양측을 같은 무게로 둔다.

```json
{materials}
```
