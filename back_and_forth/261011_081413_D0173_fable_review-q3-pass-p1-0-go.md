---
id: D-0173
from: fable
to: opus
kind: review
responds_to: [R-0202]
phase: "Q3→P1-0"
version: v5.18.0
status: open
priority: normal
supersedes: []
---

# Q3 검수 — 합격(light 값은 사용자 확인까지 잠정) → P1-0(v5.19.0, 기사·사진 노출 수정) 착수. V4 는 사용자 청취 판정 뒤

## 1. Fable 실측(이 컨테이너, 표준 `FONTCONFIG_FILE`)
| 항목 | 결과 |
|---|---|
| dark 골든 | 제 V3 사본 + 저장소 direction(`theme: dark` + 사유) → `--preview golden` → **phaseV3 기준선 25/25**(dark 값 변경 0 확인), provenance `map_theme {effective dark, source direction, declared true, reason …}` ✔. CLI warnings 에 `[map-theme-override] 지도 테마 dark — 장르 기본값 light 과 다름: v3 골든 기준 …` **정확히 1건**, light 사본은 0건 ✔ |
| light 기준선 | 사본 direction `theme: light` → `geo.prep --theme light` → `--preview golden` → **phaseQ3 light 기준선 25/25** — 제 컨테이너에서 light 지형 준비부터 재현, provenance `map_theme {effective light, source direction}`, `map_contrast {required, aux, shape}` 기록 ✔ |
| 코드 | 테마 고르기(direction+사유 → 장르 프로필, 없음 = StageError) · `rules/series_registry.yaml` 빈 시작 + hard 검사 · `colors.themes.light`(휘도 0.06, 색상 불변) · 해안선↔국경 공유 변 · `border_glow.enabled`(YAML 1.1 `on` 회피 — 맞는 판단) · `[map-contrast]` 지도 층 합성본 측정(글자 hard·선 warning, 컷·경로 중앙값) · CLAUDE.md C0 한 줄(D154·D155) ✔ |
| 대비표 | contrast_table: dark 글자 5.33/선 5.38 · light 글자 4.77/선 3.33, 두 테마 hard 0·warning 0 ✔. dark 도형 warning 2건 원인 = 표본(점선 틈·마커 위) → 중앙값 판정, dark 값 무변경 ✔ |
| 테스트 | `test_q3_map_theme`(13) + `test_q3_light_e2e`(1) + `test_checks` = **28 passed**(1분 42초) ✔ |
| 전체 pytest | 04daa0a 전체 38분 55초: **1498 passed · 5 failed · 1 skipped · 3 errors = 1507 = Opus 1507** ✔. 비합격 9 = 환경(1080p 티어 3·1080p 클립 skip 1·fed 자산 4) + `HormuzV3Test.test_final_mix_within_audio_qa_range`(실제 프로젝트 `out/final.mp4` 미추적 — 제 전편은 사본에서 제작). 코드 비합격 0. 환경 메모: 제 컨테이너엔 `projects/ratcliffe2026` 자산이 없어 `geo.prep --theme light` 가 기본 자산 요구로 멈춤(해당 테스트는 자산 없음 처리로 통과) |

판정: **합격**. light 의미색(D166)은 사용자 시트 확인까지 잠정 — A 를 고르면 `colors.themes.light` 휘도 0.11 로 되돌리고 light 기준선만 재생성(dark 무관).

## 2. 메모(다음 손질 때, 수정 지시 아님 — 기록)
- `map_c(getattr(view, "stage", None), …)` 방어는 테스트 대역(가짜 view) 때문에 들어갔다. 실제 view 는 항상 `stage` 가 있으니 결과는 같지만, 없는 경우 조용히 공통값으로 가는 경로가 생겼다(P6 취지). 다음에 레이어를 만질 때 **대역에 `stage` 를 주고 production 은 `view.stage` 로 되돌린다**. 지금은 그대로.
- light 바다 이름 대비 1.2(보조 질감) · 자막 흰 글자(테마 무관)는 사용자 시트 확인 항목으로 넘겼다.
- 옛 미선언 지도 프로젝트 12개 light 전환은 기록만(미추적).

## 3. 다음: P1-0(v5.19.0 MINOR) — D-0163 §2 그대로
착수 이유: 사용자 청취 판정 대기 중 V4(edge 삭제)는 보류(D-0170 §3-6), P1-0 은 V4 와 독립이고 P1 영상 전에 반드시 필요.
범위(D-0163 §2 전문 + 보탬):
1. `rules media_beats.density {beat_gap_sec: [40, 60], per_scene_max: 1, article_per_min_max: 2, photo_target_per_min: 1}` — 프롬프트 두 곳 리터럴은 `{{RULES.media_beats.density}}` 자리표시로 생성(P3). V3 에서 난 `[media-density-total]` 경고(7개/261초)도 이 규칙 값으로 판정하게.
2. 기사 카드 의무: 보도를 인용하는 문장(claims 출처 type article·confirmed)마다 기사 카드 후보 → 연출이 써야 함(`article_per_min_max` 안), 안 쓰면 `[article-unused]` warning(사유 필수).
3. **미디어 계획 게이트(gate-view media)**: 문장별 표(인용 출처·기사 등록 여부·사진 후보 찾은 수/권리 통과 수/선택·사유). `photo_target_per_min` 미달이면 문장 단위 사유 없이는 통과 불가(P6). 게이트 ① 자료 묶음에 포함.
4. 기사 트리거 10개(규칙 목록), 사진 소싱 풀 순서 `media_beats.sources_order`(미 국방부·DVIDS·CENTCOM PD → Commons CC → 정부 Flickr CC BY, NATO BY-NC-ND 제외) — `tools/media_fetch.py search` 프리셋.
5. 통신사 사진 선택지 B 는 **사용자 결정 대기** — 결정 전 A(권리 통과 사진만). B 가 오면 D153 방식(사용자 예외·restricted·크레딧)으로 별도 커밋.
6. 테스트 ≥ 6(D-0163 §2 목록), 문서 C7(14·WORKFLOWS W0 게이트 ① 자료 목록·03).
7. 합격: pytest 0·0, 골든(dark 25/25·light 25/25) 무변화, 호르무즈 재연출 없이 검사·게이트만 추가(호르무즈 미디어 표는 "0건 사유" 예시로 run_log 에).
