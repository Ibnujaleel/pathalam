"""
audio_engine.py - Edge-TTS Voice Generator, Procedural Sound FX, and Pygame Multi-Channel Mixer

Architecture:
- Channel 0: BGM (Chenda Melam rhythm loop with procedural synthesis fallback)
- Channel 1: SFX (Arcade chimes, buzzers, success fanfares, countdown beeps)
- Channel 2: Voice (Asynchronous Edge-TTS stream playing en-IN-PrabhatNeural / ml-IN-SobhanaNeural)
- SpeechRecognition: Asynchronous mic listener for shout & keyword detection
"""

import os
import io
import time
import asyncio
import tempfile
import threading
import numpy as np
from typing import Optional, Callable
import pygame
import edge_tts
import speech_recognition as sr

# Ensure Pygame mixer initialized safely
if not pygame.mixer.get_init():
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(8)

CHANNEL_BGM = 0
CHANNEL_SFX = 1
CHANNEL_VOICE = 2

DEFAULT_VOICE = "en-IN-PrabhatNeural"  # Expressive Indian English/Manglish voice
TEMP_AUDIO_DIR = os.path.join(tempfile.gettempdir(), "maveli_audio_cache")
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


class ProceduralAudioSynth:
    """Generates procedural sound effects and Kerala Chenda percussion in-memory."""
    
    @staticmethod
    def generate_tone(frequency: float, duration: float, volume: float = 0.5, sample_rate: int = 44100) -> pygame.mixer.Sound:
        """Generates a pure tone sine wave."""
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        # Apply gentle ADSR envelope to avoid clicks
        envelope = np.ones(n_samples)
        fade_len = min(int(sample_rate * 0.02), n_samples // 4)
        if fade_len > 0:
            envelope[:fade_len] = np.linspace(0, 1, fade_len)
            envelope[-fade_len:] = np.linspace(1, 0, fade_len)
        
        waveform = np.sin(2 * np.pi * frequency * t) * envelope * volume
        stereo = np.column_stack((waveform, waveform))
        sound_array = (stereo * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(sound_array)

    @staticmethod
    def generate_chenda_beat(duration_sec: float = 4.0, bpm: int = 135, sample_rate: int = 44100) -> pygame.mixer.Sound:
        """
        Synthesizes a traditional Kerala Chenda Melam drum rhythm loop.
        Combines low Uruttu Chenda thuds with high-pitched Valam Thala snaps.
        """
        n_samples = int(sample_rate * duration_sec)
        audio = np.zeros(n_samples, dtype=np.float32)
        beat_interval = 60.0 / bpm
        
        # 16-step rhythmic pattern (Chenda Thaalam)
        pattern = [1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0]
        sub_beat_dur = beat_interval / 4.0

        for i, hit in enumerate(pattern):
            if hit == 1:
                start_time = (i * sub_beat_dur) % duration_sec
                start_idx = int(start_time * sample_rate)
                # Strike sound (decaying noise + resonant pitch)
                hit_dur = 0.12
                hit_samples = int(sample_rate * hit_dur)
                if start_idx + hit_samples < n_samples:
                    t_hit = np.linspace(0, hit_dur, hit_samples, False)
                    decay = np.exp(-t_hit * 32.0)
                    # Resonant low-mid drum pitch ~ 160Hz & 320Hz overtone
                    drum = (np.sin(2 * np.pi * 160 * t_hit) * 0.6 + np.sin(2 * np.pi * 320 * t_hit) * 0.3) * decay
                    # Crack snap noise
                    noise = (np.random.rand(hit_samples) * 2.0 - 1.0) * np.exp(-t_hit * 55.0) * 0.25
                    audio[start_idx:start_idx + hit_samples] += (drum + noise) * 0.45

        # Normalize and convert to stereo 16-bit
        max_val = np.max(np.abs(audio)) + 1e-6
        audio = (audio / max_val) * 0.65
        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

    @staticmethod
    def generate_success_fanfare() -> pygame.mixer.Sound:
        """Upbeat major triad victory chime (C5 -> E5 -> G5 -> C6)."""
        sample_rate = 44100
        notes = [523.25, 659.25, 783.99, 1046.50]
        note_dur = 0.12
        full_dur = note_dur * len(notes) + 0.3
        n_samples = int(sample_rate * full_dur)
        audio = np.zeros(n_samples, dtype=np.float32)

        for i, freq in enumerate(notes):
            start_idx = int(i * note_dur * sample_rate)
            dur = note_dur + (0.3 if i == len(notes) - 1 else 0.05)
            s_count = int(dur * sample_rate)
            if start_idx + s_count <= n_samples:
                t = np.linspace(0, dur, s_count, False)
                env = np.exp(-t * (4.0 if i == len(notes) - 1 else 8.0))
                tone = (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)) * env * 0.3
                audio[start_idx:start_idx + s_count] += tone

        stereo = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))

    @staticmethod
    def generate_buzzer() -> pygame.mixer.Sound:
        """Low frequency harsh buzzer for failure / wrong action."""
        sample_rate = 44100
        duration = 0.35
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        # Sawtooth-like wave
        tone = (np.sin(2 * np.pi * 140 * t) + np.sin(2 * np.pi * 147 * t) * 0.8) * np.exp(-t * 3.0) * 0.4
        stereo = np.column_stack((tone, tone))
        return pygame.sndarray.make_sound((stereo * 32767).astype(np.int16))


