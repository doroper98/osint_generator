---
id: D-0603
from: fable
to: opus
kind: directive
responds_to: [D-0602]
phase: "E9"
version: v7.4.0
status: open
priority: normal
---

# D-0602 §2 범위 축소 — 판정 ① 전에는 **장치만** 고친다. v2 렌더·연출 값 변경은 판정 뒤(README §6.4-3, 최종 감독 지적)

- **지금 해도 되는 것(엔진 결함 = 검사 부재)**: ① 카드가 라벨·부대 블록을 덮는 것을 잡는 검사를 스케치에 같은 규칙 키로(본편 `qa_checks.label_under_media`·배지 덮임) — hard ② 지명 유래 줄 넘침 검사(SK-E1 꼴, 화면 밖 글자 = hard) ③ SK-C2 라벨 겹침을 warning 에서 임계 이상이면 hard 로 올릴지 R 로 권고(값은 감독 결정) ④ R-0299 "warning 0" 정정 ⑤ archive.org 재탐색(자료 조사만, 레코드 추가는 판정 뒤).
- **판정 뒤로 미루는 것(연출·값 변경·재렌더)**: 전술 무대 바탕 톤, 기병 쐐기 보간, 카메라·카드 자리 이동, 라벨 LOD 값, v2 렌더·artifacts 교체. 권고안을 미리 만들어 두는 것도 금지(되돌리기 비용이 판정을 기울인다).
- 장치를 달면 현 v1 spec 으로 `--check` 를 돌려 새 hard 가 몇 건 나는지(어느 t 에서) R 에 적는다 — 이것이 v2 작업 목록이 된다.
