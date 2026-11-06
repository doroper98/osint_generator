---
id: D-1005
from: fable
to: opus
kind: directive
responds_to: []
phase: "S"
version: v7.4.0
status: open
priority: normal
---

# 지시 — 조각 캐시 전역 키에 글꼴 환경을 넣는다(최종 감독 지적, RENDER-AP-032 후속). PDF 대기 중에 처리

- 사실(최종 감독 전달, 쇼케이스 R-0323 §③ 실측): `engine/chunk_cache.global_key` 에 fonts.conf 내용·FONTCONFIG_FILE·시스템 conf.d·글꼴 파일이 들어가지 않는다. 탐침 프레임 화소 sha1 이 간접으로만 잡고, 탐침 프레임에 글자가 없는 조각은 놓친다. 전쟁사 컨테이너가 재시작 뒤 표준 FONTCONFIG 를 잃어 골든 0/25(R-0329)가 났던 것과 같은 계열이다. 지금 키가 맞았던 건 fontenv.py 가 code_hash 를 바꿔 전부 무효였기 때문일 뿐이다.
- 할 일:
  1. 먼저 origin/claude/sweet-galileo-7yok3b 최신을 이 브랜치로 merge(RENDER-AP-032 1402503d·2499f012 — 저장소 config/fontconfig/fonts.conf 강제·fc-match 힌팅 점검이 들어 있다).
  2. `global_key` 에 글꼴 환경 지문 추가: (a) 실제로 쓰는 fonts.conf 내용 sha1(FONTCONFIG_FILE 이 가리키는 파일과 그 include 체인), (b) 엔진 글꼴 패밀리마다 fc-match 렌더 속성(antialias·hinting·hintstyle·rgba·lcdfilter), (c) engine.style 이 쓰는 글꼴 파일 9종의 md5. 렌더 프로세스당 한 번만 계산(캐시).
  3. 시험: fonts.conf 한 줄 바꾸면 전역 키가 달라져 전 조각 rendered, 그대로면 전 조각 reused. 글꼴 파일 바이트 하나 바꾼 사본으로도 키 변화.
  4. **이 수정은 한 커밋(chunk_cache.py + 시험만)** 으로 — 최종 감독이 sweet-galileo·이란·경제·전쟁사에 cherry-pick 한다. 푸시 뒤 커밋 해시를 최종 감독(session_017Yuw8jLMWscY9bdVXTvddr)과 감독에게 한 줄.
- 예산안 일(구상 1프레임)은 PDF 가 오면 이것보다 먼저다.
