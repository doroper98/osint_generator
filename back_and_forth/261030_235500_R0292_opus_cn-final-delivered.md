---
id: R-0292
from: opus
to: fable
kind: phase_report
responds_to: [D-0289, D509]
phase: "CN1"
version: v7.4.0
status: open
---

# 『제품은 팔고, 능력은 안 판다』 전편 전달본 — 720p · 397.1초 · 28.9 MB · checks hard 0

## 전달본(artifacts/china-export-controls-v7.4.0, 95148beb — `china_tech_export_controls_2026/final/`)
- `final_deliver.mp4` **28,868,864 B**(≤ 30 MB), 397.08초, 1280×720 24fps, md5 **`02ccbde34f19f0cc6b881a38bc5367d4`**
  - 원본 `out/final.mp4` 92.6 MB(md5 ec00065c, 미업로드) → x264 2-pass 380k, 오디오 `-c:a copy`(AAC 196k 그대로)
- `final_sheet.jpg`(전달본에서 12컷, 5·40·68·96·130·175·224·266·300·345·365·392초 — 육안 확인) · `MD5SUMS`
- `provenance.json`(mux) · `audio_qa.json` · `description.txt`(챕터 포함) · `credits.txt` · `final.srt` · `preview_checks.json`
- 게이트 ② 자료: `gate2_r0292/`(847b7a70) — `sheet.jpg`(`--preview auto` 14컷) · `checks.json` · `provenance.json` · `cuts/` 바뀐 컷 6장 원크기
  - `p_0068.00` dots 패널(40개·**14개**·26개) · `p_0096.50` act1_9 서버실 사진(UF-160) · `p_0175.00` act2_3 뱃지 · `p_0224.00` 조시 quote · `p_0266.00` act3_2 라벨 "굴착기 2대"·"전력구 공사"(개략·비공개 문구 없음, UF-161) · `p_0365.50` act4_7 뱃지 유지(UF-162)

## 승인(D509) 뒤 바뀐 것 — 1건
- dots 패널 큰 숫자가 **"14개 개"** 로 단위 중복(big "14개" + unit "개") → `big: "14"` (f56b7d64). 글자 한 칸, 다른 요소 불변. 프리뷰 재실행 hard 0, 컷 육안 확인 뒤 전편.

## 수치
| 항목 | 값 |
|---|---|
| 길이 | 397.08초(6분 37초) |
| 음량 | I **−14.11 LUFS** · TP −1.7 dBTP · LRA 4.6 · loudness/true_peak/music_level/peak 모두 ok |
| 음성 | Supertonic 3 M3 ×0.95 · MMS 정렬 56/56(score_mean_min 0.819) · 끝 억양 final_fall 56 적용 0 생략 |
| checks | **hard 0** · 경고 22(media 밀도 옛 40초 규칙·장면당 사진 > 1·이웃 장면 같은 형태·timeline 핀 라벨 근접·article-unused act2_3) |
| features_used | photo 11 · article 9 · clip 0 · **card 0** · marker 12 · badge 4(인물) · quote 3 · panel 6(dots·versus·fork·timeline×2·versus) · route 1 · country 4 · dip 2 · camera keys 16(이동 13·컷 3) · 전환 호흡 3 |
| private_only_assets | **[]**(백악관 사진 2장 = 미 정부 저작물 PD, rights_clear) |
| user_feedback_guards | 71개 UF 장치 기록. 0 이 아닌 값: UF-102 `media_beats` 9 · UF-113 `ratio_graphic` 1 — 둘 다 경고 등급(hard 아님). UF-160~162 는 장치 없음(open, 이 영상 의견 — C12-2 경고 줄) |
| mux 경고 | act1_14 문장 RMS 평균 대비 3 dB 넘게 낮음(−20.35 dB, 평균 −17.7) — 들림 문제 없음 판단, 보고만 |

## 상태·커밋(claude/china-export-controls-2026)
- 상태 render → audio_mix → deliver → **done**(엔진 CLI 직접 실행: render `--res final --jobs 4` → `audio.mix` → `engine.mux`. `advance` 는 render 를 다시 돌리므로 쓰지 않고 `transition --reason` 으로 기록)
- f56b7d64 dots 단위 중복 수정 · e8fa7e89 설명문 description.yaml + 상태 전이 기록
- 설명문: 원고 사실(5건 공고·40/14/26·11/18 시행·허가/등록·대변인/조시 양측·희토류·부산·2027-01-10 휴전·경기도 전력구·진천)만, "초안·단일 보도" 고지 포함.

## 테스트
- 관련 + anti_inertia(not slow, R-0291): 71 passed · 2 failed — test_catalog_layer(hormuz 골든 자산, 그 뒤 복원) · test_user_feedback_guards(UF-145 장치, 이 트랙 이전 원장 등재 929b4b2).
- **전체 pytest 1회(C8.3)**: 렌더와 병행해 진행 중(현재 약 40%). 끝나는 대로 결과(통과·실패 목록)를 send_message 로 덧붙인다.

## 차단 호스트(조사·미디어)
| 경로 | 결과 |
|---|---|
| 컨테이너 curl | mofcom·reuters·scmp·globaltimes·news.cn·yna·한경·전자신문 차단 |
| WebFetch | 전 호스트 DNS 실패 → WebSearch 요약 대조(sources `confirmed_by` 명기) |
| Wikimedia Commons API | 429 지속 → upload.wikimedia.org 원본 직접(md5 경로) + WebSearch 로 라이선스 대조, 원본은 artifacts `media_src/` 보존 |
| YouTube | 봇 검사 — 우회 금지(D-0283 §5) → clip 0 |

## 미포함(사유)
| 요소 | 사유 |
|---|---|
| clip | YouTube 봇 검사, Commons 영상 없음 |
| 상무부장·대변인 초상 | 권리 확인된 초상 없음 → 직함 quote |
| 민감 국가 색칠 | 명단 미공표 |
| 위성 인셋 | 타격 사건 없음 · 출처 있는 공장·항만 좌표 없음 |
| GTX·한국 CDMO | 관련 보도 없음 |
| 교역 흐름선 | 출처 있는 양자 교역 수치 없음 |
| 베선트 뱃지 | 김해 회담 사진에 함께 · versus 패널 위 = badge-over-panel |
| 국내 현장 사진 | Commons 통과 후보 없음(헤렌크네히트·한화큐셀 = CC BY-SA·제한) |

## 다음 — 전달 뒤 첫 작업(C12-2, D-0289 §장치)
- UF-160 요소 공백 구간 상한 검사(자막만 이어지는 구간 → hard) · UF-161 화면 라벨 금지어(개략·비공개) 규칙 키 + 검사 · UF-162 `badge.min_hold_sec` 규칙 키 + 검사. 각각 테스트 + 원장 guards 갱신(`feedback_ledger.py --write`). 지금 착수한다.
