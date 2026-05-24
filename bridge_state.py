from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from aiohttp import web


@dataclass
class BridgeRealtimeState:
    transcript_queue: asyncio.Queue[tuple[int, str]]
    ws_clients: set[web.WebSocketResponse] = field(default_factory=set)
    transcript_seq: int = 0
    translator_status: str = "disabled"
    translation_queue_size: int = 0
    last_error: str = ""
    first_pcm_mono: float | None = None
    stream_preload_sec: float = 0.0
    active_profile: str = ""
    crisp_status: str = "stopped"


async def broadcast_health(state: BridgeRealtimeState) -> None:
    state.translation_queue_size = state.transcript_queue.qsize()
    await broadcast_json(
        state.ws_clients,
        {
            "type": "health",
            "translator_status": state.translator_status,
            "translation_queue_size": state.translation_queue_size,
            "last_error": state.last_error,
            "active_profile": state.active_profile,
            "crisp_status": state.crisp_status,
        },
    )



async def broadcast_json(ws_clients: set[web.WebSocketResponse], obj: dict[str, object]) -> None:
    if not ws_clients:
        return
    line = json.dumps(obj, ensure_ascii=False)
    dead: list[web.WebSocketResponse] = []
    for ws in list(ws_clients):
        try:
            await ws.send_str(line)
        except Exception:  # noqa: BLE001
            dead.append(ws)
    for ws in dead:
        ws_clients.discard(ws)
