---
id: D-0298
from: fable
to: opus
kind: directive
responds_to: [R-0301]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 게이트 ① 승인(사용자 원문 "승인", D520) — 음성 → 연출 완성 → 믹스 → 콘티 판

## 0. 승인 기록
- `approve --project us_midterms_2026 --gate script_approval --by user`(감독 컨테이너, 2026-11-05 03:37:55Z) → 상태 **voice_timeline**. 승인 원고 지문 `script_sha1 b7ce51ec564a…`(v1.2 79문장). manifest 는 이 D 와 같은 커밋.
- **확인 요청**: 승인 기록 `shown.lint_errors` 가 "6" 으로 찍혔다(감독 컨테이너는 엔진 의존성이 없어 린트 일부가 오류로 셀 수 있다). 구현 컨테이너에서 `python -m orchestrator.main lint-script us_midterms_2026` 결과(0·0 기대)를 다음 R 에 그대로 붙여라. 0 이 아니면 원인·수정 뒤 보고(원고 문장을 바꾸는 수정이면 게이트 ① 재승인).
- R-0301 확인만(로고 예외 경로·기사 46·outlet_names 보강 — 커밋 b4d8cba 실물).

## 1. 지금 순서(W0)
1. `python -m script.plan projects/us_midterms_2026`(표준 음성 Supertonic 3 M3 ×0.95, MMS 정렬, 끝 억양 시안 C). plan.json·tts 는 커밋하지 않는다(artifacts 로).
2. 미디어: 받은 사진만으로 먼저 간다 — 못 받은 사진은 **빈 자리로 두지 말고** direction 에서 해당 문장의 사진 이벤트를 빼고 media_note 에 "Wikimedia 429 대기" 를 적는다(콘티 판 뒤 전편 전에 채우면 direction 재검증만). 로고 뱃지 5·기사 13·만평 2 는 등록 완료분이니 그대로.
3. direction v1 완성: D-0290 §6 문법 — 문장마다 카메라 사유, 핀 선 위, 요소 공백 ≤ element_gap, 뱃지 최소 유지, card 0, 패널 위 뱃지·사진 금지, area 는 데이터 파일과 일치(검사 hard), 콜드 오픈 area 동→서 delay, basics 패널(dots 100·checklist·quote 52편), act5 precedent. `engine.validate`/`checks` hard 0.
4. `python -m audio.mix` → `python -m engine.render … --animatic --jobs 4` → `out/animatic.mp4`(≤30 MB 전달본, `-c:a copy`) + `animatic_checks.json`·`animatic_provenance.json` + gate-view 미디어 요약 → artifacts 브랜치 → R(gate_request 아님 — 흐름 검토용 progress) + send_message. 감독이 사용자에게 보낸다.
5. 콘티 판에서 사용자 의견이 오면 그 영상 반영 → 재콘티(또는 사용자가 "완성본 직행" 이면 프리뷰 → 게이트 ②).

## 2. 보고에 넣을 것
- lint-script 출력, plan 요약(문장 79·정렬 점수·final_fall 적용 수·길이 초), direction 요소 수(area·marker·panel·photo·article·badge·quote·camera), checks hard/warn 목록, 사진 받기 진행(n/26), 콘티 판 md5·길이·크기.
