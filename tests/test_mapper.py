import uuid
from src.mdb_sync.application.mapper import DataMapper
from src.mdb_sync.domain.models import Sale
from datetime import datetime

def test_deterministic_raw_id():
    sale = Sale(
        bill_id="BILL001",
        customer_id="CUST001",
        bill_date=datetime(2023, 1, 1),
        net_amount=100.0,
        dis_amt=0.0
    )
    
    pg_data1 = DataMapper.map_to_pg("BILL_MASTER", sale, "TEST_SYSTEM")
    pg_data2 = DataMapper.map_to_pg("BILL_MASTER", sale, "TEST_SYSTEM")
    
    assert pg_data1["raw_id"] == pg_data2["raw_id"]
    assert isinstance(pg_data1["raw_id"], uuid.UUID)
    
    # Different entity ID should have different raw_id
    sale2 = Sale(
        bill_id="BILL002",
        customer_id="CUST001",
        bill_date=datetime(2023, 1, 1),
        net_amount=100.0,
        dis_amt=0.0
    )
    pg_data3 = DataMapper.map_to_pg("BILL_MASTER", sale2, "TEST_SYSTEM")
    assert pg_data1["raw_id"] != pg_data3["raw_id"]

def test_is_processed_flag():
    sale = Sale(
        bill_id="BILL001",
        customer_id="CUST001",
        bill_date=datetime(2023, 1, 1),
        net_amount=100.0,
        dis_amt=0.0
    )
    pg_data = DataMapper.map_to_pg("BILL_MASTER", sale, "TEST_SYSTEM")
    assert pg_data["is_processed"] is False
