from __future__ import annotations

import argparse
import json
import logging
import os

from crisp_process import normalize_crisp_argv

logger = logging.getLogger(__name__)

ARGPARSE_DESCRIPTION = "WebRTC browser audio bridge for CrispASR streaming ASR and optional translation."

DEFAULT_TRANSLATE_URL = os.environ.get(
    "CRISPASR_TRANSLATE_URL",
    "http://127.0.0.1:8080/v1/chat/completions",
)

CRISP_PATH_VALUE_FLAGS = frozenset({"-m", "-vm", "-am", "--model", "--vad-model", "--punc-model", "--aligner-model", "--translate-model"})


BRIDGE_CONFIG_KEYS = frozenset(
    {
        "host",
        "port",
        "crispasr",
        "crisp_hide_stderr",
        "verbose",
        "translate_url",
        "translate_model",
        "translate_window",
        "translate_temperature",
        "translate_top_k",
        "translate_top_p",
        "translate_repeat_penalty",
        "translate_max_tokens",
        "temperature",
        "top_k",
        "top_p",
        "repeat_penalty",
        "max_tokens",
        "print_raw_crisp_events",
        "debug_timestamps",
        "no_translate",
        "translate_prompt_file",
        "glossary_file",
        "crisp_args",
        "name",
        "description",
        "tags",
    }
)


def pop_config_arg(argv: list[str]) -> tuple[str | None, list[str]]:
    out: list[str] = []
    i = 0
    config_path: str | None = None
    while i < len(argv):
        if argv[i] in ("--config", "-c"):
            if i + 1 >= len(argv):
                raise SystemExit("error: option --config requires a path argument")
            config_path = argv[i + 1]
            i += 2
            continue
        out.append(argv[i])
        i += 1
    return config_path, out


