import os
import shutil
from datetime import datetime

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

from common.config import BACKUP_DIR, MASTER_DATA_DIR


class ExcelHelper:
    """Excel 落表辅助函数。"""

    @staticmethod
    def ensure_storage_dirs():
        os.makedirs(MASTER_DATA_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)

    @staticmethod
    def build_storage_path(file_name, base_dir):
        ExcelHelper.ensure_storage_dirs()
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, file_name)

    @staticmethod
    def build_master_path(file_name):
        return ExcelHelper.build_storage_path(file_name, MASTER_DATA_DIR)

    @staticmethod
    def build_backup_path(file_name):
        return ExcelHelper.build_storage_path(file_name, BACKUP_DIR)

    @staticmethod
    def backup_file(file_path):
        if not os.path.exists(file_path):
            return None

        ExcelHelper.ensure_storage_dirs()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{timestamp}_{os.path.basename(file_path)}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(file_path, backup_path)
        return backup_path

