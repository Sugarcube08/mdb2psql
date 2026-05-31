import pyodbc
from typing import Dict, Any, Optional, Iterator
from src.mdb_sync.config import settings
from src.mdb_sync.logging_config import get_logger

logger = get_logger(__name__)

class MDBRepository:
    def __init__(self):
        self.conn_str = settings.mdb_connection_string
        self.chunk_size = 1000

    def execute_query_yield(self, query: str, params: tuple = ()) -> Iterator[Dict[str, Any]]:
        # Connection managed safely, retries at the caller level if necessary or just fail fast per chunk
        from src.mdb_sync.concurrency import mdb_lock
        
        def robust_date_handler(value):
            if value is None:
                return None
            try:
                return str(value)
            except Exception:
                return repr(value)

        rows = []
        try:
            # ACQUIRE LOCK ONLY FOR THE READ PHASE
            with mdb_lock:
                with pyodbc.connect(self.conn_str, readonly=True) as conn:
                    # MDBTools (Linux) needs manual date conversion, but the 
                    # official Microsoft Driver (Windows) handles it natively.
                    if "MDBTools" in self.conn_str:
                        conn.add_output_converter(pyodbc.SQL_TYPE_TIMESTAMP, robust_date_handler)
                        conn.add_output_converter(pyodbc.SQL_TYPE_DATE, robust_date_handler)
                    
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    columns = [column[0].strip() for column in cursor.description]
                    
                    # Fast fetch into memory to release the lock as soon as possible
                    while True:
                        try:
                            row = cursor.fetchone()
                            if row is None:
                                break
                            rows.append(dict(zip(columns, row)))
                        except Exception as e:
                            logger.error("Failed to fetch individual row from MDB", error=str(e))
                            continue
            
            # YIELD OUTSIDE THE LOCK
            # This allows other threads to acquire mdb_lock and start their read phase
            # while this thread performs the slow DataMapping and Postgres upserts.
            for row_dict in rows:
                yield row_dict

        except Exception as e:
            logger.error("MDB query failed", error=str(e), query=query)
            raise

    def get_new_records(self, table: str, pk_col: str, last_pk: Optional[str]) -> Iterator[Dict[str, Any]]:
        if "MDBTools" in self.conn_str:
            # MDBTools lacks parameterized query and ORDER BY support
            query = f"SELECT * FROM {table}"
            return self.execute_query_yield(query)
        
        if last_pk:
            query = f"SELECT * FROM {table} WHERE {pk_col} > ? ORDER BY {pk_col} ASC"
            return self.execute_query_yield(query, (last_pk,))
        else:
            query = f"SELECT * FROM {table} ORDER BY {pk_col} ASC"
            return self.execute_query_yield(query)

    def get_full_scan(self, table: str, pk_col: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        if "MDBTools" in self.conn_str:
            query = f"SELECT * FROM {table}"
            return self.execute_query_yield(query)
            
        if pk_col:
            query = f"SELECT * FROM {table} ORDER BY {pk_col} ASC"
        else:
            query = f"SELECT * FROM {table}"
        return self.execute_query_yield(query)


