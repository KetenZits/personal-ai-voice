# Using Nova

## First-time setup

1. Install Python 3.11, create/activate `.venv`, and run `pip install -r requirements.txt` as shown in `README.md`.
2. Run `python main.py --list-microphones`; put the chosen index in `config/settings.yaml`.
3. Test capture/STT with `python main.py --push-to-talk --no-speaker-verification --debug`.
4. Enroll and train the owner with `python -m speaker.collect` then `python -m speaker.train`.
5. Configure executable paths/aliases in `config/apps.yaml`.
6. Configure existing project directories in `config/projects.yaml`.
7. Collect/train the wake phrase with `python -m wakeword.collect` and `python -m wakeword.train`.
8. Run `python main.py`.

Large faster-whisper and SpeechBrain files download on first use. After they are cached, transcription and verification run locally.

## Starting and stopping

Wake-word mode:

```powershell
python main.py
```

Debug dashboard and detailed console logs:

```powershell
python main.py --debug
```

Push-to-talk (press Enter, speak, stop speaking, then wait for the result):

```powershell
python main.py --push-to-talk
```

Setup mode without speaker verification:

```powershell
python main.py --push-to-talk --no-speaker-verification
```

Stop cleanly with `Ctrl+C`. JSON events remain in `logs/nova.jsonl`; raw audio is not logged unless you explicitly build/enable an audio retention workflow.

## Normal interaction

Say “Hey Nova,” wait for “ว่าไง,” and speak one command. For a sensitive command, repeat the generated challenge exactly and then say “confirm,” “yes,” “ยืนยัน,” “ใช่,” or “ตกลง” before the configured timeout. Say “cancel,” “no,” “ไม่,” or “ยกเลิก” to cancel.

Multi-step commands separated by “and then,” “then,” “แล้ว,” or “แลว” are supported when each part starts with a recognizable command. Every action is authorized separately.

## Example commands

Thai (the unaccented variants help when STT omits marks):

1. `Hey Nova` — wake the assistant.
2. `เปิด Chrome`
3. `เปิด Visual Studio Code`
4. `เปิด Spotify`
5. `เปิดโปรเจกต์ Study Platform`
6. `เปิดโปรเจกต์ Portfolio`
7. `เปิดโฟลเดอร์ C:\Projects`
8. `เปิดเว็บ github.com`
9. `ค้น Google เรื่อง Next.js`
10. `ค้นหา PyTorch transformer`
11. `ลดเสียงลงหน่อย`
12. `เพิ่มเสียง`
13. `ตั้งเสียงเป็น 50 เปอร์เซ็นต์`
14. `ปิดเสียงที`
15. `เปิดเสียง`
16. `เล่นเพลง`
17. `หยุดเพลง`
18. `เพลงถัดไป`
19. `เพลงก่อนหน้า`
20. `แคปหน้าจอ`
21. `ตอนนี้กี่โมง`
22. `ดูข้อมูลระบบ`
23. `ล็อกเครื่อง` (challenge and confirmation)
24. `ปิดเครื่อง` (disabled by default; challenge and confirmation if enabled)
25. `เปิด vscode แล้วเปิดโปรเจกต์ study platform แล้วเปิดเว็บ localhost:3000`

English:

1. `Hey Nova`
2. `Open Chrome`
3. `Launch VS Code`
4. `Start Spotify`
5. `Close Chrome`
6. `Open project Study Platform`
7. `Open project Portfolio`
8. `Open folder C:\Projects`
9. `Open website example.com`
10. `Go to localhost:3000`
11. `Search Google for PyTorch transformers`
12. `Turn the volume up`
13. `Lower the volume`
14. `Set volume to 40 percent`
15. `Mute the sound`
16. `Unmute audio`
17. `Play music`
18. `Pause music`
19. `Next track`
20. `Previous track`
21. `Take a screenshot`
22. `What time is it?`
23. `Show system info`
24. `Lock my computer` (challenge and confirmation)
25. `Open Chrome and then open website localhost:3000`

If an alias is not recognized, add it beneath the canonical app/project entry and restart Nova. Open-folder targets must already exist. URLs accept HTTP/HTTPS only. Web queries are URL-encoded rather than interpreted as commands.

## Permission behavior

- Level 0: volume, media, time, and system status; no speaker requirement.
- Level 1: app, project, folder, browser, search, and screenshot; verified owner required.
- Level 2: lock/restart/shutdown; owner plus configured challenge/confirmation.
- Level 3: destructive/general-purpose operations; disabled and absent from the executor.

`restart` and `shutdown` are disabled in `config/permissions.yaml`. Only change `enabled` after reading `SECURITY.md`. Confirmation expires after `assistant.confirmation_timeout_seconds`.

## Optional local Ollama

Install/run Ollama separately, make the configured model available, then set:

```yaml
llm:
  enabled: true
  url: http://127.0.0.1:11434
  model: llama3.2:3b
```

The LLM is consulted only when the normal parser returns `UNKNOWN`. Its output still cannot bypass Pydantic action validation, permissions, confirmation, or the executor allow-list.

