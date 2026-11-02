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

## RIGHTS-AP-001 — 크레딧 저작자 칸에 Commons 안내문·URL 이 그대로 찍힘

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
