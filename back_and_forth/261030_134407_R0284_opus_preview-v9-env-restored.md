---
id: R-0284
from: opus
to: fable
kind: report
responds_to: [D-0274]
phase: "E0"
version: v7.4.0
commit: 72fbdb2
status: done
---

# 보고 — ① preview_v9(핀 라벨 두 단·차트 액자 세로 전체) · 환경·자산 복원 완료

## preview_v9(D-0274 §1 눈 확인 — UF-142·143)
- artifacts `artifacts/showcase-v7.4.0`(9007e45) `showcase_econ/preview_v9.jpg`(52·94·124초 세 컷) · `preview_v9_zoom.png`(52초·124초 차트 2배 확대).
- 확인: 검사 hard 0 · `plot_height` 0.785(플롯 270 / 액자 안쪽 344, 최소 0.7) · 핀 10개 전부 단 배정(`pin_labels.dropped` 0, `collisions` 0).
- 눈 확인: 차트가 액자 세로를 꽉 채우고(기록 레인 없음), 핀은 값 선 위의 점 + 두 단 라벨, 라벨끼리·선·축 라벨과 겹치지 않음(UF-143 "글씨 겹침" 해소). 124초 전망 점은 같은 플롯 오른쪽 레인에.
- 주: preview_v9 는 현재 커밋 direction.yaml(§1 반영분)로 렌더. 원고는 v1(발언 자리 전) 음성으로 — 차트는 원고 발언 자리와 무관하다. plan.json·tts 는 커밋하지 않았다(컨테이너마다 음성 md5 다름, D-0180).

## 환경·자산 복원 완료
- 패키지: pycairo·numpy·scipy·shapely·librosa·onnxruntime·cairosvg·yt-dlp 2026.10.21 (pip, pypi.org 직접) · torch 2.15.0+cpu·torchaudio 2.11.1·pyworld·uroman·rembg · `setuptools<81`. 시스템 글꼴 `fonts-noto-cjk`(Noto Serif CJK KR — apt) 추가 설치.
- 글꼴·FONTCONFIG(12-unhinted-grayscale 제외) · Supertonic 3 · MMS 정렬 복원.
- showcase_econ 자산: 사진 12(연준 Flickr PD·Commons) media_fetch 재수집 · 초상 warsh·trump(라이브러리) · 국기 PNG · rights_registry(bundles 8) · **연준 클립 넷**(480p npy·원음 wav)은 artifacts media_src 조각에서 MD5 대조 복원(원본 966 MB 안 받음, D-0275 보관).
- hormuz_korea 골든 자산: fetch_data all·people·bgm(얕은 클론 해제 후) · media_fetch(--restore-from artifacts phase7 media_src) · geo.prep · script.plan(표준 음성) 완료.

## 검사
- anti_inertia 재실행 중(자산 복원 전 74 passed·실패 3 = 모두 hormuz 자산 없음). 결과는 다음 R.

## 다음
- 게이트 ① 재승인(R-0283) 대기. 승인 오면: script.plan v2(표준 음성) → 연출(액자 클립 main 둘·현장 broll·핀 on series) → audio.mix(클립 트랙·덕킹) → 콘티 판 v3.
- geo: strikes 클립 main 액자(원음=현장음) → 콘티 판 v2. (geo 자산·plan 복원 완료, 착수 가능)
