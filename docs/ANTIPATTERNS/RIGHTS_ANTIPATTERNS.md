<!--
tier: 3
last_synced_with: v7.4.0
ssot_for: [rights-antipatterns]
depends_on: [README.md, ../../CLAUDE.md]
last_review: 2026-11-02
-->

# Rights Antipatterns

권리·라이선스·크레딧 표기 안티패턴 카탈로그입니다. **append-only**.
각 항목은 [README.md](README.md) 의 표준 포맷을 따릅니다.

---

<!-- 번호 정정(2026-11-02): 이 브랜치에서 처음 RIGHTS-AP-001 로 적었으나, 전쟁사 트랙(claude/war-history-2026, 0893e585, 2026-11-01 11:54Z)이 먼저 RIGHTS-AP-001(유물 PD ≠ 사진 권리)을 썼다. 병합 때 번호가 겹치지 않도록 이 항목을 002 로 옮긴다(내용 불변, 최종 감독 요청). -->

## RIGHTS-AP-002 — 크레딧 저작자 칸에 Commons 안내문·URL 이 그대로 찍힘

- **증상 (symptom)**: 『미국·이란 휴전안』 final_v3(md5 87eda849) 엔딩 카드(478초)와 credits.txt 인물 사진 칸이 깨졌다.
  - 트럼프 초상 출처가 "This image is available from the United States Library of Congress's … See Commons:Licensing." 다섯 줄로 찍혔다.
  - 하메네이 초상 출처는 "http://farsi.khamenei.ir/photo-album?id=36022#i" 로 찍혔다.
  - 감독 프레임 검수가 전달 직전에 잡았다(D-0470 뒤).
- **나쁜 예 (bad)**: 공용 초상 라이브러리(`assets/library/library_manifest.json`) `source.credit` 에 Commons extmetadata `Credit`(출처 안내 문구·URL)를 그대로 저장했다. 새 컨테이너에서 프로젝트 권리 기록(`assets/rights_registry.json` people)을 그 값으로 다시 만들었고, 엔딩 카드·credits.txt 는 저작자 칸을 그대로 찍었다.
- **좋은 예 (good)**: `credit` 에는 저작자 이름만(예 "Shealeah Craighead (백악관)", "khamenei.ir") 둔다. Commons 원문은 `credit_raw` 에 보관한다. 저작자는 Commons `Artist` 메타에서 읽어 사람이 정리한다.
- **자동 조치 (mitigation)**:
  - `[credit-garbled]` hard(engine/checks.py, rules `qa_checks.credit_garbled`). 이 영상이 쓰는 권리 항목의 저작자 칸, 미디어 credit_author, credits.yaml 손 행 license 칸에 URL·"This tag does not indicate"·"Commons:"·"This image is available"·"This file was derived from" 가 있거나 80자를 넘으면 실패합니다. 콘티 판·프리뷰·전편 같은 run 입니다.
  - 라이브러리 정리: 트럼프·하메네이(감독 1f5e0987) + 10건(bezos·chey_tae_won·dario_amodei·jensen_huang·lagarde·putin·tim_cook·warsh·xi_jinping·zelensky). 모두 Commons `Artist` 메타로 바꾸고 원문은 `credit_raw` 에 남겼습니다.
- **회귀 테스트 (regression_test)**: `tests/test_uf173_guards.py::CreditGarbledTest`(안내문·URL 실패, 저작자 통과, 라이브러리 전수 0)
- **발견 버전 (discovered)**: v7.4.0
- **상태 (status)**: `active`

## RIGHTS-AP-003 — CC 라이선스 번호만 보고 통과시키면 사진 쪽 별도 이용 조건을 놓친다

