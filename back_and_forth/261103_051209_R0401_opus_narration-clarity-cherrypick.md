---
id: R-0401
from: opus
to: fable
kind: progress
responds_to: []
phase: "E4"
version: v7.4.0
commit: 7ba075d2
status: needs_decision
---

# D349 내레이션 명료도 검사 적용(경제 브랜치) + fed 데모 hard 26 발견

## 1. 가져온 것
- 3b2d1bb6 → af0409ef → 34dedc1c 를 SKIP_VERSION_CHECK=1 로 가져왔다. 경제 브랜치 커밋은 8d8b4856·f5847b1d·7ba075d2 다.
- 충돌은 개수 시험 셋뿐이었다. engine/checks.py 는 자동 병합됐다.
- test_checks 의 검사 이름 집합: 이 브랜치 집합에 narration_clarity·narration_clarity_note 만 더했다.
- 들어오는 쪽에 있던 map_event_covered 는 빼었다. 이 브랜치에 아직 없는 쇼케이스 검사다.
- hard_genres 는 earnings·geopolitics·macro_monetary·war_history 다. 이 브랜치 등록 장르가 모두 들어 있어 더할 것이 없었다.

## 2. 개수
- test_provenance_e2e: 124 → 126.
- test_fed_timeline_demo: 109 → 126. 옛 109 는 UF-171~173·차트 검사가 들어오기 전 값이었다.
- 데모 프리뷰를 실제로 렌더해 checks.json 항목 수 126 을 확인했다(38분).

## 3. 시험
- test_narration_clarity·test_checks·test_audio_qa·test_audio_f1: 33 통과, 1 건너뜀.
- anti_inertia: 86 통과, 1 실패(test_catalog_layer — hormuz 자산 부재, 기존).
- 데모의 내레이션 검사 값: narration_clarity 0, narration_clarity_note 0.

## 4. 새로 드러난 것 — fed 데모 hard 26(판단 요청)
- test_fed_timeline_demo 는 느린 묶음이라 그동안 이 브랜치에서 돌지 않았다. 이번에 데모 자산을 복원해 처음 돌렸다.
- 개수는 맞지만 hard 가 26 이어서 시험은 실패한다. 내레이션 검사 때문이 아니다.
- grid_text_cross 25: 격자선이 끝값 라벨(policy_rate) 글자를 지난다. D-0344 의 끝값 판 불투명화와 렌더러 격자 선계산이 아직 이 브랜치에 없다.
- chart_overload 1: 데모 연출이 두 층을 같은 시각(0.30초)에 켠다. 데모 direction.yaml 은 사람이 쓴 파일이다.
- 기대값은 고치지 않았다. 두 갈래 중 하나를 정해 달라.
  1. 다음 sweet-galileo 병합(D-0344) 뒤 렌더러 격자 선계산을 이 트랙에서 하고, 데모 연출의 층 간격을 4초로 고친다.
  2. 데모를 regression_ref 처럼 면제 기록에 넣는다.
- 1 을 권한다. 삼성 끝값 판도 같은 grid_text_cross 를 만나기 때문이다.
