from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
import shutil

import aiohttp
from aiohttp import web

from bridge_config import load_bridge_config_file, parse_args
from bridge_state import BridgeRealtimeState, broadcast_health
from crisp_process import SAMPLE_RATE, build_crispasr_cmd, pcm_writer, relay_stderr, relay_stdout, stream_step_bytes_from_extra
from translation import load_merged_glossary, resolve_translation_system_prompt, translate_health_url, translator_health_monitor, translator_worker
from web_app import make_app

logger = logging.getLogger(__name__)


class CrispRuntime:
    def __init__(self, state: BridgeRealtimeState, pcm_queue: asyncio.Queue[bytes]) -> None:
        self.state = state
        self.pcm_queue = pcm_queue
        self.proc: asyncio.subprocess.Process | None = None
        self.http_session: aiohttp.ClientSession | None = None
        self.tasks: list[asyncio.Task[object]] = []
        self.lock = asyncio.Lock()

    async def start(
        self,
        crisp_exe: str,
        crispy_extra: list[str],
        *,
        profile_name: str,
        crisp_hide_stderr: bool,
        verbose: bool,
        translate_enabled: bool,
        translate_url: str,
        translate_model: str,
        translate_window: int,
        translate_temperature: float,
        translate_top_k: int,
        translate_top_p: float,
        translate_repeat_penalty: float,
        translate_max_tokens: int,
        print_raw_crisp_events: bool,
        debug_timestamps: bool,
        translate_bearer: str | None,
        system_prompt: str | None,
        glossary: dict[str, str] | None,
    ) -> None:
        async with self.lock:
            await self._stop_locked()
            self._drain_pcm_queue()

            exe = self._resolve_executable(crisp_exe)
            if not exe:
                self.state.crisp_status = "error"
                self.state.active_profile = profile_name
                self.state.last_error = f"Cannot find crispasr executable: {crisp_exe!r}"
                await broadcast_health(self.state)
                raise FileNotFoundError(self.state.last_error)
            if not crispy_extra:
                self.state.crisp_status = "error"
                self.state.active_profile = profile_name
                self.state.last_error = "No CrispASR arguments in selected profile."
                await broadcast_health(self.state)
                raise ValueError(self.state.last_error)

            cmd = build_crispasr_cmd(exe, crispy_extra)
            logger.info("Spawning profile=%s: %s", profile_name, " ".join(cmd))

            cwd_path = os.path.dirname(os.path.abspath(exe))
            cwd = cwd_path if cwd_path and os.path.isdir(cwd_path) else None
            stderr_arg = asyncio.subprocess.DEVNULL if crisp_hide_stderr else asyncio.subprocess.PIPE
            self.state.active_profile = profile_name
            self.state.crisp_status = "starting"
            self.state.last_error = ""
            self.state.translator_status = "checking" if translate_enabled else "disabled"
            await broadcast_health(self.state)

            env = os.environ.copy()
            env["CRISPASR_KV_QUANT"] = "q8_0"
            env["CRISPASR_GGUF_MMAP"] = "1"
            env["CRISPASR_GGUF_PRELOAD"] = "1"
            # env["CRISPASR_KV_QUANT_K"] = "q8_0"
            # env["CRISPASR_KV_QUANT_V"] = "q8_0"
            env["CRISPASR_NEMOTRON_STREAMING"] = "1"
            env["CRISPASR_NEMOTRON_CONTEXT_PRESET"] = "3"

            self.proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=stderr_arg,
                cwd=cwd,
                limit=1024 * 1024,
                env=env
            )

            self.tasks = [
                asyncio.create_task(pcm_writer(self.proc, self.pcm_queue)),
                asyncio.create_task(
                    relay_stdout(
                        self.proc,
                        self.state,
                        enqueue_for_translate=translate_enabled,
                        print_raw_crisp_events=print_raw_crisp_events,
                        debug_timestamps=debug_timestamps,
                    )
                ),
                asyncio.create_task(self._watch_child(self.proc, profile_name)),
            ]
            if self.proc.stderr:
                self.tasks.append(asyncio.create_task(relay_stderr(self.proc, crisp_verbose=verbose)))

            preload = stream_step_bytes_from_extra(crispy_extra)
            self.state.stream_preload_sec = preload / (2 * SAMPLE_RATE)
            logger.info("Queueing initial %d-byte silence (one Crisp stream step) onto stdin.", preload)
            await self.pcm_queue.put(b"\x00" * preload)

            if translate_enabled:
                assert system_prompt is not None
                assert glossary is not None
                self.http_session = aiohttp.ClientSession()
                self.tasks.append(
                    asyncio.create_task(
                        translator_health_monitor(
                            self.state,
                            self.http_session,
                            health_url=translate_health_url(translate_url),
                        )
                    )
                )
                self.tasks.append(
                    asyncio.create_task(
                        translator_worker(
                            self.state.transcript_queue,
                            self.http_session,
                            state=self.state,
                            translate_url=translate_url,
                            translate_model=translate_model,
                            translate_window=translate_window,
                            translate_temperature=translate_temperature,
                            translate_top_k=translate_top_k,
                            translate_top_p=translate_top_p,
                            translate_repeat_penalty=translate_repeat_penalty,
                            translate_max_tokens=translate_max_tokens,
                            system_prompt=system_prompt,
                            glossary=glossary,
                            bearer=translate_bearer,
                            ws_clients=self.state.ws_clients,
                        )
                    )
                )

            self.state.crisp_status = "running"
            await broadcast_health(self.state)

    async def stop(self) -> None:
        async with self.lock:
            await self._stop_locked()
            await broadcast_health(self.state)

    async def _stop_locked(self) -> None:
        for task in self.tasks:
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []

        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=2.0)
            except TimeoutError:
                self.proc.kill()
                await self.proc.wait()
        self.proc = None

        if self.http_session:
            await self.http_session.close()
        self.http_session = None
        self.state.crisp_status = "stopped"

    async def _watch_child(self, proc: asyncio.subprocess.Process, profile_name: str) -> None:
        rc = await proc.wait()
        if proc is not self.proc:
            return
        if rc != 0:
            msg = f"CrispASR profile {profile_name!r} exited with code {rc}"
            logger.warning("%s", msg)
            self.state.last_error = msg
            self.state.crisp_status = "error"
        else:
            logger.warning("CrispASR profile %r exited cleanly.", profile_name)
            self.state.crisp_status = "stopped"
        await broadcast_health(self.state)

    def _drain_pcm_queue(self) -> None:
        while True:
            try:
                self.pcm_queue.get_nowait()
                self.pcm_queue.task_done()
            except asyncio.QueueEmpty:
                return

    @staticmethod
    def _resolve_executable(crisp_exe: str) -> str | None:
        if os.path.isfile(crisp_exe):
            return crisp_exe
        resolved = shutil.which(crisp_exe)
        if resolved and os.path.isfile(resolved):
            return resolved
        return None


