# Security

Nova can control a logged-in Windows session, so treat its configuration, model files, Python environment, and repository as trusted code. Speech and model output are always untrusted input.

## Threat model

Relevant threats include another person speaking near the microphone, audio played through a speaker, cloned/deepfake speech, malicious content in a video, false wake detections, inaccurate transcription, prompt injection against an optional LLM, command/path/URL injection, altered model artifacts, and malware already running in the user's session.

Nova does not defend against an attacker who can modify its source/configuration, replace model artifacts, control the Windows account, or inject code into the Python process.

## Speaker spoofing and replay

ECAPA verification measures voice similarity; it is not biometric proof. Recordings, high-quality synthesis, voice conversion, illness, microphone changes, and background noise can cause false accepts or rejects. FAR/FRR measured on a small local dataset may not predict attacks.

Optional challenge-response makes a fixed replay less useful by asking for a random phrase, but it is basic protection only. A live voice clone can answer it, and this implementation does not contain a trained anti-spoofing/liveness model or reliable acoustic echo-source detector. Keep shutdown/restart disabled unless the risk is acceptable, use headphones where appropriate, and lock the Windows session when absent.

## LLM and prompt injection

Ollama is disabled by default. If enabled, arbitrary speech may try to instruct the model to ignore rules. Nova treats the response as data, validates it as a bounded Pydantic `ActionPlan`, rejects extra fields/action names, and subjects every action to the normal policy. Conversational text cannot become code.

Never add either of these patterns:

```python
os.system(model_text)
subprocess.run(model_text, shell=True)
```

The existing executors construct argument arrays from configured executables and validated values, and call subprocesses with `shell=False`. A string containing `;`, `&&`, `$()`, or PowerShell syntax remains one inert argument.

## Permissions

- Level 0 is limited to low-impact media/volume and read-only status.
- Level 1 requires the verified owner before opening/closing configured resources or capturing a screenshot.
- Level 2 requires the owner and normally both challenge and expiring confirmation.
- Level 3 policies are disabled; corresponding destructive/general-purpose action types and executor branches are intentionally absent.

Confirmation state holds one action, expires after the configured timeout, binds to a random token, and is consumed after one response. A confirmation never authorizes a different action or an entire multi-action plan.

## Path, app, and URL safety

Apps and projects resolve exact case-insensitive aliases from YAML. App termination matches configured process names. Projects and folders must already exist. Web navigation permits only HTTP/HTTPS and search terms are URL-encoded. There is no file deletion, arbitrary shell, installer, message sending, or general system-settings executor.

Be cautious with an app entry whose executable is itself a shell, script host, package manager, or interpreter. The allow-list is only as safe as its configured targets. Keep YAML writable only by the owner.

## Logs and recordings

Structured logs include transcripts, intents, scores, actions, timing, and errors. Transcripts can be sensitive. Protect or rotate `logs/nova.jsonl`. Raw audio is not logged by default, and collection commands save audio only after explicit interactive prompts. Training audio and embeddings are biometric/sensitive personal data; encrypt backups and do not commit them.

## Safe baseline

1. Leave `llm.enabled`, restart, and shutdown disabled initially.
2. Keep speaker verification enabled after enrollment.
3. Use a held-out, diverse negative speaker set and choose a low-FAR threshold.
4. Add hard wake-word negatives from the real room.
5. Review every executable/project path and remove unused aliases.
6. Run under a standard Windows account, not an administrator account.
7. Keep Windows, Python dependencies, and model files updated from trusted sources.
8. Review JSON logs for unexpected wake triggers and rejected actions.

## Known limitations

Speaker verification is not replay/deepfake-resistant, VAD can react to playback, wake-word accuracy depends on locally collected data, faster-whisper can hallucinate or mishear, pyttsx3 Thai quality depends on installed Windows voices, and browser/app launches inherit the privileges of the logged-in user. Confirmation helps with mistakes; it does not turn voice control into a high-assurance authentication system.

