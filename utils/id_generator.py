# -*- coding: utf-8 -*-
from datetime import datetime
import threading

_lock = threading.Lock()
_counter = 0

def generate_contract_id():
    global _counter
    with _lock:
        _counter += 1
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{ts}{_counter:04d}"
