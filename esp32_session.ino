#include <Arduino.h>
#include <ArduinoJson.h>

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

void finishSession() {
  sessionEnded = true;
  const uint32_t durationSeconds = (millis() - sessionStartedAtMs) / 1000;

  StaticJsonDocument<384> payload;
  payload["device_id"] = DEVICE_ID;
  payload["patient_id"] = PATIENT_ID;
  payload["session_type"] = SESSION_TYPE;
  payload["duration_seconds"] = durationSeconds;
  payload["switch_activations"] = switch_activations;
  payload["successful_reps"] = successful_reps;
  payload["max_force_n"] = MAX_FORCE_N;

  Serial.printf("Session ended: %lu sec, %lu switch activations, %lu successful reps\n",
                static_cast<unsigned long>(durationSeconds),
                static_cast<unsigned long>(switch_activations),
                static_cast<unsigned long>(successful_reps));
  serializeJson(payload, Serial);
  Serial.println();
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

  sessionStartedAtMs = millis();
  Serial.println("Session started; hold the button to finish and send over USB");
}

void loop() {
  if (!sessionEnded) {
    // Hook noteSwitchActivation() into your switch-activation handler.
    // Hook noteSuccessfulRep() into your servo logic when a rep completes successfully.
    pollSessionEndButton();
  }
}