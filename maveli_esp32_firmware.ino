/*
============================================================
                 PATHAL KAVAL
          FINAL ESP32 JSON INTERFACE
============================================================

CURRENT HARDWARE
------------------------------------------------------------

MQ-3 Alcohol/Breath Sensor
    AO  -> GPIO34
    GND -> GND

LDR
    OUT -> GPIO35

10K Potentiometer
    Wiper -> GPIO32
    Outer -> 3.3V
    Outer -> GND

Omron B3F START Button
    One side -> GPIO25
    Other side -> GND
    INPUT_PULLUP

MICROPHONE
    NOT USED


============================================================
WIFI
============================================================

SSID     : Naveen
Password : 12341234


============================================================
SERIAL
============================================================

115200 baud

Telemetry:
30 Hz

Every line is ONE JSON object.

The Python/game software can read:

    serial.readline()

and then:

    json.loads(line)


============================================================
IMPORTANT
============================================================

The ESP32 does NOT run the game.

The ESP32 only:

1. Reads sensors
2. Filters/derives useful features
3. Detects button edge
4. Maintains MQ-3 adaptive baseline
5. Sends telemetry

Python/game engine handles:

- 120-second game clock
- events
- scoring
- AI
- Gemini
- HUD
- game decisions


============================================================
*/


#include <Arduino.h>
#include <WiFi.h>


// ============================================================
// PIN MAP
// ============================================================

#define MQ3_PIN       34
#define LDR_PIN       35
#define POT_PIN       32
#define BUTTON_PIN    25


// ============================================================
// WIFI
// ============================================================

const char* WIFI_SSID =
  "Naveen";

const char* WIFI_PASSWORD =
  "12341234";


// ============================================================
// TIMING
// ============================================================

// Final project target = 30 Hz

const unsigned long SAMPLE_INTERVAL_MS =
  33;


// Wi-Fi reconnect interval

const unsigned long WIFI_RECONNECT_INTERVAL_MS =
  10000;


// Button debounce

const unsigned long BUTTON_DEBOUNCE_MS =
  30;


// ============================================================
// MQ-3 BASELINE
// ============================================================

/*
   Slow adaptive baseline.

   The project specifically calls for rate-of-rise rather
   than depending on absolute MQ-3 voltage because the
   baseline changes with environment and sensor pre-heating.
*/

float mq3Baseline = 0.0;

float mq3PreviousRaw = 0.0;

unsigned long mq3PreviousTime = 0;


// Slow baseline tracking

const float MQ3_BASELINE_ALPHA =
  0.005;


// ============================================================
// BUTTON
// ============================================================

int buttonLastReading =
  HIGH;

int buttonStableState =
  HIGH;

unsigned long buttonLastChangeTime =
  0;

unsigned long startCount =
  0;


// One-shot event

bool startEvent =
  false;


// ============================================================
// TIMERS
// ============================================================

unsigned long lastSampleTime =
  0;

unsigned long lastWiFiAttempt =
  0;


// ============================================================
// WIFI CONNECT
// ============================================================

void connectWiFi()
{
  WiFi.mode(WIFI_STA);

  WiFi.disconnect();

  delay(100);

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );


  unsigned long start =
    millis();


  while (
    WiFi.status() != WL_CONNECTED &&
    millis() - start < 15000
  )
  {
    delay(250);
  }


  lastWiFiAttempt =
    millis();
}


// ============================================================
// BUTTON PROCESSING
// ============================================================

void processButton()
{
  unsigned long now =
    millis();


  int reading =
    digitalRead(BUTTON_PIN);


  // Detect physical transition

  if (
    reading != buttonLastReading
  )
  {
    buttonLastChangeTime =
      now;
  }


  // Debounce

  if (
    now - buttonLastChangeTime
    >= BUTTON_DEBOUNCE_MS
  )
  {
    if (
      reading != buttonStableState
    )
    {
      buttonStableState =
        reading;


      // -----------------------------------------------
      // BUTTON PRESSED
      // -----------------------------------------------

      if (
        buttonStableState == LOW
      )
      {
        startEvent =
          true;

        startCount++;
      }
    }
  }


  buttonLastReading =
    reading;
}


