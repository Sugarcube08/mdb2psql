# Run Locally
# Simple script to run the sync worker in the current console

Write-Host "Starting MDB Sync Worker..."
uv run python -m src.mdb_sync.main
