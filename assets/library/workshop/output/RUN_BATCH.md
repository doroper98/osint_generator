# codex 이미지 배치 실행 절차 (Phase 2 — 인물 컷아웃)

대상 **24인**. 산출물은 배경·섀도 없는 고대비 모노톤 인물이다
(17 §1.7.0 방식 B — 섀도는 런타임 합성이라 굽지 않는다).

## 사전 점검 (세션 1회)

`/skills` 로 `imagegen` 노출 확인. 안 보이면 중단하고 보고 (workshop/AGENTS.md).

## 인물별 실행

각 인물마다 아래를 실행한다. `-i` 첨부 순서가 중요하다 —
**1번이 스타일 앵커, 2번이 인물 사진**이며 프롬프트가 그 순서를 참조한다.

```bash
cd assets/library/workshop
```

### 샘 올트먼 (altman)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_altman.jpg"
```
→ 프롬프트: `output/altman_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/altman_mono_v01.png` 로 저장.

### 오드리 탕 (audrey_tang)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_audrey_tang.jpg"
```
→ 프롬프트: `output/audrey_tang_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/audrey_tang_mono_v01.png` 로 저장.

### 제프 베이조스 (bezos)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_bezos.jpg"
```
→ 프롬프트: `output/bezos_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/bezos_mono_v01.png` 로 저장.

### 최태원 (chey_tae_won)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_chey_tae_won.jpg"
```
→ 프롬프트: `output/chey_tae_won_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/chey_tae_won_mono_v01.png` 로 저장.

### 커티스 야빈 (curtis_yarvin)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_curtis_yarvin.jpg"
```
→ 프롬프트: `output/curtis_yarvin_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/curtis_yarvin_mono_v01.png` 로 저장.

### 다리오 아모데이 (dario_amodei)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_dario_amodei.jpg"
```
→ 프롬프트: `output/dario_amodei_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/dario_amodei_mono_v01.png` 로 저장.

### 대런 애쓰모글루 (daron_acemoglu)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_daron_acemoglu.jpg"
```
→ 프롬프트: `output/daron_acemoglu_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/daron_acemoglu_mono_v01.png` 로 저장.

### Hélène Landemore (helene_landemore)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_helene_landemore.jpg"
```
→ 프롬프트: `output/helene_landemore_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/helene_landemore_mono_v01.png` 로 저장.

### 젠슨 황 (jensen_huang)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_jensen_huang.jpg"
```
→ 프롬프트: `output/jensen_huang_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/jensen_huang_mono_v01.png` 로 저장.

### 알리 하메네이 (khamenei)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_khamenei.jpg"
```
→ 프롬프트: `output/khamenei_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/khamenei_mono_v01.png` 로 저장.

### 크리스틴 라가르드 (lagarde)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_lagarde.jpg"
```
→ 프롬프트: `output/lagarde_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/lagarde_mono_v01.png` 로 저장.

### 에마뉘엘 마크롱 (macron)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_macron.jpg"
```
→ 프롬프트: `output/macron_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/macron_mono_v01.png` 로 저장.

### 마이클 샌델 (michael_sandel)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_michael_sandel.jpg"
```
→ 프롬프트: `output/michael_sandel_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/michael_sandel_mono_v01.png` 로 저장.

### 일론 머스크 (musk)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_musk.jpg"
```
→ 프롬프트: `output/musk_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/musk_mono_v01.png` 로 저장.

### 베냐민 네타냐후 (netanyahu)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_netanyahu.jpg"
```
→ 프롬프트: `output/netanyahu_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/netanyahu_mono_v01.png` 로 저장.

### 피터 틸 (peter_thiel)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_peter_thiel.jpg"
```
→ 프롬프트: `output/peter_thiel_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/peter_thiel_mono_v01.png` 로 저장.

### 제롬 파월 (powell)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_powell.jpg"
```
→ 프롬프트: `output/powell_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/powell_mono_v01.png` 로 저장.

### 블라디미르 푸틴 (putin)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_putin.jpg"
```
→ 프롬프트: `output/putin_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/putin_mono_v01.png` 로 저장.

### 팀 쿡 (tim_cook)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_tim_cook.jpg"
```
→ 프롬프트: `output/tim_cook_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/tim_cook_mono_v01.png` 로 저장.

### 도널드 트럼프 (trump)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_trump.jpg"
```
→ 프롬프트: `output/trump_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/trump_mono_v01.png` 로 저장.

### 케빈 워시 (warsh)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_warsh.jpg"
```
→ 프롬프트: `output/warsh_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/warsh_mono_v01.png` 로 저장.

### 시진핑 (xi_jinping)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_xi_jinping.jpg"
```
→ 프롬프트: `output/xi_jinping_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/xi_jinping_mono_v01.png` 로 저장.

### 볼로디미르 젤렌스키 (zelensky)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_zelensky.jpg"
```
→ 프롬프트: `output/zelensky_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/zelensky_mono_v01.png` 로 저장.

### 마크 저커버그 (zuckerberg)

```bash
codex -i "references/style_anchor_portrait_v1.png" \
      -i "references/photo_zuckerberg.jpg"
```
→ 프롬프트: `output/zuckerberg_mono_v01.prompt.txt` 의 내용을 붙여넣는다.
→ 산출물을 `output/zuckerberg_mono_v01.png` 로 저장.

## 검수 (프롬프트 파일 하단 기준 4항)

1. **얼굴이 그 사람인가** — 원본 사진과 대조. 닮은 딴사람이면 반려 (G4).
2. **프로 인쇄물로 보이는가** — "이목구비 식별 가능" 수준은 불합격.
3. **오려낼 수 있는가** — 인물 경계가 흰 배경과 뚜렷이 분리되는가.
4. **금지 요소 없는가** — 섀도·종이 질감·텍스트·컬러가 하나라도 있으면 반려.

## 이번 배치에서 제외된 인물

| 인물 | 사유 |
|---|---|
| 이재용 (`lee_jae_yong`) | 저해상도 342x493 — 가공 시 얼굴 뭉개짐 우려 |
| 이창용 (`rhee_chang_yong`) | 저해상도 510x800 — 가공 시 얼굴 뭉개짐 우려 |

사진이 확보되면 `collect_portraits.py --adopt` 로 등록 후
`make_prompts.py` 를 다시 돌리면 프롬프트가 추가 생성된다.
