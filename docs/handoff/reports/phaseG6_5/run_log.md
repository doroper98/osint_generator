<!--
tier: 3
last_synced_with: v4.7.0
ssot_for: [phaseG6_5-run-log]
depends_on: [engine/checks.py, engine/direction.py, audio/mix.py, rules/video_rules.yaml, back_and_forth/260929_213242_D0104_fable_dmz-mine-reports-decisions-merge.md]
last_review: 2026-09-29
-->

# Phase G6.5 실행 기록 — dmz_mine 브랜치 병합·결정 반영 (v4.7.0)

지침 D-0104, 결정 D-0106·D-0107. 시각은 KST. 재기동 18(병합~오디오 재측정)·재기동 19(D2(b)·norm_ref) 세션.

## 0. 컨테이너 준비

phaseG6 run_log §0(= phaseG5·G4 §0) 그대로. 재기동 19 차이:
- pip·apt(ffmpeg·fonts-noto-cjk)·CA·자산 복원(phase7·phase9·G3·G4 artifacts)·fetch_data·geo.prep 는 하위 에이전트가 했다. 에이전트가 사용 한도로 중간에 끝났지만 랫클리프 국기·초상·권리·geo.prep(480p·1080p)까지 끝나 있었다.
- 남은 한 단계 `python tools/media_fetch.py projects/hormuz_korea --res 1080p`(클립 npy 2)는 첫 전체 pytest 가 `test_phase10_scale` 3건 오류로 알려 줘 따로 돌렸다.

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·CHANGELOG | 9f99ef7 | docs 테스트 |
| 병합(충돌 6) + 원격 D-0105 | 0fb7e6d · 5f97401 | 병합 커밋 메시지(충돌 해결 목록), DECISIONS D90·D91·D95 |
| D2(a) 연출 문법 | 06cf4d3 | 테스트 1(연출·수정 프롬프트 둘 다) |
| D3 W1.1 체크리스트 | 488231d | WORKFLOWS |
| D5 미사용 미디어 삭제 | 0ac50f0 | media_registry 30 항목 |
| D4 reopen --to direction | be7f030 | 테스트 2 |
| D-0106 1-C 엔딩 카드 롤 | 07ad73b · 957d9eb | 테스트 3, checks `endcard_roll` warning |
| D-0106 2-B auto: people | 1a839c1 | 테스트 2 |
| S1 LLM-AP-009 | 295ad1e | 기록만(G8 후보) |
| 오디오 재측정(post_limiter, 0.8) | d1bc80b | `audio_qa_post_limiter.json` |
| 갤러리 35 | 27e4775 | `gallery.json`·`gallery.jpg` |
| D2(b) 좌표 근거 | 2be7c80 | 테스트 3, checks 21항목, provenance `geo.unsourced` |
| norm_ref 0.7 복귀 | 4c09701 | `audio_qa_norm_ref07.json` |

## 2. 명령

```bash
python -m audio.mix projects/hormuz_korea           # norm_ref 0.7, out/mix.f32·bed_stats.json
python -m audio.mix projects/fed_policy_2026
# 스크래치 폴더에 mix.f32·bed_stats.json 복사 → audio.qa.loudnorm_two_pass(+post_limiter) → AAC 오디오만 → audio_qa
```

## 3. 운영 기록

- **dmz_mine_2026 — 자산 미보존.** 재렌더에는 tts 재합성·초상·권리 재수집이 필요하다(D-0106). 프로젝트는 데이터로만 유지하고 프리뷰를 만들지 않았다.
- 전편 재렌더는 하지 않았다(사용자 지시 D-0103). 오디오는 mux 와 같은 음량 경로를 영상 없이 스크래치 폴더에서 돌렸다. 프로젝트 `out/final.mp4` 는 만들지 않았다.
