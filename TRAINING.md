# Training Nova's Models

Run every command from the repository root with the virtual environment active. Recorded audio and trained artifacts are intentionally excluded from Git. Use WAV where possible, mono 16 kHz, and keep a separate held-out evaluation set for honest production measurements.

## Wake Word Training

The default phrase is `Hey Nova`; change `wakeword.phrase` in `config/settings.yaml` and collect a new positive dataset whenever the phrase changes.

### 1. Collect samples

Record positives:

```powershell
python -m wakeword.collect --label positive --count 100
```

Record negatives:

```powershell
python -m wakeword.collect --label negative --count 150
```

Files are stored under `data/wakeword/positive/` and `data/wakeword/negative/`. Start with at least 100–300 positive utterances from the intended user and substantially more negatives. Record different speeds, emphasis, distances, rooms, microphones, and times. Negatives should include normal conversation, phrases similar to “Hey Nova,” keyboard/fan noise, music, video audio, and silence. Only use media you are allowed to record/use.

You can copy additional supported audio into those directories. Put reusable room/noise recordings in `data/wakeword/negative/noise/`; training uses them as background overlays.

### 2. Augmentation

`wakeword.augment.augment_audio` randomly applies gain, time stretch, pitch shift, leading silence, synthetic room impulse/reverb, Gaussian microphone noise, and negative-dataset noise mixing. Augmentation runs only on the training split. Validation audio remains unchanged.

### 3. Train

```powershell
python -m wakeword.train --epochs 20 --batch-size 16
```

The model is a compact PyTorch log-mel CNN. Its best checkpoint is written to `wakeword/models/best.pt`; each run writes loss history, validation metrics, confusion matrix data, and a threshold sweep below `runs/wakeword/<timestamp>/`.

### 4. Evaluate and tune

```powershell
python -m wakeword.evaluate
```

This reports precision, recall, F1, false-positive rate, false-negative rate, confusion matrix, and the best sampled threshold in `runs/wakeword/evaluation.json`. Evaluate on recordings that were not used for training. Copy a threshold that gives an acceptable false-positive/false-negative tradeoff to:

```yaml
wakeword:
  phrase: Hey Nova
  threshold: 0.80
```

Higher thresholds reduce false activations but miss more wake words. A phrase change requires new positives and retraining—not just a YAML edit.

### openWakeWord option

Set `wakeword.backend: openwakeword` and `wakeword.model_path` to a compatible openWakeWord ONNX/TFLite model. The configured phrase, normalized to lowercase with underscores, must match the score key returned by that model. `Hey Nova` is a custom phrase and therefore needs a compatible trained/exported model; switching the backend does not magically create it.

## Speaker Training / Enrollment

Speaker verification uses pretrained SpeechBrain ECAPA-TDNN embeddings; ECAPA is downloaded on first use and is not trained from scratch.

### 1. Record the owner

```powershell
python -m speaker.collect --label owner --count 50
```

Record 30–100 clips in `data/speakers/owner/`. Vary speed, microphone distance, volume, natural sentences, and time of day. Several recording sessions are better than one continuous session.

### 2. Collect negatives

Ask other consenting speakers to record the displayed phrases:

```powershell
python -m speaker.collect --label negatives --count 50
```

Negative clips go to `data/speakers/negatives/`. Include multiple speakers and conditions. Do not train only on synthetic negatives.

### 3. Extract embeddings and train

```powershell
python -m speaker.train
```

The command extracts normalized ECAPA embeddings, creates a stratified validation split, compares cosine similarity, logistic regression, RBF SVM, and a small MLP, tunes a threshold for each, and selects the best validation F1. Outputs:

```text
speaker/models/best.joblib
speaker/models/owner_embedding.npy
runs/speaker/<timestamp>/metrics.json
runs/speaker/<timestamp>/embeddings.npz
```

Use `--device cpu` if CUDA is unreliable.

### 4. Evaluate

For serious evaluation, point `--owner` and `--negatives` at separate held-out folders:

```powershell
python -m speaker.evaluate --owner data/speakers/owner-test --negatives data/speakers/negatives-test
```

For a quick (optimistic) evaluation on the collected data:

```powershell
python -m speaker.evaluate
```

The report contains accuracy, precision, recall, F1, ROC-AUC, confusion matrix, threshold sweep, FAR, and FRR. FAR is the fraction of impostor clips accepted; FRR is the fraction of owner clips rejected. Prefer a threshold that keeps FAR suitably low even if FRR rises. Put the chosen runtime threshold in `speaker.threshold`. Note that classifier probabilities and cosine scores have different scales; retune after the selected approach or enrollment data changes.

Speaker verification is convenience-grade authentication. It is not proof against replay, voice cloning, coercion, or a compromised Windows session.

## Intent Classification Training

### Dataset format

Edit `intent/dataset/intents.json`. Each item is:

```json
{
  "text": "เปิด spotify ให้หน่อย",
  "intent": "OPEN_APP",
  "entities": {"app": "spotify"}
}
```

The `entities` field documents ground truth; intent training uses `text` and `intent`, while runtime entity extraction is separate and tested. Add varied Thai, English, code-switching, misspellings typical of Whisper, polite forms, and hard negative `UNKNOWN` examples.

### Add an intent

1. Prefer an existing `ActionType` in `brain/schemas.py`.
2. Add at least 20–50 diverse phrases to the dataset.
3. Add entity extraction in `brain/parser.py` if the action needs arguments.
4. Add a permission entry in `config/permissions.yaml`.
5. Implement a static dispatch branch in `executor/executor.py` and tests. Never add raw shell execution.
6. Train and evaluate again.

### Train

```powershell
python -m intent.train
```

The model uses Unicode character n-gram TF-IDF features and trainable logistic regression. This handles Thai (which often lacks spaces), English, and common transcription spelling variation without downloading an NLP model. It writes `intent/models/best.joblib` and a timestamped run under `runs/intent/` containing train loss, validation loss, accuracy, macro F1, confusion matrix, and per-class metrics.

Custom paths and run directory are supported:

```powershell
python -m intent.train --dataset intent/dataset/intents.json --output intent/models --runs runs/intent
```

### Evaluate

```powershell
python -m intent.evaluate
```

Open `runs/intent/evaluation.json`. Rows in the confusion matrix are true classes and columns are predicted classes in the recorded `labels` order. Low per-class recall means commands are being missed; low precision means other commands are being confused for that class. Add representative examples rather than duplicating identical phrases.

The runtime confidence cutoff is `intent.threshold` in `config/settings.yaml`. Predictions below it become `UNKNOWN`; if `allow_rule_fallback` is true, the small offline rule set can still recover common commands.

