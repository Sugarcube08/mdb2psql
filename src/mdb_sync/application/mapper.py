import uuid
from typing import Dict, Any, Optional
from datetime import datetime, date
from src.mdb_sync.domain import models
from src.mdb_sync.infrastructure.postgres import models as pg_models
from src.mdb_sync.logging_config import get_logger

logger = get_logger(__name__)

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
    def _parse_date(val: Any) -> Optional[date]:
        if val is None or val == "":
            return None

        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val

        # Convert to string and strip
        s_val = str(val).strip()

        # REQUIREMENT: split by space and use [0] index (date part), ignoring time
        parts = s_val.split()
        if not parts:
            return None

        raw_date = parts[0]

        # Robust cleaning: extract just the date pattern
        import re
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})|(\d{4}-\d{1,2}-\d{1,2})', raw_date)
        if date_match:
            raw_date = date_match.group(0)

        formats = [
            "%m/%d/%y",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(raw_date, fmt)
                return dt.date()
            except Exception:
                continue

        logger.debug("Date parsing failed", original=val, extracted=raw_date)
        return None

    @staticmethod
    def _parse_float(val: Any) -> Optional[float]:
        if val is None or val == "":
            return None
        try:
            s_val = str(val).strip()
            import re
            numeric_match = re.search(r'[-+]?\d*\.?\d+', s_val)
            if numeric_match:
                return float(numeric_match.group(0))
            return None
        except Exception:
            return None

    @staticmethod
    def map_to_domain(table_name: str, mdb_row: Dict[str, Any]) -> models.BaseEntity:
        config = DataMapper.MAPPING[table_name]
        mapped_data = {}
        
        row_lower = {k.lower(): v for k, v in mdb_row.items()}
        row_keys_lower = [k.lower() for k in mdb_row.keys()]
        
        for mdb_col, domain_col in config["fields"].items():
            if mdb_col.lower() not in row_keys_lower:
                logger.debug("COLUMN MISSING IN MDB ROW", table=table_name, column=mdb_col, available_columns=list(mdb_row.keys()))
                mapped_data[domain_col] = None
                continue

            val = mdb_row.get(mdb_col)
            if val is None:
                val = row_lower.get(mdb_col.lower())
            
            if val is not None:
                s_val = str(val).strip()
                if s_val.startswith("b'") or s_val.startswith('b"') or s_val.startswith("\\x"):
                    import re
                    val = re.sub(r'[^\x20-\x7E]', '', s_val)
                    val = re.sub(r"^b['\"](.*)['\"]$", r"\1", val)
                else:
                    val = s_val

                if isinstance(val, str):
                    val = val.strip()
                    if val == "" or val.lower() in ["none", "null", "undefined"]:
                        val = None

            if domain_col in ["bill_date", "receipt_date"]:
                val = DataMapper._parse_date(val)
            elif domain_col in ["net_amount", "amount", "discount", "dis_amt"]:
                val = DataMapper._parse_float(val)
                
            mapped_data[domain_col] = val
        
        return config["model"](**mapped_data)

    @staticmethod
    def map_to_pg(table_name: str, domain_model: models.BaseEntity, source_system: str) -> Dict[str, Any]:
        data = domain_model.model_dump()
        config = DataMapper.MAPPING[table_name]
        entity_id = str(getattr(domain_model, config["pg_pk"]))
        
        namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        data["raw_id"] = uuid.uuid5(namespace, f"{table_name}:{entity_id}")
        
        data["checksum"] = domain_model.checksum
        data["source_system"] = source_system
        data["is_processed"] = False
        return data
