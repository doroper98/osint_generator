# artifacts/us-midterms-v7.4.0 — us_midterms_2026 산출물(대용량·컨테이너 의존, D-0290 §6)

- `m1_area/` — area 이벤트 눈 확인 컷(R-0296): light·dark × 본토 w60·텍사스 w16·알래스카 w34, 상원 결과(data/state_results.yaml 그대로, band = 득표 차 5·15 포인트 기준 — 연출 잠정). 설계 해상도 854×480, render_base + draw_area 만(라벨·패널 없음).

- `media_src/commons/` — 감독 컨테이너가 Commons `Special:FilePath/<파일명>` 원본으로 받은 파일(R-0302 Wikimedia 429 우회 아님 — 다른 출구 IP, 파일당 6~20초 간격). 파일명 = Commons 파일명 그대로(`File:` 접두 없음). `media_src/MD5SUMS.commons` 로 대조. 라이선스·피사체·시기 대조는 구현 세션이 media_notes.yaml·검색 기록으로 한다(원본 바이트만 제공). 감독 결정 D-0300.

- `final/` — **교체본 2**(v7.4.0, D-0310 UF-174 첫머리 접속사 삭제 · D-0311 UF-175 숏 단위 지명 라벨 일정, D-0313 프리뷰 통과). final_deliver.mp4 md5 1816baa54dd414077434309821f7619d · 29,350,198 B · 584.21초. **이전 전달본 2e3b0c41b53c60ed1a8d2b37f4cf3431(592.83초, e4e33bb6) 은 교체됨** — git 이력에만 남음.
- `preview2/` — UF-175 카메라 이동 6구간 3프레임 띠 + D-0310 3컷 + auto 시트(D-0313 통과). `uf175_golden/` — 골든 재기준 비교(D-0312).
