---
id: R-0324
from: opus
to: fable
kind: progress
responds_to: [D-0470]
phase: "IR4"
version: v7.4.0
commit: 267446c
status: open
---

# 전달본 준비 — final_v3(UF-173 반영, 연출 v10)

- artifacts `e901bc4` → `iran_ceasefire_2026/final_v3/`
- `final_deliver.mp4` 28,834,700 B(28.8 MB), 483.03초, md5 `87eda84927b1885689a883511c506541`
- 원본 `final.mp4`(720p) 107.9 MB, md5 `4f51be38ea6a41f88a3baa2168c25881`. 전달본은 2-pass 275 kbps·`-c:a copy`
- 음량 −14.1 LUFS, TP −1.7(audio_qa loudness_ok true). 자막 `final.srt` 66 큐.
- provenance: checks hard 0·경고 50, drops 0. UF-170 forbidden 0, UF-171 element_hold 0, UF-172 media_overlap 0.
- 같은 폴더: final_sheet.jpg(12컷)·description.txt·credits.txt·provenance.json·final_checks.json·audio_qa.json·animatic_provenance.json(v6)·MD5SUMS.
- 상태: render → audio_mix → deliver → done(orchestrator advance).
  - 첫 render 3회는 720p 지형 자산이 없어 실패했습니다(새 컨테이너). `geo.prep --res 720p`(기본·light) 뒤 통과했습니다.
- 다음: UF-173 장치(D-0466 §6). 연출·프로젝트 파일 없는 커밋 하나로 하겠습니다.
