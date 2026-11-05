---
id: D-0355
from: fable
to: opus
kind: directive
responds_to: [war D-0633, UF-267]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 지침 — gate packet 을 sweet-galileo 에 먼저 만든다(사용자 게이트 승인은 감독 세션에서 기록, UF-267)

## 배경
- 전쟁사 트랙에서 사용자 게이트 승인(UF-265)을 감독 세션이 받고 기록을 구현 세션에 맡겼다. 구현 세션 권한 장치가 Self-Approval 로 막아 약 7시간 멈췄다.
- 사용자 원문 UF-266 "영상 내놔", UF-267 "내가 너한테만 교신하면 되는데 왜 이렇게 됐지? 재발 방지해".
- 규칙(README §9 "게이트 승인 기록 자리", 이 커밋에서 sweet-galileo 에도 넣음): 사용자 게이트 승인은 감독 세션에서 approve 로 기록한다. 구현 세션은 pull 해서 진행만 한다.
- 그런데 감독 컨테이너에는 `projects/{pid}/out/` 이 없다(.gitignore). 지금 approve 는 out/animatic_provenance.json 을 읽는 require_animatic 때문에 감독 쪽에서 못 돈다.
- 쇼케이스 게이트 ② 재승인, 삼성·인텔 게이트 ① 이 사용자 답 대기다. 답이 오면 이 감독 세션이 바로 기록해야 한다. 그래서 전쟁사(칸나이 완성본 렌더 중)보다 먼저 여기서 만든다. 전쟁사는 이 커밋을 가져간다(따로 만들지 않는다).

## 할 일(명세는 war D-0633 §3 과 같다)
1. **gate packet**: 게이트 자료를 올릴 때 승인 검사 입력을 git 추적 파일 `projects/{pid}/gate_packet.json` 으로 둔다(schema_version 1, Pydantic 모델, schemas/models.py).
   - 담을 것: 콘티 판 provenance 요지(total_sec·원고 sha1·만든 시각), plan 길이, 원고 sha1, 자산 승격 상태(pending 초상·휘장 수), 만든 세션·커밋.
   - 원천 파일 지문(sha1)을 담아 바꿔치기를 막는다.
   - 게이트 ① 용(원고 지문)과 게이트 ② 용(콘티 판 기록)을 같은 파일의 구역으로 둔다.
2. **approve 경로**: out/ 가 없는 작업 트리에서는 require_animatic·require_asset_library(·게이트 ① 원고 지문 확인)가 gate packet 을 읽어 같은 판정을 한다. packet 이 없거나 지문이 어긋나면 거부한다. 우회 플래그 없음. out/ 이 있으면 지금처럼 out/ 로 판정한다.
3. **진행 경로**: 구현 세션은 pull 한 project_manifest.json 의 승인 기록을 보고 진행한다.
4. **시험**: (가) out/ 없는 임시 작업 트리에서 packet 으로 게이트 ② 승인이 기록된다 (나) packet 지문이 어긋나면 거부 (다) packet 의 원고 sha1 이 현재 원고와 다르면 거부 (라) 기존 out/ 경로 판정 불변 (마) 게이트 ① 도 packet 으로 기록된다.
5. 단독 커밋으로 만들고(DECISIONS·README 는 감독이 쓴다), 해시를 알린다.
6. 이어서 지금 대기 중인 세 프로젝트의 packet 을 만들어 push 한다: showcase_geo(현재 연출 A′ 기준 — 2막 도입 사용자 선택 뒤 다시 만든다)·showcase_econ(v3)·samsung_q3_2026·intel_q3_2026(게이트 ① 용 — 원고는 경제 브랜치에 있으니 econ 구현 4 가 그 브랜치에서 만든다).

## 하지 않는 것
- 구현 세션 권한 규칙에 approve 허용을 넣지 않는다.
- 감독이 사용자 원문 없이 approve 를 실행하는 길을 만들지 않는다. approve 의 `--by`·`--comment` 에 사용자 원문과 UF 번호가 들어가야 한다.
