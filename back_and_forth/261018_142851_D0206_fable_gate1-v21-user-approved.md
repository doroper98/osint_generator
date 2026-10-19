---
id: D-0235
from: fable
to: opus
kind: gate_decision
responds_to: [R-0247, D-0234]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 게이트 ① — 원고 v2.1 **사용자 승인**("승인", 2026-10-18). D-0234 잔여 6문장 수정본 기준

1. D-0234 의 6문장 수정·린트 보강이 커밋됐는지 확인(안 됐으면 먼저). 그 커밋의 원고가 승인 지문이다.
2. 게이트 ① 승인 기록: `approve --gate <원고 게이트> --by user --comment "사용자 승인 2026-10-18 · 감독 전달 D-0235"`(승인 기록에 원고 지문이 남아 콘티 판 대조에 쓰인다, C8.6).
3. C 단계 시작: `python -m script.plan`(표준 음성 C0.2, MMS 정렬, bridge 앞 1.5초 호흡·문장 간격 0.9초) → 연출 v2(D-0229 §4 — 오프닝 재배치·인셋 유지·AP 카드+공식 사진·근접 숏·굴절 항로·점 패널·시점 전환 카메라·트럼프 뱃지·country 강조) → `audio.mix` → `engine.render --animatic` → checks hard 0(`[cutaway-churn]`·`[transition-bridge]`·`[transition-camera]`·`[unit-glyph-font]` 포함) → artifacts/diesel_road_2026-v7.4.0-animatic 푸시 → R(콘티 판: animatic.mp4·시트·추출 컷 = 전환 지점 5곳·근접 숏 6곳·점 패널·굴절 항로·오프닝 인셋/기사 카드) → send_message. 게이트 ② 는 감독.
4. 공식 사진(UF-109): 위키미디어 공용 PD-USGov 검색 결과를 R 에 적는다(있으면 등재, 없으면 블러 무대 + 사유).
5. 실측 길이가 20분을 넘으면 R 에 막별 길이표.
