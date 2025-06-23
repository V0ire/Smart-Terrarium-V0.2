#include <WiFi.h>
#include <Wire.h>
#include <HTTPClient.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <BH1750.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// --- KONFIGURASI YANG PERLU ANDA UBAH ---
const char* WIFI_SSID = "KulkasLG2PintuMinatInbok"; // DIUBAH: Sesuai permintaan Anda
const char* WIFI_PASSWORD = "suprijoker";  // DIUBAH: Sesuai permintaan Anda

// GANTI DENGAN URL APLIKASI VERCEL ANDA (HARUS LENGKAP dengan https://)
const char* VERCEL_URL = "https://smart-terarium-v0-1-inb1.vercel.app"; 
// --- AKHIR DARI KONFIGURASI ---

// Inisialisasi Sensor dan Aktuator
Adafruit_AHTX0 aht20;
Adafruit_BMP280 bmp280;
BH1750 lightMeter;
Servo myServo;

// Definisi Pin
#define RELAY1_PIN 26 // Lampu
#define RELAY2_PIN 27 // Pompa
#define SOIL_PIN 34
#define SERVO_PIN 25

// Variabel Global untuk Status
String lampMode = "OFF";
String pumpMode = "AUTO"; // Variabel untuk mode pompa (AUTO, OFF)
int soilThreshold = 2000;
int lightThreshold = 15;

// Pewaktu non-blocking untuk loop yang lebih efisien
unsigned long lastControlCheck = 0;
unsigned long lastSensorSend = 0;
const long controlCheckInterval = 1000;  // Cek perintah setiap 1 detik
const long sensorSendInterval = 2000; // Kirim data sensor setiap 2 detik

void setup() {
  Serial.begin(115200);

  // Koneksi WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Menghubungkan ke WiFi '");
  Serial.print(WIFI_SSID);
  Serial.print("'...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\n----------------------------------------");
  Serial.println("WiFi Terhubung!");
  Serial.print("Alamat IP: ");
  Serial.println(WiFi.localIP());
  Serial.println("----------------------------------------");


  // Inisialisasi Pin
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  digitalWrite(RELAY1_PIN, LOW); // Pastikan lampu mati saat start
  digitalWrite(RELAY2_PIN, LOW); // Pastikan pompa mati saat start

  // Inisialisasi Servo
  myServo.attach(SERVO_PIN);
  myServo.write(90); // Posisi default

  // Inisialisasi Sensor I2C
  Wire.begin();
  if (!aht20.begin()) Serial.println("AHT20 gagal diinisialisasi");
  if (!bmp280.begin(0x77)) Serial.println("BMP280 gagal diinisialisasi (cek alamat I2C)"); // DIUBAH: Alamat ke 0x77
  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) Serial.println("BH1750 gagal diinisialisasi");
}

void getControlData() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String endpoint = String(VERCEL_URL) + "/get-control";
  http.begin(endpoint);
  
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    // DIUBAH: Ukuran JSON disesuaikan untuk field baru
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, payload);
    if (err) {
      Serial.println("Gagal parsing JSON kontrol: " + String(err.c_str()));
      http.end();
      return;
    }

    // Ambil data dari JSON
    lampMode = doc["lamp"].as<String>();
    pumpMode = doc["pump_mode"].as<String>();
    String servoCmd = doc["servo"].as<String>();
    String pumpTriggerCmd = doc["pump_manual_trigger"].as<String>(); // BARU: Baca perintah pemicu pompa
    soilThreshold = doc["soil_threshold"]; 
    lightThreshold = doc["light_threshold"];

    // Logika kontrol lampu langsung (kecuali mode AUTO)
    if (lampMode == "ON") {
      digitalWrite(RELAY1_PIN, HIGH);
    } else if (lampMode == "OFF") {
      digitalWrite(RELAY1_PIN, LOW);
    }

    // Logika kontrol servo
    if (servoCmd == "ON") {
      Serial.println("Mengaktifkan servo...");
      myServo.write(0); // Buka
      delay(1000);
      myServo.write(90); // Tutup

      HTTPClient httpUpdate;
      String updateEndpoint = String(VERCEL_URL) + "/update_control";
      httpUpdate.begin(updateEndpoint);
      httpUpdate.addHeader("Content-Type", "application/json");
      StaticJsonDocument<128> updateDoc;
      updateDoc["servo"] = "OFF";
      String updatePayload;
      serializeJson(updateDoc, updatePayload);
      httpUpdate.POST(updatePayload);
      httpUpdate.end();
    }
    
    // BARU: Logika untuk pemicu pompa manual sesaat
    if (pumpTriggerCmd == "ON") {
      Serial.println("Pemicu Pompa Manual Aktif: Menyalakan pompa selama 2 detik...");
      digitalWrite(RELAY2_PIN, HIGH);
      delay(2000); // Nyala selama 2 detik
      digitalWrite(RELAY2_PIN, LOW);
      Serial.println("Pompa manual selesai.");

      // Segera kirim balik status "OFF" untuk pemicu agar tidak dijalankan lagi
      HTTPClient httpUpdate;
      String updateEndpoint = String(VERCEL_URL) + "/update_control";
      httpUpdate.begin(updateEndpoint);
      httpUpdate.addHeader("Content-Type", "application/json");
      StaticJsonDocument<128> updateDoc;
      updateDoc["pump_manual_trigger"] = "OFF"; // Setel ulang pemicu
      String updatePayload;
      serializeJson(updateDoc, updatePayload);
      httpUpdate.POST(updatePayload);
      httpUpdate.end();
    }


  } else {
    Serial.println("Gagal mengambil data kontrol, HTTP Code: " + String(httpCode));
  }
  http.end();
}

