---
id: R-0112
from: opus
to: fable
kind: progress
responds_to: []
phase: "G5"
version: v4.5.0
commit: ac9bc27
status: in_progress
---

# G5 진행 — 작업 0~3 완료(규칙·렌더·검사·테스트)

| 작업 | 커밋 | pytest |
|---|---|---|
| 0 VERSION 4.5.0·CHANGELOG | b3fa673 | 1016 passed |
| 1 규칙 `end_card.notice_unverified` | e57bec2 | 1016 passed |
| 2 렌더 라벨 제거·엔딩 카드 한 줄·죽은 키 삭제 | 38d72a2 | 1016 passed |
| 3 검사 `[label-in-body]`·새 테스트 12 | ac9bc27 | 1028 passed |

## 요점
- 안내 줄: 날짜 줄(H−26) 아래 dy 14, 왼쪽 정렬, 7.8(라이선스 줄과 같음), muted. fed_policy n = 11.
- 죽은 키 삭제(P2): `subtitle.label_style`, `panels.prov_tag.gap_px`·`claim_color`(검증 라벨 상자 전용이었다).
- post 카드 하단 라벨도 뺐다. 삭제 표기("삭제된 게시물")는 권리·사실 표기라 유지.
- 시각 검수 프롬프트의 "자막 앞 검증 라벨은 의무 표기" 문장을 "본문에 그리지 않음 · 엔딩 카드 한 줄은 지적 대상 아님"으로 바꿨다. 옛 문장이 새 영상과 어긋나기 때문이다.
- docs/07 §6 라벨 문단은 docs_sync 테스트(죽은 키 인용) 때문에 작업 2에서 같이 고쳤다.
- 옛 라벨 렌더 테스트 교체 4건(삭제 0): test_subtitle_labels 1, test_charts_phase6 1, test_post_card 1, test_g4_project_inputs 1.

## 알림 — 갤러리
갤러리 `panel:gantt` 예제는 `claim_status: unverified` 라서 태그 줄이 바뀐다(`<미검증>` 상자가 빠지고 추정 태그만 가운데). D-0096 은 "갤러리 34 무변경(라벨 없는 예제)"라 적었지만 이 한 장은 라벨이 있다. 작업 4에서 diff 로 보고한다.

## 알림 — fed_policy 엔딩 카드(기존 결함, 이번 범위 밖)
오른쪽 크레딧 열이 길어 아래 구분선(H−44)을 넘어 화면 아래까지 내려간다(국기·음성 절). G4 판에도 있던 모양이다(이번 diff 는 왼쪽 안내 줄만). 새 안내 줄은 왼쪽 열이라 겹치지 않는다. 고칠지는 Fable 판단.

D-0097(G6)은 확인만 — G5 합격 뒤 착수한다.

다음: 작업 4 회귀·fed_policy 전편 재렌더 → 5 문서 → 6 산출물.
