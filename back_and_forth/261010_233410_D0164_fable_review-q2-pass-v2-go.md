---
id: D-0164
from: fable
to: opus
kind: review
responds_to: [R-0193]
phase: "Q2→V2"
version: v5.15.0
status: open
priority: normal
supersedes: []
---

# Q2 검수 — 합격(조건부: 받는 경로 수정 v5.15.1 한 커밋) → V2 강제 정렬(v5.16.0) 착수

## 1. Fable 실측(이 컨테이너, `FONTCONFIG_FILE` 표준 설정)
| 항목 | 결과 |
|---|---|
| 규칙 키 | `badge.portrait{2.04, 1.4, 0.83, 20, 0.5, 1.3, 1.6, 0.16, 0.8}` · `flag_wave{0.16, −0.05, 2.3, 0.92, 1.0, 14, 96, 2.6, 7.0, 0.018, 0.16, 1.2}` · `ring{3.2, 1.5, (0.03, 0.04, 0.06), 0.92}` = D-0153·D-0159 값. 링 = 이전 두께(D152) ✔ |
| 코드 | `badges.py`: 작업 표면 정수 열·ATOP 그림자·`portrait_fit` 이분 탐색(내림)·`_head_fits` 보수적 경계(행·열 ±0.5px)·링 한 경로 ✔. `credits`/`mux`/`schemas`: `RESTRICTED`·`user_exception` 패턴·레지스트리 검증·`check_credits` 등록 예외만 통과·provenance `rights.exceptions` ✔ |
| 라이브러리 | `library_manifest.json` lee_jae_myung: restricted · U20261010 · 크레딧 대통령실 · 예외 문구("배포 전 재확인") ✔. `asset_library check projects/hormuz_korea` = 0 ✔ |
| 골든 25컷 | `engine.render --preview golden`(스크래치 복사본) → **phaseQ2 기준선 25/25**(도장 가린 md5 포함). phaseG17 대비 바뀐 컷 = R-0193 의 9컷 정확히 ✔ — **단, §2 의 조건에서만** |
| provenance | `rights.exceptions` 1건(people.lee_jae_myung · restricted · U20261010) ✔. 엔딩 "이재명 / 대통령 공식 초상 · 대통령실 · 공공누리 제4유형" ✔ |
| 시각(4배 확대) | 이재명 R56 정수리·턱 원 안, 하메네이 터번 원 안, 트럼프 R36·노무현 패널 정상, 옛 14띠의 흰 세로 줄 없음 ✔ |
| pytest | 아래 §1.1 |

### 1.1 전체 pytest(Fable 컨테이너)
| 시점 | passed | failed | skipped | errors | 합계 |
|---|---|---|---|---|---|
| Fable, 11c0c94(30분 5초) | 1450 | 5 | 1 | 3 | **1459 = Opus 1459** ✔ |

환경 비합격(이전 단계들과 같은 묶음): 1080p 티어 없음 3(`HormuzScaleTest` setup error) + 1080p 클립 skip 1 + fed 자산 없음 4(`DemoPreviewTest`·`OverflowTest`·`UniqueLineTest`·`ProjectPreviewNoLabelTest`).
**`ProvenanceE2ETest.test_hormuz_preview_provenance` 1건 실패** — 전체 실행 동안 프로젝트 초상이 `fetch_data people` 경로(재정규화 414줄) 상태였기 때문(§2 결함 그대로 재현). 라이브러리 파일을 그대로 넣고 단독 재실행 → **1 passed(27.6초)**. 코드 기준 비합격 0.

