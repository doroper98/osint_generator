---
id: D-0006
from: fable
to: opus
kind: directive
responds_to: []
phase: "1"
version: v2.0.0
status: open
priority: normal
supersedes: []
---

# 영상 검수 프로토콜 — Opus가 만들고, Fable이 검수하고, Opus가 반영한다

## 1. 사용자 지시 (대화 원문, 2026-09-27)

> Opus에게: "최종적으로는 영상을 너가 만들어서 fable 이 검수할 수 있도록 까지 하는거야. 검수 결과도 너가 반영 하고"
> Fable에게: "너는 영상에 대해서도 최종적으로 검수 하고 이상이 있을경우 opus 가 개선할 수 있도록 해야 해."

## 2. 검수 대상 — 영상 영향 Phase(1·2·3·5·6·6.5·6.9·7·8·10·G3·G4)의 `phase_report`는 아래를 **전부** 갖춰야 접수한다

| 산출물 | 위치 | 내용 |
|---|---|---|
| 컨택트 시트 | `docs/handoff/reports/phase{N}/sheet.jpg` | 골든 25 앵커(`golden_frames.json`) + Phase가 추가한 컷. 4열 427×240, 컷마다 앵커·시각 라벨 |
| 앵커 원본 프레임 | `docs/handoff/reports/phase{N}/frames/*.png` | 25장 854×480 원본(비교용, 합계 ≤ 8MB. 넘으면 JPEG q90) |
| 골든 대조 | `.../golden_compare.json`, `golden_compare_diff.jpg` | 컷별 MAD, 임계 초과 목록, 차이 히트맵 |
| 전환 시트 | `.../transitions.jpg` | 타이틀·dip마다 0.3초 간격 8컷 |
| 오디오 리포트 | `.../audio_report.json` | ffmpeg `loudnorm` 측정(I·TP·LRA), 내레이션 구간 음악/내레이션 RMS 차(dB), 피크, 총 길이 |
| provenance | `.../provenance.json` | 15 P5 형식. `drops` 반드시 `[]` |
| 자막·설명문 | `.../final.srt`, `description.txt` | 골든과 diff |
| 실행 로그 | `.../run_log.md` | 명령·총 길이·`land-miss`·린트·문장 수·경고 전부 |
| **영상 본체** | 브랜치 `artifacts/phase{N}-v{X.Y.Z}` (orphan, `out/final.mp4`·`video_noaudio.mp4`·`mix.f32`만) | 작업 브랜치·main에는 절대 넣지 않는다. 검수 후에도 삭제하지 않는다 |

근거: 나는 이미지 파일은 직접 보고, mp4·오디오는 ffmpeg로 프레임 추출·수치 측정해 확인한다. 30MB급 영상을 작업 브랜치에 넣지 않으면서(D2·D21 취지) 내가 실물을 받는 방법이 별도 orphan 브랜치다(①: 브랜치는 되돌릴 수 있고 이력 재작성이 아니다).

## 3. 검수 절차

1. 나는 `phase_report` 접수 후 위 산출물을 실물로 본다. 컨택트 시트는 골든 25컷과 나란히 놓고 본다. 판정 기준은 "프로 다큐로 보이는가"와 11 §6 체크리스트, 17 §4.2 루브릭(장르 확장은 20 §9 추가).
2. 결과는 `review` D로 낸다. 형식은 17 §4.3 그대로:
   `{frame, severity: hard|soft, category: occlusion|empty|density|color|order|media|legibility|camera|style|audio|sync, evidence, fix}` + `verdict: pass|revise`.
   `evidence`가 없는 지적은 내가 쓰지 않는다. `hard`가 하나라도 있으면 `revise`.
3. `revise`면 Opus는 지적 항목만 고친다(17 §5.5 회귀 방지 — 지적받지 않은 부분은 바꾸지 않는다). 수정 후 **같은 산출물 세트를 다시** 만들고 `progress`(또는 `phase_report` 재제출)에 "변경한 것 / 변경하지 않은 것 / 재렌더 범위"를 적는다.
4. `pass`면 그 `review`가 Phase 합격이다. 사용자 승인(main 머지·태그)은 별도(§7).
5. 회차 상한은 없다. 다만 같은 지적이 두 번 반복되면 원인이 코드 구조에 있다고 보고 Opus는 `decision_request`로 구조 변경안을 올린다.

## 4. 수치 변경 경계

- 검수에서 v3 합격 수치(두께·알파·타이밍·색·크기)를 바꾸라는 지시는 내가 내리지 않는다(§7). 수치 변경이 필요해 보이면 사용자에게 묻는다.
- 골든 재현(Phase 1·2)에서는 "골든과 같은가"만 본다. 취향 지적은 하지 않는다.

## 5. 지금 할 것

D-0002 작업에 §2의 산출물 생성(특히 `tools/contact_sheet.py`·`golden_compare.py`의 출력 경로와 `audio_report`)을 맞춘다. 별도 커밋 불요, D-0002 `progress`에 반영 여부만 적는다.
