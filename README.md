# 👑 Maveli AI (Pātāḷa Kāval) 60-Second Challenge
**Real-Time Interactive Hardware-Software Physical AI Arcade Game**

# 👑 Maveli AI (Pātāḷa Kāval) - Real-Time Cyber-Mythological AI Challenge

An interactive physical-computing arcade game built for the Google AI Hackathon. Combines **ESP32 30Hz JSON Telemetry**, **Low-Latency Laptop Microphone STT (Malayalam)**, **RandomForest Action Recognition**, and **Google Gemini Flash AI** for dynamic Underworld storytelling and real-time live plot commentary.

---

## 🛠️ Hardware & Pin Configuration (Pathalam BOM)

| Component | ESP32 Pin | Interface / Role | Game Action Mapped |
|---|---|---|---|
| **MQ-3 Breath Sensor** | `GPIO 34` (ADC) | Adaptive baseline & rate of rise (0-4095) | `TOOL_BLOW` / `BLOWING` (Key: <kbd>B</kbd>) |
| **5mm GL5528 LDR** | `GPIO 35` (ADC) | Ambient light & shade detection (0-4095) | `TOOL_LIGHT` / `LIGHT_COVERED` (Key: <kbd>L</kbd>) |
| **10K Potentiometer** | `GPIO 32` (ADC) | Fortress gate lock angle (0° - 90°) | `TOOL_GATE` / `GATE_LOCKED` (Key: <kbd>G</kbd>) |
| **Omron B3F Push Button** | `GPIO 25` (Digital) | Hardware Round Start & Reset (`INPUT_PULLUP`) | <kbd>SPACE</kbd> / Start Event |
| **Laptop Built-in Mic** | Host Audio | Malayalam STT (`ml-IN`) & Sound Energy | `TOOL_VOICE` / `SHOUT_MIC` (Key: <kbd>S</kbd>) |
| **ESP32 Wi-Fi** | Wi-Fi Station | SSID: `Naveen` / IP Telemetry | HUD Live Network Badge |

---

## 📡 30 Hz JSON Telemetry Format

Each serial line sent from the ESP32 at **115200 baud** is a complete, self-contained JSON object:

```json
{
  "t": 123456,
  "mq3_raw": 850,
  "mq3_normalized": 0.2075,
  "mq3_baseline": 840.2,
  "mq3_delta": 9.8,
  "mq3_rate": 14.5,
  "mq3_voltage": 0.684,
  "ldr_raw": 1900,
  "ldr_normalized": 0.4639,
  "ldr_percent": 46.39,
  "ldr_voltage": 1.531,
  "pot_raw": 2048,
  "pot_normalized": 0.5000,
  "pot_percent": 50.00,
  "pot_voltage": 1.650,
  "gate_angle": 45.00,
  "button": 0,
  "start_event": 0,
  "start_count": 0,
  "wifi_connected": 1,
  "wifi_rssi": -65,
  "wifi_channel": 6,
  "wifi_ip": "192.168.1.50"
}
```

---

## 🏗️ System Architecture

- **Perception & Edge (ESP32 C++)**: [`maveli_esp32_firmware.ino`](file:///c:/Users/Amal%20Vinayan/Downloads/GoogleAIHackathon/maveli_esp32_firmware.ino) samples the 10k NTC, GL5528 LDR, and B10K Potentiometer and broadcasts CSV `thermistor,ldr,0,gate_angle\n` at 115200 baud.
- **Hardware & Audio Bridge (Python)**: [`hardware_bridge.py`](file:///c:/Users/Amal%20Vinayan/Downloads/GoogleAIHackathon/hardware_bridge.py) handles serial auto-connection, seamlessly merges Laptop Microphone shout triggers, and provides virtual simulation fallback.
- **Acoustic & Voice Engine**: [`audio_engine.py`](file:///c:/Users/Amal%20Vinayan/Downloads/GoogleAIHackathon/audio_engine.py) provides background laptop mic listening, non-blocking Edge-TTS voice streams (`en-IN-PrabhatNeural`), Chenda Melam BGM loop, and procedural sound FX.
- **Machine Learning Classifier**: [`ml_pipeline.py`](file:///c:/Users/Amal%20Vinayan/Downloads/GoogleAIHackathon/ml_pipeline.py) runs a `RandomForestClassifier` with temporal rolling-window filtering to classify physical gestures in $<10\text{ms}$.
- **Maveli AI Brain**: [`maveli_brain.py`](file:///c:/Users/Amal%20Vinayan/Downloads/GoogleAIHackathon/maveli_brain.py) prompts local `gemma2:9b` (via `ollama.AsyncClient`) with a sarcastic, energetic King Mahabali Manglish persona and fallback catalog.
- **Arcade Display**: [`main_game.py`](file:///c:/Users/Amal%20Vinayan/Downloads/GoogleAIHackathon/main_game.py) renders a 60 FPS Kasavu Gold arcade HUD with circular countdown timer, particle effects, and live telemetry gauges.

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Start Ollama for Gemma 2:9B
```bash
ollama run gemma2:9b
```

### 3. Run the Arcade Game
```bash
python main_game.py
```

---

## 🎮 Keyboard Shortcuts & Simulation

| Action | Physical Input | Keyboard Key |
|---|---|---|
| **BLOWING** | 10k NTC Thermistor | Press <kbd>B</kbd> |
| **LIGHT_COVERED** | 5mm GL5528 LDR | Press <kbd>L</kbd> |
| **GATE_LOCKED** | B10K Potentiometer ($> 120^\circ$) | Press <kbd>G</kbd> |
| **SHOUT_MIC** | Laptop Built-in Mic / Shout | Press <kbd>S</kbd> |
| **START / RESTART** | — | Press <kbd>SPACE</kbd> or <kbd>R</kbd> |
| **QUIT** | — | Press <kbd>ESC</kbd> |
