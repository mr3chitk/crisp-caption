from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import deque
from collections.abc import Sequence
from urllib.parse import urlsplit, urlunsplit

import aiohttp
from aiohttp import web

from bridge_state import BridgeRealtimeState, broadcast_health, broadcast_json

logger = logging.getLogger(__name__)

def select_context_history(
    history: deque[tuple[str, str]],
    max_items: int,
) -> list[tuple[str, str]] | None:
    return list(history)[-max_items:] if max_items > 0 else None


def build_glossary_text(glossary: dict[str, str]) -> str:
    if not glossary:
        return ""
    lines = "\n".join(f"\"{k}\" is translated to \"{v}\"" for k, v in glossary.items())
    return f"GLOSSARY.\n\n{lines}"


def clean_translation_output(text: str) -> str:
    cleaned = text.strip()
    # cleaned = re.sub(r"</?\s*source\s*>", "", cleaned, flags=re.IGNORECASE)
    # cleaned = re.sub(r"</?\s*translation\s*>", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def build_translation_system_prompt(glossary: dict[str, str]) -> str:
    # HY-MT's model card recommends putting the actual translation instruction
    # in the user message and notes that the model has no default system prompt.
    del glossary  # keep the public signature stable for callers/config notes
    return ""


def build_user_message(
    text: str,
    glossary: dict[str, str],
    target_lang: str = "English",
    history: Sequence[tuple[str, str]] | None = None,
) -> str:
    context_blocks: list[str] = []

    # preprocess chars
    # text = text.replace("�","")

    if glossary:
        context_blocks.append(build_glossary_text(glossary))
    if history:
        history_lines = []
        for idx, (orig, trans) in enumerate(history, start=1):
            # history_lines.append(f"{idx}. Original:{orig}\n   Translated:{trans}")
            history_lines.append(f"{orig}")
        context_blocks.append("PREVIOUS CONTEXTS.\n\n" + "\n".join(history_lines))

    if context_blocks:
        context = "\n\n".join(context_blocks)
        return (
            f"{context}\n\n"
            f"Translate the following text into {target_lang} without any explanation.\n\n"
            f"{text}\n"
        )

    return (
        f"Translate the following text into {target_lang} without any explanation.\n\n"
        f"{text}\n"
    )


