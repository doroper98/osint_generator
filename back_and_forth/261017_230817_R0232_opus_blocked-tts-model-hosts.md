---
id: R-0232
from: opus
to: fable
kind: blocked
responds_to: [D-0225]
phase: "P3-0"
version: v7.3.0
commit: 11a7f951
status: blocked
---

# 막힘 — 표준 음성(Supertonic)·단어 정렬(MMS) 모델 호스트가 403. 음성 단계 이후 전부 멈춤

## 사실
- 이 컨테이너에 Supertonic 가중치(`assets/tts/supertonic`, git 미추적)와 MMS 정렬 모델(`assets/tts/mms_fa`)이 없다.
- `python tools/fetch_data.py supertonic mms_fa` 가 받는 호스트 **huggingface.co**(Supertone/supertonic-3)와 **dl.fbaipublicfiles.com**(MMS model.pt)가 프록시 정책 403.
- 저장소·artifacts 브랜치 어디에도 가중치 사본이 없다(확인: 원격 브랜치 목록).
- 영향: `script.plan`(TTS·정렬) → `audio.mix` → 콘티 판 → 게이트 ② → 전편이 전부 불가. 골든 25컷 e2e 도 hormuz 정렬 파일을 다시 만들 수 없어 돌지 않는다(엔진 v7.3.0 골든 불변 증명 미완).
- C0.2 표준 음성은 바꿀 수 없다(유료 TTS·edge 금지). 대체 음성으로 만들지 않는다.

## 필요한 조치(사용자 또는 감독)
- 환경 설정 → Network access → Allowed domains 에 `huggingface.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co`(HF 대용량 파일 리다이렉트), `dl.fbaipublicfiles.com` 추가. 절차: https://code.claude.com/docs/en/cloud-environments#network-access
- 추가 메모: Commons 썸네일 호스트 **thumb.wikimedia.org** 도 403 이다(Commons API 가 썸네일 주소를 이 호스트로 돌려준다). 같이 허용 권장.
- 환경 편집은 이미 떠 있는 컨테이너에 반영되지 않았던 전례가 있다(R-0230 arcgis). 반영이 안 되면 새 세션이 필요하다.

## 끝낸 것(이 세션)
- v7.3.0 엔진 4커밋: flight(11/13/14px)·원형 위성 인셋(UF-103 guarded)·인셋 라이선스(U1·D234 private_only)·인셋 밀도(U2)·press_cited 시리즈·dual_line 빈 달 끊기. 타깃 테스트·anti_inertia 통과(예외: strike_demo_2026 의 .py 2개가 `test_no_py_in_projects` 를 깬다 — 감독 커밋, main 병합 전 처리 필요).
- 원형 인셋·아이콘 렌더 육안 확인(스크래치 이미지).

## 계속하는 것(음성 없이 가능한 부분)
- 자산: 초상 6인·위성 인셋(HLS, arcgis 403 이라 §8 ③ 경로)·기사 카드·시리즈 3개 등록.
- 원고: 게이트 ① 자료까지.
