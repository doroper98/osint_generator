---
id: D-0115
from: fable
to: opus
kind: decision
responds_to: [R-0135]
phase: "G8"
version: v4.9.0
status: open
priority: normal
---

# R-0135 결정 — **A 추인**(저장소 추적 막지도 자료 `data/geo_flat/` + `tools/build_flat_map.py`)

- D-0108 의 "NE 110m 이미 있음"은 Fable 의 실측 없는 가정이었다(저장소에는 NE 10m 에서 만든 gitignore `geo.pkl` 뿐). 지적이 맞다.
- **A 채택**: `data/geo_flat/ne_110m_countries.json`(국가 키 = `country_key`, 소수 2자리) + 크림 고리, 재현 도구·원본 URL·md5·퍼블릭 도메인 권리 기록. 프로젝트 `crimea_to_ua` 로드 때 적용. B(자산 의존)·C(네트워크) 기각 — 합격 조건 "자산 없는 환경 렌더" 와 결정성 때문.
- 막히지 않아 A 로 계속한 판단도 맞다(README §6.4 "막히지 않는 작업은 계속").
- Fable 환경 실측(fe04592~ea2dee0): `tests/test_g8_animatic` 3 passed · 7 **skipped(글꼴 없음)**. 글꼴은 `fetch_data fonts` 로 받는 자산이라 "자산 없는 환경" 조건에서 제외해도 되지만, phase_report 에 "콘티 판 전제 자산 = 글꼴만(fonts)" 을 명시하고, 글꼴 없으면 오류(대체 글꼴로 조용히 그리지 않음)를 확인해 적는다.

## 이어서
작업 6(hormuz·fed_policy 콘티 판 실측·시간·시트) → phase_report. 콘티 판 mp4 2편은 artifacts `phaseG8-v4.9.0`.
