---
id: D-0318
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-176 / D538 — "주(州)가" 가 [주까](株價) 로 읽힘 (UF-127 재발) → 발음 확정·장치 확장·교체본 3

## 0. 사용자 원문(2026-11-06 08:20 KST)
> "아 시작하자마자 'states가'를 의미하는 '주가'를 stock price의 주까 라고 말하면 어떻게 해."
- 위치: cold_0 tts "…지도 위의 주가 하나씩 색을 입기 시작했습니다." 원고 안 "주가" 는 이 한 곳(감독 grep). UF-127(경유가 → 경유까) 의 재발 — 그때 장치(`tensification_traps.suffix_nouns` 는 '유' 계열 명사만, `short_key_boundary`) 가 '주+가' 를 다루지 않았다. C12-4: 새 번호·recurs_of·AP 항목·장치 보강.

## 1. 원인 확정(추정 금지 — 실측)
1. 저장소 발음 사전에 "주가" 키가 있는지 확인(있으면 UF-127 과 같은 사전 원인 → 그 키를 문맥 키로 바꾸거나 제거). 없으면 Supertonic G2P/어휘가 '주가' 를 낱말로 경음화한 것.
2. **합성 실측**: cold_0 문장을 세 변형으로 합성 — (a) 현재 "주가" (b) "주 가"(띄움) (c) 대조 "주까" — 각각 '주' 모음 끝 → 'ㄱ' 파열 사이 **무성 폐쇄 구간 길이(ms)** 와 파열 에너지를 재서 표로. 경음 [ㄲ] 은 폐쇄가 길고 파열이 강하다. (b) 가 (a)/(c) 와 뚜렷이 다르고 평음 쪽이면 (b) 채택. 세 wav 와 수치를 artifacts `uf176/` 에.
3. (b) 로도 평음이 안 나오면 **원고를 바꾼다**: cold_0 text·tts "…지도 위의 주들이 하나씩 색을 입기 시작했습니다."(사용자 지시 = 게이트 ① 갈음, script_sha1 기록). 다른 방법(표기 트릭)은 쓰지 않는다.

## 2. 장치(UF-176 — 같은 커밋 묶음)
- `tts_rules.tensification_traps`: '유' 계열 밖으로 확장 — 조사 '가' 와 붙어 다른 낱말이 되는 짧은 명사 목록(예: 주(州)·시(市)·가(家)·수(數)… 실제로 경음화·의미 충돌이 나는 것만, 각 항목에 충돌 낱말 주석) + `spoken` 규칙(띄움 또는 그대로 — §1 실측 결과대로). 린트 `tensification_issues` 가 tts 에 "{명사}가" 가 보정 없이 남아 있으면 **hard**.
- 테스트: `tests/test_v740_tensification.py` 에 cold_0 원문으로 실패 케이스(보정 전) + 보정 후 통과. 원장 UF-176 guards 연결, UF-127 항목은 그대로(재발 기록은 UF-176 에).
- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md` 새 번호: UF-127 장치가 '유' 명사 목록에 갇혀 재발 — 원칙 "조사 '가' 앞 1음절 명사는 전부 후보, 목록이 아니라 실측 검사".

## 3. 절차
- 바뀐 문장만 재합성(cold_0 + 혹시 같은 보정이 적용되는 문장) → plan → direction 재검증 hard 0 → 720p 전편 → mix → mux → final_deliver(교체본 3) → artifacts final/(교체본 2 1816baa5 "교체됨") → phase_report R(실측 표·wav·script_sha1) + send_message. 감독이 사용자에게 보낸다.
