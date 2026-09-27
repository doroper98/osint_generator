<!--
tier: 2
last_synced_with: v2.0.1
ssot_for: [phase1-runbook]
depends_on: [docs/handoff/reports/PHASE1_ENV_SETUP_WSL2.md, tools/fetch_data.py, tools/legacy_v3_run.py, tools/golden_compare.py, tools/contact_sheet.py, tools/audio_report.py]
last_review: 2026-09-27
-->

# Phase 1 골든 재현 런북 — 명령 한 줄씩

> **용도**: 사용자가 WSL2(또는 같은 Ubuntu 환경)에서 v3『호르무즈와 한국』을 처음부터 끝까지 재현하는 절차다.
> Phase 1 **판정**은 Opus 클라우드 산출물로 한다(DECISIONS D21). 이 문서는 사용자 재현용이다.
> 모든 명령은 저장소 루트에서 실행한다. 산출물은 `projects/hormuz_korea_legacy/`(gitignore)에 쌓인다.

## 0. 선행

환경 설치는 `PHASE1_ENV_SETUP_WSL2.md`를 따른다. 그다음:

```bash
source .venv/bin/activate
python tools/check_env.py                      # 20 ok / 0 missing, exit 0
pip install -r requirements-engine.txt
```

## 1. 입력 데이터 (네트워크 필요, 처음 1회)

```bash
python tools/fetch_data.py all                 # fonts ne tiles(135장) flags commons bgm
```

- Commons는 요청 간격 15초, 429가 오면 60~90초씩 기다린다. 10분 이상 걸릴 수 있다.
- `bgm`은 네트워크 없이 git 객체에서 BGM mp3를 복원한다(D22). pull 뒤 BGM이 사라졌다면 이 한 줄만 다시 돌린다.
- 실패한 항목이 있으면 `FAILED:` 목록과 함께 exit 1로 끝난다. 다시 실행하면 받은 파일은 건너뛴다.

## 2. 원고 → 음성 → 타임라인

```bash
python tools/legacy_v3_run.py plan --tts edge  # 45문장, edge-tts ko-KR-InJoonNeural -3% -2Hz
```

- **골든 재현은 반드시 edge다.** `.env`에 ElevenLabs 키가 있어도 이 명령은 키를 지우고 실행한다.
- 린트 위반이 있으면 plan3가 exit 1로 멈춘다.

## 3. 지도·인물·국기 자산

```bash
python tools/legacy_v3_run.py prep geo base people flags   # 폰트는 1단계 fetch_data fonts 가 설치(D3)
```

- `base`가 지형 티어 3개를 만든다. 로그의 `land-miss=`가 **`['MV']`(몰디브)뿐**이어야 한다.
- `people`은 rembg 모델(약 170MB)을 처음에 내려받는다.

## 4. 미디어 (사진·영상·컷아웃)

```bash
python tools/legacy_v3_run.py media            # media3(1차) + 2차(rok_iraq, niovi·strikes 5초 클립)
```

## 5. 프리뷰와 골든 대조

```bash
python tools/golden_compare.py                 # 25 앵커 렌더 → MAD 표·히트맵·frames/
python tools/contact_sheet.py sheet            # sheet.jpg (4열)
python tools/contact_sheet.py pairs            # sheet_vs_golden.jpg (골든|렌더)
python tools/contact_sheet.py transitions      # transitions.jpg (타이틀·dip 0.3초 간격 8컷)
```

출력은 `docs/handoff/reports/phase1/`이다. 여기서 먼저 육안으로 본다. 이상하면 전체 렌더 전에 멈춘다.

## 6. 전체 렌더 → 오디오 → 먹싱

```bash
python tools/legacy_v3_run.py render --jobs 4  # 4조각 병렬 → video_noaudio.mp4
python tools/legacy_v3_run.py mix              # mix.f32 (BGM 필요 — 1단계 bgm)
python tools/legacy_v3_run.py mux              # out/final.mp4 (loudnorm −14 LUFS)
python tools/legacy_v3_run.py subs             # out/final.srt, out/description.txt
python tools/legacy_v3_run.py audio            # audio_report.json
```

## 7. 확인

```bash
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 projects/hormuz_korea_legacy/out/final.mp4
```

합격선(19 §6): 총 길이 **4:52 ± 1초**(292.44초 기준), **854×480, 24fps**, 45문장, 린트 통과, `land-miss=['MV']`만, 25컷 육안 동일.

## 8. 회신 양식 (사용자 재현 시)

```
총 길이: ___ 초 / 해상도·fps: ___ / land-miss: ___
golden_compare mean MAD: ___ / 임계 초과 컷: ___
audio_report: I ___ LUFS, 음악-내레이션 차 ___ dB
sheet.jpg 경로: ___
```
