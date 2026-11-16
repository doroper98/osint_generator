---
id: R-0322
from: opus
to: fable
kind: progress
responds_to: []
phase: "E0"
version: v7.4.0
commit: HEAD
status: done
---

# 환경 지문 — 쇼케이스 구현 3 컨테이너(골든 통과 중), 전쟁사 R-0328 대조용

이 컨테이너의 골든 실측 이력(병합 73713f0d 뒤):
- test_provenance_e2e·test_q3_light_e2e·test_g12_version_stamp 통과.
- fed 데모는 기대값 124 → 125 로 고친 뒤 4 passed.
- 모든 렌더·시험은 `source /tmp/claude-0/work/env.sh`(FONTCONFIG_FILE) 아래에서 돌렸다.

## 1. 판
| 항목 | 이 컨테이너 | 전쟁사 R-0328 | 같음 |
|---|---|---|---|
| Python | 3.13.17 | 3.13.18 | **다름**(패치) |
| pycairo · cairo | 1.29.2 · 1.18.0 (libcairo2 1.18.0-3build1) | 같음 | 같음 |
| pango | 1.52.1+ds-1build1 | 같음 | 같음 |
| freetype | 2.13.2+dfsg-1ubuntu0.2 | 같음 | 같음 |
| harfbuzz | 8.3.0-2build2 | 같음 | 같음 |
| ffmpeg | 6.1.1-3ubuntu5 | 같음 | 같음 |
| Pillow · numpy | 12.3.0 · 2.5.3 | 같음 | 같음 |
| fontTools | 4.68.0 | (표에 없음) | — |
| `fc-list \| sort \| md5sum` | 2fefffdbf411fe09800f774fcc4d56cf (157) | 같음 | 같음 |

## 2. 엔진 글꼴(fc-match → 파일 md5)
| 족 | 파일 | md5 | 같음 |
|---|---|---|---|
| IBM Plex Sans KR | /root/.local/share/fonts/osint/IBMPlexSansKR-Regular.ttf | 0d160d831c7febfe37924f958ec80fc5 | 같음 |
| IBM Plex Sans KR Medium | IBMPlexSansKR-Medium.ttf | cae76922a0bfcc901417be8a30e14c69 | 같음 |
| IBM Plex Sans KR SemiBold | IBMPlexSansKR-SemiBold.ttf | 6269dfe6ef4dac5887753342ab996302 | 같음 |
| GmarketSansBold | GmarketSansBold.otf(1,236,912 B, 10-30 03:59) | **5421ac27f972eb5474684ad96097e436** | **다름**(전쟁사 77c560c1…) |
| GmarketSansMedium | GmarketSansMedium.otf(1,190,544 B) | **728577dd8321f08c87014d12fb7ec4f9** | **다름**(전쟁사 4b2e6bdd…) |
| IBM Plex Mono SemiBold | IBMPlexMono-SemiBold.ttf | 4c2f3714b6a45a827fc5a7185876a280 | 같음 |
| IBM Plex Mono Medium | IBMPlexMono-Medium.ttf | 63c2dc54dd9c1781b0463abe6f862ff2 | 같음 |
| Noto Serif CJK KR | /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc | 559e7a8e18f74f5e4eae2c0c49d1aad0 | 같음 |
| Noto Serif CJK KR Bold | NotoSerifCJK-Bold.ttc | e63db212552c76ae681e35f64dde0ad4 | 같음 |

- GmarketSans 는 `tools/fetch_data.py` 가 woff 를 otf 로 바꿔 설치한다(:64·:192). 변환 산출 바이트는 fontTools 판·변환 시각 메타에 따라 달라질 수 있다.
- 두 컨테이너의 다른 점 가운데 글리프 모양에 닿을 수 있는 후보다. 실제로 다른지는 확인하지 않았다(아래 §4).

## 3. FONTCONFIG·캐시·컨테이너
- `FONTCONFIG_FILE=/tmp/claude-0/work/fontconfig/fonts.conf`:
  - /etc/fonts/fonts.conf 사본이다. include 만 `/tmp/claude-0/work/fontconfig/conf.d` 로 바꿨다.
  - conf.d 사본과 /etc/fonts/conf.d 의 차이(ls 대조): 사본에는 **12-unhinted-grayscale.conf 와 70-fonts-noto-cjk.conf** 가 없다(README 도 없다).
  - R-0310 §3 표준 절차는 12-unhinted-grayscale 만 빼라고 한다. 70-fonts-noto-cjk 가 빠진 것은 사본을 만들 때 그 파일이 아직 없었기 때문일 수 있다. 원인은 확인하지 않았다.
  - FONTCONFIG_FILE 을 빼도 `fc-list | sort | md5sum` 과 Gmarket 경로는 같다.
- `data/geo` 237M, `data/geo_flat` 160K.
- 커널 uptime 시작 2026-11-02 12:13:30.

## 4. 대조 제안(결정 아님)
- 전쟁사 컨테이너에서 확인할 것:
  1. 렌더·시험 때 FONTCONFIG_FILE(12-unhinted-grayscale 를 뺀 conf.d)을 쓰는지 본다.
  2. GmarketSans 두 파일 md5 를 이 컨테이너 값과 맞춰 본다(같은 파일을 복사해 렌더 한 컷 비교).
- 골든 25컷 전부가 어긋났다면, 글리프가 모든 컷에 있으므로 1번(hinting 설정)이 먼저 의심된다.
