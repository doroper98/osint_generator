---
id: R-0228
from: opus
to: fable
kind: phase_report
responds_to: [D-0222, D-0223, D226, D227]
phase: "A1"
version: v7.2.0
commit: 6f8396f
status: needs_review
---

# v7.2.0 — 합격 BGM 등록·실측 하한(UF-100) + gulf_china_arms_2026 전편 전달(D-0223)

## 1. v7.2.0 BGM(D-0222) — 커밋 bf12fbb·ea86575
- 등록: `music.zabriskie_mario_bava`. Bandcamp 는 403 이라 archive.org 전집 미러에서 받았다. 사유와 `source_url` 을 레지스트리·RIGHTS.md 에 남겼다.
- 파일: sha1 `02ceb4e748b003fb7447ccd74b0ccf4fad64d3fb`, 511.269초. 조사 세션 청취 파일과 같다.
- 표기: 작가 요청 형식(앨범 Vendaface 포함). Patriarch 표기도 앨범을 보강했다. RIGHTS.md 표기는 따옴표가 들어 있어 백틱으로 감쌌다(시험 정규식 동기화).
- Drone in D: available false + `unavailable_reason`(Content ID 사전 등록).
- 하한 키 `rules audio.bgm_floor`: 박 명확도 ≥ 6, 온셋 ≥ 분당 300, 300~3000 Hz ≤ 0.10, 0~360초, sr 22050, n_fft 4096.
- 측정 함수 `audio/bgm_measure.py`(librosa 0.11.0, requirements-engine 반영). CLI `--check` 는 레지스트리 전체를 재측정해 대조한다.
- 레지스트리 모델: available 곡은 `measured` 필수, 하한 미달이면 검증 오류.
- 실측: Mario Bava 6.55·473.5·0.088. Patriarch 7.12·328.7·0.029 → 기준 곡 통과.
- 측정 방식 메모: 조사 세션 스크립트는 hop 2048 + RMS 게이팅, librosa 1.0.0 이다. 여기서는 0.11.0 이다. 대역 비중이 처음에 10.5% 로 갈렸고 n_fft 4096 으로 맞추자 세 값이 일치했다.
- 기본 BGM 순서 `audio.bgm_default: [mario_bava, patriarch]`. 원장 UF-100 guarded.
- 음량(music_under_narration_db·bed_gain)은 값 변경 없음. 이번 전편 실측은 §2 에 적었다.

## 2. gulf_china_arms_2026 전편(D-0223·D227)
- 산출물: orphan 브랜치 `artifacts/gulf_china_arms_2026-v7.2.0`(2e39d41).
  - final.mp4, final.srt, description.txt, provenance.json, audio_qa.json, prev/sheet.jpg(컨택트 시트), prev/checks.json, MD5SUMS.
  - 콘티 판·프리뷰 시트는 앞서 `artifacts/gulf_china_arms_2026-v7.2.0-animatic`(9413d07).
- final.mp4: md5 `f0d697aba6e52b70d91df2ee2284463c`, 1280×720, 256.87초, 33문장.
- 소리: −14.1 LUFS, TP −1.41, 내레이션 아래 음악 −11.9 dB(허용 [−13, −9] 안). BGM Mario Bava.
- 검사: hard 0, 경고 17. 연출 sha1 일치(from_current_direction true).
- provenance `user_feedback_guards` 42건 모두 0. camera_bounds·연속성·속도 0.
- 지도 테마 light(장르 기본값).
- 육안 확인 6컷(4·27·47·100·178·245초): 오프닝 넓은 지도·기사 위 제목·Army Recognition 기사·협정 카드와 뱃지·이라크 캐스케이드·중국 강조와 경로가 보이는 엔딩. 이상 없음.
- 원장: 이번 영상에서 새 사용자 의견 없음. open 0건.

## 3. 연출 손질과 감독 관찰 반영
- AI 초안은 `direction.ai_v1.yaml` 로 보존했다. 손질본 8샷.
  - 중국을 말하는 구간: 75°E·w76 넓은 화면(경계 안).
  - 오프닝 w76→28, 7초.
  - 청두→카므라 경로 `cn_pk`(JF-17 공동 개발).
  - 사우디 뱃지를 공식 확인 장면 앞뒤로 나눴다.
- 콘티 판 hard 5·프리뷰 frame_missing 8 → 연출 수정으로 0.
- 관찰 (1) 천궁-II 카드 캐스케이드 시점: 사우디·이라크 항목을 `korea_2`·`korea_3` 문장 시작 +0.3초로 맞췄다(2d60a04).
- 관찰 (2) 빈 상자: 0.2~0.3초 페이드라 정상으로 판정받았다. 변경 없음.
- 관찰 (3) 자문·훈련 주석: 불필요 판정에 따라 넣지 않았다. 보류 항목으로 남긴다.

## 4. 사실 상태(원고 귀속)
- 공식 확인: 파키스탄군 사우디 주둔(ISPR 10/07). 파키스탄 전투기 킹 압둘아지즈 공군기지 도착(사우디 국방부 04/11, 기종 미기재).
- 보도 수준: HQ-9, JF-17 약 16대, 병력 약 8,000, 드론 2개 대대, 파키스탄 운용·사우디 비용(Reuters 05/18 익명 소식통, 양국 정부 논평 없음). 원고는 이 귀속 그대로다.
- 워커 초안의 "알자지라가 JF-17 도착 보도" 는 기종 미기재로 바로잡았다.

## 5. 실수 기록 — 추적 대상이 아닌 파일 커밋
- 29baaa6 에 tts/(41 MB), 이어서 assets/·미디어 jpg 가 들어갔다. 448585b·ed10a02·7af616f 로 추적을 해제했다. 강제 푸시 금지라 기록에는 남는다.
- 권리 문제 파일은 없다. tts 는 자체 생성 음성, assets 는 Natural Earth·AWS 지형 파생 타일, 미디어는 PD JF-17 사진과 공공누리 제1유형 M-SAM 사진이다. 언론 사진은 없다.
- 재발 방지: 새 프로젝트 `.gitignore` 에 tts/·out/·prev/·assets/·llm_calls/·미디어 바이너리를 넣었다. 프로젝트 생성 시 기본 .gitignore 를 만드는 장치는 아직 없다. 필요하면 지시 바란다.

## 6. 남은 일
- 사용자에게 직접 보낸 것은 없다(D227). 전달은 감독 몫.
- 보류 유지: 자산 사전 점검, 검증 LLM 다중 출처 건너뜀, fed_policy 섬 카메라, Q4a·Q4b·Q5·Q6·G, 자문·훈련 주석.
