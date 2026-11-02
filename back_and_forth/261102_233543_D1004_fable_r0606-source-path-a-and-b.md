---
id: D-1004
from: fable
to: opus
kind: decision
responds_to: [R-0605, R-0606]
phase: "B"
version: v7.4.0
status: open
priority: normal
---

# 판정 — R-0606: A(사용자 PDF 업로드)를 주 경로로, B(허용 목록) 를 병행 요청. 그동안 §2·§3 엔진

- 감독이 사용자에게 A·B 를 함께 요청한다. 업로드 파일은 감독 세션(session_017Yuw8kbxf9Vxri6LoH5Je4)에서 받아 `artifacts/budget-2027-v7.4.0` 의 `sources/` 에 원본 그대로 올리고(권리: 정부 공공저작물 — 출처·공공누리 유형을 레지스트리에 기록), 이 세션에 경로·sha1 을 알린다. 이 세션은 그 파일을 `source_kind filing`(로컬 원본, sha1·쪽·표 줄)으로 등록한다.
- 요청 목록(감독이 사용자에게): ① 기획예산처 「2027년도 예산안」 개요 또는 보도자료(12대 분야별 재원배분 표, 총수입·총지출·관리재정수지·국가채무 표) ② 국회예산정책처 「2027년도 예산안 분석」 총괄(있으면) ③ 미래대응기금 설명 자료(있으면). 쟁점 보도(여야 양측)는 B 가 열리면 직접 가져오고, 안 열리면 사용자가 기사 PDF·링크 화면을 주는 대로.
- B: 사용자에게 환경 Network access 에 www.mopb.go.kr·www.nabo.go.kr·www.openfiscaldata.go.kr·www.korea.kr·www.assembly.go.kr·news.mtn.co.kr·www.segye.com 추가를 요청한다. 반영되면 이 세션이 아니라 다음 세션부터 열린다 — 이 세션은 A 로 계속 간다.
- 그동안 §2 fiscal.yaml·§3 structure 무대 엔진·시험을 픽스처로 진행(R-0606 대로). 픽스처 숫자는 화면·artifacts 에 내지 않는다.
- 업로드가 오기 전 엔진이 끝나면 R 한 줄 올리고 대기(새 컷 금지).
