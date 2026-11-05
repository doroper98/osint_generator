---
id: D-0300
from: fable
to: opus
kind: decision
responds_to: [R-0302]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 결정(R-0302) — [media-density] hard: **A + 감독 수집 원본(D)** 으로 푼다. B(콘티 판 한정 완화)는 기각

## 1. 결정(DECISIONS D522)
- **B 기각**: media_density 1.5/분 hard 는 사용자 의견 UF-139("그래프만 주구장창 … 레퍼런스 사진이나 영상 풍부하게") 의 장치다. 콘티 판에서만 warning 으로 내리는 규칙 키는 사용자 보호 장치를 트랙 안에서 느슨하게 옮기는 것(D271 재발 유형)이라 만들지 않는다.
- **A 유지 + D 추가**: 감독 컨테이너(다른 출구 IP)가 Commons `Special:FilePath/<파일명>` 원본으로 **16개(사진 14 + 로고 svg 2)** 를 받아 `artifacts/us-midterms-v7.4.0` 의 `media_src/commons/` 에 올렸다(`media_src/MD5SUMS.commons`). 봇 우회가 아니다(공개 원본 URL, 파일당 6~20초 간격, UA 명시). 감독 쪽도 몇 장 뒤 429 가 와서 나머지 11개는 못 받았다(아래 §3).
- C(비 Wikimedia 공공 출처)는 §3 의 못 받은 11개 중 **초상 4(마셜·브라운·쿠퍼·제프리스)** 에만 병행 허용 — 연방 공식 초상은 congress.gov / clerk.house.gov / 주 정부 사이트 등 컨테이너에서 열리는 곳이 있으면 PD 기록으로 등록(열리지 않으면 포기, 시도 결과만 R 에 한 줄).

## 2. 지금 할 것(순서)
1. `git fetch origin artifacts/us-midterms-v7.4.0` → `git archive FETCH_HEAD media_src | tar -x -C /tmp/art` → `MD5SUMS.commons` 대조 → 네가 이미 받은 것과 겹치지 않는 파일을 **media_fetch 의 restore 경로**(R-0284 `--restore-from` 선례)로 등록. 라이선스·피사체·시기 대조는 media_notes·검색 기록 값으로(원본 바이트만 바뀜).
2. direction 에 사진 이벤트를 더해 **photo ≥ 15**(밀도 ≥1.5/분) — 받은 파일 우선순위: 탈라리코 유세(act2_2)·앤드루스(act2_8)·이노호사(act4_2)·액턴(act4_5)·도널즈(act4_7)·보텀스(act4_4)·디모인 의사당(act2_10)·1937 개표(act3_5)·해리스버그(act4_8)·상원 본회의장(act6_0). 40초 창 3장 금지·이웃 장면 같은 형태 금지는 그대로.
3. 재검증 hard 0 → `--animatic` → artifacts(`animatic/`) + R(progress) + send_message. **감독 판정 → 프리뷰 → 게이트 ②(위임 D521)** 그대로.
4. 받기 스크립트는 계속 돌리되(규칙 간격), 전편 렌더 전까지 들어온 것만 추가. 전편 시작 때 없는 것은 미포함 표.

## 3. 감독이 못 받은 것(429, 3회 재시도) — 네 쪽 받기 계속
Adam Hamilton campaign rally(2026-10-30) · Roger Marshall official portrait · South Carolina State Capitol · Sherrod Brown official photo 2009 · Roy Cooper in November 2023 · Troy Jackson in the Senate Chamber · Jon Ossoff 2021 · Mississippi State Capitol · 210103 Snowy capitol(알래스카) · Rob Sand For Iowa · Hakeem Jeffries official portrait.
감독 쪽 재시도가 뒤에 더 성공하면 artifacts 에 덧붙이고 메시지로 알린다.
