# crisp-caption

Live Japanese captions and translation for browser audio, video playback, livestream watching, and OBS.

The target setup is a Windows PC with a Vulkan-capable GPU and about 6 GB of VRAM. With the default Japanese ASR + Hy-MT2 translation profile, the intended live delay is roughly within 5 seconds on suitable hardware.

`crisp-caption` captures tab or microphone audio in the browser, streams it to CrispASR, translates finalized utterances with a local llama.cpp server, and displays subtitles in the browser, a transparent desktop overlay, or an OBS Browser Source.

```text
browser tab/mic audio
  -> WebRTC
  -> Python bridge
  -> CrispASR Vulkan streaming ASR
  -> llama.cpp Vulkan translation server
  -> browser transcript / transparent overlay / OBS overlay
```

This repository does not vendor runtime binaries or model files. The setup scripts download Vulkan builds into `tools/` and model files into `models/`.

## Demo

Feature demos are stored in `demo/`:

![Control panel](demo/ControlPanel.png)

- [Transparent desktop overlay](demo/overlay.mp4)
- [OBS subtitle overlay](demo/obs-subtitle.mp4)
- [Full demo page](demo/)

The demo page includes GitHub-hosted video previews and local MP4 fallbacks.

## Windows Quick Start

Run these commands from the project folder:

```bat
scripts\setup-windows.bat
scripts\download-crispasr-windows.bat
scripts\download-llama-cpp-windows.bat
scripts\models-download.bat
scripts\check-deps.bat
scripts\run-windows.bat
```

Then open:

```text
http://127.0.0.1:8765/
```

In the browser UI, choose:

- `Tab audio` for video playback or livestream watching in a browser tab.
- `Microphone` for microphone capture.
- `Overlay` for a transparent always-on-top subtitle window.

On Chromium-based browsers, enable tab audio in the browser capture picker.

## What The Scripts Do

`scripts\setup-windows.bat`

- Checks Python and pip.
- Creates `.venv`.
- Installs Python dependencies.
- Installs transparent overlay dependencies.
- Creates `profiles\profile.ja.json` from `profiles\profile.ja.example.json` if missing.
- Installs frontend dependencies.
- Builds `frontend\dist`.

`scripts\download-crispasr-windows.bat`

- Downloads a fixed CrispASR Windows Vulkan runtime.
- Extracts it to `tools\crispasr\`.
- Deletes the downloaded archive.
- Checks that `tools\crispasr\crispasr.exe` starts.

`scripts\download-llama-cpp-windows.bat`

- Downloads a fixed llama.cpp Windows Vulkan runtime.
- Extracts it to `tools\llama.cpp\`.
- Deletes the downloaded archive.
- Checks that `tools\llama.cpp\llama-server.exe` exists.

`scripts\models-download.bat`

- Downloads the ASR model, VAD model, and Hy-MT2 translation model listed in `models\manifest.json`.
- Stores model files under `models\`.

`scripts\check-deps.bat`

- Checks Python packages, frontend build output, profile, CrispASR, llama.cpp, model files, ports, and translation server reachability.

`scripts\run-windows.bat`

- Starts the llama.cpp translation server in a separate window.
- Waits for `http://127.0.0.1:8080/health`.
- Starts the CrispASR bridge.
- Opens `http://127.0.0.1:8765/`.

## Hardware And Runtime

The default path uses Vulkan for both CrispASR and llama.cpp.

Recommended baseline:

- Windows 10 or 11
- Vulkan-capable GPU
- About 6 GB VRAM
- Python 3.11+
- Node.js LTS. The setup script tries Corepack/pnpm first and falls back to npm.
- Chromium-based browser for tab audio capture

If the translation server exits immediately or runs out of memory, try:

```bat
scripts\start-translation-server-low-vram-windows.bat
```

The low-VRAM server uses smaller llama.cpp context/batch settings. It may be slower or have less translation context.

## Models

The default profile expects:

