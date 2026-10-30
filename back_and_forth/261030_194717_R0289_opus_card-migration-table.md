---
id: R-0289
from: opus
to: fable
kind: progress
responds_to: [D-0306]
phase: "E0"
version: v7.4.0
commit: 60686dcd
status: done
---

# D-0306 구석 카드 폐지 — 이식 표 · 골든 재기준(7컷)

## 1. 커밋
- 4c84dbb7 — card 삭제(P2)와 이식, 검사·슬롯·시험, 원장 UF-148 guarded.
- 60686dcd — hormuz 골든 재기준(dark·light), 시험 기준선 경로 교체.

## 2. 무엇을 지웠나
- 규칙: `registries.event_types` 의 card. `qa_checks.card_over_panel.cover_types`·`timeline_frame_cover_types`·`qa_checks.chart_only_run.chart_types` 의 card. placement `card_right` 슬롯의 kinds 에서 card.
- 코드: `engine/cards.py`, `CardEvent`, 프리뷰 픽스처 `tests/fixtures/preview/card.yaml`, 프롬프트 예시 `prompts/examples/events/card.yaml`.
- 남긴 것: `layout_480p.card` 는 post·primitive·cascade·island 가 같이 쓰는 토큰이라 그대로 둔다. 스케치 미사일 도해의 카드는 다른 물건이라 손대지 않았다.

## 3. 새로 단 것
- 검사 `text_restates_narration` hard. 규칙 키 `qa_checks.restate_overlap_max` 0.6, `restate_min_words` 4. 대상은 panel·cascade·marker·island 의 제목·라벨·줄.
- `placement.center_media` 와 슬롯 `map_center_media`(폭 461)·`map_pair_left`·`map_pair_right`(각 376). 지도 무대의 사진만 해당한다. b-roll 영상은 구석 그대로(UF-141).
- `marker.big_size` 는 만들지 않았다. 옛 카드의 큰 수치(bigs) 100건은 모두 버렸다(§1.3 ③). 핀 라벨·끝값으로 옮기는 변환은 하지 않았다. 필요하면 영상별로 연출에서 다시 붙인다.
- 시험: `tests/test_v740_card_abolition.py`(레지스트리·현재 연출 card 0·이식 도구 CLI·되풀이 검사). 골든 검사 수 98 → 99.

## 4. 이식 수(카드 295개 삭제)
| 연출 | 삭제 |
|---|---|
| diesel_road_2026 | 74 |
| dmz_mine_2026 | 32 |
| fed_policy_2026 | 27 |
| hormuz-talks-2026 | 24 |
| valdai-2026 | 20 |
| gulf_china_arms_2026 | 19 |
| kaliningrad-suwalki | 15 |
| hormuz_ai · ratcliffe2026 | 14 · 14 |
| gulf_pact_2026 | 13 |
| showcase_geo | 10 |
| hormuz_ai_cam | 8 |
| hormuz_camauto · hormuz_korea · prompts/examples | 7 · 7 · 7 |
| showcase_econ | 4 |

- 옛 판(direction.vN.yaml)은 이력이라 그대로 둔다. diesel v2 는 연출 파일만 이식했고 재렌더하지 않았다.
- 전체 표는 §7 에 붙였다.

## 5. 골든 재기준(D-0306 §1-5 승인)
- 새 기준선: `docs/handoff/reports/phaseD0306/hormuz_baseline.json`(dark), `hormuz_light_baseline.json`(light). 옛 기준선은 phaseV3·phaseQ3 에 그대로 둔다.
- 바뀐 컷은 dark·light 모두 7개다. p_0006.95 · p_0035.36 · p_0138.26 · p_0145.33 · p_0150.26 · p_0218.12 · p_0229.62. 골든 연출에서 지운 card 7개와 수가 같다.
- 나머지 18컷은 화소가 같다.
- 시험 경로를 교체했다: test_provenance_e2e · test_q3_light_e2e · test_g12_version_stamp.

## 6. 시험 상태
- 관련 시험 전부 통과했다(card 시험을 post·cascade·quote 로 옮기거나 지움).
- anti_inertia 에서 남은 실패 1건: `test_open_entries_only_latest_video`(UF-147 open). D-0306 지시대로 손대지 않았다.
- 내 변경 전부터 있던 실패 2종이다(1a3b48b3 사건 레인 삭제 뒤, fed_timeline_demo).
  - g8 `AnimaticRunTest` 셋업 오류: 합성 사본 폴더 이름이 demo 라 `density_exempt_projects` 면제를 못 받는다. plot_height·axis_empty_band 도 걸린다.
  - `DemoPreviewTest`: 이 컨테이너에 fed_timeline_demo 자산이 없다.
  - 레인 기대값(events 레인)은 고쳤다. 나머지는 범위 밖이라 결정을 바란다.

