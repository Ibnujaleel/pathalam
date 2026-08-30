"""
calibration.py - Hardware Sensor Calibration Constants & Thresholds
Tune these values on-site based on the physical installation environment.
"""

# Potentiometer / Gate Angle Calibration
POT_ADC_MIN = 0
POT_ADC_MAX = 4095  # 1023 for 10-bit Arduino, 4095 for 12-bit ESP32
GATE_MAX_ANGLE_DEG = 180.0  # 180.0 or 270.0 degrees
GATE_LOCKED_THRESHOLD_DEG = 70.0

# LDR / Light Sensor Calibration
LDR_ADC_DARK = 350    # Covered / shaded reading
LDR_ADC_BRIGHT = 3200 # Normal ambient room reading
LIGHT_SHIELDED_THRESHOLD_PCT = 25.0 # Below this is considered "covered / shielded"

# MQ-3 Breath Sensor Calibration
# Rolling window fluctuation & baseline tracking
MQ3_BASELINE_ALPHA = 0.005
MQ3_WINDOW_SIZE = 15
BLOW_FLUCTUATION_THRESHOLD = 80.0  # Standard deviation or delta indicating active breath
MQ3_DELTA_THRESHOLD = 150.0        # Direct delta above baseline

# Switch / Button Calibration
BUTTON_DEBOUNCE_MS = 40