```text
models\asr\cohere-asr-ja-v0.1-q4_k.gguf
models\vad\firered-vad.gguf
models\translation\Hy-MT2-1.8B-Q4_K_M.gguf
```

`models\manifest.json` uses pinned Hugging Face `resolve` URLs with SHA256 verification. Model payloads are ignored by Git.

Hy-MT2 uses the Tencent HY Community License Agreement, not a permissive open-source license. Read `docs\third-party.md` and the upstream license before redistribution or commercial use.

## Profiles

Public example profiles live in `profiles\`.

```text
profiles\profile.ja.example.json
```

`setup-windows.bat` copies it to:

```text
profiles\profile.ja.json
```

Local profile JSON files are ignored by Git. Edit `profiles\profile.ja.json` for your machine.

Important fields:

```json
"crispasr": "tools/crispasr/crispasr.exe",
"translate_model": "Hy-MT2-1.8B",
"translate_url": "http://127.0.0.1:8080/v1/chat/completions"
```

Model paths in `crisp_args`, such as `../models/asr/model.gguf`, are resolved relative to the profile JSON file.

## Transparent Overlay

Click `Overlay` in the browser UI to start the native transparent subtitle overlay.

Controls:

- Hold `Ctrl` to show the control frame.
- Hold `Ctrl` and drag the middle area to move the overlay.
- Hold `Ctrl` and drag the handles to resize it.
- Hold `Ctrl` and click `x` to close it.
- `Ctrl+Q` also closes the overlay.

## OBS Overlay

For OBS, use a Browser Source:

```text
http://127.0.0.1:8765/obs-overlay
```

Set the Browser Source size to your canvas size, for example `1920 x 1080`. The page has a transparent background and connects to the same subtitle stream.

## Translation Server

The default translation server command is in:

```bat
scripts\start-translation-server-windows.bat
```

It uses llama.cpp Vulkan with:

```text
-c 8192 -b 2048 -ub 1024
```

The profile model name must match the llama.cpp alias:

```json
"translate_model": "Hy-MT2-1.8B"
```

Translation is final-only. Partial ASR text is shown as live preview but is not sent to the translation model.

## Troubleshooting

Run:

```bat
scripts\check-deps.bat
```

Common fixes:

- Missing Python packages: run `scripts\setup-windows.bat`.
- Missing CrispASR: run `scripts\download-crispasr-windows.bat`.
- Missing llama.cpp: run `scripts\download-llama-cpp-windows.bat`.
- Missing models: run `scripts\models-download.bat`.
- Translation server out of memory: use `scripts\start-translation-server-low-vram-windows.bat`.
- Browser page not found: rerun `scripts\setup-windows.bat` to rebuild `frontend\dist`.

## Development

Run the frontend dev server:

```bat
cd frontend
corepack pnpm install
corepack pnpm dev
```

Keep the Python bridge running on `127.0.0.1:8765`; Vite proxies backend calls.

Build the production UI:

```bat
cd frontend
corepack pnpm build
```

## Debug Commands

Use the virtual environment Python after setup:

```bat
.venv\Scripts\python.exe bridge_server.py --config profiles\profile.ja.json --print-raw-crisp-events
.venv\Scripts\python.exe bridge_server.py --config profiles\profile.ja.json --no-translate
.venv\Scripts\python.exe bridge_server.py --config profiles\profile.ja.json --no-translate --debug-timestamps
.venv\Scripts\python.exe bridge_server.py --config profiles\profile.ja.json -v
```

## Documentation

- `docs\PARAMETERS.md`: profile and CrispASR flag reference.
- `docs\changelog.md`: public release notes.
- `docs\third-party.md`: third-party runtime and model license notes.
- `profiles\profile.ja.example.json`: public Japanese live-subtitle example profile.

## License

`crisp-caption` source code is licensed under the Apache License 2.0. Runtime binaries and model files downloaded by the helper scripts are third-party artifacts under their own licenses. See `docs\third-party.md`.
