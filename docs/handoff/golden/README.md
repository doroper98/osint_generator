# golden — v3 최종본 기준 산출물

Phase 1(골든 재현)·Phase 2(모듈 분해)의 비교 기준.
- `hormuz_korea_480p.mp4`: 사용자 확인을 거친 최종본(라운드 7 반영: 비네팅 없음, 엔딩 카드 재디자인, 미디어 7종)
- `frame_*.png` + `golden_frames.json`: 문장 앵커 기준 25개 시각의 기준 프레임. 새 엔진은 같은 앵커 시각에서 육안상 동일해야 한다(평균 절대 차이 < 2/255 목표, 폰트 렌더 차이 허용).
- `hormuz_korea_ko.srt`, `youtube_description.txt`: 자막·설명문 기준.
주의: 음성(edge-tts)이 바뀌면 절대 시각이 달라지므로 비교는 **앵커(문장 id + 오프셋)** 기준으로 한다.

## 저장소 반영 시 주석 (2026-09-27, Fable 분석 세션)
- `hormuz_korea_480p.mp4`(30.2MB, 4분 52.44초, 854×480, 24fps, AAC 44.1kHz)는 **git에 커밋하지 않는다**
  (`.gitignore`: `docs/handoff/golden/*.mp4`). 사용자가 보관한 원본을 로컬에 이 경로로 복사해 쓴다.
- 검증 결과: 이 mp4에서 `golden_frames.json`의 7개 시각을 추출해 `frame_*.png`와 비교했을 때
  평균 절대 차이 0.00/255 — PNG 25장은 mp4와 픽셀 단위로 동일하다. 따라서 Phase 1·2 프레임 비교는
  mp4 없이 PNG만으로 충분하다. mp4는 오디오(믹스·더킹·효과음)와 전환 연속성 검수에만 필요하다.

## v4.1.0 주석 — 골든 v3 원본의 국가 키 충돌 결함 (back_and_forth D-0078·D-0079, DECISIONS D69·D70)
골든 v3 원본은 KZ(및 AU 조각) 육지가 바다로 그려진 결함을 포함한다(D-0078·D69, PIPELINE-AP-011 — 같은 ISO 키 피처 덮어쓰기).
골든 PNG 는 바꾸지 않는다(사용자 합격본의 사료, `tests/test_golden_frozen.py` 가 25장 md5 를 고정한다).
그 9컷(04·05·15·16·17·18·23·24·25)의 정답 프레임은 `expected_deltas.json` 의 `geo_kz_d0078` 이 가리킨다
(`docs/handoff/reports/phaseG1/golden_delta/`, 무손실 엔진 렌더, 기준 커밋 f8e507a). `tools/golden_compare.py` 는 이 컷들을 의도된 차이로 뺀다.

