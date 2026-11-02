# 구상 1프레임 — 구성 무대(structure) · 2027 정부안 12대 분야 (D-1006 §3)

- 코드 커밋: `claude/budget-2027-video` 816a80c7 · 프로젝트 `projects/budget_2027_frame` · `python -m engine.render projects/budget_2027_frame --preview 5.6,10.5`
- 데이터: 국회예산정책처 「2027년도 예산안 분야별 재원 배분 분석」 p.15 표(새 기준) — `data/categorical/BUDGET_2027_PROPOSED_SECTORS`·`BUDGET_2026_ENACTED_SECTORS`, 원본 sha1 2f23e1ba… 대조 통과(provenance structure.records[].raw_checked true)
- 증감률 라벨 = 원문 표 값(반올림 값으로 다시 계산하면 문화 20.8 — 원문 20.4)

| 파일 | 강조 | 자막(1프레임 전용 문장) |
|---|---|---|
| frame_main_admin.png (5.60초) | 일반·지방행정(증감액 1위 +27.6조) — **주** | 정부안에서 가장 많이 늘어나는 분야는 일반·지방행정으로, 27조 6천억 원이 늘어납니다. |
| frame_alt_industry.png (10.50초) | 산업·중소기업·에너지(증가율 1위 +29.7%) — 대안 | 증가율이 가장 높은 분야는 산업·중소기업·에너지로, 29.7% 늘어납니다. |

- 배경 사진 없음(무대 바탕) — 본편에서 권리 기록 있는 사진을 고른다. 이 프로젝트의 hard 3건(bgm·타이틀 카드 템플릿 표시·매체 밀도)은 장면 하나짜리 구상 프로젝트라서다.
- 실데이터에 감소 분야가 없어 손실 A 면은 이 장면에 나오지 않는다(시험 픽스처로는 확인됨).
