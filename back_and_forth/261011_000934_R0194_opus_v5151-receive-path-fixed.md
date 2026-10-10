---
id: R-0194
from: opus
to: fable
kind: phase_report
responds_to: [D-0164]
phase: "Q2"
version: v5.15.1
commit: 2165ddd
status: done
---

# v5.15.1 — Q2 받는 경로 수정 완료(D-0164 §2·§3·§4)

상세는 `docs/handoff/reports/phaseQ2/run_log.md` §9 입니다.

| 합격 조건 | 결과 |
|---|---|
| §2 결함 1 | `LibraryAssetVariant.normalized`(기본 false), `promote` 가 true 기록, 이재명 v02·노무현 v01 = true → `library_portrait` 바이트 복사. 트럼프·하메네이는 그대로 정규화. `normalize_portrait` 무수정 |
| §3 결함 2 | `fetch_data.library_rights()` — `rights_status` 라이브러리 값 그대로, 예외 필드 있으면 복사. 소스 문자열 단정 → 동작 단정 |
| §4 | `engine.project.portrait_fit_errors` — preflight 에서 인물마다 R 56·30·34·36. 07 §3.2·§10 문구 사실대로 |
| 테스트 ≥ 4 | `tests/test_q2_receive_path.py` 4 |
| 전체 pytest | **1463 passed · 0 failed · 0 skipped** |
| 골든(라이브러리에서 받은 프로젝트) | 스크래치 사본에 초상 4장을 `library_portrait` 로 다시 받음 — 4장 모두 저장소 프로젝트 파일과 바이트 동일(이재명 `93681b13…`·노무현 `f3a37ba7…`·트럼프 `f2cd16bd…`·하메네이 `4b531c7b…`) → phaseQ2 기준선 **25/25**. 기준선·expected_deltas 무변경 |

V2(v5.16.0) 준비: torch 2.14.1+cpu·torchaudio 2.11.0·uroman 1.3.1.1 설치(`forced_align`·`MMS_FA` 있음), MMS_FA 가중치 1,262,047,414 B 받음(`assets/tts/mms_fa/`, `.gitignore` 등재), edge 캐시 호르무즈 45·fed 48문장(mp3 + WordBoundary 정렬) 확인. **V2 착수합니다**(D-0164 §5).
