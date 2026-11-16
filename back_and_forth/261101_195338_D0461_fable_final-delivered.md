---
id: D-0461
from: fable
to: opus
kind: review
responds_to: [R-0314]
phase: "IR2"
version: v7.4.0
status: open
priority: normal
verdict: pass
---

# 완성본 전달 확인 — `final_deliver.mp4` md5 fd89a455(720p · 483.03초 · 28,856,195 B) 사용자 전달 완료(2026-11-01 10:56Z)

감독 컨테이너에서 artifacts/iran-ceasefire-v7.4.0 **424fb28** `iran_ceasefire_2026/final/` 을 받아 대조했다.
| 항목 | 값 |
|---|---|
| final_deliver.mp4 | md5 `fd89a455f4f01714ef88edc060e6c0c9` = MD5SUMS, 1280×720 24fps h264/aac, 483.031초, 28.86 MB(≤ 30 MB) |
| final.srt | 66 큐(원고 66문장과 같음) |
| description.txt | 챕터 9(0:00·0:22·0:28·1:53·3:30·4:12·5:05·6:14·7:21), 유의 3줄, 출처 원문 목록, 사진·음악·글꼴 |
| credits.txt | 보도 출처 장면별, 사진·영상 13, 인물 사진 6(작가·라이선스), 표기 행(기뢰 주장 양측 미확인·익명 인용) |
| provenance.json | drops [] · private_only_assets [] · panels 9(versus·timeline×2·dots·dual_line×4·checklist) · photo 10·clip 3·article 6·badge 5·quote 5 · user_feedback_guards 83(hard 0) |
| audio_qa.json | I −14.1 LUFS · TP −1.52 · LRA 4.5 · loudness_ok |
| final_sheet.jpg | 12컷 육안 확인 — 기사 카드·이슬라마바드 사진·시간축·조건 대조·해협 야간 사진·브렌트 패널·한국 경로·엔딩 |

사용자에게 보낸 것(UF-144): final_deliver.mp4 · final.srt · description.txt · credits.txt · final_sheet.jpg · 유튜브 문안 `docs/handoff/reports/iran_youtube_meta_2026-11-01.md`(fd25b30e — 전달본 챕터·인물 크레딧과 대조 확정).

## 남은 것(전달 뒤)
1. 최종 phase_report R: 전체 pytest 1회 결과 + 골든 3건(artifacts phase7 복원본) 수치 + 차단 호스트 표 + 미포함 사유 표 + 지시와 다른 사실 표. 오면 감독이 최종 감독 세션에 종료 보고를 보낸다.
2. 사용자 의견이 오면 UF-171~ 로 원장 기록 → 이 영상에서 고쳐 재전달(C12).
3. UF-170 장치(gate-view 라벨 제거·시험)는 387c2925 로 완료 — 원장 guarded.
