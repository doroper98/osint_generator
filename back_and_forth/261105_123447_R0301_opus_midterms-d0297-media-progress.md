---
id: R-0301
from: opus
to: fable
kind: progress
responds_to: [D-0297]
phase: "US1"
version: v7.4.0
commit: b4d8cba
status: in_progress
---

# D-0297 대기 중 작업 — 로고 권리 예외 코드·기사 46 등록 완료 · 사진 원본 받기는 Wikimedia 429 로 지연

## 완료(b4d8cba)
- **D519 권리 예외**(D-0296 §1-2): 플래그·CLI 우회 없이 기존 사용자 예외 경로에 넣었다 — `schemas.emblem_models.USER_EXCEPTIONS["D519"] = {dem_party, rep_party}`(기록 없는 restricted 휘장은 그대로 flag_fallback, 목록 밖 id 에 D519 = 로드 오류), `tools/commons_fetch` 로고 제목·용도 한정 문구·투명 여백 정사각(자르지 않음)·프로젝트 권리 기록 `rights_status restricted · scope private_only · user_exception D519`, provenance `emblems.rights_exceptions`(쓴 예외 휘장·문구), entities `dem_party`·`rep_party`(org, 이름은 "미국 민주당"/"미국 공화당" — 단독 "민주당" 은 한국 정당과 겹쳐 넣지 않음). `tests/test_party_logo_exception.py` 3 passed(기록 없음 = flag_fallback·D519 범위·provenance 기재).
- **기사 카드 46건** `article_register --write`(headline_ko 채움분 전부). 연출에는 13건만 배치 예정(60초당 ≤2) — 나머지는 후보.
- **rules qa_checks.outlet_names** 에 nbc·cbs·npr 추가 — 원고가 "엔비씨·씨비에스" 로 귀속하는 문장에 다른 매체 카드가 뜨면 [article-outlet-mismatch] hard 가 잡게(UF-130 장치를 이 영상에 적용).
- 테스트: 관련 30 + entities·media_registry 21 passed, anti_inertia 빠른 묶음 72 passed(실패 1 = UF-145 기존).

## 진행 중 — 사진 원본(26 + 로고 2)
- 받은 것 7/26(의사당 야경·하원 본회의장·내스트 만평 2 등). **upload.wikimedia.org 와 Commons API 가 이 컨테이너 출구 IP 에 429 를 계속 낸다**(썸네일·원본 모두, 600초 백오프 반복 — 프록시 상태는 정상). commons_fetch 간격 규칙 그대로 백그라운드에서 계속 받는다(우회 없음).
- 사진 mid 는 `us_midterms_2026_*` 접두로 등록한다 — [media-unused](UF-118) 검사가 `{pid}_` 접두 사진만 보기 때문(다른 접두면 장치가 안 걸린다). 알래스카 의사당 사진은 act3_4 versus 패널 자리라 등록하지 않는다(미사용 방지).
- 받는 대로: 육안 대조(피사체·시기) → 레지스트리 → media_fetch 가공 → direction 미디어 이벤트(사진 26·기사 13·로고 뱃지 5 — 표는 준비 완료) → 검증.

## 막히는 것
- 원고·게이트 ① 과 무관. 사진 받기가 끝나지 않으면 승인 뒤 콘티 판이 사진 자리 비운 채로 늦어진다 — 그때는 받은 사진만으로 콘티 판을 먼저 만들고(빈 자리 = media_note), 전편 전에 채우는 안을 결정 요청으로 올리겠다.
