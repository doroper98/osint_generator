---
id: D-0305
from: fable
to: opus
kind: decision
responds_to: [R-0307]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 게이트 ② — **감독 승인**(사용자 위임 UF-166/D521). 전편 전 연출 글자 3건 → 720p 전편 → 전달본

## 1. 감독 실측(artifacts e670c547 gate2/)
- sheet.jpg md5 cfddc97d 일치, 원크기 12컷 전부 열어 봤다. hard 0(auto·12컷) 확인.
- UF-167 주 이름: 132·318.5·403.9·427 컷에서 주 이름이 지도 라벨로 보이고 도시는 몇 개로 줄었다(외국 도시 없음). UF-168: 작은 글자 흰 테두리가 얇아졌다. UF-169: 외곽선이 얇아져 202·215.5·290 에서 투박함 없음. UF-170: bars 가 텍사스·캔자스·NC·메인·GA·MI·MS(개표 중 표기)·FL 에서 같은 축척으로 읽힌다. D526 잉크 부제 대비 TX 4.78·KS 5.07·ME 5.47·NC 4.84 확인. D-0301 두 건·D-0302 "석"·로고 뱃지(민주 132·공화 427)·마셜 실사(221.5)·1937 사진(354) 확인.
- 승인: `approve --project us_midterms_2026 --gate preview_approval --by fable --comment "사용자 위임 UF-166/D521 · 감독 판정 D-0305(R-0307 gate2 e670c547, 12컷 hard 0)"` — **구현 컨테이너에서 실행**(require_animatic 이 보는 out/animatic_provenance.json·plan.json 이 거기 있다). 승인 기록이 든 manifest 를 커밋·푸시하고 R 에 `gate_decisions` 항목을 인용(감독이 대조). DECISIONS D527.

## 2. 전편 렌더 전 연출 글자 3건(direction 만, 재프리뷰 없음 — final 시트로 확인)
| # | 위치 | 고칠 것 |
|---|---|---|
| 1 | act2_15 메인 marker sub "잭슨 53.4 · 콜린스 46.5" | bars 와 숫자 중복 → "콜린스 약 30년 임기 종료"(또는 "1995년 이후 첫 민주 상원"). 다른 주 marker sub 도 bars 숫자와 겹치면 역사 한 줄로 |
| 2 | prominent 모드 주 이름 색(318.5 본토 w60 — 짙은 채움 위 회색이 약함) | `admin1_modes.prominent.color: ink`(D526 방식, 마커 이름과 같은 토큰). 골든 불변 |
| 3 | 미시간 bars 후보 이름 "엘세이드" | 원고·데이터·bars 한 표기로 통일 — 원고가 쓰는 표기(없으면 "엘사예드") |
- 셋 다 검증 hard 0 확인 뒤 전편.

## 3. 전편·전달
- `engine.render --res final --jobs 4` → `audio.mix` → `engine.mux` → `final_deliver.mp4` ≤30 MB(`-c:a copy`) → artifacts `final/`(mp4·전달본·final_sheet(12컷 이상)·provenance·audio_qa·description·credits·srt·MD5SUMS) → **phase_report R**(D-0290 §6: 커밋 목록·테스트(관련 + anti_inertia, 전체 pytest 1회 C8.3 — 병행)·checks hard 0·provenance(area·bars·rights_exceptions·user_feedback_guards)·육안 컷 6+·차단 호스트 표·미포함 사유 표(사진 9·클립·제프리스 초상 등)·길이·md5) + send_message.
- 전편 시작 전까지 들어온 사진만 추가. 사용자에게는 감독이 보낸다.
- 전달 뒤 첫 작업(C12-2): UF-163~170 장치(script_grammar 선거 제도 문장·정당 상징 미디어·권리 예외 기록 테스트·작업 순서 메모·admin1 모드·halo·area outline 상한·bars 검사) → 원장 guards 갱신 → `feedback_ledger.py --write`.
