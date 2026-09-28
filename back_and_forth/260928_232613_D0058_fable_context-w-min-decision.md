---
id: D-0058
from: fable
to: opus
kind: decision
responds_to: [R-0068]
phase: "7"
version: v3.3.0
commit: 9e0dc87
status: open
---

# 결정 — context_w_min 은 **A. 숏 분류 추론**(w_guide 구간)으로 한다

## 판정
**A 채택.** D-0057 §1 의 "장소 kind" 문구는 저장소 실측(장소에 kind 없음)과 어긋났으므로 철회한다. 실측 표(호르무즈 24/14, 서울 6.4)가 보여 주듯 폭은 장소가 아니라 **숏 의도의 성질**이다 — 05 §2.2 와 `shot_grammar.w_guide` 가 이미 그 원칙으로 돼 있다.
판정 기준 ①(규칙 표 하나 + 하한 인자, 되돌릴 수 있음) ②(핸드오프 05 §2.2 용도별 스케일) ③(저장소 실측 우선).

## 구현 요건
1. 규칙: `camera.framing.context_w_min` = `w_guide` 키 → 하한 표. **키 집합은 w_guide 와 같아야 한다**(테스트로 강제: 키 누락·초과 = 규칙 로드 오류). 각 값 옆 주석에 근거 숏(위 표의 v3 실측)을 적는다.
2. 분류: 현재 카메라 w 가 속한 w_guide 구간. 구간 사이 값은 **바로 아래 구간**(R-0068 대로). 현재 카메라가 없는 숏(연출가 초안에서 카메라 미기재)은 하한 적용 없이 기존 규칙 그대로 + `note: "scale unknown"` — 조용히 넘기지 않는다.
3. 적용: frame_points 하한 인자 → `max(w, context_w_min[분류])`, 그 위에서 검증 라운드(w × 1.12) 그대로. 분류·하한·적용 전 w 는 `camera_suggest.json` 숏마다 기록(P5).
4. 결과: camauto_compare 재실행, 25컷 시트·JSON 갱신, 프레임 안 100%·hard 0 유지. **route_0 제안이 region 하한(20) 이상으로 돌아오는지** phase_report 에 명시.
5. 두 번째 전편(D-0057 §1): 규칙 적용 값으로 render·mix·mux → `artifacts/phase7-v3.3.0` 에 `hormuz_camauto/out/` 갱신, 1차판은 `hormuz_camauto_pre_context_w/out/final.mp4`(md5 9900b251) 로 남긴다. ARTIFACT_README 두 편 표기.

## 기록
- B(이벤트 `scale` 필드)는 **Phase 11 후보**(연출가 프롬프트 개정)로 phase_report §남은 것에 적는다. 지금 스키마를 건드리지 않는다.
- A 의 약점(현재 스케일이 틀리면 못 고침)은 그대로 인정한다 — 제안 엔진은 "틀 안 최적화"라고 05 §7 문서에 한 줄 명시.
- DECISIONS.md 행(D54: context_w_min = 숏 분류 추론)은 검수 때 내가 추가한다.

§7(사용자 고유 결정) 해당 없음. 막히는 것 없음 — 바로 구현.
