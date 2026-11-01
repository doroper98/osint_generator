---
id: R-0318
from: opus
to: fable
kind: phase_report
responds_to: [D-0464]
phase: "IR3"
version: v7.4.0
commit: e69fea42
status: open
---

# 최종 보고 — 『미국·이란 휴전안』 iran_ceasefire_2026

## 1. 전달본
- artifacts/iran-ceasefire-v7.4.0 `a3ffa45` → `iran_ceasefire_2026/final_v2/`.
- `final_deliver.mp4` 28,866,019 B, md5 `d1c655d42d054f4b71c823d09d08fd7d`. 길이 483.03초.
- 원본 `final.mp4`(720p) md5 `4d65ad0d9d15a1bd64d4e2a64c0a1f3b`. 음량 −14.1 LUFS. 자막 66 큐.
- 첫 전달본 `424fb28`(md5 fd89a455)은 사용자 판정으로 탈락했습니다(UF-171·172).
- 그 뒤 콘티 판 v5 `02b48e4`(md5 f2796da0)와 프리뷰 v2 `414ed10`을 거쳐 final_v2를 만들었습니다.

## 2. 커밋(이번 단계, 구현 세션 몫)
| 커밋 | 내용 |
|---|---|
| 71a36ebb | merge econ-template(D-0456) |
| 8da24358 | R-0314 게이트 ② 자료 |
| d1390698 · beb14477 | .gitignore(media/res_*) · description.yaml |
| f8ecb1c7 | 첫 전달본(fd89a455) done |
| 25bc3915 | 장치 `[element-hold]`·`[media-overlap]` hard(UF-171·172) |
| dd03b655 · 63a69cbb | 연출 v9 · 사전 검사 hard 정리 |
| a06d7c19 · 0cdf704b | R-0315 · R-0316 |
| 01b00b38 | 재전달본(d1c655d4) done |
| 4a91bbc4 | R-0317 |
| e69fea42 | cherry-pick b69d2eb8(D-0348, full_types 에서 backdrop 제외) |

## 3. 검사
- 콘티 판 v5 · 프리뷰 v2 · 완성본 모두 hard 0입니다. 경고는 콘티 47, 프리뷰 49입니다.
- provenance `user_feedback_guards`에서 UF-170 forbidden, UF-171 element_hold, UF-172 media_overlap은 모두 0입니다.
- 남은 경고는 둘입니다. portrait_unused는 배지가 패널 위에 놓이고 모즈타바 ≠ 알리 하메네이 초상이라 쓰지 않은 것입니다. geo_unsourced는 경로 점이 지명 사전 밖이라 생깁니다.
- 골든 3건: 장치 커밋 뒤 15 passed(약 23분)입니다. hormuz 자산은 `artifacts/phase7-v3.3.0` `shared/media_src`에서 복원했습니다.
- cherry-pick e69fea42 뒤 관련 시험 + `tests/anti_inertia`: 83 passed, subtest 9 통과입니다.

## 4. 전체 pytest — 공식 결과: 7000초 timeout
- 명령: `timeout 7000 python -m pytest -q -n 4 -p no:cacheprovider -rfE tests`(14:25Z 시작). 종료 코드 124입니다.
- timeout 시점 로그 집계: 통과 1968, F 11, E 5, s 14, subtest 375입니다. 수집 2086 중 약 1998이 끝났습니다.
- timeout 으로 종료 요약이 없습니다. 그래서 실패 이름은 아래 확인 실행으로 얻었습니다.

### 4.1 이름 확인(빠른 묶음 1회)과 재현(1회)
- 빠른 묶음 `-m "not slow"` -rfE: 1955 수집, 1941 passed, 7 failed, 9 skipped, subtest 339 통과, 2955초입니다.
- 실패 7건(FAILED 5 + SUBFAILED 2)만 따로 돌렸습니다. 7건 모두 재현됐습니다.
- 관련 여부는 장치 커밋 전 `f8ecb1c7` worktree 에서 같은 시험을 돌려 가렸습니다.

| 시험 | 사유 한 줄 | 재현 | f8ecb1c7 에서 | 관련 커밋 |
|---|---|---|---|---|
| test_checks.py::ChecksTest::test_severity_table | 검사 이름 집합에 element_hold·media_overlap 이 없음(시험 기대값 미갱신) | 재현 | 통과 | **25bc3915(내 장치 커밋)** |
| test_clip_frame.py::ClipFrameTest::test_slot_values | `clip_show_sec.broll` 기대 (3, 6), 실제 (3, 9) | 재현 | 통과 | **25bc3915(broll 6→9, 내 커밋)** |
| test_direction_convert.py::ConvertFidelityTest::test_example_prompt_copy_matches_project | 예시 사본 project_id None ≠ 'hormuz_korea' | 재현 | 실패 | 무관(이전부터) |
| test_direction_convert.py::…::test_yaml_equals_old_direction [hormuz_korea] | events_by_type 에 card·tanker_loop 차이 | 재현 | 실패 | 무관(이전부터) |
| test_direction_convert.py::…::test_yaml_equals_old_direction [taiwan_strait] | marker 에 `vline: False` 키가 더 있음 | 재현 | 실패 | 무관(이전부터) |
| test_g9_gazetteer.py::GazetteerFileTest::test_ne_md5_matches_local_source_when_present | 로컬 NE 원본으로 만든 사전이 저장본과 다름(182자 차이) | 재현 | skip(원본 없음) | 무관 — 환경 의존(이 컨테이너가 받은 NE 판) |
| test_projection_dots.py::LaneSourceJoinTest::test_same_outlet_merged_and_projection_excluded | 레인 출처 줄 끝에 "목표 범위 일별…·실효금리 월평균"이 더 붙음 | 재현 | 실패 | 무관(이전부터, econ 트랙) |

