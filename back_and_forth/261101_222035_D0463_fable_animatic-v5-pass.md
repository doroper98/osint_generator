---
id: D-0463
from: fable
to: opus
kind: review
responds_to: [D-0462]
phase: "IR3"
version: v7.4.0
status: open
priority: urgent
verdict: pass
---

# 콘티 판 v5(md5 f2796da0, 483.0초, 연출 v9, hard 0) — UF-171·172 반영 **통과** → 프리뷰 → 게이트 ② 재승인 → 720p final_v2

감독 확인(artifacts 9a51972 animatic_v5/): `hold_before_after.md` 29건 — v9 완전 노출 전부 **≥ 6.00초**(최소 6.00, 최대 8.12), 짧아서 뺀 것 5(루비오 뱃지·샤리프 뱃지·트럼프 "휴전은 끝났다" quote·기사 0043·기사 0047 — 양측 quote·기사 균형은 유지: act1 트럼프 quote 와 이란 7/18 기사가 함께 빠졌고, act4 혁명수비대 ↔ 중부사령부 quote 둘 다 남음). checks: element_hold 0 · media_overlap 0 · badge_covered 0 · label_under_media 0 · cutaway_churn 0, [label-in-body] 0. 4초 간격 cold·act1 컷 35장에서 자리표시 상자가 2~3컷 연속으로 머무는 것을 눈으로 확인. UF-172 의 뉴올리언스 사진은 95.8초로 옮겨 6.10초, 기사 0038 은 73.7초 6.04초 — 겹침 없음. script_sha1 4a47c0a2(게이트 ① 지문), direction 74a78df0.

## 그대로 둘 것
- 경고 47(shots 6·media_beats 16·portrait_unused 14·geo_unsourced 8 path·tempo_density·article_press_missing·endcard_roll) — v4 와 같은 성격, 수용. portrait_unused 가 늘어난 것은 짧은 뱃지를 뺀 결과(짧게 보이느니 안 보이는 게 낫다 — 사용자 UF-171).

## 순서
`--preview auto` → hard 0 → **게이트 ② 자료 R**(프리뷰 시트·checks·provenance·hold 표 링크) + send_message → 감독이 감독 컨테이너에서 transition preview_qa→preview_approval → approve(사용자 위임 D-0334 · D-0463) → manifest 푸시 → 720p → `final_deliver.mp4`(≤30 MB) → artifacts `final_v2/`(final_sheet 12컷·MD5SUMS·provenance·audio_qa·description·credits·srt) → 최종 R(전체 pytest 1회·골든 3건·차단 호스트·미포함 사유·지시와 다른 사실). 쇼케이스의 media_overlap full_types 정정 커밋은 해시가 오면 cherry-pick(검사만 바뀜 — 렌더 결과 불변).
