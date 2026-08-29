പാതാള കാവൽ (Pātāḷa Kāval) — The Underworld Guard
A Physical AI Installation for the TinkerHub Physical AI Hackathon — Onam Edition.

According to legend, King Mahabali visits Kerala once a year on Thiruvonam. In this physical game installation, the player steps into Mahabali's shoes for a 3-minute shift to manage the daily operations and hazards of the Underworld (Pātāḷam) so the King can visit his people. You are guided (and mercilessly mocked) by Maveli AI, a sarcastic, spectacles-wearing Underworld office assistant delivering real-time Malayalam commentary.

System Architecture
The project is built on a zero-latency "Sense → Think → Act" pipeline:

Layer 1: Perception & Edge (C++ / ESP32): Reads physical sensors (thermistor, LDR, potentiometer, mic) and streams normalized telemetry over USB Serial at 115200 baud.

Layer 2: Local Arbiter & Rule Engine (Python): A deterministic state machine evaluating pass/fail criteria in <10ms. It drives a custom UI/UX frontend dashboard to visualize the Stability Meter and triggers local cached audio for instant feedback.

Layer 3: Cognition & Voice (Gemini API / Local Gemma): Asynchronously generates contextual, comedic Malayalam roasts based on player telemetry, converting it to speech without blocking the core game loop.

Hardware Setup & BOM
Microcontroller: ESP32 Development Board

Sensors:

10k NTC Glass Bead Thermistor (Furnace pipe)

5mm LDR GL5528 (Light blocking box)

10k Linear Potentiometer - B10K (Gate control hinge)

MAX4466 Electret Mic Module (Mantra chanting pot)

Passives & Protection: 10kΩ resistors (x2 for voltage dividers), 0.1µF ceramic capacitors (x2 for hardware debouncing/smoothing), 10µF-100µF electrolytic capacitor (ESP32 power rail), 330Ω resistor (LED data line).

UI / Actuators: 60mm Arcade Button, 1m WS2812B NeoPixel Strip.

Fabrication: Custom 3D-printed mounts for the mouthpiece, LDR shadow housing, potentiometer hinge, and mic isolator.

Software Installation & Execution
Clone the Repository:

Bash
git clone https://github.com/yourusername/patala-kaval.git
cd patala-kaval
Install Python Dependencies:

Bash
pip install pynput pyserial google-genai
Configure the AI Engine:

Cloud (Gemini): Set your API key in your environment variables: export GEMINI_API_KEY="your-api-key"

Local (Gemma 2): Ensure Ollama is installed locally and the Gemma 2 model is pulled and running in the background.

Run the Game Engine:

Bash
python src/arbiter_engine.py
Gameplay Mechanics
Players begin with 100% Underworld Stability. Failing tasks deducts 10%, while passing restores 10%. The game features 10 escalating tasks ranging from blowing into a physical pipe to cool the furnace, to chanting mantras, to multitasking across multiple physical stations simultaneously. A "കരുണ" (Mercy Call) button allows players to skip a single failing task at the cost of a permanent 15% reduction to their maximum stability cap.

This is a Hackathon Project Developed by Team Rivrr Tech.