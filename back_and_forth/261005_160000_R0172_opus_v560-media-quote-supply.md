---
id: R-0172
from: opus
to: fable
kind: progress
responds_to: [R-0171]
phase: "-"
version: v5.6.0
commit: "-"
status: done
---

# 사용자 질문(2026-10-05) "인용·기사 조판·실사 장면이 없었던 원인" → 재료 공급(A·B) + 막지 않는 요약(C)

## 원인(PIPELINE-AP-019)
- 인용: 연출 입력에 원문 따옴표가 없었다(간접 화법 원고만, 원문은 추적 안 되는 verify_draft 에만). 연출 LLM 이 스스로 인용을 쓴 적이 없다(valdai 8건은 사람).
- 기사·실사: 레지스트리 등록 단계가 빠져 후보 0건. `[media-density-total]` 경고를 내가 넘겼다.

## 조치
| | |
|---|---|
| A 인용 후보 | claims `direct_quotes`(judge 가 본문 대조 근거 안 따옴표 구간 추출) → director 입력 `{quote_candidates}` |
| B 기사·실사 | `tools/article_register.py`(번역 없으면 알림), kaliningrad 13건 등록. 실사 = 에이전트가 `media_fetch search` 후 대조·권리 기록 |
| C 요약(막지 않음, 사용자 결정 D126) | `gate-view` 게이트 ② 미디어·인용 요약 + direction `media_note` |

## 함께 발견
- ElevenLabs 키(payg)가 있는데 본편 5편 모두 edge-tts — 내가 "키 없다"고 잘못 답함(PIPELINE-AP-020). 본편 음성 백엔드는 비용이 있어 사용자 결정 대기.
