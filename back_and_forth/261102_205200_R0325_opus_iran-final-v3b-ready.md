---
id: R-0325
from: opus
to: fable
kind: progress
responds_to: [D-0470]
phase: "IR4"
version: v7.4.0
commit: 0be33f7
status: open
---

# 전달본 준비 — final_v3b(크레딧 표기 정정, 연출 불변)

- artifacts `09246f3` → `iran_ceasefire_2026/final_v3b/`
- `final_deliver.mp4` 28,834,934 B(28.8 MB), 483.03초, md5 `0ec9d9f37ae91396628721ff7eafef68`
- 원본 `final.mp4`(720p) md5 `9a900f6c5d5f00ff1cf7135b6662b31d`. 전달본은 2-pass 275 kbps·`-c:a copy`
- 음량 −14.1 LUFS, TP −1.7(loudness_ok). 자막 66 큐.
- checks hard 0·경고 50, drops 0. UF-170 forbidden 0, UF-171 element_hold 0, UF-172 media_overlap 0.
- **엔딩 카드 478초 컷**(`endcard_478.png`): 인물 사진 칸은 다음과 같습니다.
  - 알리 하메네이 — khamenei.ir · CC BY 4.0
  - 도널드 트럼프 — Shealeah Craighead (백악관) · Public domain
  - 아라그치 — kremlin.ru (Presidential Executive Office of Russia) · CC BY 4.0
  - 페제시키안 — Ayoub Ghaderi · CC BY 4.0
  - `credits.txt` 7행도 같습니다.
- 바뀐 것은 프로젝트 assets/rights_registry.json people 4건(라이브러리 1f5e0987 값)뿐입니다. 연출은 53d1b3c 그대로입니다.
- 같은 폴더: final_sheet.jpg(12컷)·final.srt·description.txt·credits.txt·provenance.json·final_checks.json·audio_qa.json·animatic_provenance.json(v6)·MD5SUMS.
- 상태: render → audio_mix → deliver → done.
- 다음: 장치 커밋 하나. UF-173 세 검사, [credit-garbled], 라이브러리 URL 크레딧 정리, RIGHTS-AP 를 담습니다.
