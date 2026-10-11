# 감독(Fable 역할) 세션 인수인계 — 2026-10-11 (v5.21.0)

새 감독 세션은 이 문서를 먼저 읽고, 그 다음 `back_and_forth/README.md`·`CLAUDE.md`·`docs/handoff/15`·`docs/handoff/DECISIONS.md`(D169~D181)를 읽는다.
사용자 사정(세션 한도)으로 감독 역할이 이 세션으로 옮겨졌다. **역할 이름은 그대로 "fable"** 이다(`check.py --me fable`, 문서 `from: fable`).

## 1. 역할
- 구현 세션(Opus, cloud session `session_0157T2pwd4LG8dkkcvZACoWJ`)이 코드를 만든다. 감독은 **코드를 직접 고치지 않는다.** D 문서(지시·판정)를 쓰고, R 보고를 **자기 컨테이너에서 실측**해 판정하고, DECISIONS 에 한 줄 붙이고, 커밋·푸시하고, Opus 에 `send_message`(claude-code-remote MCP, session_id 위 값)로 알리고, 사용자에게 한국어(~습니다 체, 짧은 문장, 핵심 요약 1~3줄)로 보고한다.
- 사용자 고유 결정(README §7: 주제·청취 합격·게이트 승인·권리 예외·색 선택)은 감독도 내리지 않는다 — 사용자에게 묻는다.
- 문서 파일명: `python back_and_forth/check.py --me fable --next-name <slug>`; 본문 `id:` 는 파일 번호와 같게. 커밋 첫 줄 `vX.Y.Z: …` 는 `VERSION` 과 같아야 한다(hook). 리베이스는 `SKIP_VERSION_CHECK=1`. 푸시는 `git push -u origin claude/bold-mccarthy-ttmagk`(실패 시 fetch → rebase → 재시도, **force push 금지**). PR 만들지 않는다. main 병합은 트랙 끝에 감독만.
- 커밋 트레일러는 세션 안내(system reminder)의 것을 쓴다. 저장소 산출물에 모델 이름을 적지 않는다.

## 2. 검증 환경(감독 컨테이너)
- 렌더·pytest 는 반드시 `FONTCONFIG_FILE=<scratch>/restore/fontconfig/fonts.conf` — 없으면 만든다: 시스템 `/etc/fonts/fonts.conf` 를 복사해 `conf.d` 에서 `12-unhinted-grayscale.conf` 를 제외한 설정(이전 감독 컨테이너는 scratch 에 두었다; 골든 md5 가 안 맞으면 이것부터 의심).
- **C8.3(D187)**: 변경마다 타깃 + `tests/anti_inertia`(골든 e2e) — 전체는 하루 1회·병합 직전, 구현 세션이 같은 커밋에서 전체를 통과했으면 감독은 타깃·골든만 확인하고 수치는 인용. 빠른 묶음 `python -m pytest -q -m "not slow"`.
- 전체 pytest `python -m pytest -q -rs` ≈ 35~43분. 환경 고정 비합격 9 = 1080p 티어 errors 3·클립 skip 1·fed 자산 failures 4 + `HormuzV3Test.test_final_mix_within_audio_qa_range`(미추적 산출물). 코드 비합격 0 이면 합격. 수집 수는 Opus 보고와 같아야 한다(최근 1548).
- 골든: 프로젝트를 scratch 에 복사(`prev`·`out` 제외)한 뒤 `python -m engine.render <copy> --preview golden` → `docs/handoff/reports/phaseV3/hormuz_baseline.json`(dark) · `phaseQ3/hormuz_light_baseline.json`(light; direction.yaml `stage_config.mercator.theme: light` + `geo.prep <copy> --theme light`) 과 md5(`md5_masked` 는 stamp_box 가리고) 대조 → 25/25. 참고 스크립트 논리: `tests/anti_inertia/test_provenance_e2e.py` `_masked_md5`.
- e2e 테스트는 전체 pytest 와 동시에 돌리지 않는다(`projects/hormuz_korea/prev/` 공유). 컨테이너 간 **오디오 md5 는 일치하지 않는 것이 정상**(D-0180 §2-1) — 영상 골든만 대조.

## 3. 현재 상태(2026-10-12 KST, v6.0.0 — 구현 opus 갱신, D-0213 §3-2)
| 트랙 | 상태 |
|---|---|
| V3·V5 표준 음성 | 종결 — Supertonic 3 M3 ×0.95 + 끝 억양 시안 C + MMS 정렬 = 표준(CLAUDE.md C0.2, D185·D189) |
| v5.21.0 보도 인용 B ~ v5.21.8 | 합격 |
| P1 gulf_pact_2026 | 사용자 의견 UF-01~12 반영·예멘 채움 제거(D207) → `artifacts/gulf_pact_2026-v5.22.4` 사용자 전달(D208). 재렌더 없음(v5.22.5~8 은 다음 렌더부터) |
| 사용자 의견 원장(C12) | UF-01~96 전부 guarded(open 0), 게이트 ② `require_feedback_guards`, provenance `user_feedback_guards`(프리뷰·콘티·전편) |
| 경로 이름표 | 전경 층 회피·수명 고정·전 구간 비충돌(D209·D210), `label_jump` hard, 렌더·검사 장애물 통일(RENDER-AP-024) |
| D-0201 | xdist `-n 4`(v5.22.9)·국경 numpy(v5.22.10) 합격 D212 |
| V4 edge 삭제 | v5.23.0 합격 D-0213. fed_timeline_demo 표준 음성 재생성(면제 1건 D-0213) |
| GOAL G3 개정 | **v6.0.0**(MAJOR): 18번 사용자 의견 원장 + 사용자 보호 hard 검사 연결, 4번 표준 음성 문구·시험 이름(별칭 삭제) |

## 4. 다음 할 일(순서)
1. 병합 직전 전체 pytest 1회(C8.3) — R 보고 머리말 `full_pytest:`.
2. 감독 main fast-forward(README §6.5). main 이 이 브랜치의 조상이 아니면 멈추고 보고(force 금지).
3. 그 뒤: 사용자 시청 의견이 최우선. 보류 — Q4a/Q4b/Q5/Q6/G(요청 시), 검증 LLM "출처 많으면 건너뜀"(Opus 결정 요청으로), creaky 꼬리 패치(사용자 지적 때만, D-0184 §2-①), gulf 원장 후보 메모 ①41.58초 뱃지 밑 카드 ③58초 이란 채움(사용자 지적 때만).

## 5. 사용자 결정 기록(이 기간)
D169 믹스 OK·시안 C / D171 정렬 모델 CC BY-NC 유지 / D172 통신사 사진 B / D173 light A / D174 순서(P1-1 을 V5 뒤) / D180 게이트 ① "대본 오케이". ElevenLabs 금지(D127), edge 삭제는 V4.

## 6. 사용자 소통
- 한국어, 공손·명료, 한 문장 60자 이내, 문단 3~4문장, 말미 "기억해야 할 핵심 요약" 1~3줄.
- 사용자가 결정할 것만 묻는다. 파일은 SendUserFile(scratch 경로 가능). 영상은 30 MB 이하로 재인코딩(`-c:a copy` 로 음성은 원본 유지).
