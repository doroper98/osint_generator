<!--
tier: 3
last_synced_with: v2.1.0
ssot_for: [pending-release-tags]
depends_on: [back_and_forth/README.md]
last_review: 2026-09-27
-->

# 원격에 올릴 태그 목록 (append-only)

두 세션(Fable·Opus) 컨테이너는 태그 푸시가 403으로 막혀 있다. Phase pass마다 여기에 한 줄을 남긴다.
사용자가 PC에서 원할 때: `git fetch origin && git tag -a <tag> <commit> -m "<tag>: <요지>" && git push origin <tag>`.
올리지 않아도 진행에는 영향이 없다(버전은 VERSION 파일과 커밋 prefix로 추적된다).

| 태그 | 커밋 | 요지 | 원격 상태 |
|---|---|---|---|
| v2.0.1 | 5afbdc6 | Phase 1 골든 재현 합격 | 미푸시 |
| v2.1.0 | 5728df3 | Phase 2 모듈 분해·계약 합격 | 푸시됨(사용자 릴리스) |
| v2.2.0 | c6ea757 | Phase 3 지오 일반화 합격 (D-0020) | 미푸시 |
| v2.3.0 | 706e982 | Phase 4 원고·음성 합격 (D-0028) | 미푸시 |
| v2.4.0 | e7893a8 | Phase 5 뱃지·엔티티·권리 합격 (D-0031) | 미푸시 |
| v2.5.0 | 205df59 | Phase 6 패널·카드 데이터화 합격 (D-0035) | 미푸시 |
| v2.5.5 | d8150e5 | Phase 6.5 사진·영상·컷아웃·기사 합격 (D-0039) | 미푸시 |
| v3.0.0 | 4bd56fd | Phase 6.8 오케스트레이터 통합 합격 (D-0046) — MAJOR: manifest schema_version 2 | 미푸시 |
