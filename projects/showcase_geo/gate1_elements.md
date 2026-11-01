# showcase_geo 게이트 ① 덧붙임 — 막마다 넣을 요소(계획)

D-0253 §3 "게이트 ① 자료에 각 막의 요소 목록을 한 줄씩". 계획이다 — 실제로 그린 요소는 카탈로그 판 요소 표(`tools/catalog_table.py`, 코드 생성)로 확인한다.
자료는 모두 원 프로젝트 등재본(미디어 레지스트리·시리즈 레코드·초상 라이브러리)이다. 새 자산 없음.

예상 길이: 내레이션 약 172초(diesel 실측 8.85자/초) + 문장 간격·전환 호흡 약 44초 + 타이틀·엔딩 카드 16.6초 ≈ **3분 53초**(상한 4분 30초, D-0253).

| 막(문장) | 무대·카메라 | 넣을 요소 |
|---|---|---|
| cold(2) 랴잔 → 울산 | 메르카토르 light, 랴잔 확대 → 동해 | flight(drone)+위성 인셋 랴잔, boom, marker, 날짜 배지, 젤렌스키 뱃지(person), 기사(AP), 타이틀 카드 |
| act1(8) 러시아 정유소 | 서부 러시아 권역, 정유소마다 이동 | country(러·우), marker 누적, flight(drone)+인셋 키리시, card(display 큰 숫자), panel dual_line(정제 처리량 레코드), panel versus(유전 대 정유소), panel fork(원유 수출 vs 국내 경유), photo(모스크바 정유소 화재, CC0), cascade(타격 겹침 카드), 기사 |
| act2(7) 극동·울산 | 우랄 → 극동 → 동해 | route(울산 → 블라디보스토크 7척·14회), route 분기(신고 목적지 니가타 ↔ 실제 블라디보스토크), marker(울산·여수·블라디보스토크), 국기 뱃지(kr·ru), panel dots(유조선·항해 수), panel relation(구매자 관계), 기사(가디언 계열), 휘장(emblem) 뱃지 |
| act3(9) 자료 장 — 걸프·호르무즈 | 장 전환 카드 → 걸프 권역 | dip(암전 전환), tanker_loop·barrier(해협 봉쇄)·ships(발 묶인 선박), clip(미 중부사령부 공개 영상, PD), cutout(P-8A), country(이란 강조), panel statement(7개국 공동성명), panel precedent(청해부대·자이툰), panel timeline(2~3월), panel checklist, dual_line(걸프 경유 순수출 레코드), 위성 인셋 라스라판, quote(인물 발언) |
| act4(4) 자료 장 — 비무장지대 | 장 전환 카드 → 서부전선 확대(D 티어) | primitive site_diagram(군사분계선·폭발 지점 도식), marker(좌표 비공개 권역), 국기(kr·kp), 기사(한국일보·시사), photo(DMZ 표지판·철책, 등재본) |
| act5(6) 워싱턴 | 워싱턴 → 우크라이나 → 랴잔 | 인물 뱃지(트럼프·베선트·젤렌스키), quote, card(일반허가 135호), article(AP), flight(랴잔 재타격) |
| ending(2) | 네 지점 다시 모으기 | marker 재호출, 엔딩 카드(크레딧·권리·보도 출처, mono 버전 도장) |

글꼴: sans(자막·카드) · serif(기사 헤드라인) · display(큰 숫자 카드) · mono(날짜 배지·크레딧). 음성: 표준(Supertonic 3 M3 ×0.95, 끝 억양 시안 C).

## 미포함(사유)
| 요소 | 사유 |
|---|---|
| post(X 게시물 카드) | 세 원 프로젝트 sources 에 X 게시물(type x-text·x-capture)이 없다. 새 출처를 넣지 않는다(D-0251 "새 사실 없음") |
| panel gantt | 세 원 프로젝트에 기간 막대 자료(시작·끝 날짜 쌍의 사실 묶음)가 없다 |
| panel network | 세 원 프로젝트에 다자 관계망 자료가 없다(relation 패널로 관계 1건만) |
