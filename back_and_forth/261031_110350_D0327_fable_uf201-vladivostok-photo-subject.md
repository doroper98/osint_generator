---
id: D-0327
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 블라디보스토크 사진 교체: 주된 피사체가 문장의 대상이어야 한다(UF-201). 장치 [photo-subject-background]

사용자 원문(2026-10-31, UF-201): **"블라디보스토크항의 이미지로 이런 통통배(터그선)이미지가 크게 박힌 이미지를 쓰는게 맞아?"**
감독 판정: **맞지 않다.** 담당: 쇼케이스 세션 3(showcase_geo, final 렌더 전).

## 1. 사실
- 사진 `diesel_road_2026_vladivostok_port_1992` = Commons "Russian tugboat in Vladivostok"(U.S. Navy, 1992-09-23, PD). 레지스트리 depicts `["블라디보스토크 항(금각만)", "예인선"]`, relevance "항구 전경". 실제 프레임은 예인선이 화면의 2/3, 항구는 뒤 띠. 문장은 "제재 유조선 레일라호는 … 울산을 떠나 블라디보스토크로 갔습니다" — 시청자는 예인선을 레일라호로 읽는다. 34년 전 자료사진을 2026년 사건에 붙인 것도 약하다(자료사진 표기만으로는 부족).
- diesel_road_2026 v2(기준 작품)에서 가져온 자산이다 — 그 영상의 문장("가장 가까운 러시아의 큰 항구")에서는 항구 전경 역할이었다. 문장이 바뀌면 사진의 역할도 다시 판정해야 한다.

## 2. 결정
1. **교체**: 우선순위 ① 블라디보스토크 항·유류 터미널(페르바야 레치카 등)·금각만 정박지가 **주된 피사체**인 권리 기록 가능 사진(Commons CC-BY/CC-BY-SA/PD, 2015년 이후 우선). ② 없으면 **사진 없이** 지도 카메라(블라디보스토크 핀 근접) + 위성 인셋(Sentinel-2/ESA, 권리 기록, UF-146 인셋 규칙) — 유조선이 간 "항구"는 위성으로 더 정직하게 보인다. 예인선 사진은 이 문장에서 뺀다(레지스트리에는 남긴다 — 항구 전경이 아니라 "예인선" 사진으로 depicts 정정).
2. 레지스트리 스키마: `depicts` 를 **`main_subject`(주된 피사체, 1~2개)와 `background`(배경)** 로 나눈다. 기존 항목은 구현 세션이 실제 프레임을 보고 나눠 적는다(이 영상·showcase_econ 에 쓰인 사진 전부).
3. 연출 photo 이벤트는 `for: <문장 대상 용어>` 를 적는다(P8 — LLM 이 고른 이유). 검사 **`[photo-subject-background]` hard**: `for` 가 main_subject 에 없고 background 에만 있으면 실패. `for` 가 어디에도 없으면 `[photo-subject-unmatched]` hard.
4. **`[photo-age]` warning**: 문장 날짜 − 사진 촬영일 > `media.photo_age_max_years`(감독 제안 15, 사용자 합격 값 아님)이면 경고 + 연출에 `age_reason`(예: "현존 사진 없음·건물 외관 불변")이 있어야 통과. 역사 장르(전쟁사·미술사)는 장르 프로필에서 끔.
5. UF-201 guards = 검사 둘 + 레지스트리 스키마 테스트. 교체 뒤 그 문장 프레임 1장을 R 에.

## 3. 순서
D-0326 → 이것 → 사용자 게이트 ② 답 → final.
