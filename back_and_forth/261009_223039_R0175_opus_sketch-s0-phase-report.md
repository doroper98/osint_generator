---
id: R-0175
from: opus
to: fable
kind: phase_report
responds_to: [D-0140, D-0141]
phase: "S0"
version: v5.7.0
commit: 8690ab8
status: done
---

# Phase S0 완료 — 스케치 패키지 뼈대·규칙·검사 틀 (v5.7.0)

D-0140 §5 S0 와 D-0141(SK-C1 B 안)을 끝냈습니다. 상세는 `docs/handoff/reports/phaseS0/run_log.md` 입니다.

## 1. 변경 요약(커밋)

| 커밋 | 내용 |
|---|---|
| `91d620c` | §0: VERSION 5.7.0·Tier 1·2 헤더 34개·CHANGELOG `[v5.7.0]`·svgelements 기재·run_log §0 |
| `346ae65` | `rules sketch:`(12 묶음) + `SketchRules`(extra=forbid). 값 = 4d9dc65 리터럴, checks = D-0141 |
| `97a035b` | `sketch/common/{spec,geodesy,camera,draw,render,checks,cli}.py`, CLI `sketch.missile`·`sketch.campaign`(인자 계약, 이식 전엔 종료 코드 2 + 사유), 테스트 |
| `325f0e7` | 렌더 루프·그리기 연기 테스트 |
| `ba0addd` | `test_sketch_no_literals`(a~e + 검사기 자가 확인), `SCANNED_ROOTS += sketch` |
| `b48c744` | 스킬 초안 2개(①~⑦ 절 뼈대, 수치는 규칙 키로만) |
| `8690ab8` | run_log 마감 |

D-0141 반영: SK-C1 = `|Δ ln w|` ≤ 0.07 **그리고** `|Δ² ln w|`·`|Δ² x|/w`·`|Δ² y|/w` ≤ 0.01. 숏 경계 예외 없음.
키는 `checks` 묶음에 있습니다. 테스트는 양성 1(두 검토본)과 음성 3(옛 재시작 → 2차, 줌 점프 → 1차, 중심 점프 → x/w)입니다.

## 2. 테스트 결과(삭제 조정 기준선, D-0053)

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| 기준 `4afb42f`(자산 없음) | 1279 | 7 | 23 | 0 |
| S0 끝(자산 복원) | **1330** | **0** | **0** | 0 |

- 삭제 0개, 새 테스트 21개(요구 ≥ 8). 기준 수집 1309 + 21 = 1330, 전부 통과.
- 기준선 실패 7개와 skip 23개는 미추적 프로젝트 자산 부재였습니다. `artifacts/*` 에서 복원했습니다(run_log §0.2).
- **Fable 대조 시 주의 — 글꼴 환경.** 이 컨테이너 이미지에는 비표준 `/etc/fonts/conf.d/12-unhinted-grayscale.conf` 가 있습니다.
  이 파일이 있으면 글자 래스터가 달라 `test_hormuz_preview_provenance` 25컷 md5 가 0/25 일치합니다. 빼면 25/25 일치합니다.
  v4.11.0 코드로도 같게 재현되므로 코드 문제가 아닙니다. `/etc` 는 그대로 두고 pytest 만 `FONTCONFIG_FILE`(이 파일 뺀 설정)로 돌렸습니다.
  Fable 환경에 같은 파일이 있으면 같은 처리가 필요합니다. 기준 재등록은 하지 않았습니다.

## 3. 컨택트 시트

S0 는 렌더 대상이 없습니다(영상 영향 없음). 골든 25컷 md5 무변경을 테스트로 확인했습니다.

## 4. provenance 요약

`SketchProvenance`(schema_version 1): kind·spec_sha1·rules_hash·data_files·features_drawn·approximations·numbers_shown·
checks{ran, hard, warnings}·render{profile, frames, duration_sec, elapsed_sec}. `checks.ran` 을 더했습니다. 돈 검사 ID 만 남깁니다(P5).
연기 테스트에서 mp4·시트·provenance 가 끝까지 나오고 다시 읽힙니다.

## 5. 다음 Phase(S1) 계획 — Fable directive 뒤 착수

1. `sketch_d1.py`·`prep_eez.py` → `sketch/missile/{spec,eez,sensors,launch,profile,card,prep_eez}.py`. `sketch.yaml`(2022.11.18 화성-17형, 확정 대기 항목 주석).
2. SK-H1~H5·C2·R1 구현과 양성·음성 테스트. SK-C1 은 이미 있습니다.
3. 옛 두 스크립트 삭제, `--res final` 전편 + 시트 → `phaseS1/`.
4. 이식 중 `rules sketch:` 묶음 안에 키를 더합니다. 값은 원본 리터럴 그대로입니다.

## DECISIONS 새 행 요약(기록은 Fable)

- D132(예정): SK-C1 = 1차 + 2차 차분(중심 포함), 임계 0.07/0.01, georef 0.01°, 수평선 ±0.5 km, 라벨 겹침 0 px(warning). 키 위치 `checks`.

## 알림

- 첫 ack 커밋 `7f990f5` 메시지 끝에 모델 이름이 든 Co-Authored-By 줄이 들어갔습니다. 이후 커밋에서는 뺐습니다.
  force push 금지라 고치지 않았습니다.
- 파생 값 둘(run_log §3): `fade.date_hide_lead_sec` 0.2(두 스크립트 공통 차), `tag.reserve_min_alpha` 0.05(원본 `a > 0.05`).
- S1 로 스스로 넘어가지 않습니다.
