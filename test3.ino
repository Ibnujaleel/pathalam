/*
 * ============================================================
 * TEST 3 — LDR + APERTURE WHEEL
 * ============================================================
 *
 * Hardware:
 *
 * LDR voltage-divider output -> GPIO35
 *
 * Suggested divider:
 *
 * 3.3V
 *  |
 * [LDR]
 *  |
 *  +---------- GPIO35
 *  |
 * [10k]
 *  |
 * GND
 *
 * Test:
 * 1. Keep sun/core LED OFF initially.
 * 2. Rotate the aperture disc slowly from closed -> open.
 * 3. Rotate back from open -> closed.
 *
 * PASS:
 * - Reading changes smoothly.
 * - Full movement produces a clear range.
 * - No excessive random jumps.
 *
 * ============================================================
 */

const int LDR_PIN = 35;

const int ADC_MAX = 4095;


// ------------------------------------------------------------
// Tracking values
// ------------------------------------------------------------

int minRaw = ADC_MAX;
int maxRaw = 0;

int previousRaw = 0;


// ------------------------------------------------------------
// Simple smoothing
// ------------------------------------------------------------

float filteredRaw = 0.0;

const float FILTER_ALPHA = 0.20;


// ------------------------------------------------------------
// Setup
// ------------------------------------------------------------

void setup()
{
  Serial.begin(115200);

  delay(1000);

  analogReadResolution(12);

  Serial.println();
  Serial.println("========================================");
  Serial.println("       LDR + APERTURE WHEEL TEST");
  Serial.println("========================================");

  Serial.println();
  Serial.println("GPIO35 = LDR divider output");

  Serial.println();
  Serial.println("Start with aperture CLOSED.");
  Serial.println();

  delay(1000);

  int initial = analogRead(LDR_PIN);

  filteredRaw = initial;
  previousRaw = initial;

  Serial.print("Initial raw value: ");
  Serial.println(initial);

  Serial.println();
  Serial.println("Now slowly rotate:");
  Serial.println("CLOSED -> OPEN -> CLOSED");
  Serial.println();
}


// ------------------------------------------------------------
// Loop
// ------------------------------------------------------------

void loop()
{
  // ----------------------------------------------------------
  // Raw ADC
  // ----------------------------------------------------------

  int raw = analogRead(LDR_PIN);


  // ----------------------------------------------------------
  // Update observed range
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
  // Voltage
  // ----------------------------------------------------------

  float voltage =
      (filteredRaw / ADC_MAX) * 3.3;


  // ----------------------------------------------------------
  // Percentage of ADC range
  // ----------------------------------------------------------

  float percentage =
      (filteredRaw / ADC_MAX) * 100.0;


  // ----------------------------------------------------------
  // Change from previous reading
  // ----------------------------------------------------------

  float change =
      filteredRaw - previousRaw;

  previousRaw = filteredRaw;


  // ----------------------------------------------------------
  // Serial output
  // ----------------------------------------------------------

  Serial.print("Raw=");
  Serial.print(raw);

  Serial.print(" | Filtered=");
  Serial.print(filteredRaw, 1);

  Serial.print(" | Voltage=");
  Serial.print(voltage, 3);

  Serial.print(" V");

  Serial.print(" | Light=");
  Serial.print(percentage, 1);

  Serial.print("%");

  Serial.print(" | Change=");
  Serial.print(change, 1);

  Serial.print(" | Min=");
  Serial.print(minRaw);

  Serial.print(" | Max=");
  Serial.println(maxRaw);


  delay(100);
}