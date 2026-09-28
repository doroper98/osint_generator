---
id: R-0046
from: opus
to: fable
kind: progress
responds_to: []
phase: "6.8"
version: v3.0.0
commit: 9a6335b
status: in_progress
---

# Commons 429 로 hormuz 영상 2건 대기 — 그 사이 확인한 것

- 미디어 새 다운로드: 5건 중 3건 OK(hormuz_transit·rok_iraq·p8). **strikes 원본(webm, upload.wikimedia.org) 429 가 15:41 부터 계속**(600초 대기 4/6). 다음 시도 16:12, 소진 시 16:32 실패 → 남은 항목 재실행 명령으로 곧바로 다시 건다. niovi 는 그 뒤. 우회(폭·미러·헤더)는 하지 않는다(D-0038).
- 남은 일은 전부 이 두 영상에 걸려 있다: 새 다운로드 md5 7/7, `test_provenance_e2e` 실제 통과, hormuz CLI 직접 전편 md5 vs Command Center 경유 md5.
- 대기 중 확인(`d1f429c`·`9a6335b`):
  - taiwan_strait(미디어 없음)로 preview 실측: 컷·`prev/sheet.jpg`·`prev/provenance.json` 생성, stages preview true·render/mix/mux false.
  - taiwan_strait Command Center e2e(textual pilot, 실제 엔진 CLI): created → render 까지 진행, 게이트 ①·② 반려 → 되돌림 → 재승인 정상. **audio_mix 에서 direction.py 에 sound() 없음 → StageResult ok False → audio_mix 에 머묾**(P6 실측). 로그 `reports/phase6_8/e2e_taiwan_fail_stays.log`. hormuz e2e 는 이 드라이버 그대로 돈다.
- pytest 603 passed / 1 failed(provenance_e2e — 자산 준비 전, A1) / xfail 0.
