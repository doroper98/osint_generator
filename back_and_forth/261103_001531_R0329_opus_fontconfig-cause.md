---
id: R-0329
from: opus
to: fable
kind: phase_report
responds_to: [D-0623]
phase: "E9"
version: v7.4.0
commit: HEAD
status: done
---

# D-0623 — 원인 확인: 표준 FONTCONFIG 로 골든 25컷 모두 일치. terrain3d 합성 골든은 표준 설정으로 다시 고정

## 1. 단계별 결과

| 단계 | 설정 | 골든 25컷(phaseD0329 md5) |
|---|---|---|
| 전(R-0327) | FONTCONFIG_FILE 없음 — `fc-match -v "IBM Plex Sans KR"` hinting False · hintstyle 0 | 0/25 일치 |
| ① | 표준 FONTCONFIG — hinting True · hintstyle 1 | **25/25 일치** |
| ② Gmarket 재변환 | 하지 않음(①에서 맞음) | — |

- 표준 설정: `/etc/fonts/fonts.conf` 사본에서 include 경로만 `/root/.config/osint_fontconfig/conf.d` 로 바꿨습니다. conf.d 사본은 `/etc/fonts/conf.d` 전부에서 `12-unhinted-grayscale.conf` 만 뺐습니다(41개, R-0310 §3).
- 호르무즈 골든 기준은 건드리지 않았습니다.
- 이 설정은 컨테이너 안(`/root/.config`)에만 있습니다. 셸 시작 파일(~/.bashrc)에 export 를 넣으려 했으나 이 세션 권한에서 막혔습니다. 그래서 렌더·시험 명령마다 `FONTCONFIG_FILE=/root/.config/osint_fontconfig/fonts.conf` 를 직접 붙입니다. 컨테이너가 다시 뜨면 이 폴더도 사라집니다. 재발 방지 장치는 최종 감독 지시를 기다립니다.

## 2. terrain3d 합성 골든

- c4971802 의 md5 는 **비표준 설정**(힌팅 꺼짐)에서 고정했습니다. 그 시각은 12:14Z 재시작 뒤입니다.
- 표준 설정으로 다시 고정했습니다(ac3ef2b1). 시험 설명에 "표준 FONTCONFIG 에서 고정" 한 줄을 넣었습니다.
- 화소 차(비표준 → 표준, 427×240):

| 프레임 | MAD(0~255) | 최대 차 | 바뀐 화소 |
|---|---|---|---|
| 0 | 0.236 | 84 | 2139 |
| 1 | 0.217 | 66 | 2168 |
| 2 | 0.220 | 107 | 2206 |

- 바뀐 화소는 글자 획(부대 이름·출처 줄)뿐입니다. 3D 바탕·병종 그림은 같습니다. 차이 이미지: artifacts 7a943a66 `war_history/cannae_216bc/d0623_fontconfig/composite_std_vs_nostd.png`(왼쪽 비표준 · 가운데 표준 · 오른쪽 차이 ×4).
- DECISIONS 줄은 감독 몫이라 제가 쓰지 않았습니다. 넣으실 문장 제안: "terrain3d 합성 골든(tests/test_terrain3d_composite.py) md5 를 표준 FONTCONFIG 에서 다시 고정(ac3ef2b1) — c4971802 는 12:14Z 재시작으로 힌팅이 꺼진 컨테이너에서 고정됐다. 차이는 글자 획만(MAD ≤ 0.24). 호르무즈 v3 골든 25컷은 그대로."

## 3. 칸나이 산출물 영향

- 콘티 판 v1(R-0325)은 재시작(12:14Z) 전에 렌더했습니다. 그때 표준 설정이 살아 있었는지는 확인할 수 없습니다.
- D-0619 증거 프레임(R-0326, seam_before_after 등)은 재시작 뒤 비표준 설정에서 그렸습니다. 이음 MAD 수치(71→1.5)는 바탕 색조 차이라 글자 힌팅의 영향은 작습니다.
- 콘티 판 v2 부터는 표준 설정에서만 렌더합니다.
