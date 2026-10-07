import argparse
import random
from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = "http://localhost:8000/api/ingest"
DEFAULT_PATIENT = "usr_9876"
EXERCISES = [
    "wrist_extension",
    "wrist_flexion",
    "grip_close",
    "finger_extension",
]


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_session_payload(day_index: int, session_index: int, rng: random.Random, now: datetime) -> dict:
    exercise = EXERCISES[(day_index + session_index) % len(EXERCISES)]
    improvement = min(day_index / 14, 1.0)
    switch_activations = max(6, int(10 + improvement * 8 + rng.randint(0, 4) + session_index * 2))
    success_target = 0.42 + improvement * 0.45 + rng.uniform(-0.05, 0.07)
    success_target = max(0.35, min(success_target, 0.92))
    successful_reps = min(switch_activations, max(2, int(round(switch_activations * success_target))))
    duration_seconds = int(55 + improvement * 100 + session_index * 20 + rng.randint(8, 24))
    max_force_n = round(6.5 + improvement * 10.0 + rng.uniform(0.5, 2.5), 1)

    day_offset = 14 - day_index
    base_hour = 9 + session_index * 4 + rng.randint(0, 2)
    minute = rng.randint(0, 59)
    timestamp = datetime(
        now.year,
        now.month,
        now.day,
        base_hour,
        minute,
        tzinfo=timezone.utc,
    ) - timedelta(days=day_offset)

    return {
        "device_id": "DEXTRA_ESP_01",
        "patient_id": DEFAULT_PATIENT,
        "session_type": exercise,
        "duration_seconds": duration_seconds,
        "switch_activations": switch_activations,
        "successful_reps": successful_reps,
        "max_force_n": max_force_n,
        "timestamp": iso_z(timestamp),
    }


def send_session(payload: dict) -> dict:
    response = httpx.post(BASE_URL, json=payload, timeout=10.0)
    response.raise_for_status()
    return response.json()


def run_once() -> None:
    rng = random.Random()
    now = datetime.now(timezone.utc)
    payload = build_session_payload(0, 0, rng, now)
    result = send_session(payload)
    print("Sent one session:")
    print(result)


def run_seed(days: int) -> None:
    if days <= 0:
        raise ValueError("--seed must be a positive integer")

    rng = random.Random(42 + days)
    now = datetime.now(timezone.utc)
    posted = 0

    for day_index in range(days):
        sessions_today = 1 + (1 if rng.random() < 0.55 else 0)
        for session_index in range(sessions_today):
            payload = build_session_payload(day_index, session_index, rng, now)
            result = send_session(payload)
            posted += 1
            print(f"[{day_index + 1}/{days}] posted {payload['session_type']} at {payload['timestamp']} -> {result['successful_reps']} reps")

    print(f"Seeded {posted} sessions across {days} days.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate realistic Dextra rehab sessions for the local demo app.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Send a single realistic session.")
    group.add_argument("--seed", type=int, metavar="N", help="Generate N days of realistic history.")
    args = parser.parse_args()

    if args.once:
        run_once()
    else:
        run_seed(args.seed)


if __name__ == "__main__":
    main()
