<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-source-intake]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 18. 소스 인테이크 — 기사 · X 게시물 · 게시물 카드

사용자 질문(원문): "기사의 정보나 x.com 의 정보를 내가 주면 넣을 수도 있나?" → 가능. 주 소스는 X(트위터)가 될 것이라고 사용자가 밝힘.

---

## 1. 입력 형태
| 소스 | 사용자가 주는 것 | 시스템 처리 |
|---|---|---|
| 기사 | URL (또는 유료 기사면 본문 붙여넣기) | 본문 가져오기 → 매체·날짜·헤드라인·핵심 사실 추출 |
| X 게시물 | **텍스트 붙여넣기 또는 화면 캡처** + 게시일·계정 주소(가능하면) | 캡처는 비전 모델로 판독(계정명·핸들·시각·본문·첨부 여부) |
| X 링크만 | URL | x.com은 로그인 벽으로 직접 열리지 않는 경우가 대부분 → 텍스트/캡처 요청. **스크래핑 금지**(약관). 공식 API는 유료·요금 변동 |
| 공문·보도자료·데이터 | 파일/URL | 원문 보관, 사실 추출 |

---

## 2. 소스 레코드 (`intake/sources.json`)
```json
{"id": "src_x_0007", "type": "x_post", "account_name": "U.S. Central Command", "handle": "@CENTCOM",
 "account_class": "official_gov|official_org|journalist|public_figure|private|unknown",
 "posted_at": "2026-09-20T14:05:00Z", "text_original": "…", "text_ko": "…(번역)", "lang": "en",
 "url": "https://x.com/…", "capture": "intake/screenshots/src_x_0007.png", "attached_media": "video|photo|none",
 "retrieved_at": "2026-09-26", "verification": {"status": "verified|corroborated|unverified|disputed",
 "checks": ["official_account", "matches_reuters_2026-09-20"], "notes": "…"}}
```
> **[D-0052 정의]** status 는 코드가 인용 대조로 정한다(`orchestrator/source_verify.py`, D50). **verified** = 공식 1차 출처(`official_gov`·`official_org` 계정 또는 document)가 직접 밝힌 사실 + 그 소스 사용자 확인(`confirmed_by`). **corroborated** = supports 근거의 독립 origin ≥ `rules verification.independent_min`(재인용·삭제 게시물 제외). **disputed** = 독립 origin 의 contradicts 근거. 나머지 **unverified**.

기사 레코드: `type: article`, `publisher`, `headline_original`, `headline_ko`, `published_at`, `url`, `key_facts[]`(요지, 원문 장문 복제 금지).

---

## 3. 검증 규칙
1. **계정 진위**: 공식 계정 여부(정부·군·기관의 공식 핸들 목록을 `rules/official_accounts.yaml`로 관리). 사칭 계정 흔함.
2. **날짜**: 게시 시각과 사건 시각을 구분. 날짜 배지는 사건일.
3. **교차 확인**: 사실 주장은 가능하면 독립 매체 1곳 이상과 대조 → `corroborated`. 대조 불가면 `unverified`로 두고 원고에서 **"~는 주장했습니다/올렸습니다"** 로 귀속.
4. **삭제·수정**: 캡처 시점 보관. 삭제된 게시물은 "삭제된 게시물(캡처 시점 ○○)"로 표기하거나 쓰지 않는다.
5. **분쟁 사안**: 한쪽 게시물만으로 서술하지 않는다. 반대 측 입장 소스를 함께 찾는다(`03` §3).
6. 결과를 `claims.json`으로: `{claim_id, text, source_ids[], status, contested, sides?}` → research/script가 이 id만 인용(`17` §5).

---

## 4. 영상에 쓰는 방식
- **원고**: 게시물·기사 내용은 사실 목록(fact/claim)으로 들어가 문장에 녹는다. 문장 `sources`에 claim id.
- **게시물 카드**(`post`, 신규): 게시물 자체가 뉴스일 때(공식 발표, 정상의 발언).
- **기사 카드**(`article`, `14` §9): 보도를 인용할 때.
- **첨부 영상·사진**: 원칙적으로 사용 불가(올린 사람의 저작물). **예외**: 미국 정부 공식 계정(@CENTCOM 등) 자료처럼 퍼블릭 도메인이 확인된 경우 → 미디어 레지스트리로 등록해 클립/사진으로 사용(`14`).

---

## 5. 게시물 카드 명세 (`post`)

기사 카드와 같은 원칙: **캡처 이미지를 쓰지 않고 자체 조판**, X 로고(상표) 미사용.
```python
위치: 우상단 카드 자리(x = W − 300 − 24, y = 68, 폭 300) 또는 패널 위 중앙(슬롯 panel_center)
바탕: 짙은 카드 rgba(0.07,0.08,0.11,0.94), 둥근 모서리 r6, 1px 테두리 흰색 0.12, 그림자 2겹
1행: 계정 아이콘 원(r14) — 공식 기관이면 권리 확인된 휘장(07 §5), 아니면 이니셜 원(GmarketSans, 강조색 바탕)
     옆에 표시 이름 IBM Plex Sans KR SemiBold 11.5 흰색 / 아래 핸들 IBM Plex Mono 8.5 muted
     오른쪽: '공식 계정' 칩(account_class가 official_*일 때만, Sans 7.5, teal 테두리)
본문: 번역문 IBM Plex Sans KR Medium 12, 줄 간격 18, 최대 5줄 (핵심 문장 형광펜 선택)
원문 한 줄(선택): 짧은 원문 인용 Mono 8 muted, 15단어 미만
하단: 게시 시각 'YYYY. MM. DD HH:MM (UTC)' Mono 7.8 / 오른쪽 'X 게시물 · 번역' Sans 7.8
검증 상태가 unverified면 하단에 '미확인 주장' 표기(호박색 텍스트, 도장 금지)
등장: 30px 슬라이드 + 0.45초 페이드, 핵심 문장 형광펜 0.8초 후
```
- **일반인 계정**(`account_class: private`)은 표시 이름·핸들·아이콘을 가린다("개인 계정"으로 표기).
- 번역은 뜻을 유지하되 과장·요약 왜곡 금지. 원문 링크는 설명란에 기록.

---

## 6. 크레딧·설명란
- 엔딩 카드 '보도 · 자료' 섹션에 기사(매체·날짜)와 X 게시물(계정·날짜) 목록.
- 설명란에 원문 링크 전부.

---

## 7. 인테이크 서비스 개조 (`16` §3)
- `intake_service` / 웹 인테이크 페이지: 소스 유형 선택(기사 URL, 기사 본문, X 텍스트, X 캡처, 파일) + 요청 메모.
- 캡처 판독 워커(비전) → 소스 레코드 초안 → 사용자 확인(계정·시각이 맞는지) → 검증 워커(교차 확인 검색) → `claims.json`.
- `source_completeness_checker`: 원고 주장 중 claim id 없는 문장이 있으면 SCRIPT_APPROVAL 전에 차단.
