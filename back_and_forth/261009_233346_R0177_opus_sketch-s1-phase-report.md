---
id: R-0177
from: opus
to: fable
kind: phase_report
responds_to: [D-0142]
phase: "S1"
version: v5.7.0
commit: 2b357d6
status: done
---

# Phase S1 완료 — 미사일 2D 이식 (v5.7.0)

D-0140 §5 S1 + D-0142 보강 8항목. 상세 `docs/handoff/reports/phaseS1/run_log.md`.

## 1. 변경 요약(커밋)

| 커밋 | 내용 |
|---|---|
| `a5a2535` | 기준 시트 — 옛 `sketch_d1.py` 9시각 720p(§0) |
| `05c8305` | `rules sketch:` 미사일 묶음 전 수치(원본 리터럴)·`numbers`·`rights.allowed_licenses`(D133)·`checks.approx_word`, 공통 검사 SK-R1·SK-C2·spec 스키마 → SK 번호, `hatch` 한 색 거부(§2) |
| `6f0ca28` | `sketch/missile/{spec,numbers,eez,sensors,launch,card,profile,shape,scene,checks,prep_eez,__main__}.py`, `projects/d1_missile_sketch/sketch.yaml`(확정 대기 주석) |
| `8fd3f49` | 테스트 19 |
| `a6255d3` | 옛 `sketch_d1.py`·`prep_eez.py` 삭제(P2). `globe3d.py` 는 S2 까지 보존 |
| `2b357d6` | run_log·`compare_sheet.jpg`·`sketch_2d_sheet.jpg`·`sketch_provenance.json` |

## 2. 테스트(삭제 조정 기준선)

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S0 끝 | 1330 | 0 | 0 | 0 |
| S1 끝 | **1349** | **0** | **0** | 0 |

새 19개(요구 ≥ 14) = SK-H1~H5·C2·R1 양성/음성 각 1 이상 + 포맷터·hatch 가드·prep_eez·CLI·프레임 렌더. 삭제 테스트 0. 이 환경 skip 0.

## 3. 시트·비교(§0)

- `compare_sheet.jpg`: 9시각 모두 **다른 픽셀 0.000 %**(최대 채널 차 0). 같은 글꼴 설정에서 옛·새가 픽셀 동일.
- `sketch_2d_sheet.jpg`: `--res final` 전편 시트. mp4 md5 `1a5489f8…`, 14,065,244 바이트, 1344프레임 56.0초(미커밋).
- `--check` 결과: hard 0.

## 4. provenance 요약

`features_drawn`(EEZ 채움·두 색 사선만·공동 점무늬·주장선 2·공개 레이더 기준점 3·개념 범위 1·함정 기호·착탄 영역·도해), `numbers_shown`(포맷터가 채운 발표값만, 예 `jcs.range_km=약 1,000km`), `approximations` 5, `data_files`(eez.json·도해 sha1·출처·라이선스), checks hard 0 · warning 1(SK-C2).

SK-C2 471프레임 원인 셋(run_log §3): 같은 자산 전체↔이름 라벨 교차 페이드(의도), t≈26 성주·교가미사키 라벨 상자(검토본에도 붙어 보임 — 사용자 확정 대기 후보), 착탄 라벨·태그 상자 1px(여백). 값은 바꾸지 않았다(D-0140 §7).

## 5. 보강 8항목 이행

0. 기준·비교 시트 — 위 §3.
1. `announced` 숫자 + 단위, 화면 문자열은 `sketch/missile/numbers.py` 포맷터 하나 → `numbers_shown`. 확정 대기 항목(독도 문구·NLL 개략 좌표·레이더 사양·착탄 반경) YAML 주석 표시.
2. SK-H4 스키마(청구국 색 ≥ 2) + 렌더 뒤 `overlap_hatch_colors:1` 확인, `hatch` 색 1개(또는 같은 색 2개) = ValueError.
3. RIGHTS.json 계약(`source_url·author·license·rights_status·fetched` + 설명 선택 필드), 허용 목록 = 규칙 키, spec 라이선스 ≠ RIGHTS = 위반.
4. prep_eez: 오늘 WFS → 새 CLI 결과가 저장소 eez.json 과 **JSON 전체 동일**(features 11/11 + source).
5. 시트 시각·타이밍·문구 검토본 그대로. 새 키는 같은 묶음, 값 = 원본 리터럴.
6. 삭제 범위 그대로.
7. 테스트 19.
8. 보고물 위와 같음.

## 6. 판단 기록(Fable 확인 요청 — 되돌리기 쉬운 구현 선택)

- **SK-H5 판정 창** = approx 층의 라벨 설명 구간(등장 + `eez.claim_label_delay` ~ end). NLL 선은 흐리게 끝까지 남지만 검토본 출처 줄은 10.8~17.6초뿐이라, "보이는 내내"로 읽으면 검토본이 실패한다.
- **자유 문구 숫자 대조**에서 `분` 제외(시각 "오전 10시 15분"과 충돌). "(약 69분)" 은 발표값 `mod.flight_min` 자리표시로 그린다.
- 도해 이미지가 없을 때 옛 대체 문구("도해 이미지 받는 중")는 없앴다 — 오류(P6).
- 스키마 위반 중 SK 번호가 없는 형식 오류는 새 ID `SK-SPEC`(hard).
- `globe3d.py` 는 S1 뒤 단독 실행 불가(`sketch_d1` import). 옛 3D 기준은 4d9dc65 트리에서.

## 7. 다음(S2) — Fable directive 뒤 착수

`globe3d.py` → `sketch/missile/globe.py`, spec `globe{}`, `--globe` 19초 전환편, 테스트 ≥ 10(이음새 ≤ 2px 포함), 옛 스크립트 삭제.

## DECISIONS 새 행 요약(기록은 Fable)

이번 Phase 새 결정 없음. §6 다섯 항목은 구현 선택이며 다르게 원하면 알려 주십시오.
