from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

CUSTOMERS_FILE = RAW_DIR / "customers.csv"
ORDERS_FILE = RAW_DIR / "orders.csv"
NETWORK_EVENTS_FILE = RAW_DIR / "network_events.csv"
TICKETS_FILE = RAW_DIR / "tickets.csv"
DATABASE_PATH = DATA_DIR / "tecja.db"

