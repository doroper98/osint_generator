# artifacts/phaseG8-v4.9.0 — G8 콘티 판(animatic) 루틴 (v4.9.0)

back_and_forth D-0108(사용자 결정 D97). `python -m engine.render <proj> --animatic` 의 결과 두 편. 검토용 — **배포 금지**(화면 위 띠·mp4 메타데이터 표식, deliver 가 거부).

| 경로 | 내용 |
|---|---|
| fed_policy_2026/out/animatic.mp4 | 『연준, 다시 금리를 올리다』 콘티 판 — md5 `bfb93d188f702d09539f06680d583fed`, 307.12초 854×480@24, 17.1MB. 4코어 단독 실측 124.4초(렌더 72.1·음성 43.1) |
| hormuz_korea/out/animatic.mp4 | 『호르무즈와 한국』 콘티 판 — md5 `c5c8fb2eb8e03a2f62fb1b40dc0b3f1b`(3회 동일), 292.44초, 17.7MB. 4코어 단독 실측 117.9·118.7초(렌더 67.7·음성 42.6) |
| */out/animatic_provenance.json | `animatic: true`, `animatic_run`(자리표시 수·건너뛴 검사·막지도 자료 md5·시간), repo_version 4.9.0 |
| */out/animatic_checks.json | 콘티 프로파일 — hard 0, skipped 9 |
| */prev_animatic/ | `--animatic --preview auto` 시트·checks·frames |
| noasset_hormuz/animatic_provenance.json | 자산 없는 폴더(추적 파일 + plan.json + mix.f32)에서 같은 CLI — 111초, images_used [] . 영상 md5 `1175f426…` 는 위와 엔딩 카드 구간(281.9~292.1초, 245프레임)만 다르다(권리 레지스트리 없음 → 크레딧 auto 절이 비고 license_ref 자리는 rules animatic.missing_license) |

재현 입력: hormuz = `artifacts/phase7-v3.3.0` shared, fed_policy = `artifacts/phaseG4-v4.4.0` shared. 음성은 두 편 모두 기존 edge-tts plan.json(ko-KR-InJoonNeural), 믹스는 `python -m audio.mix`(fed mix.f32 md5 = G7 `0b664780…`).

```bash
python -m audio.mix projects/fed_policy_2026 && python -m engine.render projects/fed_policy_2026 --animatic --jobs 4
python -m audio.mix projects/hormuz_korea && python -m engine.render projects/hormuz_korea --animatic --jobs 4
```
VERSION 파일은 커밋 훅(prefix = VERSION) 용이다. 생성: overhaul/v2-map-engine (v4.9.0, ea2dee0), Opus 클라우드 컨테이너.
