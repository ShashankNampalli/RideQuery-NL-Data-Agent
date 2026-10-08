from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from nl_data_agent.paths import default_db_path, project_root

load_dotenv()

CSV_DIR = project_root() / "data"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    city TEXT,
    province TEXT,
    user_type TEXT NOT NULL,
    signup_date TEXT,
    is_active INTEGER
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    driver_id INTEGER NOT NULL,
    make TEXT,
    model TEXT,
    year INTEGER,
    license_plate TEXT UNIQUE,
    color TEXT,
    is_active INTEGER,
    FOREIGN KEY (driver_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS rides (
    ride_id INTEGER PRIMARY KEY,
    rider_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    requested_at TEXT,
    pickup_time TEXT,
    dropoff_time TEXT,
    pickup_latitude REAL,
    pickup_longitude REAL,
    dropoff_latitude REAL,
    dropoff_longitude REAL,
    distance_km REAL,
    fare REAL,
    surge_multiplier REAL,
    status TEXT,
    cancellation_reason TEXT,
    FOREIGN KEY (rider_id) REFERENCES users(user_id),
    FOREIGN KEY (driver_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount REAL,
    payment_method TEXT,
    payment_status TEXT,
    transaction_id TEXT UNIQUE,
    payment_time TEXT,
    FOREIGN KEY (ride_id) REFERENCES rides(ride_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    rider_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    rating INTEGER,
    comment TEXT,
    rated_at TEXT,
    FOREIGN KEY (ride_id) REFERENCES rides(ride_id),
    FOREIGN KEY (rider_id) REFERENCES users(user_id),
    FOREIGN KEY (driver_id) REFERENCES users(user_id),
    CHECK (rating BETWEEN 1 AND 5)
);

CREATE INDEX IF NOT EXISTS idx_vehicles_driver_id ON vehicles(driver_id);
CREATE INDEX IF NOT EXISTS idx_rides_rider_id ON rides(rider_id);
CREATE INDEX IF NOT EXISTS idx_rides_driver_id ON rides(driver_id);
CREATE INDEX IF NOT EXISTS idx_rides_requested_at ON rides(requested_at);
CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);
CREATE INDEX IF NOT EXISTS idx_payments_ride_id ON payments(ride_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_ride_id ON ratings(ride_id);
CREATE INDEX IF NOT EXISTS idx_ratings_driver_id ON ratings(driver_id);
"""

TABLE_LOADS: list[tuple[str, str, list[str]]] = [
    (
        "users",
        "users.csv",
        [
            "user_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "city",
            "province",
            "user_type",
            "signup_date",
            "is_active",
        ],
    ),
    (
        "vehicles",
        "vehicles.csv",
        [
            "vehicle_id",
            "driver_id",
            "make",
            "model",
            "year",
            "license_plate",
            "color",
            "is_active",
        ],
    ),
    (
        "rides",
        "rides.csv",
        [
            "ride_id",
            "rider_id",
            "driver_id",
            "requested_at",
            "pickup_time",
            "dropoff_time",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "distance_km",
            "fare",
            "surge_multiplier",
            "status",
            "cancellation_reason",
        ],
    ),
    (
        "payments",
        "payments.csv",
        [
            "payment_id",
            "ride_id",
            "user_id",
            "amount",
            "payment_method",
            "payment_status",
            "transaction_id",
            "payment_time",
        ],
    ),
    (
        "ratings",
        "ratings.csv",
        [
            "rating_id",
            "ride_id",
            "rider_id",
            "driver_id",
            "rating",
            "comment",
            "rated_at",
        ],
    ),
]


def _normalize_value(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    return value


def load_csv(cursor: sqlite3.Cursor, table_name: str, csv_file: str, columns: list[str]) -> None:
    file_path = CSV_DIR / csv_file
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    placeholders = ", ".join("?" for _ in columns)
    col_list = ", ".join(columns)
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    with open(file_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            tuple(_normalize_value(row.get(column)) for column in columns)
            for row in reader
        ]

    cursor.executemany(insert_sql, rows)
    print(f"Loaded {csv_file} ({len(rows)} rows)")


def seed(db_path: Path | None = None) -> Path:
    target = Path(db_path) if db_path else default_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print(f"Connected to SQLite at {target}")
    cursor.executescript(CREATE_TABLES_SQL)
    print("Tables created successfully")

    # Child tables first when clearing
    for table in ("ratings", "payments", "rides", "vehicles", "users"):
        cursor.execute(f"DELETE FROM {table}")

    for table_name, csv_file, columns in TABLE_LOADS:
        load_csv(cursor, table_name, csv_file, columns)

    print("\nRecord counts:")
    print("-" * 40)
    for table_name, _, _ in TABLE_LOADS:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name:<15} {count:>10,}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\nData loaded successfully.")
    return target


if __name__ == "__main__":
    seed()
