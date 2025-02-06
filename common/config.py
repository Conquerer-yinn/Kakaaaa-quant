import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# API configuration
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")

# Output configuration
MASTER_DATA_DIR = os.path.join(BASE_DIR, "storage", "data_master")
BACKUP_DIR = os.path.join(BASE_DIR, "storage", "backups")
