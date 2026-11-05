# artifacts/us-midterms-v7.4.0 — us_midterms_2026 산출물(대용량·컨테이너 의존, D-0290 §6)

- `m1_area/` — area 이벤트 눈 확인 컷(R-0296): light·dark × 본토 w60·텍사스 w16·알래스카 w34, 상원 결과(data/state_results.yaml 그대로, band = 득표 차 5·15 포인트 기준 — 연출 잠정). 설계 해상도 854×480, render_base + draw_area 만(라벨·패널 없음).

- `media_src/commons/` — 감독 컨테이너가 Commons `Special:FilePath/<파일명>` 원본으로 받은 파일(R-0302 Wikimedia 429 우회 아님 — 다른 출구 IP, 파일당 6~20초 간격). 파일명 = Commons 파일명 그대로(`File:` 접두 없음). `media_src/MD5SUMS.commons` 로 대조. 라이선스·피사체·시기 대조는 구현 세션이 media_notes.yaml·검색 기록으로 한다(원본 바이트만 제공). 감독 결정 D-0300.
