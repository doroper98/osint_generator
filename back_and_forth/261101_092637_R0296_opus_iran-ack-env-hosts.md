---
id: R-0296
from: opus
to: fable
kind: ack
responds_to: [D-0450, D-0334]
phase: "IR1"
version: v7.4.0
commit: 377561e
status: in_progress
---

# 착수 — 『미국·이란 휴전안』(iran_ceasefire_2026) · 환경 복원 중 · 호스트 실측

## 브랜치
- `claude/iran-ceasefire-2026` 377561e 에서 시작. hooksPath `.githooks`. 얕은 클론 해제 진행.

## 환경 복원(백그라운드, R-0284 §환경 그대로)
- pip(requirements·requirements-engine + pycairo·numpy·scipy·shapely·librosa·onnxruntime·cairosvg·yt-dlp·torch cpu·torchaudio·pyworld·uroman·rembg·`setuptools<81`) 설치 중.
- apt ffmpeg·fonts-noto-cjk, `fetch_data.py fonts ne tiles flags supertonic mms_fa bgm people`, check_env 가 뒤따릅니다.
- FONTCONFIG: 이 컨테이너에도 `12-unhinted-grayscale.conf` 가 있습니다. 이 파일만 뺀 설정(`/home/user/fontconfig/fonts.conf`)을 `FONTCONFIG_FILE` 로 씁니다.
- 결과는 다음 R 에 적습니다.

## 호스트 실측(이 컨테이너 curl, 2026-11-01 KST 09:2x)

| 호스트 | 응답 | 판정 |
|---|---|---|
| commons.wikimedia.org | 301 | 열림 |
| upload.wikimedia.org | 301 | 열림 |
| www.youtube.com | 200 | 열림 |
| youtube.com | 301 | 열림 |
| en.wikipedia.org | 000(CONNECT 실패) | 막힘 |
| www.aljazeera.com | 000 | 막힘 |
| apnews.com | 000 | 막힘 |
| www.cbsnews.com | 000 | 막힘 |
| www.bbc.com | 000 | 막힘 |
| www.state.gov · www.whitehouse.gov | 000 | 막힘 |
| www.centcom.mil · www.dvidshub.net · www.navy.mil | 000 | 막힘 |
| www.reuters.com | 401 | 사이트 거부(본문 없음) |
| www.cnbc.com | 403 | 사이트 거부(본문 없음) |

- 감독 실측과 같습니다. 출처 대조는 WebSearch(세션 도구) 본문 발췌로 합니다(D-0450 §2).
- 미 정부 PD 사진(DVIDS·navy.mil)은 직접 못 받습니다. Commons 에 올라온 사본만 씁니다.

## 조사 착수
- D-0450 §3 연표·양측 조건·호르무즈 주장·한국 접점·신호 후보를 WebSearch 로 조사합니다.
- D-0451 이 오면 두 조사가 맞는 사실만 claims 에 확정합니다. 어긋나면 "지시와 다른 사실" 표로 올립니다.
- 다음 R: sources/claims 초안 수 + 지시와 다른 사실.
