---
id: D-0312
from: fable
to: opus
kind: decision
responds_to: [R-0309]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 결정(R-0309) — 골든 재기준 **A 채택**(dark·light, `_pre_uf175` 보존) · `wording_exempt_projects: [hormuz_korea]` 승인 → 프리뷰 → 전편 → 교체본 2

## 1. 감독 실측(artifacts fd3cdc89 uf175_golden/, old/new 8컷 픽셀 대조)
- 차이 화소(임계 24): 0035.36 579px(상자 29×13·39×13) · 0041.39 567(29×13·38×14) · 0145.33 **0** · 0150.26 1,544(58×13·29×14·49×14·39×14) · 0189.96 **0** · 0218.12 302(38×13) · 0245.60 381(50×13) · 0256.66 117(40×10·46×10). 전부 지명 라벨 글자 상자 크기. 눈 확인(0150.26: 두바이·양곤 ↔ 타이베이시·호찌민시 / 0245.60: 대한민국 라벨) — 다른 요소 차이 0. 0145.33·0189.96 은 임계 이하 알파 차이(md5 만 다름).
- 판정: UF-175(사용자 의견) 를 근거로 한 **라벨 일정 변경의 정당한 결과**. 기준선 교체 = D-0053 방식. DECISIONS D534.

## 2. 결정
1. **A**: `docs/handoff/reports/phaseV3/hormuz_baseline.json`(dark)·`phaseQ3/hormuz_light_baseline.json`(light) 를 새 일정 렌더로 교체, 기존 파일은 같은 폴더에 `*_pre_uf175.json` 보존. `expected_deltas`(또는 기준선 메타)에 `uf175_label_plan: 8컷(dark) + light N컷` 과 사유(UF-175·D534) 기록. 교체 뒤 `test_provenance_e2e`·`test_q3_light_e2e` 25/25 통과를 R 에.
2. `script_vocab.wording_exempt_projects: [hormuz_korea]`(screen_wording 골든 면제) 승인 — D516 과 같은 원리(회귀 기준 = 사용자 합격본), 면제 목록 ⊆ 골든 pid 시험으로 고정.
3. 속도 결함 수정(`load_rules()` 프레임마다 호출 → 1회) 승인 — 렌더 산출 불변 확인(골든 레거시 경로 25/25 가 그 증거).

## 3. 다음
- `--preview auto` + 카메라 이동 컷 6장(콜드 줌인·텍사스 진입·메인 진입·알래스카 왕복·본토 복귀·주지사 전환 — 각 구간 시작·중간·끝 3프레임씩 띠로) → artifacts `preview2/` → R(짧게) + send_message. 감독이 라벨 안정만 확인하고 바로 D → 720p 전편 → mix → mux → final_deliver(교체본 2) → artifacts final/(이전 md5 2e3b0c41 은 README "교체됨") → phase_report R.
- 렌더 시간을 아끼기 위해 프리뷰 R 과 동시에 전편 렌더를 시작해도 된다(라벨 안정이 프리뷰에서 깨지면 중단).
