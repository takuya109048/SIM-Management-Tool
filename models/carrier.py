# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Plan:
    plan_name: str
    initial_fee: int
    minimum_maintenance_period: int  # days

@dataclass
class Carrier:
    carrier_name: str
    plans: List[Plan]

    @staticmethod
    def from_dict(d):
        plans = [Plan(**p) for p in d.get('plans', [])]
        return Carrier(carrier_name=d['carrier_name'], plans=plans)
