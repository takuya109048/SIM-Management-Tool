# -*- coding: utf-8 -*-
from pathlib import Path
from config.settings import CARRIERS_FILE
from utils.json_utils import load_json
from models.carrier import Carrier, Plan

def load_carriers():
    data = load_json(Path(CARRIERS_FILE))
    carriers = []
    for d in data:
        carriers.append(Carrier.from_dict(d))
    return carriers

def get_carrier_by_name(name: str):
    for c in load_carriers():
        if c.carrier_name == name:
            return c
    return None

def get_plans_for_carrier(name: str):
    c = get_carrier_by_name(name)
    if not c:
        return []
    return c.plans
