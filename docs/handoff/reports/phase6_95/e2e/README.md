<!--
tier: 3
last_synced_with: v3.2.0
ssot_for: [report-phase6_95-e2e]
depends_on: [tools/e2e_source_intake.py, tests/fixtures/e2e_intake/README.md]
last_review: 2026-09-28
-->
# e2e — X 캡처 3 + 기사 2 → 원고 초안 → 게이트 ① (D-0051 작업 13)

**전부 가상 픽스처**(`tests/fixtures/e2e_intake/README.md`) — 실존 계정·매체·사건 아님, x.com 접근 없음. LLM 단계는 실제 `claude -p`.
실행 3회: ① 픽스처 핸들 16자(X 한도 15자) → 스키마 거부, 픽스처 수정 ② build-research 에서 **LLM 사용량 한도(429)** → `--resume-from` 으로 완주, 그러나 판정 결함 발견(R-0064) ③ **D-0054 판정 보완 뒤 처음부터 재실행 = 이 폴더**(138초 완주, `run_log.jsonl`).

| 단계 | 결과 |
|---|---|
| plan-intake | IntakePlan(안내) → intake |
| add-source ×5 | 캡처 3건 판독 **정확**(계정·핸들·시각·본문·번역, `project/intake/drafts/`), 기사 2건. 전부 미확인 초안 |
| submit-intake(미확인) | **거부 rc 2**(18 §7) |
| 확인 | 기사 1건은 **Command Center 헤드리스 `c` 키**, 4건은 CLI confirm-source(주민 계정은 `--account-class private`) |
| submit-intake | intake → source_verify |
| verify-sources | 코드 판정 claims 4개: **corroborated 2 · unverified 1 · disputed 1**(status 3종 — 합격 조건 ≥2). clm_0004 "호위 선단이 노라 영해를 침범했다" = disputed(`attributed_only`, 양측 sides) |
| build-research | facts.json → research |
| build-script | 원고 5장면 11문장 → script_draft. 오류 0, 귀속 경고 0 |
| transition script_approval | 출처 검사(claims 밖 id·수치 공란 없음) 통과 → **게이트 ①** (`gate1_view.txt`) |

**귀속**: unverified claim(clm_0003, 단독 X 게시물) 인용 3문장 = "…됐다고 주장했습니다", "…돌려보냈다고 올렸습니다", "이 주장은 다른 출처로 확인되지 않았습니다" → 전부 귀속, **린트 귀속 경고 0**. disputed(clm_0004) 2문장은 양측을 "주장했습니다 / 반박했습니다"로 나눠 썼고 라벨 `<논쟁>`. 게시물 post 카드 컷: `post/unverified_watcher.png`(`<미검증>` 호박색), 개인 계정 `post/private_resident.png`(이름·핸들 가림, 시각 "게시 화면 시각").
남은 린트 경고 1건 = `now_0` 출처 공란(숫자 없는 마무리 문장 — 경고 등급).

**판정 결함과 수정**: 2회차에서 clm_0004 가 corroborated(두 기사가 "노라가 주장했다"고 보도한 것을 교차 확인으로 셈) → R-0064 → D-0054 C(판정 ⓪ 분쟁 = disputed/unverified, 귀속 인용은 사실 근거 제외·contested 승격, 라벨 `<논쟁>`) → 3회차 disputed. 2회차 기록은 싣지 않았다(판정 코드가 바뀐 뒤 무의미).
부수 효과(보고): 귀속 표지에 "밝혔·전했"도 있어 "당국이 ~라고 밝혔다" 인용은 사실 근거로 세지 않는다. 이번 실행에서는 LLM 이 표지 없는 부분만 인용해 clm_0001·0002 는 corroborated 로 남았다.

그 밖 실측 수정: 캡처 원문 줄바꿈이 post 카드에 ▯ 로 찍힘 → 공백 정규화, 시간대 없는 캡처 시각에 "(UTC)" 를 붙이던 것 → "(게시 화면 시각)".
