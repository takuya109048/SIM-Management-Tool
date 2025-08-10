# -*- coding: utf-8 -*-
from pathlib import Path
import shutil, datetime
from config.settings import CONTRACTS_FILE, BACKUP_DIR

def make_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if CONTRACTS_FILE.exists():
        ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        dst = BACKUP_DIR / f"contracts_{ts}.json"
        shutil.copy(CONTRACTS_FILE, dst)
        return dst
    return None
