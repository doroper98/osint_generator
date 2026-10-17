---
id: R-0233
from: opus
to: fable
kind: progress
responds_to: [D-0225]
phase: "P3-0"
version: v7.3.0
commit: df1d7c43
status: in_progress
---

# 인계(재기동 2 → 3) — v7.3.0 엔진 완료, 자산·원고 진행 중, 음성 전 단계

## 1. 끝낸 커밋(브랜치 claude/flight-event-sat-inset-plan)
| 커밋 | 내용 |
|---|---|
| 5cccffd0 | 새 이벤트 flight(출발 발광·점선 꼬리선·아이콘 drone/missile/jet 11/13/14px·착탄 링 = draw_boom 재사용·위성 인셋), registries·genres·콘티 판·카메라 앵커·provenance features_used.flight, tests/test_v730_flight.py |
| 8e1fcad1 | UF-103 원형 인셋(guarded: rule flight.inset.shape + 렌더 시험 3개), media_beats.inset_licenses(NASA GIBS·Sentinel·Esri private_only), MediaAsset scope, provenance private_only_assets, [inset-density], data press_cited(source_kind·cited[]·단위 mb/d·kb/d), dual_line null 끊기·record 대조·open_idx, tests/test_v730_press_cited.py |
| 11a7f951 | VERSION 7.3.0·헤더 41개·CHANGELOG·handoff 06·14·22·05 스키마 |
| c501d9c8 | media_fetch kind inset(공용 보관본 assets/library/insets 우선, 없으면 params.request_url) |
| 73ab5179·e7b03d0a | diesel_road_2026 진행 중 저장 |
| df1d7c43 | 위성 인셋 5장 공용 보관 assets/library/insets(+ inset_sources.json) |

- 시험: test_v730_* 24, anti_inertia·animatic·rules_ssot·docs_sync 통과. 유일한 실패 = `test_no_py_in_projects`(감독 커밋 projects/strike_demo_2026/*.py 2개 — main 병합 전 처리 필요, 예: .py → 다른 위치·확장자).
- **골든 25컷 md5 불변은 미검증**(hormuz 정렬 파일을 만들 MMS 모델이 없었다). 새 세션 첫 확인 항목.
- U7: [one-element] 검사가 저장소에 없다 → salvo 변경 불필요(연출에서 stagger 만).

## 2. 자산 현황
- 위성 인셋 5장(NASA GIBS HLS, §8 경로 ③ — arcgis 403 유지): 랴잔 10/07·라스라판 10/05·하르그 09/25·키리시 10/01·볼고그라드 10/10. 파일 assets/library/insets/, 출처 inset_sources.json. **미디어 레지스트리(kind inset) 미등록**, 키리시·볼고그라드는 하위 에이전트 판정만(리드 육안 미확인). 기존 3장은 512×369 가운데 자름 — 원형 렌더러가 정사각으로 다시 자른다. 노보쿠이비셰프스크·사라토프 미시도.
  - 등록 시: kind inset, license "NASA GIBS (public domain)", credit_author "NASA GIBS/HLS", file_note "위성 · 2026. 10", tool {name: gibs_hls, params: {source: <png>, request_url: <WMS 요청>}}, source_hash = png md5.
- 초상 6인: **0명 완료**(하위 에이전트가 후보 조사 중 중지). 기존 6인 라이브러리는 그대로.
- 기사 카드·시리즈 3개: **미등록**. 시리즈 값은 D-0225 §4 그대로, 레코드 id 는 대문자(RU_REFINERY_RUNS_2026·RU_DIESEL_SEABORNE_EXPORTS_2026·GULF_DIESEL_NET_EXPORTS_2026), source_kind press_cited, 빈 달 missing.

## 3. 원고
- 프로젝트 projects/diesel_road_2026, 상태 source_verify(new-project → intake 완료). order.yaml·credits.yaml(Mario Bava)·description.yaml·geo.yaml 있음.
- intake/sources.json 40건(기사 34·문서 6), claims.json 107건, verify_draft.json(검증 진행 중 중지 — 재실행 필요).
- script.yaml 초안 6장면 90문장(본문 4,202자 ≈ 9분 추정). **린트·발음 텍스트·D-0225 §3 귀속 점검 전**. 오케스트레이터 상태가 script_draft 에 도달하지 않았으므로 advance 로 검증·원고 단계를 다시 돌리거나 이 초안을 손질해 쓴다.
- 미확보 기사: 가디언 10/06 원문 대신 Kyiv Independent·UNITED24 등 2차 보도로 잡혔다(로이터·가디언 직접 페이지 접근 불가). 게이트 ① 출처 표에서 확인 필요.

## 4. 환경 복원 메모(새 컨테이너)
1. `cat /root/.ccr/ca-bundle.crt >> $(python -c "import certifi;print(certifi.where())")`
2. `pip install -r requirements-engine.txt -r requirements.txt pytest pytest-asyncio svgelements "setuptools<81"`(setuptools<81 필수 — pyworld 의 pkg_resources)
3. `apt-get update && apt-get install -y fonts-noto-cjk`
4. `git fetch --unshallow origin` 뒤 `python tools/fetch_data.py fonts ne tiles flags bgm`(IBM Plex 처음 0개)
5. 음성·정렬: `python tools/fetch_data.py supertonic mms_fa` → assets/tts/supertonic(huggingface.co Supertone/supertonic-3), assets/tts/mms_fa(dl.fbaipublicfiles.com …/model.pt). 둘 다 git 미추적.
6. 글꼴 렌더(골든 md5): /etc/fonts/conf.d 에서 12-unhinted-grayscale.conf 만 뺀 conf.d 링크 폴더 + fonts.conf 사본 → `FONTCONFIG_FILE=…`(phaseS0 §0.2).
7. hormuz 골든: phase7 artifacts → tts/·media/, `tests/fixtures/plans/hormuz_korea.plan.json` → plan.json, `fetch_data commons people`, legacy assets 복사, `commons_fetch emblems --only cheongwadae`, `geo.prep`. 그 뒤 `python -m script.plan projects/hormuz_korea`(표준 음성 정렬 파일 필요) → `pytest tests/anti_inertia/test_provenance_e2e.py tests/anti_inertia/test_q3_light_e2e.py`.
- thumb.wikimedia.org 가 403 이면 Commons 원본(upload.wikimedia.org)으로 받는다(이번 세션 하위 에이전트가 썸네일 경로를 upload 로 바꾸는 임시 래퍼를 썼다 — 저장소에 없음, 정식 방법 아님).

## 5. 미해결
- 골든 불변 검증, strike_demo .py 처리, 초상 6인, 인셋 레지스트리 등록, 기사·시리즈 등록, 원고 린트·게이트 ① 자료, 이후 음성부터 전 단계.
- 실수 기록: 이 세션에서 pull 전 `git stash -u -- projects/diesel_road_2026` 로 진행 중 파일을 잠시 숨겼다가 바로 복원했다(유실 없음). untracked 파일은 pull --rebase 를 막지 않으니 stash 할 필요가 없었다.
