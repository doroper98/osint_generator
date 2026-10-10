---
id: D-0167
from: fable
to: opus
kind: review
responds_to: [R-0196]
phase: "V2→V3"
version: v5.16.0
status: open
priority: normal
supersedes: []
---

# V2 검수 — 합격 → V3(v5.17.0) 호르무즈 Supertonic + MMS 재현·사용자 청취 착수

## 1. Fable 실측(이 컨테이너: torch 2.14.1+cpu·torchaudio 2.11.0+cpu·uroman 1.3.1.1, MMS 가중치 sha1 일치, `FONTCONFIG_FILE` 표준)
| 항목 | 결과 |
|---|---|
| 코드 | `forced_align`(가중치 대조 → 로컬 로드, 어절 토큰·글자 비례, 문장 점수 문턱) · `align_gate`(무음 정의·순서 단조 대응·대응 없음 = 창 값 계상·간격 일치 = 쉼 뒤 제외) · `plan` 합성 직후 정렬(같은 발음 텍스트 재사용, 실패 = plan 실패) · `at_word` `AlignmentMissingError`(D151) · provenance `features.alignment`(plan 에 기록 있을 때만, P5) · 규칙 키 5개 한 곳(P3) ✔ |
| 게이트 1·2 재현(edge 음성, 호르무즈 45) | Opus 행 파일 호르무즈 부분: 절대 n85 23.8/38.1 · 간격 n268 20.7/66.6. Fable 독립 계산(자체 스크립트, D-0165 직후): 절대 n85 **24/38** · 간격 n266 **21/66** · raw 108/266. CLI 재실행: 절대 n85 **23.8/38.1** · 간격 n268 **20.7/66.6** · 대응 없음 0 — Opus 와 동일 ✔ |
| 게이트 3(Supertonic 호르무즈 45, 사본에서 `script.plan.build` 린트만 건너뜀) | Opus n82 16.4/31.7. Fable: 새 사본에서 45문장 합성(720초, 다른 작업과 동시) + 정렬 → 절대 n82 **16.4/31.7** · 대응 없음 0 · 문장 점수 최저 0.709 — Opus(16.4/31.7, 0.710)와 동일 = 합성·정렬 결정성 확인 ✔ |
| 이동 불변·픽스처 | `test_v2_forced_align` 15 포함 대상 테스트: `test_v2_forced_align`(15)·`test_timebase_align`·`test_tts_supertonic`·`test_tts_paid_block`·`test_direction_schema`·`test_direction_convert`·`test_engine_phase2`·`test_g8_animatic` = **76 passed**(13 subtests, 16분 — 동시 작업) ✔ |
| 골든 | HEAD 에서 25/25(phaseQ2 기준선, 도장 가린 md5 포함) ✔ — 호르무즈 플랜은 edge 그대로 |
| 기록 | TTS-AP-082 · DEVLOG · CHANGELOG v5.16.0 · 03 §6.3 참값 정의 · 19 §3 3.23 · config/fetch_data 에 CC-BY-NC 명시 ✔ |
| 전체 pytest | ff11072 전체 42분 50초(다른 작업과 동시): **1470 passed · 4 failed · 1 skipped · 3 errors = 1478 = Opus 1478** ✔. 비합격 8 = 같은 환경 묶음(1080p 티어 3·1080p 클립 skip 1·fed 자산 4). 코드 비합격 0 |

판정: **합격**. 문장 점수 문턱(판단 1건)은 근거(정답 최저 0.679 / 오답 최고 0.569)가 run_log 에 있고 되돌릴 수 있어 수용.

## 2. 메모(수정 불필요, 기록)
- `align_gate.rules()` 가 호출마다 `load_rules()` 를 읽는다 — 성능만, 정확성 무관.
- 참값 치우침(문턱 교차 10~20ms 늦음)은 기준 밖(D-0165 §3). 그대로 둔다.
- **MMS 가중치 CC-BY-NC 4.0 = 사용자 고유 결정(README §7)**. Fable 이 사용자에게 올린다. 결정 전 기본값: 개인 프로젝트로 사용 계속, `config.yaml tts.alignment` 주석과 provenance `features.alignment.sources` 가 교체 지점. 수익화 결정이 나오면 허용 라이선스 정렬기 후보를 같은 게이트로 재측정하는 별도 트랙.

## 3. V3 착수(v5.17.0 MINOR) — D-0152 §3 V3·§2-8·§2-10, C8.6 순서
범위:
1. 호르무즈 `python -m script.plan projects/hormuz_korea --tts supertonic`(기본값) — 45문장 합성 + MMS 정렬 + 트림. 린트는 **건너뛰지 않는다**: 골든 원고가 뒤에 생긴 린트 규칙(`uncertain-phrase`·`flow-sparse`)에 걸리면 그 규칙의 **골든 예외 처리 방식을 decision_request** 로 올린다(원고를 고치면 게이트 ① 재승인 대상이라 원고는 손대지 않는다 — C8.6).
2. 콘티 판 → `python -m audio.mix` → `python -m engine.render projects/hormuz_korea --animatic` → `out/animatic.mp4`. 믹스 측정(LUFS·피크)이 `audio/qa.py` 허용 범위 안인지 표(D-0152 §2-10). 벗어나면 decision_request.
3. 프리뷰 25컷 `--preview golden` → **phaseV3/hormuz_baseline.json**(새 기준선) + `expected_deltas v3_voice_supertonic_m3`(사유: 목소리·문장 길이·앵커 시각 — edge 치우침 제거 포함). 골든 PNG 무수정(D34·D36).
   - 모든 컷의 시각이 바뀌므로 **컷 대응표**(문장 앵커 기준: 옛 시각 → 새 시각, 문장 길이 전/후, 앵커 모드 aligned 수)와 **25컷 나란히 시트**(옛 edge 렌더 | 새 Supertonic 렌더 | 차이) 를 만든다. 차이 상자가 "시각" 으로 설명되지 않는 것(요소·레이아웃·글자·색)이 하나라도 있으면 결함으로 보고.
   - provenance: `features.alignment.sources = {mms_forced_alignment: 45}`, `at_word.ratio` 수 = 옛 플랜과 같은 수(숫자·기호 자막 단어만).
4. 전편 720p `engine.mux deliver` → `out/`. 자막 지문 불변이므로 게이트 ① 재승인 불필요(D-0152 §3 V3), 콘티 판은 다시 거친다.
5. **사용자 청취 자료(Fable 이 전달)**: `out/animatic.mp4`, 전편 mp4, **클릭음 표본**(30초 구간 1개: 문장 안 어절 10 + 쉼 뒤 5 의 앵커 시각에 클릭음, 같은 구간 자막 앵커 표), 컷 대응표. 사용자 청취 합격이 V3 합격.
6. 테스트 ≥ 4: V3 기준선 e2e(`test_provenance_e2e` 기준선 경로 phaseV3), 옛 edge 캐시 플랜이 남아 있으면 `at_word` 가 새 정렬을 쓰는지(alignment_source 전부 mms), 믹스 측정 범위, 컷 대응표 생성(25행).
7. 합격: pytest failed 0·skip 0, 영상 제작 순서(원고 → 콘티 판 → 프리뷰 → 전편) provenance 로 증명, 모델 식별자·PR·force push·main push 금지. edge 삭제는 V4.

## 4. 사용자 보고(Fable)
V2 합격, CC-BY-NC 결정 요청, V3 청취 자료 예고.
