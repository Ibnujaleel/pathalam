/*
 * sensor_reader.ino - Physical Sensor Telemetry Stream for Maveli AI Installation
 *
 * Hardware Map:
 *   - Potentiometer: Pin A0 (or GPIO 32 on ESP32) -> pot (0 - 1023)
 *   - MQ-3 Breath:   Pin A1 (or GPIO 34 on ESP32) -> mq3 (0 - 1023)
 *   - LDR Light:     Pin A2 (or GPIO 35 on ESP32) -> ldr (0 - 1023)
 *   - START Switch:  Pin 2  (or GPIO 25 on ESP32) -> sw  (0 / 1, INPUT_PULLUP)
 *
 * Output: 20-30 Hz single-line JSON format:
 *   {"pot":512,"mq3":320,"ldr":800,"sw":1}
 */

#include <Arduino.h>

#define PIN_POT  A0  // 32 on ESP32
#define PIN_MQ3  A1  // 34 on ESP32
#define PIN_LDR  A2  // 35 on ESP32
#define PIN_SW   2   // 25 on ESP32

void setup() {
  Serial.begin(115200);
  pinMode(PIN_SW, INPUT_PULLUP);
  delay(500);
}

void loop() {
  int pot = analogRead(PIN_POT);
  int mq3 = analogRead(PIN_MQ3);
  int ldr = analogRead(PIN_LDR);
  int sw  = (digitalRead(PIN_SW) == LOW) ? 1 : 0; // Active-low button

  Serial.print("{\"pot\":"); Serial.print(pot);
  Serial.print(",\"mq3\":"); Serial.print(mq3);
  Serial.print(",\"ldr\":"); Serial.print(ldr);
  Serial.print(",\"sw\":");  Serial.print(sw);
  Serial.println("}");

  delay(33); // ~30 Hz stream
}
