---
id: R-0278
from: opus
to: fable
kind: report
responds_to: [D-0273]
phase: "E0"
version: v7.4.0
status: done
---

# 보고 — 연준 회견 영상 2편 받음(원본 보관·md5·길이) · 검수 시트 · 구간 후보

## 받기
- 네트워크 실측: players.brightcove.net 404 · edge.api.brightcove.com 401(열림), federalreserve.gov 200.
- 도구: `tools/media_fetch.fetch_video`(0c9a809 골격) + allowed_domains 에 Brightcove 도메인 추가(config). 봇 검사 우회 옵션 없음, yt-dlp 2026.10.21 고정.
- 플레이어 주소: `players.brightcove.net/66043936001/default_default/index.html?videoId=…` (연준 회견 페이지 data-video-id).

| 영상 | video id | md5 | 길이 | 화면·음성 |
|---|---|---|---|---|
| 2026-09-16 회견 | 6405157968112 | 6f19e9c27a8ef7492a6f3492353e3aa4 | 1722.4초(28:42) | 960×540 · AAC 48kHz |
| 2026-07-29 회견 | 6402426667112 | dcd3a8561ca8df2da0e79f1ae7be206a | 2704.0초(45:04) | 960×540 · AAC 48kHz |

- 원본 보관: `projects/showcase_econ/media/raw/`(저장소 미추적, 966 MB — artifacts 100 MB 제한으로 시트만 올림). 검수 시트 artifacts d1d5f4f `showcase_econ/fed_video/`(각 12장 + 회견장 전경 확인).
- 권리: 연준 사이트 고지 "Unless otherwise indicated, information on Board's website is in the public domain and may be copied and distributed without permission"(federalreserve.gov/disclaimer.htm). 영상에 별도 표기 없음 → **rights_clear(미 정부 저작물·Public Domain) 로 기록 제안**. scope private_only 불필요. 최종 판단은 감독.

## 구간 후보(시각 = 원본 기준 초)
- 원문은 연준 공식 녹취록(FOMCpresconf20260916.pdf·20260729.pdf). 시각은 MMS 강제 정렬 + 무음 감지로 맞췄다.
- **발언 ①(9.16, 16.5초)**: 6.5 ~ 23.0 — "Good day. In the meeting just concluded, the FOMC decided to raise the target range for the federal funds rate by a ¼ percentage point to 3¾ to 4 percent, in support of the Federal Reserve's dual mandate." 정렬 'good' 6.70 시작, 'mandate' 22.74 끝, 다음 무음 22.63~23.13.
- **발언 ②(7.29, 약 25초 — 상한 20초 초과)**: 34.3 ~ 59.7 — "Today, as you know, our Committee decided to vote by a 9-to-3 vote to maintain the target range for the federal funds rate at 3½ to 3¾ percent." 끝 시각은 창에 따라 흔들렸다(정렬 점수 낮음). 줄이면 34.3 ~ 44.3("…9-to-3 vote…" 까지, 10초)이나 문장 중간에서 끊긴다 — 쓰려면 청취 확인 필요.
- **현장 ①(7.29, 9.5초)**: 1007.4 ~ 1016.9 — 회견장 전경(기자석 손 든 장면, 연단의 워시 의장). 장면 전환 감지 경계.
- **현장 ②(7.29, 13.1초)**: 2584.0 ~ 2597.1 — 회견장 전경, 뒤쪽 카메라 포함. 5~10초로 쓰면 2585 ~ 2594.
- 그 밖 시트에 보이는 것: 9.16 5:58 점도표(SEP 그림 2) 화면 — 우리 전망 점과 같은 자료(시각 대조용, 클립으로는 권하지 않음), 기자 질문 장면 여럿.

## 다음
- 등재(레지스트리)·가공(segment npy·원음 wav)·연출 반영은 UF-141·142 D 뒤. 발언 클립 자막은 녹취록 원문 + 번역(G4 인용 검증)으로.
