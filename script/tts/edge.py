"""edge-tts 백엔드 (v2.1.0, plan3 `edge_one`). 목소리·속도·음높이는 config.yaml tts 에서(15 P3).

v2.3.0: 목소리 교체 검증(D31)용으로 `voice` 인자를 받는다. None 이면 config `tts.edge_voice`.
v2.3.0(D34): `WordBoundary` 단어 경계를 받아 `{mp3}.align.json`(script/tts/align 공통 형식)을 함께 쓴다.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from orchestrator.config import load_config
from script.tts import align


def voice_label(voice: str | None = None) -> str:
    return f"edge-tts {voice or load_config().tts.edge_voice}"


async def edge_one(text: str, path: Path, voice: str | None = None) -> None:
    import edge_tts  # noqa: PLC0415 — 선택 의존성

    cfg = load_config().tts
    last: Exception | None = None
    for _ in range(4):
        try:
            com = edge_tts.Communicate(text, voice or cfg.edge_voice, rate=cfg.edge_rate, pitch=cfg.edge_pitch,
                                       boundary="WordBoundary")
            words: list[tuple[str, float, float]] = []
            with path.open("wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append((ch["text"], ch["offset"] / align.TICKS_PER_SEC, ch["duration"] / align.TICKS_PER_SEC))
            if os.path.getsize(path) > 1000:
                align.write(path, align.from_word_boundaries(text, words))
                return
        except Exception as e:  # noqa: BLE001 — 네트워크 재시도
            last = e
            print(f"edge retry {e}", flush=True)
            await asyncio.sleep(2)
    raise RuntimeError(f"edge-tts 실패: {path.name}: {last}")


def synth_all(jobs: list[tuple[str, Path]], concurrency: int = 5, voice: str | None = None) -> None:
    async def run() -> None:
        sem = asyncio.Semaphore(concurrency)

        async def one(t: str, p: Path) -> None:
            async with sem:
                await edge_one(t, p, voice)

        await asyncio.gather(*[one(t, p) for t, p in jobs])

    if jobs:
        asyncio.run(run())
