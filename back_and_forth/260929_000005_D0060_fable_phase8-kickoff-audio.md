---
id: D-0060
from: fable
to: opus
kind: directive
responds_to: []
phase: "8"
version: v3.4.0
status: open
priority: urgent
---

# Phase 8 착수 — 오디오 (v3.4.0)

정본: 13 §Phase 8(BGM 레지스트리, `music_intensity`, 곡 교체 교차 페이드, 오디오 QA −14 LUFS·음악 −14~−18dB), **10 §3(베드·볼륨 이력: bed_gain 0.47 = 사용자 합격, 바꾸지 않는다)·§7 개선 과제 5개**, 19 §6 8행(RIGHTS.md 크레딧 문구 그대로), 17 §2 `sound:` 블록(D-0047), C9. 현재: `audio/mix.py`(bed·duck·sfx·fade, 모듈 상수 SR·SEED·TAIL_SEC·FADE_IN/OUT_SEC·FX_DUCK), `engine/mux.py` loudnorm(rules audio.loudnorm), `tools/audio_report.py`(loudnorm 측정·내레이션 대비 음악 dB, v2.0.1), `assets/audio/bgm/RIGHTS.md`(CC BY 3곡, 사용 1곡, D22 복원 절차), credits.yaml `rights: [music.zabriskie_patriarch]`, 6.95 NB11 **F1**(연출가가 음악 크레딧 없는 프로젝트에 BGM → 권리 실패 → 재요청 `bgm: null` 스키마 위반).

## 0. 첫 커밋
`VERSION` 3.4.0 + CHANGELOG(v3.3.0 종결). 그리고 **audio/mix.py 모듈 상수 → `rules audio`**(SR 제외: 샘플레이트는 코덱 상수로 두되 규칙에 `sample_rate` 로 적고 테스트로 일치 확인). 값은 **그대로**(P3, 근거 없이 바꾸지 않음). 증명: hormuz `out/mix.f32` md5 = Phase 7 artifacts 의 mix(무손실 flac 디코드 비교 또는 f32 md5). test_no_magic_numbers 대상에 `audio/` 추가.

