<!--
tier: 3
last_synced_with: v7.4.0
ssot_for: [rights-antipatterns]
depends_on: [../../schemas/media_models.py, ../../schemas/war_history.py, ../../rules/video_rules.yaml]
last_review: 2026-11-01
-->

# Rights Antipatterns

본 문서는 권리·라이선스 관련 안티패턴 카탈로그입니다. **append-only**.

각 항목은 [README.md](README.md) 의 표준 포맷을 따릅니다.

---

## RIGHTS-AP-001 — 유물의 PD 를 사진의 권리로 착각(입체 유물 사진)

- **증상 (symptom)**: 전쟁사 칸나이 스케치(v7.4.0 W4)의 주화 카드 `cannae_coin` 레코드 license 칸에 "Public domain" 을 적었다.
  Commons 의 LicenseShortName 이 "Public domain" 이었기 때문이다. 그러나 그 값은 주화(기원전 3세기 유물)의 PD-old 였다.
  사진(CNG 촬영)은 Template:CNG 로 CC BY-SA 2.5 / GFDL 이었다. 화면 허용 목록 밖의 사진이 판정 ① 컷에 나갔다.
  감독 검수(R-0299)도 레코드 license 칸만 보고 파일 페이지 틀을 대조하지 않아 놓쳤다(D-0606 §2).
- **나쁜 예 (bad)**: 레코드 `license` 하나에 손으로 적은 값으로 화면 허용을 판정한다. 입체 유물(주화·조각·부조·도기) 사진도 평면 작품처럼 PD-Art 로 본다.
- **좋은 예 (good)**: 사진 라이선스(`photo_license`)와 유물 권리(`work_license`)를 따로 적는다. 화면 판정은 `photo_license` 로만 한다.
  파일 페이지의 라이선스 분류를 `license_tags` 로 자동 기록하고 손으로 적은 값과 대조한다.
- **자동 조치 (mitigation)**:
  - `python -m sketch.war.fetch projects/<pid>`(그리고 `tools/commons_fetch.py get`)가 Commons 분류를 `license_tags` 로 기록한다.
  - `schemas.war_history.license_mismatch` — 유물 나이 PD 분류(`rules war_history.rights.work_age_tags`)를 빼고 남은 사진 분류가
    불허(`disallowed_tags`: CC-BY-SA·GFDL·NC·ND)뿐이거나, 레코드 `photo_license` 가 분류에 없으면 `[license-mismatch]` → MediaAsset 검증 실패(hard).
  - period_art·document 레코드는 `photo_license`·`license_tags` 필수, period_art 는 `work_license` 필수(`license` = `photo_license`).
  - 시험: `tests/test_war_rights.py`.
- **한계**: 유물 나이 PD 분류만 있고 사진 분류가 없는 입체 유물 사진(예: 1900년 촬영 사진처럼 사진 자체가 오래된 경우)은 통과한다.
  그런 레코드는 사진 연대를 `date` 에 적고 검수 때 사진 자체의 PD 근거를 확인한다.
- **관련**: back_and_forth R-0303 §0, D-0606 §2. 교체: CNG 사진 → Sailko 사진(CC BY 3.0, 알테스 무제움).
