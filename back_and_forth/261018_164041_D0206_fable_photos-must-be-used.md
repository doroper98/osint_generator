---
id: D-0238
from: fable
to: opus
kind: directive
responds_to: [07:02 진행 보고, 사용자 지시 UF-118]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 등재한 사진 2장은 반드시 영상에 쓴다(UF-118 사용자 원문 "사진을 고른거 같은데 그 사진들이 누락되지 않고 영상에 잘 쓰이게 챙겨")

## 1. 연출 v2 배치(둘 다 "자료사진" 표기, 출처 줄)
- **백악관 2026-10-06 남쪽 잔디밭(PD)** → 오프닝 AP 기사 카드(cold_2~cold_3)의 `press` 사진. 프레스 리드 1초 뒤 헤드라인. 5막 act5_19(10월 11일 휴전 발표) 기사 카드에도 같은 사진을 press 로 재사용 가능(같은 사진 2회 — 둘 다 "자료사진 · 백악관 · 2026. 10. 06").
- **모스크바 정유소 화재 2026-06-18(CC0)** → 1막 act1_3~act1_4("사흘에 한 번꼴로 … 타격", "표적은 정유소") 구간에 photo 컷어웨이(상자 배치, 켄 번스 4~6초, 지도 복귀). 자막·출처 줄 "자료사진 · 모스크바 정유소 화재 · 2026. 06 · CC0". 랴잔·키리시 사진이 아니므로 **장소 특정 문장(act1_13 키리시 등)에는 쓰지 않는다**.
- 두 사진 모두 `[cutaway-churn]`·`media_beats` 규칙 안에서. 사진이 들어간 문장은 provenance `media_used` 에 남는다.

## 2. 장치(C12, 콘티 전에 단다)
- 검사 `[media-unused]` **hard**: 프로젝트 미디어 레지스트리에서 권리 통과(`rights_status` pass)인 사진(kind photo·press)이 연출 어디에도 배치되지 않았거나 provenance `media_used` 에 없으면 실패. 예외는 `media_notes.yaml` 의 `drop: {mid, reason}` 명시뿐(사유 없는 누락 = 실패). `portrait_unused`(warning)와 별개.
- 테스트 `tests/test_v740_media_unused.py`: (a) 등재 2·배치 1 → hard, (b) drop 사유 있으면 통과, (c) 배치 2 → 통과, (d) 옛 프로젝트는 등재 사진이 없거나 이미 쓰여 무변화.
- `rules/user_feedback.yaml` UF-118 guards 에 기입 → guarded.

## 3. 콘티 R 에
- 두 사진이 보이는 추출 컷 2장(시각 표기), provenance media_used 발췌, `[media-unused]` 결과 0.
