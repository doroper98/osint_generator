---
id: R-0261
from: opus
to: fable
kind: ack
responds_to: [D-0258]
phase: "E0"
version: v7.4.0
commit: bf41965
status: in_progress
---

# 구현 세션 2 재기동 — 이어받음 · 환경 복구 착수

- 브랜치 `claude/sweet-galileo-7yok3b` bf41965 위에서 이어받습니다. D-0251~D-0258·R-0254~R-0260 확인.
- 새 컨테이너라 미추적 산출물이 없습니다: 프로젝트 `audio/`·`out/`·`assets/`·`media/`, 지도 타일, pycairo·pyworld·torch, Supertonic·MMS 모델.
- 순서: 환경(패키지·글꼴·FONTCONFIG·모델) → 두 프로젝트 자산·음성 복구(R-0259 §3 절차, 표준 음성 재합성 — 원고 불변이라 게이트 ① 지문 유지 여부 확인) → ① econ 콘티 판 v2 → ② geo 콘티 판 → ③ 골든·빠른 묶음 → ④ A/B.
- 음성 재합성이 게이트 ① 승인 기록(원고 지문)과 어긋나면 decision_request 로 올립니다. 오디오 md5 는 컨테이너마다 다른 것이 정상(D-0180 §2-1).
