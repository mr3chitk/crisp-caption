from __future__ import annotations

import importlib.util
import json
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "profile.ja.json"


FAILED = 0


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str, fix: str = "") -> None:
    print(f"[WARN] {message}")
    if fix:
        print(f"       Fix: {fix}")


def fail(message: str, fix: str = "") -> None:
    global FAILED
    FAILED += 1
    print(f"[FAIL] {message}")
    if fix:
        print(f"       Fix: {fix}")


def import_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def load_profile() -> dict[str, Any] | None:
    if not PROFILE.is_file():
        fail("profiles/profile.ja.json not found", "Run scripts\\setup-windows.bat")
        return None
    try:
        data = json.loads(PROFILE.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"profiles/profile.ja.json is invalid JSON: {exc}")
        return None
    ok("profiles/profile.ja.json exists")
    return data if isinstance(data, dict) else None


def resolve_profile_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROFILE.parent / path
    return path.resolve()


def crisp_arg_path(profile: dict[str, Any], flag: str) -> Path | None:
    args = profile.get("crisp_args")
    if not isinstance(args, list):
        fail("profile crisp_args must be a list")
        return None
    for idx, token in enumerate(args[:-1]):
        if token == flag:
            return resolve_profile_path(str(args[idx + 1]))
    return None


def check_python() -> None:
    ok(f"Python {sys.version.split()[0]}: {sys.executable}")
    if sys.version_info < (3, 11):
        fail("Python 3.11+ is required")


def check_packages() -> None:
    for package in ("aiohttp", "aiortc", "av", "numpy"):
        if import_exists(package):
            ok(f"Python package import works: {package}")
        else:
            fail(f"Missing Python package: {package}", "Run scripts\\setup-windows.bat")
    if import_exists("PySide6"):
        ok("Optional overlay package import works: PySide6")
    else:
        warn("Optional overlay package missing: PySide6", "Run scripts\\setup-windows.bat")


def check_frontend() -> None:
    index = ROOT / "frontend" / "dist" / "index.html"
    if index.is_file():
        ok("frontend/dist/index.html exists")
    else:
        fail("frontend build not found", "Run scripts\\setup-windows.bat")


def check_executable(path: Path, label: str, fix: str) -> None:
    if path.is_file():
        ok(f"{label} found: {path}")
    else:
        fail(f"{label} not found: {path}", fix)


def check_profile(profile: dict[str, Any]) -> None:
    crisp = str(profile.get("crispasr") or "").strip()
    if crisp.lower() == "auto":
        crisp_path = ROOT / "tools" / "crispasr" / "crispasr.exe"
    elif crisp and ("/" in crisp or "\\" in crisp or crisp.endswith(".exe")):
        crisp_path = Path(crisp)
        if not crisp_path.is_absolute():
            crisp_path = ROOT / crisp_path
    elif crisp:
        found = shutil.which(crisp)
        if found:
            ok(f"CrispASR found on PATH: {found}")
            crisp_path = None
        else:
            fail(f"CrispASR executable not found on PATH: {crisp}", "Run scripts\\download-crispasr-windows.bat or edit profiles\\profile.ja.json")
            crisp_path = None
    else:
        fail("profile crispasr is empty", "Set crispasr to tools/crispasr/crispasr.exe")
        crisp_path = None
    if crisp_path is not None:
        check_executable(crisp_path, "CrispASR", "Run scripts\\download-crispasr-windows.bat")

    asr_model = crisp_arg_path(profile, "-m")
    if asr_model:
        check_executable(asr_model, "ASR model", "Run scripts\\models-download.bat")
    vad_model = crisp_arg_path(profile, "-vm")
    if vad_model:
        check_executable(vad_model, "VAD model", "Run scripts\\models-download.bat")

    translate_model = str(profile.get("translate_model") or "").strip()
    if translate_model:
        check_executable(ROOT / "tools" / "llama.cpp" / "llama-server.exe", "llama-server", "Run scripts\\download-llama-cpp-windows.bat")
        check_executable(ROOT / "models" / "translation" / "Hy-MT2-1.8B-Q4_K_M.gguf", "Translation model", "Run scripts\\models-download.bat")
        check_translation_health(str(profile.get("translate_url") or "http://127.0.0.1:8080/v1/chat/completions"))
    else:
        warn("Translation is disabled in profile", 'Set "translate_model": "Hy-MT2-1.8B" in profiles\\profile.ja.json')


def check_port(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            warn(f"Port {port} is already in use")
        else:
            ok(f"Port {port} is free")


def check_translation_health(translate_url: str) -> None:
    health = "http://127.0.0.1:8080/health"
    if "/v1/" in translate_url:
        health = translate_url.split("/v1/", 1)[0] + "/health"
    try:
        with urllib.request.urlopen(health, timeout=2) as resp:
            if 200 <= resp.status < 300:
                ok(f"Translation server is reachable: {health}")
            else:
                warn(f"Translation server returned HTTP {resp.status}: {health}")
    except (urllib.error.URLError, TimeoutError) as exc:
        warn(f"Translation server is not running yet: {exc}", "run-windows.bat will start it, or run scripts\\start-translation-server-windows.bat")


def main() -> int:
    print("=== crisp-caption dependency check ===")
    check_python()
    check_packages()
    check_frontend()
    check_port(8765)
    profile = load_profile()
    if profile is not None:
        check_profile(profile)
    print()
    if FAILED:
        print(f"[FAIL] {FAILED} required check(s) failed.")
        return 1
    print("[OK] Required checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
