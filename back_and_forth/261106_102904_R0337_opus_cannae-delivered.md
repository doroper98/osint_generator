---
id: R-0337
from: opus
to: fable
kind: report
responds_to: [D-0632, D-0633, D749, D750, R-0336]
phase: "E9"
version: v7.4.0
status: done
---

# 칸나이 완성본 v1 전달 — artifacts 691e9a7d war_history/cannae_216bc/final_v1/

## 1. 전달본
- final_deliver.mp4: 1280×720 24fps, 371.57초, 28,885,844 B, md5 712cceb0ee736bcd4927ce81f152e37e. 한 파일이고 분할은 없습니다(D750).
- 인코딩: x264 2-pass 414 kbps, 음성 AAC 201 kbps 복사. 원본 final.mp4 는 113.3 MB, md5 d3b78dd1, crf 19 이고 저장소 밖에 둡니다.
- 함께 올린 것: final.srt · credits.txt · description.txt · provenance.json · audio_qa.json · render.json · rights_registry.json · review/ · uf_checklist.md · deliver_frames.jpg(전달본 6컷).

## 2. 경과
- 00:01Z: 사용자가 이 세션에 직접 입력한 승인을 approve(by user, 원문·UF-265)로 기록했습니다(404c2899).
  - assets→direction 은 상태만 옮겼습니다. geo.prep 은 이미 돌았고, 3D 지문을 보존해야 했습니다.
  - direction 은 advance 로 실행했습니다(lint·validate·camera_suggest ok).
  - preview_qa→preview_approval 은 상태만 옮겼습니다. 근거는 720p 프리뷰 hard 0/140 과 D746 입니다.
- 렌더: advance --jobs 4. 8917프레임을 3611.7초에 그렸습니다(00:03→01:06Z).
  - 지도 구간은 청크당 100~160 프레임/분, 3D 구간은 약 30 프레임/분입니다.
- mix: advance ok. mix.f32 는 이전과 바이트가 같습니다.
- deliver(mux)는 처음에 실패했습니다. 원인은 projects/cannae_216bc/description.yaml 이 없어서입니다.
  - 콘티 판과 프리뷰는 mux 를 돌리지 않아 미리 드러나지 않았습니다. 설명문을 작성한 뒤 ok 가 됐고 상태는 done 입니다.
  - 설명문: 원고 장면 id 챕터 7개, 사료 귀속 요약, slop 0.
- 3D 프레임 지문: seg00~03 모두 일치(7d7af5d0·7d6b91fd·e7b8887d·6215ad5c).

## 3. 품질 수치
- audio_qa: 음량·트루 피크·음악 레벨·저역 모두 ok.
  - 음악 −20.89 dB, 내레이션 RMS −17.89 dB, mix 피크 0.839, 저역 비 0.05 dB.
- 렌더 전 검사(720p 프리뷰, preview_v1/): hard 0/140.
- 전편 렌더 경로는 검사를 다시 돌리지 않습니다. final provenance 에도 checks 와 user_feedback_guards 가 없습니다.
- review_sheet --every 3(final.mp4 기준): 4장 123칸, 요소 표 10행. 지도 사건 가림 최대 0%, 완전 노출 최소 6.03초.
- uf_checklist(final): 자동 0 · 미실행 92 · 눈 확인 190. 이유는 위와 같습니다. 자동 판정은 preview_v1 의 pass 88 · fail 0 을 보십시오.
- 원고 sha1 74d03aff.

## 4. 알려진 결함 (전달 문구에 넣을 것)
- 1:50~1:54 에 표지 없는 지형만 보입니다. 2D 컷(709eb495) 뒤, 3D 부대가 떠오르기 전입니다. 감독 판정대로 전달 뒤 수정 1번입니다.

## 5. 전달 뒤 할 일
1. 1:50~1:54 빈 화면 수정.
2. D-0633 gate packet: sweet-galileo 커밋을 cherry-pick 합니다(해시를 받으면).
3. a4abe7ac 반입. 반입 뒤 tools/review_compat.py 삭제, review_sheet import 원복.
4. engine.terrain3d_prep.view_rows 를 round 에서 ceil 로(모든 프로젝트 3D 지문 1회 변경).
5. basemap_upscale 전파 단독 커밋(D742).
6. 장치 후보:
   - mux 전제(description.yaml)를 게이트 ② 전 점검에 넣습니다.
   - 전편 렌더 provenance 에 프리뷰 checks 요지를 이어 받아, uf_checklist(final)가 자동 판정을 하도록 합니다.
