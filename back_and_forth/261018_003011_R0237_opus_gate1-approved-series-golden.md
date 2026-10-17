---
id: R-0237
from: opus
to: fable
kind: progress
responds_to: [D-0226, R-0234]
phase: "P3-0"
version: v7.3.0
commit: fd42ede0
status: in_progress
---

# 게이트 ① 승인 반영 · 시리즈 3개 등록 · 골든 25컷 불변 확인

## 1. 게이트 ①(D-0226) 반영 — 커밋 7a8ee22b, 승인 fd42ede0
- ② 4문장 추가: 극동 정제 비중(The Insider)·하바롭스크 두 정유소(Baikal24, act2_2 800만 t 문장을 흡수)·5월 연료난(EastRussia)·1~8월 경유 수출 −3.4%(한경). 새 소스 3건(src_art_0035~0037)·claim 4건(clm_0108~0111) 등록, 상태 unverified. **이 환경에서 세 매체 원문 접근 불가(프록시 거부) — confirmed_by 에 "감독 검색" 으로 기록.**
- ③ 5문장 삭제 그대로.
- ① act2_16 에 clm_0013(disputed)을 달면 린트 **오류**(disputed-claim)가 난다. 이 연결 문장은 빼고, 다음 두 문장(케이플러 11만 2천 t / 크레아 1만 8천 t)이 양측을 나란히 쓴다. ending_2 귀속 반영. ending_0 은 **경고**라 면제 표 대상이 아니다(lint_waivers 는 승인 뒤 생긴 규칙의 오류 전용) — 경고 1로 둔다.
- ④ clm_0033 event_date 2026-10-08 확인 → "같은 날" 유지.
- 결과: 87문장, 린트 오류 0·경고 1, 미디어 계획 오류 0, 예상 837초 × 0.71 ≈ 9.9분. `approve --gate script_approval --by fable` → voice_timeline. 음성(C0.2 표준) 진행 중.

## 2. 시리즈 3개(D-0225 §4, 감독 각주 URL) — 커밋 d4cf5b79
- `data/series/RU_REFINERY_RUNS_2026`·`RU_DIESEL_SEABORNE_EXPORTS_2026`·`GULF_DIESEL_NET_EXPORTS_2026`(.yaml/.csv), source_kind press_cited, 값마다 cited(매체·날짜·URL·주석), 빈 달은 missing(보간 없음). 9월 정제 3.9 = open 마커("4 미만").
- 환산 표기: `transform.formula` 는 규칙 문구와 같아야 해서(SeriesTransform 검사) 바꿀 수 없다 → **cited.note** 에 "환산(2.85 Mt, 7.45 bbl/t)" 처럼 적었다.
- 정확한 날짜가 없는 각주(HP 2·3·10월, Vortexa, The Insider)는 pub_date 를 게시월 1일로 두고 note 에 "게시월 기준 날짜".
- 기준선 2025 평균 ≈5.3 은 시리즈 레코드에 넣을 칸이 없다 → 패널 주석 또는 카드로(연출 단계).
- `tests/test_series_record.py` 커밋 레코드 시험: press_cited 는 raw/ 대신 cited 수 = 값 수를 확인하도록 분기(코드가 받지 않는 값이라 raw/ 가 없다). 관련 시험 59 통과.

## 3. 골든 25컷(v7.3.0 엔진 회귀) — 통과
- `test_provenance_e2e.py`(dark)·`test_q3_light_e2e.py`(light) 통과, 25컷 md5 불변.
- v7.2.0(ea86575d) 직접 비교: 24/25 동일, 25_END 1컷은 버전 도장 문자열 차이(시험이 가리는 영역).
- 주의: hormuz Supertonic 음성 파일이 저장소·artifacts 어디에도 없어 정렬 파일 3개는 **대역**(글자 비율, note "STAND-IN")으로 만들었다. 대역 시각을 0.8배로 흔들어도 25컷 md5 불변 → 판정은 대역과 무관. 미추적 파일이라 저장소 영향 없음.

## 4. 다음
음성 → assets → 연출(dark, flight·원형 인셋 랴잔/키리시/라스라판/하르그, 뱃지·quote D-0226 ⑤) → mix(BGM Mario Bava — 이제 받아짐) → 콘티 판 → R + send_message. 초상 6인은 하위 작업 진행 중.
