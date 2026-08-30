"""
sensor_state.py - Raw Sensor Telemetry to Semantic State Conversion
Implements rolling-window fluctuation filter for breath detection and angle/percent mapping.
"""

import time
import math
import collections
from typing import Dict, Any, Optional
from bridge.calibration import (
    POT_ADC_MIN, POT_ADC_MAX, GATE_MAX_ANGLE_DEG,
    LDR_ADC_DARK, LDR_ADC_BRIGHT,
    MQ3_BASELINE_ALPHA, MQ3_WINDOW_SIZE, BLOW_FLUCTUATION_THRESHOLD, MQ3_DELTA_THRESHOLD
)


class SemanticState:
    """Represents high-level physical state derived from hardware sensors."""
    def __init__(
        self,
        gate_angle: float = 0.0,
        is_blowing: bool = False,
        light_pct: float = 50.0,
        switch_on: bool = False,
        is_voice_active: bool = False,
        raw_pot: int = 0,
        raw_mq3: int = 0,
        raw_ldr: int = 0,
        raw_sw: int = 0,
        timestamp: Optional[float] = None
    ):
        self.gate_angle = float(gate_angle)        # 0.0 to 180.0 / 270.0 degrees
        self.is_blowing = bool(is_blowing)         # True when breath blowing is active
        self.light_pct = float(light_pct)          # 0.0% to 100.0%
        self.switch_on = bool(switch_on)           # Physical Start button state
        self.is_voice_active = bool(is_voice_active) # Laptop mic / Malayalam chant trigger
        
        self.raw_pot = int(raw_pot)
        self.raw_mq3 = int(raw_mq3)
        self.raw_ldr = int(raw_ldr)
        self.raw_sw = int(raw_sw)
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_angle": round(self.gate_angle, 1),
            "is_blowing": self.is_blowing,
            "light_pct": round(self.light_pct, 1),
            "switch_on": self.switch_on,
            "is_voice_active": self.is_voice_active,
            "raw_pot": self.raw_pot,
            "raw_mq3": self.raw_mq3,
            "raw_ldr": self.raw_ldr,
            "raw_sw": self.raw_sw,
            "timestamp": self.timestamp
        }


class SemanticStateConverter:
    """
    Tracks baseline drift, computes rolling variance for MQ-3,
    and maps raw ADC to semantic engineering units.
    """
    def __init__(self):
        self.mq3_baseline = 500.0
        self.mq3_history = collections.deque(maxlen=MQ3_WINDOW_SIZE)
        self.last_sw_state = 0
        self.voice_active_timer = 0.0

    def set_voice_trigger(self, active: bool = True, duration: float = 1.0):
        """Sets the voice chant state (from Laptop Mic)."""
        if active:
            self.voice_active_timer = time.time() + duration

    def process_raw(self, raw_data: Dict[str, Any]) -> SemanticState:
        """
        Parses raw dict (supports both compact Arduino {'pot', 'mq3', 'ldr', 'sw'}
        and verbose ESP32 JSON schema {'pot_raw', 'mq3_raw', 'ldr_raw', 'button', etc.}).
        """
        now = time.time()

        # 1. Extract raw fields with flexible schema support
        raw_pot = int(raw_data.get("pot", raw_data.get("pot_raw", 0)))
        raw_mq3 = int(raw_data.get("mq3", raw_data.get("mq3_raw", 0)))
        raw_ldr = int(raw_data.get("ldr", raw_data.get("ldr_raw", 0)))
        raw_sw  = int(raw_data.get("sw", raw_data.get("button", raw_data.get("start_event", 0))))

        # 2. Gate Angle Mapping (0.0 to GATE_MAX_ANGLE_DEG)
        pot_normalized = max(0.0, min(1.0, (raw_pot - POT_ADC_MIN) / max(1.0, (POT_ADC_MAX - POT_ADC_MIN))))
        # If pre-calculated in ESP32 firmware, prioritize it
        gate_angle = float(raw_data.get("gate_angle", pot_normalized * GATE_MAX_ANGLE_DEG))

        # 3. Light Percentage (0% Dark to 100% Bright)
        if "ldr_percent" in raw_data:
            light_pct = float(raw_data["ldr_percent"])
        else:
            denom = max(1.0, LDR_ADC_BRIGHT - LDR_ADC_DARK)
            light_pct = max(0.0, min(100.0, ((raw_ldr - LDR_ADC_DARK) / denom) * 100.0))

        # 4. MQ-3 Breath / Blow Fluctuation Detection
        self.mq3_history.append(raw_mq3)
        self.mq3_baseline += MQ3_BASELINE_ALPHA * (raw_mq3 - self.mq3_baseline)
        mq3_delta = raw_mq3 - self.mq3_baseline

        # Calculate standard deviation over rolling window
        if len(self.mq3_history) > 2:
            mean = sum(self.mq3_history) / len(self.mq3_history)
            variance = sum((x - mean) ** 2 for x in self.mq3_history) / len(self.mq3_history)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        is_blowing = (std_dev >= BLOW_FLUCTUATION_THRESHOLD) or (mq3_delta >= MQ3_DELTA_THRESHOLD)

        # 5. Switch & Voice Triggers
        switch_on = (raw_sw == 1)
        is_voice_active = (now < self.voice_active_timer) or (raw_data.get("laptop_mic", False) is True)

        return SemanticState(
            gate_angle=gate_angle,
            is_blowing=is_blowing,
            light_pct=light_pct,
            switch_on=switch_on,
            is_voice_active=is_voice_active,
            raw_pot=raw_pot,
            raw_mq3=raw_mq3,
            raw_ldr=raw_ldr,
            raw_sw=raw_sw,
            timestamp=now
        )
