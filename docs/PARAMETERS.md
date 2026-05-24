# Parameter Reference

This file explains the flags used by the example profiles in `profiles/`.

Current practical profile baseline:

```text
--backend cohere
-l ja
-m ../models/cohere-asr-ja-v0.1-q4_k.gguf
--stream-json
--stream-final-mode redecode
--stream-utterance-max-sec 60
--stream-final-on-silence-ms 300-330
--stream-vad-merge-gap-ms 250
--stream-length 8000
--stream-step 600
--stream-partial-decode-ms 0
--vad
-vm ../models/firered-vad.gguf
-vt 0.67
-vspd 180
-vsd 330
-vmsd 10
-vp 110
```

## Main Streaming Flags

| Flag | Current setting | Effect | Tradeoff |
|---|---:|---|---|
| `--stream-json` | on | Emits structured `partial`, `final`, and `silence` events. | Required for this bridge UI. |
| `--stream-step` | `750` in the public stable example | How often the stream loop processes new audio. | Lower can feel more live but may increase partial decode work. Tune this together with your model and hardware. |
| `--stream-length` | `8000` | Rolling audio context window in ms. | More context can improve recognition, but more repeated work. Current value is a practical middle ground. |
| `--stream-final-on-silence-ms` | `300` or `330` | Trailing silence needed before finalizing an utterance. | Lower finalizes faster; too low can split phrases. |
| `--stream-vad-merge-gap-ms` | `250` | Merges nearby VAD slices separated by small gaps. | Higher can reduce fragmentation but may glue reactions and increase active partial work. |
| `--stream-final-mode` | `redecode` | Redecodes the final utterance span for better final text. | Better final quality with extra finalization work. |
| `--stream-utterance-max-sec` | `60` | Hard cap for one utterance. | Prevents runaway long segments; keep high enough to avoid artificial cuts. |
| `--stream-partial-decode-ms` | `0` | Partial decode cadence override, when supported by the CLI. | Current profiles rely mainly on `--stream-step`; revisit if CrispASR gains better partial throttling. |

## Backend And Model Flags

Model paths inside `crisp_args` are resolved relative to the profile JSON file when they come from a config file.

| Flag | Current setting | Effect | Notes |
|---|---|---|---|
| `--backend` | `cohere` | Selects the ASR backend. | Current tested Japanese profile uses Cohere ASR. |
| `-l` | `ja` | Source language. | Set to match the content. |
| `-m` | `cohere-asr-ja-v0.1-q4_k.gguf` | ASR model path. | Must exist locally. |

## VAD Flags

| Flag | Current setting | Effect | Tradeoff |
|---|---:|---|---|
| `--vad` | on | Enables VAD-based streaming segmentation. | Required for the current low-latency utterance flow. |
| `-vm` | `firered-vad.gguf` | VAD model path. | Must exist locally. |
| `-vt` | `0.67` | VAD speech threshold. | Higher rejects more noise but can miss quiet speech. |
| `-vspd` | `180` | Minimum speech duration in ms. | Lower keeps short reactions; too low can increase noise fragments. |
| `-vsd` | `330` | Minimum silence duration in ms. | Lower finalizes quicker; higher reduces cuts but delays finals. |
| `-vmsd` | `10` | Maximum speech duration in seconds for VAD regions. | Guard against overly long VAD spans. |
| `-vp` | `110` | Speech padding in ms. | Helps avoid clipping word starts/ends; too high glues phrases. |

## Punctuation

Do not pass `--punc-model` in realtime JSON+VAD profiles for now.

- FireRedPunc called on frequent streaming partial/slice events caused large lag spikes.
- Turning punctuation off reduced accumulated lag substantially.
- If punctuation is needed, apply it only after final text, either in CrispASR if supported or in the bridge/client layer.

## Translation Settings

| Key | Current setting | Effect |
|---|---:|---|
| `translate_model` | `Hy-MT2-1.8B` in the public example | Enables translation when non-empty. Match this to your translation server model alias. |
| `translate_url` | `http://127.0.0.1:8080/v1/chat/completions` | OpenAI-compatible chat completions endpoint. |
| `translate_window` | `4` or `8` | Number of recent final translation pairs used as context. |
| `temperature` | `0.7` | Translation sampling temperature. |
| `top_k` | `20` | Translation top-k. |
| `top_p` | `0.6` | Translation top-p. |
| `repeat_penalty` | `1.05` | Repetition penalty. |
| `max_tokens` | `4096` | Output cap for longer subtitles/context. |
| `translate_prompt_file` | empty | Optional custom prompt file. Useful for domain style. |
| `glossary_file` | empty | Optional term mapping JSON. Useful for names and proper nouns. |

Translation is final-only. Partial ASR remains visible as preview text, but partials are not sent to the translation server.

## Choosing A Profile

- Use `profiles/profile.ja.example.json` as the public Japanese baseline, then copy it to a local ignored profile before editing machine-specific paths.
- Keep profile count small; each profile should represent a real live-operation choice.
