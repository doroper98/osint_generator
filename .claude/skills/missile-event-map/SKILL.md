---
name: missile-event-map
description: 북한 미사일 발사 사건의 화면 스케치(2D 지도 — EEZ·탐지 자산·발사·궤적·탄착 불확실성·고도 단면, 3D 지구본 전환)를 spec YAML 만 써서 만든다. "북한 미사일 발사", "탄착", "탐지 자산", "EEZ", "레이더 수평선" 영상 시안을 요청받았을 때 쓴다.
---

# missile-event-map — 미사일 발사 사건 화면 스케치

> **초안(S0, v5.7.0).** 절차 뼈대만 있다. CLI 는 S1(2D)·S2(3D) 에서 동작한다. 완성은 S4(D-0140 §8).
> 이 스킬은 코드를 담지 않는다. `python -m sketch.missile` 를 부르는 절차서다(D131).

## ① 쓰는 때 · 안 쓰는 때

- 쓴다: 발사 사건 하나를 사용자 검토용 화면 스케치(자막·내레이션 없음)로 보일 때.
- 쓰지 않는다: 본편 영상. 스케치는 엔진 레지스트리 밖이다(D128). 본편은 원고 → 콘티 → 본편 순서(CLAUDE.md C8.6).

## ② 수집할 사실 (출처 필수)

- 발사 지점·시각, 비행 거리·정점 고도·속도 — 합동참모본부 발표.
- 비행 시간·탄착 기준점 거리 — 일본 방위성 발표. 두 기관 값을 나란히 같은 무게로.
- EEZ 경계 — Marine Regions(VLIZ, CC BY 4.0).
- 탐지 자산 거리 — 공개 사양·보도. 위치 비공개 자산은 위치를 쓰지 않는다.
- 미사일 도해 — 권리가 분명한 Commons 도해(`tools/commons_fetch.py` UA·간격).

## ③ 프로젝트 폴더 준비

(S1 에서 채운다 — geo.yaml 티어, `python -m geo.prep`, `python -m sketch.missile.prep_eez`.)

## ④ spec 작성 규칙

(S1 에서 채운다 — approx 표시, 화면 숫자는 announced 값만(SK-H1), 탄착은 영역(SK-H2), 비공개 자산(SK-H3),
중첩 주장 두 색 사선(SK-H4), 독도·NLL 문구는 사용자 확정 항목.)

## ⑤ 실행

```bash
python -m sketch.missile projects/<pid> --check           # 검사만 — 종료 코드 ≠ 0 이면 고친다
python -m sketch.missile projects/<pid> --frames 5,27     # 정지 화면 확인
python -m sketch.missile projects/<pid> --res final       # 사용자 전달본(720p)
python -m sketch.missile projects/<pid> --globe --res final
```

## ⑥ 사용자 전달물

mp4 · 컨택트 시트 · `out/sketch_provenance.json` · 사용자 확정 대기 목록.

## ⑦ 금지 · 한계

- 화면 수치는 `rules/video_rules.yaml sketch:` 키로만 바꾼다. 스킬·spec 에 값을 복사하지 않는다(C0).
- 계산한 거리·시간을 화면에 쓰지 않는다. 발표값만.
- 본편 요소가 아니다. 등록 전 요소(arc·occupied·arrow 이벤트, globe 무대)는 S4 보고의 후보 목록에만 있다.