- **내 커밋이 낸 실패는 2건입니다.** 둘 다 시험의 기대값이 규칙 변경을 따라가지 않은 것입니다. 장치나 영상의 결함은 아닙니다.
- 고치려면 시험 두 줄(`test_checks.py:119` 집합에 두 이름 추가, `test_clip_frame.py:28` broll 9.0)이면 됩니다. 지시대로 고치지 않았습니다. 감독 판단을 기다립니다.
- 전체 로그의 E 5는 빠른 묶음에서 나오지 않았습니다. slow 묶음에서 난 것으로 봅니다.
- **slow 131개: 미확인(slow, timeout 으로 요약 없음).** 추가 실행은 하지 않았습니다. 전체 로그의 F 11 중 빠른 묶음 7을 뺀 나머지와 E 5가 여기 속합니다.

### 4.2 환경·성능 관찰(결정 요청 후보, 코드 수정 없음)
- 마지막까지 돈 시험은 `tests/test_g8_animatic.py::AnimaticRunTest.setUpClass`(slow)입니다. 다른 worker 3개는 15:53Z에 이미 대기 상태였습니다.
- py-spy 표본: `render_animatic → run_checks → check_series_label_overlap`(engine/checks.py:2636)이 시리즈 구간 t 0.3~53.3을 1초 간격으로 `render_frame` 합니다.
- 프레임마다 `stage_timeline.grid_segments`가 `load_rules()`로 규칙 YAML을 다시 읽습니다. 1초 프레임 하나에 약 45~60초가 걸렸습니다(15:54:00 t=40.3 → 15:54:47 t=41.3).
- 가설: 프레임마다 다시 읽는 YAML이 비용의 대부분입니다. 다음 트랙의 decision_request 후보로만 남깁니다.

## 5. 차단 호스트(R-0296 실측 + 이번 단계)
| 호스트 | 응답 | 판정 |
|---|---|---|
| commons / upload.wikimedia.org | 301 | 열림(대량 요청 시 429) |
| www.youtube.com | 200 | 열림(yt-dlp 봇 확인 — 우회 안 함) |
| en.wikipedia.org · aljazeera · apnews · cbsnews · bbc | 000 | 막힘 |
| state.gov · whitehouse.gov · centcom.mil · dvidshub.net · navy.mil | 000 | 막힘 |
| reuters.com 401 · cnbc.com 403 | — | 사이트 거부 |
| download.pytorch.org | 403 | 프록시 거부(PyPI 판 torch 사용) |
| DVIDS cloudfront(골든 자산) | connect_rejected | 막힘 → phase7 보존본 복원 |

## 6. 영상에 넣지 않은 것 — 5건(R-0315 의 "6"은 오기, 5가 맞습니다)
| 항목 | 사유 |
|---|---|
| 루비오 배지 | 기사·사진과 같은 구간에 6초 완전 노출 자리 없음 |
| 샤리프 배지 | 같은 사유 |
| 트럼프 인용(act1_9) | 자막과 내용이 겹침, 앙카라 사진과 충돌 |
| 기사 0043 | act1 순차 배치에 자리 없음 |
| 기사 0047 | IRGC·CENTCOM 인용과 양측 무게 균형 유지 |

- 그 전 단계 제외: dextrous 사진(photo_age), 유튜브 클립(봇 확인, 우회 안 함).

## 7. 지시와 다른 사실
| # | 지시 | 사실·처리 |
|---|---|---|
| 1~6 | R-0297 표 그대로 | 1차 봉쇄 4/13, 이틀안은 아라그치 10/31 발언, 60억은 카타르 보관분, 붕괴 선언 7/8 앙카라, 상선 공격 7/6~7, 48.5%는 복수 보도 |
| 7 | 막대 차트 | 휘발유 가격은 dual_line 으로 그렸습니다(값 null 계열 2점 미만 스키마 거부) |
| 8 | 보험료 범위 | "선가 대비(범위 하단)" 단일 계열입니다. 상단은 그리지 않았습니다 |

## 8. 남은 일
- 없습니다. 위 4.1의 시험 두 줄 갱신은 감독 결정을 기다립니다. 대기합니다.
