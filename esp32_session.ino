#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <time.h>

// Set these before flashing the device.
const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char *SERVER_IP = "192.168.1.10";

const char *DEVICE_ID = "DEXTRA_ESP_01";
const char *PATIENT_ID = "usr_9876";
const char *SESSION_TYPE = "wrist_extension";
const uint8_t SESSION_END_BUTTON_PIN = 27;
const unsigned long LONG_PRESS_MS = 2000;
const unsigned long BUTTON_DEBOUNCE_MS = 35;
const float MAX_FORCE_N = 0.0f; // Replace with the session maximum from your force-sensor logic.

uint32_t switch_activations = 0;
uint32_t successful_reps = 0;
uint32_t sessionStartedAtMs = 0;
bool sessionEnded = false;

int lastButtonReading = HIGH;
int stableButtonState = HIGH;
unsigned long lastButtonChangeMs = 0;
unsigned long buttonPressedAtMs = 0;
bool longPressHandled = false;

void noteSwitchActivation() {
  if (!sessionEnded) {
    ++switch_activations;
  }
}

void noteSuccessfulRep() {
  if (!sessionEnded) {
    ++successful_reps;
  }
}

bool syncClock() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  struct tm timeInfo;
  if (!getLocalTime(&timeInfo, 15000)) {
    Serial.println("NTP time sync failed");
    return false;
  }
  Serial.println("NTP time synchronized (UTC)");
  return true;
}

bool makeTimestamp(char *buffer, size_t bufferSize) {
  time_t now = time(nullptr);
  if (now < 1700000000) {
    if (!syncClock()) {
      return false;
    }
    now = time(nullptr);
  }

  struct tm utcTime;
  gmtime_r(&now, &utcTime);
  return strftime(buffer, bufferSize, "%Y-%m-%dT%H:%M:%SZ", &utcTime) > 0;
}

bool postSession(const char *jsonPayload) {
  const String url = String("http://") + SERVER_IP + ":8000/api/ingest";

  for (int attempt = 1; attempt <= 2; ++attempt) {
    WiFiClient client;
    HTTPClient http;

    Serial.printf("POST attempt %d/2 to %s\n", attempt, url.c_str());
    if (!http.begin(client, url)) {
      Serial.println("HTTP setup failed");
      continue;
    }

    http.addHeader("Content-Type", "application/json");
    const int status = http.POST(reinterpret_cast<const uint8_t *>(jsonPayload), strlen(jsonPayload));
    if (status >= 200 && status < 300) {
      Serial.printf("Session uploaded; HTTP %d\n", status);
      http.end();
      return true;
    }

    if (status < 0) {
      Serial.printf("POST failed: %s\n", http.errorToString(status).c_str());
    } else {
      Serial.printf("Server returned HTTP %d: %s\n", status, http.getString().c_str());
    }
    http.end();
  }

  Serial.println("Session upload failed after one retry");
  return false;
}

void finishSession() {
  sessionEnded = true;
  const uint32_t durationSeconds = (millis() - sessionStartedAtMs) / 1000;
  char timestamp[25];
  if (!makeTimestamp(timestamp, sizeof(timestamp))) {
    Serial.println("Cannot upload session without a valid NTP timestamp");
    return;
  }

  StaticJsonDocument<384> payload;
  payload["device_id"] = DEVICE_ID;
  payload["patient_id"] = PATIENT_ID;
  payload["session_type"] = SESSION_TYPE;
  payload["duration_seconds"] = durationSeconds;
  payload["switch_activations"] = switch_activations;
  payload["successful_reps"] = successful_reps;
  payload["max_force_n"] = MAX_FORCE_N;
  payload["timestamp"] = timestamp;

  char jsonPayload[384];
  const size_t payloadSize = serializeJson(payload, jsonPayload, sizeof(jsonPayload));
  if (payloadSize == 0 || payloadSize >= sizeof(jsonPayload)) {
    Serial.println("Could not serialize session payload");
    return;
  }

  Serial.printf("Session ended: %lu sec, %lu switch activations, %lu successful reps\n",
                static_cast<unsigned long>(durationSeconds),
                static_cast<unsigned long>(switch_activations),
                static_cast<unsigned long>(successful_reps));
  postSession(jsonPayload);
}

void pollSessionEndButton() {
  const unsigned long now = millis();
  const int reading = digitalRead(SESSION_END_BUTTON_PIN);

  if (reading != lastButtonReading) {
    lastButtonChangeMs = now;
    lastButtonReading = reading;
  }

  if (now - lastButtonChangeMs >= BUTTON_DEBOUNCE_MS && reading != stableButtonState) {
    stableButtonState = reading;
    if (stableButtonState == LOW) {
      buttonPressedAtMs = now;
      longPressHandled = false;
    }
  }

  if (!sessionEnded && stableButtonState == LOW && !longPressHandled &&
      now - buttonPressedAtMs >= LONG_PRESS_MS) {
    longPressHandled = true;
    finishSession();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(SESSION_END_BUTTON_PIN, INPUT_PULLUP);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Connecting to Wi-Fi %s", WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.printf("\nWi-Fi connected; device IP: %s\n", WiFi.localIP().toString().c_str());

  syncClock();
  sessionStartedAtMs = millis();
  Serial.println("Session started; hold the button to finish and upload");
}

void loop() {
  if (!sessionEnded) {
    // Hook noteSwitchActivation() into your switch-activation handler.
    // Hook noteSuccessfulRep() into your servo logic when a rep completes successfully.
    pollSessionEndButton();
  }
}