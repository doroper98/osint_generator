---
id: R-0308
from: opus
to: fable
kind: phase_report
responds_to: [D-0290, D-0305, D-0306, D-0307, D-0308]
phase: "US1"
version: v7.4.0
commit: 8376f201
status: done
---

# us_midterms_2026 전편 완성 — final_deliver.mp4 29.8 MB · 720p · 592.8초 (artifacts e4e33bb6 `final/`)

## 1. 산출물(artifacts/us-midterms-v7.4.0 e4e33bb6 `final/MD5SUMS`)
| 파일 | md5 | 비고 |
|---|---|---|
| final_deliver.mp4 | 2e3b0c41b53c60ed1a8d2b37f4cf3431 | 29,776,485 B · 1280×720 · 592.83초 · 영상 2패스 200 kbps, 음성 `-c:a copy`(AAC 196 kbps) |
| final_sheet.jpg (+ frames/ 20컷) | 68209007f99213046bca106675d066c1 | 8·30·45·111·132·202·215.5·251·290·310.5·318.5·334·354·385·403.9·427·465·503·548·590초 |
| provenance.json | 7eee5a308e4a73fc465f87a279a119a3 | stages plan·geo·preview·render·mix·mux true |
| audio_qa.json | fa1c435f94f33e8900797cf5047ab054 | I −14.08 LUFS · TP −1.67 · LRA 3.9 · 내레이션 구간 음악 −12.06 dB — 전부 ok |
| description.txt·credits.txt·final.srt·render.json | MD5SUMS 참조 | |
- 마스터 final.mp4 = 175,314,194 B · md5 881c0c617090ccd2afdb4d0801b013e0 — GitHub 100 MB 한도로 미커밋(컨테이너 보관, `final/MASTER_final_mp4.md5`).

## 2. 원고·승인 지문
- 게이트 ① 승인본 v1.2 sha1 b7ce51ec → 사용자 지시로 갈음한 표시·문구 수정: D528(UF-171 매체명 라틴) · D529(UF-172 '개표 중' 제거) · D530(UF-173 '사실상 유력') → **현 script_sha1 = 760ef1f4f5fbb14ad54e4f93b0e6dde05b773fa9**(manifest 다음 기록에 인용 바람). lint 0·0. 79문장 592.83초(D-0307·D-0308 문장 10개만 재합성, MMS·final_fall 그대로). 게이트 ② = 감독 기록 d92b259a(D527).
- D-0308 문장표와 다른 점 1: act3_6 캔자스 "약 7천 표"(NBC 11/5 저녁 7,045 — 감독 승인).

## 3. 검사·provenance
- 전편 사전 검사 hard 0(경고 72: shots·media_beats·geo_unsourced·portrait_unused·article_press_missing·endcard_roll·ratio_graphic). 프리뷰 auto hard 0, 원크기 컷(게이트 ② 12 + D-0306 3 + D-0307/8 5) 모두 hard 0.
- features_used: photo 17 · article 5 · **bars 16**(유력 3: MS·AK 상원, KS 주지사; side_auto 3) · area 2(71 항목, 유력 빗금 4) · marker 27 · panel 6 · badge 7(person 3·emblem 4) · quote 2 · dip 2 · **card 0**.
- assets.emblems.rights_exceptions: dem_party·rep_party(user_exception D519, private_only 범위 문구) — 공개 배포 전 재확인 필요. private_only_assets [] (inset 없음).
- user_feedback_guards 74건 기록(돈 장치·결과). 이 영상 의견 UF-163~173 은 장치 미부착(C12-2 전달 뒤 첫 작업).
- 테스트: bars 13 · area · checks · parity · label 관련 통과, anti_inertia 빠른 묶음 72 passed(UF-145 기존 1 제외), 골든 dark·light 25/25(2 passed). **전체 pytest(C8.3) 진행 중** — 첫 시도는 렌더 중단(pkill)·원장 YAML 오류와 겹쳐 무효(39 % 에서 시간 초과), 재실행 결과는 별도 메시지.

## 4. 이번 트랙에서 바뀐 엔진·규칙(주요 커밋)
- area(98745688) · 정당 로고 예외 D519(b4d8cba5) · bars 이벤트·admin1 모드·외곽선(f6fe9057) · bars 앵커 수정·출처 글자(d1e05e50) · crop_y·element_gap bars(8c922582) · resolve_sides(7326622f) · bars name-clip(2aba88d6) · 마커 부제 잉크 D526(4fb57e83) · 주 이름 잉크 D527(7217c656) · data.units 석 D524(f02adeca) · user_feedback.yaml 따옴표(fc0a26c5).
- 영상: 연출 보정 6회(0860e10f…dbabd0b0) · 사진 등록(79dd32ca) · 크레딧 롤(16cb8a36·b1185715·da34e026) · D-0301(8922d003) · D-0303(2fd248c9·923e5114) · D-0306(92363258) · D-0307/8(311fd0b3·8e7e2bb0) · 음악 강도(8376f201).

## 5. 차단 호스트 표(우회하지 않음)
| 호스트 | 결과 | 영향 |
|---|---|---|
| upload.wikimedia.org · commons API | 429 반복(600초 대기) | 사진 원본 10/26 만 직접 수신, 7장은 감독 수집(D-0300) |
| c-span.org | 403 | 클립 0 |
| bioguide.congress.gov · congress.gov · senate.gov · marshall.senate.gov · loc.gov | 403 | 공식 초상 대체 불가 |
| apnews.com(AP 결과) | 차단 | 콜은 2차 보도 인용(D517) |
| clerk.house.gov | 열림 | 제프리스 사진 335×410 뿐 — 미사용 |

## 6. 미포함 표
| 항목 | 사유 |
|---|---|
| 사진 9(쿠퍼·잭슨·콜린스·오소프·SC·MS·AK 의사당·샌드·제프리스) | Wikimedia 429 — 전편 시작 전까지 미수신 |
| 해밀턴 유세·아이오와 의사당 사진 | 결과 문장을 bars 가 차지(media_notes drop, D-0303) |
| 기사 카드 0028·0037·0035·0029 | 결과 문장 자리를 bars 에 내줌(기사 9 → 5) |
| 조지아·오하이오 주지사 bars | 후보 사진 문장(7초) — 사진·막대 각 4초 불가 |
| 알래스카 주지사 마커·bars | 원고 문장에 없음(지도 빗금만) |
| 클립 | c-span 403 |

## 7. 다음(C12-2 전달 뒤 첫 작업)
- UF-163~173 장치: script_grammar 선거 제도 문장·정당 상징·권리 예외 테스트·admin1 모드·halo·area outline 상한·bars 검사·매체명 표기(script_vocab.outlet_display)·'개표 중' 금지어·'유력' 표기 규칙 → 원장 guards 갱신 → feedback_ledger --write.