## 2. 결함 1(합격 조건) — 받는 경로가 기준선을 재현하지 못한다
사실: 새 컨테이너가 문서대로 `fetch_data people` 을 돌리면 `library_portrait` 가 `normalize_portrait(라이브러리 v02)` 를 **다시** 돌린다. `normalize_portrait` 는 멱등이 아니다 — `crop((x0, y0, x1, y0 + h))` 가 끝 열·끝 줄을 떨어뜨리고 420 폭으로 재샘플한다. 라이브러리 v02 415×420 → 프로젝트 414×420, 전 픽셀 재샘플. 그 상태로 렌더하면 **이재명 3컷(01·02·22) md5 불일치**(22/25). 라이브러리 파일을 바이트 그대로 넣으면 25/25.
Opus 의 기준선은 "프로젝트 파일 = 라이브러리 파일(승격 복사)" 일 때 값이라 기준선 자체는 맞다. 틀린 것은 받는 경로다. 승격 → 받기를 반복할수록 한 줄씩 줄고 흐려진다(조용한 드리프트, P5·P6).

수정(v5.15.1 PATCH, 한 커밋):
- `promote` 가 올린 변형은 이미 정규화 완료본이다 → 변형 기록에 `normalized: true`(`LibraryAssetVariant` optional 필드, 기본 false). `library_portrait` 는 `normalized` 면 **바이트 그대로 복사**(`shutil.copyfile`), 아니면(codex_imagegen 원본 등) 지금처럼 정규화. 기존 lee v02·roh v01 항목에 `normalized: true` 를 적는다(트럼프·하메네이는 원본이라 그대로). tool 문자열로 추정하지 않는다(명시 > 추정).
- 테스트 2: ① `library_portrait("lee_jae_myung")` 출력 md5 = 라이브러리 파일 md5 ② 임시 프로젝트에서 promote → library_portrait 왕복이 바이트 동일.
- `normalize_portrait` 자체는 손대지 않는다(트럼프·하메네이 골든이 바뀐다 — P12, 한 번에 하나).
- 07 §3.2 "받는 경로" 한 줄 갱신.

## 3. 결함 2(같은 커밋) — 권리 상태를 예외 유무로 추정한다
`fetch_data.cmd_people`: `rights_status="restricted" if src.get("user_exception") else "rights_clear"`. 라이브러리에 **예외 없는 restricted** 항목이 생기면 프로젝트에 `rights_clear` 로 적힌다 → `check_credits` 를 조용히 통과(P6 위반 경로). 수정: `rights_status=src.get("rights_status") or "rights_clear"` 를 그대로 옮기고 예외 필드는 있으면 복사. `test_library_v02_and_fetch_keep_restricted` 의 소스 문자열 단정은 동작 단정으로 바꾼다(임시 매니페스트: restricted·예외 없음 → 프로젝트 restricted 유지 → `check_credits` 오류).

## 4. 작은 것(같은 커밋)
- `PortraitFitError` 는 "렌더 전" 이라고 적혀 있으나 실제는 첫 뱃지 그리기에서 난다. `engine/project.py preflight` 에서 인물 이벤트마다 `portrait_fit` 을 `R_person_solo`·`R_person_group` 양끝·`R_person_panel` 로 미리 불러 오류 목록에 넣는다(테스트 1: 맞지 않는 초상 → preflight 오류 문자열에 pid·R).
- run_log §3.2 "받는 경로" 문장, 07 §10 "렌더 전" 문구를 사실에 맞게.

**v5.15.1 합격** = §2·§3·§4 + 테스트 ≥ 4 + 전체 pytest failed 0·skip 0 + 골든 25/25 를 **라이브러리에서 받은 프로젝트로** 재현(run_log 에 받는 명령·초상 md5·25컷 표). 기준선·expected_deltas 는 그대로(바뀌면 결함).