def discover_profiles(profiles_dir: Path) -> list[dict[str, object]]:
    profiles: list[dict[str, object]] = []
    local_profile_names = {path.name for path in profiles_dir.glob("*.json") if ".example." not in path.name}
    for path in sorted(profiles_dir.glob("*.json")):
        if ".example." in path.name:
            local_name = path.name.replace(".example.", ".")
            if local_name in local_profile_names:
                continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or not isinstance(data.get("crisp_args"), list):
            continue
        data = load_bridge_config_file(str(path))
        profiles.append(
            {
                "name": path.name,
                "label": str(data.get("name") or path.stem),
                "description": str(data.get("description") or ""),
                "tags": data.get("tags") if isinstance(data.get("tags"), list) else [],
                "path": str(path),
                "translate_model": str(data.get("translate_model") or ""),
                "crispasr": str(data.get("crispasr") or ""),
            }
        )
    return profiles


def resolve_profile_path(profiles_dir: Path, name: str) -> Path:
    candidate = Path(name)
    if candidate.is_absolute():
        path = candidate
    else:
        path = profiles_dir / candidate.name
    path = path.resolve()
    if path.parent != profiles_dir.resolve() or path.suffix.lower() != ".json" or not path.is_file():
        raise ValueError(f"Unknown profile: {name}")
    return path


