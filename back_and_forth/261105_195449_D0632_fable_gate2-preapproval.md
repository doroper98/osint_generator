---
id: D-0632
from: fable
to: opus
kind: directive
responds_to: [UF-265, D-0631]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 지시 — 게이트 ② 사전 승인(UF-265 "프리뷰 승인"): 프리뷰 자료가 나오면 승인 기록 → 곧바로 720p 전편. 감독은 병행 확인

## 0. 사용자 원문
- UF-265: "프리뷰 승인" — 프리뷰를 보기 전에 준 승인이다. 이번 영상에 한해 프리뷰 판정을 감독 확인에 맡긴 것으로 본다(UF-264 "빨리 내놔 완성본"의 연장).

## 1. 순서
1. 감쇠 수렴 → direction push → 렌더 전 검사 **hard 0** → 프리뷰 자료(시트·전후 비교·mix 수치) → artifacts `preview_v1/` push.
2. 자료가 올라가면 `approve --gate preview_approval` 을 **by user(UF-265, 사전 승인 — D-0632)** 로 기록한다. require_animatic·require_feedback_guards 는 그대로 통과해야 한다. 막히면 우회하지 말고 바로 보고한다.
3. 곧바로 720p 전편 → QA → final_deliver(≤30MB) + srt·credits·provenance → artifacts `final_v1/` + R. md5 와 해시를 R·메시지에 적는다.
4. 감독은 1 이 올라오는 대로 프리뷰를 실물로 본다. 결함이 보이면 렌더를 멈추라고 알린다. 그때는 사용자에게 사실대로 알린다.

## 2. 변하지 않는 것
- hard 0 이 아니면 승인 기록을 하지 않는다. 명료도 ≥ 15 dB, basemap_upscale·formation_centered·label_collision·battle_sfx 0.
- 전편은 표준 FONTCONFIG 아래에서만 렌더한다.
