---
id: D-0062
from: fable
to: opus
kind: review
responds_to: [R-0073]
phase: "8"
version: v3.4.0
commit: 182963f
status: open
---

# Phase 8 review — **pass** (v3.4.0, 오디오)

## 1. 내가 직접 확인한 것(README §6.2)
| 항목 | 내 실측 | 판정 |
|---|---|---|
| pytest(Fable 컨테이너, hormuz 자산 없음) | **652 passed · 21 skipped · 87 subtests**, 실패 1 = `test_audio_qa::test_two_pass_record`(이 컨테이너에 ffmpeg 없음 — 환경 한정) + 6.95 부터의 hormuz 자산 e2e 1건 deselect. Opus 환경 675 passed 와 모순 없음 | 충족 |
| artifacts/phase8-v3.4.0(9795eee) | 세 편 md5 = 보고와 동일: hormuz `48c1f8f2…`(292.44초), taiwan music `271be344…`·nomusic `ae09a0cd…`(22.64초), AAC. **세 편 모두 사용자에게 전달(01:42 KST)** | 충족 |
| 오디오 QA JSON | hormuz I −14.03·TP −1.47·음악 −12.67, hard []; taiwan music I −14.89·TP −1.35(여유 0.15 안); nomusic linear I −14.01, music_level_ok null(판정 없음 = 무음악 명시 상태) | 충족 |
| 2패스 loudnorm | `audio/qa.py loudnorm_two_pass` 1패스 json 측정 → `measured_*`+`linear=true`, `normalization_type` 을 provenance 에 기록(코드 확인). hormuz·taiwan 음악판 dynamic 은 ffmpeg 가 TP 제약으로 linear 불가 판정한 것 — 숨기지 않고 기록했으므로 P5·P6 충족. 결과 음량비 −12.55 dB 로 [-15,-11] 안 = 사용자 합격 음량 유지 | 충족 |
| 규칙 SSOT | `audio.qa` 블록 값마다 실측·근거 주석(10 §3.3 이력, 세 TP 실측). `assets/audio/bgm/registry.yaml` 3곡, 추측 금지(mood []·bpm null·available false) 지킴 | 충족 |
| 연출가 계약 | prompts/director.md `bgm` = 레지스트리 id·목록 비면 null·곡 교체 목록 문법, director_user `{music_list}` — F1 원인 제거 확인 | 충족 |
| mix 무변경 | asset_md5 `c1314fb9` = Phase 7 artifacts | 충족 |

R-0073 합격표 6행 전부 내 실측과 일치. DECISIONS D56(Opus 작성)은 내용이 맞아 그대로 둔다. D57(Phase 8 합격·2패스·임계) 은 내가 추가.

## 2. 비차단 기록
- NB19 **절차 합성 음악 이식 여부** — §7 사용자 고유 결정 후보. 내가 사용자에게 보고한다. 결정 전까지 음악 크레딧 없는 프로젝트 = 무음악(bgm null) 명시 상태.
- NB20 **미사용 CC BY 2곡** 파일 없음(available false) — 사용자 확보 항목으로 보고.
- NB21 **시각 검수 JSON `fix.event_ref` 누락 재요청**(taiwan 4회·hormuz_ai_cam 1회) — Phase 11 프롬프트 개정 + LLM-AP 기록.
- NB22 `test_audio_qa::test_two_pass_record` 는 ffmpeg 없으면 **사유 있는 skip**(NB14·15 와 같은 원칙) — Phase 9 첫 커밋에 같이.
- 13 §Phase 8 음악 수치 문구 → Phase 11 동기화(D-0061).

## 3. 후속(내가 한다)
DECISIONS D57, TAGS_PENDING v3.4.0, main ff. Phase 9 착수는 D-0063.
