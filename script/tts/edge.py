"""edge-tts 백엔드 (v2.1.0, plan3 `edge_one`). 목소리·속도·음높이는 config.yaml tts 에서(15 P3)."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from orchestrator.config import load_config


def voice_label() -> str:
    return f"edge-tts {load_config().tts.edge_voice}"


async def edge_one(text: str, path: Path) -> None:
    import edge_tts  # noqa: PLC0415 — 선택 의존성

    cfg = load_config().tts
    last: Exception | None = None
    for _ in range(4):
        try:
            await edge_tts.Communicate(text, cfg.edge_voice, rate=cfg.edge_rate, pitch=cfg.edge_pitch).save(str(path))
            if os.path.getsize(path) > 1000:
                return
        except Exception as e:  # noqa: BLE001 — 네트워크 재시도
            last = e
            print(f"edge retry {e}", flush=True)
            await asyncio.sleep(2)
    raise RuntimeError(f"edge-tts 실패: {path.name}: {last}")


def synth_all(jobs: list[tuple[str, Path]], concurrency: int = 5) -> None:
    async def run() -> None:
        sem = asyncio.Semaphore(concurrency)

        async def one(t: str, p: Path) -> None:
            async with sem:
                await edge_one(t, p)

        await asyncio.gather(*[one(t, p) for t, p in jobs])

    if jobs:
        asyncio.run(run())
