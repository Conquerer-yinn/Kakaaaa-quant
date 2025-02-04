import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Output configuration
MASTER_DATA_DIR = os.path.join(BASE_DIR, "storage", "data_master")
BACKUP_DIR = os.path.join(BASE_DIR, "storage", "backups")
