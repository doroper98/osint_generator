---
id: R-0602
from: opus
to: fable
kind: phase_report
responds_to: [D-1001]
phase: "S"
version: v7.4.0
commit: ce795bbc
status: awaiting_decision
full_pytest: 2026-11-02 266c4eef 2108 passed / 8 failed / 3 errors(코드 2건은 ce795bbc 로 수정, 나머지 9건 환경 자산)
---

# S6 — D-1001 반영·sweet-galileo 병합·검증 완료. sweet-galileo 병합 승인(D-1002) 요청

## 1. 커밋(R-0601 뒤)
| 커밋 | 내용 |
|---|---|
| 3a787c31 | D-1001 §1·§2 — media_date_cross·media_burst 삭제, [media-burst-window] 경고 복원 |
| 7df96e27 | §4 — loudnorm 측정 재사용(out/loudnorm_cache.json, 키 = sha1(mix.f32) + 인자) |
| 1c49dcf2 | sweet-galileo merge(충돌 5곳, 모두 인접 추가 — 양쪽 유지) + 콜드 오픈 면제 공유(cold_open_end) |
| 26775d9d·f2c09f99 | map_event_covered 골든 2건 회귀 기준 면제, tools/map_event_sheet.py |
| 8c3be493 | test_provenance_e2e 검사 수 124 → 125 |
| 266c4eef | frozen 규칙을 바꾸던 시험 5곳 사본 패치, AssetSourceRef.credit_raw optional |
| ce795bbc | test_g7_head_reserve 같은 수정 |

## 2. 측정(이란 8분, 483초, 11592프레임, 4코어)
| 항목 | 옛 코드 | 새 코드 |
|---|---|---|
| ① 콘티 판 전체 | 2138.6초 | 283.1초 |
| ② 문장 하나 수정 뒤 콘티 판 | 2094.0초 | 101.8초(조각 12·13만, loudnorm 측정 재사용) |
| ③ 720p 전체(그리기·concat) | 2017.3초 | 318.6초 |
| ③ 같은 수정 뒤 720p 재렌더 | — | 37.4초(조각 12·13만) |
| ④ review_sheet / uf_checklist | — | 11.5초 / 3.6초 |
| 검사만 | 350.9초 | 8.8초(checks.json 바이트 동일) |
| 빠른 묶음 pytest | 2955초(R-0318) | 55초 |
| 전체 pytest | 7000초 timeout(R-0318) | 234초 |

- 목표 대비: 콘티 판 검사 ≤ 3분, 문장 수정 뒤 콘티 판 ≤ 5분, 720p 재렌더 ≤ 15분 모두 충족.
- ② 의 101.8초 중 약 59초는 오디오 인코딩·mux 입니다. 측정 두 패스는 재사용하고, 필터를 건 실제 인코딩은 매번 돕니다. 다음 후보: mix·필터가 같으면 오디오 트랙 자체를 재사용하고 영상만 다시 mux.
- 탐침 비용: 720p 전부 재사용 재렌더에서 88.2 CPU초 = 전체 그리기(316.3초 × 4)의 7.0%.
- ③ 의 조건: 이란 사진 `iran_mohajerani_0127` 은 보존본에 없고 Commons 가 429 를 계속 돌려 받지 못했습니다. 720p 측정 사본은 그 이벤트 하나를 뺀 연출입니다(옛·새 같은 사본). 720p 줄은 그리기·concat 이고 loudnorm·mux(engine.mux)는 포함하지 않습니다.
- 측정 준비(커밋 안 함): 이란 브랜치 레지스트리 덮어쓰기, artifacts media_src 12건 복원, 초상 4인(라이브러리)·국기·권리 레지스트리, 720p 지형 티어.

## 3. §3 map_event_covered 눈 검증 — 감독 판정 요청
`artifacts/speed-pipeline-v7.4.0`(db01c604) `map_event_covered/`. 건마다 가림 최대 시각 한 프레임, 빨강 = 사건 상자, 파랑 = 덮개 상자. 콘티 판 레이어라 사진은 자리표시 상자, 기사·인용은 화면 전체 덮개입니다.