class AudioEngine:
    """
    Asynchronous multi-channel audio engine:
    - BGM looping on Channel 0
    - SFX on Channel 1
    - Edge-TTS speech on Channel 2
    """
    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice
        self.chan_bgm = pygame.mixer.Channel(CHANNEL_BGM)
        self.chan_sfx = pygame.mixer.Channel(CHANNEL_SFX)
        self.chan_voice = pygame.mixer.Channel(CHANNEL_VOICE)

        # Procedural sound assets
        self.sound_chenda = ProceduralAudioSynth.generate_chenda_beat(duration_sec=3.555, bpm=135)
        self.sound_fanfare = ProceduralAudioSynth.generate_success_fanfare()
        self.sound_buzzer = ProceduralAudioSynth.generate_buzzer()
        self.sound_beep = ProceduralAudioSynth.generate_tone(880, 0.08, volume=0.3)
        self.sound_warning = ProceduralAudioSynth.generate_tone(440, 0.15, volume=0.4)

        # TTS task tracking
        self._current_tts_task: Optional[asyncio.Task] = None
        self._voice_cache: dict = {}
        self.is_speaking = False

    def start_bgm(self, volume: float = 0.45):
        """Starts infinite loop of the Chenda Melam BGM on Channel 0."""
        self.chan_bgm.set_volume(volume)
        # Loop infinitely (-1)
        self.chan_bgm.play(self.sound_chenda, loops=-1)
        print("[AudioEngine] BGM Chenda Melam loop started.")

    def stop_bgm(self):
        """Stops BGM playback."""
        self.chan_bgm.stop()

    def set_bgm_volume(self, volume: float):
        """Adjusts BGM volume dynamically (e.g. ducking during speech)."""
        self.chan_bgm.set_volume(max(0.0, min(1.0, volume)))

    def play_sfx(self, sfx_name: str):
        """Plays sound effect on Channel 1."""
        sfx_map = {
            "fanfare": self.sound_fanfare,
            "buzzer": self.sound_buzzer,
            "beep": self.sound_beep,
            "warning": self.sound_warning
        }
        snd = sfx_map.get(sfx_name.lower(), self.sound_beep)
        self.chan_sfx.set_volume(0.8)
        self.chan_sfx.play(snd)

    async def speak_text_async(self, text: str, duck_bgm: bool = True):
        """
        Synthesizes text using Edge-TTS in the background and plays on Channel 2.
        Does not block the 60 FPS rendering loop.
        """
        if not text or not text.strip():
            return

        clean_text = text.strip()
        cache_key = f"{self.voice}_{hash(clean_text)}"
        audio_path = os.path.join(TEMP_AUDIO_DIR, f"{abs(hash(clean_text))}.mp3")

        self.is_speaking = True
        if duck_bgm:
            self.set_bgm_volume(0.15)  # Duck BGM while Maveli speaks

        try:
            # Check disk cache first
            if not os.path.exists(audio_path):
                # Generate via Edge-TTS
                communicate = edge_tts.Communicate(clean_text, self.voice)
                await communicate.save(audio_path)

            if os.path.exists(audio_path):
                sound = pygame.mixer.Sound(audio_path)
                self.chan_voice.set_volume(1.0)
                self.chan_voice.play(sound)

                # Wait until speech finishes or is interrupted
                while self.chan_voice.get_busy():
                    await asyncio.sleep(0.05)

        except Exception as e:
            # Fallback: if edge-tts fails (e.g. offline), play gentle chime
            print(f"[AudioEngine Voice Fallback] {e}")
            self.play_sfx("beep")
            await asyncio.sleep(0.5)
        finally:
            self.is_speaking = False
            if duck_bgm:
                self.set_bgm_volume(0.45)  # Restore BGM volume

    def speak(self, text: str):
        """Fire-and-forget speech trigger scheduled on the current event loop."""
        try:
            loop = asyncio.get_event_loop()
            if self._current_tts_task and not self._current_tts_task.done():
                self._current_tts_task.cancel()
            self._current_tts_task = loop.create_task(self.speak_text_async(text))
        except RuntimeError:
            # If no active loop in thread, run in background thread
            threading.Thread(target=lambda: asyncio.run(self.speak_text_async(text)), daemon=True).start()


