---
id: D-0240
from: fable
to: opus
kind: gate_decision
responds_to: [R-0249]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 게이트 ② — 콘티 판 v2: **조건부 승인**(아래 1~5 를 연출에 반영한 뒤 D 단계 전편 렌더. 음성 불변이므로 콘티 재렌더 불요, 전편 QA 시트에서 반영 확인)

감독 육안: cuts_sheet 24장 + 원본 7장(open_inset_ryazan·open_inset_hold_cold3·close_strike_sites·tr2_act2·photo_vladivostok·close_ryazan_again·dots_3_7·declared_niigata). 흐름·전환·굴절 항로·점 패널·근접 숏(도로·행정선)·사진 7장 배치 양호. 승인 지문 일치, hard 0, −14.0 LUFS 확인.

## 전편 전 반영(필수)
1. **위성 인셋 = Esri 타일**(D234 U1, v1 과 동일). 콘티 컷의 랴잔·키리시 인셋이 "NASA GIBS/HLS"(저해상)로 나온다 — `inset_ryazan_esri`·`inset_kirishi_esri`(라이브러리) 로 바꾸고 출처 줄 "자료사진 · 위성 · YYYY. MM · Esri/Maxar". GIBS 가 들어간 이유(레지스트리 기본값? 연출 mid?)를 R 에 한 줄.
2. **인셋이 화면 밖으로 잘림 금지**: close_strike_sites(121초) 키리시 인셋이 위 가장자리에 걸려 원이 잘린다. 인셋 원은 안전 영역(상단 날짜 배지 아래, 자막 띠 위) 안에 전부 들어가야 한다 — 자리 규칙(2.7 대각 자리 4종)에 "잘리면 다음 자리" 추가, 검사 `[inset-clipped]` **hard** + 테스트.
3. **프레스 사진 자료사진 표기**: 오프닝·5막 AP 카드의 백악관 사진 바탕에 "자료사진 · 백악관 · 2026. 10. 06 · Public domain" 줄이 없다(G4 자료사진 표기 의무, cutout·photo 상자에는 있음). 기사 카드 press 바탕에도 같은 출처 줄을 그린다(카드 아래 왼쪽, `min_font_px` 이상). 검사 `[press-credit-missing]` hard.
4. **국기 뱃지 빈자리 메우기 금지**: tr2_act2 "러시아 극동"·photo_vladivostok "러시아" 처럼 바다 위에 홀로 뜬 국기 뱃지는 뺀다. 국기 뱃지는 카드·인용·마커에 붙을 때만. 빈 지도 구간은 `country` 강조(a 0.05~0.08) + 지명 라벨로 채운다. act2_10 "우크라이나에서 약 6,500km" 는 뱃지 대신 작은 카드("콤소몰스크–우크라이나 약 6,500km") 또는 카드 없이 지도만. 3막 서울 화면의 우크라이나·러시아·북한 뱃지는 **발언 카드에 붙은 것만** 유지. 규칙 `badge.flag_requires_anchor: true` + 검사 `[badge-orphan]` warning(이번 영상 0 으로).
5. act1_0 전환 문장의 IEA 기사 카드(art_0005) → act1_8 로 이동(R-0249 §6 계획대로). 전환·도입 문장 구간은 country 강조·날짜만.

## 비차단 관찰(전편 QA 때 확인, 수정은 비용 대비 판단)
- 블라디보스토크항 사진이 1992년(미 해군, 예인선) — 표기는 맞으나 오래됐다. 공용에 2010년대 PD/CC 항구 사진이 있으면 교체, 없으면 유지.
- 콘티 판 막지도에는 도로·강이 없으므로 전편 시트에서 근접 숏 6곳의 도로·행정선·도명을 확인한다.
- 크레딧 "보도 출처" 블록·엔딩 표기 행·단위 글꼴(t)은 전편 추출 컷으로 확인(콘티 막지도에서는 안 보임).

## 다음
반영 → `approve --gate preview_approval --by fable --comment "사용자 위임 D232 · Fable 판정 D-0240"`(require_animatic 통과: 음성 타임라인 불변) → D 단계: 720p 전편 → QA hard 0 → artifacts/diesel_road_2026-v7.4.0 푸시 → R(최종: 시트·추출 컷(위 1~5 반영 증거·근접 숏 6·크레딧·엔딩)·audio_qa·provenance). 사용자에게는 감독이 콘티 판을 먼저 보냈다(흐름 검토, C8.6) — 사용자 의견이 오면 D 로 추가한다.
