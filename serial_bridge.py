import argparse
import json
import time
from datetime import UTC, datetime

import requests
import serial

# Update COM3 to your ESP32 port (e.g., 'COM3' on Windows or '/dev/ttyUSB0' on Linux/Mac)
SERIAL_PORT = 'COM5'  
BAUD_RATE = 115200
API_URL = 'http://127.0.0.1:8000/api/ingest'

def main():
    parser = argparse.ArgumentParser(description="Forward ESP32 serial sessions to Dextra.")
    parser.add_argument("--port", default=SERIAL_PORT, help="ESP32 serial port, for example COM5")
    args = parser.parse_args()

    while True:
        try:
            with serial.Serial(args.port, BAUD_RATE, timeout=1) as ser:
                print(f"Listening on {args.port}...")
                while True:
                    try:
                        line = ser.readline().decode("utf-8", errors="replace").strip()
                    except serial.SerialException as error:
                        print(f"Serial read failed; reconnecting: {error}")
                        break
                    if not (line.startswith("{") and line.endswith("}")):
                        continue

                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as error:
                        print(f"Ignoring invalid JSON from device: {error}")
                        continue

                    payload.setdefault("timestamp", datetime.now(UTC).isoformat())
                    print(f"Received session JSON: {json.dumps(payload)}")
                    try:
                        response = requests.post(API_URL, json=payload, timeout=5)
                        if response.ok:
                            print(f"Session uploaded; backend HTTP {response.status_code}: {response.text}")
                        else:
                            print(f"Backend rejected session; HTTP {response.status_code}: {response.text}")
                    except requests.RequestException as error:
                        print(f"Session upload failed: {error}")
        except serial.SerialException as error:
            print(f"Could not use {args.port}: {error}")
        time.sleep(2)


if __name__ == "__main__":
    main()