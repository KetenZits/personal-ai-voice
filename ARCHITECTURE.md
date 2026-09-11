# Architecture

```mermaid
flowchart TD
    A[Microphone 16 kHz mono] --> B[VAD / rolling buffer]
    B --> C[Wake-word detector]
    C --> D[ECAPA speaker verification]
    D --> E[VAD command recorder]
    E --> F[faster-whisper STT]
    F --> G[Intent classifier + entity parser]
    G -. UNKNOWN only .-> L[Optional local Ollama]
    L --> V[Pydantic validation]
    G --> P[Permission layer]
    V --> P
    P --> R{Challenge / confirmation?}
    R --> X[Strict action executor]
    X --> T[Local TTS + structured log]
```

## Runtime states

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> LISTENING_FOR_WAKE_WORD
    IDLE --> LISTENING_FOR_COMMAND: push-to-talk
    LISTENING_FOR_WAKE_WORD --> VERIFYING_SPEAKER: wake detected
    VERIFYING_SPEAKER --> LISTENING_FOR_COMMAND: owner accepted
    VERIFYING_SPEAKER --> LISTENING_FOR_WAKE_WORD: rejected
    LISTENING_FOR_COMMAND --> PROCESSING: speech ends
    PROCESSING --> EXECUTING: authorized
    PROCESSING --> SPEAKING: denied / prompt
    EXECUTING --> SPEAKING: result
    SPEAKING --> LISTENING_FOR_WAKE_WORD
    SPEAKING --> LISTENING_FOR_COMMAND
    SPEAKING --> IDLE
```

`assistant_state.StateMachine` rejects illegal transitions and exposes a locked snapshot to the debug dashboard.

## Modules

- `audio/`: `sounddevice` stream, mono/normalization/resampling, WebRTC VAD with energy fallback, VAD-ended recording, WAV helpers.
- `wakeword/`: collection, augmentation, dataset, log-mel CNN, train/evaluate, streaming inference, and openWakeWord adapter.
- `speaker/`: enrollment, pretrained SpeechBrain ECAPA embedding extraction, four verifier approaches, evaluation, runtime scoring.
- `stt/`: waveform preparation and faster-whisper adapter. Model initialization chooses CUDA/float16 or CPU/int8 and retries CPU after CUDA startup failure.
- `intent/`: JSON dataset, Unicode character n-gram classifier, rule fallback, training and evaluation.
- `brain/`: Pydantic contracts, entity extraction, compound parsing, optional Ollama JSON adapter, permissions, confirmation, replay challenge.
- `executor/`: app/project alias resolution and a fixed action dispatch table. Platform libraries are imported only inside the actions that need them.
- `tts/`: replaceable pyttsx3/SAPI engine and voice selection.
- `main.py`: composition root and resilient user interaction loop.
- `logging_setup.py` / `dashboard.py`: JSONL telemetry and a lightweight terminal status view.

## Trust boundary

```mermaid
flowchart LR
    U[Untrusted speech/text] --> M[ML or LLM]
    M --> S[Strict Action schema]
    S --> P[Policy + identity + confirmation]
    P --> A[Allow-listed adapter]
    A --> W[Windows]
```

Speech, STT text, entity values, and LLM JSON are untrusted. An `Action` rejects unknown fields and unknown action types. URLs are limited to HTTP(S), apps/projects are alias-resolved from configuration, paths must exist, and subprocess calls use fixed executable/argument lists with `shell=False`. There is no general shell dispatch branch.

## Training artifacts and data flow

Wake-word audio becomes fixed two-second log-mel features for the CNN. Speaker recordings become normalized 192-dimensional ECAPA embeddings (dimension is model-dependent), then a validation comparison selects the best verifier. Intent text becomes Unicode character n-gram TF-IDF features for logistic regression. Each trainer makes a stratified split and saves metrics beneath `runs/`.

## Extension points

Add TTS engines behind a `speak(text)` interface, new STT behind `transcribe(audio, rate)`, and local language models behind `parse(text) -> ActionPlan`. New actions require a schema enum value, permission policy, executor branch, and tests. This deliberate duplication makes security review visible.

