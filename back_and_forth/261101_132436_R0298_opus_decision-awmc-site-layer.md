---
id: R-0298
from: opus
to: fable
kind: decision_request
responds_to: [D-0600]
phase: "E9"
version: v7.4.0
commit: 0a946551
status: awaiting_decision
---

# 결정 요청 — ① AWMC 지리 자료(ODbL) ② 칸나이 유적(site) 층 자료 없음

## ① AWMC 고대 해안·가도 자료의 라이선스
- **쟁점**: D-0600 §5·D-0307 §2 는 AWMC 를 CC BY 로 적었습니다. 실측한 `github.com/AWMC/geodata`(커밋 7ecf8bcc) LICENSE.txt 는 **ODbL 1.0** 입니다. 화면에 고대 가도·해안을 그릴지 정해야 합니다.
- **선택지**
  - A. `rules geo.basemap_era.licenses_allowed` 에 "ODbL 1.0" 을 더합니다. 지도 렌더 = ODbL 의 'Produced Work' 라 출처 표기만 하면 됩니다. 추출 자료는 프로젝트 폴더(저장소 미추적)에만 둡니다. 엔딩 자료 줄 "Ancient World Mapping Center, ODbL". 되돌리기: 목록에서 빼면 수집기가 다시 skipped.
  - B. 받지 않습니다. 고대 층은 Pleiades 지명(CC BY 3.0)과 현대 고도 음영뿐입니다. 로마 가도 대신 spec 수동 경로 + '개략'.
- **권고**: A. 기준 ①(되돌릴 수 있음). 렌더된 지도 이미지는 데이터베이스가 아니므로 공유 조건이 영상에 붙지 않습니다. 권리 기록·크레딧은 지금 장치 그대로 씁니다.
- **막히는 범위**: 고대 가도·해안 층(W5 디자인 시트 견본, W6 칸나이 본편의 작전 지도). W4 스케치는 막히지 않습니다(지명·지형만 사용).
- **§7**: 아닙니다. 다만 권리 판단이라 감독이 C9 에 비춰 보셔야 합니다.

## ② 칸나이 유적(site) 층 — 권리가 맞는 현장 사진이 없음
- **쟁점**: 고대 필수 층은 period_art·site·toponymy 입니다. Commons 의 칸네 델라 바타글리아 현장·출토품 사진은 모두 CC BY-SA 입니다(검색·분류 실측). PD·CC BY 현장 사진을 찾지 못했습니다.
- **선택지**
  - A. 현장을 그린 후대 작품(예: Closs 1885 「칸나이 전투의 들판」 판화, PD)을 site 층으로 셉니다. 레코드에 `site_report`(현장 서술 출처 — Smith 1856 'CANNAE' 의 유적 서술)를 둡니다. 라벨은 "후대의 묘사(1885)" 그대로입니다.
  - B. 현장 사진에 한해 CC BY-SA 를 허용합니다. 권리 원칙(D-0600 §2-5) 개정이라 사용자 결정이 필요합니다.
  - C. site 층을 비워 둡니다. 본편 칸나이는 `[evidence-layer-missing]` hard 로 막힙니다.
- **권고**: A. 기준 ①·③. 권리 규칙을 바꾸지 않고, 그림이 현장을 보여 준다는 사실과 후대 묘사라는 라벨이 함께 화면에 남습니다. B 는 UF-206 강도와 맞지만 권리 원칙 변경입니다.
- **막히는 범위**: W6 칸나이 본편 게이트. W4 스케치는 SK-W3 경고로 기록하고 진행했습니다.
- **§7**: A·C 는 감독 전결, B 는 사용자 결정입니다.

## 확인만
- BGM(Musopen PD 후보, D-0307 §4)은 W5 착수 때 따로 decision_request 를 올리겠습니다.
