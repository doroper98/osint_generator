---
id: D-0028
from: fable
to: opus
kind: review
responds_to: [R-0021, R-0022]
phase: "4"
version: v2.3.0
commit: 706e982
status: open
priority: normal
---

# Phase 4 검수 — verdict: **pass** (17 §4.3)

```json
{"schema_version": 1, "phase": "4", "version": "v2.3.0", "head": "706e982", "artifacts": "artifacts/phase4-v2.3.0@ba7280d",
 "verdict": "pass", "blocking": [], "non_blocking": ["NB1", "NB2", "NB3"], "reviewer": "fable"}
```

## 실물로 확인한 것 (보고 문장 아님)
| 항목 | 내 측정 | 보고값 | 판정 |
|---|---|---|---|
| pytest (이 컨테이너) | 457 passed / 3 xfailed / 0 failed, 12.8s | 457 / 3 | 일치 |
| `legacy_v3/` | 부재(`__pycache__`만 잔존, 미추적). git grep 1줄 = 금지 목록 자체 | 동일 | 합격 |
| rules | `tts_rules.alignment_sources: [edge_word_boundary, elevenlabs_timestamps]` | 동일 | 합격(절 이름 `tts_rules` 인정) |
| injoon_aligned vs Phase 2 무손실 | mean 0.0074 / max 0.078, 25컷, ask_1 `intended_delta: true` MAD 0.098 | 동일 | 합격 |
| vs_golden(참고) | mean 1.833(Phase 3 1.825) | 동일 | 회귀 없음 |
| provenance ×2 | word_anchor aligned, at_word {aligned 7, ratio 0}, resynthesized 45, rules_hash 9b55a204, repo 2.3.0 | 동일 | 합격 |
| voice_swap.md §1 | 전환−경계 7단어×3목소리 전부 ≤0.5 ms | ≤1 ms | 합격 |
| voice_swap.md §2 | Δ전환 = Δ경계 7/7 (한국 −1.312 = −1.312) | 7/7 | **무수정 싱크 증명 성립** |
| sheet_injoon_vs_sunhi.jpg | 25쌍 육안 — 구성·패널·자막 동일, 절대 시각만 다름 | 동일 | 합격 |
| refusal_sync.jpg | 두 목소리 × 5개국, 경계 −0.15초 미전환 / +0.35초 전환. 순서 독일→영국→일본→호주→한국 | 동일 | 합격 |
| artifacts/phase4-v2.3.0 | final.mp4 injoon 292.44초 / sunhi 293.926초, h264+aac 2트랙, mix.flac·srt·provenance 동봉 | 동일 | 합격 |
| direction.py 무수정 | sha1 3411936a3cec 양쪽 동일(보고서·ARTIFACT_README 교차 확인) | 동일 | 합격 |

D-0021 §2 합격 조건 8행 전부 충족. ±0.15초 행은 D-0026 §4 표로 대체됨을 확인.

## 비차단(NB) — Phase 5 안에서 처리
- NB1 `fetch_data bgm`이 얕은 클론에서 실패(`bd37b58` 없음). run_log 기록만으로 두지 말고 `tools/fetch_data.py`가 얕은 클론을 감지해
  **명확한 오류 메시지**(`git fetch --unshallow` 안내)로 실패하게 한다(P6 조용한 실패 금지). 코드 3~5줄.
- NB2 provenance `voice`가 최상위 키다. 03/05 명세와 어긋나지 않으면 유지. 어긋나면 D 요청.
- NB3 `legacy_v3/__pycache__`는 미추적 잔존물이다. `.gitignore`는 이미 막고 있으니 각 컨테이너에서 지우면 된다. 조치 불요.

## 승인 절차(M2)
- 이 review가 Phase 4 승인이다. 내가 `overhaul/v2-map-engine → main` ff 푸시, `TAGS_PENDING.md`에 v2.3.0 → 706e982 append.
- Phase 5 착수 지침은 D-0029.

## R-0021 확인
D-0024·25·26·27 처리 확인. `chunk_ranges` 테스트 삭제 0으로 유지한 것 좋다.

## 파일명 시각 — KST로 재전환(사용자 지시 2026-09-28)
파일명 시각을 **KST(UTC+9)**로 바꿨다. 기존 파일 전부 +9시간으로 환산해 rename(내용 무수정). `check.py --next-name`이 KST를 낸다. Opus는 `--next-name` 출력만 쓰면 된다. 보고서 본문의 시각도 KST로 적는다.
