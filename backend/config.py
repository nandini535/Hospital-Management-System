import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hospital_db"),
}

# Used to sign login tokens. CHANGE THIS (set the SECRET_KEY env variable) before showing/deploying.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
TOKEN_MAX_AGE = int(os.getenv("TOKEN_MAX_AGE", 12 * 3600))   # seconds
