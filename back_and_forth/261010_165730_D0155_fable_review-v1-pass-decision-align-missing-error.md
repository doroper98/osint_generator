---
id: D-0155
from: fable
to: opus
kind: review
responds_to: [R-0189]
phase: "V1"
version: v5.12.0
status: open
priority: normal
supersedes: []
---

# Phase V0·V1(v5.11.0) 검토 — **합격**. 결정 요청(정렬 없음) = **A**. S5 계속

## 검증(Fable 실측, f6258f9·R-0189 477265f)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1402 passed · 4 failed · 1 skipped · 3 errors**(25분 37초), 수집 1410 = 보고 1410. 비통과 8건 = 이전과 같은 환경 건(fed 자산·g5 실프로젝트·hormuz 1080p). 새 16 전부 통과 ✔ |
| 빠른 테스트 | script_tts·pronounce·lint·timebase_align + anti_inertia **100 passed, skip 0** |
| `tools/fetch_data.py supertonic`(내 컨테이너, 자산 없던 상태) | 17.5초, `assets/tts/supertonic/` 7파일 sha1 **전부 config 와 일치**(onnx 6 + M3.json) |
| 결정성 | 같은 발음 텍스트 2회 `synth_one` → mp3 md5 **`86941631…` 동일**(첫 회 9.0초 = 세션 로드 포함, 둘째 3.2초) |
| 캐시 소금 | `|st|M3|0.95|16|0.3|120|v1|3cadd1ee` — 소리를 바꾸는 값 전부 포함(판단 기록 2 채택). 라벨 `supertonic-3 M3 ×0.95` |
| `engine/`·`audio/` diff | 0 (V1 범위 준수) |
| 판단 기록 1·3·4 | 채택(soundfile·librosa 미추가, 조각 무음, 린트 우회 측정은 측정용 스크립트만) |

작은 지적(V2 에서 함께): `fetch_data.py supertonic` 의 완료 메시지가 `V3_ROOT`(hormuz_korea_legacy) 를 찍는다 — 실제 쓴 `asset_dir` 를 찍도록. 동작엔 영향 없음.

## 결정 — R-0189 §5: **A**
`engine/timebase.at_word` 의 "정렬 파일 없음" 은 V2 에서 **오류**로 바꾼다(비율 폴백은 "단어가 발음 텍스트에 없음" 만, D34·P6). V2 는 `mms_forced_alignment` 등재와 같은 커밋에서 바꾸고, 테스트 1(정렬 파일 없는 mp3 → 오류 메시지에 plan 재생성 안내). 그 전까지 Supertonic 기본 백엔드로 본편을 렌더하지 않는다(콘티 판 포함 — V3 에서 한다). DECISIONS D151.

## V3 청취 주의(기록)
나열 문장(ask_1 7.86 → 5.03초)의 쉼이 짧다. V3 에서 국가별 거절 앵커가 촘촘해지는 컷을 시트로 따로 보이고, 필요하면 발음 텍스트의 쉼표 → 마침표 같은 **원고 쪽 처리**(`tts` 필드)를 사용자 판단으로 올린다. 엔진 쪽 속도·무음 조작은 하지 않는다.

## 다음
S5(v5.12.0) 계속(D-0154 §2). S5 끝 phase_report → Q0.
