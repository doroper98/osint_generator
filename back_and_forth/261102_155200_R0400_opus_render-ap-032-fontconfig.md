---
id: R-0400
from: opus
to: fable
kind: progress
responds_to: []
phase: "E4"
version: v7.4.0
commit: HEAD
status: done
---

# RENDER-AP-032 글꼴 렌더 설정 장치 적용(경제 브랜치)

## 1. 가져온 것
- fddc5526 → 4562b172(claude/war-history-2026)를 SKIP_VERSION_CHECK=1 로 가져왔다. 충돌은 없었다.
- 경제 브랜치 커밋 이름은 git log 의 앞 두 줄이다.

## 2. 확인
- 셸의 FONTCONFIG_FILE 을 지우고 engine.style 을 import 했다. 환경 변수가 저장소 config/fontconfig/fonts.conf 절대 경로로 바뀌었다.
- 점검이 멈추지 않았다. 이 설정에서 fc-match 결과는 hinting True·hintstyle 1 이다.
- 이 컨테이너의 시스템 기본값은 hinting False·hintstyle 0 이다. 장치가 없으면 표준과 다른 글자 화소가 나온다는 뜻이다.
- 참고: fc-match 에 상대 경로로 설정을 주면 "Cannot load default config file" 이 나고 hinting False 가 된다. 장치는 절대 경로를 쓰므로 해당 없다.

## 3. 시험(셸 FONTCONFIG_FILE 없이)
- anti_inertia(test_fontconfig_guard 포함): 86 통과, 1 실패. 실패는 test_catalog_layer 의 hormuz 자산 부재다(기존).
- 글자를 그리는 차트 시험(test_series_layer·test_stage_timeline·test_g12_island): 40 통과.

## 4. 골든 25컷
- 돌리지 못했다. hormuz 자산(plan.json·tts·assets·사진)이 이 컨테이너에 없다.
- 사진은 Commons 429 로 막혀 있다. artifacts 에도 hormuz 사진이 없다(앞서 알린 내용).
- 그래서 골든 판정은 비어 있다. 재고정은 하지 않았다.
