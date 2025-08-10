# -*- coding: utf-8 -*-
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CONTRACTS_FILE = DATA_DIR / "contracts.json"
CARRIERS_FILE = DATA_DIR / "carriers.json"
BACKUP_DIR = DATA_DIR / "backup"