## 7. 전체 이식 표
| 연출 | 태그 | 줄 | 큰 수치(bigs) | 처리 |
|---|---|---|---|---|
| projects/diesel_road_2026/direction.yaml | 러시아 국방부 | 무인기 격추 — 그 파편이 불을 냈다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 2026년 첫 여덟 달 |  | 사흘에 한 번 우크라이나의 러시아 정유소 타격 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 표적 | 원유를 캐는 유전이 아니라 / 경유·휘발유를 만드는 정유소 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 카네기 국제평화재단 분석 | 표적이 정유소로 옮겨 간 뒤 / 러시아 안 원유 정제가 어려워졌다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 같은 분석 | 러시아 원유 수출은 오히려 늘었다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 원유는 팔리고, 공장은 타격 | 원유는 계속 팔려 나갔다 / 경유·휘발유 만드는 공장이 타격 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 서방 제재 | 정제 설비 교체 장비를 구하기 어렵다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 러시아 경유 생산 · 월간 |  | 750만 ton 3월 / 약 590만 ton 5월 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 국제에너지기구 추정 |  | 30% 가까이 올해 러시아 경유 생산 감소 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 러시아 | 거꾸로 연료를 사들이기 시작 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 정유소가 멈추자 | 경유를 팔던 러시아 / 연료를 사 와야 하는 처지 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 러시아 철도 관계자 | 극동연방관구 정유소는 두 곳뿐 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 러시아 업계 전문가 |  | 60~65% 극동 정유소가 채우는 경유 수요 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 같은 전문가 | 옴스크 정유소 물량 / → 드론 피해 입은 서쪽으로 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 극동의 연료 | 다른 지역에서 철도로 들어오는 연료에 의존 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 극동 연료 부족 | 5월 정유소 피격 뒤 시작 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 연해주 · 화물차 경유 주유 한도 |  | 100L 시내 / 200L 간선도로 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 연해주 당국 설명 | 실제 부족이 아니라 / 되팔기를 막기 위한 조치 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 동북아 → 러시아 선적 | 2022년 2월 이후 처음 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 극동 석유제품 철도 하역 | 주된 곳: 블라디보스토크가 있는 연해주 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 7~8월 한국 항구 선적 |  | 17만 6천 ton 이상 대부분 경유 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 레일라호 두 차례 |  | 약 5만 7천 ton 실어 나른 경유 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 레일라호 두 번째 항해 | 신고 목적지: 일본 니가타 / 실제 도착: 블라디보스토크 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 아스토리아호 · 8월 1일 울산 |  | 약 1만 1천 ton 선적량 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 청천호 · 여수 앞바다 |  | 약 2만 6천 ton 옮겨 받은 연료 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 케이플러 자료 · 구매자 | 로스네프트 — 러시아 국영 석유회사 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 케이플러 자료 · 구매자 | NNK — 하바롭스크 정유소 보유 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 가디언 보도 뒤 | 한국 정부 ↔ 우크라이나 논쟁 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 외교부 | 경유·항공유 등 석유 정제제품 / 대러 수출통제 품목 아님 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 정부 |  | 1,402개 상황허가 대상 품목 · 군사용 전용 가능 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 2024년 한국 경유 수출 |  | 2억 166만 배럴 1992년 통계 이후 최대 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 올해 1~8월 한국 경유 수출 |  | 1억 2,982만 배럴 수출량 / −3.4% 1년 전 대비 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 정부 수출 관리 | 휘발유·경유·등유 수출 물량 / 지난해 수준 안으로 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 정부 | 실제 항로와 신고 목적국이 다른지 확인 / 국내법 위반 여부 가린다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 정부 | 신고지로 곧장 가지 않은 사실만으로는 / 허위 신고 단정 어렵다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 청와대 국가안보실 | 무역통계상 한국 → 러시아 / 경유·휘발유·제트유 수출 기록 없음 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 한국 항만 기록 | 연료의 소유주·판매자는 나오지 않는다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 우크라이나가 문제 삼은 것 | 법 조항보다 그 시점 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 청와대 | 거래 주체·원산지·최종 구매자 미확인 / 개별 거래 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 구매자 로스네프트 · 제재국 | 영국 · 미국 · 유럽연합 · 호주 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 재무부 | 2025년 10월 22일 로스네프트 제재 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 재무부 경고 | 제재 대상과의 중대한 거래를 돕는 / 외국 금융기관도 제재 가능 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 외교 갈등 | 주우크라이나 대사 소환 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 외교 갈등 | 북한군 포로 이송 공개 갈등에 뒤이어 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 트럼프 대통령 | 하르그섬 석유 시설은 겨냥하지 않기로 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 이란 주장 | 미국과 이스라엘이 함께 공격 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 이란 경고 | 걸프 전역의 에너지 시설에 보복 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 라스라판 LNG 생산 라인 |  | 14기 중 2기 멈춤 / 연 1,300만 ton 생산 능력의 약 17% | 삭제 |
| projects/diesel_road_2026/direction.yaml | 호르무즈 통과 석유제품 · 하루 |  | 67만 7천 배럴 통과량 / 360만 배럴 전쟁 전 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 9월 경유 정제마진 |  | 배럴당 약 95달러 사상 최고 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 한국 원유 수입 중 중동산 비중 |  | 69.1% 지난해 / 48.5% 올해 5~7월 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 국제에너지기구 | 경유 부족, 2027년까지 이어질 수 있다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 | 지난해 러시아 석유회사들을 제재 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 재무부 · 3월 12일 | 일반허가 134호 / 이미 배에 실린 러시아산 원유·석유제품 거래 허용 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 재무부 | 일반허가 135호 / 러시아산 경유 판매·운송·수입 허용 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 일반허가 135호 |  | 2027년 4월 7일 까지 유효 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 노바크 러시아 부총리 |  | 월 300만~350만 ton 늘 수 있는 경유 수출 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 베선트 재무장관 | 가진 모든 법적 권한으로 이행 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 카네기 국제평화재단 추정 |  | 약 70억 달러 이론상 가치 · 6개월 약 500만 ton 기준 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 경유 평균 가격 |  | 갤런당 6.26달러 평균 가격 / 80% 가까이 상승 연초 대비 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 미국 국내 정치 | 경유값이 정치 문제가 됐다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 중간선거 앞 트럼프 대통령 | 경유값 상승 → 정유소 공격 탓 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 그 해법 | 에너지 휴전 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 백악관 당국자 | 첫 단계: 서로의 정유소를 공격하지 않는다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 우크라이나 반발 | 러시아의 정유망이 훨씬 크다 / 맞교환은 불공평 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 젤렌스키 대통령 | 러시아가 에너지 시설 공격을 멈추면 / 우크라이나도 멈춘다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 크렘린궁 | 우크라이나의 에너지 시설 공격 / 미국의 평화 노력에 어긋난다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 젤렌스키 대통령 | 트럼프 대통령에게 배신감을 느낀다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 에너지 휴전 |  | 나흘 10월 11일 발효 → 10월 15일 끝 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 워싱턴 | 러시아산 경유 거래 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 네 장면 | 모자란 경유 한 가지로 이어져 있다 |  | 삭제 |
| projects/diesel_road_2026/direction.yaml | 국제에너지기구 |  | 2027년까지 경유 부족이 이어질 수 있다 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 콤소몰스크나아무레 – 우크라이나 |  | 약 6,500km 거리 | 삭제 |
| projects/diesel_road_2026/direction.yaml | 강유정 청와대 수석대변인 | 우크라이나 측 주장은 사실과 다르고 부적절 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 폭발 지점 |  | 약 10m 군사분계선 남쪽 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 9월 21일 |  | 3명 한국군 장병 부상 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 합참 발표 · 9월 28일 | 북한군 지뢰일 가능성이 매우 높다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 투입 인원 |  | 18명 간부 15명 · 병사 3명 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 강신철 국방장관 · 9월 22일 | 북한 것인지 지금은 알 수 없다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 강신철 국방장관 · 9월 22일 | 확실한 증거가 필요하다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 9월 27일 | 군 · 유엔사 합동 현장조사 착수 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 합동 현장조사 |  | 약 40명 사고 지점 주변 수색 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 국과수 감정 · 다친 장병의 장구류 | TNT 성분 / 갈색 이물질 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 국과수 감정 · 다친 장병의 장구류 | 철제 파편은 확인되지 않음 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 9월 29일 · 합동조사 | 북한군 수지반보병지뢰 1발 추가 발견 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 강신철 국방장관 답변 | 사고 당시 국가안전보장회의는 열리지 않았다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 국민의힘 | 조사 지연, 대북 정책 둘러싼 정치적 압력과 관련 있나 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 청와대 | 현장조사 일정은 합참·유엔사의 군사적 판단 / 대통령 유엔 연설과 관련 없다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 이재명 대통령 | 신속하고 철저한 조사 주문 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 민주당 | 북한 지뢰로 최종 판명되면 / 북한이 사과하고 재발 방지 약속해야 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 국민의힘 | 대북 확성기 곧바로 다시 설치하라 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 국방부 | 확성기 재개, 최종 판단과 함께 검토 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 군 당국 · 북한군이 군사분계선을 넘은 횟수 |  | 20여 차례 최근 한 달 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 세계일보 보도 · 북한군이 군사분계선을 넘은 횟수 |  | 20여 차례 최근 한 달 / 17차례 2025년 한 해 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 세계일보 보도 | 2024년 4월부터 비무장지대 안 요새화 작업 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 2015년 8월 · 코리아헤럴드 | 하사 2명 다리 잃어 / 합동조사단: 북한 목함지뢰가 원인 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 우크린폼 · AP 인용 · 9월 21일 | 폭발 원인은 아직 밝혀지지 않았다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 젤렌스키 대통령 · 유엔총회 연설 | 김정은이 병사들을 화폐처럼 쓰고 대가를 받는다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 한국 외교부 | 발언은 부인하지 않음 / 이송 세부 사항은 확인하지 않음 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 쇼이구 러시아 안보회의 서기 · 2025년 6월 |  | 1,000명 북한 공병 / 5,000명 건설 인력 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 힌시테인 쿠르스크 주지사 |  | 약 4만2,400헥타르 지뢰 제거로 정리한 면적 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 알자지라 보도 |  | 120일 파견 기간 / 9명 숨진 인원 | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 쿠르스크 경험과 이번 지뢰 | 이어져 있다는 근거는 나오지 않았다 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 아직 규명되지 않은 것 | 지뢰를 누가, 언제 묻었나 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 아직 나오지 않은 판정 | 장병들이 처음 봤다는 지뢰 — 유엔사 판정 |  | 삭제 |
| projects/dmz_mine_2026/direction.yaml | 아직 발표되지 않은 것 | 최종 판정 / 상응 조치의 내용 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 2026년 9월 16일 · FOMC | 미국 연준, 금리 인상 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 연방기금금리 | 은행끼리 하루짜리 자금을 빌려줄 때 적용 / 미국의 기준금리 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | FOMC 성명 · 목표 범위 | 목표 범위 0.25%p 인상 / 새 목표 범위 3.75~4% |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 연준 이사회 자료 · 9월 |  | 3.75% 목표 범위 하단 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 9월 16일 FOMC 표결 |  | 12 대 0 만장일치 | 삭제 |
| projects/fed_policy_2026/direction.yaml | FOMC 성명 · 9월 16일 | “Inflation remains elevated.” / 인플레이션은 여전히 높다 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 2025년 10월 29일 목표 범위 |  | 3.75~4% 지금과 같은 수준 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 2026년 FOMC | 7월까지 다섯 번의 회의 / 모두 금리 동결 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 선제 지침 | 중앙은행이 앞으로의 금리 방향을 / 미리 시사하는 문구 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 7월 29일 FOMC 표결 |  | 9 대 3 동결 결정 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 7월 29일 FOMC 성명 · 반대표 | 해맥 · 카시카리 · 로건 / 0.25%p 인상을 원하며 반대 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | PCE 물가 | 개인이 소비한 상품과 서비스 / 가격의 변화를 재는 지표 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 근원 PCE | 변동이 큰 식품과 에너지를 뺀 값 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 워시 의장 추정 · 9월 16일 |  | 약 3.6% 8월 PCE 상승률 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 워시 의장 · 9월 16일 |  | 약 3.2% 근원 PCE | 삭제 |
| projects/fed_policy_2026/direction.yaml | 워시 의장 · 9월 16일 |  | 약 4.1% 실업률 · 낮은 수준 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 8월 고용 |  | +16.2만 명 고용 증가 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 9월 16일 · 인상 당일 |  | 약 −0.4% S&P500 지수 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 9월 16일 · 미 국채 |  | 약 5% 10년물 금리 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 경제전망요약 (SEP) | FOMC 참가자들이 각자 내놓은 / 경제 전망을 모은 자료 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 경제전망(SEP) 중앙값 · 올해 |  | 3.7% PCE 물가 | 삭제 |
| projects/fed_policy_2026/direction.yaml | SEP 전망 중앙값 · 내년 |  | 2.3% PCE 물가 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 경제전망(SEP) 중앙값 · 올해 |  | 2.3% 실질 GDP 성장률 | 삭제 |
| projects/fed_policy_2026/direction.yaml | 점도표 · FOMC 참가자별 금리 전망 | 참가자별 전망 · 약속 아님 / 중앙값: 연내 추가 인상 1회 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 트럼프 대통령 · 소셜미디어 | 금리를 1% 이하로 / 빨리 내려야 한다 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 워시 의장 · 9월 16일 기자회견 | 인플레이션이 너무 오래 높았다 / 가격 안정에 먼저 초점 |  | 삭제 |
| projects/fed_policy_2026/direction.yaml | 점도표가 가리킨 추가 인상 | 아직 정해지지 않았다 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 5월 18일 · 로이터 보도 | 사우디아라비아에 중국산 방공체계 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 로이터 인용 소식통 | 운용은 사우디군이 아니라 파키스탄군 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 로이터 인용 소식통 | 비용은 사우디가 댄다 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 배치 규모 |  | 약 8,000명 병력 / 약 16대 전투기 | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 로이터 보도 | 여기에 중국산 HQ-9 방공체계 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 안보 관리 두 명 | 무인기 2개 대대도 함께 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | HQ-9 · JF-17 배치 | 두 나라 정부가 확인하지 않은 보도 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 로이터 보도 | 2025년 9월 상호방위협정에 따른 배치 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 2025년 9월 · 두 나라 발표 | 한쪽에 대한 공격을 / 양국 모두에 대한 공격으로 간주 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 협정 전문 비공개 |  | 최대 8만 명 배치 가능성 | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 소식통 설명 | 사람과 장비 — 파키스탄 / 돈 — 사우디 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 사우디 방공 · 미들이스트아이 | 미국산 패트리어트 / 미국산 사드 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 로이터 보도대로라면 | 그 옆에 중국산 HQ-9 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 다른 점 | 사우디가 직접 산 것이 아니라 / 동맹국 군대가 들여와 운용 / 비용은 사우디 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 10월 2일 · 로이터 보도 |  | 3만~4만 명 파키스탄 병력 | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 요격탄 1발 가격 |  | 약 110만 달러 천궁-II / 약 370만 달러 패트리어트 PAC-3 | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 사우디 하늘의 방공체계 | 미국산 — 패트리어트·사드 / 한국산 — 천궁-II · 계약대로라면 / 중국산 — HQ-9 · 로이터 보도대로라면 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 보도대로라면 이번에는 | 사우디가 사들인 것이 아니라 / 동맹국 군대가 들여와 운용 |  | 삭제 |
| projects/gulf_china_arms_2026/direction.yaml | 로이터 보도대로라면 | 미국산 패트리어트·사드를 갖춘 사우디 하늘 / 중국산 체계가 동맹국 군대를 통해 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 3국 현역 병력 |  | 약 140만 명 글로벌 파이어파워 2026 지수 기준 | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 후티·이란 | 메카 공격 시도를 부인 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 10월 5일 · 메카 협정 전략정치국방위원회 | 협정 발동 결정 / 집단방위 공약을 실제로 이행 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 10월 5일 · 3국 공동성명 | 후티를 위협으로 명시하지 않음 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 아시프 국방장관 · 보도 | 전투 작전에는 사우디군만 참여 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 10월 초 · 탈환 공세 | 사우디 주도 연합군 · 예멘 정부군 / 후티 점령지 탈환 공세 시작 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 후티 | 정부군의 모카 도달 주장 부인 |  | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 사우디 민간항공청 · 10월 8일 공격 |  | 최소 3명 사망 · 조종사 포함 사우디인 | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 사우디 발표 · 10월 10일 재공격 |  | 최소 12명 사망 | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 사우디 민간항공청 · 10월 10일 재공격 |  | 최소 309명 부상 | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 산업통상부 · 5월 26일 브리핑 |  | 69.1% → 48.5% 중동산 원유 비중 | 삭제 |
| projects/gulf_pact_2026/direction.yaml | 산업통상부 · 미주산 원유 비중 |  | 23.1% → 35.6% 지난해 → 올해 5~7월 | 삭제 |
| projects/gulf_pact_2026/direction.yaml | TIME 보도 · 10월 8일 | 트럼프, 후티 직접 타격 요청 거절 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 쟁점 · 무엇을 먼저 하느냐 | 해협 · 제재 · 자금 · 핵 사찰 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 아락치 이란 외무장관 · 9월 25일 |  | 4~5일 미국 측 조치 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 해제 대상 동결 자산 |  | 약 120억 달러 이란이 요구하는 동결 자금 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 미국 관리 · 거부 이후 | 간접 협상은 이어진다 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 아락치 이란 외무장관 | 카타르가 새 아이디어를 미국에 전달 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 페제시키안 이란 대통령 | 미국과의 협상, 더는 신뢰하지 않는다 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 페제시키안 이란 대통령 | 미국이 먼저 이란의 길을 막았다 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 미국 관리 · 6월 | 이란이 상선에 발포해 합의를 깼다 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 트럼프 대통령 · 9월 28일 | 미국이 이길 것 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 트럼프 대통령 · 측근들에게 | 중간선거 뒤 폭격 재개 예상 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 전쟁 전 |  | 약 20% 이 해협을 지난 세계 석유 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 해협 통과 · 마린트래픽 집계 |  | 132건 9월 21~27일 일주일 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 해협 통과 · 전쟁 전 |  | 약 130건 하루 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 쿠퍼 미 중부사령관 · 9월 26일 |  | 2000건 최근 몇 달 미군이 지원한 통항 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 쿠퍼 미 중부사령관 · 9월 26일 |  | 10억 배럴+ 미군이 지원한 원유 수송 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 브렌트유 · 9월 28일 |  | 108달러 안팎 배럴당 · 3% 넘게 상승 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 후티 | 사우디 선박에 해상봉쇄 선언 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 한국 원유 수입 |  | 70% 호르무즈 해협 경유 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 한국 헬륨 공급 |  | 약 65% 카타르산 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 코스피 · 9월 28일 |  | -2.7% 하락 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 한국 정부 | 유가 상한제 도입 |  | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | CSIS 분석 · 4월 초 |  | 7760만 배럴 IEA 공동 방출 뒤 정부 비축유 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | CSIS 분석 · 4월 초 |  | 약 26일분 당시 실소비 기준 | 삭제 |
| projects/hormuz-talks-2026/direction.yaml | 9월 30일 기준 · 확인되지 않은 것 | 미국의 답변에 담긴 내용 / 해협과 핵 사찰, 무엇이 먼저 움직일지 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 기자회견 · 9월 18일 | 전쟁에 개입하는 파병은 하지 않겠다 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 기자회견 · 9월 18일 | 한국 선박·국민 보호 / 최소한의 활동만 이어간다 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 지난해 한국 수입 · 이 해협 경유 |  | 61% 원유 | 삭제 |
| projects/hormuz_ai/direction.yaml | 지난해 한국 수입 · 같은 길 |  | 54% 나프타 · 플라스틱 원료 | 삭제 |
| projects/hormuz_ai/direction.yaml | 2월 28일 | 미국·이스라엘, 이란 공습 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 국제해사기구 · 6월 11일까지 |  | 46건 선박 공격 / 14명 숨진 선원 | 삭제 |
| projects/hormuz_ai/direction.yaml | 걸프 안쪽에 발이 묶였다 |  | 천여 척 배 / 2만 명 선원 | 삭제 |
| projects/hormuz_ai/direction.yaml | 9월 초 · 국내 방송 보도 | 정부, 연내 파병 준비 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 거론된 선택지 | 해상초계기 / 군수지원함 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 대통령실 · 9월 4일 | 군사적 방안 포함해 검토 / 결정된 것은 없다 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 이재명 대통령 · 9월 18일 | “전쟁에 들어가는 파병은 없다” |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 열어 둔 여지 | 분쟁의 주변부에서 한국군이 맡을 역할 |  | 삭제 |
| projects/hormuz_ai/direction.yaml | 미군 발표 |  | 10억 배럴 호위 작전으로 해협 밖으로 나간 원유 | 삭제 |
| projects/hormuz_ai/direction.yaml | 지난해 기준 |  | 61% 이 해협에 기댄 원유 수입 | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 기자회견 · 9월 18일 | 전쟁에 개입하는 파병은 하지 않는다 / 한국 선박·국민 보호, 최소한의 활동만 |  | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 지난해 한국 수입 중 호르무즈 경유 |  | 61% 원유 / 54% 나프타 | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 2월 28일 | 미국·이스라엘, 이란 공습 |  | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 국제해사기구 · 6월 11일까지 | 선박 공격 46건 / 선원 14명 사망 / 배 천여 척 · 선원 2만 명 발 묶임 |  | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 거론된 선택지 | 해상초계기 / 군수지원함 |  | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 이재명 대통령 · 9월 18일 | 전쟁에 들어가는 파병은 없다 / 분쟁 주변부의 역할은 열어 둠 |  | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 미군 발표 · 호위 작전 |  | 10억 배럴 해협 밖으로 내보낸 원유 | 삭제 |
| projects/hormuz_ai_cam/direction.yaml | 지난해 기준 |  | 61% 원유 수입의 호르무즈 경유 비중 | 삭제 |
| projects/hormuz_camauto/direction.yaml | 기자회견 · 9월 18일 | 전쟁에 개입하는 파병은 없다 / 한국 선박·국민 보호는 최소한으로 계속 |  | 삭제 |
| projects/hormuz_camauto/direction.yaml | 2025년 수입 중 호르무즈 경유 비중 |  | 61% 원유 / 54% 나프타 | 삭제 |
| projects/hormuz_camauto/direction.yaml | 국제해사기구 · 6월 11일 기준 | 선박 공격 46건 / 선원 사망 14명 / 발 묶인 배 약 1,000척 · 선원 2만 명 |  | 삭제 |
| projects/hormuz_camauto/direction.yaml | 거론된 선택지 | 해상초계기 / 군수지원함 |  | 삭제 |
| projects/hormuz_camauto/direction.yaml | 이재명 대통령 · 발언 요지 | “전쟁에 관여하거나 들어가는 / 파병은 없다” |  | 삭제 |
| projects/hormuz_camauto/direction.yaml | 미 중부사령부 발표 |  | 10억 배럴 호위 작전으로 반출된 원유 | 삭제 |
| projects/hormuz_camauto/direction.yaml | 2025년 기준 |  | 61% 원유 수입의 호르무즈 경유 비중 | 삭제 |
| projects/hormuz_korea/direction.yaml | 기자회견 · 9월 18일 | 전쟁에 개입하는 파병은 없다 / 한국 선박·국민 보호는 최소한으로 계속 |  | 삭제 |
| projects/hormuz_korea/direction.yaml | 2025년 수입 중 호르무즈 경유 비중 |  | 61% 원유 / 54% 나프타 | 삭제 |
| projects/hormuz_korea/direction.yaml | 국제해사기구 · 6월 11일 기준 | 선박 공격 46건 / 선원 사망 14명 / 발 묶인 배 약 1,000척 · 선원 2만 명 |  | 삭제 |
| projects/hormuz_korea/direction.yaml | 거론된 선택지 | 해상초계기 / 군수지원함 |  | 삭제 |
| projects/hormuz_korea/direction.yaml | 이재명 대통령 · 발언 요지 | “전쟁에 관여하거나 들어가는 / 파병은 없다” |  | 삭제 |
| projects/hormuz_korea/direction.yaml | 미 중부사령부 발표 |  | 10억 배럴 호위 작전으로 반출된 원유 | 삭제 |
| projects/hormuz_korea/direction.yaml | 2025년 기준 |  | 61% 원유 수입의 호르무즈 경유 비중 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 러시아의 서면 메시지 · 2026년 9월 30일 | 나토가 칼리닌그라드 공중·해상 봉쇄를 준비한다는 정보 (러시아 주장) |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 러시아의 서면 메시지 · 2026년 9월 30일 | 칼리닌그라드가 고립되면 / 핵무기를 포함한 모든 무기를 쓸 준비 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 수바우키 회랑 국경 구간 |  | 104km 폴란드–리투아니아 국경 구간 길이 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 이스칸데르 · 이동식 체계 |  | 500km 사거리 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 알리하노프 칼리닌그라드 주지사 · 발언 |  | 40~50% 리투아니아 경유 품목 중 금지 대상 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 메르츠 독일 총리 · 발언 요지 | 나토 동부 측면 방어를 직접 맡겠다 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 나우세다 리투아니아 대통령 · 발언 요지 | 독일 여단의 도착은 역사적 사건 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 나토 · 2026년 9월 29일 |  | 9개 동부 측면 다국적 전투단 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 폴란드 동부 방패 사업 |  | 800km 러시아·벨라루스 쪽 국경 보호 설계 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 투스크 폴란드 총리 · 발언 요지 | 이 요새화는 평화를 위한 투자 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 2021년 자파드 참가 병력 |  | 약 20만 명 러시아 당국 발표 | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 나토 · 2025년 9월 | 조약 4조에 따른 협의 / 이스턴 센트리 활동 시작 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 안보 보장 조약 · 2024년 12월 | 루카셴코–푸틴 서명 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 루카셴코 대통령 · 2024년 12월 발언 요지 | 벨라루스에 러시아 전술핵 수십 기 |  | 삭제 |
| projects/kaliningrad-suwalki/direction.yaml | 무라베이코 벨라루스 총참모장 · 발언 요지 | 공격 행동은 고려하지 않는다 / 공격 준비설은 근거가 없다 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 여러 매체 보도 | 2021년 이후 CIA 국장의 첫 러시아 방문 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 보도 · 수송기 기종 |  | C-17 미 공군 수송기 | 삭제 |
| projects/ratcliffe2026/direction.yaml | 방문 앞두고 · 보도 | 미국, 우크라이나에 요청 / 모스크바 등지 공격을 멈춰 달라 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 키이우포스트 인용 | 이 회동에 관해 미국에서 정보를 받았다 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 젤렌스키 대통령 | 회동 상대는 러시아 정보당국자들 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | CNN·CBS 인용 익명 소식통 | 랫클리프, 이란 지원을 끊으라고 촉구 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 익명 소식통 | 해협이 다시 열리지 않으면 추가 제재 경고 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 트럼프 대통령 | 이번 방문은 이란과 관련이 없다 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | CNN·CBS · 미국 정보당국 평가 | 푸틴, 나토 결속을 시험하는 도발에 나설 수 있다 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 트럼프 대통령 | 푸틴은 나토 영토를 공격하지 않을 것 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 크렘린 · 페스코프 대변인 | 평가가 러시아의 의도를 반영하지 않는다 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 아직 확정되지 않은 것 | 나토에 대한 경고가 실제로 전달됐는지 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 여전히 엇갈리는 것 | 이란·호르무즈가 회담 의제였는지 |  | 삭제 |
| projects/ratcliffe2026/direction.yaml | 공개되지 않은 것 | 그날 모스크바에서 오간 말의 목록 |  | 삭제 |
| projects/showcase_econ/direction.yaml | 9월 16일 · 연준 |  | 3.75~4% 기준금리 목표 범위 · 0.25%p 인상 | 삭제 |
| projects/showcase_econ/direction.yaml | 2026년 1~6월 | 네 번의 회의 · 금리 그대로 |  | 삭제 |
| projects/showcase_econ/direction.yaml | 연준 성명 · 9월 16일 | 인플레이션은 여전히 높다 |  | 삭제 |
| projects/showcase_econ/direction.yaml | 8월 소비자물가 · 1년 전 대비 |  | 3.4% 상승 | 삭제 |
| projects/showcase_geo/direction.yaml | 2026년 첫 여덟 달 |  | 사흘에 한 번 우크라이나의 러시아 정유소 타격 | 삭제 |
| projects/showcase_geo/direction.yaml | 표적 | 원유를 캐는 유전이 아니라 / 경유·휘발유를 만드는 정유소 |  | 삭제 |
| projects/showcase_geo/direction.yaml | 원유는 팔리고, 공장은 타격 | 원유는 계속 팔려 나갔다 / 경유·휘발유 만드는 공장이 타격 |  | 삭제 |
| projects/showcase_geo/direction.yaml | 7~8월 한국 항구 선적 |  | 17만 6천 ton 이상 · 대부분 경유 | 삭제 |
| projects/showcase_geo/direction.yaml | 미국 | 지난해 러시아 석유회사들을 제재 |  | 삭제 |
| projects/showcase_geo/direction.yaml | 미국 재무부 | 일반허가 135호 / 러시아산 경유 판매·운송·수입 허용 |  | 삭제 |
| projects/showcase_geo/direction.yaml | 에너지 휴전 |  | 나흘 10월 11일 발효 → 10월 15일 끝 | 삭제 |
| projects/showcase_geo/direction.yaml | 워싱턴 | 러시아산 경유 거래 |  | 삭제 |
| projects/showcase_geo/direction.yaml | 네 장면 | 모자란 경유 한 가지로 이어져 있다 |  | 삭제 |
| projects/showcase_geo/direction.yaml | 아직 규명되지 않은 것 | 지뢰를 누가, 언제 묻었나 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 발다이 토론클럽 연례회의 | 9월 28일 – 10월 1일 · 모스크바 지역 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 · 발다이 연설 | 세계가 위험한 순간을 지나고 있다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 이날 발언의 두 갈래 | 안보 / 에너지 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 발언의 성격 | 핵무기 사용 결정 발표는 아니다 / 서방에 개입의 한계를 경고 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 러시아 → 나토 서한 | 칼리닌그라드 방어를 위해 핵무기 사용 가능 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 나토 답신 · 9월 30일 | 방어 동맹임을 강조 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 앨리슨 하트 나토 대변인 | “러시아의 무력 위협과 무책임한 핵 수사를 규탄한다” |  | 삭제 |
| projects/valdai-2026/direction.yaml | 뤼터 나토 사무총장 | 러시아의 핵 위협을 심각하게 받아들이지 않는다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 · 발다이 연설 | 유럽 국가를 공격할 계획이 없다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 · 발다이 연설 | 우크라이나에 무기 공급하는 유럽 공장도 공격 계획 없다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 | 우크라이나용 무기 생산 유럽 공장을 감시하고 있다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 · 3자 회담 | 의제가 마련되면 시진핑·트럼프와 3자 회담 준비 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 수바우키 회랑 길이 | 출처마다 설명이 엇갈린다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 · 10월 1일 | 제재 해제 때까지 세계시장에 경유를 공급하지 않겠다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 러시아 · 9월 30일 | 연료 생산업체 경유 수출 금지 / 10월 31일까지 연장 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 비생산업체 대상 | 경유 수출 금지 1월까지 유지 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 러시아 휘발유 평균 가격 |  | +21% 연초 대비 | 삭제 |
| projects/valdai-2026/direction.yaml | 러시아 연방반독점청 · 9월 30일 |  | 58건 주유소 체인 폭리 의심 사례 조사 | 삭제 |
| projects/valdai-2026/direction.yaml | 푸틴 대통령 | 러시아도 우크라이나에 같은 방식으로 대응하고 있다 |  | 삭제 |
| projects/valdai-2026/direction.yaml | 하나로 묶은 메시지 | 군사적 긴장 · 연료 공급 · 제재 |  | 삭제 |
| prompts/examples/hormuz_direction.yaml | 기자회견 · 9월 18일 | 전쟁에 개입하는 파병은 없다 / 한국 선박·국민 보호는 최소한으로 계속 |  | 삭제 |
| prompts/examples/hormuz_direction.yaml | 2025년 수입 중 호르무즈 경유 비중 |  | 61% 원유 / 54% 나프타 | 삭제 |
| prompts/examples/hormuz_direction.yaml | 국제해사기구 · 6월 11일 기준 | 선박 공격 46건 / 선원 사망 14명 / 발 묶인 배 약 1,000척 · 선원 2만 명 |  | 삭제 |
| prompts/examples/hormuz_direction.yaml | 거론된 선택지 | 해상초계기 / 군수지원함 |  | 삭제 |
| prompts/examples/hormuz_direction.yaml | 이재명 대통령 · 발언 요지 | “전쟁에 관여하거나 들어가는 / 파병은 없다” |  | 삭제 |
| prompts/examples/hormuz_direction.yaml | 미 중부사령부 발표 |  | 10억 배럴 호위 작전으로 반출된 원유 | 삭제 |
| prompts/examples/hormuz_direction.yaml | 2025년 기준 |  | 61% 원유 수입의 호르무즈 경유 비중 | 삭제 |
