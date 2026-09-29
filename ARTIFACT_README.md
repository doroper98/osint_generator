# artifacts/phaseG7-v4.8.0 — G7 요소 크기 (v4.8.0)

back_and_forth D-0101(사용자 결정 D89)·D-0104 D2(c)·D6·D-0109(D98)·D-0111·D-0112·D-0113. 인물 뱃지 적응 크기(한 명 56 / 여럿 30~34), 기사 카드 조판(w 440·헤드라인 18, fed_policy 두 건 가운데), 화면 글자 크기 표(본문 ≥ 12·메타 ≥ 9, 자막 21), 사진 켄 번스 연속 변환, 청와대 휘장 등재. 전편은 **480p 두 편만** 만들었다(1080p 생략, D-0113·재기동 21 지시).

| 경로 | 내용 |
|---|---|
| fed_policy_2026/out/final_480p.mp4 | 『연준, 다시 금리를 올리다』 480p 전편 — md5 `6920c35d5b4e025147c5e312bcb7af5e`, 307.12초 854×480@24, I −14.04 LUFS · TP −1.83 dBTP |
| hormuz_korea/out/final_480p.mp4 | 『호르무즈와 한국』 480p 전편(사용자 비교용) — md5 `9d00319d0651ebeb0b05b90e577fd3ac`, 292.44초, I −14.05 LUFS · TP −1.72 dBTP |
| */out/provenance_480p.json | repo_version 4.8.0, rules_hash 745bf177… |
| */out/final.srt · credits.txt · description.txt · audio_qa.json | 자막·크레딧·설명문·오디오 QA(두 편 hard 0) |
| fed_policy_2026/prev_g7/ | auto 프리뷰 22컷(= 작업 브랜치 `reports/phaseG7/regression_baselines.json` 22/22), checks hard 0 |
| hormuz_korea/prev_g7/ | 골든 프리뷰 25컷(= `reports/phaseG7/hormuz_baseline.json` 25/25), checks hard 0 |

오디오: 두 편 모두 `python -m audio.mix` 로 다시 계산했다(G6.5 norm_ref 0.7·post_limiter). 오디오 스트림 md5(`ffmpeg -map 0:a -c copy -f md5`): fed_policy `01fac3e4fbed8230edad3e117abc39a8`, hormuz `98ae5d3f416438175dee1feec992b620`. 음량 값은 G6.5 `audio_qa_norm_ref07.json` 과 같다.

재현 입력: hormuz = `artifacts/phase7-v3.3.0` shared, fed_policy = `artifacts/phaseG4-v4.4.0` shared(+ phaseG5 README 의 AI 연출 기록 복원). 연출 파일은 작업 브랜치의 것(fed_policy 기사 2건 `place: center`, D-0101 §2). 청와대 휘장은 새 컨테이너에서 `python -m tools.commons_fetch emblems projects/hormuz_korea --only cheongwadae` 가 필요하다(두 편 모두 쓰지 않음, 갤러리·테스트용).

```bash
python -m audio.mix projects/fed_policy_2026 && python -m engine.render projects/fed_policy_2026 --jobs 3 && python -m engine.mux projects/fed_policy_2026
python -m audio.mix projects/hormuz_korea && python -m engine.render projects/hormuz_korea --jobs 3 && python -m engine.mux projects/hormuz_korea
# out/final.mp4 → final_480p.mp4
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v4.8.0, d4cfe12), Opus 클라우드 컨테이너.
