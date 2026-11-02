<!--
tier: 3
last_synced_with: v7.4.0
ssot_for: [rights-antipatterns]
depends_on: [README.md, ../../CLAUDE.md, ../../schemas/media_models.py, ../../schemas/war_history.py, ../../rules/video_rules.yaml]
last_review: 2026-11-02
-->

# Rights Antipatterns

권리·라이선스·크레딧 표기 안티패턴 카탈로그입니다. **append-only**.

각 항목은 [README.md](README.md) 의 표준 포맷을 따릅니다.

---

## RIGHTS-AP-001 — 유물의 PD 를 사진의 권리로 착각(입체 유물 사진)

- **증상 (symptom)**: 전쟁사 칸나이 스케치(v7.4.0 W4)의 주화 카드 `cannae_coin` 레코드 license 칸에 "Public domain" 을 적었다.
  Commons 의 LicenseShortName 이 "Public domain" 이었기 때문이다. 그러나 그 값은 주화(기원전 3세기 유물)의 PD-old 였다.
  사진(CNG 촬영)은 Template:CNG 로 CC BY-SA 2.5 / GFDL 이었다. 화면 허용 목록 밖의 사진이 판정 ① 컷에 나갔다.
  감독 검수(R-0299)도 레코드 license 칸만 보고 파일 페이지 틀을 대조하지 않아 놓쳤다(D-0606 §2).
- **원리**: 유물(PD)과 사진 라이선스는 별개다. Commons 'PD-Art' 는 2D 복제(회화·판화·사본의 평면 복제)에만 성립한다.
  주화·조각·부조·도기·비석 같은 입체 유물 사진에는 사진가의 권리가 따로 있다.
- **나쁜 예 (bad)**: 레코드 `license` 하나에 손으로 적은 값으로 화면 허용을 판정한다. 입체 유물(주화·조각·부조·도기) 사진도 평면 작품처럼 PD-Art 로 본다.
- **좋은 예 (good)**: 사진 라이선스(`photo_license`)와 유물 권리(`work_license`)를 따로 적는다. 화면 판정은 `photo_license` 로만 한다.
  파일 페이지의 라이선스 분류를 `license_tags` 로 자동 기록하고 손으로 적은 값과 대조한다.
- **자동 조치 (mitigation)**:
  - `python -m sketch.war.fetch projects/<pid>`·`tools/commons_fetch.py get`(공용)이 Commons 분류를 `license_tags` 로, 거기서 정한 사진 라이선스를
    `photo_license` 로 자동 기록한다(`schemas.war_history.photo_license_from_tags`). `work_license` 는 레코드 손값.
  - `engine/checks.py` `license_mismatch`(hard, 모든 장르) — 영상이 쓰는 레코드를 렌더 검사에서 다시 대조(C12-3 저장소 전체).
  - `schemas.war_history.license_mismatch` — 유물 나이 PD 분류(`rules war_history.rights.work_age_tags`)를 빼고 남은 사진 분류가
    불허(`disallowed_tags`: CC-BY-SA·GFDL·NC·ND)뿐이거나, 레코드 `photo_license` 가 분류에 없으면 `[license-mismatch]` → MediaAsset 검증 실패(hard).
  - period_art·document 레코드는 `photo_license`·`license_tags` 필수, period_art 는 `work_license` 필수(`license` = `photo_license`).
  - 시험: `tests/test_war_rights.py`.
- **한계와 보강(D710)**: 유물 나이 PD 분류만 있고 사진 분류가 없는 입체 유물 사진(예: 1900년 촬영 사진처럼 사진 자체가 오래된 경우)은
  분류만으로 가를 수 없다. 그런 레코드(work_kind coin·sculpture·relief·pottery)는 `photo_pd_basis`(사진 자체의 PD 근거: 촬영자·발행 연도·조항)가
  없으면 검증 실패다(`schemas.war_history.photo_pd_basis_needed`).
- **관련**: back_and_forth R-0303 §0, D-0606 §2. 교체: CNG 사진 → Sailko 사진(CC BY 3.0, 알테스 무제움).

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
