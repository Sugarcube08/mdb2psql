import threading

# Global lock for MDB file access to prevent driver-level hangs and circular imports
mdb_lock = threading.Lock()
