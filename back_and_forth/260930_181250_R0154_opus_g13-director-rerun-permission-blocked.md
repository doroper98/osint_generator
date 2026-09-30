---
id: R-0154
from: opus
to: fable
kind: blocked
responds_to: [D-0130]
phase: "G13"
version: v5.2.0
commit: f8775eb
status: blocked
---

# G13 진행 — §A·§B·§C·Q1~Q3 완료, §D 연출가 재실행은 권한 거부로 멈춤

## 완료(커밋)
| 항목 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION 5.2.0 | ca80d0a | docs_sync 8 |
| §A·§B·§C | ef0bf61 → 6e47317 | 전체 pytest **1216 passed·failed 0**(기준 1207 + 9). hormuz golden 25컷 = phaseG12 기준선 **25/25 바이트 동일** |
| Q3 B panel | 2293c3b | 테스트 1(패널만 있는 구간 통과) |
| Q2 A 기사 4건 | 359415b | fed 기사 2 → 6. fox_0729←src_art_0002, cnn_0916←src_art_0003, nbc_0916←src_art_0005, abc_0916←src_art_0006. 원문 8·10·14·11단어 |
| 스윕 도구 | f8775eb | fed 3컷 × 3변형 시트, v9 G12 값 6컷(전) |

## v9 연출(전)에 대한 새 검사 실측
- `[backdrop-main-missing]` 0.00–11.06s 1건(hard) — 오프닝에 차트 아일랜드 없음.
- `[card-island]` 11건 — 긴 카드(x0 394~559)가 left 상자(오른쪽 끝 564)를 침범.
- 보도 인용 카드 10개, article 2개.

## 막힘
`tools/ai_direction_run.py`(연출가 LLM 재실행, direction.yaml 교체) 실행이 이 세션의 자동 권한 판정에서 거부됐다. 우회하지 않고 멈춘다. 사용자가 이 명령을 허용하거나 직접 실행해야 §D(연출가 재실행·480p·시트·artifacts)를 이어갈 수 있다.
