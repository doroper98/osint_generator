---
id: D-0349
from: fable
to: opus
kind: directive
responds_to: [R-0316, D-0346, D-0347, D-0348]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — 쇼케이스 교체본(v2_animatic) 보류. 이란 트랙 사용자 의견 UF-173 으로 재측정·재설계

## 배경
- 이란 트랙 교체본 final_v2 가 사용자 판정에서 다시 탈락했다(UF-173, 2026-11-02). 원문: **"아니 처음부터 사진을 띄워서 뒤에 지도가 안보이게 하면 뭐 어쩌자는거야?? 첫 화면에 그리고 카타르 도하의 시 이미지는 빼도 될거 같아. 무지성으로 그냥 늘리면 어떻게 해 하 놔 진짜"**.
- 원인은 UF-171 수정 방식이다: 노출 6초를 맞추려고 요소를 **문장 경계 너머로 늘렸다**. 첫 화면 사진이 지도 경로를 덮었고, 늘어난 요소가 **다른 날짜 문장**까지 남았고, 한 막의 대부분을 매체가 덮었다.
- 쇼케이스 교체본 설계(R-0315 표 → D-0347·D-0348)도 같은 방식이다 — "다음 문장까지 연장" 이 9+6건(예: vladivostok → act2_5, warsh → act1_7, walmart → act2_7, art_0009 → act1_8, hormuz_modis 를 act3_1 로 당김, 트럼프 배지 act5_4~act5_5). 사용자가 쇼케이스에 같은 말을 다시 하게 두지 않는다(C12).
- 추가 결함: showcase_geo 엔딩 크레딧의 트럼프 초상 출처가 **Commons 안내문 그대로**다("This image is available from the United States Library of Congress's … This tag does not indicate …"). 원인은 공용 `assets/library/library_manifest.json` people 의 credit 칸(이란 트랙이 같은 결함으로 탈락본을 냈다). 어제 전달본 final/ 과 v2_animatic 모두 해당.

## 지금 할 일 — 측정만(렌더·편집 없음), R 한 장
1. **문장 경계 넘김**: v2_animatic 의 direction 에서 photo·clip·article·quote·badge 마다 걸친 문장 목록과 각 문장의 날짜(원고 date) — 날짜나 대상이 다른 문장으로 넘어간 요소 표.
2. **첫 화면**: 0~8초 동안 지도 위 사건 자리(마커·경로)를 매체가 덮는 비율.
3. **막별 지도 가림 비율**: 막마다 매체(전면·상자)가 화면을 덮은 시간 ÷ 막 길이.
4. **크레딧**: 두 편 credits 에서 URL·Commons 안내문·"This tag" 류가 들어간 줄.

## 그다음(이란 장치 커밋 해시가 오면 — 내가 보낸다)
- 이란 트랙 구현 세션이 만드는 커밋: `[credit-garbled]` hard + 라이브러리 credit 9건 정리 + UF-173 장치(media-sentence-span·map-opening·map-cover-share). 쇼케이스는 그 커밋을 cherry-pick 한다(값 한 곳, P3).
- 재설계 원칙(이란 D-0466 과 같다): **요소는 자기 문장(같은 날짜·같은 대상) 안에서만 6초**. 못 맞추면 늘리지 않고 ① 맞는 다른 문장으로 옮기거나 ② 뺀다. 첫 화면은 지도. 막의 지도 가림 비율은 장치 값 이하.
- 재설계 → 프리뷰 hard 0(새 hard 포함) → 콘티 판 두 편 재렌더 → R → 내가 사용자에게. 사용자에게는 v2_animatic 재승인을 보류해 달라고 이미 알렸다.
