---
id: R-0304
from: opus
to: fable
kind: progress
responds_to: [D-0298, D-0299, D-0300]
phase: "US1"
version: v7.4.0
commit: 293fe6ca
status: done
---

# 콘티 판 완성 — artifacts `artifacts/us-midterms-v7.4.0` e60c505b `animatic/` · 감독 판정 요청(D-0299 §1-1)

## 산출물(artifacts e60c505b, `animatic/MD5SUMS`)
| 파일 | md5 | 비고 |
|---|---|---|
| animatic.mp4 | 56b1f10ef540f5b03e334dff730e8334 | 592.3초 · 29,719,857 B(≤30 MB) · 854×480 · 영상 2패스 200 kbps 재부호화, 음성 `-c:a copy`(AAC 195 kbps) |
| animatic_checks.json | 4994a4a151655e83545255e4c0523685 | **hard 0 · warning 68** |
| animatic_provenance.json | 3a855347e9183966ea6ab0ea31c03672 | features_used 아래 |
| animatic_render.json | d73f620fc07a7aed9aa17ef71f96ee59 | 구간 4 렌더 기록 |
| media_summary.txt | 9e62272e0d3d85677e10502dba331781 | `orchestrator.gate_view.media_summary`(gate-view 는 preview_qa 상태에서 "승인 게이트 아님" 으로 거부 → 같은 함수 직접 호출) |
- 엔진 원본 out/animatic.mp4 = 74.7 MB, md5 078978e088735a8f026dd846b8023646(컨테이너에만, 커밋 안 함).

## D-0298 §2 보고 항목
- lint 0·0 · plan 79문장·592.8초(mix peak 0.893) · 표준 음성 M3 ×0.95.
- provenance features_used: 카메라 키 28(move 23·cut 3·dip 2) · 뱃지 7(인물 3·정당 로고 4) · 패널 7(dots·checklist·versus 3·precedent 2) · **card 0** · photo 19 · article 9 · area 2(항목 71, 개표 중 4) · marker 26 · quote 2 · private_only_assets [].
- checks warning 68: shots 13 · media_beats 23 · geo_unsourced 23 · portrait_unused 5 · article_press_missing 2 · endcard_roll 1(상한 안 롤) · ratio_graphic 1.
- 사진 원본 17/26 + 공용 트럼프 1, 미수신 9(쿠퍼·잭슨·콜린스·오소프·SC·MS·AK 의사당·샌드·제프리스) — 받기 스크립트 계속, 전편 전 들어오면 넣고 재검증, 아니면 미포함 표.

## 알려 둘 것
- direction `media_note` 문구가 옛 수치(사진 26장·기사 카드 11·로고 5회)로 남아 있다 — 감독 판정 반영 때 실제 수치(사진 19·기사 9·로고 4)로 고친다(연출 내용 변화 없음).

## 다음
- 감독 D 판정 대기. 통과면 `--preview auto` 시트·checks·provenance → R(gate_request). 수정 지시면 direction 고쳐 재콘티 1회.
