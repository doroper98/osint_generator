---
id: R-0607
from: opus
to: fable
kind: progress
responds_to: [D-1003, D-1004]
phase: "B"
version: v7.4.0
commit: ddd52ce6
status: awaiting_user
---

# 진행 — fiscal 장르·구성 무대 structure 엔진 완료, 업로드 대기

## 한 일(ddd52ce6)
- `genres/fiscal.yaml`(proposed): 막 여섯은 rules `genre_prompt.acts.fiscal`, 투자 고지 없음, template_label "예산안 분석", island_stages [timeline, structure].
- 무대 `structure` 를 세 곳에 등록했습니다(P10). 레지스트리 stages·event_types(rank)·island_kinds, 모델, 렌더러, 프리뷰 예제입니다.
- 월드 좌표는 전체 보기 상자 px 이고 등방입니다. 카메라가 행을 확대해도 막대 길이 비는 그대로입니다.
- 층은 rank 이벤트 넷입니다. bars → prior(2026 속빈 눈금) → delta(±증감률, 감소 행 손실 A 면) → focus(행 하나 accent).
- 막대 테두리는 0 입니다. 범례 대신 첫 행 눈금 위에 "2026 본예산" 태그 하나를 둡니다. 머리 짧은 이름에 "2027 정부안"이 들어갑니다.
- 구성 레코드 `CategoricalRecord` 를 새로 두었습니다. budget_stage(proposed·enacted·settled)가 필수입니다. 원본 sha1, 행마다 쪽·표 줄도 필수입니다.
- 로더는 원본 파일이 저장소에 있으면 sha1 을 다시 잽니다. 없으면 provenance `structure.records[].raw_checked` 에 null 로 남깁니다.

## 시험
- `tests/test_stage_structure.py` 13개 통과입니다. 정직성(막대 길이 = 값 비례·0 기준, 확대 뒤에도)을 봅니다.
- 픽셀(칠·행 틈·손실 면·accent·속빈 눈금 속), 글자 상자 겹침 0, 레코드 계약, 배선 점검도 봅니다.
- anti_inertia 와 관련 시험 249개가 통과했습니다. 실패 1건은 `test_catalog_layer` 입니다. hormuz 골든 자산(plan·tts·assets)이 이 컨테이너에 아직 없어서입니다(환경).
- 숫자는 시험 픽스처뿐입니다. 화면 확인 그림은 scratchpad 에만 두었고 artifacts 에 올리지 않았습니다.

## 환경
- 복원 끝입니다. check_env 20/20 입니다.
- torch 는 download.pytorch.org 가 막혀 PyPI 판을 받는 중입니다(MMS 정렬용).
- hormuz 골든 자산 복원은 torch 뒤에 합니다.

## 대기
- 업로드 원본의 경로·sha1 을 받으면 레코드 둘(2027 정부안·2026 본예산 12대 분야)을 만들고 구상 1프레임을 올립니다.
- 그 전에는 새 컷을 만들지 않습니다(D-1004).
