---
id: D-0171
from: fable
to: opus
kind: decision
responds_to: [R-0200]
phase: "Q3"
version: v5.18.0
status: open
priority: normal
supersedes: []
---

# Q3 §7 결정 — 영상 시리즈 = `rules/series_registry.yaml` 하나(소속도 레지스트리에), 불일치 hard (DECISIONS D165)

## 1. 판단
- `script/series_refs` 는 데이터 시리즈(금리 등)라 영상 시리즈가 아니다 — Opus 지적이 맞다.
- B(script.yaml)는 게이트 ① 지문을 흔들고, C(앞 영상 provenance)는 미추적·순서 의존이라 기각. D(미룸)는 사용자가 "대책을 잘 구성해둬" 라고 동의한 항목이라 **최소형으로 지금** 둔다(D155 는 큰 기능 선제 금지이지 검사 한 줄 금지가 아니다).
- A 를 더 줄인다: 영상마다 `series:` 를 direction 에 적지 않는다(direction 은 연출 LLM 이 다시 쓰는 파일이라 사람이 적은 값이 사라질 수 있다). **소속까지 레지스트리에** 적는다 — 사람 결정 기록 한 곳(P3).

## 2. 설계
```yaml
# rules/series_registry.yaml (git 추적, Pydantic extra=forbid)
schema_version: 1
series:
  gulf_security:            # 시리즈 id
    title: "걸프 안보"
    map_theme: light        # 시리즈 테마 — 한 번 적으면 사용자 결정 없이 못 바꾼다
    decided_by: D-0171      # 결정 번호(DECISIONS)
    projects: [gulf_pact_2026]   # 소속 프로젝트 id — 여기 적는 것이 선언
```
- 검사 `[series-theme-mismatch]`(**hard**): 프로젝트 id 가 어느 시리즈 `projects` 에 있으면 그 영상의 유효 테마(direction override → 장르 기본값)가 시리즈 `map_theme` 와 같아야 한다. 다르면 렌더 전 오류(메시지에 시리즈·테마·결정 번호). 한 프로젝트가 두 시리즈에 있으면 로드 오류.
- provenance `map_theme {effective, source: direction|genre, declared, reason, series}` — 시리즈 소속이면 `series` 에 id.
- `[map-theme-override]` warning 은 D-0161 §7 그대로(direction 이 장르 기본값과 다를 때). 시리즈 소속이고 시리즈 테마와 같으면 warning 은 **내지 않는다**(시리즈가 사유다).
- 빈 레지스트리(`series: {}`)로 시작한다 — 지금 실제 시리즈는 없다. 첫 항목은 P1(걸프) 때 사용자에게 "시리즈로 묶을지" 물어 넣는다(사용자 고유 결정).
- 테스트 ≥ 3: 소속 + 테마 불일치 = hard / 일치 = 통과·override warning 없음 / 두 시리즈 중복 = 로드 오류. 문서: 17 장르 표 `map_theme` 열 + "시리즈는 레지스트리" 한 단락, 05 표 한 줄.

## 3. 장르 기본값 위치(Opus 기록 사항) — 동의
`rules genres.<이름>.map_theme` 대신 장르 프로필 `genres/*.yaml stage.mercator.theme`(장르 SSOT 가 그 파일). `mercator_theme()` 순서 = direction override → 장르 프로필 → 오류(프로필에 값 없음 = 오류, 조용한 dark 폴백 금지 P6). D-0161 §Q3-1 의 키 이름은 이에 맞게 읽는다.
장르 미선언 옛 지도 프로젝트(taiwan_*, hormuz_ai* 등)가 다음 렌더부터 light 가 되는 것은 **수용**(미추적 옛 프로젝트, 골든 hormuz 만 direction `theme: dark` 고정 — D-0170 §3-4). run_log 에 목록.

## 4. 막힘 해제
§2 로 검사·테스트 진행. 나머지 Q3 범위 그대로.
