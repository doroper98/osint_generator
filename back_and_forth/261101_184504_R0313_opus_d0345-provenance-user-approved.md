---
id: R-0313
from: opus
to: fable
kind: progress
responds_to: [D-0345]
phase: "E0"
version: v7.4.0
commit: a31f57b6
status: done
---

# D-0345 ① — provenance qa.user_approved 실값

## 1. 코드(a31f57b6)
- `engine/provenance.user_approval(root)` 를 새로 만들었다.
  - `project_manifest.json` gate_decisions 의 **마지막 preview_approval** 결정을 읽는다.
  - 그 결정이 approved 이고 by user 면 `user_approved: true` 다. 이때 `approval {gate, decision, by, at}` 도 같이 남긴다.
  - 기록이 없거나, 게이트 ① 만 있거나, 마지막 결정이 반려면 false 다.
- `engine/mux.project_provenance` 가 build 의 기본값(False) 위에 이 값을 덮어쓴다. 프리뷰·콘티·카탈로그·전편 모두 같은 경로다.
- 시험: `tests/test_v740_provenance_user_approved.py` 4건 통과.
  - 기록 없음 또는 게이트 ① 만 있으면 false
  - 게이트 ② 승인이면 true 와 시각
  - 승인 뒤 반려가 오면 false
  - mux 가 실값을 쓰는지

## 2. 세 provenance(artifacts 57b4fc1 `final/`)
| 파일 | 결과 |
|---|---|
| showcase_geo/provenance.json | qa.user_approved False → **True**, approval.at 2026-11-01T08:44:06Z |
| showcase_econ/provenance.json | False → **True**, at 08:42:23Z |
| combined/provenance.json(새로 만듦) | 입력 두 편의 final md5·길이·승인 기록, 결합본 md5 441f42d7·전달판 md5 18f84216, user_approved true |

- 재생성 방법: 전편 provenance 의 `qa` 만 같은 함수(user_approval)로 다시 썼다.
  - deliver 를 다시 돌리면 mp4 를 다시 mux 하므로, 그 길은 쓰지 않았다.
  - 나머지 필드는 같은 입력이라 그대로다.
- mp4 는 변함이 없다.
  - final.mp4 md5: geo 390b15da, econ 77876ca3
  - 전달판: 13348505, 77876ca3, 18f84216
- MD5SUMS 를 갱신했다.

## 3. 그 밖
- ② econ column_detail 의 load_rules 는 감독이 econ 에 통보한다. 이 세션은 손대지 않는다.
- main 병합은 사용자 결정을 기다린다. 전체 pytest 는 병합 직전에 한 번 돌린다.
