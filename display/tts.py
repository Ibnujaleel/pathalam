"""
tts.py - Malayalam Text-To-Speech Audio Synthesizer
Synthesizes high-quality Malayalam spoken voice (Edge-TTS) for projection audio.
"""

import os
import asyncio
import threading
from typing import Optional

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), "audio_cache")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

MALAYALAM_VOICE = "ml-IN-MidhunNeural"  # or "ml-IN-SobhanaNeural"


class TTSEngine:
    """Handles background synthesis of Malayalam alert audio files."""
    def __init__(self, voice: str = MALAYALAM_VOICE):
        self.voice = voice
        self.is_busy = False

    def speak_async(self, text: str, output_filename: str = "alert.mp3") -> str:
        """
        Synthesizes text to an MP3 file asynchronously in a background thread.
        Returns the output filepath.
        """
        output_path = os.path.join(AUDIO_CACHE_DIR, output_filename)

        def worker():
            try:
                import edge_tts
                async def generate():
                    communicate = edge_tts.Communicate(text, self.voice)
                    await communicate.save(output_path)
                asyncio.run(generate())
            except Exception as e:
                print(f"[TTS Warning] Edge-TTS error ({e}). Web Speech API fallback will handle it in browser.")

        threading.Thread(target=worker, daemon=True).start()
        return output_path
