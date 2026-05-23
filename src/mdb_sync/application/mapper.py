from typing import Dict, Any, Type, List, Optional
from datetime import datetime
from src.mdb_sync.domain import models
from src.mdb_sync.infrastructure.postgres import models as pg_models
from src.mdb_sync.logging_config import logger

class DataMapper:
    MAPPING = {
        "BILL_MASTER": {
            "model": models.Sale,
            "pg_model": pg_models.RawSale,
            "pk": "Bill_ID",
            "pg_pk": "bill_id",
            "fields": {
                "Bill_ID": "bill_id",
                "CUSTOMER_ID": "customer_id",
                "BILL_DATE": "bill_date",
                "NET_AMOUNT": "net_amount",
                "Dis_Amt": "dis_amt",
            }
        },
        "Receipt_Master": {
            "model": models.Receipt,
            "pg_model": pg_models.RawReceipt,
            "pk": "Receipt_ID",
            "pg_pk": "receipt_id",
            "fields": {
                "Receipt_ID": "receipt_id",
                "Customer_ID": "customer_id",
                "Receipt_Date": "receipt_date",
                "Amount": "amount",
                "Discount": "discount",
                "Bank_Name": "bank_name",
                "Receipt_Type": "receipt_type",
            }
        },
        "ReturnGoods": {
            "model": models.RG,
            "pg_model": pg_models.RawRG,
            "pk": "RG_ID",
            "pg_pk": "rg_id",
            "fields": {
                "RG_ID": "rg_id",
                "CUSTOMER_ID": "customer_id",
                "RGTYPE": "rgtype",
                "NET_AMOUNT": "net_amount",
            }
        },
        "CUSTOMER_MASTER": {
            "model": models.Customer,
            "pg_model": pg_models.RawCustomer,
            "pk": "CUSTOMER_ID",
            "pg_pk": "customer_id",
            "fields": {
                "CUSTOMER_ID": "customer_id",
                "CUSTOMER_NAME": "customer_name",
                "City_ID": "city_id",
                "MOBILE1": "mobile1",
            }
        },
        "City_Master": {
            "model": models.City,
            "pg_model": pg_models.RawCity,
            "pk": "City_ID",
            "pg_pk": "city_id",
            "fields": {
                "City_ID": "city_id",
                "City_Name": "city_name",
                "Group_ID": "group_id",
            }
        }
    }

    @staticmethod
    def _parse_date(val: Any) -> Optional[datetime]:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        
        # Try parsing from string (common for mdbtools/invalid dates)
        try:
            # mdbtools often returns YYYY-MM-DD HH:MM:SS
            # Stripping everything after seconds in case of microseconds
            clean_val = str(val).split(".")[0]
            return datetime.strptime(clean_val, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                # Try simple date
                date_part = str(val).split(" ")[0]
                return datetime.strptime(date_part, "%Y-%m-%d")
            except:
                logger.warning("Could not parse date", value=val)
                return None

    @staticmethod
    def map_to_domain(table_name: str, mdb_row: Dict[str, Any]) -> models.BaseEntity:
        config = DataMapper.MAPPING[table_name]
        mapped_data = {}
        
        # Create a lowercase mapping of the mdb_row keys for case-insensitive lookup
        row_lower = {k.lower(): v for k, v in mdb_row.items()}
        
        for mdb_col, domain_col in config["fields"].items():
            # Try exact match first, then case-insensitive
            val = mdb_row.get(mdb_col)
            if val is None:
                val = row_lower.get(mdb_col.lower())
            
            # Special handling for dates
            if domain_col in ["bill_date", "receipt_date"]:
                val = DataMapper._parse_date(val)
                
            mapped_data[domain_col] = val
        
        return config["model"](**mapped_data)

    @staticmethod
    def map_to_pg(table_name: str, domain_model: models.BaseEntity, source_system: str) -> Dict[str, Any]:
        data = domain_model.model_dump()
        data["checksum"] = domain_model.checksum
        data["source_system"] = source_system
        data["is_processed"] = False
        return data
