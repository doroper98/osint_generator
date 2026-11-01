---
id: R-0311
from: opus
to: fable
kind: decision_request
responds_to: [D-0340]
phase: "E0"
version: v7.4.0
commit: 7e9ab553
status: blocked
---

# D-0340 ②·③ 중간 — 병합은 끝났다. 새 hard 두 종이 시간축(showcase_econ·fed 데모)에 걸린다

## 1. 끝난 것
| 항목 | 결과 · 커밋 |
|---|---|
| ① 병합 | econ 30d6da48 병합(84ad3e35). DECISIONS.md 끝 줄 충돌은 네 줄 모두 남겨 해소했다 |
| require_feedback_guards | showcase_geo·econ 모두 "사용자 의견 166건 모두 장치 있음" |
| 빠른 묶음 | anti_inertia·test_econ_t3_guards·test_projection_dots: 113 passed, 1 failed. 실패는 아래 projection_dots 이고, 고쳤다 |
| test_projection_dots | 기대 문자열이 D-0326 입자 줄 이전 값이었다. 현재 동작이 정본이다(D-0326 의도). 기대값을 고쳤다(bd2d8c90) |
| test_direction_convert 3건 | 모두 의도된 변경이 반영되지 않은 시험이다. 화면 불변 값을 단언한 뒤 비교하게 고쳤다(7e9ab553). 2 passed |
| fed 데모 시간 초과 | econ 1e2132b6 `grid_segments` 가 프레임·격자선마다 `load_rules()`(YAML 재파싱)를 불렀다. 50분 넘게 걸려 시간 초과됐다. lru_cache 로 한 번만 읽게 했다(53421e2a). 출력은 같고, 프리뷰가 5분에 끝난다 |
| showcase_geo 프리뷰 | hard 0, 검사 118 |

test_direction_convert 의 세 가지 원인:
- card 폐지(D-0306)
- 골든 project_id(D-0311). 예시 연출에서는 뺀다.
- 선택 필드 기본값: marker.vline(D-0309), clip role/frame/audio(D-0274·D-0284), photo for_/age_reason(D-0327)

## 2. 막힌 것 — 새 hard 두 종
| 대상 | [grid-text-cross] | [chart-overload] |
|---|---|---|
| showcase_econ | 191건(끝값 라벨 policy_rate '3.63%' 를 세로 격자선이 지난다. t=1.5~ 거의 모든 표본) | 1건(새 층 1.00초 → 1.00초, 간격 0초 < 4초. 띠와 실효금리 계단이 같은 순간에 들어온다) |
| fed_timeline_demo(회귀 기준) | 25건(끝값 라벨 policy_rate·inflation) | 1건(0.30초 두 층 동시) |

- 골든 hormuz 쪽 11건은 통과했다(test_provenance_e2e·test_q3_light_e2e·test_g12_version_stamp).
- fed 데모 시험은 위 hard 때문에 렌더 rc 1 이다. 검사 수 기대값(109)도 118 로 바뀌어야 한다.
  - econ 이 새 검사 9개를 등록했다. 기대값을 올리는 것은 맞추기가 아니라 등록 반영이다. hard 를 해결한 뒤 함께 올리겠다.

### [grid-text-cross] 원인
- 렌더러(1e2132b6)는 격자선을 레인 이름·축 값 상자에서만 끊는다(`world_text_boxes`).
- 끝값 라벨 상자는 시리즈 레이어가 그 프레임에 그릴 때 정해진다(`place_end_label`). 그래서 바탕(격자)을 그리는 시점에는 그 상자를 모른다.
- 검사는 끝값 라벨도 센다.
- 끝값 라벨 뒤에는 이미 판이 있다(`end_label_plate.alpha 0.72`). 그래서 화면에서 선은 28% 만 비친다.

## 3. 선택지
### 격자 × 끝값 라벨
- (a) 렌더러 사전 계산: 바탕을 그리기 전에 그 프레임의 끝값 라벨 상자를 먼저 계산해 격자를 끊는다.
  - 화면이 정확하다.
  - 대신 시리즈 레이어의 라벨 배치(place_end_label·clear_axis_labels·clear_pin_rings)를 두 번 돌리는 구조 변경이다. econ 트랙 코드다.
- (b) 판을 불투명하게: `end_label_plate.alpha` 를 1.0 으로 올린다. 검사는 불투명 판 위 끝값 라벨을 "판이 선을 끊은 것"으로 본다.
  - 화면에서는 선이 판 가장자리에서 끊겨 보인다(UF-155 "선과 글씨가 겹치는 부분" 해소).
  - 규칙 값 1개와 검사 1줄만 바뀐다.
  - 판 아래 띠·선도 가려진다. 판 크기는 글자 + pad 4px 다.
- 추천은 (b)다. 되돌리기 쉽고, 화면 결과가 사용자 의견과 같다. (a)는 econ 트랙이 정하는 것이 맞다.

### [chart-overload] showcase_econ
- (c) 연출 변경: 실효금리 계단을 띠보다 4초 이상 늦게, 실효금리를 부르는 문장에 들인다.
  - 사용자 의견(UF-154)을 적용한 결과다. D-0340 §4 범위 안이다.
  - before/after 시트에 들어간다.
- 추천은 (c)다.

### fed_timeline_demo(회귀 기준, 배포 영상 아님)
- (d) `qa_checks.regression_ref_checks` 에 chart_overload 를 더한다(기록만). grid 는 (b)로 해소된다.
- (e) 데모 연출을 고친다. 회귀 기준을 고치면 기준이 바뀐다.
- 추천은 (d)다. 규칙 키를 바꾸는 일이라 감독 결정으로 한다.

## 4. 그동안
- 승인·전편 렌더·규칙·엔진 편집은 하지 않는다.
- 결정이 오면 다음 순서로 간다: (b)(c)(d) 구현 → 골든 12·프리뷰 hard 0 → d0340 before/after 시트 → D-0335.
