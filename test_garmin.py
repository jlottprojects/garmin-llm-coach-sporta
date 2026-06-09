import os
import sys
import json
import logging
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Optional: Uncomment if you need full library debugging logs in your console
# logging.basicConfig(level=logging.INFO)

# Load local environment secrets
load_dotenv()

EMAIL = os.getenv("GARMIN_EMAIL")
PASSWORD = os.getenv("GARMIN_PASSWORD")

# Define the library's native token directory cache
TOKEN_DIR = str(Path("~/.garminconnect").expanduser())


def init_api() -> Garmin:
    """Initializes Garmin API.

    Restores valid tokens natively from TOKEN_DIR if available, or drops back
    safely into standard credential + MFA login if expired.
    """
    print("🔄 Initializing Garmin API Client Framework...")

    # 1. Instantiate the modern configuration profile
    # The library handles reading/refreshing its token file automatically inside this folder
    client = Garmin(
        email=EMAIL,
        password=PASSWORD,
        prompt_mfa=lambda: input("\n🔒 Enter your 6-digit Garmin MFA code: ").strip(),
    )

    try:
        # 2. Fire the native strategy engine
        # Pass TOKEN_DIR directly—the engine reads/writes token files completely behind the scenes
        print(f"📂 Activating session management cache tracker at: {TOKEN_DIR}")
        client.login(TOKEN_DIR)
        print("✅ Success: Authenticated cleanly with Garmin Core Engines.")
        return client

    except GarminConnectTooManyRequestsError as err:
        print(
            f"\n❌ [RATE LIMIT ERROR] Garmin firewall blocked this IP signature: {err}"
        )
        print(
            "⚠️ Action Required: Stop executions and allow 15-30 minutes for Cloudflare cooldown."
        )
        sys.exit(1)

    except (GarminConnectAuthenticationError, GarminConnectConnectionError) as err:
        print(f"\n❌ [CREDENTIAL/NETWORK ERROR] Gateway handshake rejected: {err}")
        print(
            "⚠️ Check that your email/password string variables are correctly set in your .env file."
        )
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ [UNEXPECTED FAILURE] Execution pipeline halted: {e}")
        sys.exit(1)


def extract_daily_data():
    """Fetches key physical and biometric data sets for yesterday and saves to a raw JSON file."""
    target_date = date.today() - timedelta(days=1)
    date_str = target_date.isoformat()
    print(f"\n🚀 --- Initiating Extract Sequence for Target Date: {date_str} ---")

    try:
        # Initialize verified client link
        client = init_api()

        # Ingestion Object Containers
        print("📥 Pulling Target Sleep Log Matrices...")
        try:
            sleep_data = client.get_sleep_data(date_str)
        except Exception as s_err:
            print(f"⚠️ Notice: Sleep parsing skipped or unavailable for date: {s_err}")
            sleep_data = {}

        print("📥 Pulling Core User Summary Tracking Profiles...")
        try:
            stats_data = client.get_user_summary(date_str)
        except Exception as sum_err:
            print(f"⚠️ Notice: Daily summary counters unavailable for date: {sum_err}")
            stats_data = {}

        print("📥 Pulling Body Composition Biometrics...")
        try:
            weight_data = client.get_body_composition(date_str)
        except Exception as w_err:
            print(f"⚠️ Notice: Body composition empty or skipped for date: {w_err}")
            weight_data = {}

        # Assemble Pipeline JSON Payload
        payload = {
            "extract_date": date_str,
            "sleep": sleep_data,
            "activity_summary": stats_data,
        }

        # Generate target directories locally inside project space
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"garmin_{date_str}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        print(
            f"\n🏆 [PIPELINE SUCCESS] Complete data block written securely to: {output_file}"
        )

    except Exception as e:
        print(f"\n🚨 [CRITICAL DROP] Extraction pipeline structural failure: {e}")


if __name__ == "__main__":
    extract_daily_data()