- **증상 (symptom)**: 『2027년 예산안 분석』 사진 수집 중(R-0615), Korea.net Flickr(대한민국 정부 공식 계정)의 2026 국무회의 사진이 Flickr 라이선스 12(CC BY-SA 4.0)로 붙어 있었다. 그런데 사진마다 설명란에 "available only for publication by news organizations and/or for public purposes", "partial reproduction … or use of the photograph with other images is strictly prohibited without the express written permission" 조건(한국어 병기 "보도 혹은 공익목적 … 부분 복제 … 다른 이미지에 통합 … 금지")이 있었다. 라이선스 번호 관문(`flickr_license_ok`)만으로는 통과했을 사진이다.
- **나쁜 예 (bad)**: Flickr `license` 번호나 Commons `LicenseShortName` 만 보고 권리 통과로 판정한다. CC 표시와 충돌하는 별도 조건(보도·공익 한정, 자르기·합성 금지)이 붙은 사진이 영상에 들어간다.
- **좋은 예 (good)**: 라이선스 번호와 함께 사진 쪽 설명란·태그·이용 조건 글을 읽는다. 제한 조각이 하나라도 있으면 라이선스와 상관없이 거부하고 사유를 검색 기록에 남긴다. 권리가 불확실하면 받지 않는다(C9·20 §8, 감독 판단 D613).
- **자동 조치 (mitigation)**:
  - 규칙 키 `rules media.restriction_phrases`(영문·한국어 조각, 대소문자 무시) 하나를 Flickr·Commons 가 같이 쓴다(`schemas.emblem_models.restriction_hits`).
  - Flickr: `tools/media_fetch.flickr_restrictions`(meta description·설명·태그 글) → `fetch_flickr` 거부, `media_fetch.py flickr-check <url> --log <proj> --sid <sid>` 가 판정과 거부 사유를 media_search.json rejected 에 남긴다.
  - Commons: `commons_fetch._ii` 가 ImageDescription·UsageTerms·Permission 을 `terms` 로 읽고, `search(media=True)` 가 `terms_hits` 가 있으면 allowed false, 검색 기록 rejected 에 "별도 이용 조건(…)". `media_fetch` 의 Commons 받기도 같은 조각으로 거부.
- **회귀 테스트 (regression_test)**: `tests/test_sa_obligation.py::RestrictionPhraseTest`(Korea.net 조건 문구 = 라이선스 12 여도 거부·문구 없으면 통과·NC/ND 13~16 거부, Commons UsageTerms 거부)
- **발견 버전 (discovered)**: v7.4.0
- **상태 (status)**: `active`

## RIGHTS-AP-004 — CC BY-SA 고지 줄(링크 의무)을 손으로 적은 크레딧 행이 '크레딧 오염' 검사에 걸렸다

- **증상 (symptom)**: nvidia-chips-china-2026 프리뷰. CC BY-SA 사진 10장의 고지 줄이 길어 엔딩 크레딧 롤 속도가 상한을 넘었다(`[endcard-overflow]`). 사진 줄을 두 열로 나누려고 credits.yaml 손 행에 고지 줄(저작자 · 제목 · 라이선스 · 링크 · 변경 사항)을 그대로 적자 `[credit-garbled]` 가 10건 났다("https:// 포함").
- **나쁜 예 (bad)**: `[sa-obligation]` 은 엔딩 크레딧 줄에 링크를 요구하고, `[credit-garbled]` 는 손 행의 링크를 금지한다. 자동 나열(`auto: media`) 한 절로만 두 검사를 함께 통과할 수 있었고, 그 절은 한 열에만 놓인다.
- **좋은 예 (good)**: 손 행의 license 칸이 그 자산의 고지 줄(`engine.credits.sa_line`)과 글자 그대로 같으면 의무 고지로 본다. 한 글자라도 다르면 종전대로 오염 검사를 받는다.
- **자동 조치 (mitigation)**: `engine.checks.is_sa_notice_row` — `check_credit_garbled` 가 정확히 일치하는 고지 줄 행만 건너뛴다. SA 가 아닌 자산·다른 절(people 등)·다른 문자열은 예외가 없다.
- **회귀 테스트 (regression_test)**: `tests/test_sa_obligation.py::NoticeRowNotGarbledTest`
- **발견 버전 (discovered)**: v7.4.0
- **상태 (status)**: `active`
