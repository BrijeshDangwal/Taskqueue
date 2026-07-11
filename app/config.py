import os

class Settings:
    # Redis serves as BOTH broker and backend in this project.
    # Format: redis://<host>:<port>/<db_number>
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = Settings()