---
id: R-0125
from: opus
to: fable
kind: progress
responds_to: [D-0106]
phase: "G6.5"
version: v4.7.0
commit: 27e4775
status: awaiting_decision
---

# G6.5 진행 — D-0106 반영, D-0104 §2 중 D2(b) 만 남음(R-0124 결정 대기)

## 끝난 것

| 항목 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·CHANGELOG | 9f99ef7 | docs 테스트 |
| 병합(충돌 6 + 원격 D-0105) | 0fb7e6d · 5f97401 | DECISIONS D90·D91·**D95**(원 D87), R-0118·R-0119·R-0122 |
| D2(a) 연출 문법 `rules direction_grammar` | 06cf4d3 | 연출·수정 프롬프트 둘 다, 테스트 1 |
| D3 W1.1 체크리스트 | 488231d | WORKFLOWS |
| D5 미사용 미디어 3 + 그 PNG 조판 스크립트 삭제 | 0ac50f0 | media_registry 30 항목 |
| D4 `reopen --to direction --reason` | be7f030 | manifest.reopens(사유·연출 판 번호), 테스트 2 |
| D-0106 1-C 롤 + 상한 60 px/s | 07ad73b · 957d9eb | 테스트 3(200px 롤 30.8 px/s·1234px 오류·넘침 없음), checks 항목 19(`endcard_roll` warning) |
| D-0106 2-B `auto: people` = entities 이름 | 1a839c1 | 테스트 2(hormuz 수동 행 이재명·노무현과 같음, 없는 인물 = RightsError) |
| S1 LLM-AP-009 | 295ad1e | 기록만(G8 후보) |
| 오디오 재측정(post_limiter) | d1bc80b | 아래 |
| 갤러리 35 | 27e4775 | G4 기준 33 동일, gantt = G5 변경, site_diagram 새로 |

- pytest: **1056 passed · failed 0**(1055 + e2e 항목 수 수정 1). hormuz 골든 25/25·랫클리프·데모·fed_policy 기준선 테스트 포함.
- D5 추가 설명: `projects/dmz_mine_2026/build_site_diagram.py` 는 지운 개념도 PNG 3장을 만들던 스크립트라 함께 지웠습니다(site_diagram 요소로 대체, P2). 되돌리기 = 0ac50f0 revert.
- 롤 거리 정의: 넘침 판정은 G5 한도(428) 그대로, 거리 = 마지막 기준선 − (scroll_bottom − scroll_fade_px) — 마지막 줄이 아래 페이드 구역 위에서 멈춥니다(브랜치 원 구현은 페이드 안에서 멈춰 마지막 줄이 흐렸음).

## 오디오 — post_limiter 뒤(`reports/phaseG6_5/audio_qa_post_limiter.json`)

| | I | TP | 음악 레벨 | hard |
|---|---|---|---|---|
| hormuz(0.8) | −14.04 | −1.71 | −12.12 | 0 |
| fed_policy(0.8) | −14.05 | −1.84 | −12.89 | 0 |
| hormuz(0.7, G6 스윕 판) | −14.05 | −1.72 | −11.55 | — |

**권고(결정 아님)**: G6 에서 norm_ref 를 0.8 로 올린 이유는 트루 피크였습니다. 리미터가 들어온 지금은 0.7 도 TP 여유가 큽니다. D-0102 의 원래 기준(음악 레벨 여유 0.3 dB 최소값)대로 0.7 로 되돌리면 저역 절대가 +0.8 → +1.4 dB 가 됩니다. 사용자 청감 판정과 묶어 결정해 주십시오(되돌리기 = 규칙 값 하나).

## 남은 것

- D2(b) `[geo-unsourced]` — R-0124 결정 대기. 결정이 오면 구현·테스트 → G6.5 phase_report.
- dmz 프리뷰 — D-0106 대로 보류. run_log 에 "자산 미보존" 한 줄은 phase_report 때 씁니다.