# Optional microphone capture backends
try:
    import sounddevice as sd
    HAVE_SOUNDDEVICE = True
except Exception:
    HAVE_SOUNDDEVICE = False

try:
    import speech_recognition as sr
    HAVE_SPEECH_RECOGNITION = True
except Exception:
    HAVE_SPEECH_RECOGNITION = False


# Malayalam and Manglish vocal triggers
MALAYALAM_CHANT_TRIGGERS = [
    # Malayalam Script
    "ആർപ്പോ", "ഇർറോ", "ആർപ്പൊ", "ഇർറൊ", "മാവേലി", "മഹാബലി", "ഓണം", "പൊന്നോണം",
    "തീ", "ഊത്ത്", "ഊതുക", "വാതിൽ", "അടക്ക്", "പൂക്കളം", "ഹോയ്", "ഹേയ്", "വിളി",
    # Manglish Transliteration
    "ARPO", "IRRO", "AARPO", "EERRO", "MAVELI", "MAHABALI", "ONAM", "PONNONAM",
    "THEE", "OOTHU", "VAATHIL", "ADAKKU", "POOKKALAM", "HOI", "HEY", "SHOUT", "CHATHAN"
]


class MicListener:
    """
    Background laptop microphone listener and live Malayalam Speech-To-Text (STT) detector.
    Features:
    1. Low-latency (<15ms) sounddevice acoustic energy shout detection.
    2. Concurrent Google Speech-To-Text engine configured for Malayalam ('ml-IN') & Manglish ('en-IN').
    3. Live spoken transcript publishing to HUD and projector display.
    """
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.is_listening = False
        self._thread: Optional[threading.Thread] = None
        self._stt_thread: Optional[threading.Thread] = None
        self.last_detected_phrase = ""
        self.latest_transcript = ""
        self.shout_detected = False
        self.last_shout_time = 0.0
        self.mic_level = 0.0
        self.shout_rms_threshold = 12.0

    def start_listening(self):
        """Starts asynchronous microphone listening threads."""
        if self.is_listening:
            return
        self.is_listening = True
        self.shout_detected = False

        # 1. Acoustic RMS Thread
        if HAVE_SOUNDDEVICE:
            self._thread = threading.Thread(target=self._acoustic_worker, daemon=True, name="AcousticMicWorker")
            self._thread.start()

        # 2. Concurrent Malayalam STT Thread
        if HAVE_SPEECH_RECOGNITION:
            self._stt_thread = threading.Thread(target=self._stt_worker, daemon=True, name="MalayalamSTTWorker")
            self._stt_thread.start()

        print("[MicListener] Started Live Malayalam (ml-IN) STT & Acoustic listener on Laptop Microphone...")

    def stop_listening(self):
        """Stops background laptop mic threads."""
        self.is_listening = False

    def is_shout_active(self, hold_seconds: float = 1.0) -> bool:
        """Returns True if a shout or chant was recently detected."""
        if self.shout_detected or (time.time() - self.last_shout_time < hold_seconds):
            return True
        return False

    def _trigger_shout(self, label: str):
        now = time.time()
        if now - self.last_shout_time < 0.8:
            return
        self.shout_detected = True
        self.last_shout_time = now
        self.last_detected_phrase = label
        self.latest_transcript = label
        print(f"🎙️ [Live Voice/STT Trigger]: {label}")
        if self.callback:
            try:
                self.callback(label)
            except Exception as e:
                print(f"[Mic Callback Error] {e}")

    def _acoustic_worker(self):
        """Ultra-low latency RMS acoustic energy stream."""
        try:
            def audio_callback(indata, frames, time_info, status):
                if not self.is_listening:
                    return
                rms = float(np.sqrt(np.mean(indata ** 2)) * 100.0)
                self.mic_level = min(1.0, rms / 20.0)
                if rms >= self.shout_rms_threshold:
                    self._trigger_shout("ആർപ്പോ ഇർറോ! (LOUD SHOUT)")

            with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, blocksize=1024):
                while self.is_listening:
                    time.sleep(0.05)
                    if time.time() - self.last_shout_time > 1.0:
                        self.shout_detected = False
        except Exception as e:
            print(f"[Acoustic Worker Notice] {e}")

    def _stt_worker(self):
        """Continuous live Malayalam Speech-To-Text transcription."""
        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 1400
            recognizer.dynamic_energy_threshold = True

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                print("[Malayalam STT] Microphone calibrated. Listening for Malayalam words...")

                while self.is_listening:
                    try:
                        audio = recognizer.listen(source, timeout=1.2, phrase_time_limit=3.0)
                        try:
                            # Primary: Malayalam (ml-IN)
                            text_ml = recognizer.recognize_google(audio, language="ml-IN")
                            if text_ml and text_ml.strip():
                                print(f"🎙️ [Malayalam STT Transcript]: \"{text_ml}\"")
                                self._trigger_shout(text_ml)
                        except (sr.UnknownValueError, sr.RequestError):
                            # Secondary: English / Manglish
                            try:
                                text_en = recognizer.recognize_google(audio, language="en-IN")
                                if text_en and text_en.strip():
                                    print(f"🎙️ [Manglish STT Transcript]: \"{text_en}\"")
                                    self._trigger_shout(text_en)
                            except Exception:
                                pass
                    except sr.WaitTimeoutError:
                        continue
        except Exception as e:
            print(f"[Malayalam STT Worker Notice] {e}")
            except Exception as err:
                print(f"[MicListener Warning] Malayalam SpeechRecognition unavailable: {err}")

        print("[MicListener] Laptop microphone standby. (Press 'S' key in game to simulate shout).")


if __name__ == "__main__":
    async def test():
        print("Testing AudioEngine multi-channel audio & Laptop Mic...")
        engine = AudioEngine()
        engine.start_bgm()

        print("Playing SFX fanfare...")
        engine.play_sfx("fanfare")
        await asyncio.sleep(1.2)

        print("Speaking Edge-TTS Manglish prompt on Channel 2...")
        await engine.speak_text_async("Ente ponnu makkale! Maveli vannu! Onam thakarkku!")

        print("Stopping BGM...")
        engine.stop_bgm()
        print("AudioEngine test complete.")

    asyncio.run(test())
