<!--
tier: 3
last_synced_with: v2.0.1
ssot_for: [phase1-run-log]
depends_on: [docs/handoff/reports/PHASE1_RUNBOOK_WSL2.md]
last_review: 2026-09-27
-->

# Phase 1 골든 재현 — 실행 로그 (Opus 클라우드 컨테이너, D21)

환경: Ubuntu 24.04 컨테이너, Python 3.11.15, 4 vCPU, ffmpeg 6.1.1(apt), pycairo 1.29.1 / cairo 1.18.0.
`tools/check_env.py` = 20 ok / 0 missing. 저장소 커밋 `5308a7f`(산출물 커밋 직전).

## 명령과 결과 (런북 순서)

| 단계 | 명령 | 결과 |
|---|---|---|
| 데이터 | `fetch_data.py fonts ne tiles flags` | 폰트 8, NE 3, 타일 135(W77·G42·K16), flag-icons 13×2 |
| 데이터 | `fetch_data.py commons` (3회 + 원본 재시도 4회) | 메타 8건, 이미지 6, 영상 원본 2. Wikimedia 429(`x-envoy-ratelimited`)로 약 2시간 소요. **트랜스코딩본 미사용** |
| 데이터 | `fetch_data.py bgm` | git 객체 bd37b58 복원, sha1 c0ddb7b3 일치, 931.8초 |
| 원고·음성 | `legacy_v3_run.py plan --tts edge` | **45문장, 총 292.44초**, voice `edge-tts ko-KR-InJoonNeural`, **린트 위반 0** |
| 지도 | `prep geo base flags` | geo 116개국, admin1 12개국, places 3013. **tier W land-miss=['MV'], G·K 없음**. flags 28 |
| 인물 | `prep people` | 인물 4·휘장 1, rembg u2net_human_seg(176MB 첫 다운로드). rights_registry = 참조본과 동일 |
| 미디어 | `legacy_v3_run.py media` | 사진 2·컷아웃 1·클립 2(각 120프레임 480×270@24), strikes 24.6초·niovi 59.421초(참조와 동일) |
| 대조 | `golden_compare.py` | 25 앵커 ±0.01초, **평균 MAD 1.825/255**, 2.0 초과 3컷(참고값) |
| 시트 | `contact_sheet.py sheet / pairs / transitions` | sheet.jpg, sheet_vs_golden.jpg, transitions.jpg(타이틀 + dip 4) |
| 렌더 | `legacy_v3_run.py render --jobs 4` | 7018프레임, 4조각, **86초** |
| 오디오 | `mix` / `mux` | mix peak 0.911(마스터 리미터 전), loudnorm 후 **−14.23 LUFS**, TP −1.43 |
| 자막 | `subs` | final.srt 45문장, description.txt = 골든과 바이트 동일 |
| 측정 | `audio`, `legacy_provenance.py` | audio_report.json, provenance.json |

## 최종 파일

`out/final.mp4`: codec_name=h264 width=854 height=480 r_frame_rate=24/1 codec_name=aac sample_rate=44100 channels=2 r_frame_rate=0/0 duration=292.438005 
크기 30,152,025 B (골든 30.2MB).

## 합격선 대조 (19 §6, D-0005 결정 1)

| 기준 | 결과 |
|---|---|
| 4:52 ± 1초 | 292.438초 ✅ |
| 854×480 @24 | ✅ |
| 45문장 | ✅ |
| 린트 통과 | ✅ |
| land-miss = ['MV']만 | ✅ |
| 25컷 육안 동일 | Fable 검수 대상 (Opus 1차 확인: 위치·구성·색 차이 없음) |

## 경고·특이 사항

1. **Commons 429**: API·upload 모두 Wikimedia 공유 IP 제한. 항목별 캐시·같은 폭 미리 받기로 legacy 코드의 API 재호출을 없앴다(`fetch_data` 커밋).
2. **edge-tts CA**: edge-tts는 `certifi` 번들을 고정 사용해 세션 프록시 CA를 모른다. TLS 검증을 끄지 않고 컨테이너의 certifi 번들에 `/root/.ccr/ca-bundle.crt`를 덧붙였다. 저장소 무변경. WSL2 무관.
3. **골든 SRT 39번**: `00:03:55,1000`(골든 측 반올림 버그). 우리 SRT는 `00:03:56,001`. 나머지 시각 차는 문장 22번부터 최대 6ms(음성 재합성 미세 편차). 텍스트 45줄 동일.
4. **media_registry p8 date**: media3가 Commons에서 새로 읽어 "Taken on 25 September 2025"(참조본은 "Taken on 25 Septembe"로 잘림). 화면 표기에는 쓰이지 않는 필드.
5. **audio_report music_below_narration 12.7dB**: Phase 8 목표 14~18dB 밖. v3 음악 이득 0.47은 사용자 합격 값(라운드 3 "배경음악 너무 작다")이라 바꾸지 않았다. 측정법은 근사(효과음이 음악 스템에 포함).
6. **provenance badges 8**: 19 부록 B·test_provenance_e2e 기대값은 9. 실제 연출층 EV의 badge 이벤트는 8(person 3·flag 4·emblem 1). 패널 안에서 그리는 뱃지(P_refusal의 트럼프·국기 등)는 badge 이벤트가 아니다.
7. **mix.f32(103MB)**: GitHub 파일 100MB 제한 → 영상 브랜치에는 24비트 FLAC(`mix.flac`, 44.7MB)로 올렸다.
