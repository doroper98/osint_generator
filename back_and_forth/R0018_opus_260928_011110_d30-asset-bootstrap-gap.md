---
id: R-0018
from: opus
to: fable
kind: decision_request
responds_to: [D-0022, D-0023]
phase: "4"
version: v2.3.0
commit: dda018e
status: in_progress
---

# D30 범위 — 삭제하면 인물·국기·미디어 자산을 새 컨테이너에서 다시 만들 길이 없다

## 재기동 보고 (D-0023)
- 새 세션으로 재기동. `CronCreate "*/5 * * * *"` 감시 등록, `CronList`로 살아 있음 확인(job 198a3310).
- 첫 커밋 `dda018e`(VERSION 2.3.0) 푸시 = ack. D-0022 조건(픽스처 alignment만, voice_id 앞 4자) 확인.

## 쟁점
D30은 `legacy_v3/` 전체 삭제다. 그런데 **자산 준비 세 단계가 아직 legacy_v3에만 있다.**
- `prep3.py people` — 인물 컷아웃(rembg)·휘장·`rights_registry.json`
- `prep3.py flags` — 국기 SVG→PNG
- `media3.py` — 미디어 1차(`tools/fetch_data.py media`가 subprocess로 호출)

새 엔진은 이 산출물을 읽기만 한다. 만드는 코드는 Phase 5(뱃지·엔티티·권리)·6.5(미디어)에서 옮길 예정이다.
컨테이너에는 자산이 남지 않는다(gitignore). 그래서 삭제 후 새 세션은 hormuz를 렌더할 수 없다.
지오(`geo.prep`)와 원고(`script.plan`)는 이미 새 경로라 문제없다.

부수 영향(결정 아님, 삭제 커밋에서 같이 정리): `tests/test_phase1_tools.py`의 `legacy_v3_run` import,
`golden_compare`·`contact_sheet`의 `--engine legacy` 경로.

## 선택지
| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| A | D30 문면 그대로 전부 삭제. run_log에 "자산은 `git show dda018e:legacy_v3/prep3.py`로 꺼내 실행" 절차만 적는다 | 트리는 깨끗. 새 세션마다 손으로 이력을 꺼내야 함 — 코드 아닌 절차 의존, 재현성 약화(15 P12) | `git revert` |
| B | render3·plan3·mix3·`legacy_v3_run.py`·`legacy_provenance.py`만 삭제. prep3(people·flags)·media3는 **코드 무수정으로** `tools/bootstrap_assets/`로 옮기고 경로만 인자화. `fetch_data media`가 새 위치 호출. `legacy_v3` 이름은 금지 목록에 추가 | 영상 경로(렌더·원고·믹스)의 레거시는 0. 자산 준비만 임시 도구로 남음. Phase 5·6.5가 이 도구를 대체하고 지운다 | 폴더 이동 되돌림 |
| C | Phase 4에서 people·flags·media를 새 모듈로 정식 이식 후 전부 삭제 | 범위 확대(Phase 5·6.5 선취, D-0021 §3 "하지 않는 것" 취지와 충돌) | 모듈 삭제 |

## Opus 권고: B
- ① 되돌리기 쉬움(파일 이동). ② 19 §6 Phase 3 행의 삭제 취지는 "영상을 만드는 옛 통로 제거"다. 자산 부트스트랩은 영상 통로가 아니다.
- ③ 실측: 이 컨테이너에서 자산 재생성에 prep3 people·flags·media3가 필요함을 확인(Phase 1 런북 3·4단계, phase2 run_log "Phase 1 자산 하드링크").
- A는 매 세션 수작업, C는 범위 확대라 B가 가장 좁다.

## 막히는 범위
- 막힘: D30 삭제 커밋만.
- 계속함: 이 컨테이너 자산 재생성(현 HEAD의 legacy_v3로 — 삭제 전이라 가능), D-0021 작업 2~9 전부.

## §7 해당 여부
없음(§7.1 금지 항목 아님). Fable 전결.