## 1. 커밋 순서(한 커밋 한 의도, `v3.4.0:` prefix)
1. **BGM 레지스트리**(10 §7-1): `assets/audio/bgm/registry.yaml` — id(= credits `rights` 키, 예 `music.zabriskie_patriarch`), 파일명, sha1(RIGHTS.md 값), 길이, 라이선스, **표기 문구(RIGHTS.md 작가 표준 표기 그대로)**, 분위기 태그, BPM(실측 or null — 추측 금지). 3곡 등재(미사용 2곡은 sha1 을 fetch_data 로 복원해 실측; 복원 불가면 `sha1: null·available: false` 로 적고 등재는 한다). RIGHTS.md 는 사람용 문서로 유지, **레지스트리가 SSOT**: 크레딧 카드·description.txt 의 음악 문구는 레지스트리에서 생성(현재 credits.yaml 수기 문구와 같은 결과 — hormuz 엔딩 카드 25컷 END MAD 0 로 증명).
2. **`sound.bgm` = 레지스트리 id**: direction.yaml `sound.bgm` 은 파일명이 아니라 레지스트리 id. 파일명은 코드가 레지스트리에서 푼다. **없는 id·레지스트리 밖 파일명 = 로드 오류**(P10). hormuz·taiwan_ai·hormuz_ai·hormuz_camauto·prompts/examples 의 direction 을 id 로 옮긴다(원본 v3 direction 수정은 이 한 줄뿐 — DECISIONS 에 적는다). `credits.rights` 의 music.* 와 `sound.bgm` 불일치 = 권리 오류(check_credits).
3. **F1 해결(P6 — 조용한 폴백 없음)**: 연출가 입력에 `{music_list}` = 그 프로젝트 credits 에 등록된 음악 id 목록(+분위기 태그). **목록이 비면 "sound.bgm: null 허용 + intensity/cues 만"** 으로 스키마를 바꾼다(재요청이 스키마를 어기던 원인 제거). bgm null 이면 믹서는 베드 없이 내레이션+sfx 만 섞고 provenance `audio.bgm: null` 로 기록 — 이것은 폴백이 아니라 명시 상태다. 절차 합성 음악(10 §6 v1)은 **이번 Phase 에 이식하지 않는다**(사용자 결정 §7 후보로 phase_report 에 한 줄).
4. **장면별 강도 `music_intensity`**(10 §7-2): 이미 `sound.intensity` 앵커 곡선이 있다(D-0047). 추가할 것은 **원고(script.yaml) 장면에 `music_intensity` 힌트(0~1, 선택)** 를 두고 연출가가 `sound.intensity` 를 만들 때 입력으로 받는 것 — 코드가 원고 힌트를 direction 에 자동 주입하지 않는다(P8, 연출은 LLM). hormuz v3 는 힌트 없음(무변경).
5. **곡 교체 교차 페이드**(10 §7-3): `sound.bgm` 을 `[{id, from: 앵커}]` 목록으로도 받는다(문자열 1개 = 목록 1개와 동치). 경계에서 규칙 `audio.crossfade_sec` 교차 페이드. hormuz 는 1곡이라 mix 무변경(md5 증명). 시연은 taiwan_ai(2곡, 미사용 CC BY 곡 복원 가능할 때) — 불가하면 합성 사인 픽스처로 테스트만.
6. **오디오 QA = 검사기 하나**(10 §7-5, 13): `tools/audio_report.py` 의 측정 함수를 `audio/qa.py` 로 옮기고(tools 는 얇은 CLI), checks 에 `audio` 항목 추가: 최종 −14 LUFS ±1·TP ≤ −1.5(rules audio.loudnorm)·내레이션 구간 음악 −14~−18dB(규칙 `audio.qa.music_under_narration_db: [-18, -14]`)·피크 ≤ master_peak. **hormuz v3 를 먼저 실측**: 범위 안이면 hard, 밖이면 **규칙을 v3 에 맞추지 말고 decision_request**(사용자 합격본과 13 수치의 충돌 = 내 결정). provenance `audio` 단계(qa 결과 요약, bgm id, crossfade 수, bed_gain).
7. **문장 간 음량 편차**(10 §7-4): hormuz 45문장 RMS 편차 실측(`reports/phase8/sentence_rms.json`). 정규화는 **실측 뒤 decision_request**(수치 없이 옵션을 만들지 않는다).
8. **taiwan_ai F1 재실행**: 음악 크레딧 없는 상태로 AI 연출 1회 → 권리 실패 없이 `bgm: null` 로 통과, 크레딧 있는 상태 1회 → 레지스트리 id 로 통과. 둘 다 provenance audio 기록.
9. **테스트 ≥ 15**: 레지스트리 파리티(id=credits 키·sha1·문구), 없는 id 오류, bgm null 믹스, 교차 페이드 길이·연속성, QA 임계(합성 픽스처로 안/밖), 규칙 리터럴 0, hormuz 회귀(25컷 MAD 0 + mix md5 동일).
10. **산출물** `docs/handoff/reports/phase8/`: registry 사본, hormuz `audio_qa.json`·`sentence_rms.json`, taiwan F1 두 실행 로그·provenance, crossfade 시연(파형 png), run_log·asset_md5. **artifacts/phase8-v3.4.0**: taiwan_ai 전편(짧음, bgm 레지스트리 id·crossfade 시연판) mp4 + hormuz 는 mix 무변경이라 mp4 재렌더 없음(md5 로 증명). 영상이 나오면 내가 사용자에게 전달한다.

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 사용자 합격 음량 유지 | hormuz `mix.f32` md5 = Phase 7 artifacts 와 동일(bed_gain 0.47·duck 0.5 무변경), 25컷 MAD 0 |
| 권리 SSOT | 크레딧 카드·description 음악 문구 = 레지스트리 문구(테스트), 없는 id = 오류 |
| F1 | taiwan_ai 음악 없는 프로젝트에서 AI 연출 루프가 권리 실패·스키마 위반 없이 완주 |
| 오디오 QA | hormuz final.mp4 −14 LUFS ±1, 음악/내레이션 dB 실측 보고(범위 밖이면 decision_request) |
| 하나의 검사기 | 오디오 측정 코드 경로 1개(audio/qa.py ← checks·tools 둘 다 호출) |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 15, 환경 의존 테스트는 사유 있는 skip |

## 3. 하지 않는 것
ElevenLabs 전환(10 §7-4 는 실측만), 절차 합성 음악 이식, 번들(9), 해상도·성능(10), bed_gain·duck 수치 변경, 골든 PNG 교체, mp3 git 추적.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report. 결정 필요 시 decision_request(§7 사용자 고유 결정 후보: 절차 합성 음악 이식 여부 — 요청만 적고 기다리지 않는다). 턴 종료 금지(21 §6).
