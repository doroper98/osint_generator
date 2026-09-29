# artifacts/phaseG3-v4.3.0 — Phase G3 시간축 무대 실증 (v4.3.0)

back_and_forth D-0084 작업 6. 사용자 검수 대상(참고 영상 — 합격 조건은 프리뷰 12컷 시트). 영상 본체·재현 입력은 작업 브랜치에 넣지 않고 이 orphan 브랜치에 둔다. 삭제하지 않는다.

| 경로 | 내용 |
|---|---|
| fed_timeline_demo/out/final.mp4 | 『금리와 물가, 두 줄의 기록』 — 연방기금 실효금리(FEDFUNDS)·소비자물가 상승률(CPIAUCSL 전년 대비) 시간축. md5 `70984b297a5777c503e9acbc9255e110`, 77.6초 854×480@24, AAC, 무음악(bgm null) |
| fed_timeline_demo/out/mix.flac | out/mix.f32(44.1kHz 스테레오 f32le) 무손실 |
| fed_timeline_demo/out/{provenance,audio_qa}.json · final.srt · credits.txt · description.txt | provenance stage timeline·genre macro_monetary(proposed)·series 2(CPI missing 2025-10), 오디오 QA(I −14.02) |
| fed_timeline_demo/direction.yaml | 작업 브랜치 `projects/fed_timeline_demo/direction.yaml` 과 같다(사람 작성) |
| shared/tts, shared/plan.json | edge-tts(ko-KR-InJoonNeural) 10문장 합성·타임라인 |

데이터: 작업 브랜치 `data/series/`(FRED, Public Domain: Citation Requested, 2026-09-29 수신, 2026년 8월 기준). 투자 권유가 아닌 정보 제공 목적.

## 복원 절차 (새 컨테이너)
```bash
git fetch origin artifacts/phaseG3-v4.3.0
mkdir -p /tmp/artG3 && git archive FETCH_HEAD shared | tar -x -C /tmp/artG3
P=projects/fed_timeline_demo; mkdir -p $P/tts $P/assets && cp -r /tmp/artG3/shared/tts/. $P/tts/ && cp /tmp/artG3/shared/plan.json $P/
python -c "from pathlib import Path; from tools.commons_fetch import record_bundles; record_bundles(Path('$P/assets/rights_registry.json'))"
python -m engine.render $P --preview auto
python -m engine.render $P --jobs 4 && python -m audio.mix $P && python -m engine.mux $P
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v4.3.0), Opus 클라우드 컨테이너.
