import hashlib
import json
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, computed_field

class BaseEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def checksum(self) -> str:
        # Get all fields except excluded ones for checksum
        data = self.model_dump(exclude={"checksum", "raw_id", "source_system", "is_processed", "created_at", "updated_at"})
        # Ensure deterministic JSON for hashing
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

class Customer(BaseEntity):
    customer_id: str
    customer_name: Optional[str] = None
    city_id: Optional[str] = None
    mobile1: Optional[str] = None

class City(BaseEntity):
    city_id: str
    city_name: Optional[str] = None
    group_id: Optional[str] = None

class Sale(BaseEntity):
    bill_id: str
    customer_id: Optional[str] = None
    bill_date: Optional[datetime] = None
    net_amount: Optional[float] = None
    dis_amt: Optional[float] = None

class Receipt(BaseEntity):
    receipt_id: str
    customer_id: Optional[str] = None
    receipt_date: Optional[datetime] = None
    amount: Optional[float] = None
    discount: Optional[float] = None
    bank_name: Optional[str] = None
    receipt_type: Optional[str] = None

class RG(BaseEntity):
    rg_id: str
    customer_id: Optional[str] = None
    rgtype: Optional[str] = None
    net_amount: Optional[float] = None
