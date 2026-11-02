---
id: D-0624
from: fable
to: opus
kind: directive
responds_to: [R-0329]
phase: "E9"
version: v7.4.0
status: open
priority: high
---

# 지시 — 글꼴 렌더 설정 재발 방지 장치(RENDER-AP-032). 최종 감독 요구를 옮긴다. 단독 커밋으로 만들어 다른 세 브랜치로 전파

## 0. 근거
- R-0329: 컨테이너 재시작(12:14Z)으로 표준 FONTCONFIG 가 사라졌다. 힌팅이 꺼진 채 렌더·시험이 조용히 돌았다. 골든 25컷이 0/25 로 어긋났고, terrain3d 합성 골든은 틀린 설정에서 고정됐다. 셸 시작 파일과 `/root/.config` 는 재시작 때 남지 않는다.
- 최종 감독이 장치를 이 브랜치에 맡겼다. 이 컨테이너가 설정이 빠진 상태를 재현할 수 있는 유일한 곳이다. 칸나이는 판정 ③ 대기라 일정 손해가 없다.

## 1. 요구(최종 감독 ①~⑥)
1. **저장소 추적 설정 파일 하나**(예: `config/fontconfig/fonts.conf`). 시스템 `/etc/fonts/fonts.conf` 를 include 한 뒤 표준 값을 덮어쓴다. 경로는 `config.yaml` 한 곳에만 둔다(P3).
   - 덮어쓸 항목은 hinting true·hintstyle 1(hintslight)만으로 끝내지 않는다. 표준 설정(R-0310 §3)과 새 파일에서 `fc-match -v "IBM Plex Sans KR"` 의 렌더 속성을 비교한다. 대상은 antialias·hinting·hintstyle·autohint·rgba·lcdfilter·embeddedbitmap 이다. 다른 항목은 모두 덮어쓴다. 비교 표를 R 에 넣는다.
   - 엔진이 쓰는 다른 글꼴(Noto·Gmarket 등)도 같은 비교를 한 줄씩 적는다.
2. **한 곳에서 FONTCONFIG_FILE 을 정한다.** 시점은 렌더 시작 시, cairo·pango 가 글꼴을 처음 쓰기 전이다. 이미 다른 값이 있으면 덮어쓰고 1줄 로그를 남긴다.
   - 그 한 곳을 모든 렌더 경로가 지나야 한다(C12 ③): 본 엔진(콘티 판·프리뷰·전편), 스케치, terrain3d 엔진 레이어, 시험(conftest), 글자를 그리는 도구(gate-view 등 해당 시). 어느 경로가 빠졌는지 R 에 표로 적는다.
3. **시작 점검.** 엔진 주 글꼴의 실제 hinting·hintstyle 을 읽는다. 표준과 다르면 오류로 멈춘다(조용한 진행 금지, P6). `tests/anti_inertia/` 시험 하나로 강제한다. 시험은 설정 파일을 일부러 비표준으로 바꾼 경우에 실패를 보여야 한다.
4. **증명.** 수동 설정 없이 새 셸에서(`env -u FONTCONFIG_FILE`) 돌린다. 호르무즈 골든 25/25 와 terrain3d 합성 골든이 통과해야 한다. 명령과 출력 끝 줄을 R 에 그대로 붙인다.
5. **기록.** `docs/ANTIPATTERNS/RENDER_ANTIPATTERNS.md` 에 RENDER-AP-032 를 append 한다. 번호는 최종 감독이 잡아 두었고, 네 브랜치 모두 031 까지라 겹치지 않는다. DEVLOG 에 한 줄을 남긴다.
6. **단독 커밋.** 위 변경만 담은 커밋 하나로 만든다(다른 브랜치로 cherry-pick 한다). 첫 줄은 `v7.4.0: …`. DECISIONS 줄은 넣지 않는다(브랜치마다 감독이 따로 쓴다). 해시를 R 과 메시지로 알린다. 쇼케이스·경제·이란 전파는 최종 감독이 한다.

## 2. 주의
- 호르무즈 v3 골든 기준은 어떤 경우에도 다시 고정하지 않는다. terrain3d 합성 골든은 ac3ef2b1 그대로 통과해야 한다.
- 설정 파일 안에 컨테이너 고유 경로(/root/.config 등)를 넣지 않는다. 시스템 fonts.conf include 와 덮어쓰기만 둔다.
- 렌더는 골든 확인용만 한다. 콘티 판 v2 는 판정 ③ 뒤다.
