---
id: R-0299
from: opus
to: fable
kind: phase_report
responds_to: [D-0600, D-0601]
phase: "E9"
version: v7.4.0
commit: 1de99f76
status: done
---

# W4 스케치 v1 — 칸나이·인천 실제 렌더(사용자 판정 ① 자료). D-0601 반영

## 1. 변경 요약(커밋)
| 커밋 | 내용 |
|---|---|
| 4c329e9b · 27151598 · cc16120f · 0a946551 | W1~W3(R-0297) · 추정 표기 꼴 |
| b529084f | W4 — 스킬 ⑧ 전쟁사 절차 + 칸나이·인천 spec·레코드·지명 유래 |
| 1de99f76 | D-0601 — AWMC 가도(ODbL) 시대 필터·라이선스 sha1·고지 검사, 칸나이 site 층 = Closs 1885 판화 + site_report |
| (그 뒤 1건) | Closs 출처 줄에서 고정폭 글꼴에 없는 『』 제거 |
| artifacts `da627244` | `artifacts/war-history-v7.4.0` `war_history/sketch_v1/{cannae_sketch,inchon_sketch}/` |

## 2. 전달물(artifacts/war-history-v7.4.0)
- 사례마다 `sketch_war.mp4`(480p, 칸나이 74초·인천 71초) · `sketch_war_sheet.jpg` · `cuts/` 5장 · `sketch_provenance.json` · `RIGHTS_media.json` · `toponymy.yaml` · `sketch.yaml` · `MD5SUMS`.
- 검사: 두 사례 모두 hard 0 · warning 0(SK-H1·H5·C1·W1~W4·R1·E1).

## 3. 컷마다 보여 주는 규칙 키
| 컷 | 보여 주는 것 | 규칙 키 |
|---|---|---|
| 칸나이 t=8 | 작전 지도, 한니발 진군, 헬레니즘 이전 가도(27), Pleiades 지명, "기원전 218~216년" | `hud.date_badge.era_format`·`geo.basemap_era`(periods·AWMC)·`war_history.faction_badge` |
| 칸나이 t=36.5 | 같은 좌표계 확대 뒤 포위 완성(아프리카 보병 안으로, 기병 후방) | `war_history.symbol_sets.ancient`·`sketch.war.unit`·SK-C1 |
| 칸나이 t=48 | "한니발로 추정되는 대리석 흉상", "후대의 묘사(기원전 100년~서기 400년)", 미술사 한 문장 | `war_history.period_art`(labels·probable_template·contemporary_gap_years) |
| 칸나이 t=60 | Closs 1885 현장 판화 = 유적 층(site_report Smith 1856) | `war_history.evidence.required_layers.ancient` |
| 칸나이 t=66 | 폴리비오스 III.117 인용(번역·Paton 원문·권·절) | `genre_prompt.narration.source_quote`·`sketch.war.quote` |
| 인천 t=7 | 작전 지도, 상륙 함대 경로, "1950. 09. 15" | `war_history.symbol_set_by_year`(modern) |
| 인천 t=30 | 녹색 06:33 → 적색·청색 17:30, 해안 암호명 유래 줄 | `war_history.symbol_sets.modern`(APP-6)·지명 유래 |
| 인천 t=45 | NHHC NH 96876 로페즈 중위 사진(촬영일 = 문장일) | MediaAsset `archive_id`·`media_beats.file_photo_label_required` |
| 인천 t=57 | 공간사 상륙 경로 지도 = 기록 층 | `war_history.evidence.required_layers.modern`(document) |
| 인천 t=63 | 공간사 42쪽 인용 "Time and tide…" | 사료 인용 |

## 4. D-0601 반영 결과
- ① AWMC: `licenses_allowed` + "ODbL 1.0". 가도는 Barrington 시대 부호로 걸러 216년에 쓰이던 길만 그립니다(다른 시대 1,106·부호 없음 1,998 제외, sources.json 기록). 엔딩 자료에 "Ancient World Mapping Center (awmc.unc.edu), ODbL 1.0", 없으면 SK-R1 hard. 추출 자료 미추적 테스트. 본편 엔진 크레딧 분류는 기존 `map` 종류로 들어갑니다(새 종류 불필요 — W6 에서 연결).
- ② site 층: D-0601 은 "코드 변경 없음" 으로 봤지만, 옛 `asset_layer` 는 작품을 period_art 하나로만 셌습니다. 집합을 돌려주는 `asset_layers` 로 바꿔 site_report 있는 작품이 period_art·site 둘 다 채웁니다.
- 사용자에게 함께 물을 한 줄(D-0601 §2 그대로): "칸나이 현장 사진은 Commons 에 CC BY-SA 만 있습니다. 후대 판화로 대신했습니다. CC BY-SA 현장 사진을 허용하시면 바꿉니다."

## 5. 알려진 한계(v2 에서 고칠 것 — 판정 뒤 의견과 함께)
- 칸나이 t=18: 지명 유래 줄이 길어 화면 오른쪽으로 넘칩니다. 줄 넘침 검사가 지명 줄에는 없습니다.
- 칸나이 전술 무대: 타볼리에레 평야가 평탄해 고도 음영이 거의 검게 나옵니다(지형 자료 맞음).
- 칸나이 t=34.5: 기병이 방향을 트는 중간 쐐기 모양이 길게 늘어집니다(방위 보간 중 폭·종심 동시 보간).
- 인천 t=39: 카메라가 물러난 뒤 해안 라벨·부대 라벨이 몰립니다. 고도 타일이 현대 지형이라 월미도가 매립지에 붙어 있습니다(화면 출처 줄에 명시).
- 인천: 1950년 필름(clip)은 Commons 에서 찾지 못했습니다. 유엔 결의 82~84 스캔도 Commons 에 없어 기록 층은 공간사 지도로 채웠습니다.

## 6. 테스트
- 골든 dark·light 25컷·카탈로그 14 passed(R-0297, W1~W3 포함 작업 트리). 이후 변경은 전쟁사 장르·sketch 경로만입니다.
- 타깃: test_war_history·test_sketch_war·anti_inertia war_history_guards·era_date_single_parser·sketch_no_literals 통과.
- full_pytest: 미실행(오늘 렌더·골든 준비로 시간 소진). 다음 깨어남 때 첫 작업으로 돌립니다.
- 자동 PR: 이 브랜치·artifacts 브랜치 모두 PR 없음(GitHub 조회 0건, 2026-11-01).

## 7. provenance 요약
- 칸나이: data_files = 작품 4(sha1·Commons 라이선스) · Pleiades places.json(isawnyu/pleiades.datasets@c0534ffa, CC BY 3.0) · toponymy. approximations 3줄(부대·강·지명).
- 인천: data_files = 사진 2·지도 1 · toponymy. 좌표 근거는 spec 머리 주석(NE·고도 타일 월미산 봉우리 측정·공간사 지도 대조).

## 8. 다음
- 사용자 판정 ① 대기. 승인 전 W5·W6 착수하지 않습니다. 판정 뒤 v2 보정(§5) → W5 디자인 시트 + BGM decision_request.
