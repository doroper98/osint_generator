<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [overhaul-decision-log]
depends_on: [docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, docs/handoff/KICKOFF_PROMPT.md]
last_review: 2026-09-27
-->

# v2 개편 결정 기록 (append-only, 한 결정 = 한 줄)

판정 기준(사용자 지시 2026-09-27): ① 되돌릴 수 있는 선택 우선 ② 핸드오프 문서를 따름 ③ 핸드오프와 저장소 실측 규칙이 충돌하면 저장소 규칙을 따르고 그 사실을 기록.
반드시 사용자에게 묻는 것: 제한 휘장 사용(D5), GOAL 합격 기준 개정(D4), agents_reviewer 스키마 변경(D7).
형식: `| 날짜 | ID | 결정 | 근거(기준 번호) | 결정자 | 되돌리는 방법 |`

| 날짜 | ID | 결정 | 근거 | 결정자 | 되돌리는 방법 |
|---|---|---|---|---|---|
| 2026-09-27 | D1 | 기준 브랜치 = `overhaul/v2-map-engine` ← `origin/collage`(v1.2.1) | collage ⊇ main(35 commits, 역방향 0), 인물 라이브러리·공방이 collage에만 있음(13 §0.1 권장안) | 사용자 승인 | main에서 재분기 + 커밋 체리픽 |
| 2026-09-27 | D2 | 골든 mp4(30MB)는 git에 커밋하지 않고 `docs/handoff/golden/`에 로컬 복사(.gitignore) | ③ 저장소 규칙: `assets/audio/bgm/RIGHTS.md`가 대용량 커밋을 사고로 기록·정리 권고. 핸드오프 golden/README는 mp4 포함을 전제하나(②와 충돌) PNG 25장이 mp4와 픽셀 동일해 비교 기준은 유지됨. ① 나중에 LFS/커밋으로 바꿀 수 있음 | Fable(위임) | gitignore 줄 삭제 후 커밋 |
| 2026-09-27 | D3 | GmarketSans·IBM Plex·Noto 폰트 파일은 커밋하지 않고 `tools/fetch_data.py fonts`(Phase 1)가 다운로드·변환해 `assets/fonts/.cache/`(gitignore)에 둔다. 라이선스 텍스트만 `assets/fonts/LICENSES.md`에 커밋 | ② 09 §1.1 "배포 조건 확인 후 커밋 여부 결정"을 그대로 따름(확인 전 미커밋) ① 확인 후 커밋으로 전환 가능. Windows 사용자 환경에서는 fetch 스크립트가 `%LOCALAPPDATA%\Microsoft\Windows\Fonts` 설치까지 수행 | Fable(위임) | 폰트 파일 add + fetch 스크립트에서 캐시 경로만 변경 |
| 2026-09-27 | D6 | 소수점 발음은 저장소 정책 유지("십삼쩜일", TTS-AP-059). 핸드오프 신규 항목 TTS-AP-066은 "자막≠발음 분리 유지"로 문안 조정. ElevenLabs 연결 후 사용자가 청취해 최종 확정 | ③ 저장소 실청취 결정(v0.43.4)이 핸드오프 03 §5.4·12 §3.1과 충돌 → 저장소 규칙 | 사용자 | `rules/video_rules.yaml tts_rules.decimal_policy` 한 줄 + `bundle/text.py _decimal_tts` |
| 2026-09-27 | D8 | archive 브랜치는 **하나**, 이름 `archive/hyperframes-briefing`, 분기점 = `origin/collage` tip(9dcda27). hyperframes(briefing·demo·shorts)·remotion·scene_builder 연쇄·쇼츠 문서·design_sheets 전부 포함 | ② 02 §4.3이 명시한 이름을 그대로 씀(15 P2 `archive/*`와도 일치). 하나로 두는 이유는 복원 단순성(①). 이름이 내용보다 좁지만 브랜치 설명은 DECISIONS·CHANGELOG에 기록 | Fable(위임) | `git branch -m` 또는 추가 archive 브랜치 |
| 2026-09-27 | M1 | main 첫 머지는 **Phase 1(골든 재현) 통과 후**. 이후에는 사용자가 Phase 보고를 승인할 때마다 `git merge --ff-only overhaul/v2-map-engine` + 태그 `vX.Y.Z`. ff-only 실패 시 중단·보고 | 사용자 지시(첫 머지 시점) + 19 §4.1 권고(이후 주기). ① ff 머지는 태그로 되돌림 가능 | 사용자 + Fable | `git reset --hard <이전 태그>`는 main 이력 재작성이므로 사용자만 |
| 2026-09-27 | R1 | 개편 중 발견되는 모든 결정은 이 파일에 한 줄씩 추가하고 Phase 보고서에 요약한다. 과거 행 수정 금지(정정은 새 행 + `[supersedes …]`) | 사용자 지시 | 사용자 | — |
| 2026-09-27 | D10 | 사용자 제공 `20_GENRE_EXTENSION_FREE_PRODUCTION.md`를 `docs/handoff/`에 원문 그대로 편입(거버넌스 헤더만 부착)하고 GOAL G7 목록에 추가. 구현(Phase G1~G4: 무대 추상화·장르 프로필·시간축 무대·첫 비지정학 영상)은 20 §12대로 **Phase 6.9 이후**에 두며 Phase 0~6.9 순서는 바꾸지 않는다. Phase 0에서는 코드·규칙 파일을 미리 만들지 않는다(C8.4). 단 Phase 2 엔진 분해 때 카메라·`View`가 `(x, y, w)` 월드 좌표로 일반화 가능한 경계를 유지하도록 Phase 1·2 계획에 메모 | ② 20 §12가 순서를 명시 ① 문서 편입만이라 되돌리기 쉬움 | Opus(판정 기준 ①②) | 파일 삭제 + G7 한 구절 삭제 |
