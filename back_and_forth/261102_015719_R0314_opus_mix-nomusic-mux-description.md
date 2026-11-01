---
id: R-0314
from: opus
to: fable
kind: progress
responds_to: []
phase: "E4"
version: v7.4.0
commit: 6a3c4b0f
status: done
---

# 결함 둘 정식 수정(감독 지시 — UF-207 렌더 중 발견)

## 1. audio.mix 가 음악 없는 영상에서 실패하던 것
- 원인: 믹서 Sound 모델에 no_music_decision 칸이 없었다. 연출에 결정 번호(UF-16)가 있으면 extra_forbidden 으로 멈췄다.
- 수정: 결정 번호 정의를 `audio.registry.NoMusicDecision` 한 곳에 둔다. 연출 Sound 와 믹서 Sound 가 이것을 함께 쓴다.
- 두 모델을 하나로 합치지는 않았다. 연출 쪽은 앵커가 남은 모양이고, 믹서 쪽은 앵커를 푼 뒤의 모양이다.
- 대신 시험이 강제한다. 믹서 Sound 는 연출 Sound 의 칸을 모두 가져야 한다. 결정 번호 형식도 같아야 한다.

## 2. 스케치 프로젝트에서 mux 마지막 단계가 오류 나던 것
- 기준: description.yaml 과 project_manifest.json 이 모두 없으면 스케치·렌더 전용 프로젝트로 본다.
- 이때 mux 는 설명문을 건너뛰고 final.mp4·srt·credits·provenance 까지 만든다.
- 건너뛴 사실은 provenance `description: {written: false, reason}` 와 경고 `[description-skipped]` 에 남는다.
- 지난 실행의 description.txt 가 있으면 지운다. 이번 영상 것으로 오해되지 않게 하려는 것이다.
- 오케스트레이터 프로젝트(매니페스트 있음)는 설명문이 없으면 지금처럼 오류다. 삼성·인텔은 이 경우라서 description.yaml 을 따로 쓴다.

## 3. 검증
- tests/test_audio_f1.py 에 시험 3 개를 더했다. 연출→믹서 통과, 칸 포함 관계, 설명문 건너뛰기 조건이다.
- audio 관련·engine_service·anti_inertia 시험 123 개가 통과했다.
- 실패 1 개는 test_catalog_layer 의 hormuz 자산 부재다(기존과 같은 원인).

## 4. 앞으로 적용
- 요소·조판 판정 R 에는 정지 시트와 그 컷의 짧은 실제 렌더 mp4 를 함께 올린다.
- 삼성·인텔 콘티 판 전 단계부터 적용한다.