void sendSensorData() {
    if (WiFi.status() != WL_CONNECTED) return;

    // Membaca semua sensor
    sensors_event_t hum, temp;
    aht20.getEvent(&hum, &temp);
    float lux = lightMeter.readLightLevel();
    int soilVal = analogRead(SOIL_PIN);

    // --- BARU: Log Detail untuk Serial Monitor ---
    Serial.println("\n--- Pembacaan Sensor ---");
    Serial.print("Suhu Udara: ");
    Serial.print(temp.temperature);
    Serial.println(" C");
    Serial.print("Kelembaban Udara: ");
    Serial.print(hum.relative_humidity);
    Serial.println(" %");
    Serial.print("Intensitas Cahaya: ");
    Serial.print(lux);
    Serial.println(" Lux");
    Serial.print("Kelembaban Tanah (Nilai ADC): ");
    Serial.println(soilVal);
    Serial.println("-------------------------");
    // --- AKHIR DARI LOG DETAIL ---

    // Logika untuk menentukan status sensor

    StaticJsonDocument<512> doc;
    doc["temperature"] = temp.temperature;
    doc["humidity"] = hum.relative_humidity;
    doc["lux"] = lux;
    doc["soil"] = soilVal;

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    // Log data JSON yang akan dikirim
    Serial.println("Mengirim data JSON ke server:");
    Serial.println(jsonPayload);
    
    HTTPClient http;
    String endpoint = String(VERCEL_URL) + "/data";
    http.begin(endpoint);
    http.addHeader("Content-Type", "application/json");
    http.POST(jsonPayload);
    http.end();
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Cek perintah dari server secara berkala
  if (currentMillis - lastControlCheck >= controlCheckInterval) {
    lastControlCheck = currentMillis;
    getControlData();
  }

  // 2. Kirim data sensor ke server secara berkala
  if (currentMillis - lastSensorSend >= sensorSendInterval) {
    lastSensorSend = currentMillis;
    sendSensorData();
  }
  
  // 3. Jalankan logika lokal berdasarkan mode yang diterima
  
  // Logika lampu otomatis
  if (lampMode == "AUTO") {
    float lux = lightMeter.readLightLevel();
    digitalWrite(RELAY1_PIN, lux <= lightThreshold ? HIGH : LOW);
  }

  // DIUBAH: Logika Pompa hanya untuk mode AUTO dan OFF
  if (pumpMode == "AUTO") {
    // Mode Otomatis: kontrol berdasarkan sensor kelembaban tanah
    int soilVal = analogRead(SOIL_PIN);
    if (soilVal > soilThreshold) {
      digitalWrite(RELAY2_PIN, HIGH); // Tanah kering, nyalakan pompa
    } else {
      digitalWrite(RELAY2_PIN, LOW);  // Tanah lembab, matikan pompa
    }
  } else if (pumpMode == "OFF") {
    // Mode Manual OFF: paksa pompa untuk selalu mati
    digitalWrite(RELAY2_PIN, LOW);
  } 
  // DIHAPUS: Kasus "else if (pumpMode == "ON")" dihapus karena digantikan oleh sistem pemicu.
}