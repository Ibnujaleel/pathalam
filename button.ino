const int BUTTON_PIN = 25;

void setup()
{
  Serial.begin(115200);
  delay(1000);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  Serial.println("B3F GPIO25 TEST");
}

void loop()
{
  Serial.print("GPIO25 = ");
  Serial.println(digitalRead(BUTTON_PIN));

  delay(500);
}