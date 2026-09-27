---
id: R-0007
from: opus
to: fable
kind: progress
responds_to: [D-0008]
phase: "1"
version: v2.0.1
commit: HEAD
status: in_progress
supersedes: [R-0006]
---

# R-0006 철회 — 원본 영상 수신 완료, 골든 대조 1차 결과, 전체 렌더 진행 중

## 1. R-0006(결정 요청)은 더 이상 필요 없다

10분 간격 원본 재시도 4회째에 두 원본을 받았다. **트랜스코딩본은 쓰지 않았다.**

| 파일 | 크기 | 길이(ffprobe) | 참조 media_registry |
|---|---|---|---|
| strikes.webm | 5.85MB | 24.600초 | 24.6 |
| niovi.webm | 2.51MB | 59.421초 | 59.421 |

R-0006에 답하지 않아도 된다(이 파일의 `supersedes`). 이미 결정을 썼다면 참고로만 남긴다.

## 2. D-0008 확인

- provenance: `tools/legacy_provenance.py`(render3의 CAM·EV 실측 집계, `engine: "legacy_v3"`, `prompts: {}`, `drops: []`) 추가 완료.
- SRT 39번 골든 측 오류는 phase_report 자막 diff에 명시한다. CA 번들 조치는 run_log에만 남긴다.

## 3. 자산 단계 결과

| 단계 | 결과 |
|---|---|
| prep people | 인물 4(trump·khamenei=라이브러리, lee·roh=Commons+rembg), 휘장 navcent. `rights_registry.json` = 참조본과 동일 |
| media | 사진 2(hormuz_transit·rok_iraq 720×450), 컷아웃 p8, 클립 2(각 120프레임 480×270@24). 레지스트리 = media3 3건 + 참조 2건 병합 |

## 4. 골든 25컷 대조 (1차, `docs/handoff/reports/phase1/golden_compare.json`)

- 앵커 시각: 25개 전부 골든과 **±0.01초** 이내(음성 재합성이 결정적).
- **평균 MAD 1.82/255.** 골든 PNG는 mp4(H.264) 추출본이라 무손실 렌더와 원래 1.5 안팎의 차이가 난다.
- 2.0 초과 3컷: `timeline_4`(3.10, 영상 클립 프레임 압축 질감), `past_1`(2.97, 자료사진 질감), `now_3`(2.93, 지도 라벨 글자 가장자리).
  히트맵으로 확인했고 위치·구성·색 차이는 없다. 판정 임계는 Phase 2(D21)이므로 참고값이다.
- 전환 시트: 타이틀 뒤 dip(under)에서 타이틀이 유지된다(라운드 4 수정 재현). dip 2·3·4도 1초 암전 후 컷.

## 5. 다음

전체 렌더(4조각 병렬) 진행 중 → mix → mux → subs → audio_report → provenance → run_log →
산출물 커밋 + 영상 orphan `artifacts/phase1-v2.0.1` → `phase_report`.
