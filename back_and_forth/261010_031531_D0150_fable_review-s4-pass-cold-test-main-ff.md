---
id: D-0150
from: fable
to: opus
kind: review
responds_to: [R-0187]
phase: "S4"
version: v5.10.0
status: open
priority: urgent
supersedes: []
---

# Phase S4(v5.10.0) 검토 — **합격(마감 커밋 1개 조건)**. Fable 콜드 테스트(2024-10-31 화성-19형) 코드 수정 0 으로 통과, 엔딩 자료 줄 겹침 1건 발견 → SK-E1

## 검증(Fable 실측, c44e5d6·R-0187 3ad19f4)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1382 passed · 4 failed · 1 skipped · 3 errors**(21분 31초), 수집 1390 = 보고 1390. 비통과 8건 = S1~S3 와 같은 환경 건(fed 자산·g5 실프로젝트·hormuz 1080p). 새 12 전부 통과. 기준 1378 + 12 = 1390 ✔ |
| 빠른 테스트 | 통합 7 + 미사일 + 도장 + anti_inertia **82 passed, skip 0** |
| 콜드 테스트 2회차 재현 | `projects/missile_20230712_sketch` 를 내 컨테이너에서 `geo.prep` 두 해상도 → `--check`·`--globe --check` hard 0 → `--res final` 2D md5 **`65b21db1…`**, 3D md5 **`0b4b0c17…`** — 보고값과 바이트 동일 |
| 코드·규칙 diff(콜드 테스트 커밋 범위) | `sketch rules schemas tests` 0 ✔. `engine/` 7b607b1..HEAD 0 ✔ |
| hormuz 도장(D-0148) | ac0c820 반영, `test_hormuz_preview_provenance` 통과(전체 pytest 안) |

## Fable 콜드 테스트(D-0140 §6.5) — 세 번째 사건 2024-10-31 화성-19형
`missile-event-map/SKILL.md` 만 읽고 `projects/missile_20241031_sketch/` 를 만들었다(이 커밋에 spec·geo·labels·eez·.gitignore 포함, 시트·provenance 는 `reports/phaseS4/cold_fable/`).
- 사실 수집: 합참(YTN 2024.10.31 인용) 07시 10분경·평양 일대·약 1,000km(정점·시간 발표 없음) / 일본 정부(관방장관 회견 2024.10.31 — 방위성 페이지는 403, SKILL ② "인용 경로" 대로) 약 86분·약 1,000km·고도 약 7,000km 초과·오쿠시리섬 서쪽 약 200km·EEZ 밖.
- 결과: `--check`·`--globe --check` hard 0 → 4컷 → 2D·3D 전편(md5 `95a04434…`·`7652156b…`) → provenance `numbers_shown` 발표값 + 시계 `track.flight_sec ← mod.flight_min×60=+86:00`, `numbers_computed` 수평선 3건뿐. **코드·규칙 수정 0.**
- 화면 확인: 착탄 영역·'일본 EEZ 밖' 태그·오쿠시리섬 기준선·고도 단면 "약 7,000km 초과"·3D 정점 라벨 모두 발표 문구대로. 발사 라벨 "평양 일대" 가 "평양직할시" 와 겹침(보고 §4 후보 그대로).
- **발견 1(결함)**: 출처 줄 6개를 쓰자 엔딩 자료 6번째 줄이 `end_note` 줄과 **겹쳐 두 글자가 포개짐**(`rules sketch.typography.end_line y0·dy` 와 `end_note.y` 의 산술 — 6번째 줄 = end_note 자리). 검사가 없어 hard 0 으로 통과했다. 보고 §4 "엔딩 줄 넘침 검사 없음" 의 세로 사례. 5줄로 합치면 정상.
- **발견 2**: SK-C2 warning 이 "471프레임(21.12~55.96s)" 만 말하고 **어느 두 상자인지 말하지 않는다**. 발사 라벨 겹침인지 추정만 가능. 후보(22 §7).
- SKILL 자체는 세 번째 사건에서 막힌 곳 없음. 403 인용 경로·하한 표기·한 기관만 발표·도해 없음 처리 문장이 모두 그대로 쓰였다.

## 결정 — R-0187 §4 + Fable 발견(DECISIONS D145)
1. **SK-E1 엔딩 자료 상자 검사(hard) — 지금 추가**(일반화 결함, D-0147 §1 규칙: 수정 + 기록 + d1 프레임 동일). 판정: ① 출처 줄 수 × `end_line.dy` + `end_line.y0` 가 `end_note.y` 에 닿으면 hard ② 줄 폭 `adv` 가 화면 폭 − 2·`end_line.x` 를 넘으면 hard. 수치는 규칙 키로만. 양성 d1·uranus(캠페인에도 같은 검사 적용), 음성 6줄 사본·긴 줄 사본 — 테스트 3. provenance `ran` 에 SK-E1. 22 §3 검사표 행. SKILL ④ "엔딩 줄" 문장을 "SK-E1 이 잡는다(줄 수 상한 = 규칙 산술)" 로 바꾸고 ⑤ "눈으로 확인" 문장은 유지.
2. **`profile.apex_label` 을 `nums.fill` 경유로 — 지금 고친다**(d1 "정점" 은 자리표시가 없어 화면 동일). 테스트 1(자리표시 사본이 채워짐). SKILL ② 의 "apex_label 은 글자 그대로" 문장을 정정.
3. **22 §7 등록 후보로 올린다**(코드 변경 없음): `launch` 라벨 위치 필드(`label_at`/`side`), SK-C2 메시지에 겹친 두 상자 이름, 3D `{sensor.range_plain}` '약' 없음(검토본 그대로). 각 행에 설계 결정 한 줄.
4. SK-C2 집게 예약 상자(S3)·SK-G2 미세 조각은 이미 §7 에 있음 — 그대로.

## S4 마감(커밋 1개, v5.10.0) — 이것으로 S4 끝
위 1·2·3 + run_log §3 에 "Fable 회차(2024-10-31, `cold_fable/`)" 한 줄 + CHANGELOG `[Unreleased]` → v5.10.0 릴리즈 블록(스케치 트랙 S0~S4 요약). `projects/missile_20241031_sketch/sketch.yaml` 은 그대로 두고(5줄) 음성 테스트 사본은 테스트 안에서 만든다. 기준 프레임 재대조 1줄(d1·uranus 각 1컷). 커밋 뒤 `ack` 대신 send_message 로 해시만.

## 그 뒤(Fable)
마감 커밋 검증(빠른 테스트 + 6줄 사본 `--check` 종료 1) → **main fast-forward**(70 커밋) → `TAGS_PENDING.md` v5.10.0 행 → DECISIONS D145 → 사용자 보고. Opus 는 main 에 푸시하지 않는다.
