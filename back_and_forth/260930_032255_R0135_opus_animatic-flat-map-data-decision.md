---
id: R-0135
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G8"
version: v4.9.0
commit: f6540ca
status: awaiting_decision
---

# G8 막지도 자료 — D-0108 "NE 110m, 이미 있음" 이 저장소에 없음

## 쟁점
D-0108 설계표는 막지도 채움을 "NE 110m(이미 있음)" 으로 적었습니다. 실측하면 저장소에 110m 자료가 없습니다.
- 추적 파일 중 Natural Earth 는 0건(`git grep 110m` 결과 D-0108 한 줄뿐).
- 지오메트리는 프로젝트마다 `geo.prep` 이 NE **10m** 에서 만든 `assets/geo.pkl`(gitignore)뿐입니다.
- 이것을 쓰면 Fable 환경(자산 없음)에서 막지도를 못 그립니다. 합격 조건 "자산 없는 환경 렌더" 를 어깁니다.

추가 사실: NE 110m 국가 파일은 크림반도를 RU 에 넣습니다(실측, 34.1E 45.0N → Russia). 랫클리프·dmz_mine 은 `crimea_to_ua: true` 입니다(04 §3.2).

## 선택지
- **A(권고)** 저장소에 막지도 자료 한 벌을 추적 파일로 둔다.
  `data/geo_flat/ne_110m_countries.json`(국가 키 = `country_key` 규칙, 좌표 소수 2자리, 약 160KB) + 크림 고리(NE 10m admin1, 단순화).
  만드는 도구 `tools/build_flat_map.py`(재현 가능, 원본 URL·md5 기록). 프로젝트 `crimea_to_ua` 는 로드 때 적용.
  Natural Earth 는 퍼블릭 도메인(라이선스 원문 확인)이라 권리 기록만 남깁니다.
- **B** 프로젝트 `assets/geo.pkl`(10m) 을 쓴다. 자산 없는 환경에서는 오류. 합격 조건과 충돌합니다.
- **C** 렌더 때 110m 을 내려받는다. 네트워크 의존·결정성 약화, 오프라인 테스트 불가.

## 근거
- 합격 조건(자산 없는 환경 렌더, D-0114 재확인)을 지키는 것은 A 뿐입니다.
- 110m 은 "러프한 막지도" 취지와 맞고 렌더도 가볍습니다. 파일 삭제로 되돌릴 수 있습니다.
- 모든 환경에서 같은 자료라 콘티 판 md5 결정성이 환경과 무관해집니다.

## 막히는 범위
없음. A 로 구현을 계속하고, 다른 결정이 오면 자료 출처 함수 하나만 바꿉니다.
카메라 경계는 `geo.yaml` 티어 W bbox 를 그대로 씁니다(`tier_record` 가 bbox 를 그대로 옮기는 것을 확인, tiers.pkl 불필요).
