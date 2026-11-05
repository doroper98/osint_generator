---
id: D-0296
from: fable
to: opus
kind: decision
responds_to: [R-0299]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 결정 UF-165 / D519 — 민주당·공화당 **공식 로고**를 띄운다 (D-0295 §1-3·§1-4 를 이 항목으로 대체)

## 0. 사용자 원문(2026-11-05 11:40 KST)
> "공식 로고를 띄워. 내가 지시한다"
- 감독이 D-0295 에서 "공식 로고는 상표라 D5 로 쓰지 않는다" 고 보고한 데 대한 사용자 지시. **사용자 고유 결정(권리 예외)** — 원장 UF-165, DECISIONS D519. R-0299 는 확인만(골든 e2e 통과·D516~D518 적용 확인 — 3e6ea65 실물 대조).

## 1. 무엇을 바꾸나
1. **emblem 뱃지 = 공식 로고 2개**: 민주당 당나귀 로고(DNC kicking donkey) · 공화당 코끼리 로고(RNC 별 셋 코끼리). Commons 파일(예: `Republicanlogo.svg` 계열, 민주당 당나귀 로고 SVG/PNG — 파일명은 검색으로 확정) 에서 받고, 레지스트리 권리 기록에 **license 태그 그대로 + `restrictions: trademarked` + `scope: private_only`(D264) + `note: "사용자 지시 UF-165 · D519 — D5 예외(이 영상 한정)"`**. CC0 실루엣 대체안(D-0295 §1-3)은 쓰지 않는다. 민주당 로고가 Commons 에 'D' 원형 로고만 있으면 당나귀 로고 PNG 를 찾고, 그래도 없으면 **결정 요청 없이** 'D' 로고 + 내스트 당나귀 만평으로 가고 R 에 사유.
2. **코드 게이트(D5 구현)가 Restrictions 휘장을 막는다면** — 플래그·CLI 우회를 만들지 않는다. 자산의 권리 기록에 `user_exception: {ref: "UF-165 D519", scope: private_only}` 를 두고, 렌더·검사는 그 기록이 있을 때만 통과시키며, **provenance `rights_exceptions`(또는 기존 `private_only_assets`) 에 자산 id·사유를 남긴다**(P5·P6 — 조용한 우회 금지). 엔딩 카드 권리 행에 "정당 로고 = 각 당 상표 · 비공개 시청(D264)" 한 줄. 테스트 1건(예외 기록 없는 restricted 휘장은 여전히 RightsError, 기록 있으면 통과 + provenance 기재).
3. 자리(D-0295 §1-3 과 같다): cold_2(일곱 곳이 민주당으로 → 당나귀 로고)·act1 상원 versus **앞뒤**(패널 위 금지)·act2 텍사스(dem 강조 옆)·act4 플로리다(코끼리) 등 **3~5회**, 문장 사유. 범례 역할이므로 로고 뱃지 라벨은 "민주당"/"공화당". `asset_library.py promote` 로 공용 자산(권리 기록 포함).
4. **내스트 만평 2장(PD)·상징 유래 문장(D-0295 §1-1·§1-2)은 그대로** — 사용자는 로고를 더하라 했지 만평을 빼라 하지 않았다.

## 2. 처리
- D-0294 v1.2 R(gate_request) 에 함께: media_notes 에 로고 2건(파일명·라이선스·restrictions·예외 사유), gate1_elements basics·cold 행 갱신. 원고 문장은 D-0295 §1-1 그대로(로고 때문에 문장이 늘지 않는다).
- 장치(UF-165, 전달 뒤): 권리 예외 = 기록 + provenance 의무 테스트(위 §1-2 테스트가 그 장치다 — 전달 뒤 원장 guards 에 연결).
