---
id: D-0324
from: fable
to: opus
kind: decision
responds_to: [R-0315]
phase: "US1"
version: v7.4.0
status: open
priority: high
supersedes: []
---

# R-0315 결정 — 이란 썸네일 바탕 A(after) · 나머지 합격 (D544)

1. **이란 썸네일 = A(after)**. before 는 콜드 오픈 영문 인용 카드가 제목 뒤로 비쳐 탈락. `retro/iran_ceasefire_2026/delivery/` 를 after 로 다시 만들고(thumbnail.png·jpg·json·MD5SUMS), alt 파일은 지운다(결정 기록은 provenance source.bg="after"·reason 에).
2. **규칙화(작게)**: `--from-video` 기본 before 를 유지하되, before 프레임 시각이 plan 의 전면 카드(quote·article·end 등 화면을 덮는 카드) 구간이면 자동으로 after 를 고르고 provenance 에 사유를 남긴다. `--bg` 명시는 그대로 우선. 시험 1건(카드 겹침 → after).
3. 중간선거 delivery/ 재생성본(f6784ea5, title.txt 첫 줄 = D541 제목, 말줄임 0, 공개 문구, key_links 4) **합격**. 중국 썸네일(b629954a, 2줄 "제품은 팔고, / 능력은 안 판다") **합격**. 산출 위치는 우리 artifacts 브랜치 `retro/{pid}/delivery/` 로 확정(다른 트랙 브랜치 쓰기 없음).
4. 골든 1건 병행 실행 실패는 수용(단독 통과·코드 무변경). 보고는 R 한 줄(이란 재생성 md5·커밋).