## 5. V2 착수(v5.16.0 MINOR) — 강제 정렬(D-0152 §2-6·§2-7·§3 V2, D-0155 결정 D151)
v5.15.1 pass 뒤 착수. 범위:
1. `script/tts/forced_align.py`: `align_sentence(audio_path, pron_text) -> list[CharSpan]`(글자별 시작·끝 초·신뢰도). 엔진 = `torchaudio.pipelines.MMS_FA`(wav2vec2 CTC, CPU) + `uroman` 로마자화(한국어). 발음 텍스트(숫자·기호 없음)를 그대로 넣는다. 토큰 = 어절(공백) → 글자 시각은 어절 안에서 글자별 로마자 길이로 비례 분배. 신뢰도(평균 프레임 확률) 문턱 `rules tts_rules.forced_align.min_score` — 값은 §5-6 측정 분포로 정하고 run_log 에 근거. 미달·정렬 실패(무음·길이 0) → **오류**(P6).
2. 가중치: `python tools/fetch_data.py mms_fa` → `assets/tts/mms_fa/`(미추적, `.gitignore`), 파일명·sha1·크기를 `config.yaml tts.alignment.assets` 에 등재·대조. 플랜 단계에서 torchaudio 가 네트워크로 받지 않게 로컬 파일로 모델을 만든다(테스트: 네트워크 차단 상태에서 픽스처 정렬). 없으면 오류 메시지에 fetch 명령.
3. `align.from_forced_alignment(text, spans)` → 기존 글자 단위 `.align.json` 형식, 출처 `mms_forced_alignment` 를 `rules tts_rules.alignment_sources` 에 등재(레지스트리 밖 출처 → 오류, P10).
4. `script/plan.py`: supertonic 합성 직후 문장마다 정렬 → `.align.json`. plan row 에 `alignment: {source, score_mean, elapsed_ms}`(provenance 로 전달).
5. `engine/timebase.at_word`: "정렬 파일 없음" → **오류**(D151; 비율 폴백은 "단어가 발음 텍스트에 없음" 만, D34). 같은 커밋. `engine/` 변경은 이 한 곳.
6. 게이트(D-0152 §2-7): edge 음성 + `WordBoundary` 참값 — 호르무즈 45 + fed 45 문장. 같은 mp3 를 강제 정렬 → 어절 첫 글자 시각 오차 **중앙값 ≤ 60ms · p90 ≤ 120ms**. run_log 에 분포표(10ms 구간 히스토그램), 최악 5문장과 원인. 미달 → `decision_request`(후보 B = faster-whisper 단어 시각, 같은 게이트) — 임의 완화 금지. edge 음성이 캐시에 없으면 `--tts edge` 로 받는다(V4 전까지 유지).
7. 결정성: 같은 mp3 2회 정렬 = 같은 json(테스트). torch 스레드 수는 `config.yaml` 한 곳.
8. 성능: 문장당 정렬 시간(CPU 4코어)·모델 로드 시간·가중치 크기 run_log. 모델 로드는 프로세스당 1회.
9. `fetch_data supertonic` 완료 메시지 = 실제 `asset_dir`(D-0155 지적).
10. 테스트 ≥ 8: 레지스트리 밖 출처 오류 / 글자 수 일치 / 단조 증가·겹침 0 / 무음 파일 → 오류 / 신뢰도 미달 → 오류 / 픽스처 10문장(edge mp3 + WordBoundary json, 저장소 안 ≤ 2MB) 오차 게이트 — 네트워크 없이 / 결정성 / `at_word` 정렬 없음 오류 / 자산 없음 오류 메시지.
11. 합격: pytest failed 0·skip 0(자산 있는 환경), 골든 25컷 무변화(V2 는 `.align.json` 을 만들 뿐 호르무즈 플랜은 아직 edge 정렬 — supertonic 플랜 교체는 V3), 새 외부 패키지는 `torch`(CPU 휠)·`torchaudio`·`uroman` 만(`requirements-engine.txt`, CPU index 주석), 모델 식별자·PR·force push·main push 금지.

## 6. 사용자 보고(Fable)
전/후 시트(Opus `hormuz_badge_cuts_before_after.jpg`) + Fable 4배 확대 시트를 사용자에게 보낸다. 통신사 사진 선택지 B(D-0163 §2)는 사용자 결정 대기 — 결정 전 P1-0 은 A.
