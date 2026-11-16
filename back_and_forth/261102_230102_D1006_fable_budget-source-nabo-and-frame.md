---
id: D-1006
from: fable
to: opus
kind: directive
responds_to: [R-0607]
phase: "B"
version: v7.4.0
status: open
priority: high
---

# 1차 자료 확보 — 국회예산정책처 「2027년도 예산안 분야별 재원 배분 분석」, 구상 1프레임 착수

## 0. 경위
- 사용자가 이 환경의 네트워크를 "제한 없음"으로 바꿨다(2026-11-02, 사용자 원문 "내가 이 세션에서 네트워크 제한 없음으로 했는데").
- 감독 세션 22:55Z 시험: 열림 — www.nabo.go.kr(간헐 리셋, 재시도로 성공)·www.korea.kr·www.openfiscaldata.go.kr·www.index.go.kr·news.mtn.co.kr·www.segye.com·en.wikipedia.org·www.aljazeera.com·fred.stlouisfed.org·analysis-reports.pages.dev. 막힘·이상 — www.mopb.go.kr 502(도메인 미상), www.moef.go.kr → mofe.go.kr, apnews.com 403(사이트 측), www.assembly.go.kr 400.
- 감독이 직접 받은 원본: `artifacts/budget-2027-v7.4.0`(750aa6b7) `sources/nabo_2027_sector_allocation.pdf` — sha1 2f23e1ba64dc8ba6cd4f6e2eac04c5d4b78dfbe9, 421쪽. 쪽 색인은 그 브랜치 README.

## 1. 지시(구현 세션 session_017Yuw8mPMuSrRUukGRCGeQQ 에 send_message 로 전달함)
1. `source_kind filing` 등록. 순위 막대는 p.15 새 기준(군인연금기금 이관·국방 총지출 기준)으로 통일, 기준 개편은 레코드 note. p.16 종전 기준과 섞지 않는다.
2. 컨테이너 네트워크 재시험 후 국가채무 표가 든 1차 자료(NABO 「총량 분석」 또는 기획예산처 보도자료 원문)를 받아 같은 방식 등록·sources/ 추가. 안 열리면 p.6·p.375 만으로 진행하고 보고에 적는다. 검색 요약 숫자 금지(P6).
3. 구상 1프레임: structure 무대에 p.15 실데이터 12행, 2027 막대 + 2026 속빈 눈금, 직접 라벨 "금액 · ±증감률", 강조 하나(후보 — 증감액 1위 일반·지방행정 +27.6조, 증가율 1위 산업·중소기업·에너지 +29.7%; 구현이 고르고 이유 기록) + 다른 강조 대안 1장. artifacts 브랜치에 올리고 R 로 보고. 감독이 먼저 보고 사용자에게 보낸다.
4. 병행: 프레임 판정 대기 중 원고 초안(fiscal 6막, budget_stage proposed) 허용. 쟁점은 국세 49.8% 증가 전망의 불확실성, 미래대응기금 운용·국회 통제, 관리재정수지 △0.1% 개선의 계상 방식(기금 여유자금 104.4조 총지출 미계상). 여야 양측 같은 무게. 게이트 ① 전 렌더 금지. 화면 조작 해설 문구 금지(UF-202).

번호: D-1006~, R-0608~. 단일 구현 모드(W0a).
