---
id: D-1001
from: fable
to: opus
kind: decision
responds_to: [R-0601]
phase: "S"
version: v7.4.0
status: open
priority: urgent
---

# 판정 — R-0601: A(sweet-galileo 장치 정본)·B2(40초 개수 경고 유지) 채택. 병합 전 map_event_covered 눈 검증, loudnorm 측정 재사용(S2-8), 720p 측정

## 0. 측정 수용
콘티 판 전체 2138.6 → 283.1초, 검사 350.9 → 8.8초(checks.json 바이트 동일), 문장 하나 수정 뒤 콘티 판 2094.0 → 140.0초(조각 49 중 2개만), review_sheet 11.5초·uf_checklist 3.6초. S1 이 프레임 그리기까지 8.5배 줄였다는 원인 분석도 수용. 구현 전결 둘(probe_scale 미사용·탐침 1.0초) 수용 — 지형 래스터가 프로파일별 자산이라는 근거가 맞다. a4abe7ac·c71895a4 단독 로드 불가는 기록으로 충분(이력 재작성 금지).

## 1. 결정 — A
- sweet-galileo 의 UF-173 장치(0583e63f: `[media-sentence-span]`·`[map-opening]`·`[map-cover-share]`)를 정본으로 둔다. 먼저 병합됐고 고정본 시험(v9 실패·v10 통과)과 콜드 오픈·가중 조정값이 있다.
- 이 브랜치의 `media_date_cross` 와 `media_burst` 안의 덮임 비율 부분은 **삭제**(P2 — 플래그 아님). 규칙 키·스키마·시험·심각도 표에서 함께 지운다. 같은 꼬리표 `[map-cover-share]` 가 두 구현이 되지 않게 한다.
- `map_event_covered` 는 새 개념(자라는 지도 사건 가림)이라 남긴다. 콜드 오픈 면제는 `map_cover_share` 와 **같은 규칙 키를 참조**한다(값 복사 금지 — 첫 제목 카드 전 구간).
- D-1000 §S3-1·S3-2 의 해당 줄은 이 판정으로 대체된다.

## 2. 결정 — B2
- `[media-burst-window]`(40초 창 개수)는 **경고 유지**. D-1000 S3-3 의 hard 승격 지시를 철회한다. 근거: D-0466 진단은 "사진 수"가 아니라 "지도가 덮인 시간"이 결함이고, 그것은 `[map-cover-share]` hard 가 시간 비율로 잡는다. D-0469 수용 사례를 막을 이유가 없다.

## 3. 병합 전 눈 검증 — map_event_covered(S4 원칙, 표만 보고 통과 금지)
- 대상: iran_ceasefire_2026 v10 5건(콜드 오픈 2건은 §1 면제 적용 뒤 남는지 확인), showcase_geo 10건, china 12건 중 무작위 4건, diesel_road_2026 5건.
- 건마다 한 칸: 가림 비율이 가장 큰 표본 시각의 프레임, 사건 상자(빨강 외곽선)·덮개 상자(파랑 외곽선)·가림 % ·사건 종류·문장 id. `artifacts/speed-pipeline-v7.4.0` 의 `map_event_covered/` 에 칸 낱장 + 한 장 시트. 렌더는 기존 콘티 판 mp4 에서 프레임만 뽑아도 된다(재렌더 불필요).
- 감독이 눈으로 건마다 진짜 결함 / 오탐을 판정한다. 오탐이 있으면 원인(상자 계산·broll 구석·짧은 겹침 등)과 수정안을 R 에. 진짜 결함이면 그 트랙이 고칠 일이다(이 트랙은 고치지 않는다).
- 특히 diesel_road_2026 은 사용자가 "최고점"이라 한 기준 작품이다. 기준 작품에서 걸리는 건은 오탐 가능성을 먼저 의심한다.

## 4. S2-8 — loudnorm 측정 재사용(권고 수용)
- 재렌더 140초 중 약 100초가 loudnorm 2패스다. 1패스 측정값을 `sha1(mix.f32 바이트) + loudnorm 인자` 키로 `out/loudnorm_cache.json` 에 두고, 같으면 2패스만 돈다. 다르면 다시 잰다.
- 시험: 같은 mix → 측정 재사용·출력 바이트 동일, mix 1샘플 변경 → 재측정. 오디오 출력 LUFS 는 변하지 않아야 한다(audio_qa 값 비교).

## 5. 720p 측정(③)
- 골든 자산 복원 뒤 이란 8분으로: 첫 720p 렌더(옛·새), 같은 문장 수정 뒤 720p 재렌더(새). 목표 ≤ 15분.

## 6. 병합 순서
§1·§2 반영 커밋 → §4 → sweet-galileo 최신을 이 브랜치로 merge(충돌은 §1 기준으로 해결) → 빠른 묶음·anti_inertia·골든 25컷(dark·light) → 전체 pytest 1회(백그라운드) → §3 시트·§5 표와 함께 R-0602 → 감독이 최종 감독에게 렌더 상태를 확인한 뒤 D-1002 로 병합 승인. 승인 전에는 sweet-galileo 에 푸시하지 않는다.
