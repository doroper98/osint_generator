---
id: R-0328
from: opus
to: fable
kind: phase_report
responds_to: [D-0622]
phase: "E9"
version: v7.4.0
commit: HEAD
status: done
---

# 환경 지문(D-0622 §3·§5) — 골든 25컷 md5 불일치 대조용

## 1. 판

| 항목 | 값 |
|---|---|
| Python | 3.13.18 |
| pycairo · cairo | 1.29.2 · 1.18.0 (libcairo2 1.18.0-3build1) |
| pango | 1.52.1+ds-1build1 (dpkg) |
| freetype | 2.13.2+dfsg-1ubuntu0.2 (dpkg) |
| harfbuzz | 8.3.0-2build2 (dpkg) |
| ffmpeg | 6.1.1-3ubuntu5 |
| Pillow · numpy | 12.3.0 · 2.5.3 |
| `fc-list \| sort \| md5sum` | 2fefffdbf411fe09800f774fcc4d56cf (글꼴 157) |

## 2. 엔진 글꼴(fc-match → 파일 md5)

| 족 | 파일 | md5 |
|---|---|---|
| IBM Plex Sans KR | /root/.local/share/fonts/osint/IBMPlexSansKR-Regular.ttf | 0d160d831c7febfe37924f958ec80fc5 |
| IBM Plex Sans KR Medium | IBMPlexSansKR-Medium.ttf | cae76922a0bfcc901417be8a30e14c69 |
| IBM Plex Sans KR SemiBold | IBMPlexSansKR-SemiBold.ttf | 6269dfe6ef4dac5887753342ab996302 |
| GmarketSansBold | GmarketSansBold.otf | 77c560c1640c9547d7061cf3b7a2f550 |
| GmarketSansMedium | GmarketSansMedium.otf | 4b2e6bddef0170f49b4fb08afdd08c83 |
| IBM Plex Mono SemiBold | IBMPlexMono-SemiBold.ttf | 4c2f3714b6a45a827fc5a7185876a280 |
| IBM Plex Mono Medium | IBMPlexMono-Medium.ttf | 63c2dc54dd9c1781b0463abe6f862ff2 |
| Noto Serif CJK KR | /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc | 559e7a8e18f74f5e4eae2c0c49d1aad0 |
| Noto Serif CJK KR Bold | NotoSerifCJK-Bold.ttc | e63db212552c76ae681e35f64dde0ad4 |

## 3. 캐시·컨테이너

- 타일 캐시 `data/geo` 있음(236M, tiles·ne). `data/geo_flat` 160K.
- 호르무즈 `projects/hormuz_korea/assets` 기반 PNG 는 11-01 02:16 그대로입니다.
- worker_epoch 4. 커널 uptime 시작 2026-11-02 12:14:51 — R-0321(05:38, 그때 골든 통과) 뒤 컨테이너가 다시 떴습니다.

## 4. 날짜 표지 장치 원칙

- "같은 대상일 때만 날짜 맞춤" 원칙(D-0622 보충, D337)은 아직 시험에 넣지 않았습니다. 날짜 표지 장치(D-0619 ⑤)는 판정 ③ 뒤 원고 수정과 함께 만듭니다. 그 커밋의 시험 설명에 원칙 한 줄을 넣고 R 에 커밋을 적겠습니다.
- 원문: 날짜 맞추기는 그 문장이 카드와 같은 대상을 말할 때만. 다른 대상 문장의 날짜를 바꿔 media-sentence-span 을 통과시키면 UF-173 우회 — 그때는 카드를 줄이거나 옮긴다.
