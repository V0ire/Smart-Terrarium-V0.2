#include <WiFi.h>
#include <Wire.h>
#include <HTTPClient.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <BH1750.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

const char* ssid = "KulkasLG2PintuMinatInbok";
const char* password = "suprijoker";
const char* serverHost = "http://192.168.43.205:5000";

Adafruit_AHTX0 aht20;
Adafruit_BMP280 bmp280;
BH1750 lightMeter;
Servo myServo;

#define RELAY1_PIN 26
#define RELAY2_PIN 27
#define SOIL_PIN 34
#define SERVO_PIN 25

String lampMode = "OFF";
int soilThreshold = 2100;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung: " + WiFi.localIP().toString());

  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  digitalWrite(RELAY1_PIN, LOW);
  digitalWrite(RELAY2_PIN, LOW);

  myServo.attach(SERVO_PIN);
  myServo.write(90);

  Wire.begin();
  if (!aht20.begin()) Serial.println("AHT20 gagal");
  if (!bmp280.begin(0x77)) Serial.println("BMP280 gagal");
  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) Serial.println("BH1750 gagal");
}

void checkControlFromServer() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverHost) + "/get-control");
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();
      DynamicJsonDocument doc(256);
      DeserializationError err = deserializeJson(doc, payload);
      if (err) return;

      String lampCmd = doc["lamp"] | "OFF";
      String servoCmd = doc["servo"] | "";
      int newThreshold = doc["threshold"] | soilThreshold;

      lampMode = lampCmd;
      soilThreshold = newThreshold;

      if (lampCmd == "ON") digitalWrite(RELAY1_PIN, HIGH);
      else if (lampCmd == "OFF") digitalWrite(RELAY1_PIN, LOW);

      if (servoCmd == "ON") {
        myServo.write(0);
        delay(1000);
        myServo.write(90);

        HTTPClient http2;
        http2.begin(String(serverHost) + "/control");
        http2.addHeader("Content-Type", "application/x-www-form-urlencoded");
        http2.POST("servo=OFF");
        http2.end();
      }
    }
    http.end();
  }
}

void loop() {
  sensors_event_t hum, temp;
  aht20.getEvent(&hum, &temp);
  float lux = lightMeter.readLightLevel();
  int soilVal = analogRead(SOIL_PIN);

  float soilPercent = map(soilVal, 2900, 1400, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  if (lampMode == "AUTO") {
    digitalWrite(RELAY1_PIN, lux < 15 ? HIGH : LOW);
  }

  if (soilVal > soilThreshold + 250) {
    digitalWrite(RELAY2_PIN, HIGH);
  } else if (soilVal <= soilThreshold) {
    digitalWrite(RELAY2_PIN, LOW);
  }

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverHost) + "/data");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    String postData = "temp=" + String(temp.temperature) +
                      "&hum=" + String(hum.relative_humidity) +
                      "&lux=" + String(lux) +
                      "&soil=" + String(soilVal) +
                      "&soil_percent=" + String(soilPercent);
    http.POST(postData);
    http.end();
  }

  checkControlFromServer();

  String lampStatus = digitalRead(RELAY1_PIN) == HIGH ? "ON" : "OFF";
  String pumpStatus = digitalRead(RELAY2_PIN) == HIGH ? "ON" : "OFF";
  String servoStatus = "OFF";

  Serial.println("\n WiFi Terhubung: " + WiFi.localIP().toString());
  Serial.print("\n Lampu: ");
  Serial.print(lampStatus);
  Serial.print(" | Pompa: ");
  Serial.print(pumpStatus);
  Serial.print(" | Servo: ");
  Serial.println(servoStatus);
  Serial.printf("\n T: %.1fC H: %.1f%% Lux: %.1f Soil: %d (%.1f%%)\n", temp.temperature, hum.relative_humidity, lux, soilVal, soilPercent);

  delay(500);
}
