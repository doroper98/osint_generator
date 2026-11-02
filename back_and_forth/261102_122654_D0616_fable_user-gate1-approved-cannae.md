---
id: D-0616
from: user
to: opus
kind: decision
responds_to: [R-0317, D-0612, D-0613, D-0615]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 결정(UF-254) — 칸나이 원고 v3.1 **게이트 ① 승인**. 표준 음성 → 연출 → 콘티 판으로

## 0. 사용자 원문(2026-11-02, 위임 감독 세션)
**"승인"** — 승인 대상: 칸나이 원고 v3.1 게이트 ① 자료(정정본, 문장 접미 라벨 제거판), `projects/cannae_216bc/script.yaml` sha256 1ded8d48…(a559737d 이후 무변경). 64문장·예상 476초.

## 1. 지금 할 것(순서)
1. **게이트 ① 승인 기록**: `python -m orchestrator.main approve --project cannae_216bc --gate script_approval --comment "사용자 승인(D-0616, UF-254 원문 '승인') — 원고 v3.1 sha256 1ded8d48"`. 승인 기록의 원고 지문이 지금 script.yaml 과 같은지 확인(다르면 멈추고 R).
2. **표준 음성**(C0.2, 재질문 금지): Supertonic 3 M3 ×0.95 + 문장 끝 시안 C + MMS 정렬. 발음 사전 점검(라틴·그리스 고유명사 — 아이밀리우스·세르빌리우스·하스드루발·마하르발·볼투르누스·베누시아·키살피나·폴리비오스·리비우스·마크로비우스·콰드리가리우스) — 이상하면 발음 텍스트만 고친다(자막·지문 불변, 지문이 바뀌면 게이트 ① 재요청).
3. **연출(direction)** — 감독 메모(D-0615 §3 + 장르 문법):
   - 주 무대 mercator **relief**, 이탈리아 작전 지도(한니발 진군) → 칸나이 확대(같은 좌표계).
   - **terrain3d 구간**: 배치(deployment) 막 후반 ~ 포위(encirclement) 막 — 90° 내려다보기로 들어가 부대 키프레임(forces 파일)으로 배치·초승달·양익 포위를 움직이고, 대형을 설명하는 문장(deployment_10~11 초승달, encirclement_6~8 포위)에서만 천천히 기울어 궤도. 장면 단위, 문장마다 회전 금지(C0).
   - 증거 카드: 셰켈 은화(당대)·타니트 비석(당대, "재현" 고지 문장과 같은 자리)·흉상(후대, 추정 표기)·트럼불 1773(후대)·클로스 1885 + Smith 현장 서술(후대) — 카드마다 미술사 한 문장, element_hold 6초·media_overlap·label_under_media 지킴.
   - 사료 인용 카드 2(폴리비오스 III.117 / 리비우스 XXII.51 마하르발 — 번역 자막 + 원문·저자·권·장 카드), 로마력 날짜 문장에 마크로비우스 출처 줄.
   - 사상자 문장: force 레코드 띠(ancient_range 라벨 "사료마다 다르다").
   - 날짜 뱃지: "기원전 216년 8월 2일(로마력)" 구간과 "기원전 218~216년" 구간.
   - 진영 범례·타니트 휘장, 로마 무휘장 사유는 provenance.
4. **믹스**: `python -m audio.mix` — BGM = Zabriskie(bgm_default 첫째, D-0613). 같은 구간(전투 절정 30초)의 **코리올란 서곡 발췌 믹스 견본**(wav 또는 mp4)을 따로 만든다(bed_gain 0.43 동일).
5. **콘티 판**: `python -m engine.render projects/cannae_216bc --animatic` → artifacts `war_history/cannae_216bc/animatic_v1/`(mp4 ≤30MB·시트·provenance·checks·코리올란 견본) → R. 감독이 사용자에게 보낸다(판정 자리 ③).

## 2. terrain3d 등록과의 관계(D-0608 §2 그대로)
- 음성·MMS·믹스는 지금 바로(terrain3d 와 무관). 연출 초안도 지금 쓴다.
- 콘티 판 렌더는 terrain3d 구간 등록이 끝난 뒤. 음성·연출이 준비됐는데 등록이 3시간 넘게 남으면 decision_request(① terrain3d 구간 없이 콘티 판 v1 먼저 ② 기다림) — 감독이 정한다.

## 3. 그대로
asset_library check 0(콘티 판 전, C8-7), 원장 open 장치(C12-2), PR·main 금지, 커밋 첫 줄 형식·즉시 push, 렌더는 run_in_background.
