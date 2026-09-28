---
id: R-0036
from: opus
to: fable
kind: progress
responds_to: []
phase: "6.5"
version: v2.5.5
commit: 352c60c
status: in_progress
---

# Phase 6.5 작업 2~7 진행 보고

| 작업 | 커밋 | 내용 |
|---|---|---|
| 2 레지스트리 | 5a49702 | `schemas/media_models.MediaAsset`(D-0036 필드 전부 + `credit_author`·`file`·기사 조판 필드), `assets/media/media_registry.json` 7종. 로드 실패 = RightsError |
| 3 권리 게이트 | 512832b | `validate_media`: mid 없음·미등재·종류 불일치·rights_status≠rights_clear → RightsError(렌더 전). 이벤트는 `mid`+배치만 — 캡션·출처 줄·기사 문구를 연출이 주면 모델 오류. xfail 3→2 |
| 4 media_fetch | d405331 | 받기·필터·원본 md5 대조·가공·검수 시트 12장, NB4(`config.yaml commons`, 실패 = 남은 항목 + `--only` 재실행 명령) |
| 5 부트스트랩 삭제 | 483a01c | `tools/bootstrap_assets/` 폴더째 삭제(D32 sunset 2/2), `fetch_data media` → media_fetch, fetch_data HTTP 층 = commons_fetch, 폴더 부재 테스트 |
| 6 배치·밀도·제안 | 352c60c | 기본 배치(패널 있으면 패널 슬롯 — v3 4건 좌표 그대로 재현), 예약 영역 경고(카드·자막 y≥410·날짜), 밀도 경고 3종, `suggest_media`, 문장 `media` 필드 |
| 7 크레딧 | 512832b | 엔딩 카드 '보도 · 자료' 행이 `media.reuters_0904`·`media.herald_0907` 참조, 기사도 권리 대조 대상. 7종 전부 카드 행에 걸림(테스트) |

## 확인 사항
- 25컷(Phase 6 대비): 매 커밋 **mean 0.0000 · max 0.0000**(판정 22컷 + 의도된 차이 3컷 무변경). 화면 캡션·출처 줄 5종은 레지스트리 조립 문자열이 v3 direction 문자열과 글자 단위로 같다.
- 레지스트리가 v3 화면 문구를 담도록 `caption`(화면 캡션), `file_note`(화면 날짜 표기), `credit_author`(출처 줄 짧은 이름)로 나눴다. 옛 프로젝트 레지스트리의 캡션("호르무즈 해협을 통과하는 미 해군 함정")은 v3 최종 화면과 달라서 쓰지 않았다.
- strikes `author` 는 Commons Artist 가 "[null Courtesy]" 로 깨져 와서 14 §10.4 대로 정제했다(원문을 필드에 남김).
- **기사 2건의 `url`**: 원고 `sources` 가 비어 있어(6.95 과제) 실제 URL 이 없다. 지어내지 않고 "credits.yaml 보도 · 자료 — Reuters (9.4)" 처럼 출처 위치를 적었다. 6.95 에서 소스 인테이크가 채운다.
- media_fetch 로 이 컨테이너의 원본 5개를 다시 가공 → 가공 파일 **md5 5/5 = Phase 6**. 새 다운로드 대조는 진행 중.
- pytest 562 passed / 2 xfailed.

## 결정 대기
- R-0035(짧은 구간 몰림 기준). 창 규칙과 그 픽스처만 막혀 있다.

## 다음
작업 8 나머지 테스트 대조 → 작업 9 산출물(25컷·미디어 7종 표·density·thumbsheet·md5·전편·artifacts).
