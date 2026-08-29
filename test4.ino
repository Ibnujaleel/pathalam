/*
 * ============================================================
 * TEST 4 — 10K LINEAR GATE POTENTIOMETER
 * ============================================================
 *
 * CONNECTION:
 *
 * POT outer pin 1 -> 3.3V
 * POT outer pin 2 -> GND
 * POT middle pin -> GPIO32
 *
 * PASS:
 * - Reading changes smoothly
 * - No sudden jumps
 * - No dead zones
 * - Repeated movement gives repeatable values
 *
 * The project maps the potentiometer to gate angle:
 *
 * ADC 0      -> ~0 degrees
 * ADC 4095   -> ~90 degrees
 *
 * ============================================================
 */

const int POT_PIN = 32;

const int ADC_MAX = 4095;

float filteredRaw = 0.0;

const float FILTER_ALPHA = 0.20;

int minRaw = ADC_MAX;
int maxRaw = 0;

void setup()
{
  Serial.begin(115200);

  delay(1000);

  analogReadResolution(12);

  Serial.println();
  Serial.println("========================================");
  Serial.println("       GATE POTENTIOMETER TEST");
  Serial.println("========================================");

  Serial.println();
  Serial.println("GPIO32 = potentiometer wiper");
  Serial.println("3.3V   = potentiometer outer pin");
  Serial.println("GND    = potentiometer outer pin");

  Serial.println();
  Serial.println("Turn the gate slowly:");
  Serial.println("CLOSED -> OPEN -> CLOSED");
  Serial.println();

  int initial = analogRead(POT_PIN);

  filteredRaw = initial;

  Serial.print("Initial ADC = ");
  Serial.println(initial);

  Serial.println();
}

void loop()
{
  // ----------------------------------------------------------
  // Read ADC
  // ----------------------------------------------------------

  int raw = analogRead(POT_PIN);

  // ----------------------------------------------------------
  // Track actual range
  // ----------------------------------------------------------

  if (raw < minRaw)
    minRaw = raw;

  if (raw > maxRaw)
    maxRaw = raw;

  // ----------------------------------------------------------
  // Filter
  // ----------------------------------------------------------

  filteredRaw =
      FILTER_ALPHA * raw +
      (1.0 - FILTER_ALPHA) * filteredRaw;

  // ----------------------------------------------------------
  // Convert to voltage
  // ----------------------------------------------------------

  float voltage =
      (filteredRaw / ADC_MAX) * 3.3;

  // ----------------------------------------------------------
  // Convert to gate angle
  // ----------------------------------------------------------

  float gateAngle =
      (filteredRaw / ADC_MAX) * 90.0;

  // ----------------------------------------------------------
  // Output
  // ----------------------------------------------------------

  Serial.print("Raw=");
  Serial.print(raw);

  Serial.print(" | Filtered=");
  Serial.print(filteredRaw, 1);

  Serial.print(" | Voltage=");
  Serial.print(voltage, 3);

  Serial.print(" V");

  Serial.print(" | Gate=");
  Serial.print(gateAngle, 1);

  Serial.print(" deg");

  Serial.print(" | Min=");
  Serial.print(minRaw);

  Serial.print(" | Max=");
  Serial.println(maxRaw);

  delay(100);
}