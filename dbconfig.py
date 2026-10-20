"""Local MySQL configuration. Set DB_* environment variables first."""
import os

mysql = {
    "port": int(os.getenv("DB_PORT", "3306")),
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "bencars"),
}
