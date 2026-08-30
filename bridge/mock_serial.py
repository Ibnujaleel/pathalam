"""
mock_serial.py - Mock Hardware Generator for Testing
Simulates realistic physical fluctuations and interactive keyboard triggers.
"""

import time
import random
import threading
from bridge.sensor_state import SemanticState


class MockSerialReader:
    """Mock replacement for SerialReader allowing end-to-end software testing."""
    def __init__(self):
        self._running = False
        self._thread = None
        self._state = SemanticState()
        self._lock = threading.Lock()
        self.port_name = "MOCK_VIRTUAL"
        self.is_connected = True

        self._target_gate = 20.0
        self._target_blow = False
        self._target_light = 65.0
        self._target_switch = False
        self._target_voice = False

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True, name="MockSerialWorker")
        self._thread.start()
        print("[MockSerialReader] Virtual sensor simulator started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("[MockSerialReader] Virtual sensor simulator stopped.")

    def set_voice_trigger(self, active: bool = True, duration: float = 1.2):
        with self._lock:
            self._target_voice = active

    def trigger_action(self, action_name: str, duration_sec: float = 3.0):
        """Simulates physical action for automated testing."""
        action_name = action_name.upper()
        print(f"[MockSerial] Simulating action: {action_name} for {duration_sec}s")

        if action_name == "TOOL_BLOW":
            self._target_blow = True
        elif action_name == "TOOL_LIGHT":
            self._target_light = 5.0  # Covered
        elif action_name == "TOOL_GATE":
            self._target_gate = 85.0  # Locked
        elif action_name == "TOOL_VOICE":
            self._target_voice = True

        def reset_after():
            time.sleep(duration_sec)
            self._target_blow = False
            self._target_light = 65.0
            self._target_gate = 20.0
            self._target_voice = False

        threading.Thread(target=reset_after, daemon=True).start()

    def _worker(self):
        while self._running:
            now = time.time()
            with self._lock:
                # Add realistic noise
                gate = max(0.0, min(180.0, self._target_gate + random.gauss(0, 0.5)))
                light = max(0.0, min(100.0, self._target_light + random.gauss(0, 1.0)))
                self._state = SemanticState(
                    gate_angle=gate,
                    is_blowing=self._target_blow,
                    light_pct=light,
                    switch_on=self._target_switch,
                    is_voice_active=self._target_voice,
                    raw_pot=int(gate * (4095.0 / 180.0)),
                    raw_mq3=2800 if self._target_blow else 500,
                    raw_ldr=200 if light < 20 else 2200,
                    raw_sw=1 if self._target_switch else 0,
                    timestamp=now
                )
            time.sleep(0.033)

    def get_state(self) -> SemanticState:
        with self._lock:
            return self._state
