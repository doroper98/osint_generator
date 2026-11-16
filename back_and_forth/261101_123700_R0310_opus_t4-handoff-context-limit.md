---
id: R-0310
from: opus
to: fable
kind: progress
responds_to: [D-0336, D-0339]
phase: "E4"
version: v7.4.0
commit: HEAD
status: handoff
---

# 구현 세션 3 → 다음 구현 세션 인계 명세(T4·T5 착수 전, 컨텍스트 한계)

## 1. 상태
- 브랜치 `claude/econ-template-2026` 머리 = R-0309 다음 이 파일. 작업 트리는 깨끗하고 모두 push 했다.
- D-0339 ①~④ 는 끝났다(R-0309). 남은 일은 D-0336 §3 T4 → T5(삼성·인텔 영상, W0 순서 의무)다.

## 2. 다음 세션 시작 순서
1. `git config core.hooksPath .githooks && git fetch origin claude/econ-template-2026 && git checkout claude/econ-template-2026 && git pull --ff-only`
2. 컨테이너 준비(R-0298 §3 + 이 세션 보정):
   - apt: ffmpeg·libcairo2-dev·fonts-noto-cjk·pkg-config
   - pip: `-r requirements.txt -r requirements-engine.txt`. torch 는 pypi 판이다. pyworld 가 pkg_resources 를 찾으므로 `setuptools<81` 도 넣는다.
   - `python tools/fetch_data.py fonts supertonic mms_fa`
3. FONTCONFIG(중요): `/etc/fonts/fonts.conf` 를 복사하고 include 경로만 바꾼다. conf.d 사본에서는 12-unhinted-grayscale 를 뺀다.
   - 짧은 fonts.conf(include 한 줄)로는 글꼴 디렉터리가 빠진다. 그러면 fc-match 가 빈 값을 낸다.
   - 확인: `fc-match -v "IBM Plex Sans KR"` 가 hinting True, hintstyle 1 이어야 한다.
4. 스케치 회귀용 프로젝트 `projects/econ_t2_{stage,guidance,slope,dumbbell,diverging}` 는 .git/info/exclude 다.
   - direction·script 는 artifacts `t2_stage_v3/*/project/` 에서 가져온다.
   - labels.yaml 은 fed_timeline_demo 사본, credits.yaml 은 artifacts `t2_multilayer_v3/project/credits.yaml` 이다.
   - 권리: `python -c "from pathlib import Path; from tools.commons_fetch import record_bundles; record_bundles(Path('projects/econ_t2_X/assets/rights_registry.json'))"`
   - 그다음 `python -m script.plan projects/econ_t2_X` 를 돌린다. media_fetch 는 네트워크에서 멈춘다.
5. 새 검사 실측 스크립트는 /tmp/chk.py 에 있었다(컨테이너와 함께 사라진다). 내용은 load_project 뒤 checks 의 새 함수 7개를 부르는 것이 전부다.
   - PYTHONPATH 에 저장소를 넣는다.
   - grid·border 는 프레임을 그리므로 컷당 1~3분 걸린다.

## 3. 이 세션에서 바뀐 것(다음 세션이 알아야 할 것)
- 새 hard 검사 7: chart_overload·chart_layers_min·secondary_axis_single·bars_from_zero·estimate_actual_pair·grid_text_cross·bar_border.
- 값은 rules `qa_checks.chart_depth` 에 있다. 골든 검사 항목 수는 118 이다.
- **삼성·인텔 본편은 차트 아일랜드 하나에 층 3 이상이 필요하다**([chart-layers-min]). 새 층 사이는 4초 이상 띄운다([chart-overload]). 연출 단계에서 문장마다 층 하나씩 켠다.
- 렌더러: 격자선이 레인 이름·축 값 앞에서 끊긴다(`stage_timeline.grid_segments` · `series.world_text_boxes`).
- 렌더러가 기록하는 목록 DRAWN_BARS·DRAWN_INSETS·DRAWN_GRID 를 검사가 쓴다.
- 레지스트리: series 스타일·island 종류를 늘리려면 rules registries, events Literal, `engine.registry` 표, tests/fixtures/preview 예제를 함께 고친다.

## 4. 열린 것
- 골든(test_provenance_e2e·test_q3_light_e2e)은 이 컨테이너에서 못 돌렸다. hormuz 자산이 없다.
- 전체 pytest 하루 1회도 아직 안 돌렸다. 다음 세션의 첫 일로 권한다. -n 4 로 약 1.5시간이다.
- `test_projection_dots::LaneSourceJoinTest` 실패는 sweet-galileo 에서 들어온 것이다. 쇼케이스 몫이다.
- D-0339 예시에 있던 W0 "구상 1프레임 승인 기록" 장치는 만들지 않았다(R-0309 §3). 지시가 오면 단다.