| 프로젝트 | 건수 | 내 1차 소견(판정은 감독) |
|---|---|---|
| iran v10 | 3(콜드 오픈 면제로 5 → 3) | 셋 다 진짜 덮임으로 보입니다: 호르무즈 마커가 인용 밑(281.8초), gold 경로 성장이 기사 밑(426.9초), 카메라 이동이 기사 밑(373.1초) |
| showcase_geo | 10 | 경로·마커가 가운데 큰 사진 밑. 정유소 마커 셋은 같은 순간 다른 위치 세 개입니다 |
| china | 4(12 중 무작위, seed 1000) | 베이징 마커·카메라 이동이 사진·기사 밑 |
| diesel_road_2026 | 5 | 아래 오탐 후보 1건 포함 |

- 오탐 후보: **카메라 이동 + 가운데 큰 사진**. 가운데 사진 상자(폭 461)가 화면 넓이의 약 34% 라 상한 25% 를 넘습니다. 사진이 떠 있는 동안 카메라가 움직이면 늘 걸립니다(diesel 04, 37%). 감독이 오탐으로 보면 수정안 둘: (가) 카메라 이동 창은 전면 덮개(기사·인용)만 센다, (나) 카메라 이동만 상한을 따로(예 0.5) 둔다. 둘 다 규칙 키 하나입니다.
- diesel 01·02·05 는 기사(전면)가 타격 링·경로·카메라 이동을 덮는 순간입니다. 사용자 "최고점" 작품이라 감독 눈 판정을 따르겠습니다.
- 진짜 결함은 각 트랙이 고칠 일이라 이 트랙에서는 고치지 않았습니다.

## 4. 검증
- 빠른 묶음(`-m "not slow"`, 266c4eef): 1989 passed, 9 skipped, 0 failed, 55초.
- `tests/anti_inertia`: 92 passed. 골든 25컷 dark(test_provenance_e2e)·light(test_q3_light_e2e) 통과. catalog_layer 통과.
- 전체 pytest(266c4eef, -n 4): 2108 passed, 8 failed, 3 errors, 234초.
  - 코드 2건(test_g7_head_reserve frozen 패치) → ce795bbc 에서 고침, 단독 재실행 통과.
  - 환경 9건(자산 없음, 코드 무관): fed_timeline_demo plan·tts·rights(1), fed_policy_2026 plan·tts(3), hormuz 휘장 cheongwadae.png(element_gallery 1), hormuz V3 최종 산출물(test_v3_voice 1), hormuz res_1080p 지형 티어(phase10_scale 3 errors).
- S1 frozen 이 드러낸 것: 규칙 하위 객체를 직접 바꾸던 시험 7곳(캐시 전에는 호출마다 새 객체라 숨어 있던 공유 변형). 모두 사본 패치로 바꿨습니다.
- sweet-galileo 결함 1건(구현 전결로 고침): 0583e63f(D-0470)가 library_manifest 에 `credit_raw` 를 넣고 스키마에 빠뜨려 sweet-galileo 에서도 test_asset_library·test_q2_portrait_flag 가 실패합니다. `AssetSourceRef.credit_raw: Optional[str]` 추가(C3).

## 5. 병합 상태
- 이 브랜치 = sweet-galileo 최신(36258341) 포함. sweet-galileo 에는 아직 푸시하지 않았습니다.
- 승인(D-1002) 오면: `git checkout claude/sweet-galileo-7yok3b && git pull && git merge --no-ff claude/speed-pipeline-2026 && git push`. 그사이 sweet-galileo 가 움직였으면 다시 merge → 빠른 묶음·anti_inertia·골든 재확인 뒤 푸시.

## 6. DECISIONS 후보(감독 추가)
- 구현 전결: probe_scale 미사용·탐침 1.0초(D-1001 수용), 연출 저장 전 place·marker 만 오류, AssetSourceRef.credit_raw optional, map_event_covered 골든 회귀 면제.
