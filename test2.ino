/*pass
 * ============================================================
 * TEST 2 — MQ-3 BREATH SENSOR
 * ============================================================
 *
 * CONNECTION:
 *
 * MQ-3 VCC -> ESP32 3.3V
 * MQ-3 GND -> ESP32 GND
 * MQ-3 AO  -> ESP32 GPIO34
 *
 * IMPORTANT:
 * - Use AO, NOT DO.
 * - Let sensor warm up before judging results.
 *
 * PASS:
 * 1. Reading is reasonably stable at rest.
 * 2. Blowing produces a repeatable change.
 * 3. Reading trends back toward baseline after stopping.
 * ============================================================
 */

const int MQ3_PIN = 34;

void setup()
{
  Serial.begin(115200);

  delay(1000);

  analogReadResolution(12);

  Serial.println();
  Serial.println("========================================");
  Serial.println("          MQ-3 SENSOR TEST");
  Serial.println("========================================");

  Serial.println();
  Serial.println("Wiring:");
  Serial.println("MQ-3 VCC -> 3.3V");
  Serial.println("MQ-3 GND -> GND");
  Serial.println("MQ-3 AO  -> GPIO34");
  Serial.println();

  Serial.println("Allowing MQ-3 to warm up...");
  Serial.println("Do not blow yet.");
  Serial.println();

  unsigned long start = millis();

  while (millis() - start < 180000)
  {
    unsigned long elapsed = (millis() - start) / 1000;
    unsigned long remaining = 180 - elapsed;

    int raw = analogRead(MQ3_PIN);

    Serial.print("Warmup: ");
    Serial.print(elapsed);
    Serial.print(" s | Remaining: ");
    Serial.print(remaining);
    Serial.print(" s | Raw: ");
    Serial.println(raw);

    delay(1000);
  }

  Serial.println();
  Serial.println("========================================");
  Serial.println("WARMUP COMPLETE");
  Serial.println("Now observe the baseline.");
  Serial.println("Then blow gently into the sensor.");
  Serial.println("========================================");
  Serial.println();
}


void loop()
{
  int raw = analogRead(MQ3_PIN);

  float voltage = (raw / 4095.0) * 3.3;

  Serial.print("MQ3 raw     : ");
  Serial.print(raw);

  Serial.print("    Voltage : ");
  Serial.print(voltage, 3);

  Serial.println(" V");

  delay(100);
}