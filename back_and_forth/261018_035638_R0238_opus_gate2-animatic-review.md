---
id: R-0238
from: opus
to: fable
kind: review_request
responds_to: [D-0225, D-0226]
phase: "P3-0"
version: v7.3.0
commit: e8bf0207
status: awaiting_gate
---

# 게이트 ② 콘티 판 검토 요청 — diesel_road_2026

## 자료(artifacts 브랜치 `artifacts/diesel_road_2026-v7.3.0-animatic`, 커밋 cbf672ff)
| 파일 | 값 |
|---|---|
| animatic.mp4 | 585.4초 · md5 `dc732d1e263410796e788baea1eb27e8` |
| 음량 | −14.1 LUFS · 실피크 −1.8 dBTP · LRA 3.7 LU |
| animatic_checks.json | **hard 0** · warning 40 |
| prev/sheet.jpg | 22컷 프레임 시트(4·14·64·116·125·165·200·230·270·300·340·370·386·400·418·445·480·512·528·540·560·578초) |
| animatic_provenance.json | features_used: flight 12(drone 8·jet 2·missile 2)·인셋 3(랴잔·키리시·라스라판, private_only)·dual_line 3(press_cited 레코드 대조)·versus 1·기사 19·뱃지 6(국기 3·인물 3)·dip 4 |

## 연출 이력
1. AI 연출가 1회(flight 길이 검증 1건 실패) → 구현 세션 보강: dark 테마·위성 인셋 3·시리즈 패널 3(D-0225 §2.4).
2. 프리뷰 검수 루프 3회(hard 34→20→15, 연출 수정 LLM).
3. 수동 수정 3회(감독 지침 18:10Z 반영): 국기 뱃지(러시아 3)·인물 뱃지(푸틴·젤렌스키·노박)·기사 카드(대사 소환·사우스파르스 양측)·하르그 jet flight(걸프 해상 개략 → 하르그)·오프닝 이동 9초·엔딩 구도(lon 80·lat 45·w 104)·뱃지 자리 조정. → hard 0.
- 검사 빈틈 1건 수정(커밋 41fba183): route_missing 이 flight 를 경로로 치지 않았다 → flight(출발→착탄)를 그 문장의 경로로 인정 + 시험.
- 지침 1)의 "country 강조로 frame 충족" 분기는 만들지 않았다 — 검사에 이미 있는 "국기 뱃지가 보이면 충족"(D-0205) 분기로 해결해 엔진 변경이 필요 없었다.

## 경고(warning 40) 요지
- media_beats 14: 사진·영상 0장(권리 통과 사진 없음 — 사우스파르스 플랫폼 CC BY 4.0 1장 후보는 미사용), 이웃 장면 같은 형태(기사).
- geo_unsourced 13: 마커 좌표 출처 표기 경고(정유소·항만 좌표 = 공개 지명 좌표).
- portrait_unused 10: 라이브러리 초상이 있는데 뱃지로 안 쓴 인물 언급(트럼프·이재명 등은 기사 카드가 덮음).
- article-unused 5(act1_4·act2_14·act2_18·ending_0·ending_2): 60초당 2장 상한 또는 맺음.
- map-theme-override 1: dark(D232 U8 사유 기록).

## 알려 둘 것
- 감독 메모 ⑤의 인물 뱃지 중 트럼프(act4_2·act4_7)·베선트(act4_5)·이재명(act4_13)은 그 문장을 기사 카드가 덮어 뱃지를 두지 않았다. 강유정·블라시우크·알카비는 초상이 없어 카드.
- 볼고그라드 인셋은 원고에 없어 미사용. 하르그는 인셋 없이 jet flight + boom.
- 엔딩 "표기" 행: 비행 경로 개략 · 51% 검증 전 · 위성 사진은 피격 전 자료(비공개 시청 한정). 맨 아래 가장 작은 글씨 전용 칸이 없어 크레딧 행으로 넣었다.

## 다음(지시대로 판정을 기다리지 않음)
- 720p 전편 렌더 진행 중(국기 자산 누락으로 1회 실패 → 프로젝트 국기 PNG 생성 후 재시작). 끝나면 artifacts/diesel_road_2026-v7.3.0 + R 최종.
- 판정에서 수정이 나오면 연출 수정 후 콘티 판·전편 재렌더.
