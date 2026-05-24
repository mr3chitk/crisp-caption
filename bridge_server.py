#!/usr/bin/env python3
"""WebRTC -> CrispASR bridge entry point.

The implementation is split into sibling modules so this file only owns CLI
bootstrap and process startup.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from bridge_config import parse_args
from bridge_logging import configure_logging
from bridge_runtime import async_main
from translation import load_merged_glossary, resolve_translation_system_prompt

logger = logging.getLogger(__name__)


def main() -> None:
    ns, crisp_extra = parse_args(sys.argv)
    configure_logging(ns.verbose)

    translate_enabled = not ns.no_translate and bool((ns.translate_model or "").strip())
    translate_bearer = os.environ.get("OPENAI_API_KEY") or None

    system_prompt: str | None = None
    glossary: dict[str, str] | None = None
    if translate_enabled:
        glossary = load_merged_glossary((ns.glossary_file or "").strip() or None)
        system_prompt = resolve_translation_system_prompt(
            (ns.translate_prompt_file or "").strip() or None,
            glossary,
        )
        if (ns.translate_prompt_file or "").strip():
            logger.info("Translation prompt file: %s", (ns.translate_prompt_file or "").strip())
        if (ns.glossary_file or "").strip():
            logger.info("Glossary file: %s", (ns.glossary_file or "").strip())
    if getattr(ns, "bridge_config_path", None):
        logger.info("Bridge config: %s", ns.bridge_config_path)

    try:
        asyncio.run(
            async_main(
                ns.crispasr,
                crisp_extra,
                ns.host,
                ns.port,
                crisp_hide_stderr=ns.crisp_hide_stderr,
                verbose=ns.verbose,
                translate_enabled=translate_enabled,
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
                translate_bearer=translate_bearer,
                system_prompt=system_prompt,
                glossary=glossary,
                initial_profile=Path(ns.bridge_config_path).name if getattr(ns, "bridge_config_path", None) else "",
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
