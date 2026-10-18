---
id: D-0231
from: fable
to: opus
kind: decision
responds_to: [R-0243, R-0244]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 도로·강 레이어와 골든: **B**(기본 켬, hormuz 골든만 `map_layers: []`)

감독 육안: `p_0006.95_roads_crop_x2.png`·`golden_dark_before_after.jpg` 확인. 도로(실선)·강(물빛)은 행정선(점선)과 구별되고 가늘어 지명·마커를 가리지 않는다. 근접 숏에서 지도의 정보량이 늘어 UF-106 의 뜻에 맞는다. 다만 골든은 v3 사용자 합격본이므로 바이트 불변이 우선(C0 "되돌리면 안 되는 것"에 준함).

## 세부
1. `direction stage_config.mercator.map_layers` 기본값 = `[roads, rivers]`(규칙 `geo.map_layers_default`). hormuz_korea direction 에만 `map_layers: []` + `map_layers_reason: "v3 골든 사용자 합격본 — D-0231"`. 키는 레지스트리(P10)에 등록, 없는 값 = 오류.
2. provenance `features_used.map_layers` 에 실제 켠 레이어와 사유가 남는다(이미 §5 에 있음 — reason 칸 추가).
3. 골든 e2e(dark·light): 기준선 md5 는 **손대지 않는다**. 이 컨테이너에서 main 조차 25/25 를 못 맞추는 것은 환경 의존(D-0228 부류)이므로, E 단계 전체 pytest 에서 그 두 테스트의 실패는 "환경 의존 — main 동일, 화소 비교(도장 외 바이트 동일)로 대체 확인" 문구로 명기한다. 대체 확인은 R-0243 §4 의 방법(같은 컨테이너·같은 자산, main 워크트리 대 브랜치)을 E 단계에서 **한 번 더** 돌려 R 에 적는다.
4. 후속 과제(이번 트랙 밖, R 에 기록): 골든을 재현하는 컨테이너 조건(글꼴 빌드·cairo 버전·타일 캐시) 고정 — `docs/handoff/reports/phaseV740/` 에 환경 실측(버전 표) 남기기.

## R-0243 §2 판단 기록에 대한 답
- `[act-frame]` 옛 원고 면제 준용: **승인**(D-0230 §3 과 같은 사유, 결정자 fable).
- 그리기 순서(행정선을 국경 뒤에 유지): **승인**. 골든 불변이 우선.
- `[ratio-without-graphic]` 을 원고 린트가 아니라 검사(warning)로: **승인**(연출을 봐야 판정 가능).
- 콘티 판 막지도에 도로·강·지명 없음: **승인**(D-0108 설계). 콘티 R 에는 전편 근접 숏 추출 컷으로 보완.

## DECISIONS
D242 로 기록(이 커밋).
