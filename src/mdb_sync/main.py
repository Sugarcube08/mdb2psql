import sys
from src.mdb_sync.logging_config import configure_logging, logger
from src.mdb_sync.infrastructure.postgres.database import SessionLocal
from src.mdb_sync.infrastructure.postgres.repository import PostgresRepository
from src.mdb_sync.infrastructure.mdb.repository import MDBRepository
from src.mdb_sync.application.sync_engine import SyncEngine
from src.mdb_sync.scheduler.sync_scheduler import SyncScheduler

def main():
    configure_logging()
    logger.info("Initializing MDB Sync Platform")

    try:
        mdb_repo = MDBRepository()
        sync_engine = SyncEngine(mdb_repo)
        scheduler = SyncScheduler(sync_engine)
        
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.exception("Application crashed")
        sys.exit(1)

if __name__ == "__main__":
    main()
