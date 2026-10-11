---
id: D-0187
from: user
to: opus
kind: decision
responds_to: [R-0212]
phase: "P1-3"
version: v5.21.1
status: open
priority: urgent
supersedes: []
---

# 사용자 결정 — 콘티 판 합격 · 음악 넣기 · 본영상 진행 (감독 기록)

사용자 원문(2026-10-11, 감독 세션 대화): **"음악을 넣고 만들고, 콘티 합격. 본영상 만들어"**

## 1. 결정
1. **콘티 판 흐름 합격** — gulf_pact_2026 animatic(md5 `e8eab455…`, 325.24초, light). C8.6 흐름 검토 완료.
2. **음악 넣기** — 연출가의 `sound.bgm: null` 을 바꾼다. 곡은 지난 합격 영상과 같은 공용 BGM `music.zabriskie_patriarch`, 균형은 사용자 승인값 bed_gain 0.43(D169). 다른 곡을 쓰려면 감독에게 먼저 묻는다.
3. **본영상 진행.**

## 2. 진행 순서(감독 지시)
1. D-0186 §2-1 무스카트 대비 국소 보정 PATCH(골든 두 테마 25/25 무변화) + §3-2 article-unused 사유 + §3-3 겹침 카드 왼쪽 잘림 확인(잘림이면 고침).
2. 음악 `sound.bgm` 설정은 연출 손질로 기록(`origin: ai+human_edit` 유지, 사유 "사용자 D-0187"). 음성 타임라인은 그대로라 콘티 판 기록(`animatic_provenance`)이 유효해야 한다 — 거부되면 콘티 판을 다시 만들고 그 사실을 보고한다(건너뛰기 금지).
3. `approve --gate preview_approval` — 승인 문구에 사용자 원문을 그대로 남긴다.
4. 프리뷰 25컷 QA → 전편 720p → mux. mux 에서 `[rights-exceptions]` 경고·엔딩 크레딧 B 행·설명란 "사진 출처 (보도 인용)" 줄 확인.
5. 전편 `final.mp4`·provenance·checks·audio_qa·컨택트 시트·mux 경고 전체를 커밋·보고하고 감독 세션에 send_message. 사용자 전달은 감독 검수 뒤 감독이 한다(30 MB 넘으면 감독이 재인코딩).

## 3. 기록
DECISIONS D184.
