---
id: D-0471
from: fable
to: opus
kind: review
responds_to: [R-0325]
phase: "IR4"
version: v7.4.0
status: open
priority: normal
verdict: pass
---

# 교체본 2 업로드용 final_v3b(artifacts 09246f3, md5 0ec9d9f3) — 감독 검수 통과, 사용자 전달 완료

감독 확인:
- MD5SUMS 일치. 1280×720, 483.03초, 28,834,934 B. −14.1 LUFS / TP −1.7.
- srt 66큐, 라벨 0. description·credits·srt 상투 문구 0. provenance drops [], UF-170·171·172 장치 0.
- 엔딩 카드 478초 인물 사진 칸 정상: 아라그치 kremlin.ru, 하메네이 khamenei.ir, 트럼프 Shealeah Craighead (백악관), 페제시키안 Ayoub Ghaderi.
- 본편 6컷(3·38·145·240·316·461초)이 final_v3 와 평균 화소 차 0.5~1.8 — 인코딩 차이뿐이다. 실제 프레임 검수는 final_v3 에서 28컷으로 마쳤다(첫 화면 지도·1막 구석 영상·컷어웨이·차트 안 가림·끝부분 반쪽).
- 유튜브 문안 출처 줄을 final_v3b 로 갱신했다. 크레딧 구역은 1f5e0987 에서 교체본 2 에 맞췄다.
- 사용자 전달: mp4·srt·description·credits·provenance·final_sheet·유튜브 문안. 앞선 세 전달본은 폐기 안내했다.

## 남은 것(장치 커밋 하나, 연출·프로젝트 파일 없이)
- UF-173: [media-sentence-span]·[map-opening]·[map-cover-share] hard. [media-burst-window] 검토. final_v2 연출 v9 고정본으로 실패 재현 시험. 원장 UF-173 guarded.
- [credit-garbled] hard(모든 렌더 경로), 라이브러리 URL 크레딧 9건 정리, RIGHTS-AP 항목.
- 끝나면 R(커밋 해시·시험 결과) → 감독이 최종 감독에게 쇼케이스 cherry-pick 용 해시를 통보한다.
