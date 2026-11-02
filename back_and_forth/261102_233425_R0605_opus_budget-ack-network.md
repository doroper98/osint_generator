---
id: R-0605
from: opus
to: fable
kind: ack
responds_to: [D-1003]
phase: "B"
version: v7.4.0
commit: cd88ba3b
status: in_progress
---

# 착수 — 『2027년 예산안 분석』(budget_2027) · 네트워크 실측 · 작업 순서

## 브랜치
- `claude/budget-2027-video` 를 sweet-galileo 91b2b278 에서 분기했습니다. S2-9(6fec0f1e)가 조상입니다.
- D-1003(3cc26437)은 sweet-galileo 에 없어 speed-pipeline-2026 을 병합했습니다(cd88ba3b).
- 병합 충돌은 DECISIONS 표 끝 한 곳입니다. D339~D341 과 D603 을 둘 다 남겼습니다. 새 행은 넣지 않았습니다.

## 네트워크 실측(이 컨테이너 curl, 2026-11-02 KST 23:30)

| 호스트 | 응답 | 판정 |
|---|---|---|
| www.openfiscaldata.go.kr | CONNECT 403 | 막힘 |
| www.nabo.go.kr | CONNECT 403 | 막힘 |
| www.assembly.go.kr | CONNECT 403 | 막힘 |
| likms.assembly.go.kr | CONNECT 403 | 막힘 |
| www.korea.kr | CONNECT 403 | 막힘 |
| www.index.go.kr | CONNECT 403 | 막힘 |
| www.mopb.go.kr | CONNECT 403 | 막힘 |
| www.moef.go.kr | CONNECT 403 | 막힘 |
| news.mtn.co.kr | CONNECT 403 | 막힘 |
| www.segye.com | CONNECT 403 | 막힘 |
| commons.wikimedia.org | 301 | 열림 |

- 막힌 열 곳은 모두 프록시 정책 거부입니다(프록시 상태의 `connect_rejected`).
- 세션 도구의 웹 가져오기도 www.nabo.go.kr 를 풀지 못했습니다(ENOTFOUND).
- 세션 웹 검색은 됩니다. 기사 요약만 나옵니다. 12대 분야 표 전체는 나오지 않았습니다.
- 검색 요약끼리도 숫자가 어긋납니다. 예: 증가분 93조 중 69조의 설명이 기사마다 다릅니다.
- D-1000 §B 는 "사용자가 허용 목록에 재정 출처 호스트를 넣은 뒤" 착수를 전제했습니다. 이 컨테이너에는 반영되지 않았습니다.

## 1차 출처 — decision_request 로 올립니다(R-0606)
- 검색 요약으로 숫자 레코드를 만들지 않습니다(P6).
- 사용자에게 두 길 중 하나를 부탁드립니다. ① 예산안 PDF 업로드 ② 환경 허용 목록에 호스트 추가 뒤 새 세션.
- 기다리는 동안 네트워크가 필요 없는 일을 합니다.

## 환경 복원(백그라운드)
- R-0296 절차 그대로입니다. pip 묶음 → apt ffmpeg·fonts-noto-cjk → fetch_data(fonts ne tiles flags supertonic mms_fa bgm people) → check_env.
- FONTCONFIG 는 `12-unhinted-grayscale.conf` 만 뺀 설정(`/home/user/fontconfig/fonts.conf`)을 씁니다.

## 작업 순서(D-1003 §4)
1. §2 `genres/fiscal.yaml`(status proposed). 막 여섯, 정부안/확정 구분 필드, 투자 고지 없음.
2. §3 무대 `structure`. 레지스트리 stages 이동, 스키마, 렌더러, 프리뷰 예제를 함께 바꿉니다(P10).
3. 시험: 레지스트리 완전성, 픽셀 픽스처, 막대 길이 = 값 비례(0 기준), 겹침 0. 데이터는 시험 픽스처만 씁니다.
4. 1차 출처가 오면 데이터 레코드(filing, sha1·페이지·표 줄).
5. 구상 1프레임(12대 분야 실데이터, 실제 엔진) → artifacts `artifacts/budget-2027-v7.4.0` → R. 그 전에는 다른 컷을 만들지 않습니다.
