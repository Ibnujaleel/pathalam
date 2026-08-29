wifi test status complete check done 
#include <WiFi.h>

const char* WIFI_SSID = "Naveen";
const char* WIFI_PASSWORD = "12341234";

void scanNetworks()
{
  Serial.println();
  Serial.println("========================================");
  Serial.println("         WIFI SCAN STARTING");
  Serial.println("========================================");

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(1000);

  int count = WiFi.scanNetworks();

  if (count <= 0)
  {
    Serial.println("No Wi-Fi networks found.");
    return;
  }

  Serial.print("Networks found: ");
  Serial.println(count);
  Serial.println();

  for (int i = 0; i < count; i++)
  {
    Serial.print("Network ");
    Serial.println(i + 1);

    Serial.print("  SSID    : ");
    Serial.println(WiFi.SSID(i));

    Serial.print("  RSSI    : ");
    Serial.print(WiFi.RSSI(i));
    Serial.println(" dBm");

    Serial.print("  Channel : ");
    Serial.println(WiFi.channel(i));

    Serial.print("  BSSID   : ");
    Serial.println(WiFi.BSSIDstr(i));

    Serial.println();
  }

  Serial.println("========================================");
  Serial.println("          WIFI SCAN COMPLETE");
  Serial.println("========================================");
}


// ------------------------------------------------------------
// CONNECT TO NAVEEN
// ------------------------------------------------------------

bool connectToWiFi()
{
  Serial.println();
  Serial.println("========================================");
  Serial.println("        WIFI CONNECTION TEST");
  Serial.println("========================================");

  Serial.print("SSID     : ");
  Serial.println(WIFI_SSID);

  Serial.println("Password : ********");

  Serial.println();
  Serial.println("Connecting...");

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(500);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startTime = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - startTime < 30000)
  {
    delay(500);

    Serial.print(".");
    Serial.print(" status=");
    Serial.println(WiFi.status());
  }

  Serial.println();
  Serial.println();

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("########################################");
    Serial.println("          WIFI CONNECTED!");
    Serial.println("########################################");

    Serial.print("SSID       : ");
    Serial.println(WiFi.SSID());

    Serial.print("IP address : ");
    Serial.println(WiFi.localIP());

    Serial.print("Gateway    : ");
    Serial.println(WiFi.gatewayIP());

    Serial.print("Subnet     : ");
    Serial.println(WiFi.subnetMask());

    Serial.print("RSSI       : ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");

    Serial.print("Channel    : ");
    Serial.println(WiFi.channel());

    Serial.print("BSSID      : ");
    Serial.println(WiFi.BSSIDstr());

    Serial.print("MAC        : ");
    Serial.println(WiFi.macAddress());

    Serial.println("########################################");

    return true;
  }

  Serial.println("########################################");
  Serial.println("          WIFI CONNECTION FAILED");
  Serial.println("########################################");

  Serial.print("Final status = ");
  Serial.println(WiFi.status());

  Serial.println();
  Serial.println("Status values:");
  Serial.println("1 = WL_NO_SSID_AVAIL");
  Serial.println("4 = WL_CONNECT_FAILED");
  Serial.println("6 = WL_DISCONNECTED");

  Serial.println("########################################");

  return false;
}


void setup()
{
  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println();
  Serial.println("========================================");
  Serial.println("       PATHALA KAVAL ESP32 TEST");
  Serial.println("       SCAN + CONNECT TO NAVEEN");
  Serial.println("========================================");

  // Step 1: scan
  scanNetworks();

  // Step 2: connect
  connectToWiFi();
}


void loop()
{
  delay(5000);

  Serial.println();
  Serial.println("----------- LIVE STATUS ------------");

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("WIFI: CONNECTED");

    Serial.print("SSID : ");
    Serial.println(WiFi.SSID());

    Serial.print("IP   : ");
    Serial.println(WiFi.localIP());

    Serial.print("RSSI : ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  }
  else
  {
    Serial.print("WIFI: NOT CONNECTED");
    Serial.print(" | Status = ");
    Serial.println(WiFi.status());
  }

  Serial.println("------------------------------------");
}