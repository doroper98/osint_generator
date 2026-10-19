<!--
tier: 3
last_synced_with: v7.4.0
ssot_for: [phaseV740-environment]
depends_on: [rules/video_rules.yaml, engine/typography.py, engine/style.py]
last_review: 2026-10-18
-->

# v7.4.0 렌더 컨테이너 환경 실측(D-0231 §4)

골든 e2e 25컷 md5 가 컨테이너마다 달라지는 원인 후보를 고정하기 위한 기록입니다.
diesel_road_2026 v2 전편과 골든 화소 비교를 이 환경에서 돌렸습니다.

## 1. 런타임·네이티브 라이브러리

| 항목 | 버전 |
|---|---|
| Python | 3.13.16 |
| 커널 | Linux 6.18.44 |
| cairo(라이브러리) | 1.18.0(libcairo2 1.18.0-3build1) |
| pycairo | 1.29.2 |
| pango | 1.52.1 |
| freetype | 2.13.2 |
| harfbuzz | 8.3.0 |
| fontconfig | 2.15.0 |
| FFmpeg | 6.1.1-3ubuntu5 |
| numpy | 2.5.3 |
| shapely | 2.2.0 |
| Pillow | 12.3.0 |
| pydantic | 2.13.5 |
| PyYAML | 6.0.1 |
| onnxruntime(Supertonic 3) | 1.29.0 |
| torch / torchaudio(MMS 정렬) | 2.14.1 / 2.11.0 |
| fontTools | 4.67.0 |

## 2. 글꼴(rules `fonts:` 해석 결과)

`~/.local/share/fonts/osint/` 의 파일입니다. md5 는 앞 12자리입니다.

| 규칙 키 | 해석된 파일 | md5 |
|---|---|---|
| sans | IBMPlexSansKR-Regular.ttf | 0d160d831c7f |
| sansm | IBMPlexSansKR-Medium.ttf | cae76922a0bf |
| sansb | IBMPlexSansKR-SemiBold.ttf | 6269dfe6ef4d |
| sansbb | IBMPlexSansKR-Bold.ttf | 9b6cbc413f72 |
| disp / dispm | GmarketSansBold.otf / GmarketSansMedium.otf | c0b5ec75cf4f / 77ceaa35dba9 |
| mono / monom | IBMPlexMono-SemiBold.ttf / IBMPlexMono-Medium.ttf | 4c2f3714b6a4 / 63c2dc54dd9c |
| serif | /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc | 시스템 패키지 |

## 3. 남은 과제

- 골든 기준선 md5 를 다시 맞추려면 위 표의 cairo·pango·freetype·harfbuzz 조합과 타일 캐시를 같이 고정해야 합니다.
- 이번 트랙에서는 기준선을 바꾸지 않았습니다(D-0231 §3). 대체 확인은 main 워크트리 대 브랜치 화소 비교입니다.
