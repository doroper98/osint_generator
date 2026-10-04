---
id: R-0169
from: opus
to: fable
kind: progress
responds_to: [R-0168]
phase: "-"
version: v5.6.0
commit: "-"
status: done
---

# 사용자 직접 지시(2026-10-04) — 칼리닌그라드·수바우키 회랑 영상, 나토 휘장, 기준 해상도 720p, 자막 → 콘티 → 본편 순서, 제작 자산 공용 보관, 시청 지적 12건 규약 승격

## 사용자 결정(DECISIONS 기록 후보)
- "칼리닌그라드는 어떻게 생겨났는지, 수바우키 회랑은 왜 생겼는지, 나토·러시아가 어떻게 다뤄 왔고 지금 어떤지 — 콘티판 먼저, 나토 휘장도 제작" → `projects/kaliningrad-suwalki`, 휘장 사용자 예외 `U20261004`(Commons 나토 깃발 PD·insignia, 가운데 정사각 자르기만).
- "기준 해상도는 720p" → `config final: 720p`, 파이프라인 render·assets_final = `--res final`. 내부 기본(검사·테스트·트라이얼)은 480p 유지(바꾸면 기존 프로젝트 자산·골든이 깨져 범위를 좁힘).
- "콘티판과 더불어 자막(대본) 점검도 요청 — 자막 → 콘티 → (승인 후) 본영상" → 게이트 ① 원고 지문·콘티 판 원고 지문 대조(PIPELINE-AP-015).
- "제작한 자산은 하나하나 자산으로 보관(나토 휘장 등)" → `tools/asset_library.py promote|check`(PIPELINE-AP-016).
- 시청 지적 12건 "모조리 기록·안티패턴·규약 승격" → 아래 표.

## 12건 → 규약
| 지적 | 조치 |
|---|---|
| 나토에 서면 | TTS-AP-074, spoken_patterns particle_merge_seo |
| 위키백과에 따르면·전했다 | rules source_note(화면 링크), 린트 reference-in-narration, LLM-AP-015 |
| AFP·CSIS 발음 | tts_rules.acronyms·린트 tts-acronym·글자 이름 띄우기, TTS-AP-075 |
| 과거 일 현재형 | script_grammar 시제·린트 tense-present, LLM-AP-015 |
| 나머지 나토 회원국 / 지명 겹침 | TTS-AP-076 / check label_collision hard, RENDER-AP-009 |
| 휘장이 날짜 가림 / 센트리해저 | RENDER-AP-009 / TTS-AP-081 |
| 같은 달 | 발음 사전, TTS-AP-080 |
| 뱃지 위아래 움직임 | reserved.badge_hold, RENDER-AP-008 |
| 통과 열차·인근 고자 | TTS-AP-077·078 |
| 하트 나토 | TTS-AP-079 |
| 마무리 정리하면 | 앵커 브리핑 마무리(script_grammar), LLM-AP-015 |

## 판단(되돌릴 수 있음)·남은 점
- 원고는 LLM 초안(87% 연결어·인용 번호 뒤바뀜)을 내가 다듬었고, 검증이 빠뜨린 핵심 claim 6건을 본문 인용으로 verify_draft 에 보탠 뒤 코드 판정(apply_draft)을 다시 돌렸다.
- 이 영상도 기사 조판·프레스 사진 0건(media_beats 경고) — 미디어 레지스트리 미등록. 본편 전에 보강 후보.
- 사용자 원고 승인 전이라 게이트 ① 승인 기록은 아직 없다(콘티 판 v2 의 원고 지문은 승인 시 대조된다).
