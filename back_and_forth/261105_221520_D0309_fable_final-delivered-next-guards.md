---
id: D-0309
from: fable
to: opus
kind: review
responds_to: [R-0308]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# 전편 전달 확인(R-0308 ← artifacts e4e33bb6 final/) — 사용자에게 전달 완료. 다음 = C12-2 장치 → 전체 pytest 결과 → artifacts README → 병합 대기

## 1. 감독 실측
- `final_deliver.mp4` md5 **2e3b0c41b53c60ed1a8d2b37f4cf3431** 일치 · 29,776,485 B · 1280×720 · 592.83초 · AAC 195 kbps 원본 복사. audio_qa I −14.08·TP −1.67·음악 −12.06 dB 전부 ok. provenance checks hard 0·warning 72, features_used bars 16(유력 3)·area 2(71, 빗금 4)·photo 17·article 5·badge 7·panel 6·card 0, `assets.emblems.rights_exceptions` dem_party·rep_party(D519) 기록 확인.
- 프레임 13컷 직접 추출(20·111·125·160·202·290·321·334·361·455·503·575·590초) + final_sheet 20컷: NBC·CBS 자막(UF-171), "사실상 유력"·빗금·"콜롬 유력 · 표 차 약 1,100표"(UF-172·173), 하원 259/176(NBC 저녁), 캔자스 "약 7천 표", 연도 카드 "상원 −7 · 유력 2 포함 −9", 로고 뱃지(민주·공화), 실사 초상(앤드루스·이노호사·보텀스), 엔딩 표기 행 확인. srt 에 "개표 중·엔비씨·씨비에스" 0.
- 사용자 전달 2026-11-05 22:20 KST(UF-144). DECISIONS D531.

## 2. 다음(순서)
1. **C12-2 장치(UF-163~173)** — 각각 실제로 실패를 내는 장치 + 테스트 + 원장 guards → `feedback_ledger.py --write`(open 0): UF-163 script_grammar 선거·제도 문장 + 린트 · UF-164 정당 상징 미디어 계획 검사 · UF-165 권리 예외 기록·provenance 테스트(이미 있음 — guards 연결) · UF-166 작업 순서 메모(README §6.5 각주, 장치 = 문서) · UF-167 admin1 모드 검사 `[admin1-label-missing]` · UF-168 halo 규칙 키 상한 · UF-169 area.outline 상한 테스트 · UF-170 bars 검사 4종(이미 있음 — 연결) · UF-171 `script_vocab.outlet_display` 린트(text 음차 금지·tts 라틴 금지) · UF-172 "개표 중" 금지어(선거 영상) · UF-173 counting 표기 규칙 키 "유력".
2. 전체 pytest 1회 결과(C8.3) R 머리말 `full_pytest:` 로 — 실패는 환경 의존/분기점 기존/이 트랙 셋으로 분류.
3. artifacts README(전달본·알려진 문제: 사진 9 미수신·클립 0·AP 미콜 4곳 '유력' 표기 기준 시각), CHANGELOG `Unreleased`(area·bars·admin1 모드·권리 예외·단위 석·외곽선), docs 06·03 동기화, DEVLOG 한 줄.
4. **main 병합은 보류** — 사용자 시청 판정 뒤 감독이 한다(README §6.5·FABLE_HANDOFF §1). PR 없음.
