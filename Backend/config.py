import os

def _load_env():
    """Load key-value pairs from .env if present"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, ".env"),
        os.path.join(os.path.dirname(base_dir), ".env")
    ]
    for p in candidates:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
            break

_load_env()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "sentiment_db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "ssl": os.getenv("DB_SSL", "false").lower() in ("true", "1", "yes")
}

APP_SECRET_KEY = os.getenv("SECRET_KEY", "sentiment-secret-key")

