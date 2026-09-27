<!--
tier: 2
last_synced_with: v0.43.4
ssot_for: [v2-direction-schema, v2-visual-qa, v2-prompt-specs]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 17. AI 연출가 · 시각 자기검수 루프 · 프롬프트 명세

## 0. 왜 필요한가
채팅 영상의 품질 절반은 엔진이 아니라 **편마다의 연출 판단과 프리뷰를 보고 고치는 과정**에서 나왔다. v3 연출층(약 150줄)은 이 영상 하나를 위해 손으로 썼고, 매 라운드 프리뷰 시트를 보고 가림·잘림·글리프 깨짐·과한 강조를 고쳤다. 이 과정을 파이프라인 단계로 만든 것이 이 문서다.

---

## 1. 흐름
```
script.yaml + plan.json + 자산 목록(assets.lock) + 지오 역량(티어·라벨 범위) + 규칙(rules/video_rules.yaml)
   → [연출 LLM] direction.yaml v1
   → engine.validate (스키마·레지스트리·예약영역·숏 규칙)  ── 실패 → 연출 LLM에 오류 전달, 1회 재작성
   → engine.render --preview auto  → prev/*.png + sheet.jpg + checks.json(결정적 검사)
   → [시각 검수 LLM] qa_verdict.v1.json
   → 이슈 있으면 [연출 LLM] direction.yaml v2 → 재프리뷰 → [검수] (최대 2회, 결정적 종료)
   → 사용자 승인 게이트 ② (잔여 이슈 목록과 함께)
```
루프 상한과 종료 조건은 코드가 결정한다(agents_reviewer AP-V6-2, AP-V6-5: 루프 제어에 LLM 쓰지 않음).

---

## 2. 연출 결과물 형식 — `direction.yaml` (선언형 권장)

v3는 파이썬(`render3.py` 상단)으로 연출했다. 자동화에서는 **선언형 YAML**이 안전하다(스키마 검증, 코드 실행 없음, 버전 비교 가능).

```yaml
version: 1
shots:
  - scene: open
    at: {sid: open_0, off: 0}          # 문장 앵커
    mode: cut                          # cut | move | dip
    camera: {lon: 127.35, lat: 36.35, w: 6.4}
  - scene: route
    at: {sid: route_1, off: -0.6}
    mode: move
    dur: 3.4
    camera: {lon: 88.5, lat: 19.5, w: 90}
events:
  - type: marker
    start: {sid: route_0, off: 0.1}
    end: {scene_end: route}
    lon: 56.35
    lat: 26.55
    label: 호르무즈 해협
    sub: 가장 좁은 곳 약 39km
    side: right
    hl: true
  - type: badge
    start: {sid: open_0, off: 0.6}
    end: {scene_end: open}
    entity: lee_jae_myung               # 엔티티 레지스트리 id (07 §6) → kind/flag/portrait 자동
    lon: 125.05
    lat: 37.25
    R: 34
  - type: panel
    kind: refusal
    start: {scene_start: ask, off: -0.2}
    end: {sid: ask_3, off: 0.5, edge: end}
    data: {requester: trump, targets: [de, gb, jp, au, kr], refuse_anchor: ask_1}
  - type: clip
    asset: niovi                         # 미디어 레지스트리 id (14 §6)
    start: {word: {sid: war_2, text: 닫았습니다}}
    dur: 5.0
    place: map_left
```
- 앵커 문법: `{sid, off}`(문장 시작 기준), `{sid, off, edge: end}`(문장 끝), `{scene_start|scene_end, off}`, `{word: {sid, text}}`(단어 앵커).
- 좌표 대신 `place: map_left | map_right_low | panel_center | card_slot` 같은 **배치 슬롯**을 허용하고, 엔진이 예약 영역을 피해 실제 좌표를 계산한다(연출 LLM이 픽셀을 다루지 않게).
- 모든 타입은 이벤트 레지스트리(15 §P10)에 있어야 한다.

---

## 3. 결정적 사전 검사 (`checks.json`) — LLM 검수 전에 코드가 잡는 것
| 검사 | 방법 | 기준 |
|---|---|---|
| 요소 겹침 | 프레임마다 RESERVED 사각형 + 카드/미디어/자막/날짜 영역 교차 계산 | 핵심 요소(뱃지·마커·미디어) 교차 0 |
| 화면 밖 잘림 | 뱃지 전체 높이(R×3.3), 라벨 폭 포함 경계 검사 | 0 |
| 글리프 누락 | 그릴 모든 문자열의 문자가 해당 폰트에 있는지(fontTools cmap) — Mono+한글, Gmarket 공백 | 0 |
| 숏 규칙 | 숏 길이, 장면당 이동 수, 암전 빈도 | 숏 ≥ 6초, 장면당 이동 ≤ 1(예외 표시), 암전 ≤ 1/90초 |
| 미디어 비트 | 러닝타임 대비 미디어 수, 장면당 개수, 형태 연속 반복 | 40~60초당 1, 장면당 ≤ 1 |
| 라벨 밀도 | 프레임별 도시 라벨 수 | ≤ 18 |
| 날짜 | 날짜 배지 문자열 형식, 문장 date와 일치 | 100% |
| 자막 | 줄 수 | ≤ 2 |
| 권리 | 사용 자산 전부 레지스트리·라이선스 필드 | 누락 0 |
| 금지 컴포넌트 | 도장, 비네트, 모서리 브랜드/섹션 표기 | 0 |
Hard 실패가 있으면 LLM 검수를 부르지 않고 연출 LLM에 오류만 돌려준다(agents_reviewer AP-V5-29: 결정적 게이트 통과 후에만 LLM).

---

## 4. 시각 검수 LLM

