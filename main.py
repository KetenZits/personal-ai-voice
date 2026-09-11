"""Personal Voice AI Assistant for Windows."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

from assistant_state import AssistantState, StateMachine
from audio.microphone import MicrophoneStream, list_input_devices
from audio.recorder import UtteranceRecorder
from audio.vad import VoiceActivityDetector
from brain.llm import OllamaClient
from brain.parser import CommandParser
from brain.permissions import ConfirmationManager, PermissionManager
from brain.replay import ChallengeResponse
from brain.router import BrainRouter
from brain.schemas import Action, AuthorizationContext
from config.loader import load_apps, load_permissions, load_projects, load_settings
from dashboard import DebugDashboard
from executor.apps import AppController
from executor.executor import ActionExecutor
from executor.projects import ProjectController
from intent.classifier import IntentClassifier
from logging_setup import configure_logging, log_event
from tts.engine import TTSEngine


class NovaAssistant:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.settings = load_settings(args.config)
        if args.no_speaker_verification:
            self.settings.speaker.enabled = False
        configure_logging(self.settings.logging.level, self.settings.logging.file, args.debug)
        self.log = logging.getLogger("nova")
        self.state = StateMachine()
        self.state.update(
            microphone=str(self.settings.audio.device or "Windows default"),
            wake_word=self.settings.wakeword.phrase,
            speaker="PENDING" if self.settings.speaker.enabled else "DISABLED",
        )
        self.dashboard = DebugDashboard(self.state, args.debug)
        classifier = IntentClassifier(
            self.settings.intent.model_path, self.settings.intent.threshold,
            self.settings.intent.allow_rule_fallback,
        )
        parser = CommandParser(classifier)
        llm = OllamaClient(self.settings.llm.url, self.settings.llm.model,
                           self.settings.llm.timeout_seconds) if self.settings.llm.enabled else None
        self.router = BrainRouter(parser, llm)
        replay = self.settings.replay_protection
        self.permissions = PermissionManager(
            load_permissions(), replay.enabled, replay.challenge_for_level,
        )
        self.confirmations = ConfirmationManager(self.settings.assistant.confirmation_timeout_seconds)
        self.challenge = ChallengeResponse()
        apps = AppController(load_apps())
        self.executor = ActionExecutor(apps, ProjectController(load_projects(), apps))
        self.tts = TTSEngine(**self.settings.tts.model_dump())
        self.transcriber = None
        self.verifier = None
        self.detector = None
        self._active_microphone: MicrophoneStream | None = None

    def initialize_models(self, need_wakeword: bool = True) -> None:
        from stt.whisper import WhisperTranscriber
        stt = self.settings.stt
        self.transcriber = WhisperTranscriber(
            model_name=stt.model, language=stt.language, device=stt.device,
            compute_type=stt.compute_type, beam_size=stt.beam_size,
        )
        if self.settings.speaker.enabled:
            from speaker.verify import SpeakerVerifier
            self.verifier = SpeakerVerifier(
                self.settings.speaker.model_path, self.settings.speaker.threshold,
                self.settings.speaker.device,
            )
        if need_wakeword:
            from wakeword.inference import create_detector
            self.detector = create_detector(
                self.settings.wakeword.backend, self.settings.wakeword.model_path,
                self.settings.wakeword.phrase, self.settings.wakeword.threshold,
                self.settings.audio.sample_rate,
            )

    def _speak(self, text: str, return_state: AssistantState = AssistantState.IDLE) -> None:
        print(f"{self.settings.assistant.name}: {text}")
        current = self.state.state
        if current != AssistantState.SPEAKING:
            self.state.transition(AssistantState.SPEAKING)
        self.tts.speak(text)
        # The input callback keeps running while TTS speaks. Drop those queued
        # frames so Nova never treats its own prompt as the user's reply.
        if self._active_microphone is not None:
            self._active_microphone.clear()
        self.state.transition(return_state)
        self.dashboard.show()

    def _record(self, frames: object) -> np.ndarray:
        cfg = self.settings.audio
        recorder = UtteranceRecorder(
            VoiceActivityDetector(cfg.sample_rate, cfg.frame_ms, cfg.vad_backend, cfg.energy_threshold),
            cfg.sample_rate, cfg.frame_ms, cfg.pre_roll_seconds, cfg.silence_seconds,
            cfg.max_command_seconds,
        )
        return recorder.record(frames)

    def _transcribe(self, audio: np.ndarray) -> str:
        if self.transcriber is None:
            raise RuntimeError("Speech-to-text model is not initialized")
        if self.settings.logging.audio_enabled:
            from audio.utils import save_wav
            save_wav(Path("data/commands") / f"command-{datetime.now():%Y%m%d-%H%M%S-%f}.wav",
                     audio, self.settings.audio.sample_rate)
        result = self.transcriber.transcribe(audio, self.settings.audio.sample_rate)
        self.state.update(transcription=result.text, stt_confidence=result.confidence)
        log_event(self.log, "STT", text=result.text, language=result.language,
                  confidence=result.confidence, duration=result.duration_seconds)
        self.dashboard.show()
        return result.text

    def _verify(self, audio: np.ndarray) -> AuthorizationContext:
        if not self.settings.speaker.enabled:
            return AuthorizationContext(speaker_verified=True)
        if self.verifier is None:
            return AuthorizationContext(speaker_verified=False)
        authorized, score = self.verifier.verify(audio, self.settings.audio.sample_rate)
        self.state.update(speaker="AUTHORIZED" if authorized else "REJECTED", speaker_score=score)
        log_event(self.log, "SPEAKER", authorized=authorized, similarity=score)
        self.dashboard.show()
        return AuthorizationContext(speaker_verified=authorized, speaker_score=score)

    def _prompt_text_or_voice(self, prompt: str, frames: object | None) -> str:
        self._speak(prompt, AssistantState.LISTENING_FOR_COMMAND)
        if frames is None:
            answer = input("> ").strip()
            self.state.transition(AssistantState.PROCESSING)
            return answer
        audio = self._record(frames)
        self.state.transition(AssistantState.PROCESSING)
        return self._transcribe(audio)

    def _authorize(self, action: Action, auth: AuthorizationContext, frames: object | None) -> bool:
        decision = self.permissions.check(action, auth)
        if decision.requires_challenge:
            challenge = self.challenge.create()
            spoken = self._prompt_text_or_voice(f"Please say {challenge.phrase}", frames)
            if not self.challenge.verify(spoken):
                self._speak("Challenge failed", AssistantState.PROCESSING)
                return False
            auth.challenge_passed = True
            decision = self.permissions.check(action, auth)
        if decision.requires_confirmation:
            pending = self.confirmations.request(action)
            answer = self._prompt_text_or_voice(f"Confirm {action.type.value}?", frames)
            if self.confirmations.respond(answer, pending.token) is None:
                self._speak("Cancelled or confirmation expired", AssistantState.PROCESSING)
                return False
            return True
        if not decision.allowed:
            self._speak(decision.reason, AssistantState.PROCESSING)
            return False
        return True

    def handle_text(self, text: str, auth: AuthorizationContext | None = None,
                    frames: object | None = None) -> list[object]:
        auth = auth or AuthorizationContext(speaker_verified=not self.settings.speaker.enabled)
        if self.state.state == AssistantState.IDLE:
            self.state.transition(AssistantState.LISTENING_FOR_COMMAND)
        if self.state.state != AssistantState.PROCESSING:
            self.state.transition(AssistantState.PROCESSING)
        plan = self.router.route(text)
        results = []
        for action in plan.actions:
            self.state.update(intent=action.type.name, intent_confidence=action.confidence,
                              last_target=action.target)
            log_event(self.log, "INTENT", intent=action.type.name, confidence=action.confidence,
                      action=action.type.value, target=action.target)
            self.dashboard.show()
            authorized = self._authorize(action, auth, frames)
            # A spoken challenge authorizes one action, not the rest of a
            # compound plan.
            auth.challenge_passed = False
            if not authorized:
                continue
            if self.state.state != AssistantState.EXECUTING:
                self.state.transition(AssistantState.EXECUTING)
            result = self.executor.execute(action)
            results.append(result)
            self.state.update(last_action=result.message)
            log_event(self.log, "EXECUTOR", action=action.type.value, target=action.target,
                      success=result.success, result=result.message, duration=result.duration_seconds)
            self.dashboard.show()
            self._speak(result.message, AssistantState.PROCESSING)
        if self.state.state != AssistantState.IDLE:
            if self.state.state == AssistantState.PROCESSING:
                self.state.transition(AssistantState.IDLE)
        return results

    def run_push_to_talk(self) -> None:
        cfg = self.settings.audio
        if self.transcriber is None:
            self.initialize_models(need_wakeword=False)
        self.state.transition(AssistantState.LISTENING_FOR_COMMAND)
        with MicrophoneStream(cfg.sample_rate, cfg.frame_ms, cfg.device) as mic:
            self._active_microphone = mic
            try:
                frames = mic.frames()
                while True:
                    input("Press Enter to record a command (Ctrl+C to stop)...")
                    mic.clear()
                    audio = self._record(frames)
                    if not audio.size:
                        print("No speech detected"); continue
                    if self.settings.speaker.enabled:
                        self.state.transition(AssistantState.VERIFYING_SPEAKER)
                    else:
                        self.state.transition(AssistantState.PROCESSING)
                    auth = self._verify(audio)
                    if not auth.speaker_verified:
                        self._speak("เสียงนี้ไม่ใช่เจ้าของเครื่อง", AssistantState.LISTENING_FOR_COMMAND)
                        continue
                    if self.state.state == AssistantState.VERIFYING_SPEAKER:
                        self.state.transition(AssistantState.PROCESSING)
                    try:
                        text = self._transcribe(audio)
                    except Exception as exc:
                        self.log.exception("STT failed")
                        self._speak(f"Speech recognition failed: {exc}", AssistantState.LISTENING_FOR_COMMAND)
                        continue
                    self.handle_text(text, auth, frames)
                    self.state.transition(AssistantState.LISTENING_FOR_COMMAND)
            finally:
                self._active_microphone = None

    def run_wakeword(self) -> None:
        cfg = self.settings.audio
        if self.transcriber is None or self.detector is None:
            self.initialize_models(need_wakeword=True)
        self.state.transition(AssistantState.LISTENING_FOR_WAKE_WORD)
        window: deque[np.ndarray] = deque(maxlen=max(1, int(2.5 * 1000 / cfg.frame_ms)))
        cooldown_until = 0.0
        with MicrophoneStream(cfg.sample_rate, cfg.frame_ms, cfg.device) as mic:
            self._active_microphone = mic
            try:
                frames = mic.frames()
                for frame in frames:
                    window.append(frame)
                    if time.monotonic() < cooldown_until:
                        continue
                    detected, score = self.detector.process_frame(frame)
                    self.state.update(wake_word=self.settings.wakeword.phrase, wake_confidence=score)
                    if not detected:
                        continue
                    log_event(self.log, "WAKEWORD", confidence=score, phrase=self.settings.wakeword.phrase)
                    # Both detector backends keep temporal state. Consume this
                    # activation once so it cannot retrigger after cooldown.
                    reset_detector = getattr(self.detector, "reset", None)
                    if callable(reset_detector):
                        reset_detector()
                    self.state.transition(AssistantState.VERIFYING_SPEAKER)
                    auth = self._verify(np.concatenate(tuple(window)))
                    if not auth.speaker_verified:
                        self._speak("เสียงนี้ไม่ใช่เจ้าของเครื่อง", AssistantState.LISTENING_FOR_WAKE_WORD)
                        window.clear()
                        cooldown_until = time.monotonic() + self.settings.wakeword.cooldown_seconds
                        continue
                    self._speak(self.settings.assistant.greeting, AssistantState.LISTENING_FOR_COMMAND)
                    command = self._record(frames)
                    if not command.size:
                        window.clear()
                        self.state.transition(AssistantState.LISTENING_FOR_WAKE_WORD)
                        cooldown_until = time.monotonic() + self.settings.wakeword.cooldown_seconds
                        continue
                    self.state.transition(AssistantState.PROCESSING)
                    try:
                        text = self._transcribe(command)
                    except Exception as exc:
                        self.log.exception("STT failed")
                        self._speak(f"Speech recognition failed: {exc}", AssistantState.LISTENING_FOR_WAKE_WORD)
                        window.clear()
                        cooldown_until = time.monotonic() + self.settings.wakeword.cooldown_seconds
                        continue
                    self.handle_text(text, auth, frames)
                    mic.clear()
                    window.clear()
                    self.state.transition(AssistantState.LISTENING_FOR_WAKE_WORD)
                    cooldown_until = time.monotonic() + self.settings.wakeword.cooldown_seconds
            finally:
                self._active_microphone = None

    def run_resilient(self, push_to_talk: bool) -> None:
        """Reopen the microphone after PortAudio/device disconnect errors."""
        runner = self.run_push_to_talk if push_to_talk else self.run_wakeword
        while True:
            try:
                runner()
                return
            except Exception as exc:
                is_audio_error = isinstance(exc, OSError) or exc.__class__.__module__.startswith("sounddevice")
                if not is_audio_error:
                    raise
                self.log.exception("Microphone failed; retrying in two seconds")
                print(f"Microphone error: {exc}. Retrying in 2 seconds...")
                self.state.reset()
                time.sleep(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-speaker-verification", action="store_true")
    parser.add_argument("--push-to-talk", action="store_true")
    parser.add_argument("--list-microphones", action="store_true")
    parser.add_argument("--text", help="Process one typed command (useful for setup/tests)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.list_microphones:
            for device in list_input_devices():
                print(device)
            return 0
        assistant = NovaAssistant(args)
        if args.text:
            assistant.handle_text(args.text, AuthorizationContext(speaker_verified=True))
        else:
            assistant.run_resilient(args.push_to_talk)
    except KeyboardInterrupt:
        print("\nNova stopped.")
    except (ImportError, FileNotFoundError, RuntimeError) as exc:
        if logging.getLogger().handlers:
            logging.getLogger("nova").error("Startup failed: %s", exc)
        print(f"Startup failed: {exc}", file=sys.stderr)
        return 2
    except Exception:
        logging.getLogger("nova").exception("Unexpected fatal error")
        return 1
    return 0


if __name__ == "__main__": raise SystemExit(main())
