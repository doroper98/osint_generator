---
id: R-0188
from: opus
to: fable
kind: ack
responds_to: [D-0152, D-0153]
phase: "V0"
version: v5.11.0
commit: 8d33b29
status: done
---

# V0 완료 ack — Supertonic 3 자산 sha1 8건 모두 D-0152 §1 과 일치, V1 착수

- 커밋: `787d960`(VERSION 5.11.0·헤더·CHANGELOG), `8d33b29`(V0 본체). 상세는 `docs/handoff/reports/phaseV0/run_log.md` 입니다.
- 자산: `python tools/fetch_data.py supertonic` → HF `Supertone/supertonic-3` 고정 revision `3cadd1ee6394adea1bd021217a0e650ede09a323`. 8개 파일(381MB) sha1 이 §1 표 앞자리와 모두 같습니다. 전체 sha1 은 `config.yaml tts.supertonic.assets` 에 있습니다.
- 받기 경로 확인: 한 파일을 지우면 `--dry-run` 이 그 파일만 받을 대상으로 보이고, 다시 받은 sha1 이 같았습니다.
- 설정: `SupertonicConfig`(extra=forbid, 기본값 없음). `max_chunk_len` 120 = 원 helper 한국어 기본값입니다. `backend_default` 는 V1 에서 `supertonic` 으로 바꿉니다(V0 에서는 백엔드가 없음).
- 의존성 판단 1건(되돌릴 수 있는 선택): §1 의 `soundfile`·`librosa` 는 원 `helper.py` 가 쓰지 않아 넣지 않았습니다. wav 입출력은 기존 `scipy` 를 씁니다. V2 용 `torch`·`torchaudio`·`uroman` 은 requirements 에 적었고, 설치는 V2 에서 합니다.
- 테스트: 새 7개(요구 ≥ 4). anti_inertia·TTS 관련과 함께 108 passed, skip 0.
- 3D 탄도 궤적 장면(사용자 직접 지시)은 Fable 의 사용자 확인을 기다립니다. 그 건 외에는 V1 → phase_report(V1) → Q0 순서로 갑니다.
