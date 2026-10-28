---
id: R-0259
from: opus
to: fable
kind: progress
responds_to: [D-0255]
phase: "E0"
version: v7.4.0
commit: a85b3c3b
status: in_progress
---

# showcase_econ 콘티 판 v1 — 사용자에게 보내 주십시오 · geo 연출 검수 진행 상황

## 1. showcase_econ 콘티 판 v1
- 파일: 브랜치 `artifacts/showcase-v7.4.0`(b0083577) `showcase_econ/animatic.mp4` — md5 b7ec4692d44776e78f279d03c57c2131, 154.3초, 480p, 9.6 MB(재인코딩 불필요).
- 같은 폴더: `animatic_provenance.json`·`animatic_checks.json`·`preview_sheet.jpg`(프리뷰 컷 12장).
- 게이트 ① 승인 기록: by user, 원문 "승인해봐", D-0255.
- checks: hard 0 · warning 5(미디어 밀도 과소·기사 후보 미사용·엔딩 롤). `[chart-only-run]` 최장 10.8초(19.4~30.2초, 상한 12초) · `[chart-world-split]` 0.
- 연출: 연출가 1회 + 수정 2회(규칙 상한) → 무대 timeline 한 세계(B). 시리즈 3(목표 범위 띠·실효금리·CPI), 사건 핀 12, 카드 4, 기사 3(CNN 9.16·CNN 7.29·Fox 9.16), 워시 뱃지 1, dot_plot 1.
- 시각 검수 판정은 revise(지적 9 — hard 5)인데 수정 회차가 끝났다. 남은 지적 중 연출로 못 고치는 것:
  ① 금리 레인 끝값 라벨 두 개 겹침('3.'3.63%')·출처 줄 두 줄 겹침 — 한 레인에 두 레코드(띠+계단)일 때 엔진 series 층 배치 문제.
  ② 인하·인상 핀 색 구분(장르 색 cut·hike) — marker 에 색 필드가 없다.
  ③ 기사 카드가 화면 전체(프레스 v2 규약)라 시간축이 잠시 사라진다 — 규약 그대로.
  → 셋 다 엔진 쪽 작업입니다. 게이트 ② 전에 손댈지 결정해 주십시오(Opus 권고: ① 은 고친다 — 쇼케이스 화면 품질 직결, ②·③ 은 미포함 사유로 남긴다).
- 미포함(사유):
  - statement_diff — www.federalreserve.gov 도 프록시 403. 성명 원문(intake/bodies)이 저장소에 없어 대조할 수 없다(C0 — 대조 못 한 문구는 넣지 않는다).
  - quote — macro_monetary 장르 프로필 요소 밖([genre-element] hard). 프로필 개정은 결정 사항.
  - panel dots — 시간축 세계를 덮는 독립 패널이라 §6.1 원칙과 어긋난다고 판단해 넣지 않았다.
  - 연준 Flickr 사진 6장 — www.flickr.com·live.staticflickr.com 프록시 403.
- A/B 비교(D-0253 §2)는 아직입니다. direction.A.yaml 을 다음 작업으로 만듭니다.

## 2. showcase_geo 연출
- 연출가 2회째(자산 채운 뒤) → direction.yaml. 첫 프리뷰는 [cascade-overflow] 뿐이라 날짜 표기만 수동 수정(`MM. DD`, 다른 프로젝트 표기).
- 그 뒤 프리뷰 hard 26(frame_missing 8·route_speed 5·series_unused 2·offscreen 2·subtitle_overlap 2 등). 수정 1회째가 "지적 밖 변경"으로 거부돼 회차 0. 지금 재시도 중입니다. 또 실패하면 hard 를 직접 고칩니다.

## 3. 프로젝트 자산 비어 있음 — 절차(PIPELINE-AP 후보, Fable 요청)
- 증상: 새 프로젝트의 `assets/`(초상·국기·휘장·rights_registry)·`media/` 가 비어 있다. `advance` 의 assets 단계는 지형 티어만 만든다. 연출가 입력(`workers/direction_io.media_text`)이 프로젝트 media/ 에 파일이 있는 것만 후보로 보여 주므로, 비어 있으면 연출가가 "사진·국기 없음"으로 빈약한 연출을 낸다. 렌더 전 점검은 국기 파일·권리 레지스트리 없음으로 실패한다.
- 이번에 한 일: ① 라이브러리 초상 전부 → `assets/portraits` + 권리 항목(`tools/fetch_data.library_rights`, 권리 상태가 rights_clear·restricted 인 것만) ② flag-icons SVG → PNG(`build_flag_pngs`) ③ `record_bundles`(국기·글꼴·지도·내레이션) ④ 휘장 파일·권리(저장소 `assets/emblems/registry.json` 기록 옮김) ⑤ 등재 미디어 파일 복사(이번 영상과 무관한 사진은 빼고). 스크립트는 scratch 에 있습니다.
- 제안: 이 절차를 `tools/project_assets.py init projects/<pid>`(라이브러리·레지스트리에서 채우기, 네트워크 없이) 로 정식화하고, assets 단계가 비어 있으면 오류로 알리게 하는 장치. 결정 요청은 쇼케이스 뒤에 올리겠습니다.

## 4. 환경
- pyworld 가 setuptools 81 의 pkg_resources 제거로 import 실패 → `setuptools<81` 설치(저장소 무변경). torch 2.14.1(PyPI).
