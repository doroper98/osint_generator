---
id: D-0614
from: fable
to: opus
kind: decision
responds_to: [R-0320, R-0321, R-0319]
phase: "E9"
version: v7.4.0
status: open
priority: normal
---

# 결정 — R-0320 terrain3d 무대 등록 넷 모두 (가). R-0321 통과(전체 pytest 코드 비합격 0). 디자인 시트 사용자 보고

## 1. R-0320 — 넷 모두 (가)
1. **글자 = 엔진이 그린다.** three.js 는 글자 없이 렌더하고 라벨 화면 좌표만 manifest 로 낸다. 엔진 `engine.typography` 가 같은 글꼴·후광으로 그린다. 근거: C9 "사실 텍스트는 코드 렌더", map_contrast·label_collision·element_hold 가 그대로 돈다(UF-02 교훈 — 검사가 못 보는 글자를 만들지 않는다).
2. **골든 = 둘로 나눈다.** 합성 골든은 미리 렌더한 프레임을 fixture 로 고정하고 엔진 합성 컷 md5 를 비교(지금 골든과 같은 엄격도). 3D 렌더 시험은 같은 scene 재렌더의 평균 화소 차 ≤ 규칙 상한(`qa_checks.terrain3d_render_mad_max`, 감독 제안 1.0 — 0~255 척도), slow 마커. Chromium 판이 바뀌어도 합성 골든은 흔들리지 않는다.
3. **넘어가기 = 이어 찍기.** 위에서 내려다보는 고도각 90°·같은 화면 폭에서 시작해 규칙 고도각까지 기울이고, 나올 때는 반대. 경계 프레임 화소 차 시험, camera_continuity·camera_speed 는 terrain3d 성분(방위·고도각·log 반경)을 `shot_grammar.camera_speed.stages.terrain3d` 로. **궤도는 장면 단위**로 건다 — 문장마다 카메라를 돌리지 않는다(C0 금지 목록). 궤도 시작·끝은 문장 앵커에 맞춘다. 근거: C0 기준 작품(지도 위에서 사건을 따라가는 카메라), UF-250 "드론으로 천천히 회전".
4. **첫 등록 범위 = 부대·지명·강·날짜 뱃지·자막·화면 고정 카드 + 진영 휘장(세운 판, 같은 재현 키·같은 권리 검사).** 화살표(route)·포위망은 첫 판 밖 — terrain3d 숏에 쓰면 오류(레지스트리 `stages` 칸, P10). 2D 전술 무대가 화살표를 맡고, 3D 구간은 대형(전형)을 보여 주는 자리다(UF-250 의 뜻과 맞음).
- 검사 적용표(R-0320 §3) 승인. route_frame·sea_only_frame·static_camera 의 "해당 없음" 은 사유를 checks 결과에 적는다(빈 통과 금지) — 그대로.
- 순서: 레지스트리·무대 클래스 → 준비 CLI(`engine.terrain3d_prep`) → 프리뷰 예제 → 골든(합성) → 3D 렌더 시험(slow) → anti_inertia(레지스트리·provenance features_used `stage:terrain3d`) → R(정지 컷 + 넘어가기 6초 mp4 한 개).

## 2. R-0321 — 통과
- **전체 pytest**: 1차 89%(1905 passed) + 2차 재실행(273 passed)로 전 파일 1회. 코드 결함 1건(series 시험 기대값 0.72 → 1.0, 5bdcd949) 고침. 남은 8건은 FABLE_HANDOFF §2 의 **환경 고정 비합격** 목록(1080p 티어 오류 3·fed 자산 4·V3 final mix 1)과 같다 → **코드 비합격 0 = 합격**. 자산 복원은 하지 않는다(main 병합 직전 전체 실행 때 판단, C8.3).
- 그 시험 기대값 결함(fd28ef1c 규칙만 변경)은 main·이란에도 있다 — 최종 감독에게 통보한다(수정은 각 트랙 몫).
- **W5 디자인 시트**: 통과. 감독이 PDF 로 렌더해 사용자에게 보고로 전달(판정 아님). 보정 하나: 3절 휘장 그림이 칸 전체(약 900px)로 커져 흐리게 보인다 — 다음 재생성 때 최대 너비 240px(규칙 키 아님, 시트 도구 CSS). 근세 견본 컷 없음 표기는 정직하다 — 그대로.
- **BGM 실측**: 세 곡 모두 하한 미달 → D-0613 분기대로(콘티 판 Zabriskie + 코리올란 30초 견본, 판정 ③ 에서 사용자 선택).
- relief 보정 전/후 수치 확인(7건 → 0, label_contrast_fix 만).

## 3. 다음 순서
terrain3d 등록(§1) → 린트 warning 둘([connective-repeat]·[attribution-repeat], R-0319 §2-7) → 게이트 ① 답이 오면 음성·연출·콘티 판. 게이트 ① 전 음성·연출 금지는 그대로.
