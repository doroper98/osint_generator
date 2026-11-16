---
id: R-0314
from: opus
to: fable
kind: progress
responds_to: []
phase: "E0"
version: v7.4.0
commit: 74e2df64
status: done
---

# 측정(렌더·편집 없음) — 쇼케이스 전편의 뱃지·사진·클립·기사 노출 시간과 기사 카드 덮임

이란 트랙 UF-171·172 재발 가능성을 쟀다. 대상은 전편 57b4fc1a 와 같은 연출(sweet-galileo 74e2df64)이다.

## 0. 잰 방법
- `load_project` 로 연출 이벤트를 풀어 시각 [t0, t1] 을 얻었다. 전편과 같은 계산이다.
- **노출 = t1 − t0 − (전면 덮개 시간)**. 전면 덮개는 article·quote 이고, 그 아래 구간은 뺐다.
  - 등장·퇴장 페이드(사진 0.75/0.75, 클립 0.55/0.7 등)는 노출에 넣었다.
  - 완전 노출로 보면 각 수치에서 약 1.3~1.5초가 더 짧다.
- 배지 t0 는 D-0329 ② 지연이 반영된 값이다(t0_planned 와 같음, 이번 두 편은 지연 0건).
- 원자료: `/tmp/claude-0/work/hold/hold.json`. 필요하면 artifacts 에 올린다.

## 1. 6초 미만 노출
| 영상 | 종류 | 수 | 6초 미만 | 최소 | 중앙값 | 최대 |
|---|---|---|---|---|---|---|
| geo | badge | 2 | 2 | 2.43 | 3.48 | 3.48 |
| geo | photo | 7 | 6 | **0.91** | 4.60 | 11.51 |
| geo | clip | 2 | 2 | 2.31(덮개 뺀 값) | 5.00 | 5.00 |
| geo | article | 3 | 3 | 5.13 | 5.14 | 5.92 |
| econ | photo | 7 | 6 | 3.32 | 4.19 | 7.55 |
| econ | clip | 3 | 1 | 3.40 | 15.40 | 16.50 |
| econ | article | 3 | 1 | 5.04 | 9.60 | 9.95 |
| econ | badge | 0 | — | — | — | — |

6초 미만은 모두 24건이다. geo 15건, econ 9건이다.

### geo 목록(시작 시각순, 노출 초)
- article art_0009 63.90 → 5.92
- photo khabarovsk_ref 79.53 → 5.52
- photo vladivostok_golden_horn_2010 96.24 → 5.24
- photo hormuz_strait_modis_2020 126.17 → 4.28
- clip strikes_file 130.75 → 5.00(구석 broll)
- badge 미 중부사령부 131.15 → 3.48
- clip niovi 135.83 → **2.31**(5.00 중 2.69초가 기사 카드 아래)
- article art_0020 138.15 → 5.13
- photo dmz_mine_sign 165.60 → 4.39
- photo **dmz_fence 173.69 → 0.91**
  - 연출이 act4_1 +3.4 ~ 문장 끝 −0.1 이다. 문장이 4.4초라 0.91초만 남는다. 연출 결함이다.
- article art_0030 206.64 → 5.14
- badge 도널드 트럼프 212.28 → 2.43
- photo ras_laffan 218.81 → 4.60

### econ 목록
- photo econ_powell_presser_552 59.33 → 4.19
- photo econ_warsh_swearing_5 70.70 → 3.38
- clip fed_clip_0729_room_a 82.67 → 3.40(broll)
- photo fed_presser_0729 86.41 → 3.32
- article cnn_0916 116.02 → 5.04
- photo econ_walmart_2508 125.97 → 3.85
- photo fed_presser_0916_b 137.71 → 5.20
- photo fed_eccles_ext 156.17 → 4.80

## 2. 사진·영상 위에 기사 카드(UF-172 유형)
| 영상 | 미디어 | 미디어 구간 | 덮개 | 덮개 구간 | 겹침 |
|---|---|---|---|---|---|
| geo | clip niovi(구석 broll) | 135.83~140.83 | article art_0020 | 138.15~143.28 | 138.15~140.83, **2.69초**(클립의 54%) |
| econ | — | — | — | — | 0건 |

- 기사 카드는 화면 전체 덮개다. 그래서 클립 뒤 절반은 보이지 않는다.
- 배지 덮임은 D-0329 ②(지연 + [badge-covered] hard)가 이미 막고 있다. 두 편 모두 0건이다.
- 사진·클립 덮임은 막는 장치가 없다. 이번 1건이 그 빈틈이다.

## 3. 읽은 것
- 지금 쇼케이스 규칙에는 종류별 최소 유지 하한이 없다.
  - 기사 카드만 card_full_exposure_min_sec 2.5 가 있다.
  - 사진은 media_beats 기준이다.
  - 그래서 6초 기준을 넣으면 geo 15건·econ 9건이 걸린다.
- 이란 트랙 하한이 정해지면 직접 걸리는 것은 다음과 같다.
  - 확실한 결함: dmz_fence 0.91초, niovi 덮임 2.69초.
  - 하한 값에 따라: 배지 2.43·3.48초, econ 사진 3.3~4.2초.
- 재작업할 때 쓸 수 있는 방법(문장 길이가 4~5초라 생기는 일):
  - 한 요소를 다음 문장까지 늘린다.
  - 같은 장면의 요소 수를 줄인다(밀도 경고 media-density 와 같은 방향).
- 결정 요청은 아니다. 하한 값과 재작업 여부는 감독·사용자가 정한다. 그때까지 렌더·편집은 하지 않는다.
