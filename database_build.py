import sqlite3
import datetime


def setup_database():
    # Connects to a local file named garmin_health.db
    # If the file doesn't exist, SQLite will create it automatically
    conn = sqlite3.connect("garmin_health.db")
    cursor = conn.cursor()

    # Create the structured table for daily health metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_metrics (
        date TEXT PRIMARY KEY,
        sleep_score INTEGER,
        hrv_status INTEGER,
        resting_heart_rate INTEGER,
        body_battery_max INTEGER,
        training_load INTEGER
    )
    """)

    # Generate 5 days of realistic mock training data ending today
    today = datetime.date.today()
    mock_data = [
        ((today - datetime.timedelta(days=4)).isoformat(), 78, 55, 52, 85, 240),
        (
            (today - datetime.timedelta(days=3)).isoformat(),
            45,
            42,
            58,
            50,
            410,
        ),  # High fatigue day
        ((today - datetime.timedelta(days=2)).isoformat(), 82, 54, 50, 90, 110),
        (
            (today - datetime.timedelta(days=1)).isoformat(),
            88,
            58,
            49,
            98,
            0,
        ),  # Rest day
        (today.isoformat(), 62, 48, 55, 70, 350),  # Today's current state
    ]

    # Insert data safely using parameterized queries
    cursor.executemany(
        """
    INSERT OR REPLACE INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?)
    """,
        mock_data,
    )

    conn.commit()
    conn.close()
    print("🚀 success: 'garmin_health.db' created locally with 5 days of metrics.")


if __name__ == "__main__":
    setup_database()
