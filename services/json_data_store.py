import json
import os
import threading

# Define file paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CARRIERS_FILE = os.path.join(DATA_DIR, 'carriers.json')
CONTRACTS_FILE = os.path.join(DATA_DIR, 'contracts.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Simple lock for file operations to prevent race conditions
file_locks = {
    USERS_FILE: threading.Lock(),
    CARRIERS_FILE: threading.Lock(),
    CONTRACTS_FILE: threading.Lock(),
}

def load_data(filepath):
    """Loads data from a JSON file."""
    with file_locks[filepath]:
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(filepath, data):
    """Saves data to a JSON file."""
    with file_locks[filepath]:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def generate_next_id(data_list, id_key='id'):
    """Generates the next available integer ID for a list of dictionaries.
    Optionally specify id_key if the ID field has a different name.
    """
    if not data_list:
        return 1
    return max(item.get(id_key, 0) for item in data_list) + 1

def initialize_data_files():
    """Ensures that the data JSON files exist and are initialized as empty lists if they don't."""
    for filepath in [USERS_FILE, CARRIERS_FILE, CONTRACTS_FILE]:
        if not os.path.exists(filepath) or not load_data(filepath):
            save_data(filepath, [])

def generate_contract_id():
    """Generates a unique contract ID (e.g., 'C-YYYYMMDD-XXXX')."""
    today = date.today().strftime('%Y%m%d')
    contracts = load_data(CONTRACTS_FILE)
    # Find the highest existing sequence number for today
    max_seq = 0
    for contract in contracts:
        contract_id = contract.get('contract_id', '')
        if contract_id.startswith(f'C-{today}-'):
            try:
                seq = int(contract_id.split('-')[-1])
                if seq > max_seq:
                    max_seq = seq
            except ValueError:
                pass
    return f'C-{today}-{max_seq + 1:04d}'

from datetime import date
