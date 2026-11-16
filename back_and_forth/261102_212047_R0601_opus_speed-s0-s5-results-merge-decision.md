---
id: R-0601
from: opus
to: fable
kind: decision_request
responds_to: [D-1000]
phase: "S"
version: v7.4.0
commit: 76e34943
status: awaiting_decision
---

# S0~S5 완료·S6 측정 · sweet-galileo 병합 전 결정 요청(UF-173 장치와 S3 검사 중복)

## 1. 커밋(claude/speed-pipeline-2026)
| 커밋 | 내용 |
|---|---|
| 3e434661 | S0 단계 시간 기록 `engine/timing.py` → `out/timings.jsonl`, provenance `timings` |
| 9732dc43 | 원장 문서 표 재생성(UF-300·301 줄 누락으로 test_doc_table 실패하던 것) |
| e69fdae5 | 6299f295 cherry-pick |
| 45fafee1 | S1 load_rules 캐시 + VideoRules frozen, 사적 규칙 캐시 셋을 load_rules 하나로 |
| 60261f48 | S2 고정 격자 조각 캐시 |
| a4abe7ac | S3 hard 검사 셋 |
| c71895a4 | S4 review_sheet·uf_checklist, README §6.3a, LLM-AP-023 |
| c418ce23 | S5 WORKFLOWS W0a, 연출 좌표 규칙 |
| 76e34943 | S2-7 탐침 간격 0.5 → 1.0초 |

- 정정: a4abe7ac·c71895a4 두 커밋은 스키마 hunk 를 잘못 올려 그 커밋 단독으로는 규칙이 로드되지 않습니다. c418ce23 부터 정상입니다. 푸시된 이력이라 고치지 않았습니다. bisect 때 두 커밋은 건너뜁니다.

## 2. 측정(이란 8분 콘티 판, 483초, 11592프레임, 4코어)
측정 명령: `python /home/user/bench/render_bench.py <proj> animatic 4 <label>`. 옛 코드 = 0b60c74 worktree, 새 코드 = HEAD worktree. 두 worktree 모두 이란 브랜치 media_registry 를 덮어썼습니다(커밋 안 함). 클립 원음이 이 컨테이너에 없어 mix.f32 는 같은 길이 사인파입니다(렌더 시간과 무관). 하네스는 검사를 돌리고 시간을 재되 hard 여부와 무관하게 렌더를 계속합니다(새 S3 검사가 이 연출을 막기 때문).

| 항목 | 옛 코드 | 새 코드 |
|---|---|---|
| ① 콘티 판 전체 | 2138.6초 | 283.1초 |
| — 프로젝트 로드 | 220.6 | 1.8 |
| — 검사(glyph_sweep 포함) | 199.5 | 7.7 |
| — 프레임 그리기 | 1469.7 | 172.9 |
| — loudnorm 2패스·mux | 248.8 | 100.7 |
| ② 문장 하나 연출 수정 뒤 콘티 판 | 2094.0초(전부 다시) | 140.0초(조각 49 중 12·13만 다시) |
| ③ 같은 수정 뒤 720p | 미측정(아래 4절) | 미측정 |
| ④ review_sheet / uf_checklist | — | 11.5초 / 3.6초 |

- S1 검사만: 350.9초 → 8.8초. `animatic_checks.json` 바이트 동일(시간 필드 없음). 목표 ≤ 3분 충족.
- 프레임 그리기가 8.5배 빨라진 것은 조각 재사용이 아니라 S1 입니다. 옛 렌더도 프레임마다 규칙 YAML 을 다시 읽었습니다.
- ② 목표 ≤ 5분 충족. 이제 loudnorm 2패스(약 100초)가 재렌더 시간의 3/4 입니다. D-1000 S2-4 가 "그대로"라 손대지 않았습니다. 다음 후보로 권고합니다: mix.f32 가 같으면 1패스 측정값을 재사용.
- 탐침 비용(S2-7): 간격 0.5초에서 전부 재사용 재렌더의 탐침 73.5 CPU초 = 전체 렌더 그리기 691.6 CPU초의 10.6%. 1.0초로 바꿔 7.2%. 첫 렌더(후보 없음)는 그리면서 서명을 떠서 0입니다.
- 구현 전결: probe_scale 0.25 는 쓰지 않았습니다. 지형 래스터가 프로파일별 자산(assets/res_<프로파일>)이라 축소 장치에서 그릴 수 없습니다. 출력 해상도 그대로 탐침합니다. 설정 키도 넣지 않았습니다.
- S2 정확성 시험(tests/test_chunk_cache.py, 64초 픽스처): 가운데 조각 마커 하나 변경 → 그 조각만 rendered → `--no-cache` 결과와 프레임 md5 동일. md5 동일이 나와 PSNR 기준은 쓰지 않았습니다.
- 측정 중 사고: 첫 수정 측정에서 수정 문구가 연출에 두 번 있어 수정 스크립트가 실패했고 연출이 그대로였습니다. 그 실행은 조각 49 전부 재사용(올바른 동작)이었습니다. 문장 act2_2 의 레바논 마커만 고쳐 다시 쟀고 위 표가 그 값입니다.

## 3. S3 새 검사 건수(병합 전 이 브랜치 기준)
| 프로젝트 | map_event_covered | media_date_cross | media_burst | 시각 출처 |
|---|---|---|---|---|
| iran_ceasefire_2026 v10(현재) | 5 | 0 | 2 | 실제 음성·정렬 |
| iran v9(사용자 탈락본) | 14 | 8 | 2 | 실제 음성·정렬 |
| showcase_geo | 10 | 4 | 2 | plan.json 시각 + 합성 정렬 |
| showcase_econ | 0 | 2 | 0 | 같음 |
| china_tech_export_controls_2026 | 12 | 0 | 2 | 같음(china 브랜치 레지스트리) |
| fed_timeline_demo | 0 | 0 | 0 | 합성 |
| diesel_road_2026(연출 기준 작품, 추가) | 5 | 1 | 0 | plan.json 시각 + 합성 정렬 |
| hormuz_korea 골든 | 대기 | 대기 | 대기 | 자산 복원 중 |

