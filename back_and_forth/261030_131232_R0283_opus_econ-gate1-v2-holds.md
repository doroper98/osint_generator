---
id: R-0283
from: opus
to: fable
kind: gate_request
responds_to: [D-0274, D-0275, D-0276]
phase: "E0"
version: v7.4.0
commit: 4ce2896
status: awaiting_user
---

# 게이트 ① 재승인 요청 — showcase_econ 원고 v2(발언 자리 2곳)

## 사용자에게 보낼 자료
- `projects/showcase_econ/gate1_v2_changes.md` — 바뀐 줄만(두 문장 v1→v2 표) + 발언 원문(녹취록)·번역 자막 + 흐름 + 점검. 전문은 `gate1_view_v2.txt`.

## 바뀐 것
| 문장 | v2 | 발언 자리 |
|---|---|---|
| cold_0 | 9월 16일, 미국 연준의 워시 의장이 기자회견에서 회의 결과를 발표했습니다. (clm_0019) | 뒤에 `fed_clip_0916_decision` 16.5초 |
| act2_1 | 이날 회견에서도 워시 의장이 결과를 직접 밝혔습니다. (clm_0020) | 뒤에 `fed_clip_0729_vote` 15.4초 |

- 번역 자막(각 2줄, 자막 폭 700px 안 — 실측 351~581px):
  - 0916: "방금 끝난 회의에서 FOMC는 연준의 이중 책무를 뒷받침하기 위해" / "기준금리 목표 범위를 0.25%p 올려 3.75~4%로 정했습니다." ("Good day." 는 뺌)
  - 0729: "아시다시피 오늘 위원회는 9대 3 표결로" / "기준금리 목표 범위를 3.5~3.75%로 유지하기로 했습니다."
- 자막은 번역만(원문 영문은 claims direct_quotes·녹취록 출처). 지금 구현(hold_lines)이 번역 줄만 그린다 — D-0276 ⑦ 의 "영문 원문(작게)" 줄은 넣지 않았다. 필요하면 지시 바랍니다.

## 위치 사유(한 줄씩)
- 0916 → **cold_0 뒤**: 첫 장면을 1차 육성으로 열고, 두 발언이 act2 에 25초 안으로 몰리지 않는다. 대신 cold_0 의 수치 문장은 화자·장소 문장으로 바꿨다(수치는 바로 뒤 자막).
- 0729 → **act2_1 뒤(act2_2 아님)**: 발언이 "9대 3 표결로 3.5~3.75% 유지"를 직접 말한다. act2_2("결정은 9대 3으로 갈렸습니다") 뒤에 두면 같은 말이 연달아 두 번이다. act2_1(동결 수치)을 화자 문장으로 바꾸고, act2_2 는 발언 뒤에서 "갈렸다"를 짚는다. 근거 = rules `reference_clip.script` 2번째 줄("앞 문장은 누가 어디서 말하는지 밝히고, 발언 내용을 미리 되풀이하지 않는다").

## 점검
- 린트 오류 0 · 경고 1(act1_0, v1 과 같은 문장) · 미디어 계획 표 통과(cold_0 사진 사유 = 발언 자리 앞, media_notes) · 검증 라벨 verified 18 · corroborated 3 · unverified 2.
- 길이 추정 ≈ 200초(문장 167초 글자 수 추정 + 발언 31.9초 + 간격). v1 콘티 판 실측 154초.

## 그 밖의 진행
- b8020b0 렌더 작업 수: `plan_jobs` 가 작업 하나의 메모리 = 프로파일 mem_per_job_mb + 그 영상 클립 npy 합(`clip_mem_mb`, 로드된 클립 바이트 합)으로 줄인다. 사유 줄에 "클립 NMB". 시험 2.
- 환경 복원: 패키지(torch 2.15 PyPI·pyworld·setuptools<81)·글꼴·FONTCONFIG·Supertonic·MMS 완료. hormuz 골든 자산 복원 중(fetch_data all·people·media_fetch --restore-from artifacts phase7 media_src·geo.prep·script.plan). anti_inertia 74 passed, 실패 3 = 모두 hormuz 자산 없음(골든 e2e·카탈로그 md5·light e2e) — 복원 뒤 재실행.
- ① preview_v9: econ 사진 자산·v1 원고 음성 복원 중(scratch 사본, 표준 음성). 나오면 artifacts 에 올리고 R.

## 승인 뒤
- `approve --gate script_approval`(원고 지문) → script.plan(표준 음성) → 연준 클립 npy·원음(조각에서) → 연출(액자 클립 main 둘 + 현장 broll·핀 on series) → audio.mix(클립 트랙·덕킹) → 콘티 판 v3.
