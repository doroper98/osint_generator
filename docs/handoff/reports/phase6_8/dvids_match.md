<!--
tier: 3
last_synced_with: v3.0.0
ssot_for: [phase6_8-dvids-match]
depends_on: [assets/media/media_registry.json, tools/media_fetch.py]
last_review: 2026-09-28
-->

# DVIDS 1차 출처 대체 원본 — 같은 영상 확인 (back_and_forth D-0045, D43)

Commons 원본 webm 이 환경 egress 단위로 429 차단(15:41~, Fable 컨테이너도 API 429)이라 두 영상을 DVIDS 원 배포처에서 받았다.
정본(레지스트리 `url`·`source_hash`·`segment`)은 고치지 않았다. 대체본은 `source_variants[]` 에만 적는다.

| mid | DVIDS | 라이선스 | 원본 | 길이(정본 / DVIDS) | offset_sec |
|---|---|---|---|---|---|
| strikes | [1013909](https://www.dvidshub.net/video/1013909), VIRIN 260707-D-D0477-3001 | PUBLIC DOMAIN | DOD_111826477.mp4 h264 1920×1080 60fps, md5 `9933fefd8c174f7bb8a3f4f48d713726` | 24.6 / 24.600 | **0** |
| niovi | [881959](https://www.dvidshub.net/video/881959), VIRIN 230503-N-NO146-2001 | PUBLIC DOMAIN | DOD_109612827.mp4 h264 1280×720 30fps, md5 `48e9ef6cc3aef00d43f50bc99b1cd4f6` | 59.421 / 59.400 | **0** |

## 프레임 대응 (검수 시트 12장, 같은 함수 `media_fetch.thumbsheet`)
Phase 6.5 `thumbsheet_{mid}.jpg`(Commons 원본) 와 이번 `thumbsheet_{mid}_dvids.jpg` 의 같은 칸(같은 시각)을 평균 절대 차이(/255)로 비교.
타일 가장자리 4px 은 초록 테두리 때문에 뺐다.

| strikes 시각(초) | 1.0 | 3.1 | 5.1 | 7.2 | 9.2 | 11.3 | 13.3 | 15.4 | 17.4 | 19.5 | 21.5 | 23.6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MAD | 0.67 | 0.70 | 1.19 | 0.62 | 0.88 | 0.72 | 0.64 | 0.47 | 0.13 | 0.14 | 0.98 | 1.09 |

| niovi 시각(초) | 2.5 | 7.4 | 12.4 | 17.3 | 22.3 | 27.2 | 32.2 | 37.1 | 42.1 | 47.0 | 52.0 | 56.9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MAD | 0.75 | 0.97 | 2.79 | 1.07 | 1.23 | 0.96 | 0.92 | 1.06 | 1.03 | 1.08 | 1.04 | 1.07 |

- 모든 칸이 같은 장면·같은 순서다(최대 2.79/255 — 인코딩 차이 수준). 장면이 바뀌는 칸도 같은 시각에 바뀐다 → **시각 오프셋 0**.
- 사용 구간(strikes 1.5–6.5 / niovi 28–33초)도 같은 장면이다. strikes 13초 이후 소형 선박 구간은 종전대로 쓰지 않는다(14 §2.2, D-0039 확인).
- niovi 는 DVIDS 가 0.021초 짧다(끝 쪽). 사용 구간(28–33)과 무관.

## 가공 결과 (Commons 호출 0, `media_fetch.py projects/hormuz_korea --variant dvids --restore-from <보존본>`)
| 파일 | Phase 6.5 md5 | 이번 | 판정 |
|---|---|---|---|
| hormuz_transit.jpg · _720.jpg | deff52c2 · 95867702 | 같음 · 같음 | 새 다운로드 = Phase 6.5 |
| rok_iraq.jpg · _720.jpg | 1eae29c2 · f0b62278 | 같음 · 같음 | 〃 |
| p8.jpg · p8_cut.png | 7851450b · 7427d942 | 같음 · 같음 | 〃 |
| strikes_480.npy | 61f7b89f | 169d0de5 | 다름 — DVIDS 원본(D-0045 예상). 25컷 클립 컷은 expected_deltas 후보 |
| niovi_480.npy | 704f8a93 | a62901eb | 〃 |

새 다운로드 md5(D-0038): 사진 원본 3 + 가공 3(컷아웃 포함) = 6/6 같음. 영상 2건은 Commons 가 풀리면 정본으로 다시 대조한다(D-0045 §4).
