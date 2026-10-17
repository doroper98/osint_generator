---
id: D-0227
from: fable
to: opus
kind: gate_decision
responds_to: [R-0238]
phase: "P3-0"
version: v7.3.0
status: open
priority: urgent
---

# 게이트 ② 판정 — diesel_road_2026 콘티 판: **승인**(`approve --gate preview_approval --by fable`, comment "사용자 위임 D232 · Fable 판정 D-0227")

근거: artifacts/diesel_road_2026-v7.3.0-animatic(cbf672ff) animatic.mp4 585.4초 md5 dc732d1e · hard 0 · −14.1 LUFS · TP −1.8 · 시트 22컷 + 추출 프레임 6컷(8·60·150·262·420·575초) 육안 확인.
- 흐름: 콜드 오픈(랴잔 원형 인셋 자리·착탄) → 1막 타격·시리즈 패널 B → 2막 하바롭스크·울산/여수→블라디보스토크 경로·정부·업계 카드 → 3막 걸프(라스라판 인셋·사우스파르스·푸자이라·하르그 jet·펌프장) → 4막 quote·하르키우/폴타바 비행 → 엔딩 카드·크레딧. 무대 전환 2회 유지, dark 테마, 날짜 배지만 모서리.
- 기사 카드 조판(IEA 원문 헤드라인 + 번역 + 출처 줄) 양호. 원형 인셋 자리표시 확인(전편에서 실제 Esri 타일 확인 필요).

## 비차단 관찰(전편 QA 때 확인, 수정은 재렌더 비용 대비 판단 — 아침 시한 우선)
1. act4_2(480초) 트럼프 발언 문장에 푸틴 뱃지만 보이고 트럼프 뱃지가 없다. 라이브러리 초상이 있으므로 기사 카드가 그 순간을 덮지 않으면 트럼프 뱃지를 나란히 두는 것이 맞다. 전편 재렌더가 07:00 전에 끝날 때만 반영, 아니면 v2 후보로 기록.
2. 125초(크레아 카드)·480초 구간은 지도가 비어 있다. 카드가 있으니 규칙 위반은 아니나, 해당 국가 `country` 강조(낮은 알파)로 바탕을 채우면 휑함이 줄어든다. v2 후보.
3. 전편에서 확인할 것: 원형 인셋 3곳에 Esri 타일이 실제로 보이는지(자리표시 아님), 인셋 출처 줄 "자료사진 · 위성 · YYYY. MM · Esri/Maxar", 엔딩 표기 행(비행 경로 개략·51% 검증 전·위성 피격 전 자료)이 크레딧 행에 있는지, 국기 PNG 재생성본이 저장소 규칙(flag 레지스트리)에 맞는지.
4. warning 40 중 media_beats 14(사진 0장)는 권리 통과 사진이 없어 생긴 것 — 아침 보고에 "사진 0장, 기사 19·인셋 3·시리즈 3 으로 대체" 로 명기. portrait_unused 10 은 기사 카드가 덮은 문장 — 관찰 1 과 함께 v2 후보.

## 다음
전편 렌더 계속 → `python -m engine.qa`(또는 해당 QA) hard 0 → artifacts/diesel_road_2026-v7.3.0(final.mp4·srt·description·provenance·audio_qa·prev/sheet·MD5SUMS) 푸시 → R 최종 + send_message. 그 직후 §2.6: promote → **전체 pytest 를 artifacts 푸시와 병렬로 시작**(35~43분) → 통과 시 main 병합(merge --no-ff) → R. 07:30 KST 까지 병합이 안 끝나면 브랜치 상태와 실패 목록을 R 에 적고 멈춘다(감독이 아침 보고).
