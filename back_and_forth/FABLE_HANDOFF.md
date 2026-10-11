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
- 전체 pytest `python -m pytest -q -rs` ≈ 35~43분. 환경 고정 비합격 9 = 1080p 티어 errors 3·클립 skip 1·fed 자산 failures 4 + `HormuzV3Test.test_final_mix_within_audio_qa_range`(미추적 산출물). 코드 비합격 0 이면 합격. 수집 수는 Opus 보고와 같아야 한다(최근 1548).
- 골든: 프로젝트를 scratch 에 복사(`prev`·`out` 제외)한 뒤 `python -m engine.render <copy> --preview golden` → `docs/handoff/reports/phaseV3/hormuz_baseline.json`(dark) · `phaseQ3/hormuz_light_baseline.json`(light; direction.yaml `stage_config.mercator.theme: light` + `geo.prep <copy> --theme light`) 과 md5(`md5_masked` 는 stamp_box 가리고) 대조 → 25/25. 참고 스크립트 논리: `tests/anti_inertia/test_provenance_e2e.py` `_masked_md5`.
- e2e 테스트는 전체 pytest 와 동시에 돌리지 않는다(`projects/hormuz_korea/prev/` 공유). 컨테이너 간 **오디오 md5 는 일치하지 않는 것이 정상**(D-0180 §2-1) — 영상 골든만 대조.

## 3. 현재 상태(2026-10-11 16:40 KST)
| 트랙 | 상태 |
|---|---|
| V5 끝 억양(v5.20.0) | 합격 D-0180. 사용자 최종 청취 자료(전편·전/후 발췌) 전달함 — **사용자 청취 판정 대기**(그 판정이 V3·V5 최종) |
| v5.20.1 light A | 합격 D-0183 |
| v5.20.2 octave_clean | 합격 D-0184(관찰 3건 기록) |
| v5.21.0 보도 인용 B | R-0211(f8fda51) **검증 중 — 미판정.** 코드 리뷰는 끝(D-0177 원칙과 일치, 판단 ③ 별도 photo 항목+press_of 수용). 이전 감독 컨테이너 실측: **골든 dark 25/25·light 25/25 무변화 확인됨(f8fda51)**, 타깃 `test_b_press_quote` 17 passed. 남은 것: 전체 pytest(Opus 1548·0·0) 재현 → 합격 D 문서 + DECISIONS. 이전 감독 컨테이너의 실행 결과는 사라졌으니 다시 돌리거나, 시간이 없으면 타깃(`tests/test_b_press_quote.py` 17 passed 확인됨)+골든만 돌리고 전체 pytest 는 Opus 수치를 인용하되 그렇게 적는다 |
| P1 사용자 영상 gulf_pact_2026 | 게이트 ① **승인됨**(D180 "대본 오케이"). P1-2 진행 중: 음성 48문장 325.24초(final_fall 47), 사진 A 5장 + B 1장(Reuters via Al Jazeera, riyadh_airport_2), 미디어 표 통과. 다음 Opus 단계: AI 연출(light) → audio.mix → **P1-3 콘티 판** → 감독에게 |

## 4. 다음 할 일(순서)
1. R-0211 판정 마무리(위). 판정문에 "B 사진 파일·레지스트리·권리 항목은 Opus 컨테이너에만 있음 — 콘티 판 검수 때 카드 프레임·provenance `rights.exceptions`·mux `[rights-exceptions]` 경고로 확인" 을 적는다.
2. **P1-3 콘티 판 검수**: Opus 가 `out/animatic.mp4`·provenance·컨택트 시트를 보내면 ① provenance `features_used`(prosody·map_theme light·media 비트·기사 카드 press_quote) ② 경고 목록(`[article-unused]`·`[media-density]`·`[rights-exceptions]` 1건은 정상) ③ B 사진이 그 기사 카드 프레스 칸에만, 크레딧 줄 "사진: Reuters via Al Jazeera" ④ 자막·발음(숫자·기호 없음) ⑤ 길이·장면 흐름 을 보고, **사용자에게 콘티 판 영상을 보내 흐름 검토**를 요청한다(C8.6 — 건너뛰기 금지). 사용자 승인 → Opus 가 `approve --gate preview_approval`(require_animatic) → 프리뷰 25컷 QA → 전편 720p → 사용자 최종 청취.
3. 전편 뒤: V4(edge 경로 삭제, D-0179 순서상 사용자 최종 청취 뒤) 지시 → 판정 → main 병합(감독).
4. 보류: Q4a/Q4b/Q5/Q6/G 는 요청 시. 검증 LLM "출처 많으면 건너뜀" 문제는 P1 뒤 Opus 결정 요청으로 받는다. creaky 꼬리 연속성 패치는 사용자가 끝 거칠기를 지적할 때만(D-0184 §2-①).

## 5. 사용자 결정 기록(이 기간)
D169 믹스 OK·시안 C / D171 정렬 모델 CC BY-NC 유지 / D172 통신사 사진 B / D173 light A / D174 순서(P1-1 을 V5 뒤) / D180 게이트 ① "대본 오케이". ElevenLabs 금지(D127), edge 삭제는 V4.

## 6. 사용자 소통
- 한국어, 공손·명료, 한 문장 60자 이내, 문단 3~4문장, 말미 "기억해야 할 핵심 요약" 1~3줄.
- 사용자가 결정할 것만 묻는다. 파일은 SendUserFile(scratch 경로 가능). 영상은 30 MB 이하로 재인코딩(`-c:a copy` 로 음성은 원본 유지).
