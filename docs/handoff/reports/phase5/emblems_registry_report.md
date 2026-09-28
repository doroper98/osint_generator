<!--
tier: 3
last_synced_with: v2.4.0
ssot_for: []
depends_on: [assets/emblems/registry.json, schemas/emblem_models.py]
last_review: 2026-09-28
-->

# 휘장 레지스트리 보고 (Phase 5, v2.4.0, back_and_forth D-0029 작업 3·9)

규칙(D5, README §7.2 — Fable 전결): 위키미디어 `Restrictions`가 하나라도 있으면 코드가 `flag_fallback`으로 확정한다.
라이선스 불허(CC BY-SA 등)·파일 없음도 `flag_fallback`. `user_decision` 상태는 없다. 파일의 decision 이 규칙과 다르면 로드 오류
(`schemas/emblem_models.py EmblemEntry._decision_matches_rule`) — 손으로 `use` 로 바꿔 우회할 수 없다.

수집: `python tools/commons_fetch.py emblems`(2026-09-28 KST, Commons API). 제목은 search 로 확인한 **기관 공식본**이다.
제한 태그가 없는 변형본(예: `Seal of the Central Intelligence Agency (B&W).svg`)으로 우회하지 않았다.
`flag_fallback` 기관은 휘장 파일을 **받지 않는다**(프로젝트 `assets/emblems/`에 없음).

| id | 기관 | Commons 파일 | 라이선스 | Restrictions | decision | reason | 대체 국기 |
|---|---|---|---|---|---|---|---|
| navcent | 미 해군 중부사령부 | File:United States Naval Forces Central Command patch 2014.png | Public domain | — | **use** | no_restrictions | us |
| centcom | 미 중부사령부 | File:Seal of United States Central Command.svg | Public domain | — | **use** | no_restrictions | us |
| irgc | 혁명수비대 | File:Seal of the Army of the Guardians of the Islamic Revolution.svg | Public domain | insignia | **flag_fallback** | restrictions: insignia | ir |
| rok_navy | 한국 해군 | File:Emblem of the Republic of Korea Navy.svg | South Korea-Gov | insignia, trademarked | **flag_fallback** | restrictions: insignia, trademarked | kr |
| mnd_korea | 국방부 | File:Emblem of the Ministry of National Defense (South Korea).svg | Public domain | insignia, trademarked | **flag_fallback** | restrictions: insignia, trademarked | kr |
| cheonghae | 청해부대 | — | — | — | **flag_fallback** | no_emblem_file | kr |
| cia | CIA | File:Seal of the U.S. Central Intelligence Agency.svg | Public domain | insignia | **flag_fallback** | restrictions: insignia | us |
| potus | 백악관 | File:Seal of the President of the United States.svg | Public domain | insignia | **flag_fallback** | restrictions: insignia | us |

요약: use 2(navcent, centcom), flag_fallback 6(irgc, rok_navy, mnd_korea, cheonghae, cia, potus).

## 렌더 경로
- `engine/layers/badges.py resolve_kind`: `kind=emblem` 뱃지가 `flag_fallback`이면 국기 뱃지(`flag11:<대체 국기>`)로 그린다. 위치·크기·알파는 그대로.
- `engine/project.py preflight`: `flag_fallback` 휘장은 휘장 이미지 키를 만들지 않는다 → 파일이 로드될 경로가 없다.
- provenance `assets.emblems.{used, flag_fallback}`, `assets.images_used`로 실제 사용을 증명한다.
- hormuz 는 `navcent`(use) 하나만 쓴다 — 뱃지 픽셀 무변경.
