# Install Service
# This script uses NSSM to install the MDB Sync worker as a Windows Service

$NSSM = "C:\tools\nssm.exe" # Path to nssm.exe
$SERVICE_NAME = "MDBSyncService"
$PYTHON_PATH = "C:\Path\To\Your\dbupdater\.venv\Scripts\python.exe"
$SCRIPT_PATH = "C:\Path\To\Your\dbupdater\src\mdb_sync\main.py"
$WORK_DIR = "C:\Path\To\Your\dbupdater"

& $NSSM install $SERVICE_NAME $PYTHON_PATH
& $NSSM set $SERVICE_NAME AppParameters "-m src.mdb_sync.main"
& $NSSM set $SERVICE_NAME AppDirectory $WORK_DIR
& $NSSM set $SERVICE_NAME Start SERVICE_AUTO_START
& $NSSM start $SERVICE_NAME

Write-Host "Service $SERVICE_NAME installed and started."
