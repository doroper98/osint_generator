---
name: campaign-front-map
description: 전역(戰役)의 전황 작전도 화면 스케치(국가·제대별 부대 부호, 날짜별 전선, 진격 화살표, 포위망, 당시 지명)를 spec YAML 만 써서 만든다. "전황", "작전도", "전선", "제대 배치", "포위" 영상 시안을 요청받았을 때 쓴다.
---

# campaign-front-map — 전황 작전도 화면 스케치

> **초안(S0, v5.7.0).** 절차 뼈대만 있다. CLI 는 S3 에서 동작한다. 완성은 S4(D-0140 §8).
> 이 스킬은 코드를 담지 않는다. `python -m sketch.campaign` 을 부르는 절차서다(D131).

## ① 쓰는 때 · 안 쓰는 때

- 쓴다: 한 전역의 날짜별 전황을 사용자 검토용 화면 스케치(자막·내레이션 없음)로 보일 때.
- 쓰지 않는다: 본편 영상. 스케치는 엔진 레지스트리 밖이다(D128).

## ② 수집할 사실 (출처 필수)

- 날짜별 전선 — 권리가 분명한 참고 작전도(Commons SVG, 라이선스·저자 기록).
- 부대 배치(국가·제대·병종) — 참고 지도 2종 이상 대조. 위치는 개략임을 밝힌다.
- 당시 지명과 현재 이름.
- 수치(병력 등)는 사료마다 다르면 범위로.

## ③ 프로젝트 폴더 준비

(S3 에서 채운다 — geo.yaml 티어, `python -m geo.prep`, 참고 SVG + spec georef 블록 → `python -m sketch.campaign.prep_georef`.)

## ④ spec 작성 규칙

(S3 에서 채운다 — 제대 XXXX·XXX·XX, 병종 inf·arm·cav(SK-G3), 포위망 다각형 유효(SK-G2), 전선·부대 위치 개략 표기(SK-H5),
정합 잔차(SK-G1).)

## ⑤ 실행

```bash
python -m sketch.campaign projects/<pid> --check
python -m sketch.campaign projects/<pid> --frames 6,20
python -m sketch.campaign projects/<pid> --res final
```

## ⑥ 사용자 전달물

mp4 · 컨택트 시트 · `out/sketch_provenance.json` · 사용자 확정 대기 목록.

## ⑦ 금지 · 한계

- 화면 수치는 `rules/video_rules.yaml sketch:` 키로만 바꾼다(C0).
- 현대 국경·행정구역선·현대 지명을 당시 지도에 그리지 않는다.
- 본편 요소가 아니다. 등록 전 요소는 S4 보고의 후보 목록에만 있다.
