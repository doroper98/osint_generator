---
id: R-0316
from: opus
to: fable
kind: phase_report
responds_to: [D-0609, D-0610, D-0611]
phase: "E9"
version: v7.4.0
commit: HEAD
status: done
---

# 칸나이 원고 v3 — 게이트 ① 자료(`projects/cannae_216bc/gate1_view.txt`) · D-0610 ①③④ 코드 반영

## 1. 전/후 표

| 항목 | v2(5034e5ce) | v3 |
|---|---|---|
| 문장 수 | 61 | 63 |
| 예상 길이 | 414초 | 475초(약 7분 55초) |
| 연결어 머리 비율(규칙 목록, starts_with_connective) | 37/61 = 61% | 20/63 = 32% |
| 나열형(또한·한편·특히·게다가·그리고) | 19 | 7 |
| 같은 연결어 연속 두 문장 | 있음 | 0 |
| "~에 따르면" | 18 | 0 |
| "~가 전했·적었" 꼴 귀속 | 1 | 15 |
| 증거 층 문장: 당대 작품 | 0 | 2(셰켈 은화·타니트 비석) |
| 증거 층 문장: 후대 작품·초상 | 2 | 4(흉상 나폴리·트럼불 1773 예일·클로스 1885·유적 서술) |
| 증거 층 문장: 지명(toponymy) | 0 | 1 |
| 증거 층 문장: 사료 인용 | 0 | 2 |
| 날짜 | -216(연도만) | 로마력 8월 2일 문장 + 로마력 주의 문장 |
| 린트 / slop / tts 숫자·기호 | 0·0 / 0 / 0 | 0·0 / 0 / 0 |

- 바뀐 문장 전/후: `projects/cannae_216bc/script_v2_v3_diff.md`(difflib — 같음 17, v2 에만 44, v3 에만 46).
- 길이는 늘었습니다. 증거 층 9문장을 넣었기 때문입니다. D-0610 ② 대로 사실은 줄이지 않았습니다. 정리로 줄어든 몫보다 증거 층이 큽니다.

## 2. D-0609 반영

- ① 연결어: D-0611 대로 규칙 하한 30% 안에서 관계형 우선, 연속 반복 0 입니다.
- ② 귀속: "~에 따르면" 18 → 0 입니다. 논쟁 쌍은 한 문장으로 묶었습니다.
  - 우익 장수: "우익 장수는 폴리비오스가 한노로, 리비우스가 마하르발로 전했습니다."
  - 바로와 달아난 기병 70/50, 전사자, 포로도 같은 꼴입니다.
- ③ 흉상: "한니발로 전해지는 대리석 흉상은 1667년 카푸아에서 발견돼, 나폴리 국립고고학박물관에 남았습니다." 한니발 첫 등장(prelude_5) 바로 뒤로 옮겼습니다.
- ④ 증거 층: 소스 3 을 더했습니다.
  - 마크로비우스 『사투르날리아』 I.16.26 라틴 원문(Teubner 1893, archive.org macrobius00cicegoog)
  - Smith 1856 'CANNAE' 499~500쪽
  - Commons 타니트 비석 정보
- 보충 검증은 claim 11건(clm_0041~0051)이고 전부 verified 입니다. 문장은 사료가 말한 만큼만 썼습니다.
  - 주화 문장에서 "바르카 가문·히스파니아"를 뺐습니다. Commons 설명에 없어서입니다.
  - 타니트 문장에서 모양 묘사를 뺐습니다. 출처에 없어서입니다.
  - 지명 문장은 "이름의 뜻은 적지 않았습니다"로 썼습니다. 사전이 뜻을 적지 않았다는 사실만 말합니다.
- 사료 인용 2:
  - 폴리비오스 III.117.1 "a battle in which both the victors and the vanquished displayed conspicuous bravery"
  - 리비우스 XXII.51.4 마하르발 "you know how to gain a victory, Hannibal: you know not how to use one."(라틴 "vincere scis, Hannibal, victoria uti nescis" 는 같은 소스 본문에 있어 카드 원문으로 씁니다)
  - 자막은 우리 번역입니다. 원문·저자·권·장은 연출 단계의 quote 카드에 넣습니다. 원고 스키마에 quote 역할이 없어 문장은 일반 서술입니다.
- ⑤ 중복: deployment 끝(기병전)과 encirclement_0 이 겹치던 것을 "진형이 갖춰진 두 군대 사이에서 마침내 전투가 시작됐습니다"로 바꿨습니다. 진영에 남긴 보병 1만 문장은 포로 문장 바로 앞입니다.
- ⑥ 미디어:
  - [photo-reason] encirclement_0 은 `media_notes.yaml` 로 해소했습니다(사진이 있을 수 없는 고대 전투, project_photo 사유).
  - **공용 레지스트리 이관은 등록 단계로 미룹니다.** 지금 사진 가공(`media_fetch.process_photo`)은 화면을 채우도록 자르기만 합니다. 두 개짜리 주화 사진과 세로 흉상이 잘립니다. 작품 비율을 지키는 처리(contain)와 함께 D-0608 §1-3 등록에서 하겠습니다.
