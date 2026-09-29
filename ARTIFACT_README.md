# artifacts/phaseG5-v4.5.0 — G5 검증 라벨 본문 제거·엔딩 카드 한 줄·크레딧 열 재배치 (v4.5.0)

back_and_forth D-0096(사용자 결정 D85, CLAUDE.md C9 개정). 『연준, 다시 금리를 올리다』(projects/fed_policy_2026) 재렌더. 원고·연출(direction v7)·오디오는 G4 그대로이고, 자막 첫 줄 `<미검증>`·`<논쟁>` 접두가 빠지고 엔딩 카드 맨 마지막 줄에 "확인되지 않은 보도·논평 인용 11건 — 출처는 위 목록"(가장 작은 글씨) 한 줄이 붙었다. 삭제하지 않는다.

**2차 갱신(back_and_forth D-0098 §2·§4, D-0099 A, 작업 브랜치 b558eac)**: 첫 판(3a2b8e1)은 엔딩 카드 오른쪽 크레딧 열이 하단 구분선 아래로 넘쳐 국기·음성 절이 잘렸다. `credits.yaml` 에서 사진·기사 카드를 한 절 "사진 · 기사 카드" 로 합치고 열을 재배치(왼쪽 자료·보도·국기 / 오른쪽 안내·글꼴·음성·사진 · 기사 카드, 마지막 기준선 415·423 ≤ 한도 428), 자료 절의 같은 줄 반복(FEDFUNDS·목표 범위 레코드)을 한 줄로 합쳤다. 영상에서 바뀐 것은 엔딩 카드뿐(프리뷰 22컷 중 엔딩 2컷만 첫 판과 다름). 첫 판 md5: 480p `5aa5a527…`, 1080p `6b82cdef…`.

| 경로 | 내용 |
|---|---|
| fed_policy_2026/out/final_480p.mp4 | 480p 전편 — md5 `3eb4ae2a8eb48886dac23caedb9d1862`, 307.1초 854×480@24 |
| fed_policy_2026/out/final_1080p.mp4 | 1080p 전편 — md5 `a65ac872bae31f6f9ba37e492f7ca9aa`, 1920×1080@24 |
| fed_policy_2026/out/provenance_{480p,1080p}.json | G4 판과 차이 = repo_version·rules_hash 두 칸뿐(첫 판과는 rules_hash 한 칸)(script.labels verified 27·corroborated 8·unverified 9·disputed 2 그대로) |
| fed_policy_2026/out/final.srt · credits.txt · description.txt · audio_qa.json | 자막·크레딧·설명문·오디오 QA(I −14.02 LUFS, TP −1.59 = G4 동일) |
| fed_policy_2026/prev_g5/ | G5 코드 auto 프리뷰 22컷 원본 해상도 PNG·시트·frames·checks(hard 0) |

오디오: 두 mp4 의 오디오 스트림 md5(`ffmpeg -map 0:a -c copy -f md5`)가 G4 판(`artifacts/phaseG4-v4.4.0`)과 같다(`06324317…`). 무손실 믹스는 G4 브랜치의 `mix.flac` 을 쓴다.
2차 갱신도 `python -m audio.mix` 로 믹스를 다시 계산했다(G4 `mix.flac` 을 f32 로 풀어 쓰면 s32 양자화 때문에 오디오 스트림 md5 가 달라진다 — 18a562f4, 쓰지 않음).
재현 입력(tts·plan.json·media_src·intake 본문·assets)은 바뀌지 않았다 — `artifacts/phaseG4-v4.4.0` shared 와 그 ARTIFACT_README 복원 절차 그대로.

## provenance ai_direction 기록 복원
AI 연출 기록 파일(direction.meta.json, prev/qa_verdict·revision·qa_loop)은 작업 브랜치에서 git 무시 대상이고 G4 브랜치에도 없었다. 새 컨테이너에서는 작업 브랜치 `docs/handoff/reports/phaseG4/fed_policy/run2·run3` 사본을 `projects/fed_policy_2026/prev/` 에 넣고, direction.meta.json 을 G4 provenance 가 기록한 값(origin ai, model `config.yaml llm.model`, prompt_sha1 903e5087…)으로 만들었다. `engine.provenance.ai_direction_summary` 결과가 G4 provenance 의 ai_direction 과 같음을 확인했다. 연출을 다시 돌리지 않았다.

```bash
# G4 복원(phaseG4 ARTIFACT_README) 뒤
R=docs/handoff/reports/phaseG4/fed_policy; P=projects/fed_policy_2026
cp $R/run2/qa_verdict.v1.json $R/run2/revision.v2.json $R/run2/revision.v3.json $P/prev/
cp $R/run3/qa_verdict.v2.json $R/run3/qa_verdict.v3.json $R/run3/revision.v{4,5,6,7}.json $R/run3/qa_loop.json $P/prev/
echo '{"origin":"ai","model":"config.yaml llm.model","prompt_sha1":"903e50877c53f08ac39e20c0855a04cf7c54c0c8"}' > $P/direction.meta.json
python -m engine.render $P --jobs 4 && python -m audio.mix $P && python -m engine.mux $P
python -m engine.render $P --jobs 4 --res 1080p && python -m engine.mux $P
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v4.5.0), Opus 클라우드 컨테이너.
