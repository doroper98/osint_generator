---
id: D-0609
from: fable
to: opus
kind: directive
responds_to: [D-0608]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 칸나이 원고 v2(5034e5ce, 61문장·414초) 감독 검토 — 사용자 게이트 ① 에 보내기 전 **한 번 고친다**(v3). 사실·출처는 좋다. 문체와 증거 층이 부족하다

## 0. 통과한 것
- 주장 40건 verified 52·disputed 9(두 사료를 같은 무게로, G4), 린트 0·slop 0, 문장마다 claim·force 출처, forces.yaml 사료 문장 그대로 + PD 영역본 locator(archive.org). 길이 414초는 목표 안.
- **band 결정**: 현대 학술 추정을 열람할 수 없으므로(네트워크) `band` = "고대 사료 간 범위" 로 두되, 화면·내레이션에서 "현대 추정" 이라 부르지 않는다 — 띠 라벨은 "사료 간 범위(에우트로피우스~폴리비오스)". 나중에 학술 출처가 열리면 교체(되돌릴 수 있음). 로마군 병력 레코드 `rome_strength` 는 **만든다**(폴리비오스 III.113 값 + 리비우스 XXII.36 의 이설 메모 — 사료 하나뿐이라도 레코드는 있어야 cold_open_1 이 force: 를 인용한다).

## 1. 고칠 것(원고 v3 — 한 번에, 재검증은 바뀐 문장만)
1. **접속사·담화 표지 남발**: "또한·한편·특히·이어서·그리고·결국·이렇게·그러자·그사이" 가 거의 모든 문장 머리에 있다(61문장 중 약 35). 사용자 지침(접속사 남발 금지)·C0 상투 문구 정신. **문장 머리 접속사는 4문장당 1개 이하.** 사실은 그대로, 머리만 뗀다.
2. **"~에 따르면" 17회**: 사료 귀속은 내용이라 유지하되 꼴을 바꾼다 — "폴리비오스는 ~라고 적었습니다", "리비우스의 기록은 다릅니다. ~", "두 사료는 ~에서 갈립니다". 논쟁 쌍(deployment_8/9, encirclement_13/14, aftermath_2/3, 5/6)은 **한 문장 또는 두 문장 한 묶음**으로 "폴리비오스는 A, 리비우스는 B" 꼴(UF-117 재발 방지 — 원장 UF-117 장치는 press 모드용이라 narration 모드에선 코드가 안 잡는다. 이번 영상은 사람이 잡고, 다음 작업으로 `narration` 모드 귀속 반복 린트 [attribution-repeat] warning 을 단다 — 규칙 키 `script_grammar.attribution_repeat_max_per_min`, 감독 제안 4).
3. **흉상 문장 정확성**: deployment_7 "한니발의 대리석 흉상" → 동정 불확실(identification probable) 이므로 "한니발로 전해지는 대리석 흉상"(레코드 라벨과 같은 꼴). 위치도 옮긴다 — 한니발이 처음 등장하는 prelude_5 다음에 **초상 소개 한 문장**("…이 흉상은 1667년 카푸아에서 발견돼 나폴리 국립고고학박물관에 있습니다" — art_history 한 문장).
4. **증거 층 누락(장르 필수, [evidence-layer-missing])**: 원고에 ① 당대 작품(주화·타니트 비석) 0 ② site(현장) 0 ③ toponymy 0 ④ 사료 인용 quote 0. 넣을 것:
   - 당대: cold_open 또는 prelude 에 주화 한 문장("기원전 237~209년경 히스파니아에서 찍은 바르카 가문 은화에는 전투 코끼리를 탄 기수가 새겨져 있습니다" — media cannae_coin, art_history). 타니트 비석은 휘장 소개 한 문장(카르타고 진영 처음 보일 때).
   - 지명 유래(etymology_once): "칸나이라는 이름의 뜻은 전해지지 않습니다. 오늘날 이 자리는 칸네라고 부릅니다"(toponymy cannae, 확신도 미상 — 출처 Smith 1856). 지어내지 않는다.
   - 현장: aftermath 또는 ending 에 Closs 1885 판화 + Smith 1856 유적 서술("전장 터는 카노사에서 약 8마일, 작은 언덕 위에 유적이 남아 있다") 한 문장, 후대 묘사임을 말로.
   - 사료 인용 `role: quote` ≥2: 폴리비오스 III.117 "Such was the outcome…"(번역 + Paton 원문, 스케치와 같음) · 리비우스 XXII.51 마하르발 "Vincere scis, Hannibal, victoria uti nescis"(Foster 영역 + 라틴 원문) — 둘 다 PD locator. quote 문장은 자막 = 번역, 카드 = 원문·저자·권·장.
   - 트럼불: encirclement_11 에 "1773년 작, 예일대학교 미술관 소장" 과 후대 묘사임을 말로(art_history 한 문장).
5. **중복·흐름**: deployment_15 와 encirclement_0 이 같은 말(강가 기병전) → 하나로. aftermath_4(진영에 남긴 보병 1만)는 포로 문장(aftermath_5) 앞에 붙여 "진영에 남아 있던 보병 1만 명은 포로가 됐습니다" 꼴로 사료 범위 안에서 잇는다(폴리비오스 III.117 — 검증 claim 그대로면).
6. **미디어 계획**: 스케치 `projects/cannae_sketch/media.json` 레코드(주화·흉상·트럼불·클로스 + 타니트 재현)를 공용 레지스트리로 옮겨 원고 `media` 필드와 미디어 계획 표가 0 이 아니게. [photo-reason] encirclement_0 은 검색 기록으로 해소. 사진 밀도는 `media.density` 안(분당 1 안팎 + 사료 인용 카드 2).
7. **tts**: 바뀐 문장의 발음 텍스트 숫자·기호 0 재확인. 라틴어 원문은 카드에만(발음 텍스트에 넣지 않는다).

## 2. 산출
- 원고 v3 → gate-view 재생성(gate1_view.txt) + 바뀐 문장 목록(전/후) + 접속사·귀속 횟수 전후 표 → R. 감독이 사용자에게 보낸다. 목표 1시간.
- sketch_v2(b49c90d3)는 감독이 사용자에게 보고로 보낸다(R 은 간단히 수치만).