- v9 는 D-0466 이 든 결함을 그대로 잡습니다: 6/18 기사가 7/7 문장 위, 40초에 4개, 1막 덮임 87%.
- v10 의 map_event_covered 5건 중 2건은 콜드 오픈(제목 카드 22.8초 전)입니다: 도하 마커 3.8초, 카메라 이동 12.5초. D-0468 승인 연출(아라그치 인용)과 부딪힙니다. 3건은 본문입니다: 호르무즈 마커 280초, 카메라 이동 373초, gold 경로 420초.
- 다른 프로젝트는 고치지 않았습니다(지시대로).

## 4. 결정 요청 — sweet-galileo 의 UF-173 장치(0583e63f, D-0470)와 S3 중복

쟁점: sweet-galileo 최신에 같은 결함을 재는 hard 검사가 이미 들어왔습니다. 병합하면 같은 개념이 두 번, `[map-cover-share]` 는 같은 꼬리표로 두 구현이 됩니다(SSOT 위반). 또 `[media-burst-window]` 는 두 트랙 결정이 반대입니다.

| 개념 | sweet-galileo(D-0470) | 이 브랜치 S3(D-1000) |
|---|---|---|
| 다른 날짜 문장으로 넘어감 | media_sentence_span hard(tol 0.5) | media_date_cross hard(grace 0.5) — 같은 개념 |
| 지도 덮임 시간 비율 | map_cover_share hard(30초 창, 전면·가운데 1·그 밖 0.5, 콜드 오픈 면제, 골든 면제) | media_burst 의 [map-cover-share](40초 창, 가중 없음) — 같은 꼬리표 |
| 40초 창 개수 | [media-burst-window] **경고 유지**(D-0469 수용 사례가 막힘) | **hard**(D-1000 S3-3) |
| 첫 화면 지도 | map_opening hard | 없음 |
| 자라는 지도 사건 가림 | 없음 | map_event_covered hard |

선택지:
- A(권고). sweet-galileo 쪽을 정본으로 둡니다. 이 브랜치의 media_date_cross 와 media_burst 의 덮임 비율 부분을 지웁니다(P2 삭제). map_event_covered 는 새 개념이라 남깁니다. 단 map_cover_share 와 같은 콜드 오픈 면제(첫 제목 카드 전)를 더합니다. 40초 창 개수는 아래 B1/B2 로 따로 정합니다.
  - 결과: 개념마다 검사 하나. D-0470 고정본 시험(test_uf173_guards, v9 실패·v10 통과)과 골든 면제가 그대로입니다.
  - 위험: map_event_covered 를 v10 에 돌리면 본문 3건이 남아 v10 이 막힙니다. 이것이 결함인지 감독 눈 판정이 필요합니다.
  - 되돌리기: 커밋 단위 revert.
- B. 이 브랜치 쪽을 정본으로 둡니다. D-0470 세 검사 중 두 개를 지우고 고정본 시험을 이 브랜치 검사로 옮깁니다.
  - 위험: 승인된 D-0468·D-0469 판정을 뒤집습니다. 콜드 오픈·가중치 같은 조정값이 사라집니다.
- 40초 창 개수: B1 = D-1000 대로 hard(D-0469 수용 사례가 막힘). B2 = 경고 유지(D-0470 검토 결과). 권고 B2. 같은 결함은 map_cover_share hard 가 시간 비율로 잡습니다. 개수 상한은 사진 수가 아니라 덮임이 문제라는 D-0466 의 진단과 맞지 않습니다. D-1000 지시와 다르므로 결정이 필요합니다.

판정 기준: ① 되돌릴 수 있는 선택 — A·B2 는 지우기만 하면 됩니다. ② 핸드오프·저장소 실측 규칙 우선 — D-0470 이 먼저 병합됐고 고정본 시험이 있습니다.

막히는 범위: sweet-galileo merge 충돌 해결(rules·schema·checks·test_checks·DECISIONS), 그 뒤 빠른 묶음·anti_inertia·골든, S6 병합 승인 요청. 결정 없이 하는 일: 골든 자산 복원(진행 중), hormuz 건수, 720p 측정, 전체 pytest 준비.

§7 해당 없음(감독 전결).

## 5. 그 밖
- S0 감싼 지점: 원고 린트·TTS·MMS 정렬(문장마다)·audio.mix·연출 LLM 호출(run_worker)·렌더 프리뷰/콘티 판/카탈로그/전편 × 그리기·검사·인코딩·프리뷰 시트·mux. 전달본 재인코딩은 저장소 코드 경로가 없어(손 명령) 감싸지 못했습니다.
- S3 스케치 경로: 스케치 spec 에 사진·영상·기사·인용 요소가 없어 해당 없음입니다.
- S5: 연출 프롬프트의 옛 안내가 places 좌표를 직접 만드는 예였습니다. 규칙 키 geo.director_coords 로 바꿨습니다. 저장 전 점검에서 place·marker 의 사전 미대조 좌표만 오류로 둡니다. 경로 경유점은 warning 그대로입니다(구현 전결).
- 시험(변경마다): 관련 시험 + anti_inertia 빠른 묶음 통과(hormuz 자산이 필요한 2건 제외 — 복원 뒤 재실행). 전체 pytest 는 병합 직전 1회.
