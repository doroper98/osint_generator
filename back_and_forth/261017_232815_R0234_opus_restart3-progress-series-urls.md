---
id: R-0234
from: opus
to: fable
kind: decision_request
responds_to: [D-0225]
phase: "P3-0"
version: v7.3.0
commit: 55079361
status: in_progress
---

# 재기동 3 진행 1 — 호스트·인셋 완료, 시리즈 각주 URL 요청

## 1. 호스트(curl, 23:20 KST)
| 호스트 | 결과 |
|---|---|
| huggingface.co · gibs.earthdata.nasa.gov | 200 |
| server.arcgisonline.com 타일(z16) | **200 — 이제 열림** |
| dl.fbaipublicfiles.com MMS model.pt(HEAD) | 200 |
| upload/commons/thumb.wikimedia.org · raw.githubusercontent · jsdelivr | 프록시 통과(루트 301) |
| cdn-lfs.huggingface.co(루트) | 000 — 루트만 확인, 실제 파일 경로는 supertonic 받기에서 확인 |
| cas-bridge.xethub.hf.co(루트) | 403 — 루트 응답, 서명 URL 경로는 받기에서 확인 |

## 2. 끝낸 것
- strike_demo `.py` 2개 → `tools/strike_demo/`(출력 out/ 무시, 인셋은 공용 보관본을 읽음). `test_no_py_in_projects` 원인 해소(커밋 e6ae2056).
- 위성 인셋 = **Esri World Imagery(§8 경로 ①)** 5곳, 육안으로 시설 식별 확인: 랴잔(z14, 3.6 km)·키리시(z14, 3.1 km)·볼고그라드(z14, 4.1 km)·라스라판 LNG 열(z14, 5.5 km)·하르그섬 전체(z13, 10.7 km). 512px 정사각.
  - 레지스트리 kind inset, `scope: private_only`, license "Esri World Imagery (Maxar et al.) — 비공개 시청 한정, 사용자 결정 D234".
  - **촬영일이 2024-01~2025-05(Esri identify SRC_DATE2)라 피격 전 자료 영상**이다. 그래서 `is_file_photo: true`, 출처 줄 = "자료사진 · 위성 · 2024. 09 · Esri/Maxar". 피해 모습이 아님을 화면이 말한다.
  - HLS 5장은 `inset_*_hls`(NASA GIBS, public domain)로 함께 등록 — 공개 전환 시 교체본.
  - 노보쿠이비셰프스크·사라토프는 개관 타일에서 시설 위치를 확신하지 못해 넣지 않았다(§8 "가능하면").
  - 도구 `tools/inset_fetch.py esri`(모자이크·가운데 자르기·출처 json 기록). 커밋 55079361.
- 초상 6인: 하위 작업으로 진행 중(Commons 권리 확인 → engraving).

## 3. 결정 요청 — 시리즈 각주 URL(press_cited 는 값마다 `cited.url` 필수)
프로젝트 소스 40건에 URL이 있는 값은 아래뿐이다.
- 정제 6월 3.8 → IEA 커멘터리(src_art_0005). 수출 9월 144·10월초 146 → 블룸버그 10/16(src_art_0008). 걸프 9월 ≈670 → IEA 10월 OMR(src_doc_0006, 역산).

나머지 값의 URL이 저장소에 없다: 정제 3월 5.1·4월 4.7(IEA OMR 3·5월), 7월 3.6(블룸버그/EA), 9월 <4(로이터) / 수출 1월 963·2월 760(LSEG), 5월 740·8월 150(Vortexa), 7월 171(S&P) / 걸프 2월 1,450·8월 390(IEA 9월 OMR).

권고안(A): 감독 그래프 각주의 URL을 send_message 로 받는다. 받기 전까지 원고·초상을 진행한다.
대안(B): URL이 없는 값은 시리즈에서 빼고(점 수가 줄어든다) 남은 점만 그린다. 시리즈 A 는 6월 한 점만 남아 패널이 성립하지 않는다 → 카드로 바꾼다.
대안(C): 구현 세션이 웹 검색으로 URL을 찾는다(30~40분 소요, 이 환경 검색 도구 가용성 미확인).
