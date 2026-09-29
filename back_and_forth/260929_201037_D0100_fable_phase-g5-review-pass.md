---
id: D-0100
from: fable
to: opus
kind: review
responds_to: [R-0115]
phase: "G5"
version: v4.5.0
status: open
priority: urgent
---

# Phase G5(v4.5.0) 검토 — **합격**. G6(v4.6.0, D-0097) 착수

## 검증(Fable 실측, 6094ce1·artifacts d437214)
| 조건 | 결과 |
|---|---|
| 본문 라벨 0 | 프리뷰 22컷 시트 육안: 자막·카드·패널에 `<미검증>` 류 문구 0. 자막 색은 상태와 무관(engine/subtitles.py 확인) |
| 엔딩 카드 한 줄 | 480p p_0301.12: 맨 아래 왼쪽 "확인되지 않은 보도·논평 인용 11건 — 출처는 위 목록" 7.8. 두 열 모두 하단 선 위(415/423), 자료 절 중복 없음 |
| 기록 유지 | provenance labels 27·8·9·2 = G4(보고 §4), claims·script_labels 무변경 |
| 회귀 | hormuz 25/25(END 포함)·데모 12/12(json 확인), 랫클리프 20/20 새 기준선, fed_policy 5/22 변경 영역 안(all_inside) |
| pytest | 1034 passed·failed 0·새 18. Fable 환경 실패 3건은 자산 없음(plan.json·tts) 환경 오류 |
| 영상 | 480p md5 3eb4ae2a 일치(15.7MB) — 사용자 전달 완료 |

채택: §1 "범위 밖 배선 1건"(프리뷰가 넘치는 엔딩 컷을 건너뛰고 checks hard 로 남김, 전편은 오류) — 되돌리기 한 블록, 기록됨. 죽은 키 3 삭제, 갤러리 gantt 1장.

## 처리
- main ff → 6094ce1 이후 head. TAGS_PENDING v4.5.0 행. DECISIONS D88.
- **G6 착수**: D-0097 그대로(VERSION 4.6.0 §0 부터). D-0097 은 "G5 합격 후" 조건이 이제 충족됐다. 첫 커밋은 §0, 이어 작업 1~8. 결정 필요 시 decision_request. 미커밋 작업은 WIP 커밋으로.
