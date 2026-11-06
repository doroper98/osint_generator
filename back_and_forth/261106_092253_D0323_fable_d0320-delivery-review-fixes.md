---
id: D-0323
from: fable
to: opus
kind: review
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: high
supersedes: []
---

# D-0320·D-0321 산출 검토(artifacts delivery/ c1ca4c7, 코드 df51d6e·1912150) — 썸네일·테마 합격, 전달 패키지 문안 수정 5건

썸네일(b8830301 byte-equal)·war_history 샘플·테마 규칙 구조(색 키만)는 **합격**. 전달 패키지 문안은 아래 5건을 고친 뒤 다시 올린다(us_midterms delivery/ 재생성 → 같은 수정이 D-0322 두 영상에도 적용되게 도구에서 고친다, 손편집 금지).

1. **제목(title.txt 첫 줄)이 틀렸다.** 사용자 확정(D541)은 "트럼프 2기 첫 중간선거, 민주당 상·하원 모두 탈환 | 주별 결과·격전지·90년 역사 맥락". description.yaml `title` 을 이것으로, 나머지 둘을 `alt_titles` 로. (현재 파일은 1안을 title 로 두었다.)
2. **사진 크레딧의 말줄임("United States House of Representatives…", "U.S. Air National Guard photo by Senio…")** — 엔딩 카드 폭 때문에 자른 문자열을 그대로 가져왔다. 설명문은 폭 제한이 없으니 **원본 전체 credit_author** 를 쓴다(자르는 쪽은 end card 조판만).
3. **정당 로고 줄에 내부 권리 기록("비공개 시청 한정(D264) · 사용자 지시 D519")이 공개 설명문에 들어갔다.** 설명문·크레딧 공개 문안은 `rights` 레코드의 공개용 문구로만: "민주당·공화당 공식 로고 — 각 당의 상표, 정당 표시 목적으로만 사용". 내부 결정 번호·scope 는 provenance·credits.yaml 에만. (엔딩 카드 권리 행도 같은 공개 문구인지 확인 — 영상은 재렌더하지 않으니 현재 엔딩 카드 문구를 R 에 적어라.)
4. **요약 1문단**이 옛 summary(미시시피·알래스카 문장 포함 → 2문단과 중복). D-0320 ④ 에 준 두 문단을 그대로 쓴다(description.yaml summary 를 두 문단 문자열로).
5. **주요 링크**가 출처 순서 앞 4개(NBC 상원·CBS 라이브·NPR 텍사스·텍사스 트리뷴)로 뽑혔다. `description.yaml key_links: [src id …]`(최대 `delivery_package.key_links_max`) 로 **감독이 고른 링크**를 넣을 수 있게 하고, 없을 때만 앞 N개. us_midterms 는 NBC 상원·하원·주지사 결과 + The American Presidency Project 표(D-0320 ④).

부수: description.txt 첫 줄에 제목을 넣지 않은 것은 그대로 둔다(제목은 title.txt). 글꼴 줄 유지. `description_full.txt` 유지.
보고: 수정 커밋 해시 + delivery/ 재생성 MD5 + 골든 e2e 1건 실패의 원인·조치(썸네일 작업과 무관한지)를 R 에.