async def async_main(
    crisp_exe: str,
    crispy_extra: list[str],
    host: str,
    port: int,
    *,
    crisp_hide_stderr: bool,
    verbose: bool,
    translate_enabled: bool,
    translate_url: str,
    translate_model: str,
    translate_window: int,
    translate_temperature: float,
    translate_top_k: int,
    translate_top_p: float,
    translate_repeat_penalty: float,
    translate_max_tokens: int,
    print_raw_crisp_events: bool,
    debug_timestamps: bool,
    translate_bearer: str | None,
    system_prompt: str | None,
    glossary: dict[str, str] | None,
    initial_profile: str,
) -> None:
    pcm_queue: asyncio.Queue[bytes] = asyncio.Queue()
    trans_q: asyncio.Queue[tuple[int, str]] = asyncio.Queue()
    bridge_state = BridgeRealtimeState(transcript_queue=trans_q)
    runtime = CrispRuntime(bridge_state, pcm_queue)
    base_dir = Path(__file__).resolve().parent
    profiles_dir = base_dir / "profiles"

    async def list_profiles() -> dict[str, object]:
        return {
            "profiles": discover_profiles(profiles_dir),
            "active": bridge_state.active_profile,
            "crisp_status": bridge_state.crisp_status,
        }

    async def select_profile(name: str) -> dict[str, object]:
        path = resolve_profile_path(profiles_dir, name)
        ns, crisp_args = parse_args(["bridge_server.py", "--config", str(path)])
        translate_is_enabled = not ns.no_translate and bool((ns.translate_model or "").strip())
        profile_glossary: dict[str, str] | None = None
        profile_prompt: str | None = None
        if translate_is_enabled:
            profile_glossary = load_merged_glossary((ns.glossary_file or "").strip() or None)
            profile_prompt = resolve_translation_system_prompt(
                (ns.translate_prompt_file or "").strip() or None,
                profile_glossary,
            )
        await runtime.start(
            ns.crispasr,
            crisp_args,
            profile_name=path.name,
            crisp_hide_stderr=ns.crisp_hide_stderr,
            verbose=ns.verbose,
            translate_enabled=translate_is_enabled,
            translate_url=ns.translate_url,
            translate_model=(ns.translate_model or "").strip(),
            translate_window=ns.translate_window,
            translate_temperature=ns.translate_temperature,
            translate_top_k=ns.translate_top_k,
            translate_top_p=ns.translate_top_p,
            translate_repeat_penalty=ns.translate_repeat_penalty,
            translate_max_tokens=ns.translate_max_tokens,
            print_raw_crisp_events=ns.print_raw_crisp_events,
            debug_timestamps=ns.debug_timestamps,
            translate_bearer=os.environ.get("OPENAI_API_KEY") or None,
            system_prompt=profile_prompt,
            glossary=profile_glossary,
        )
        return {
            "profiles": discover_profiles(profiles_dir),
            "active": bridge_state.active_profile,
            "crisp_status": bridge_state.crisp_status,
        }

    if crispy_extra:
        await runtime.start(
            crisp_exe,
            crispy_extra,
            profile_name=initial_profile or "cli",
            crisp_hide_stderr=crisp_hide_stderr,
            verbose=verbose,
            translate_enabled=translate_enabled,
            translate_url=translate_url,
            translate_model=translate_model,
            translate_window=translate_window,
            translate_temperature=translate_temperature,
            translate_top_k=translate_top_k,
            translate_top_p=translate_top_p,
            translate_repeat_penalty=translate_repeat_penalty,
            translate_max_tokens=translate_max_tokens,
            print_raw_crisp_events=print_raw_crisp_events,
            debug_timestamps=debug_timestamps,
            translate_bearer=translate_bearer,
            system_prompt=system_prompt,
            glossary=glossary,
        )
    else:
        bridge_state.crisp_status = "stopped"
        bridge_state.translator_status = "disabled"
        bridge_state.last_error = "Select a profile before starting capture."

    runner = web.AppRunner(
        make_app(
            pcm_queue,
            bridge_state,
            list_profiles=list_profiles,
            select_profile=select_profile,
        )
    )
    await runner.setup()
    await web.TCPSite(runner, host, port).start()
    logger.info("Serving http://%s:%s/ - select a profile, allow capture, then wait for SDP.", host, port)

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down (KeyboardInterrupt)...")
    finally:
        await runtime.stop()
        await runner.cleanup()
