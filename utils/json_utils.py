# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import Any
from datetime import date, datetime

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

def date_decoder(obj):
    for key, value in obj.items():
        if isinstance(value, str):
            try:
                obj[key] = datetime.fromisoformat(value).date()
            except (ValueError, TypeError):
                pass
    return obj

def load_json(path: Path):
    try:
        if not path.exists():
            return []
        with path.open('r', encoding='utf-8') as f:
            return json.load(f, object_hook=date_decoder)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DateEncoder)