// ============================================================
// INITIAL MQ-3 CALIBRATION
// ============================================================

void calibrateMQ3()
{
  long total =
    0;


  const int samples =
    100;


  for (
    int i = 0;
    i < samples;
    i++
  )
  {
    total +=
      analogRead(MQ3_PIN);


    delay(20);
  }


  mq3Baseline =
    (float)total /
    samples;


  mq3PreviousRaw =
    mq3Baseline;


  mq3PreviousTime =
    millis();
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(115200);

  delay(1000);


  // ----------------------------------------------------------
  // ADC
  // ----------------------------------------------------------

  analogReadResolution(12);


  // ----------------------------------------------------------
  // BUTTON
  // ----------------------------------------------------------

  pinMode(
    BUTTON_PIN,
    INPUT_PULLUP
  );


  // ----------------------------------------------------------
  // WIFI
  // ----------------------------------------------------------

  connectWiFi();


  // ----------------------------------------------------------
  // MQ-3
  // ----------------------------------------------------------

  calibrateMQ3();


  // ----------------------------------------------------------
  // TIMERS
  // ----------------------------------------------------------

  lastSampleTime =
    millis();

  lastWiFiAttempt =
    millis();
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  unsigned long now =
    millis();


  // ==========================================================
  // BUTTON
  // ==========================================================

  processButton();


  // ==========================================================
  // WIFI RECONNECTION
  // ==========================================================

  if (
    WiFi.status() != WL_CONNECTED
  )
  {
    if (
      now - lastWiFiAttempt
      >= WIFI_RECONNECT_INTERVAL_MS
    )
    {
      connectWiFi();
    }
  }


  // ==========================================================
  // 30 Hz TELEMETRY
  // ==========================================================

  if (
    now - lastSampleTime
    < SAMPLE_INTERVAL_MS
  )
  {
    return;
  }


  lastSampleTime =
    now;


  // ==========================================================
  // MQ-3
  // ==========================================================

  int mq3Raw =
    analogRead(MQ3_PIN);


  // Time since previous MQ-3 reading

  float dt =
    (
      now -
      mq3PreviousTime
    ) / 1000.0;


  if (dt <= 0)
  {
    dt = 0.001;
  }


  mq3PreviousTime =
    now;


  // ----------------------------------------------------------
  // ADAPTIVE BASELINE
  // ----------------------------------------------------------

  mq3Baseline =
    mq3Baseline +
    MQ3_BASELINE_ALPHA *
    (
      (float)mq3Raw -
      mq3Baseline
    );


  // ----------------------------------------------------------
  // DELTA FROM BASELINE
  // ----------------------------------------------------------

  float mq3Delta =
    (float)mq3Raw -
    mq3Baseline;


  // ----------------------------------------------------------
  // RATE OF RISE
  // ----------------------------------------------------------

  float mq3Rate =
    (
      (float)mq3Raw -
      mq3PreviousRaw
    ) / dt;


  mq3PreviousRaw =
    mq3Raw;


  // ----------------------------------------------------------
  // MQ-3 NORMALIZED
  // ----------------------------------------------------------

  float mq3Normalized =
    mq3Raw / 4095.0;


  // ==========================================================
  // LDR
  // ==========================================================

  int ldrRaw =
    analogRead(LDR_PIN);


  float ldrNormalized =
    ldrRaw / 4095.0;


  float ldrPercent =
    ldrNormalized * 100.0;


  float ldrVoltage =
    ldrNormalized * 3.3;


  // ==========================================================
  // POTENTIOMETER
  // ==========================================================

  int potRaw =
    analogRead(POT_PIN);


  float potNormalized =
    potRaw / 4095.0;


  float potPercent =
    potNormalized * 100.0;


  float potVoltage =
    potNormalized * 3.3;


  // ----------------------------------------------------------
  // GATE ANGLE
  // ----------------------------------------------------------

  float gateAngle =
    potNormalized * 90.0;


  // ==========================================================
  // BUTTON
  // ==========================================================

  int buttonState =
    (
      buttonStableState == LOW
    )
    ? 1
    : 0;


  // ==========================================================
  // WIFI
  // ==========================================================

  int wifiConnected =
    (
      WiFi.status() == WL_CONNECTED
    )
    ? 1
    : 0;


  // ==========================================================
  // JSON START
  // ==========================================================

  Serial.print("{");


  // ==========================================================
  // TIMESTAMP
  // ==========================================================

  Serial.print("\"t\":");
  Serial.print(now);


  // ==========================================================
  // MQ-3
  // ==========================================================

  Serial.print(",\"mq3_raw\":");
  Serial.print(mq3Raw);


  Serial.print(",\"mq3_normalized\":");
  Serial.print(
    mq3Normalized,
    4
  );


  Serial.print(",\"mq3_baseline\":");
  Serial.print(
    mq3Baseline,
    2
  );


  Serial.print(",\"mq3_delta\":");
  Serial.print(
    mq3Delta,
    2
  );


  Serial.print(",\"mq3_rate\":");
  Serial.print(
    mq3Rate,
    2
  );


  Serial.print(",\"mq3_voltage\":");
  Serial.print(
    mq3Raw / 4095.0 * 3.3,
    3
  );


  // ==========================================================
  // LDR
  // ==========================================================

  Serial.print(",\"ldr_raw\":");
  Serial.print(ldrRaw);


  Serial.print(",\"ldr_normalized\":");
  Serial.print(
    ldrNormalized,
    4
  );


  Serial.print(",\"ldr_percent\":");
  Serial.print(
    ldrPercent,
    2
  );


  Serial.print(",\"ldr_voltage\":");
  Serial.print(
    ldrVoltage,
    3
  );


  // ==========================================================
  // POTENTIOMETER
  // ==========================================================

  Serial.print(",\"pot_raw\":");
  Serial.print(potRaw);


  Serial.print(",\"pot_normalized\":");
  Serial.print(
    potNormalized,
    4
  );


  Serial.print(",\"pot_percent\":");
  Serial.print(
    potPercent,
    2
  );


  Serial.print(",\"pot_voltage\":");
  Serial.print(
    potVoltage,
    3
  );


  Serial.print(",\"gate_angle\":");
  Serial.print(
    gateAngle,
    2
  );


  // ==========================================================
  // BUTTON
  // ==========================================================

  Serial.print(",\"button\":");
  Serial.print(buttonState);


  Serial.print(",\"start_event\":");
  Serial.print(
    startEvent ? 1 : 0
  );


  Serial.print(",\"start_count\":");
  Serial.print(startCount);


  // ==========================================================
  // WIFI
  // ==========================================================

  Serial.print(",\"wifi_connected\":");
  Serial.print(wifiConnected);


  if (wifiConnected)
  {
    Serial.print(",\"wifi_rssi\":");
    Serial.print(WiFi.RSSI());


    Serial.print(",\"wifi_channel\":");
    Serial.print(WiFi.channel());


    Serial.print(",\"wifi_ip\":\"");
    Serial.print(WiFi.localIP());
    Serial.print("\"");
  }
  else
  {
    Serial.print(",\"wifi_rssi\":0");
    Serial.print(",\"wifi_channel\":0");
    Serial.print(",\"wifi_ip\":\"\"");
  }


  // ==========================================================
  // END JSON
  // ==========================================================

  Serial.println("}");


  // ==========================================================
  // CLEAR ONE-SHOT START EVENT
  // ==========================================================

  startEvent =
    false;
}
