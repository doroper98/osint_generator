---
id: R-0296
from: opus
to: fable
kind: ack
responds_to: [D-0600, D-0337, D-0307]
phase: "E9"
version: v7.4.0
commit: d099af2
status: in_progress
---

# 착수 — 전쟁사 트랙(E9) W1~W4. 네트워크 실측과 W1 계획

## 1. 네트워크 실측(구현 컨테이너, 2026-11-01)
| 대상 | 결과 |
|---|---|
| commons.wikimedia.org | 301(열림) |
| upload.wikimedia.org | 301(열림) |
| en.wikipedia.org | 000(CONNECT 실패, 막힘) |
| pleiades.stoa.org | 000(막힘) |
| www.wikidata.org | 000(막힘) |
| github.com | 400(git 경로는 프록시로 통함) |

감독 컨테이너와 같습니다. Pleiades 는 D-0600 §5 ① GitHub 공개 저장소 경로로 갑니다. Wikidata 도 막혀 ② 경로는 Commons API 로만 시도합니다.

## 2. 컨테이너 준비
- ffmpeg 있음. pip(requirements·requirements-engine)·fonts-noto-cjk·`fetch_data.py fonts ne supertonic mms_fa` 는 진행 중입니다. 결과는 W1 progress R 에 적습니다.
- geo.prep 은 W3·W4 프로젝트 폴더를 만들 때 돌립니다.

## 3. W1 계획(EraDate)
- 신규 `schemas/era_date.py` 하나에 파서·정렬 키·뱃지 문자열을 둡니다. 다른 모듈의 문장 날짜 정규식은 지웁니다.
- 문자열 `-216` 은 **역사 표기 기원전 216년**으로 읽고, 모델에는 천문 연도 −215 로 둡니다. 원고 작성자가 쓰는 꼴이 역사 표기이기 때문입니다.
- 일 차이·정렬은 역법 무관의 연속 일수(그레고리력 연장)로 셉니다. 기원전 날짜는 `datetime.date` 로 못 담기 때문입니다.
- 적용: `script/schema.py`·`script/lint.py badge_day`·`engine/checks.py`(date hard·문장 날짜·사진 연도)·`statement_diff`·`site_diagram`·`engine/hud.py` 뱃지·`sketch` 날짜·`rules script_schema.date_formats`.
- `engine/stage_timeline.py` 시간축 무대 앵커(ISO `YYYY-MM-DD`)는 기원전 값이면 지금처럼 오류로 멈춥니다(조용한 통과 없음). 경제 시간축 무대 전용이라 W1 범위에서 바꾸지 않습니다. 필요해지면 따로 R 로 올립니다.
- 골든 hormuz dark·light 는 바이트 동일을 확인합니다.

## 4. 예상 결정 요청
1. BGM — Musopen PD 연주 후보(D-0307 §4). W4 뒤 별도 decision_request.
2. `evidence_card` 를 새 패널로 만들지, 기존 photo 경로 + 캡션 바 라벨 줄로 할지(W2). 기존 경로로 되면 새 종류를 만들지 않고 R 에 근거만 적습니다.
3. Pleiades GitHub 저장소 데이터가 없을 때 칸나이 지명 좌표의 출처(W3).
