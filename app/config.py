import os

class Settings:
    # Redis serves as BOTH broker and backend in this project.
    # Format: redis://<host>:<port>/<db_number>
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Postgres — the durable system-of-record for job history.
    # Format: postgresql+psycopg2://<user>:<password>@<host>:<port>/<db>
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://taskqueue:taskqueue@localhost:5432/taskqueue",
    )

settings = Settings()