def load_bridge_config_file(path: str) -> dict[str, object]:
    pth = os.path.expanduser(path)
    if not os.path.isfile(pth):
        logger.error("Bridge config file not found: %s", pth)
        raise SystemExit(2)
    with open(pth, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        logger.error("Bridge config must be a JSON object: %s", path)
        raise SystemExit(2)
    bad = set(data) - BRIDGE_CONFIG_KEYS
    if bad:
        logger.warning("Ignoring unknown keys in bridge config: %s", ", ".join(sorted(bad)))
    return data


def resolve_config_crisp_paths(tokens: list[str], config_path: str | None) -> list[str]:
    if not config_path:
        return tokens
    base_dir = os.path.dirname(os.path.abspath(os.path.expanduser(config_path)))
    resolved = list(tokens)
    for idx, token in enumerate(resolved[:-1]):
        if token not in CRISP_PATH_VALUE_FLAGS:
            continue
        value = resolved[idx + 1]
        if not value or os.path.isabs(value) or "://" in value:
            continue
        resolved[idx + 1] = os.path.normpath(os.path.join(base_dir, value))
    return resolved


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    argv = argv[1:]
    if "--" in argv:
        idx = argv.index("--")
        main_argv = argv[:idx]
        crisp_argv = argv[idx + 1 :]
    else:
        main_argv = argv
        crisp_argv = []

    crisp_argv = [a for a in crisp_argv if a != "--"]

    config_path, main_argv = pop_config_arg(main_argv)
    cfg: dict[str, object] = {}
    if config_path:
        cfg = load_bridge_config_file(config_path)

    crisp_from_cfg = cfg.get("crisp_args")
    defaults = {k: cfg[k] for k in BRIDGE_CONFIG_KEYS if k in cfg and k != "crisp_args"}
    translate_sampling_aliases = {
        "temperature": "translate_temperature",
        "top_k": "translate_top_k",
        "top_p": "translate_top_p",
        "repeat_penalty": "translate_repeat_penalty",
        "max_tokens": "translate_max_tokens",
    }
    for src, dst in translate_sampling_aliases.items():
        if src in defaults and dst not in defaults:
            defaults[dst] = defaults[src]
    for bkey in (
        "crisp_hide_stderr",
        "verbose",
        "no_translate",
        "print_raw_crisp_events",
        "debug_timestamps",
    ):
        if bkey in defaults and not isinstance(defaults[bkey], bool):
            del defaults[bkey]

    p = argparse.ArgumentParser(description=ARGPARSE_DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)

    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument(
        "--crispasr",
        default=os.environ.get("CRISPASR_EXE", "crispasr"),
        help="crispasr executable (PATH or CRISPASR_EXE env)",
    )

    p.add_argument(
        "--crisp-hide-stderr",
        action="store_true",
        help="Discard CrispASR stderr entirely (default: forwarded at DEBUG; use -v for INFO diagnostics)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose: ICE (aioice) DEBUG, aiohttp access, aiortc; also CrispASR stderr at INFO (VAD, Vulkan)",
    )
    p.add_argument(
        "--print-raw-crisp-events",
        action="store_true",
        help="Print raw CrispASR stream-json events on stdout while still broadcasting bridge transcript events to /ws.",
    )
    p.add_argument(
        "--debug-timestamps",
        action="store_true",
        help="Add bridge wall-clock/backlog timing fields to terminal transcript JSON for latency debugging.",
    )

    p.add_argument(
        "--translate-url",
        default=DEFAULT_TRANSLATE_URL,
        help="OpenAI-compatible chat completions URL "
        "(default env CRISPASR_TRANSLATE_URL or http://127.0.0.1:8080/v1/chat/completions)",
    )
    p.add_argument(
        "--translate-model",
        default="",
        metavar="MODEL",
        help="Enable translation worker when non-empty (e.g. HY-MT). Ignored with --no-translate.",
    )
    p.add_argument(
        "--translate-window",
        type=int,
        default=6,
        help="Sliding window of recent (source, translated) pairs in the prompt (default 6)",
    )
    p.add_argument(
        "--translate-temperature",
        type=float,
        default=0.0,
        help="Translation sampling temperature (default 0.7).",
    )
    p.add_argument(
        "--translate-top-k",
        type=int,
        default=20,
        help="Translation top-k sampling value (default 20).",
    )
    p.add_argument(
        "--translate-top-p",
        type=float,
        default=0.6,
        help="Translation top-p sampling value (default 0.6).",
    )
    p.add_argument(
        "--translate-repeat-penalty",
        type=float,
        default=1.05,
        help="Translation repeat penalty / repetition penalty (default 1.05).",
    )
    p.add_argument(
        "--translate-max-tokens",
        type=int,
        default=256,
        help="Maximum number of tokens generated per translation request (default 256).",
    )
    p.add_argument(
        "--translate-prompt-file",
        default="",
        metavar="PATH",
        help="UTF-8 text file for translation system prompt (glossary is injected into current user message).",
    )
    p.add_argument(
        "--glossary-file",
        default="",
        metavar="PATH",
        help='JSON object {"source":"translation", ...}; terms come only from this file (omit for no glossary).',
    )
    p.add_argument(
        "--no-translate",
        action="store_true",
        help="Disable translation worker (WebSocket still receives transcripts only)",
    )
    p.set_defaults(**defaults)

    cli_crisp = normalize_crisp_argv(crisp_argv)

    ns = p.parse_args(main_argv)
    setattr(ns, "bridge_config_path", config_path)

    cfg_crisp: list[str] = []
    if isinstance(crisp_from_cfg, list):
        cfg_crisp = normalize_crisp_argv([str(x) for x in crisp_from_cfg])
        cfg_crisp = resolve_config_crisp_paths(cfg_crisp, config_path)

    # Config crisp_args is the base; optional `-- ...` appends (later tokens override in typical CLIs).
    if cfg_crisp and cli_crisp:
        crisp_argv = cfg_crisp + cli_crisp
    elif cfg_crisp:
        crisp_argv = cfg_crisp
    else:
        crisp_argv = cli_crisp
    print(ns)
    print("\n")
    print(crisp_argv)
    return ns, crisp_argv
