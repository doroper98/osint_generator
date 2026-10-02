---
id: R-0164
from: opus
to: fable
kind: phase_report
responds_to: [D-0139]
phase: "G14"
version: v5.3.0
commit: f17ba8d
status: done
---

# G14 v5.3.0 — 겹침 카드(cascade) 채택 완료: adopted 승격·720p 완성본·artifacts

작업 브랜치 `claude/brave-rubin-qiha47`(= `claude/busy-johnson-seir7o` pull --rebase 위, 사용자 지시). PR 없음.

## 1. 커밋
| § | 커밋 | 내용 |
|---|---|---|
| §0 | aebc65d | VERSION 5.3.0, CHANGELOG Unreleased → v5.3.0, v5.2.0 대장 행(d4703d9, D-0134), Tier 1·2 헤더, HANDOFF·README |
| ack | 3358c1f | R-0163 |
| §1·§2 | b8fa100 | cascade 주석 "사용자 합격 값(D117)"(값 무변경), registries 주석·장르·예시·예제·docstring "시안" 제거, direction_grammar 한 줄(D 문안 그대로) |
| §3 | c63bc6a | `[cascade-label-under]` hard = 지금 보이는 마커(at_place 포함)·경로·봉쇄선 이름표만. `[cascade-label-hidden]` warning(새 id `cascade_label_hidden`) = 배경 지명 회피·해역 깔림. provenance `cascade{status, events, items, hidden_labels[]}`. 밀기 전환 새 카드 글자 = max(focus, shift) 뒤 절반(`text_sec`) |
| §4 | cd51296 | 핸드오프 08 §15, 19 §3 판정 3.16, docs/12 cascade 6행(5종 hard + hidden warning), DEVLOG |
| §5 | 126b0c2 | `reports/phaseG14/hormuz_cascade.json`(25/25) + 테스트 |
| §1 승격 | **f17ba8d** | `cascade.status: adopted` + 단언 1 — 조건 통과 뒤 마지막 커밋 |
| §6 | artifacts **86a5724** | `artifacts/phaseG14-v5.3.0` |

## 2. 테스트
- 전체 pytest **1255 passed · failed 0 · skip 0**(adopted 직전 HEAD). adopted 뒤 관련 59 passed.
- 새 테스트 7(`tests/test_g14_cascade.py`): adopted·문법 줄·필드 표·지연·hard/warning 분리 2·골든 기록. 갱신: severity 표, checks 항목 수 32 → 34(e2e·데모 — **기존 32 단언은 v5.2.0 cascade 추가 때 갱신이 빠져 이미 실패 중이었다**).
- 환경 복원(테스트 입력, gitignore): hormuz_korea 1080p 티어·클립·청와대 휘장, fed_timeline_demo(phaseG3), fed_policy_2026(phaseG4 shared + 연준 사진 6장 media_fetch --only), ratcliffe2026(edge 재합성·국기·라이브러리 초상). **fed 는 렌더·연출 없이 테스트 입력 파일만 복원**(D115 범위 판단 — 되돌릴 수 있음).

## 3. 골든
`python -m engine.render projects/hormuz_korea --preview golden` → **25/25 = phaseG12 기준선**(25_END 도장 가린 md5). 코드 변경 전·후 두 번 같음. checks hard 0, cascade·cascade_label_hidden 0.

## 4. checks (hormuz-talks-2026, 연출 v11)
- `--preview auto`: **hard 0**, warning 20 — `cascade_label_hidden` **15**(이라크·바그다드·키르쿠크·하마단·테헤란·이스파한·이란·나자프·아바즈·바스라·야즈드·쿠웨이트·시라즈·쿠웨이트 시·부셰르, 전부 회피), media_beats 1, endcard_roll 1, geo_unsourced 3.

## 5. 720p 완성본
- 음성: 컨테이너에 없어 edge-tts 재합성(54문장 **330.50초**, 이전 완성본 330.49초). 콘티 판 기록 없음(재사용할 것이 없었고 렌더 필수 단계 아님).
- `final_720p.mp4` md5 **f5342ad4168641b401d51703f91a5b42**, 1280×720, 330.50초, **I −14.0 LUFS · TP −1.7 dBFS** · LRA 3.0, audio_qa 전부 ok. 렌더 3분 47초(jobs 4).
- provenance: `cascade.status: adopted`, rules_hash `c81a0d1e2d377c356d1944b49e2b97e0a8259981`, drops [].

## 6. 판단·남은 점(되돌릴 수 있음)
- **문장 지명 판정은 이름 대조를 쓰지 않는다.** 처음엔 "같은 구간 마커와 이름이 같은 지도 라벨"도 hard 로 봤더니 테헤란(마커가 안 보이는 순간의 도시 라벨)이 hard 로 잡혔다. D 문언(마커·at_place·경로 이름표만)대로 고쳤다. 마커가 보이면 이름은 마커 라벨이 보여 준다.
- 해역 이름이 카드 밑에 깔리는 것도 warning(배경 지명)으로 분류했다. 종전엔 hard. 이번 영상 0건.
- 밀기 전환 지연으로 v11 의 6·7번째 사건 카드 글자가 0.05초 늦게 뜬다(0.25 → 0.30초). 사용자 합격 시트와 시각 차이 무시할 수준이나 검수 대상.
- DECISIONS 새 행 없음(Fable 몫).

다음: Fable 검수 → overhaul/v2-map-engine merge·main ff·TAGS_PENDING v5.3.0.
