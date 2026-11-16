---
id: D-0358
from: fable
to: opus
kind: decision
responds_to: [R-0325, D-0357]
phase: "E0"
version: v7.4.0
status: open
priority: high
---

# 결정 — showcase_econ 새 hard 13 은 A(연출을 고친 뒤 재승인 자료로)

## 판정
- **A 로 간다.** 승인받는 판이 본편이 되는 판이어야 한다(D366 과 같은 원칙). v3 로 묻고 나중에 고치는 B 는 쓰지 않는다.
- geo 실측(R-0325 §2)은 수락한다. 감독이 전후 프레임(artifacts 48dab273 `d0357_basemap/basemap_before_after.jpg`)을 실물로 봤다. 105초·175초 지형이 선명해졌고 라벨·경로는 그대로다.

## 1. econ 고칠 것(연출만)
1. [spoken-number-visible] 8건: 그 문장이 말하는 숫자를 그 문장 동안 데이터 무대 라벨로 보인다.
   - 숫자는 원고·claims 의 출처 값 그대로 쓴다. 새 숫자를 만들지 않는다.
   - 증감(0.25%p)은 '−0.25%p' 처럼 방향을 붙인다. 방향은 원고 문장과 같아야 한다.
   - ending_0 의 4% 두 번은 같은 라벨 하나로 덮어도 된다. 검사가 통과하는지로 판정한다.
2. [backdrop-subject-unmatched] 5건: 배경 사진마다 장면 주제 for 를 적는다. 레지스트리 main_subject/background 와 맞춘다.
3. **원고(script.yaml)는 바꾸지 않는다.** 게이트 ① packet 이 그대로 유효해야 한다. 원고를 바꿔야만 풀리는 건이 있으면 멈추고 decision_request 로 올린다.

## 2. 순서
1. 고친다 → 프리뷰 렌더 전 검사 hard 0.
2. 콘티 판 v4 → gate packet 재생성(②구역 포함) → artifacts.
3. R 보고: 바뀐 장면 전후 프레임, 검사 수, packet digest, 콘티 판 길이.

## 3. geo
- 남은 hard 는 [media-density] 하나다. 2막 도입 사용자 답(R-0321)을 기다린다. 답이 오면 감독이 알린다.
- 답 뒤 콘티 판 v4 를 만들 때 지도 티어 변경(d6df558f)이 같이 들어간다. 전후 프레임은 재승인 자료에 넣는다.

## 4. 금지
- 검사 면제·문턱 조정 금지. 숫자 라벨을 화면 밖이나 1프레임만 띄워 검사만 넘기는 연출 금지.
