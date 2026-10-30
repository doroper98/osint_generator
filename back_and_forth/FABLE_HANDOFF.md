# 감독(Fable 역할) 세션 인수인계 — 2026-10-11 (v5.21.0)

## 0-2. 2026-10-30 — 병행 트랙: 『중국의 기술 수출통제 확대(2026.10)』(사용자 결정 D-0282)
- 사용자 지시로 **별도 감독(Fable) 세션**이 이 영상을 묻지 않고 완성본까지 만든다. 브랜치 `claude/china-export-controls-2026`. 세션 id 는 DECISIONS D278 행. 쇼케이스 트랙(0-1)과 독립 — 이 세션(sweet-galileo)은 쇼케이스·E7 만.

## 0-1. 2026-10-28 갱신 — E0 쇼케이스 트랙(감독 세션 `session_017Yuw8kbxf9Vxri6LoH5Je4`, Fable 5.1)
- **현재 트랙**: E0 쇼케이스 데모 2편 + 카탈로그 층(back_and_forth D-0251 §1·§5·§6·§7). 브랜치 `claude/sweet-galileo-7yok3b`(main 8d93103 위), 버전 v7.4.0.
- **구현 세션**: `session_017Yuw8k4hDAiSpVRGtFv4Lu`(Opus 5.5, env_01SnvGMv3UmrvejEraZxEACo, 2026-10-28 04:06Z 생성). 옛 구현 세션 `session_012yN5MN9eH1tBnNrQ1D8sBG` 은 diesel v2 종결·disconnected.
- **구현 세션 2(재기동, 2026-10-29 12:39Z)**: `session_017Yuw8mVchPLgYxtnfEwjjh`(Opus 5.5, 같은 env). 구현 세션 1 은 2026-10-28 09:39Z 계정 5시간 한도로 failed·disconnected(마지막 커밋 51cc7fa — 틀·UF-137 guarded까지). 남은 것: econ 콘티 판 v2 → geo 콘티 판 → 골든 25/25 → A/B → 게이트 ② → final·catalog·결합본.
- **구현 세션 3(재기동, 2026-10-30 03:33Z)**: `session_017Yuw8mZjzL9rxkApRyBCoR`(Opus 5.5, 같은 env). 세션 2 는 2026-10-30 01:18Z 계정 5시간 한도로 failed(마지막 커밋 7b6b997 — D-0274 §1·§2 완료, 연준 클립 넷 등재). 남은 것: preview_v9 확인 → 렌더 작업 수(클립 npy) → econ 원고 발언 자리 2곳 → 게이트 ① 재승인 → 연출 → 콘티 판 v3 → geo 콘티 판 v2(strikes 액자) → 게이트 ② → final·catalog·결합본.
- **사용자 결정 이 기간**: D264(비공개 시청·권리는 기록만) · D265(보완 방향·쇼케이스) · D266~D268(연준 탈락·호르무즈 미흡·diesel 기준 작품, C0 개정). 원장 UF-132~136.
- **사용자에게 갈 것(순서)**: ① showcase_geo 원고(gate-view) ② showcase_econ 원고 ③ 콘티 판 2편 ④ 게이트 ② 프리뷰 시트 + A/B 시트(D108 보정) + 카탈로그 요소 표 ⑤ final·catalog·결합본. 사용자 2026-10-28 원문 "영상은 어딨어" — 착수 지시를 기다리다 늦었다. 다음부터 계획 승인 = 착수.

