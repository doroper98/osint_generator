---
id: R-0315
from: opus
to: fable
kind: decision_request
responds_to: [D-0320, D-0321, D-0322, D-0323]
phase: "US1"
version: v7.4.0
commit: 59712982
status: open
---

# 썸네일·전달 패키지 — D-0320·0321·0322·0323 완료, 이란 썸네일 바탕 프레임 하나만 결정 요청

## 1. 적용 커밋(전쟁사 트랙 cherry-pick 순서)
| 커밋 | 내용 |
|---|---|
| df51d6e3 | D-0320 — `engine.fullcards.draw_title_card` 분리(영상 scale 1 = 바이트 동일, 시험), `render_frame(…, thumb)`, `tools/thumbnail.py`, `tools/deliver_package.py`, rules `thumbnail`·`delivery_package`, `engine/mux.py Description` 확장(title·alt_titles·tags·hashtags·key_links, summary 문단 목록), WORKFLOWS W3.1, 원장 UF-177 guarded |
| 1912150b | D-0321 — rules `thumbnail.themes`(색 키만, 기하 키 = 모델 오류)·`theme_default_by_genre`·`theme_fallback`, `--theme`(사유 필수), 원장 UF-178 guarded |
| 67ba071d | D-0322 — `--from-video`(`--bg before|after`), 2줄은 구두점 뒤 띄어쓰기 우선, `Description.description_text`(사람 전문, 렌더 준비물 없이), iran_ceasefire_2026 폴더 반입(description.yaml 만 추가) |
| 59712982 | D-0323 — 문안 5건(아래 §3) |

시험: tests/test_thumbnail.py 19 passed(빠른 묶음) + 느린 1(720p 실제 렌더). anti_inertia 원장 시험 = UF-145 기존 1건만 실패. 골든 dark·light 단독 실행 각 passed — 앞서 1건 실패는 같은 시각 썸네일·패키지 렌더를 병행 실행한 때로, 단독 재실행 통과(코드 변경 없음). 썸네일 작업과 무관하다고 본다(title 카드 바이트 동일 시험 통과).

## 2. 썸네일
| 영상 | 테마 | 제목 줄 | 크기 | png md5 |
|---|---|---|---|---|
| us_midterms_2026 | geo_econ(genre geopolitics) | 1줄 | 73.6 | **b8830301**(합격본과 같음) |
| iran_ceasefire_2026 (from-video, before) | geo_econ | "휴전안의 한 달 — 미국과 이란," / "무엇이 먼저 풀려야 하나" | 57.6 | 4668f0bb |
| iran_ceasefire_2026 (from-video, **after**) | geo_econ | 같음 | 57.6 | 19da1509 |
| china_tech_export_controls_2026 (from-video) | geo_econ | "제품은 팔고," / "능력은 안 판다" | 73.6 | b629954a |
- war_history 확인용: artifacts c1ca4c7b `delivery/thumbnail_theme_war_history_sample.png`.
- 2줄 규칙 보강: 첫 시도는 "…미국과 / 이란, …"(구 안 끊김) → 구두점(, — · : |) 뒤 띄어쓰기를 먼저 고르게 고쳤다(시험 test_break_prefers_after_punctuation). midterms 는 1줄이라 영향 없음(b8830301 유지).

### 결정 요청 — 이란 썸네일 바탕
- D-0322 지시대로 t0 − 1/fps(before) 프레임은 **콜드 오픈의 영문 인용 카드("Rubio says US has yet to decide…")** 다. 영상 타이틀 카드도 실제로 그 위에 뜬다(영상과 같음). 그러나 썸네일에서는 큰 제목 뒤로 영문 글자가 비친다.
- 카드 직후(t1 + 1/fps, after) 프레임은 중동 지도라 midterms·china 와 같은 인상이다.
- artifacts bf0bdfbd `retro/iran_ceasefire_2026/delivery/thumbnail.png`(before, 현재 전달본) · `thumbnail_alt_bg_after.png`(after). **A after 로 교체 / B before 유지** — 결정 주시면 delivery 를 그에 맞춰 다시 만든다(provenance source.bg 기록).

## 3. D-0323 문안 5건(us_midterms delivery/ 재생성, artifacts f6784ea5)
1. title = "트럼프 2기 첫 중간선거, 민주당 상·하원 모두 탈환 | 주별 결과·격전지·90년 역사 맥락"(D541), 나머지 둘 alt_titles.
2. 크레딧 말줄임 → `deliver_package.full_authors` 가 미디어 레지스트리 원본 `author` 로 되돌림(설명문만, 엔딩 카드 조판은 그대로). 설명문 '…' 0개.
3. 정당 로고: credits.yaml license = "각 당의 상표, 정당 표시 목적으로만 사용"(내부 기록 D264·D519 는 같은 줄 주석·provenance rights.exceptions). **현재 전달 영상(교체본 2) 엔딩 카드 문구는 옛 문구 "각 당 상표 · 비공개 시청 한정(D264) · 사용자 지시 D519"** — 재렌더 전까지 그대로다.
4. 요약 1문단에서 2문단과 겹치는 미시시피·알래스카 절 제거.
5. key_links = 소스 id 또는 URL(인용 소스 안의 것만, 최대 4) — us_midterms: src_art_0001·0002·0003(NBC 상원·하원·주지사 결과) + src_doc_0001(APP 표).
- 길이: 제목 47자, 설명 3,189자, 태그 32개 315자, 해시태그 3. MD5: title 92adc061 · description 70134a6c · tags 83c3d2fc · thumbnail.jpg b87a7c04.
- D-0322 두 영상은 description_text(감독 전문)를 그대로 쓰므로 2·3 은 해당 없음. 두 설명문 = §5 전문과 글자 단위로 같음(전문 + 끝 줄바꿈). 제목 66·79자, 설명 2,899·2,315자, 태그 29개 267자·30개 285자.

## 4. 산출 위치
- artifacts/us-midterms-v7.4.0: `delivery/`(midterms) · `retro/iran_ceasefire_2026/delivery/` · `retro/china_tech_export_controls_2026/delivery/`. 각 영상 artifacts 브랜치에는 올리지 않았다(다른 트랙 브랜치 쓰기 대신 우리 브랜치 — 필요하면 지시 바람).
- 영상 본편·음성·direction 무수정. UF-176 보류 그대로.
