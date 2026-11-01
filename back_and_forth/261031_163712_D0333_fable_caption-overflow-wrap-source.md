---
id: D-0333
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — 미디어 캡션 넘침: 캡션 줄 ellipsis, 출처 줄 wrap(권리 표기는 자르지 않는다). [caption-overflow] hard

- 실측(세션 3): 넘침 6건 모두 출처 줄(geo strikes_file 319/280px, econ fed_* 다섯 자리 229~308/216px), 캡션 줄 0건. 골든 두 편 0건. 잘리는 쪽은 줄 끝 = 라이선스 이름.
- 결정 **(3) 혼합** — 캡션 줄 `ellipsis`, 출처 줄 `wrap`(두 줄, 바 높이 +1줄 ≈12px). 권리 표기(C9)는 화면에서 자르지 않는다. 바가 커지면 media_box 가 따라가 겹침 검사가 같이 본다. 두 줄로도 넘치면 hard.
- 규칙 키 `layout_480p.media_caption.overflow {caption: ellipsis, source: wrap}`(감독 제안 값, 사용자 합격 값 아님) + checks `[caption-overflow]` hard, 모든 미디어 슬롯. 골든 면제 없음. 대표 2컷(strikes_file·fed_eccles_ext)을 R 에.