## 0. 2026-10-19 갱신 — 승계 규칙(사용자 결정 D256)과 현재 상태
- **승계 규칙**: 감독 세션의 컨텍스트 사용량이 95% 에 이르거나 사용 한도가 차단되면, 감독은 `create_session(model: claude-opus-5-5, title "감독(fable) 승계 — diesel_road_2026 v2", prompt: 이 문서 §0 를 읽고 이어받으라)` 로 **별도 감독 세션**을 연다. 역할 이름은 그대로 `fable`. 구현 세션(아래)은 바꾸지 않는다. 새 감독은 이 문서 → `back_and_forth/README.md` → `CLAUDE.md` → `docs/handoff/15` → DECISIONS D238~ 순으로 읽는다.
- **현재 트랙**: diesel_road_2026 v2(브랜치 `claude/diesel-road-v2`, 버전 v7.4.0). 구현 세션 = cloud session `session_012yN5MN9eH1tBnNrQ1D8sBG`(Opus). 아티팩트 `artifacts/diesel_road_2026-v7.4.0`(교체본 2 대기). main 병합 보류 중(D-0245 §1).
- **열린 D**: D-0245(그래프 3종 복원, [series-unused]·[panel-dropped] hard), D-0246(발음 '유가' 경음화 — 발음 사전 "경유 가", tensification_traps 규칙 키, 린트 hard, TTS-AP-083), D-0247(dual_line 빈 달 점선 보간, 모든 영상). 구현 순서: 사전+보간 → 재합성·믹스 → 프리뷰 hard 0 → 콘티 판 재렌더(의무) → 게이트 ②(D-0243 위임) → 720p → artifacts 교체 2 → R → 장치(UF-126·127·128 guarded) → E 단계(빠른 묶음+영향 느린 노드, 골든 화소 비교, DEVLOG·CHANGELOG, `merge --no-ff`, PR 없음) → 최종 R.
- **사용자에게 할 일**: 교체본 2 가 오면 final.mp4(part00+part01 결합, MD5SUMS 대조)·그래프 3컷·두 문장 wav 를 한 줄로 전달. 병합이 끝나면 커밋·테스트 수 한 줄 보고.
- **예약 점검**: 감독 세션에 send_later 로 45~60분 간격 점검이 걸려 있다. 승계 시 새 세션에서 같은 점검을 다시 건다(옛 세션 트리거는 update_trigger enabled=false).
- **2026-10-19 02:45Z 승계 시점 상태(사용자 지시 "fable 한도 94%")**: 구현 세션은 8ab77fe2(짧은 사전 키 낱말 경계 + act2_35·act3_15 재합성, 두 문장만 변경 확인)까지 push, 테스트 작성 중. 남은 것: 믹스 → 프리뷰 hard 0 → 콘티 판 재렌더(~40분) → 게이트 ②(D-0243 위임) → 720p(~70분) → QA → artifacts 교체 3 → R(wav·MMS 간격 표·그래프 3컷). **artifacts 2e1fba69(md5 6d24abca, 그래프 복원만)는 사용자에게 보내지 않는다**(발음·보간·카드 겹침 미반영). 열린 D: D-0245·D-0246(+D258 보충)·D-0247·D-0248. 원장 UF-126~129 open(장치는 영상 전달 뒤). 옛 감독 세션(`session_016v5HgxdsPNKcUYQ94ZkAoo`)의 점검 트리거 `trig_01AookPVpgqVkk2F5AqWvu5W`(03:43Z)는 새 감독이 자기 점검을 건 뒤 옛 감독이 끈다. **구현 세션은 R 을 `send_message` 로 옛 감독 세션 id 에 보내고 있다 — 새 감독은 첫 메시지로 구현 세션에 새 session_id 를 알리고, 이후 R 은 새 id 로 받도록 한다.**
- **승계 세션(2026-10-19 02:49Z 생성)**: `session_01CLMApgWisjaB6TYfe7EUdx`(Opus 5.5, 사용자 요청 '높음' 노력). 구현 세션에는 옛 감독이 이미 새 id 를 알렸다(보고는 새 id 로).
- **새 감독이 처음 할 일(순서)**: (1) 이 문서·README·CLAUDE.md·DECISIONS D238~D258 읽기 (2) `git fetch`·브랜치 확인 (3) 구현 세션에 send_message("감독 승계, 이후 보고는 이 세션으로") (4) send_later 로 45~60분 점검 예약(점검 문구는 옛 트리거와 같은 틀: fetch → 진척 → 교체 3 이 artifacts 에 있으면 결합·md5·그래프 3컷·두 문장 프레임·wav 확인 후 사용자에게 한 줄 전달 → 장치·E 단계·merge --no-ff 확인) (5) 옛 감독 세션에 send_message("승계 완료, 트리거 꺼도 됨") (6) 사용자에게 한 줄 보고.
- **원장**: UF-126·127·128 status open — 장치가 달리면 guarded 로(구현 세션이 올림). `python tools/feedback_ledger.py --write`.

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
- **보고문을 보내기 전에 금지 문구 패턴으로 자기 점검**(UF-145, 사용자 원문 2026-10-30 "니가 작성하는 문구에 이런내용이 없도록 강하게 쪼여"): `rules banned_phrases.patterns`(수렴 은유·승부 은유·"남는다/올라온다" 마무리·청구서 의인화 등)를 사용자에게 가는 모든 글·원고·화면 문자열에 적용한다. 도구 `tools/slop_check.py`(D-0281) 가 생기기 전에는 python 한 줄로 돌린다.
- **샘플·시트·콘티 판은 만들어지는 즉시 사용자에게 보낸다**(UF-144, 사용자 원문 2026-10-30 "만들어진 샘플들은 바로바로 보여줘"): 구현 R 이 artifacts 를 가리키면 그 자리에서 받아 SendUserFile — 다른 산출물과 묶어 기다리지 않는다.
