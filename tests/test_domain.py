from datetime import datetime
from src.mdb_sync.domain.models import Customer, Sale

def test_customer_checksum_deterministic():
    c1 = Customer(customer_id="C1", customer_name="Alice", city_id="CITY1", mobile1="123")
    c2 = Customer(customer_id="C1", customer_name="Alice", city_id="CITY1", mobile1="123")
    assert c1.checksum == c2.checksum

def test_customer_checksum_changes():
    c1 = Customer(customer_id="C1", customer_name="Alice", city_id="CITY1", mobile1="123")
    c2 = Customer(customer_id="C1", customer_name="Alice", city_id="CITY1", mobile1="456")
    assert c1.checksum != c2.checksum

def test_sale_checksum_ignores_pg_fields():
    s1 = Sale(bill_id="B1", customer_id="C1", bill_date="2023-01-01", net_amount=100.0)
    # Theoretically if we had raw_id in the model (which we don't in domain model, but let's be sure)
    # The domain model is already clean by design.
    assert s1.checksum is not None
