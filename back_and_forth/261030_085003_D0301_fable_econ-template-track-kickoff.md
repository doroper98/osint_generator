---
id: D-0301
from: fable
to: opus
kind: plan
responds_to: []
phase: "E3"
version: v7.4.0
status: open
priority: urgent
---

# 계획 — 경제 주제 영상 템플릿 트랙 착수(E3 공시 데이터 · E4 새 시각 요소 · E5 기업 장르 · E7 실적 발표 템플릿) — 전용 구현 세션, 브랜치 `claude/econ-template-2026`

## §0 근거
- 사용자 지시(2026-10-30): "이 세션(session_017Yuw8gt7PXV5fzmtcn2t8J 『경제 주제 영상 제작 커버리지』, 2026-10-27)에서 이야기 했던 경제 주제에 대한 영상제작 템플릿을 개발착수 하도록 지시 해. 감독 … fable 세션을 새로 띄울지 아니면 구현을 위한 Opus 세션을 바로 띄울지는 니가 판단해."
- 그 세션의 결론(감독이 transcript 로 확인): 경제 영상의 병목은 숫자의 출처(공시 원문을 코드가 읽는 경로) → 새 차트는 막대·워터폴·생키 셋 → 기업 장르·company 엔티티·투자 고지 → 앤트로픽 S-1 첫 실증. 이 결론은 이미 **D-0251 §2 E1~E6** 로 계획화됐고, 실적 발표 템플릿은 **D-0278(E7)** 로 구체화됐다. 새 계획을 쓰지 않는다 — 두 문서가 정본이다.
- **감독 판단**: 별도 감독(Fable) 세션을 띄우지 않는다. 계획이 이미 정밀하고(Opus 가 그대로 실행할 수준), 감독은 이 세션이 맡는다. **전용 구현 세션(Opus 5.5) 하나**를 띄운다. 쇼케이스 구현 세션 3 은 E7 에서 손을 뗀다(쇼케이스 게이트 ②·D-0300 에 집중).

## §1 범위와 순서(각 단계 = R 보고 + 변경마다 타깃 테스트·anti_inertia·골든 25컷)
| 단계 | 내용(정본) | 산출 |
|---|---|---|
| T1 | **E3 공시 데이터 경로**(D-0251 E3 + D-0278 §4.2): `frequencies` quarterly·daily, `units` 조 원·십억 달러·달러·곳·배, `source_kind filing`(form·accession/rcept_no·filed_on·item·locator·url), 라이선스 `public_filing`·`private_only_market_data`, `sources_allowed` 확장, `tools/fetch_filing.py`(EDGAR 8-K/10-Q/S-1 표 + OpenDART), Yahoo chart 일별 시세, 긴 문서 검증 입력 분할(목차 단위) | 삼성·인텔 Q3 2026 레코드 12개(D-0278 §7 id) + 앤트로픽 S-1 레코드 초안, raw md5 |
| T2 | **E4 새 시각 요소 스케치**(20 §4.1 ② — 실제 엔진 렌더, 목업 금지): series `bars`(stack 옵션)·`estimate`·가이던스 band(D-0278 §4.1) + `waterfall`·`sankey`(D-0251 E4 — 무대 안 요소, 독립 패널 금지, 문장 앵커마다 하나씩 자람) | 스케치 5~6컷 artifacts → 감독 → 사용자 승인 |
| T3 | **E4 등록**(승인 뒤 한 커밋): 레지스트리·스키마·렌더러·프리뷰 예제·검사([bars-from-zero]·[estimate-actual-pair]·[price-window-label]·생키 합 검사)·테스트 | |
| T4 | **E5 장르·엔티티**: `genres/earnings.yaml`(D-0278 §4.3, corporate 를 earnings 로 구체화) + `EntityIn.kind company` + `[invest-notice-missing]` hard + narration 스위치 3 + intake 가이드 earnings + `prompts/` 재생성·파리티 테스트 | |
| T5 | **E7 프로젝트 둘 W0**: `samsung_q3_2026` → `intel_q3_2026`(D-0278 §3 다섯 막·§7). 게이트 ①·② 는 **사용자** — 자료는 감독이 전달. 콘티 판 의무 | 원고 gate-view → 콘티 판 → 프리뷰 → final |
| T6 | 앤트로픽 S-1 실증(E6)은 T5 뒤 별도 D | |

## §2 운영 규칙
- 브랜치 `claude/econ-template-2026`(sweet-galileo 머리에서 분기). 쇼케이스 트랙과 같은 파일(`rules/video_rules.yaml`·`schemas/*`·`engine/checks.py`)을 만지므로 **하루 1회 sweet-galileo 를 merge 해 따라온다**(충돌은 구현이 풀고 R 에 적는다). PR 금지·main 푸시 금지. 커밋 첫 줄 `v{VERSION}: …`.
- D 번호: 이 트랙은 감독이 D-0300~ 에서 발행(쇼케이스와 같은 감독). R 번호는 check.py 가 준다.
- 사용자 결정 대기(D-0278 §8): 도메인 허용·주가 출처·길이·편 구성·새 요소 승인. **막히면 묻지 말고** press_cited·허용 출처로 먼저 만들고 기록, 감독이 사용자에게 한 번에 묻는다.
- 금지 문구(UF-145)·표준 음성·차트 세계·축 고정·사진 밀도·클립 액자·인셋 규칙(UF-146) 전부 적용. 보고문은 `tools/slop_check.py`(sweet-galileo 137d2d58) 로 점검.
- 렌더는 run_in_background 만(nohup 금지). 렌더 중 규칙·엔진 변경 금지(W0).
