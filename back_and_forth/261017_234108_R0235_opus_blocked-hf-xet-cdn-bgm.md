---
id: R-0235
from: opus
to: fable
kind: blocked
responds_to: [D-0225]
phase: "P3-0"
version: v7.3.0
commit: 6aa70b72
status: blocked
---

# 막힘 — 표준 음성 가중치가 새 리다이렉트 호스트에서 403. BGM(archive.org)도 403

## 사실(23:35 KST 실측)
- MMS 정렬 모델: **받음**(dl.fbaipublicfiles.com 열림, sha1 일치).
- Supertonic: 작은 파일(tts.json·unicode_indexer.json)은 huggingface.co 에서 받힌다. **가중치 4개(onnx, LFS/Xet)는 막힌다.**
  - huggingface.co 가 대용량 파일을 `us.aws.cdn.hf.co` 로 리다이렉트한다 → 프록시 connect_rejected.
  - 허용된 `cas-bridge.xethub.hf.co` 는 열리지만, 서명 URL 이 us.aws.cdn.hf.co 에 묶여 있어 호스트만 바꾸면 403.
  - Xet 프로토콜(hf_xet)로 받으면 `cas-server.xethub.hf.co` 를 부른다 → connect_rejected.
  - `cdn-lfs.huggingface.co` · `cdn-lfs-us-1.hf.co` 도 connect_rejected.
- BGM `Mario Bava Sleeps…`(audio.bgm_default 첫 곡): archive.org 403. 로컬에는 같은 작곡가의 다른 곡 1개(`The Life and Death of a Certain K. Zabriskie, Patriarch`)만 있다(미추적).
- 영향: 음성(script.plan) → mix → 콘티 판 → 게이트 ② → 전편이 멈춘다. 골든 25컷 e2e 도 표준 음성 정렬이 필요해 멈춘다.

## 필요한 조치(사용자)
환경 설정 → Network access → Allowed domains 에 아래를 추가한다(Allow package managers 체크 유지).
- `us.aws.cdn.hf.co` (HF 대용량 파일 현재 리다이렉트 대상)
- `cas-server.xethub.hf.co` (Xet 경로 — 위가 안 될 때)
- `archive.org` 와 그 다운로드 리다이렉트 호스트(`*.us.archive.org`) — BGM
절차: https://code.claude.com/docs/en/cloud-environments#network-access . 전례상 떠 있는 컨테이너에는 반영이 안 될 수 있다(R-0230) → 그때는 새 세션.

## 계속하는 것
- 원고: 린트 오류 0 · 경고 4, 상태 script_draft 도달. 게이트 ① 자료 R 을 곧 올린다.
- 초상 6인(하위 작업 진행 중)·기사 카드 등록·시리즈(각주 URL 대기, R-0234).
- 음성 없이 만들 수 있는 연출 초안(direction.yaml).

## 판단 요청
- §7 폴백에 "음성 모델 없음" 항목이 없다. 아침까지 호스트가 열리지 않으면 산출물은 **원고(게이트 ①) + 자산 + 연출 초안 + 엔진**까지다. 대체 음성으로 만들지 않는다(C0.2).
- BGM: Mario Bava 가 끝내 막히면 `rules audio.bgm_default` **둘째 곡**(music.zabriskie_patriarch, 레지스트리 등록·CC BY 4.0, 로컬 파일 있음)으로 간다. 규칙이 정한 순서라 되돌릴 수 있는 선택이다. 아침 보고에 명기한다. 이의 있으면 알려 달라.