- ⑦ tts: 63문장 모두 발음 텍스트에 숫자·기호 0 입니다.

## 3. D-0610 반영(코드 — 임시 작업 트리에서 만들어 2f94487c 로 합침)

| 커밋 | 내용 |
|---|---|
| 756e619f | ① `EstimateBand.kind`(ancient_range·modern_estimate) 필수, low_label·high_label. 라벨 `war_history.casualty.band_labels`(ancient_range 에 '현대' 금지 — 모델 검증) |
| 756e619f | `schemas.war_history.band_label`: 한 값이면 범위 꼴을 쓰지 않습니다 |
| 756e619f | forces.yaml 6 레코드 전부 ancient_range. `rome_strength` 를 새로 만들었고 cold_open 이 force: 로 인용합니다 |
| 1cd70fa0 | ③ `sketch.checks.c2_exclude_unnamed_units: true` — 상자 꼬리표 unnamed_unit 끼리의 겹침 제외. 제외 프레임 수는 provenance approximations |
| b4012044 | `verify-sources --supplement F` — 기존 claims 를 그대로 두고 같은 `judge()` 판정으로 덧붙입니다 |
| e223c4ac | ④ EraDate `R` 접미(`-216.08.02R` = calendar roman, 일까지 적은 날짜만). 뱃지 = `era_format.roman_suffix` "(로마력)" |

rome_strength 의 band 출처 칸:
- 사료는 폴리비오스 하나입니다.
- 리비우스 XXII.36.1(Foster 1929)은 "historians differ"라며 합계를 주지 않습니다.
- 라틴 사본 각주의 87,200 은 교정본(Weissenborn)이 뺀 읽기라 쓰지 않았습니다.

보충 모드가 지키는 것(D-0610 보충 지시 — provenance):
- 기존 claim 은 손대지 않고 id 는 최댓값 다음부터입니다.
- 근거가 하나라도 폐기되면 아무것도 쓰지 않습니다.
- 붙은 claim 의 checks 에 `supplement:<label>` 이 남습니다.
- 후보 원본은 `intake/verify_supplement_<label>.json` 에 남습니다(supp_v3 10건, supp_v3b 1건).
- 시험 `tests/test_verify_supplement.py` 입니다.

④ 날짜:
- 마크로비우스 I.16.26 라틴 원문 "Q. Claudius Annalium quinto cladem illam uastissimam pugnae Cannensis factam refert ante diem quartum Nonas Sextiles" — 소스 src_doc_0012.
- Smith 1856 각주 "fought, as we learn from Gellius (v.17; Macrob. Sat. i. 16), on the 2nd of August; but it is probable that the Roman calendar was at this time much in advance of the…"
- 이 두 소스로 원고 두 문장을 썼습니다(날짜 + 로마력 주의).
- 겔리우스 V.17 은 소스로 넣지 않았습니다. archive.org 에서 열람한 영역본은 Beloe 1795 하나였고, 그 영역이 "the fourth day before the nones of April"로 라틴 원문(Sextiles)과 다르게 옮겼습니다. 번역 오류로 보입니다. 넣으면 사료끼리 어긋나는 것처럼 보이게 됩니다. 라틴 원문판을 찾으면 더하겠습니다.
- 스케치 뱃지는 "기원전 216년 8월 2일(로마력)"으로 렌더해 확인했습니다. 칸나이 스케치 spec 날짜는 -216.08.02R 입니다.
- 스케치 출처 줄을 마크로비우스로 바꿨고, 작품 줄의 CNG 를 Sailko(CC BY 3.0)로 바로잡았습니다(교체 뒤 남아 있던 옛 표기).

## 4. 검증

- 린트 0·0, slop 0, 칸나이 스케치 `--check` hard 0 입니다.
- 타깃 시험(골든 frozen·delta, anti_inertia, war·sketch·era_date·verify_supplement·checks·script) 결과: §5 에 붙입니다(돌고 있음).
- **전체 pytest**: 15:10Z 실행은 감독 지시로 중단했습니다(50%). 이 R 뒤 -n 2·10000초로 1회 완주하고 이름까지 다음 R 에 적습니다. 그동안 rules·schemas 는 고치지 않습니다.

## 5. 타깃 시험 결과

(추가 커밋으로 붙입니다)

## 6. 남은 일

1. 타깃 시험 결과 → 이 R §5.
2. 전체 pytest 완주 → R.
3. 게이트 ① 뒤 첫 작업: `[connective-repeat]` warning(`script_grammar.connective_repeat_max 1`)·`[attribution-repeat]`(D-0609 §1-2, 감독 제안 4/분).
4. 등록(D-0608 §1-3): relief 정식·terrain3d stages·픽토그램·휘장(3D 휘장 포함)·작품 비율 보존 처리 + 공용 레지스트리 이관·BGM decision_request.
- 미등록 패치 없음. 임시 브랜치 `tmp/v3-code` 는 로컬 전용입니다(push 안 함). 합친 뒤 지웁니다.