### 4.1 입력
- `prev/sheet.jpg`(장면별 2~3컷, 4열) + 전환 구간 연속 컷 시트 + 각 컷의 시각·문장·연출 이벤트 목록(JSON) + `checks.json` 요약 + 검수 기준(아래).
- `base_llm_worker`에 이미지 첨부 기능 추가: `claude -p`에 이미지 파일 경로를 프롬프트로 전달(Claude Code는 로컬 이미지 파일을 읽을 수 있다). 브리지 방식이 막히면 API 경로로 전환.

### 4.2 검수 기준(루브릭 — `01` 피드백 전체에서 도출)
1. 화면이 휑한가(확대 장면에 라벨·도시가 충분한가) / 과밀한가
2. 요소가 가려지거나 잘렸나(뱃지 머리, 라벨, 카드 뒤)
3. 모서리에 날짜 외 요소가 있나, 도장·비네트가 있나
4. 색이 사실을 왜곡하나(국가 채움 과다, 대륙붕과 육지 혼동)
5. 관계선·요소가 동시에 몰려 나오나(정돈)
6. 미디어가 문장 대상과 맞나, 자료사진 표기·출처 줄이 있나
7. 글자가 읽히나(크기·헤일로·대비), 깨졌나
8. 같은 장면에 카메라가 두 번 이상 움직였나, 먼 거리를 컷 없이 이동했나
9. 전체가 "프로 다큐처럼 보이는가"

### 4.3 출력 스키마
```json
{"verdict": "pass|revise",
 "issues": [{"frame": "p_0184.20", "severity": "hard|soft", "category": "occlusion|empty|density|color|order|media|legibility|camera|style",
             "evidence": "부산 국기 뱃지가 선택지 카드 뒤에 가려짐", "fix": {"event_ref": "badge:busan", "suggest": "place: map_right_low 또는 lat 22.3"}}],
 "praise": ["…"]}
```
- `evidence` 필수(근거 없는 지적은 무시 — agents_reviewer AP-V6-8).
- 검수 LLM은 연출 파일을 **직접 고치지 않는다**. 수정은 연출 LLM이 한다(AP-V6-11: 검수자는 지시만).

---

## 5. 프롬프트 명세 (템플릿 파일 + 규칙 파일 결합, 15 §P3)

모든 프롬프트 공통 머리말(규칙 파일에서 자동 삽입):
- 금지 문구 목록과 판단 기준(`03` §2)
- 사실·균형 원칙(`03` §3)
- 출력은 지정 스키마 JSON/YAML만

### 5.1 research (`prompts/research.md`)
- 역할: 검증된 소스 레코드(18)를 바탕으로 사실 목록을 만든다. 부족하면 웹 검색으로 보강하되 모든 사실에 `source_ids`.
- 입력: 요청 요지, `sources.json`, `claims.json`
- 출력: `facts: [{id, text, date, place, actors[], numbers[], source_ids[], confidence, contested(bool), sides?}]`
- 금지: 출처 없는 수치, 한쪽 입장만 있는 논쟁 사실(contested=true면 sides 필수).

### 5.2 script (`prompts/script.md`)
- 역할: 사실 목록으로 원고 YAML을 쓴다. 장면 수·길이는 내용이 정한다(고정 막 금지).
- 입력: 요청, `facts`, 엔티티·미디어 후보 목록, 규칙
- 출력: `02` §2.1 스키마. 문장마다 `date`, `text`, `tts`(숫자·기호 없는 발음 텍스트, 6월=유월·10월=시월·개월은 한자어), `emphasis`(text 부분문자열), `sources`(fact id), 선택 `media`.
- 자기점검 목록(출력 전): 문장당 주장 1개, 자막 2줄 이내, 귀속 동사, 마무리는 예언 대신 미정 사실.
- 예시: v3 `plan3.py SCRIPT` 발췌 5문장(콜드 오픈·수치·귀속·찬반·마무리).

### 5.3 director (`prompts/director.md`)
- 역할: 원고와 타이밍으로 `direction.yaml`을 쓴다.
- 입력: `script.yaml`, `plan.json`(문장 t0/t1), 엔티티·미디어 레지스트리, 지오 역량(티어 범위, 라벨 가능 국가), 이벤트 레지스트리, 숏 문법 요약(`05` §2), 패널 사용 기준(`08` §1), 미디어 비트(`14` §10).
- 출력: §2 스키마.
- 필수 규칙: 장면당 이동 1회, 원거리는 dip, 숏 ≥ 6초, 한 문단 장소는 한 화면, 모서리엔 날짜만, 뱃지·미디어는 배치 슬롯 사용, 패널은 지도가 못 하는 정보에만.
- 예시: v3 연출층을 YAML로 변환한 전체본(Phase 2에서 생성해 `prompts/examples/hormuz_direction.yaml`로 보관).

### 5.4 visual_qa (`prompts/visual_qa.md`)
- §4 전체.

### 5.5 revise_direction (`prompts/revise_direction.md`)
- 입력: 직전 `direction.yaml`, `qa_verdict`, `checks.json`
- 출력: 수정된 `direction.yaml` 전체 + `changelog: [{issue_ref, change}]`
- 규칙: 지적받지 않은 부분은 바꾸지 않는다(회귀 방지).

---

## 6. 모델 운용
- 원고·연출·검수: Opus 계열(구독 브리지 `claude -p` 기본). codex는 선택적 외부 비평자로만(본문 작성 금지 — agents_reviewer AP-V6-11).
- 토큰 절약: 검수 입력 이미지는 컨택트 시트 1~2장(개별 프레임 전부 넣지 않음).
- 실패 처리: 스키마 불일치 → 1회 재요청 → 실패 시 단계 중단·보고(폴백 금지).
