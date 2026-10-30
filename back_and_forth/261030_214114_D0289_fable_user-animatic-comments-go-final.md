---
id: D-0289
from: user
to: opus
kind: decision
responds_to: [R-0290, D-0288]
phase: "CN1"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 결정 — 콘티 판 v2 "아주 만족", 의견 3건 반영한 **완성본으로 바로 직행**

사용자 원문(2026-10-30, 감독 세션 대화, 캡처 1장 첨부 — 경기도 marker·route 라벨):
> "콘티 아주 만족스러워. 세가지 코멘트가 있어. 그거 반영하는 완성본으로 바로 직행해.
> 1. 1:30~1:50 즘 까지 거의 아무것도 안뜨고 자막과 나레이션만 나오는 구간이 있어. 사진 하나정도 더 추가 하는게 좋을거 같아.
> 2. 이미지의 경로 개략, 좌표 비공개 라는 문구는 빼.
> 3. 마지막 쯤에 시진핑과 트럼프 뱃지가 나오는데 너무 빨리 사라져."

원장: UF-160·161·162(status open — 이 영상은 고쳐서 먼저 보내고 장치는 전달 뒤 첫 작업, C12-2). 게이트 ② 승인 기록에 경고 줄로 남는다.

## 반영(연출 v3, 원고·음성 불변)
1. **UF-160**: act1_8~act1_10(약 90~110초, "오픈소스·논문 공개 기술 제외" / "앱·웹 범위 밖, 현지 설치 범위 안" / "수출 전 상무부 시스템 등록") 에 **사진 1장**(가운데 액자). 후보: 데이터센터·서버실(PD — NASA·DOE 연구소 등) 또는 베이징 상무부 청사(PD/CC BY 만). 권리 기록·자료사진 표기. 사진 합계 12(D-0288 ③ 커터헤드 포함).
2. **UF-161**: act3_2 route 라벨 "굴착기 2대 · 경로 개략" → **"굴착기 2대"**, 경기도 marker sub "전력구 공사 · 좌표 비공개" → **"전력구 공사"**. 개략·비공개 사실은 **엔딩 카드 표기 행**(D85 방식)에만 남긴다("경로·공사 지점은 개략 표현"). 검사·린트가 라벨 문구를 강제하면 `lint_waivers` 에 사유 "사용자 결정 UF-161" 로 면제하고 R 에 적는다.
3. **UF-162**: act4_6 트럼프·시진핑 뱃지 end → **act4_7 끝(+0.3)** 까지(act4 마지막 문장 "상무부는 아직 … 내놓지 않았습니다" 까지 유지). 겹치는 요소 없음 확인.
4. D-0288 보강 ①~⑤(조시 quote·부산 회담 뱃지·커터헤드 사진·사진 자리·베선트 사유)도 같이.

## 순서(사용자 지시 "완성본으로 바로 직행" — 감독 결정 D507)
- **콘티 판 v3 재검토는 생략**한다(사용자가 콘티 흐름을 승인했고 음성·원고가 그대로다). 다만 상태 머신·검사는 그대로 돈다: 연출 v3 → checks hard 0 → `engine.render --preview auto`(preview_qa, 시트는 R 에 첨부만) → 감독 `approve --gate preview_approval --by fable --comment "사용자 결정 D-0289(원문 '콘티 아주 만족스러워 … 완성본으로 바로 직행해') · 사용자 위임 D-0282"` → **720p 전편** → `engine.mux`(deliver) → 전달본 ≤30 MB(`-c:a copy`) + provenance + phase_report → artifacts 브랜치 → 최종 R + send_message.
- 콘티 판 기록은 v2(`out/animatic_provenance.json`, 음성 타임라인 동일)로 require_animatic 을 충족한다. 연출만 바뀌므로 다시 만들지 않는다 — 코드가 거부하면 콘티 판 v3 를 `--jobs 4` 로 돌리되 감독 검토 없이 바로 프리뷰로 간다.
- 프리뷰 시트가 나오면 R 하나(시트·checks·바뀐 컷 5곳 확대: act1_9 사진·act3_2 라벨·act4_6 뱃지·act2_9 quote·act2_3 뱃지) — 감독은 그 R 로 게이트 ② 를 친다. 전편 렌더는 승인 뒤.

## 장치(전달 뒤 첫 작업 — 구현 세션, 같은 브랜치)
- UF-160: `[media-gap]` 검사 — 사진·영상·기사·패널·뱃지·quote·route 어느 것도 없는 자막 구간이 `media_beats.max_text_only_run_sec`(규칙 키, 제안 15) 를 넘으면 hard. 테스트 1.
- UF-161: 규칙 키 `labels.disclosure_in_endcard_only: true` — marker sub·route label 에 "개략"·"비공개" 낱말 금지 검사(hard) + 엔딩 표기 행 생성. W1.1 M5 문구 개정(DOC).
- UF-162: `badge.min_hold_sec`(규칙 키, 제안 6) + `[badge-short]` 검사 hard. 테스트 1.
- 원장 guards 채우고 status guarded, `feedback_ledger.py --write`.
