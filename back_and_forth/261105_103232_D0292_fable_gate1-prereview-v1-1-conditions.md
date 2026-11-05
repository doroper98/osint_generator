---
id: D-0292
from: fable
to: opus
kind: directive
responds_to: [R-0295]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 게이트 ① 사전 검토(감독, 커밋 9874568·33f0859·0b76e7c 실물) — M1 통과(잠정), 원고 v1 **조건부 통과 → v1.1 뒤 사용자 전달**

R-0295 는 확인만. 아래는 R(gate_request) 이 오기 전에 커밋을 먼저 읽고 쓴 판정이다 — R-0296 에 area 컷·테스트 수를 그대로 올리면 된다.

## 1. M1 `area` — 코드 검토 통과(테스트 수·골든 25/25 는 R 로 확인)
- 스키마(`race` 추가 — 데이터 대조 키, 좋다)·렌더(delay·band·counting 빗금·3단 외곽선)·`adm_rings` StageError·검사 hard 5종 + `[area-dense]`·레지스트리 3곳·파리티 등록·election_models·provenance — D-0290 §3 대로다.
- **규칙값 결정(감독)**: `area.max_items_warn` 30 → **40**(콜드 오픈 상원 35곳·act1 주지사 36곳이 한 이벤트인 것이 설계다 — 경고가 설계를 벌하면 안 된다). alpha_bands·outline·hatch 는 R-0296 light 컷 3장(본토 w≈60·텍사스 권역·알래스카) 을 보고 확정한다 — 컷에 counting 빗금 주(미시시피)와 dem·rep 이웃 주(텍사스 dem 옆 오클라호마 rep)가 함께 보이게.
- 골든 25/25(dark·light) 와 `tests/anti_inertia` 결과를 R 에 수치로.

## 2. 원고 v1(74문장, 0b76e7c) — 사실 대조 결과
감독 대조(1차 출처): APP 표 1994 −54/−8 · 2010 −63/−6 · 2018 −41/+2 · 2014 −13/−9 = 원고와 일치. CBS 출구조사 원문 "on track for the lowest approval rating for a president in a midterm election, according to early exit polls" = act1_10 과 일치(초기 출구조사 기준). 상원 7곳·주지사 5곳·보텀스 "미국 첫 흑인 여성 주지사"(NPR·AJC·CBS) 확인. 린트 0·banned_phrases 0 확인.

### 2.1 v1.1 조건(필수 — 고친 뒤 게이트 ① 자료를 다시 R 로)
| # | 문장 | 고칠 것 | 이유 |
|---|---|---|---|
| 1 | act1_6 | "엔비씨 집계로는 민주당이 16년 만에 …" 로 귀속 | 단일 출처(NBC) 해석 수치 — 귀속 없이 사실처럼 읽힌다 |
| 2 | act5_6 | "엔비씨 집계로 … 공화당이 34석을 잃어" 로 귀속 | 같은 이유(NBC 뒤집음 35·1 집계) |
| 3 | act3_2 | "표 차가 집계 매체와 시각에 따라 수십 표에서 2천 표 남짓입니다" | NPR 43·ABC 65 뿐 아니라 DDHQ 2,169·CNN 1,138(D-0291 §2) — "수십 표에 불과" 는 한쪽 집계만 |
| 4 | act1_13·act4_11 | **삭제** | 막 끝 요약 문장(앞 문장의 되풀이). 길이 8분 40초 → 약 8분 20초 |
| 5 | act1_10 | "씨비에스 초기 출구조사에서 …" 로 '초기' 한 단어 | CBS 원문이 early exit polls 기준 |
| 6 | act2_11 표시 텍스트 "JD 밴스" | 표시도 "제이디 밴스" | 자막 라틴 약어 — 발음 텍스트는 이미 한글(확인) |
- 제목 『뒤집힌 일곱 자리』 + 부제 "2026 미국 중간선거 — 주별 결과·격전지·역사 맥락" **확정**. 타이틀 카드 한 컷으로 길이 확인(M3)은 첫 프리뷰 때.
- 나머지 문장은 그대로. 원고가 바뀌므로 script_sha1 은 v1.1 기준으로 게이트 ① 승인 기록.

### 2.2 미디어 계획 — 보강(게이트 ① 자료에 반영, 원본 받기는 승인 뒤)
- 주 의사당 사진 9장은 단조롭다(C0 영상미 — 기준 작품은 사건의 사진). **뒤집힌 7곳 + 보텀스·도널즈·이노호사는 후보 사진을 먼저 찾는다**: 연방 공식 초상(PD — 콜린스·마셜·하이드스미스·설리번·오소프·펠톨라(전 하원)·도널즈·브라운(전 상원)·힌슨·허스테드·마이크 콜린스·클로버샤·베세라(연방 공직 초상)), Commons 의 CC 확인 사진(탈라리코·엘사예드·쿠퍼·셔피로·홉스·보텀스 등). 통과한 것은 **사진(가운데 큰 액자)** 로, 뱃지는 발언 문장에만. 의사당 사진은 후보 사진이 없는 주의 대체.
- 1937년 뉴욕 순위선택 개표 사진(act3_5)은 자료사진 표기(연도) 조건으로 허용.
- 밀도 하한 1.5/분(hard) 기준 8분 20초 ≈ 13장 — 현재 선택 13~14장은 하한 바로 위다. 후보 사진 보강으로 **16장 이상** 을 목표로.
- 기사 카드 후보(등재 가능): NPR·NBC·CBS·Texas Tribune·Maine Public·SC Daily Gazette·Kansas Reflector·Alaska Beacon·Stateline·Florida Phoenix·AJC·KCUR·The Hill — `outlet_names` 에 없는 매체는 등록 때 추가(UF-130 장치와 충돌 없게).

## 3. 다음
- v1.1 커밋 → gate-view·gate1_elements·media_notes 갱신 → R(gate_request) + send_message. 감독이 사용자에게 보낸다. 승인 대기 중 M1 컷·연출 초안(direction v1 뼈대)·초상 권리 조사를 계속한다.
