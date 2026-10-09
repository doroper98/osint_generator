---
id: R-0180
from: opus
to: fable
kind: phase_report
responds_to: [D-0143, D-0144]
phase: "S2"
version: v5.8.0
commit: f156f7b
status: done
---

# Phase S2 완료 — 미사일 3D 지구본 전환 이식 (v5.8.0)

D-0143 보강 8항목 + D-0144(이음새 A). 상세 `docs/handoff/reports/phaseS2/run_log.md`.

## 1. 변경 요약(커밋)

| 커밋 | 내용 |
|---|---|
| `f935f52` | §0: VERSION 5.8.0·헤더·CHANGELOG(v5.7.0 S0·S1 pass 마감)·기준 시트(4d9dc65 worktree 7컷) |
| `634bdf7` | `rules sketch.globe` 전 수치(원본 리터럴)·`numbers` deg/range_sep, geodesy 배열판(`dest_arr`·`to_local`·`merc_y_deg`), `render.CrossfadeScene`, provenance `numbers_computed` |
| `d578693` | `sketch/missile/globe.py`(기하·카메라·래스터·볼륨)·`globe_scene.py`(장면·라벨·패널), `--globe`, SK-C1(3D)·SK-H6, spec `globe{}`, 결함 수정 |
| `888934b`·`7a550ad` | 테스트 14(이음새 회귀 `checks.seam_px` 포함) |
| `1baba50` | `globe3d.py` 삭제(P2) |
| `f156f7b` | run_log·`compare_sheet.jpg`·`sketch_globe_sheet.jpg`·`sketch_provenance.json` |

## 2. 테스트

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S1 끝 | 1349 | 0 | 0 | 0 |
| S2 끝 | **1363** | **0** | **0** | 0 |

새 14개(요구 ≥ 10). 삭제 테스트 0. 옛 단정 1줄(`--globe` 종료 코드 2) 삭제. 4faf90b 메시지 "15" 는 오기(실제 13 + 이음새 1).

## 3. 비교(§0)

7시각 중 **1.0·4.5·6.5·9.0 픽셀 동일**(0.000 %). 12.5·15.0·17.5 = 0.99 % — 원인은 결함 수정 둘뿐:
1. 정점 라벨 위 잘림(t ≈ 9.3~9.8) → 위 여백 안으로.
2. 수평선 패널에 덮인 착탄 라벨(t ≥ 10.6) → 패널 아래로(provenance `label_moved_below_panel`).
3. 정점 값 "약 6,040km"(발표값 버림) → 포맷터 "6,040.9km"(SK-H1).

이식 중 찾은 단위 함정: 원본은 선 굵기·대시·머리 반지름·발사/착탄/정점 라벨 오프셋을 720p 장치 px 로 적었다 → `globe.px_ref_height: 720` 기준으로 옮겨 720p 에서 원본과 같다.

## 4. 렌더·provenance

| 프로파일 | 시간 | md5 |
|---|---|---|
| 480p | 2분 4초(≤ 180초) | `dd1fb5b5…` 1,570,171 B |
| 720p | 4분 17초(≤ 10분) | `6486ed5d55a0ddf924db4c8fb94c48a9` 2,983,730 B, 456프레임 19.0초 |

provenance(final): kind `missile_globe`, hard 0·warning 0, ran 8종(SK-H6 포함), `numbers_computed` 6(수평선 거리·고도, 식·입력), `numbers_shown` 에 기하 계산값 없음.
SK-C1(3D) 검토본 최대 0.00055 / Δ ln f 0.0042. 이음새 480p 11.70 · 720p 11.74 ≤ 12.5.

## 5. 사용자 확정 대기 목록(누적 — S4 에서 정리)

- 독도 문구, NLL 개략 좌표, 레이더 사양 값, 착탄 반경 25km(S1)
- 2D t ≈ 26 성주·교가미사키 라벨 밀착(D-0143)
- 2D→3D 교차 전환 중 궤적선 이중 겹침 ≈ 12px(D-0144)
- 3D 레이더 방위·고각 0~60° = 개념값

## 6. 다음(S3) — Fable directive 뒤 착수

천왕성 작전도 이식: `svg_georef.py`·`sketch/campaign/*`·`prep_georef`, spec, SK-G1~G3·H5, 옛 두 스크립트 삭제.

## DECISIONS 새 행 요약(기록은 Fable)

D135(SK-C1 3D)·D136(H6·numbers_computed)·D137(이음새 A, `checks.seam_px` 12.5)은 Fable 기록. 이번 Phase 에서 새로 요청할 결정은 없습니다.
