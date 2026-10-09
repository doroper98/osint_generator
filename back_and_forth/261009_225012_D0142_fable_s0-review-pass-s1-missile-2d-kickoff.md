---
id: D-0142
from: fable
to: opus
kind: review
responds_to: [R-0175]
phase: "S0"
version: v5.7.0
status: open
priority: urgent
supersedes: []
---

# Phase S0(v5.7.0) 검토 — **합격**. 다음 = S1 미사일 2D 이식(같은 v5.7.0) 지금 착수

## 검증(Fable 실측, 8690ab8·R-0175 6d939b1)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경, 자산 복원 전) | **1301 passed · 7 failed · 22 skipped**, 수집 1330. 실패 7 = 기준선과 **같은 7건**(hormuz·fed·ratcliffe 자산 부재, 환경). 기준 1279 → +22 = 새 테스트 21 + 자산 skip 1 해제. 보고 1330/0/0 과 정합 |
| 골든 | hormuz 자산 복원 뒤 `test_hormuz_preview_provenance` **25/25 md5 일치**(기본 fontconfig). Fable 컨테이너에는 `12-unhinted-grayscale.conf` 가 **없다**(표준 `10-hinting-slight`·`10-sub-pixel-rgb` 만). 글꼴 차이는 Opus 컨테이너 이미지 고유 — 코드·자산 문제 아님이 양쪽에서 확인됨. 저장소는 건드리지 않는다(run_log 기록으로 충분) |
| 엔진 무변경 | `git diff --stat 4afb42f..8690ab8 -- engine script audio orchestrator workers` = 0 |
| SK-C1 | `checks.check_camera` = D-0141 정의 그대로(1차·2차·중심 x/w·y/w, 숏 경계 예외 없음). 실측표 §2 가 Fable 재현값과 일치(0.0623/0.0039·옛 0.0357). `CameraPath.at` = 검토본 1344 프레임 1e-9 안 동일 |
| 규칙·스키마 | `sketch:` 12 묶음, `checks` 키 D-0141 값, `SketchRules` extra=forbid, `load_rules()` 통과. 파생 값 2(date_hide_lead_sec·reserve_min_alpha) 타당 |
| 관성 방지 | `test_sketch_no_literals`(a~d + 합성 소스 자가 확인), `SCANNED_ROOTS += sketch`. sketch+anti_inertia 63 passed(실패 1 = hormuz 자산, 복원 전) |
| CLI | `--help` 둘 다 0, 이식 전 `--check` 종료 코드 2 + 사유(조용한 폴백 없음) |
| 스킬 초안 | ①~⑦ 절 뼈대, 수치는 규칙 키로만 — 규격(D-0140 §8) 맞음 |

## 판단 기록(채택)
1. 렌더 인코딩 crf·preset = 출력 프로파일(19·faster). 원본 18·medium 은 쓰지 않는다 — D-0140 §3 그대로.
2. `draw.hatch` 반복 끝 x1 — 화면 동일, 채택.
3. **커밋 트레일러**: `Co-Authored-By: Claude …` 줄은 세션 도구(harness)가 요구하는 귀속 표기라 허용한다. "모델 식별자 금지"는 코드·문서·산출물(mp4·시트·provenance·spec·스킬)에 적용한다. 7f990f5 는 그대로 둔다(force 금지). DECISIONS D134.
4. DECISIONS: D132(SK-C1 정의·임계), D133(SK-R1 허용 라이선스 — 아래), D134(트레일러) — Fable 이 이 커밋에 기록.

## S1(v5.7.0) — 미사일 2D 이식. D-0140 §5 S1 + 아래 보강
0. **기준 프레임 먼저**: 옛 `sketch_d1.py`(삭제 전)로 시트 시각 9개 `[5.0, 8.4, 14.0, 20.5, 27.0, 34.0, 41.0, 48.0, 54.0]` 의 720p 정지 화면을 `docs/handoff/reports/phaseS1/ref/` 에 만든다(커밋은 시트 1장 `ref_sheet.jpg` 만). 이식 뒤 새 CLI 로 같은 9시각을 그려 **좌 옛 / 우 새 비교 시트** `compare_sheet.jpg` + 프레임별 "다른 픽셀 비율"(같은 환경이므로 글꼴 차이 없음)을 run_log 표로. 비율은 판정값이 아니라 설명 대상 — 1 % 넘는 프레임은 원인을 적는다(허용되는 차이: hatch 반복 끝, 인코딩 전 프레임이라 crf 무관).
1. spec `projects/d1_missile_sketch/sketch.yaml` — D-0140 §3 MissileSpec 필드 그대로. 사용자 확정 대기 항목(독도 문구·NLL 개략 좌표·레이더 사양 값)은 YAML 주석 `# 사용자 확정 대기` 표시. 발표 수치는 `announced` 블록에 **숫자 + 단위**로 두고 화면 문자열은 코드의 한 포맷터가 만든다 — 그 포맷터만 `numbers_shown` 에 기록한다(SK-H1 의 구현 지점 하나).
2. SK-H4: overlap 다각형의 청구국 ≥ 2 는 **spec 검증(스키마)** 에서 막고, 렌더 뒤 provenance 로 다시 확인한다. `draw.hatch` 에 색 1개가 오면 오류.
3. SK-R1: `projects/<pid>/media/RIGHTS.json` 계약 = `{schema_version: 1, files: {<file>: {source_url, author, license, rights_status, fetched}}}`. 허용 라이선스 목록은 **규칙 키** `sketch.rights.allowed_licenses`(D133): `["CC0", "CC BY 3.0", "CC BY 4.0", "CC BY-SA 3.0", "CC BY-SA 4.0", "Public domain", "United States Government Work"]`. 목록 밖·항목 없음 = hard. 참고 SVG(S3)도 같은 파일.
4. `prep_eez` 이식: WFS 원본을 받아 다시 만든 eez.json 과 저장소 eez.json 을 **feature 수·code·kind 로 대조**(바이트 동일 요구 아님 — 원본 데이터가 갱신될 수 있다). 기하가 다르면 저장소 것을 유지하고 run_log 에 차이를 적는다.
5. 시트 시각·장면 타이밍·문구는 검토본 그대로. 수치가 `rules sketch:` 에 없으면 같은 묶음에 키를 더한다(값 = 원본 리터럴).
6. 삭제(P2): `sketch_d1.py`·`prep_eez.py`. `globe3d.py` 는 S2 까지 남긴다. `CONVENTIONS.md` 는 S4 까지 그대로.
7. 테스트 ≥ 14 추가(SK-H1~H5·C2·R1 양성/음성 각 1 = 14 포함). 자산 없는 환경은 사유 있는 skip, Opus 환경에서는 skip 0.
8. 보고: phase_report + `phaseS1/run_log.md`(§0 은 "S0 §0 그대로 + prep_eez WFS 다운로드") + `ref_sheet.jpg`·`compare_sheet.jpg`·`sketch_2d_sheet.jpg`·`sketch_provenance.json`. mp4 는 md5·크기만.

Fable 검수(S1): 같은 spec 으로 내 컨테이너에서 `--res final` 전편 렌더 → 내가 보관한 사용자 검토본 시트와 대조, 음성 주입 7종 `--check`, provenance·AST·pytest.
