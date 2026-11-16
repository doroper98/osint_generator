---
id: R-0606
from: opus
to: fable
kind: decision_request
responds_to: [D-1003]
phase: "B"
version: v7.4.0
commit: cd88ba3b
status: open
priority: urgent
---

# 결정 요청 — 예산안 1차 출처를 받을 길(사용자 몫)

## 상황
- 재정 1차 출처 호스트가 이 컨테이너에서 모두 막혔습니다(R-0605 표). 기획예산처·국회예산정책처·열린재정·국회 전부입니다.
- 웹 검색 요약에는 12대 분야 표 전체가 없습니다. 요약끼리 숫자도 어긋납니다.
- 그래서 구상 1프레임에 쓸 실데이터를 만들 수 없습니다(P6, D-1003 §1).

## 선택지
- **A(권고) — 사용자 PDF 업로드.** 기획예산처 「2027년도 예산안」 개요(12대 분야별 재원배분 표, 총수입·총지출·관리재정수지·국가채무 표)와 국회예산정책처 「2027년도 예산안 분석」(총괄)입니다. 파일은 `source_kind filing` 로 등록합니다(sha1·페이지·표 줄).
- B — 환경 허용 목록에 호스트 추가(www.mopb.go.kr, www.nabo.go.kr, www.openfiscaldata.go.kr, www.korea.kr, news.mtn.co.kr, www.segye.com) 뒤 새 세션에서 재착수. 설정 경로는 환경 메뉴 → Edit → Network access 입니다(https://code.claude.com/docs/en/cloud-environments#network-access).
- A 를 권하는 이유: 지금 세션의 환경 복원·엔진 작업을 버리지 않습니다. 쟁점 보도(양측 기사)는 업로드가 어려우면 B 를 같이 하셔도 됩니다.

## 기다리는 동안
- `genres/fiscal.yaml` 과 무대 `structure` 엔진을 시험 픽스처로 만듭니다. 픽스처 숫자는 화면에 내지 않습니다.
