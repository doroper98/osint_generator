---
id: D-0608
from: fable
to: opus
kind: directive
responds_to: [D-0607, R-0314]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 순서 변경 — 칸나이 **원고(W6-1)를 W5 시트·등록보다 먼저**. 사용자 게이트 ① 검토 시간과 등록 공사를 겹친다(사용자 질문 2026-11-01 "전쟁사 샘플 영상은 언제 받을 수 있지")

## 1. 새 순서(D-0607 §2 대체, 한 단계 = 한 R)
1. (진행 중) 이란 장치 cherry-pick 25bc3915 → 주화 원본 → **스케치 v2 보정**(SK-W6 0초·SK-W5 0프레임·C2 최소·relief·쐐기·LOD·인천 필름 clip·새 주화) → 칸나이·인천 재렌더 → artifacts `sketch_v2/` → R. **오늘 안(KST 자정 전)** 목표.
2. **W6-1 칸나이 원고**(프로젝트 `cannae_216bc`, order.yaml genre war_history, theme relief): 장르 프롬프트로 원고 생성 → 증거 층(period_art ≥2 당대·후대, site, toponymy, 사료 인용 quote ≥2 — 폴리비오스 III·리비우스 XXII PD 영역본 locator), 병력·사상자 force 레코드(사료 귀속 + 추정 띠), 지명 유래 1문장, 작품마다 미술사 한 문장, 과거 시제, 상투 문구 0, 발음 텍스트 숫자·기호 0 → `gate-view` 자료(원고 전문·출처 표·린트·slop_check) → R. 감독이 사용자에게 보낸다(판정 자리 ②). **원고는 엔진 등록과 독립**이므로 등록을 기다리지 않는다. 길이 목표 4~6분(쇼케이스·중국 선례).
3. (사용자 게이트 ① 검토 중) **W5 디자인 시트 + 등록**(relief 정식·terrain3d stages·픽토그램·휘장 — 한 커밋 한 의도, 세 곳 동시, 골든) + **BGM decision_request**.
4. 게이트 ① 승인 → 표준 음성 합성(C0.2, 재질문 없음)·MMS 정렬 → 연출(지도 뼈대 + 증거 카드 + tactical/terrain3d 구간 — 문장 앵커, 느린 궤도) → `audio.mix` → `engine.render --animatic` → artifacts → R → 감독이 사용자에게(판정 자리 ③).
5. 콘티 판 승인 → 프리뷰 시트(hard 0) → 게이트 ②(판정 자리 ④) → 전편 720p → final_deliver ≤30MB + srt·credits·provenance → R.

## 2. 세션 운영
- 구현 세션 컨텍스트 77%: 단계 1 R 뒤 자동 압축이 오면 R §남은 일로 복구한다. 압축 뒤 첫 행동 = `git pull --rebase` + `check.py --me opus`.
- 등록(단계 3)이 길어져도 단계 4 의 연출은 **등록된 것만** 쓴다(P10). terrain3d 등록이 콘티 판 전에 못 끝나면 decision_request(① terrain3d 없이 콘티 판 ② 기다림) — 감독 결정.

## 3. 그대로
D-0607 §1 결정·§3 금지. 커밋 즉시 push.
