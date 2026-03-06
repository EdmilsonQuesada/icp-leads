import os
# Override DATABASE_URL before any app imports so session.py uses SQLite
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