# Keys allowed inside --config JSON (flat); crisp_args is the base CrispASR argv (optional argv after `--` appends).
def load_merged_glossary(glossary_file: str | None) -> dict[str, str]:
    if not glossary_file or not str(glossary_file).strip():
        return {}
    g: dict[str, str] = {}
    pth = os.path.expanduser(glossary_file.strip())
    if not os.path.isfile(pth):
        logger.error("Glossary file not found: %s", pth)
        raise SystemExit(2)
    with open(pth, encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        logger.error("Glossary file must be a JSON object: %s", pth)
        raise SystemExit(2)
    for k, v in loaded.items():
        if isinstance(k, str) and isinstance(v, str):
            g[str(k)] = v
    return g


def resolve_translation_system_prompt(
    translate_prompt_file: str | None,
    glossary: dict[str, str],
) -> str:
    if translate_prompt_file and str(translate_prompt_file).strip():
        pth = os.path.expanduser(translate_prompt_file.strip())
        if not os.path.isfile(pth):
            logger.error("Translation prompt file not found: %s", pth)
            raise SystemExit(2)
        with open(pth, encoding="utf-8") as f:
            base = f.read().strip()
        return base
    return build_translation_system_prompt(glossary)


def translate_health_url(translate_url: str) -> str:
    parts = urlsplit(translate_url)
    return urlunsplit((parts.scheme or "http", parts.netloc, "/health", "", ""))


async def translator_health_monitor(
    state: BridgeRealtimeState,
    session: aiohttp.ClientSession,
    *,
    health_url: str,
    interval_sec: float = 3.0,
) -> None:
    while True:
        try:
            async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                body = await resp.text()
                if 200 <= resp.status < 300:
                    state.translator_status = "online"
                    if (
                        state.last_error.startswith("llama-server health check failed")
                        or state.last_error.startswith("llama-server loading model")
                    ):
                        state.last_error = ""
                else:
                    msg = ""
                    try:
                        data = json.loads(body) if body else {}
                        err = data.get("error", {}) if isinstance(data, dict) else {}
                        if isinstance(err, dict):
                            msg = str(err.get("message") or err.get("code") or "").strip()
                    except json.JSONDecodeError:
                        msg = body[:120].strip()

                    if resp.status == 503 and "loading" in msg.lower():
                        state.translator_status = "checking"
                        state.last_error = f"llama-server loading model: {msg or 'HTTP 503'}"
                    else:
                        state.translator_status = "offline"
                        detail = f": {msg}" if msg else ""
                        state.last_error = f"llama-server health check failed: HTTP {resp.status}{detail}"
        except asyncio.CancelledError:
            raise
        except aiohttp.ClientConnectorError as ex:
            state.translator_status = "offline"
            state.last_error = f"llama-server connection refused: {ex}"
        except asyncio.TimeoutError:
            state.translator_status = "offline"
            state.last_error = "llama-server health check timeout"
        except Exception as ex:  # noqa: BLE001
            state.translator_status = "offline"
            state.last_error = f"llama-server health check failed: {ex}"

        await broadcast_health(state)
        await asyncio.sleep(interval_sec)


async def translator_worker(
    transcript_queue: asyncio.Queue[tuple[int, str]],
    session: aiohttp.ClientSession,
    *,
    state: BridgeRealtimeState,
    translate_url: str,
    translate_model: str,
    translate_window: int,
    translate_temperature: float,
    translate_top_k: int,
    translate_top_p: float,
    translate_repeat_penalty: float,
    translate_max_tokens: int,
    system_prompt: str,
    glossary: dict[str, str],
    bearer: str | None,
    ws_clients: set[web.WebSocketResponse],
) -> None:
    context_items = translate_window
    history: deque[tuple[str, str]] = deque(maxlen=max(12, context_items * 4))
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    state.translator_status = "checking"
    state.translation_queue_size = transcript_queue.qsize()
    await broadcast_health(state)

    while True:
        seq, text = await transcript_queue.get()
        await broadcast_health(state)
        stripped = text.strip()
        if not stripped:
            transcript_queue.task_done()
            await broadcast_health(state)
            continue
        messages: list[dict[str, str]] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        context_history = select_context_history(history, context_items)
        messages.append({"role": "user", "content": build_user_message(stripped, glossary, history=context_history)})

        payload = {
            "model": translate_model,
            "messages": messages,
            "temperature": translate_temperature,
            "top_k": translate_top_k,
            "top_p": translate_top_p,
            "repeat_penalty": translate_repeat_penalty,
            # "dry_multiplier": 0.8,
            "max_tokens": translate_max_tokens,
            "stream": False,
        }
        try:
            async with session.post(
                translate_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                body = await resp.text()
                if resp.status >= 400:
                    short_err = (body[:240] if body else "") or resp.reason
                    msg = f"translate HTTP {resp.status}: {short_err}"
                    logger.warning("%s", msg)
                    state.translator_status = "error"
                    state.last_error = msg
                    await broadcast_json(
                        ws_clients,
                        {
                            "type": "translation_error",
                            "seq": seq,
                            "message": msg,
                        },
                    )
                    transcript_queue.task_done()
                    await broadcast_health(state)
                    continue
                try:
                    data = json.loads(body)
                    result = clean_translation_output(data["choices"][0]["message"]["content"] or "")
                except (json.JSONDecodeError, KeyError, IndexError, TypeError) as ex:
                    msg = f"translate parse error: {ex}"
                    logger.warning("%s body=%s", msg, body[:120])
                    state.translator_status = "error"
                    state.last_error = msg
                    await broadcast_json(
                        ws_clients,
                        {"type": "translation_error", "seq": seq, "message": msg},
                    )
                    transcript_queue.task_done()
                    await broadcast_health(state)
                    continue
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            msg = "translation timeout"
            logger.warning("%s", msg)
            state.translator_status = "offline"
            state.last_error = msg
            await broadcast_json(ws_clients, {"type": "translation_error", "seq": seq, "message": msg})
            transcript_queue.task_done()
            await broadcast_health(state)
            continue
        except aiohttp.ClientConnectorError as ex:
            msg = f"llama-server connection refused: {ex}"
            logger.warning("%s", msg)
            state.translator_status = "offline"
            state.last_error = msg
            await broadcast_json(ws_clients, {"type": "translation_error", "seq": seq, "message": msg})
            transcript_queue.task_done()
            await broadcast_health(state)
            continue
        except Exception as ex:  # noqa: BLE001
            msg = f"translate request failed: {ex}"
            logger.warning("%s", msg)
            state.translator_status = "error"
            state.last_error = msg
            await broadcast_json(ws_clients, {"type": "translation_error", "seq": seq, "message": msg})
            transcript_queue.task_done()
            await broadcast_health(state)
            continue

        history.append((stripped, result))
        state.translator_status = "online"
        state.last_error = ""
        await broadcast_json(ws_clients, {"type": "translation", "seq": seq, "text": result})
        transcript_queue.task_done()
        await broadcast_health(state)
