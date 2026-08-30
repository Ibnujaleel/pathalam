"""
main.py - Maveli AI Installation Orchestrator
Connects Serial Bridge -> Game State Manager -> Gemini AI Client -> Web Projector Display.
"""

import sys
import time
import asyncio
import threading
from typing import Optional

from bridge.serial_reader import SerialReader
from bridge.mock_serial import MockSerialReader
from game.state_manager import GameStateManager
from ai.maveli_client import MaveliClient
from display.server import DisplayServer, broadcast_state
from audio_engine import MicListener


class InstallationOrchestrator:
    """
    Main orchestration loop for the physical interactive installation.
    """
    def __init__(self, use_mock_hardware: bool = False, http_port: int = 8000):
        self.use_mock_hardware = use_mock_hardware
        self.http_port = http_port

        # 1. Serial Bridge
        if self.use_mock_hardware:
            self.reader = MockSerialReader()
        else:
            self.reader = SerialReader()

        # 2. Laptop Microphone Acoustic Listener
        self.mic = MicListener(callback=self._on_mic_shout)

        # 3. Game & AI Subsystems
        self.game = GameStateManager(session_duration_sec=60.0)
        self.ai = MaveliClient()

        # 4. Zero-Dependency Display Server
        self.display_server = DisplayServer(host="0.0.0.0", port=self.http_port)
        from display.server import set_voice_action_callback
        set_voice_action_callback(self._on_mic_shout)

        self.running = False
        self._is_generating_incident = False

    def _on_mic_shout(self, phrase: str):
        print(f"[Installation] Malayalam Chant / Shout Detected: {phrase}")
        self.reader.set_voice_trigger(True, duration=1.2)

    def start(self):
        print("=" * 65)
        print("   👑 MAVELI AI (PĀTĀḶA KĀVAL) - INSTALLATION ORCHESTRATOR")
        print("=" * 65)

        # Start hardware & audio
        self.reader.start()
        self.mic.start_listening()
        self.display_server.start()
        self.running = True

        print(f"[DisplayServer] Projector Display active at: http://localhost:{self.http_port}")
        print("-----------------------------------------------------------------")
        print("Controls:")
        print("  - Physical START Button (GPIO 25) or [SPACE]: Start / Restart")
        print("  - Physical MQ-3 Breath (GPIO 34)   or [B]: Blow Hearth")
        print("  - Physical GL5528 LDR (GPIO 35)    or [L]: Cover Light")
        print("  - Physical 10K Pot (GPIO 32)       or [G]: Lock Gate")
        print("  - Laptop Mic Chant                 or [S]: Shout Cry")
        print("-----------------------------------------------------------------\n")

    def stop(self):
        self.running = False
        self.reader.stop()
        self.mic.stop_listening()
        print("[Installation] Shutdown complete.")

    async def run_loop(self):
        self.start()

        # Initial game start
        self.game.start_game()
        await self._trigger_ai_crisis()

        while self.running:
            # 1. Fetch live semantic state from hardware
            semantic_state = self.reader.get_state()

            # 2. Update game session & crisis deadlines
            events = self.game.update(semantic_state)

            # Handle Sarcastic Reaction on Success / Fail
            if events.get("action_succeeded"):
                asyncio.create_task(self._trigger_reaction("SUCCESS"))
            elif events.get("crisis_failed"):
                asyncio.create_task(self._trigger_reaction("FAIL"))

            # 3. If a new crisis is required, fetch from Gemini AI asynchronously
            if events.get("needs_new_incident") and not self._is_generating_incident and self.game.state == GameStateManager.STATE_PLAYING:
                asyncio.create_task(self._trigger_ai_crisis())

            # 4. Prepare broadcast state packet for projector overlay
            broadcast_payload = {
                **self.game.to_dict(),
                "sensors": semantic_state.to_dict(),
                "reaction_text": getattr(self, "current_reaction_text", "")
            }

            # 5. Broadcast to connected projector browser(s)
            await broadcast_state(broadcast_payload)

            await asyncio.sleep(0.033)  # 30 Hz loop

    async def _trigger_reaction(self, outcome: str):
        if not self.game.active_incident:
            return
        inc_title = self.game.active_incident.incident_title
        time_spent = time.time() - self.game.incident_start_time

        loop = asyncio.get_running_loop()
        reaction = await loop.run_in_executor(
            None,
            self.ai.generate_reaction,
            inc_title,
            outcome,
            time_spent,
            self.game.stability_hp
        )
        self.current_reaction_text = reaction
        print(f"\n👑 [Maveli's Sarcastic Reaction ({outcome})]: {reaction}\n")

    async def _trigger_ai_crisis(self):
        if self._is_generating_incident:
            return
        self._is_generating_incident = True
        self.current_reaction_text = ""

        st = self.reader.get_state()
        recent_tools_str = self.game.get_tool_history_str()

        # Run Gemini API request in thread pool to avoid blocking the 30Hz loop
        loop = asyncio.get_running_loop()
        incident = await loop.run_in_executor(
            None,
            self.ai.generate_incident,
            self.game.time_left,
            self.game.stability_hp,
            recent_tools_str,
            st.gate_angle,
            st.light_pct,
            st.is_blowing
        )

        self.game.set_new_incident(incident)
        self._is_generating_incident = False


if __name__ == "__main__":
    use_mock = "--mock" in sys.argv

    orchestrator = InstallationOrchestrator(use_mock_hardware=use_mock)
    try:
        asyncio.run(orchestrator.run_loop())
    except KeyboardInterrupt:
        orchestrator.stop()
        print("\nInstallation stopped by user.")
