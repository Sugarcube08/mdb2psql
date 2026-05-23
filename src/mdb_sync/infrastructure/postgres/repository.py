from typing import List, Optional, Type, TypeVar, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from src.mdb_sync.infrastructure.postgres.models import Base, SyncState, SyncFingerprint
from datetime import datetime

T = TypeVar("T", bound=Base)

class PostgresRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, model_class: Type[T], data: dict, unique_col: str):
        unique_val = data.get(unique_col)
        stmt = select(model_class).where(getattr(model_class, unique_col) == unique_val)
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
        else:
            new_obj = model_class(**data)
            self.session.add(new_obj)

    def get_sync_state(self, table_name: str) -> Optional[SyncState]:
        return self.session.get(SyncState, table_name)

    def update_sync_state(self, table_name: str, last_pk: Optional[str]):
        state = self.get_sync_state(table_name)
        if state:
            state.last_pk = last_pk
            state.last_sync_at = datetime.utcnow()
        else:
            state = SyncState(table_name=table_name, last_pk=last_pk, last_sync_at=datetime.utcnow())
            self.session.add(state)

    def get_fingerprint(self, table_name: str, entity_id: str) -> Optional[SyncFingerprint]:
        return self.session.get(SyncFingerprint, (table_name, entity_id))

    def update_fingerprint(self, table_name: str, entity_id: str, checksum: str):
        fingerprint = self.get_fingerprint(table_name, entity_id)
        if fingerprint:
            fingerprint.checksum = checksum
            fingerprint.last_seen_at = datetime.utcnow()
        else:
            fingerprint = SyncFingerprint(
                table_name=table_name,
                entity_id=entity_id,
                checksum=checksum,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow()
            )
            self.session.add(fingerprint)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
