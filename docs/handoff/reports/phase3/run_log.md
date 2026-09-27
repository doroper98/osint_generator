<!--
tier: 3
last_synced_with: v2.2.0
ssot_for: [phase3-run-log]
depends_on: [geo/prep.py, geo/prep_geometry.py, geo/prep_tiers.py, engine/render.py, tools/golden_compare.py]
last_review: 2026-09-27
-->

# Phase 3 실행 기록 — 지오 일반화 (v2.2.0, Opus 클라우드 컨테이너)

## 준비
Phase 1 에 받은 Natural Earth 3종·지형 타일(W z5 77장, G·K z7 58장)을 `data/geo/{ne,tiles/z5,tiles/z7}`에 하드링크로 넣었다(캐시 규칙: `data/geo/`, gitignore).
hormuz_korea `assets/`는 Phase 1 하드링크를 끊고, 지오 외 자산(인물·휘장·국기·권리 레지스트리)만 복사했다.

## 명령
| 단계 | 명령 | 결과 |
|---|---|---|
| hormuz 지오 | `python -m geo.prep projects/hormuz_korea` | ok. W land-miss small=[MV](5.1px² < 16, D29), G·K 없음. 16초 |
| 대만해협 지오 | `python -m geo.prep projects/taiwan_strait` | ok. 새 타일 32장 받음, land-miss 없음. 8초 |
| 대만해협 원고 | `python -m script.plan projects/taiwan_strait --tts edge` | ok, 2문장, 22.64초 |
| 대만해협 프리뷰 | `python -m engine.render projects/taiwan_strait --preview 3.0,7.5,16.0` | taiwan_sheet.jpg |
| hormuz 25컷 | `python tools/golden_compare.py --engine new --ref docs/handoff/reports/phase2/frames --out docs/handoff/reports/phase3` | MAD 0.0000 (평균·최대) |
| 골든 직접 대조 | `python tools/golden_compare.py --engine new --reference golden --out docs/handoff/reports/phase3/vs_golden` | 평균 1.825/255, 최대 3.10 (H.264 추출본 참고값, Phase 1 legacy 대 골든과 같은 값) |
| hormuz 전편 | `python -m engine.render projects/hormuz_korea --jobs 4` | video_noaudio.mp4 md5 31159ccb… = Phase 1·2 와 동일 → artifacts 브랜치 생략(D28) |

## 자산 대조 (asset_md5.json)
base_{W,G,K}_* 9장 전부 md5 동일. geo.pkl 의 coarse·fine·meta·admin1·places 값 동일(v3 geo3.pkl 의 `tiers` 키는 엔진이 쓰지 않아 뺐다 — 티어는 tiers.pkl).

## 엔진 변경 (렌더 수치 무변경)
- `View.base` 상세 티어를 G·K 고정 이름 대신 "W 외 전부, 정의 순서"로(대만해협 KeyError 수정). 블렌딩 규칙 그대로.
- 권리·미디어 레지스트리 파일이 없는 프로젝트 = 빈 레지스트리(쓰면 preflight 오류).
- 엔진이 `assets/geo.pkl`을 읽는다(옛 이름 geo3.pkl).
