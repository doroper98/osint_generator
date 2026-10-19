<!--
tier: 3
last_synced_with: v7.4.0
ssot_for: [phaseV740-uf127-listening]
depends_on: [rules/video_rules.yaml, script/lint.py, assets/pronounce/pronounce_ko.json]
last_review: 2026-10-19
-->

# UF-127 청취 자료 — "경유가·제트유가" 경음화 수정(D-0246, TTS-AP-083)

청취 판정은 사용자만 합니다(CLAUDE.md C0.2). 아래는 첨부 자료입니다.

## 1. 파일

| 파일 | 내용 |
|---|---|
| final_act2_35.wav | 전편에 들어간 수정 음성(표준 음성 M3 ×0.95, 끝 억양 시안 C) |
| final_act3_15.wav | 같음 |
| probe_act2_35_fixed.wav | 탐침 합성(끝 억양 보정 전) — 수정본 "경유가" |
| probe_act2_35_spaced.wav | 탐침 — 띄움 후보 "경유 가"(채택 안 함) |
| probe_act2_35_old.wav | 탐침 — 옛 사전 결과 "경유까" |
| probe_act3_15_fixed.wav | 탐침 — 수정본 "제트유가" |
| probe_act3_15_old.wav | 탐침 — 옛 사전 결과 "제트유까" |
| probe_contrast_yuga.wav | 대조 — "국제 유가가 크게 올랐습니다"(油價, 사전이 "유까" 로 읽힘) |

## 2. MMS 강제 정렬 — '유' 끝 → '가/까' 시작 간격

| 사례 | 발음 텍스트 조각 | 간격(ms) |
|---|---|---|
| act2_35 수정 | 경유가 | 0 |
| act2_35 띄움 | 경유 가 | 0 |
| act2_35 옛 | 경유까 | 0 |
| act3_15 수정 | 제트유가 | 100 |
| act3_15 옛 | 제트유까 | 80 |
| 대조 | 유까가 | 40 |

모두 120ms 이하입니다. 수정본은 원문 그대로라 쉼을 만들지 않습니다.

## 3. 회귀(전 프로젝트 원고 790문장, 사전 적용 결과 비교)

수정 전(0fc86a73) 대비 바뀐 문장은 2개뿐입니다.

| 문장 | 수정 전 | 수정 뒤 |
|---|---|---|
| diesel_road_2026 act2_35 | …실린 경유까 들어간… | …실린 경유가 들어간… |
| diesel_road_2026 act3_15 | …휘발유, 제트유까 수출된… | …휘발유, 제트유가 수출된… |
