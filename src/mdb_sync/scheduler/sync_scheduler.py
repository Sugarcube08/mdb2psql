import time
from src.mdb_sync.application.sync_engine import SyncEngine
from src.mdb_sync.logging_config import logger
from src.mdb_sync.config import settings
from src.mdb_sync.infrastructure.postgres.database import SessionLocal
from src.mdb_sync.infrastructure.postgres.repository import PostgresRepository

class SyncScheduler:
    def __init__(self, sync_engine: SyncEngine):
        self.sync_engine = sync_engine
        self.interval = settings.SYNC_INTERVAL_SECONDS

    def run_once(self):
        logger.info("Starting sync cycle")
        
        db = SessionLocal()
        try:
            pg_repo = PostgresRepository(db)
            self.sync_engine.set_pg_repo(pg_repo)
            
            # 1. Sync master tables (Full Scan)
            master_tables = ["City_Master", "CUSTOMER_MASTER"]
            for table in master_tables:
                try:
                    self.sync_engine.sync_table_full(table)
                except Exception as e:
                    logger.error("Failed to sync master table", table=table, error=str(e))

            # 2. Sync transactional tables (Incremental + Reconciliation)
            transactional_tables = ["BILL_MASTER", "Receipt_Master", "ReturnGoods"]
            for table in transactional_tables:
                try:
                    self.sync_engine.sync_table_incremental(table)
                    self.sync_engine.reconcile_table(table)
                except Exception as e:
                    logger.error("Failed to sync transactional table", table=table, error=str(e))
        finally:
            db.close()

        logger.info("Sync cycle completed")

    def start(self):
        logger.info("Starting scheduler", interval=self.interval)
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.critical("Critical error in sync loop", error=str(e))
            
            logger.info("Sleeping", seconds=self.interval)
            time.sleep(self.interval)
