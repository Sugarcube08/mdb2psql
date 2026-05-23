from pydantic_settings import BaseSettings, SettingsConfigDict

import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Postgres
    POSTGRES_URI: str = "postgresql://postgres:postgres@localhost:5432/mdb_sync"

    @property
    def postgres_url(self) -> str:
        # Detect if running inside Docker
        is_docker = os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER", "false") == "true"
        
        if is_docker:
            # URI is used as provided in .env (targeting graphora-postgres)
            return self.POSTGRES_URI
        else:
            # For local tools (Alembic), swap internal host with localhost
            # This allows the same .env to work for both
            return self.POSTGRES_URI.replace("@graphora-postgres", "@localhost")

    # MDB
    MDB_PATH: str = "./data/raw/Billing.mdb"
    MDB_DRIVER: str = "{Microsoft Access Driver (*.mdb, *.accdb)}"

    @property
    def mdb_connection_string(self) -> str:
        return f"DRIVER={self.MDB_DRIVER};DBQ={self.MDB_PATH};"

    # Sync
    SYNC_INTERVAL_SECONDS: int = 3600
    RECONCILIATION_WINDOW_ROWS: int = 5000
    RECONCILIATION_CHUNK_LIMIT: int = 5000
    SOURCE_SYSTEM: str = "BILLING_MDB"
    
    # Pruning
    PRUNE_INTERVAL_SECONDS: int = 86400  # Default 1 day
    RETENTION_DAYS_SALES: int = 30
    RETENTION_DAYS_RECEIPTS: int = 30
    RETENTION_DAYS_RG: int = 30

    # Logging
    LOG_LEVEL: str = "info"
    LOG_FORMAT: str = "auto"  # "auto", "json", or "console"

settings = Settings()
