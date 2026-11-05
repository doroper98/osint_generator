---
id: D-0320
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 지시 UF-177 / D540 — 썸네일 도구 + 전달 패키지 규칙(제목·설명·태그·썸네일)

## 0. 사용자 원문(2026-11-06)
> "썸네일도 만들어. 썸네일은 제목 페이지에서 제목을 좀 더 키우고(필요하다면 어색하지ㅜ않은 줄바꿈 가능) 주위에 금빛 얇은 선 테두리를 최외곽에서 조금 떨어진 곳에 고급지게 그려서 만들어. 이건 영상 줄때 매번 만들어서 주는 규칙으로 하자. 제목, 설명, 태그, 썸네일"

D-0319 보류(UF-176 '주가' 수정·교체본 3)는 그대로다 — **영상 본편은 건드리지 않는다.** 이 지시는 전달 패키지 도구·규칙만이다.

## 1. 썸네일 도구 `tools/thumbnail.py` (P1 독립 CLI, 수치는 규칙에서만 P3)
- 입력: `projects/{pid}` (out/plan·geo 준비물 그대로). 출력: `out/thumbnail.png`(1280×720) + `out/thumbnail.jpg`(품질 92, 2 MB 이하) + provenance `thumbnail` 항목(P5: 제목 크기·줄 수·테두리 수치·원본 프레임 t).
- 구성: **타이틀 카드와 같은 장면**(`engine.fullcards` 의 title 카드 — 카드 중간 시각 t = c.t0 + dur/2 의 바탕 장면 + 같은 어둡기 그라데이션, 모든 글자 alpha 1). 새로 그리지 말고 `draw_fullcards` 의 title 분기를 **함수로 분리**(`draw_title_card(ctx, plan, a, lt, title_scale, border)`) 해서 렌더와 썸네일이 같은 코드를 쓴다(관성 방지 — 썸네일만 다른 모양 금지).
- 제목 키움: `rules thumbnail.title_scale` (초안 1.6 → 46×1.6 ≈ 74 설계px, 720p 에서 ≈110px). 폭이 `W × max_w_ratio` 를 넘으면 **띄어쓰기 중 가운데에 가장 가까운 곳에서 2줄**(어절 안에서 자르지 않는다), 2줄도 넘으면 title_fit_size 방식으로 줄인다. 2줄 줄간격 `thumbnail.title_line_gap`(초안 1.08em). 제목·금선·부제·날짜 묶음의 세로 중심은 원래 타이틀 카드와 같은 곳(설계 y≈262)에 둔다 — 제목이 커진 만큼 묶음을 위아래로 균등하게 벌린다.
- 금빛 테두리: `rules thumbnail.border {inset: 22, width: 1.2, radius: 2, alpha: 0.9, glow_width: 4, glow_alpha: 0.14}` (설계px, 색 `C["gold"]`). 최외곽에서 inset 만큼 안쪽에 얇은 한 줄 + 아주 옅은 바깥 번짐(금속 느낌). 두 줄·장식 모서리·그림자 과장 금지(고급 = 절제).
- 금지: 썸네일 전용 문구·화살표·얼굴 확대·AI 생성 그림. 타이틀 카드 구성 밖의 요소를 넣지 않는다(C0 되돌리면 안 되는 것과 같은 무게).

## 2. 전달 패키지 `tools/deliver_package.py` + 규칙 `delivery_package:`
- `projects/{pid}/publish.yaml` (schema `schemas/publish_models.py`, Pydantic v2): `title`(≤100자), `alt_titles[]`, `description`(≤5,000자, 챕터 줄 포함), `tags[]`(쉼표 연결 ≤500자), `hashtags[]`(3개). 설명 초안은 도구가 만든다(제목·부제·요약 문단은 publish.yaml 에서, 챕터는 out/final.srt 장면 첫 문장 −1초, 출처·사진·음악·지도 줄은 기존 credits 자료에서 — 실제로 쓰인 자산만, D-0314 교훈). 사람이 publish.yaml 을 고치면 그대로 쓴다.
- 산출: `out/delivery/{title.txt, description.txt, tags.txt, thumbnail.jpg}` + `out/delivery/MD5SUMS`. 네 항목 중 하나라도 없거나 한도를 넘으면 **오류**(조용한 생략 금지 P6). provenance `delivery_package` 에 네 항목과 한도 검사 결과.
- 이번 영상 값(감독이 이미 사용자에게 준 것 — 그대로 publish.yaml 에): 제목 "뒤집힌 일곱 자리 — 2026 미국 중간선거, 주별 결과와 격전지", 설명·태그·해시태그는 감독 스크래치 파일을 R 로 요청하면 보내겠다 — 우선 `out/description.txt`(7,383자) 를 5,000자 아래로 줄인 감독본이 있으니 그 구조(요약 2문단·챕터 10줄·자료·주요 링크 4·인물 사진·자료사진·기사 인용·정당 로고·지도·Music·표기·해시태그 3)를 따른다.

## 3. 장치(UF-177, C12)
- `tests/anti_inertia/test_user_feedback_guards.py` 에 UF-177 → `tools/deliver_package.py` 검사 + `tests/test_thumbnail.py`(제목 폭 초과 → 2줄, 2줄 초과 → 줄임, 테두리 수치가 규칙에서 읽힘, 출력 크기 1280×720, provenance 기록). 원장 UF-177 guards 연결·status guarded.
- `WORKFLOWS.md` 전달 단계에 "final_deliver + delivery 패키지 네 항목" 명시. `docs/handoff/19`·`DECISIONS` 는 감독이 적었다.

## 4. 절차·보고
- 순서: 규칙 블록 → 도구 → 테스트 → `python tools/thumbnail.py projects/us_midterms_2026` → `python tools/deliver_package.py projects/us_midterms_2026` → artifacts `delivery/`(thumbnail.png·jpg, 네 txt, MD5SUMS) → R(phase_report: 썸네일 png 첨부 경로·수치·테스트 수) + send_message.
- 영상 본편·음성·direction 은 수정하지 않는다. 커밋 prefix v7.4.0:, 모델명 기재 금지, PR 금지.

## 5. 부칙(감독 실측 추가) — 기존 설명문 경로를 확장한다, 새 경로 금지(P2)
- 설명문은 이미 `projects/{pid}/description.yaml`(headline·summary·chapters[at=장면 id|TITLE, label]) → `engine/mux.py` 가 `out/description.txt` 를 만든다. **publish.yaml 을 따로 만들지 말고 `description.yaml` 에 `title`·`alt_titles`·`tags`·`hashtags` 를 추가**하고(스키마는 그 파일의 Pydantic 모델 확장), `deliver_package.py` 는 mux 의 설명문 생성 함수를 호출한다.
- 현재 `description.txt` 가 7,383자(출처 원문 52줄 전부)라 유튜브 한도 5,000자를 넘는다 → 규칙 `delivery_package.description_max_chars: 5000`. 출처 줄은 **매체명(날짜) 요약 + 주요 링크 N개(`delivery_package.key_links_max: 4`)** 로 줄이고, 전체 링크 목록은 `out/description_full.txt` 로 따로 남긴다(기록용). 사진 줄은 provenance `assets.images_used` 에 실제로 있는 것만(D-0314 교훈: 못 받은 9장 제외).
- 챕터: `description.yaml chapters` 에 basics 장(중간선거란)이 빠져 있다 — 장면마다 한 줄이 기본값(장면 첫 문장 −1초, 장면 라벨은 description.yaml 에서).
