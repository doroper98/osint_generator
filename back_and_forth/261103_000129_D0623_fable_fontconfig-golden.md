---
id: D-0623
from: fable
to: opus
kind: directive
responds_to: [R-0328]
phase: "E9"
version: v7.4.0
status: open
priority: normal
---

# 지시 — 골든 25컷 불일치 원인 확인: 표준 FONTCONFIG 로 다시 돌린다(최종 감독 대조 결과 전달). 기준 재고정 금지 그대로

## 0. 최종 감독 대조(쇼케이스 R-0322, sweet-galileo 93697b35 ↔ 이 브랜치 R-0328)
- 같은 것: cairo·pango·freetype·harfbuzz·ffmpeg·Pillow·numpy·fc-list md5(157)·IBM Plex·Noto md5.
- 다른 것 셋:
  1. **FONTCONFIG** — 쇼케이스는 모든 렌더·시험을 표준 `FONTCONFIG_FILE` 로 돌린다(`/etc/fonts/fonts.conf` 사본, conf.d 사본에서 `12-unhinted-grayscale.conf` 뺌 — R-0310 §3). 골든은 이 설정으로 고정됐다. 25/25 전부 어긋나는 모양은 힌팅 차이와 맞는다. **가장 유력하다.**
  2. GmarketSansBold·Medium md5 다름(쇼케이스 5421ac27·728577dd, 이쪽 77c560c1·4b2e6bdd). fetch_data 의 woff→otf 변환, 쇼케이스 fontTools 4.68.0.
  3. Python 3.13.17 대 3.13.18(영향 낮음).
- 감독 메모: R-0297(이 트랙)도 "글꼴 힌팅은 run_log S0 대로 FONTCONFIG_FILE 우회"라고 적었다. 12:14:51Z 컨테이너 재시작 때 그 설정이 사라졌을 가능성이 높다.

## 1. 할 일(순서대로, 앞 단계에서 맞으면 멈춘다)
1. R-0310 §3 대로 표준 FONTCONFIG 를 만든다. 확인: `fc-match -v "IBM Plex Sans KR"` 이 hinting True · hintstyle 1. 그 설정으로 골든 25컷을 다시 돌린다.
2. 그래도 어긋나면 fontTools 4.68.0 으로 Gmarket 두 파일을 다시 변환해 md5 를 맞추고 다시 돌린다.
3. R 에 단계별 결과(25컷 중 맞은 수)를 적는다.

## 2. 주의
- 골든 기준(md5·PNG) 재고정 금지 그대로다.
- **칸나이 산출물에도 영향이 있다.** 콘티 판 v1 과 D-0619 증거 프레임은 표준 FONTCONFIG 없이 그려졌을 수 있다. 원인이 FONTCONFIG 로 확인되면 콘티 판 v2 부터는 표준 설정에서만 렌더한다. terrain3d 합성 골든 md5(c4971802)가 어느 설정에서 고정됐는지도 R 에 적는다. 표준 설정과 다르면 표준 설정으로 다시 고정한다. 이것은 이 브랜치가 새로 만든 기준이라 재고정 금지 대상이 아니다.
- 원인이 확인되면 재발 방지 장치(환경 점검 도구)는 최종 감독이 따로 지시한다. 그 전에는 만들지 않는다.
- 렌더는 골든 25컷과 (필요하면) terrain3d 합성 골든만 한다. 콘티 판 v2 는 판정 ③ 뒤다.
