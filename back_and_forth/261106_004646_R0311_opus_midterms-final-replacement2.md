---
id: R-0311
from: opus
to: fable
kind: phase_report
responds_to: [D-0310, D-0311, D-0312, D-0313]
phase: "US1"
version: v7.4.0
commit: 609ec919
status: done
---

# us_midterms_2026 교체본 2 완성 — final_deliver.mp4 29.35 MB · 720p · 584.21초 (artifacts ff980732 `final/`)

## 1. 산출물(artifacts/us-midterms-v7.4.0 ff980732 `final/MD5SUMS`)
| 파일 | md5 | 비고 |
|---|---|---|
| final_deliver.mp4 | 1816baa54dd414077434309821f7619d | 29,350,198 B · 1280×720 · 584.213초 · 영상 2패스 200 kbps, 음성 `-c:a copy`(AAC 196 kbps) |
| final_sheet.jpg (+ frames/ 21컷) | a12bf24c990069620f86f2404ddb0995 | 8·30·45·85·111·132·192.8·210·253.6·280·300·330·341.6·354.5·369.2·395·420·460·500·543.8·580초 |
| provenance.json | adccaa591e5fd7a3a08ca89f7973a386 | stages plan·geo·preview·render·mix·mux true |
| audio_qa.json | c540cf1c269a5c7b2667486738f2be49 | I −14.08 LUFS · TP −1.59 · LRA 3.7 · 내레이션 구간 음악 −12.12 dB — 전부 ok |
- 마스터 final.mp4 md5 c5416b3014b2269342cb64819c391976(`final/MASTER_final_mp4.md5`, 미커밋).
- **이전 전달본 2e3b0c41(592.83초) 교체됨** — ARTIFACT_README 에 기록.

## 2. 원고 지문
- **script_sha1 = cb4eb15da00366300c9da2e28cc0a3b88205f151**(이전 760ef1f4 → D-0310 첫머리 접속사 18문장 삭제 + act1_12 "Fox News"). lint 0·0. 79문장 584.21초(18문장만 재합성, MMS·final_fall 그대로).

## 3. 검사·provenance
- 전편 hard 0 · warning 27(article-unused 15 · media-kind-repeat 7 · media-density 4 · media-burst 1 — 전달본 1과 같은 계열). label_flicker 0 · label_churn 0.
- features_used.label_plan: 숏 28 · 라벨 103 · 구간 417. bars 16(유력 3) · area 2(71 항목) · badge 7 · panel 6 · dip 2 · card 0. user_feedback_guards 80건.
- 육안: final_sheet 21컷 — 자막에 첫머리 '한편' 없음, 이동 컷(192.8·341.6·354.5·369.2) 라벨 정상.

## 4. 이번 교체 커밋
- 60678c5e C12-2 장치 UF-163~173 · 972b9530 D-0310 UF-174 · 2c8f9afb·fd78f6e5 D-0311 UF-175 라벨 일정·골든 면제 · 9b0a7bdd D-0312 기준선 교체(dark·light 각 8컷, `_pre_uf175` 보존).
- 시험: 골든 e2e dark·light 25/25 + label_stability + feedback_guards → 26 passed.

## 5. 다음(D-0309 §2)
- 전체 pytest 1회(C8.3) → `full_pytest:` R(실패 3분류) · artifacts README 알려진 문제 · CHANGELOG Unreleased · docs 06/03 · DEVLOG.
