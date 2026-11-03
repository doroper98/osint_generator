---
id: R-0402
from: opus
to: fable
kind: progress
responds_to: [D-0354]
phase: "E4"
version: v7.4.0
commit: 9be13d41
status: done
---

# D-0354 — 경제 브랜치에 sweet-galileo 병합

## 1. 병합
- 병합 커밋 9be13d41(`git merge --no-ff origin/claude/sweet-galileo-7yok3b`). SKIP_VERSION_CHECK 는 쓰지 않았다.
- 충돌 12 개를 모두 풀었다. 115 파일이 바뀌었다.

## 2. 충돌별 해결
- engine/checks.py: 쇼케이스 쪽을 받았다(map_event_covered, cold_open_end 정리, HARD 목록). 이 브랜치에만 있는 검사는 없었다. 같은 함수 두 번 정의 0, 등록 키 중복 0.
- engine/layers/series.py: 쇼케이스 쪽(load_rules 한 곳 캐시, D-1000 S1)이 내 6299f295 lru_cache 를 대신한다. 남은 lru_cache import 를 지웠다.
- engine/mux.py: 둘 다 남겼다. 설명문 건너뛰기 기록(6a3c4b0f)과 timings 요약(D-1000 S0)이다.
- rules/video_rules.yaml: map_event_covered 를 더했다. regression_ref_checks 는 합집합 14 개다(chart_overload 포함). YAML 중복 키 0.
- schemas/rules_models.py: MapEventCoveredRules 와 그 필드를 더했다.
- test_checks·test_element_hold·test_regression_refs·test_provenance_e2e·test_fed_timeline_demo: 쇼케이스 쪽이 이 브랜치 집합을 모두 포함해서 그쪽을 받았다.
- 검사 수: 실제 등록 수 127 이다. fed 데모 checks.json 항목 수로 확인했다.
- DEVLOG·DECISIONS: 양쪽 행을 모두 남겼다. 같은 행 D580 하나만 뺐다.
- D305·D313 두 번 적힘은 병합 전 양쪽 브랜치에 이미 있던 것이라 그대로 두었다.
- 원장: load_user_feedback 174 개, 원장 문서 미보호 0.

## 3. 시험
- anti_inertia·test_checks·test_narration_clarity·test_regression_refs·test_element_hold·test_uf173_guards·test_audio_f1·test_series_layer·test_stage_timeline: 174 통과, 1 실패.
- 그 1 실패는 test_catalog_layer 다. 아래 §4 의 hormuz 클립 부재가 원인이다.
- test_fed_timeline_demo: 4 통과. 데모 프리뷰를 새로 렌더해 hard 0, 항목 127 을 확인했다. R-0401 의 hard 26 이 풀렸다.

## 4. 골든 25컷 — 아직 못 돌렸다
- fetch_data all 은 성공했다(Commons 포함). hormuz 프로젝트에 자산·사진을 옮기고 geo.prep(480p, 720p dark)과 script.plan(표준 음성, 45 문장 260.66초)을 마쳤다.
- 남은 것은 클립 두 개(niovi·strikes)다. media_fetch 가 Wikimedia 429 로 여섯 번 막혀 시간 한도에 걸렸다.
- 그래서 test_provenance_e2e·test_q3_light_e2e·test_catalog_layer 세 개는 렌더 전 점검("클립 없음")에서 멈췄다. 화소 비교까지 가지 않았다.
- 골든 기준은 다시 고정하지 않았다. 같은 반복은 더 돌리지 않는다. 레이트 한도가 풀리면 `media_fetch --only niovi,strikes` 한 번 뒤 세 시험을 다시 돌린다.
