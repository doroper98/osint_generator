"""인물별 codex `$imagegen` 프롬프트 세트를 생성한다 (Phase 2 — 2단계).

`prompts/portrait_cutout.md` 의 프롬프트 본문(첫 ``` 블록)을 **SSOT 로 읽어** 슬롯만
치환한다. 템플릿을 코드에 복사하지 않으므로 문서를 고치면 산출물이 따라 바뀐다.

사용::

    python assets/library/workshop/make_prompts.py            # 생성
    python assets/library/workshop/make_prompts.py --dry-run  # 대상만 확인

산출::

    output/{person_id}_mono_v01.prompt.txt   인물별 프롬프트 전문 (G4-10 기록 의무)
    output/RUN_BATCH.md                      사용자가 codex 에서 실행할 절차서
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REFS = HERE / "references"
MANIFEST = REFS / "photo_manifest.json"
TEMPLATE = HERE / "prompts" / "portrait_cutout.md"
OUT = HERE / "output"
ANCHOR = "style_anchor_portrait_v1.png"

#: 사용자 결정 2026-08-15 — 사진 문제로 이번 배치에서 제외.
#: 사진이 확보되면 `--adopt` 로 등록 후 본 스크립트를 다시 돌리면 된다.
EXCLUDED: dict[str, str] = {
    "kim_jong_un": "사진 미확보 (Commons 후보가 분장 배우 / 실제 인물은 restrictions 차단)",
    "lee_jae_yong": "저해상도 342x493 — 가공 시 얼굴 뭉개짐 우려",
    "rhee_chang_yong": "저해상도 510x800 — 가공 시 얼굴 뭉개짐 우려",
}


def load_template() -> str:
    """portrait_cutout.md 의 첫 코드펜스 블록을 프롬프트 본문으로 쓴다."""
    text = TEMPLATE.read_text(encoding="utf-8")
    m = re.search(r"^```\s*\n(.*?)^```\s*$", text, re.DOTALL | re.MULTILINE)
    if not m:
        raise SystemExit(f"error: {TEMPLATE} 에서 프롬프트 코드블록을 찾지 못했습니다.")
    body = m.group(1).strip()
    for slot in ("{person_name}", "{person_photo}"):
        if slot not in body:
            raise SystemExit(f"error: 템플릿에 {slot} 슬롯이 없습니다 — 템플릿 확인 필요.")
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"error: {MANIFEST} 없음 — 먼저 collect_portraits.py 를 실행하십시오.")
        return 1

    people = json.loads(MANIFEST.read_text(encoding="utf-8"))["people"]
    template = load_template()

    targets, skipped = [], []
    for pid, rec in sorted(people.items()):
        if pid in EXCLUDED:
            skipped.append((pid, rec, EXCLUDED[pid]))
            continue
        if not (REFS / rec["local_file"]).is_file():
            skipped.append((pid, rec, "사진 파일 없음"))
            continue
        targets.append((pid, rec))

    print(f"대상 {len(targets)}인 / 제외 {len(skipped)}인")
    for pid, rec, why in skipped:
        print(f"  - 제외 {pid:18} {why}")

    if args.dry_run:
        for pid, rec in targets:
            print(f"  + {pid:18} {rec['name_en']}")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for pid, rec in targets:
        body = (
            template
            .replace("{person_name}", rec["name_en"] or rec["name_ko"])
            .replace("{person_photo}", rec["local_file"])
        )
        header = (
            f"# {rec['name_ko']} ({rec['name_en']}) — {pid}\n"
            f"# 생성: make_prompts.py / 템플릿 SSOT: prompts/portrait_cutout.md\n"
            f"# 입력 사진: references/{rec['local_file']}  ({rec['license']})\n"
            f"# 출처: {rec['source_page'] or '-'}\n"
            f"# 저작자: {rec['artist'] or '-'}\n"
            f"# 산출 예정: output/{pid}_mono_v01.png\n\n"
        )
        dest = OUT / f"{pid}_mono_v01.prompt.txt"
        dest.write_text(header + body + "\n", encoding="utf-8")
        written.append((pid, rec, dest))
        print(f"  + {dest.name}")

    _write_batch_doc(written, skipped)
    print(f"\n[생성] {len(written)}건 → {OUT}")
    print(f"[절차서] {OUT / 'RUN_BATCH.md'}")
    return 0


def _write_batch_doc(written: list, skipped: list) -> None:
    lines: list[str] = [
        "# codex 이미지 배치 실행 절차 (Phase 2 — 인물 컷아웃)",
        "",
        f"대상 **{len(written)}인**. 산출물은 배경·섀도 없는 고대비 모노톤 인물이다",
        "(17 §1.7.0 방식 B — 섀도는 런타임 합성이라 굽지 않는다).",
        "",
        "## 사전 점검 (세션 1회)",
        "",
        "`/skills` 로 `imagegen` 노출 확인. 안 보이면 중단하고 보고 (workshop/AGENTS.md).",
        "",
        "## 인물별 실행",
        "",
        "각 인물마다 아래를 실행한다. `-i` 첨부 순서가 중요하다 —",
        "**1번이 스타일 앵커, 2번이 인물 사진**이며 프롬프트가 그 순서를 참조한다.",
        "",
        "```bash",
        "cd assets/library/workshop",
        "```",
        "",
    ]
    for pid, rec, dest in written:
        lines += [
            f"### {rec['name_ko']} ({pid})",
            "",
            "```bash",
            f"codex -i \"references/{ANCHOR}\" \\",
            f"      -i \"references/{rec['local_file']}\"",
            "```",
            f"→ 프롬프트: `output/{dest.name}` 의 내용을 붙여넣는다.",
            f"→ 산출물을 `output/{pid}_mono_v01.png` 로 저장.",
            "",
        ]

    lines += [
        "## 검수 (프롬프트 파일 하단 기준 4항)",
        "",
        "1. **얼굴이 그 사람인가** — 원본 사진과 대조. 닮은 딴사람이면 반려 (G4).",
        "2. **프로 인쇄물로 보이는가** — \"이목구비 식별 가능\" 수준은 불합격.",
        "3. **오려낼 수 있는가** — 인물 경계가 흰 배경과 뚜렷이 분리되는가.",
        "4. **금지 요소 없는가** — 섀도·종이 질감·텍스트·컬러가 하나라도 있으면 반려.",
        "",
        "## 이번 배치에서 제외된 인물",
        "",
        "| 인물 | 사유 |",
        "|---|---|",
    ]
    for pid, rec, why in skipped:
        lines.append(f"| {rec['name_ko']} (`{pid}`) | {why} |")
    lines += [
        "",
        "사진이 확보되면 `collect_portraits.py --adopt` 로 등록 후",
        "`make_prompts.py` 를 다시 돌리면 프롬프트가 추가 생성된다.",
        "",
    ]
    (OUT / "RUN_BATCH.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
