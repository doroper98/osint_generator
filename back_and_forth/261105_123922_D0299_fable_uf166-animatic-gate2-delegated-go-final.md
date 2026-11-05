---
id: D-0299
from: fable
to: opus
kind: decision
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 결정 UF-166 / D521 — 콘티 판 검토·게이트 ② 는 감독 위임, 완성본 직행

## 0. 사용자 원문(2026-11-05 12:45 KST)
> "콘티 나한테 승인 받을 필요 없이 니가 검토해서 승인하고 완성본 직행해"

## 1. 바뀌는 절차(D-0298 §1-4·§1-5 대체)
1. 콘티 판(`--animatic`)은 그대로 만든다(코드 강제 `require_animatic`, 건너뛰지 않는다). 만들면 artifacts + R + send_message — **사용자 검토를 기다리지 않는다.** 감독이 콘티 판을 보고 D 로 판정(흐름·요소·호흡). 고칠 것이 있으면 direction 수정 → 재콘티(사용자 의견이 아니라 감독 판정이므로 1회로 끝내는 것을 목표).
2. 감독 통과 → 바로 `--preview auto` 시트·checks·provenance → R(gate_request). 감독이 `approve --project us_midterms_2026 --gate preview_approval --by fable --comment "사용자 위임 UF-166/D521"` → D.
3. 게이트 ② 뒤 **720p 전편**(`engine.render --res final --jobs 4` → `audio.mix` → `engine.mux`) → `final_deliver.mp4` ≤30 MB(`-c:a copy`) → artifacts `artifacts/us-midterms-v7.4.0` → phase_report R(D-0290 §6 항목 + 차단 호스트 표 + 미포함 사유 표). 감독이 사용자에게 보낸다.
4. 사진 Wikimedia 429 로 못 받은 것: 콘티 판은 받은 것만으로, **전편 렌더 전까지** 받아 direction 에 넣고 재검증(hard 0). 전편 시작 시점까지 못 받으면 그 문장은 사진 없이 가고 미포함 표에 사유(media_note).
5. R-0301 §막히는 것(콘티 판 빈 자리) 은 §1-4 로 해소.

## 2. 그대로인 것
- 게이트 ② 전 `asset_library.py check` 0, C12 open 은 이 영상 의견(UF-163~166)만 — 앞선 영상 의견은 전부 guarded(148) 확인됨. checks hard 0, banned_phrases 0, 권리 기록(로고 D519 예외 포함), provenance(area·rights_exceptions·user_feedback_guards).
- 사용자 의견이 중간에 오면 그 자리에서 원장 기록 + 그 영상 반영(C12-1).
