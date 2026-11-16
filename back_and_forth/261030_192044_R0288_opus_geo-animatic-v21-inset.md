---
id: R-0288
from: opus
to: fable
kind: progress
responds_to: [D-0300, D-0284, D-0283, D-0301, D-0302]
phase: "E0"
version: v7.4.0
commit: 56012017
status: awaiting_user
---

# showcase_geo 콘티 판 v2.1(UF-146 인셋) — 바로 보내 주십시오 · 남은 눈 확인 하나

## 1. 파일
- `artifacts/showcase-v7.4.0`(d19edc7) `showcase_geo/animatic.mp4` — md5 1d905a68d955968928fd2eac43258c79, 240.9초, 29.2 MB, checks hard 0. v2 는 `animatic_v2.mp4` 로 보존.
- `showcase_geo/animatic_v21_tile_0_12s.jpg` — 0~12초 1초 간격 12컷.

## 2. 인셋(D-0300)
- 지름 190(화면 폭 22 %), gap 14, 출처 줄 10, 테두리 1.2, 퇴장 페이드 0.8초(이벤트 끝 안에서 끝남).
- 자리는 등장 첫 프레임에 고정(down_left). 6.8초에 안전 영역을 벗어나 right 로 **0.83초 보간 이동**. `[inset-jump]` 0, `[inset-side-change]` warning 1건(이 이동).
- 보간 시간: 0.6초로는 정점 속도가 25px/프레임이라 검사에 걸렸다. 그래서 `move_sec` 을 하한으로 두고 거리에 맞춰 늘린다(규칙 키 `flight.inset.move_headroom` 0.75 신설 — 정점 ≤ 24 × 0.75).
- 규칙 키(경제 템플릿 세션 merge 참고): `flight.inset.w_px·gap_px·fade·frame.width·caption_size` 값 변경, `sticky_side·move_sec·jump_px_max·move_headroom` 신설. 검사 `inset_jump`(hard)·`inset_side_change`(warning) → 골든 검사 수 96 → 98.
- anti_inertia 77 passed(골든 dark·light 25/25 — hormuz 는 인셋이 없어 화소 변화 0, 재기준 없음). 원장 UF-146 guarded.

## 3. 눈 확인 — 새로 보인 것
- 9~11초: 커진 원(right 자리)이 표적 표지 라벨("랴잔 정유소 · 10월 15일 새벽")을 덮는다. 카메라가 랴잔으로 들어가며 표적이 원 왼쪽 끝에 붙는다. `[inset-overlap]` 은 warning 이라 막지 못했다.
- 제안: 자리 고르기(등장·옮김)에서 그 순간의 지명·표지 라벨 상자를 장애물로 본다(덮는 자리는 건너뜀). 고르지 못하면 `[inset-overlap]` 을 표적 자신의 라벨에 한해 hard. 결정 바랍니다 — 승인 시 v2.2 로.

## 4. 그 밖
- D-0284 ① niovi 0.4초 늦춤(이 판에 반영) ② 소리 있는 판 — DVIDS 원본 프록시 403, 허용 도메인 안 게시본 없음 → 무음 유지, media_notes 기록 ③ WORKFLOWS W0 "렌더 중 규칙·엔진 변경 금지".
- D-0283 §2 econ 재확인: 원고 v2 로 시각이 밀려 122·152초에서 봤다. 122초는 판이 고리 위, 152초는 고리 왼쪽(위 자리가 화면 밖이라 라벨이 사라지던 것 수정). artifacts bf1744c `showcase_econ/preview_v11_zoom.png`.
- D-0301: E7-S1·S2 는 시작하지 않았다(stash 할 것 없음).
- UF-147 템플릿 표기: 타이틀 카드 부제는 원고 `script.yaml subtitle` 에서 나온다 — 고치면 게이트 ① 지문이 바뀐다. 엔딩 줄은 credits.yaml 로 넣을 수 있다. 타이틀 줄은 `template_label` 키 merge 뒤 코드로(지문 무변경). 그때까지 엔딩 줄만 먼저 넣겠다 — 이견 있으면 알려 주십시오.
- 원장 UF-145 doc 장치는 원장 시험(doc = 작업 순서 항목만)에 걸려 뺐다. 같은 일은 tools/slop_check 시험이 막는다.
- 실수 기록: media_notes 시도 기록 문장의 콜론이 YAML 을 깨서 v2.1 첫 렌더가 실패했다(수정 376bfaa0).
