# Three-Minute Demo Script

## Before the Demo

1. From the project root, start the app with `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.
2. Check `http://127.0.0.1:8000/health`, then open `http://127.0.0.1:8000/` in the browser.
3. If the dashboard has little history, open a second terminal and run `python simulate_device.py --seed 14`. This adds backdated sample sessions; it does not replace existing data.
4. If demonstrating the ESP32, ensure it is on the same network, configured with the computer's LAN IP, and visible in the serial monitor at 115200 baud.

## Run of Show

| Time | Click / action | Say |
| --- | --- | --- |
| 0:00-0:25 | Start on **Dashboard**. Point to the summary statistics and weekly activity chart. | “Dextra turns a completed orthosis session into a progress view: repetitions, time, consistency, and a weekly trend for the demo patient.” |
| 0:25-0:55 | Trigger one new session: hold the ESP32 session-end button for two seconds, or run `python simulate_device.py --once` in the second terminal. Stay on the dashboard and wait for the refresh. | “At the end of a session, the device sends one JSON HTTP request. The dashboard checks for updates every five seconds, so the new session appears without a page reload.” |
| 0:55-1:25 | Click **History**. Use the exercise-type filter and show the matching rows; clear the filter afterward. | “History keeps the individual sessions available for review, with filtering and pagination when the list grows.” |
| 1:25-1:55 | Click **Achievements**. Point out one unlocked badge and one locked badge with progress. | “Achievements make consistency visible. Unlocked badges and the remaining progress use the same recorded session history.” |
| 1:55-2:30 | Click **Exercises**, then open an exercise such as **Wrist Extension**. | “The exercise library pairs plain-language movement guidance with the session count and success rate for that exercise.” |
| 2:30-3:00 | Click **Dashboard** again and point out the recent session and updated total. | “The full path is device, API, local database, then the dashboard. The simulator uses the same ingestion endpoint, which also makes the demo repeatable.” |

## Hardware Fallback

If the ESP32, Wi-Fi, or local network upload fails, leave the dashboard open and run this in the second terminal:

```shell
python simulate_device.py --once
```

It POSTs a realistic session to the same local `/api/ingest` endpoint. Wait up to five seconds for the latest session and statistics to refresh, then continue the script. If the simulator cannot connect, verify the app is still running at `http://127.0.0.1:8000/health` and retry. A multi-day history can be prepared before the demo with `python simulate_device.py --seed 14`; that command adds records and should not be repeated casually.

The current ESP32 sketch has placeholder sensor hooks and reports `0.0` for maximum force until those values are connected to the device logic. Describe the live hardware step as a transport/integration demonstration, not as validated clinical measurement.