import pyodbc
from typing import List, Dict, Any, Optional
from src.mdb_sync.config import settings
from src.mdb_sync.logging_config import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class MDBRepository:
    def __init__(self):
        self.conn_str = settings.mdb_connection_string

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        try:
            with pyodbc.connect(self.conn_str, readonly=True) as conn:
                # Handle invalid dates by converting them to strings
                conn.add_output_converter(pyodbc.SQL_TYPE_TIMESTAMP, lambda x: str(x) if x else None)
                conn.add_output_converter(pyodbc.SQL_TYPE_DATE, lambda x: str(x) if x else None)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("MDB query failed", error=str(e), query=query)
            raise

    def get_new_records(self, table: str, pk_col: str, last_pk: Optional[str], limit: int = 1000) -> List[Dict[str, Any]]:
        # On Linux/MDBTools, ORDER BY + LIMIT/TOP is broken.
        # We do a full scan and let the SyncEngine filter by last_pk.
        if "MDBTools" in self.conn_str:
            query = f"SELECT * FROM {table}"
            return self.execute_query(query)
        
        # Windows-native path remains optimized
        if last_pk:
            query = f"SELECT TOP {limit} * FROM {table} WHERE {pk_col} > ? ORDER BY {pk_col} ASC"
            return self.execute_query(query, (last_pk,))
        else:
            query = f"SELECT TOP {limit} * FROM {table} ORDER BY {pk_col} ASC"
            return self.execute_query(query)

    def get_recent_records(self, table: str, pk_col: str, limit: int = 5000) -> List[Dict[str, Any]]:
        if "MDBTools" in self.conn_str:
            query = f"SELECT * FROM {table}"
            return self.execute_query(query)
            
        query = f"SELECT TOP {limit} * FROM {table} ORDER BY {pk_col} DESC"
        return self.execute_query(query)

    def get_full_scan(self, table: str) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {table}"
        return self.execute_query(query)
