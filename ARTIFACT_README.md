# artifacts/phaseG4-v4.4.0 — Phase G4 첫 비지정학 영상 (v4.4.0)

back_and_forth D-0090 작업 4·9, D-0093. 『연준, 다시 금리를 올리다』(projects/fed_policy_2026, 장르 macro_monetary proposed, 주 무대 timeline). 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| fed_policy_2026/out/final_480p.mp4 | 480p 전편 — md5 `16f6e9452616167741e2037a92f07667`, 307.1초 854×480@24, AAC, 무음악(bgm null), I −14.02 LUFS |
| fed_policy_2026/out/final_1080p.mp4 | 1080p 전편 — md5 `9e68c8d7e6f1dda44735d7a780981f03`, 1920×1080@24(같은 mix) |
| fed_policy_2026/out/provenance_{480p,1080p}.json | genre macro_monetary(proposed)·order 결정 상태(by default = 사용자 미확정)·elements(dot_plot·statement_diff approval pending)·series 5·배치 stage:timeline_* |
| fed_policy_2026/out/mix.flac · final.srt · credits.txt · description.txt · audio_qa.json | 믹스 무손실·자막·크레딧·설명문·오디오 QA |
| fed_policy_2026/prev_selected/ | 선택 판(direction v7) 프리뷰 22컷 원본 해상도 PNG·시트·frames·checks(hard 0) — 게이트 ② 육안 검수용 |
| shared/tts, shared/plan.json | edge-tts(ko-KR-InJoonNeural) 48문장 합성·타임라인 |
| shared/media_src/ | 연준 이사회 Flickr 기자회견 사진 원본 3장(Public Domain Mark — 사진 페이지 license 10 을 `tools/media_fetch` 가 확인) |
| shared/intake_bodies/ | 연준 공식 문서 본문 9건(성명 8·의장 모두발언 1, 미국 연방정부 기관 발표). 기사 본문 6건은 저작권 때문에 싣지 않는다 — `add-source --fetch` 로 다시 받는다 |
| shared/assets/ | 권리 레지스트리(묶음 + people.warsh)·워시 라이브러리 초상 가공본 |

데이터: 작업 브랜치 `data/series/`(DFEDTARL·DFEDTARU·FEDFUNDS·CPIAUCSL = FRED Public Domain: Citation Requested, SEP_20260916 = 연준 SEP 그림 2). 투자 권유가 아닌 정보 제공 목적.

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phaseG4-v4.4.0
mkdir -p /tmp/artG4 && git archive FETCH_HEAD shared | tar -x -C /tmp/artG4
P=projects/fed_policy_2026; mkdir -p $P/tts $P/media $P/assets/flags $P/intake/bodies
cp -r /tmp/artG4/shared/tts/. $P/tts/ && cp /tmp/artG4/shared/plan.json $P/
cp /tmp/artG4/shared/media_src/*.jpg $P/media/ && python tools/media_fetch.py $P --only fed_presser_0916,fed_presser_0916_b,fed_presser_0729 --no-sheets
cp -r /tmp/artG4/shared/assets/. $P/assets/ && cp projects/hormuz_korea/assets/flags/us_* $P/assets/flags/
cp /tmp/artG4/shared/intake_bodies/*.txt $P/intake/bodies/
# 기사 6건 본문: intake/sources.json 의 url 로 다시 받는다(statement_diff 대조는 연준 성명 본문만 쓴다)
python -m engine.render $P --preview auto
python -m engine.render $P --jobs 4 && python -m audio.mix $P && python -m engine.mux $P
python -m engine.render $P --jobs 4 --res 1080p && python -m engine.mux $P
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v4.4.0), Opus 클라우드 컨테이너.
