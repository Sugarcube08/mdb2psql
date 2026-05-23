from typing import List, Dict, Any, Optional
from src.mdb_sync.infrastructure.mdb.repository import MDBRepository
from src.mdb_sync.infrastructure.postgres.repository import PostgresRepository
from src.mdb_sync.application.mapper import DataMapper
from src.mdb_sync.logging_config import logger
from src.mdb_sync.config import settings

class SyncEngine:
    def __init__(self, mdb_repo: MDBRepository):
        self.mdb_repo = mdb_repo
        self.pg_repo: Optional[PostgresRepository] = None

    def set_pg_repo(self, pg_repo: PostgresRepository):
        self.pg_repo = pg_repo

    def sync_table_incremental(self, table_name: str):
        if not self.pg_repo: raise RuntimeError("PG Repo not set")
        config = DataMapper.MAPPING[table_name]
        state = self.pg_repo.get_sync_state(table_name)
        last_pk = state.last_pk if state else None

        logger.info("Starting incremental sync", table=table_name, last_pk=last_pk)
        
        rows = self.mdb_repo.get_new_records(table_name, config["pk"], last_pk)
        if not rows:
            logger.info("No new records found", table=table_name)
            return

        # Sort rows by PK to ensure deterministic processing if mdbtools didn't sort
        try:
            rows.sort(key=lambda x: x.get(config["pk"], 0))
        except:
            pass

        processed_count = 0
        new_last_pk = last_pk
        batch_size = 100

        for i, row in enumerate(rows):
            try:
                # Manual filtering for mdbtools which returns full scan
                current_pk = str(row[config["pk"]])
                if last_pk and not (current_pk > last_pk):
                    continue

                domain_model = DataMapper.map_to_domain(table_name, row)
                entity_id = getattr(domain_model, config["pg_pk"])
                
                # Update detect
                fingerprint = self.pg_repo.get_fingerprint(table_name, entity_id)
                if not fingerprint or fingerprint.checksum != domain_model.checksum:
                    pg_data = DataMapper.map_to_pg(table_name, domain_model, settings.SOURCE_SYSTEM)
                    self.pg_repo.upsert(config["pg_model"], pg_data, config["pg_pk"])
                    self.pg_repo.update_fingerprint(table_name, entity_id, domain_model.checksum)
                    processed_count += 1
                
                new_last_pk = str(row[config["pk"]])
                
                # Batch commit
                if processed_count > 0 and processed_count % batch_size == 0:
                    self.pg_repo.update_sync_state(table_name, new_last_pk)
                    self.pg_repo.commit()
                    logger.debug("Batch committed", table=table_name, count=processed_count)

            except Exception as e:
                logger.error("Failed to sync row", table=table_name, error=str(e), row=row)
                continue

        self.pg_repo.update_sync_state(table_name, new_last_pk)
        self.pg_repo.commit()
        logger.info("Incremental sync completed", table=table_name, processed=processed_count, last_pk=new_last_pk)

    def reconcile_table(self, table_name: str):
        if not self.pg_repo: raise RuntimeError("PG Repo not set")
        config = DataMapper.MAPPING[table_name]
        logger.info("Starting reconciliation", table=table_name)

        rows = self.mdb_repo.get_recent_records(table_name, config["pk"], settings.RECONCILIATION_WINDOW_ROWS)
        
        updated_count = 0
        for i, row in enumerate(rows):
            try:
                domain_model = DataMapper.map_to_domain(table_name, row)
                entity_id = getattr(domain_model, config["pg_pk"])
                
                fingerprint = self.pg_repo.get_fingerprint(table_name, entity_id)
                if not fingerprint or fingerprint.checksum != domain_model.checksum:
                    pg_data = DataMapper.map_to_pg(table_name, domain_model, settings.SOURCE_SYSTEM)
                    self.pg_repo.upsert(config["pg_model"], pg_data, config["pg_pk"])
                    self.pg_repo.update_fingerprint(table_name, entity_id, domain_model.checksum)
                    updated_count += 1
                
                if updated_count > 0 and updated_count % 100 == 0:
                    self.pg_repo.commit()
            except Exception as e:
                logger.error("Failed to reconcile row", table=table_name, error=str(e), row=row)
                continue

        self.pg_repo.commit()
        logger.info("Reconciliation completed", table=table_name, updated=updated_count)

    def sync_table_full(self, table_name: str):
        if not self.pg_repo: raise RuntimeError("PG Repo not set")
        config = DataMapper.MAPPING[table_name]
        logger.info("Starting full scan sync", table=table_name)

        rows = self.mdb_repo.get_full_scan(table_name)
        
        processed_count = 0
        for i, row in enumerate(rows):
            try:
                domain_model = DataMapper.map_to_domain(table_name, row)
                entity_id = getattr(domain_model, config["pg_pk"])
                
                fingerprint = self.pg_repo.get_fingerprint(table_name, entity_id)
                if not fingerprint or fingerprint.checksum != domain_model.checksum:
                    pg_data = DataMapper.map_to_pg(table_name, domain_model, settings.SOURCE_SYSTEM)
                    self.pg_repo.upsert(config["pg_model"], pg_data, config["pg_pk"])
                    self.pg_repo.update_fingerprint(table_name, entity_id, domain_model.checksum)
                    processed_count += 1
                
                if processed_count > 0 and processed_count % 100 == 0:
                    self.pg_repo.commit()
            except Exception as e:
                logger.error("Failed to sync master row", table=table_name, error=str(e), row=row)
                continue

        self.pg_repo.commit()
        logger.info("Full scan sync completed", table=table_name, processed=processed_count)
