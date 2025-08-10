# -*- coding: utf-8 -*-
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import date

@dataclass
class Contract:
    contract_id: str
    previous_contract_id: Optional[str] = None
    contract_date: Optional[date] = None
    scheduled_termination_date: Optional[date] = None
    phone_number: Optional[str] = None
    contractor_name: Optional[str] = None
    carrier_name: Optional[str] = None
    plan_name: Optional[str] = None
    sim_id_last_5_digits: Optional[str] = None
    initial_fee: Optional[int] = 0
    first_month_cost: Optional[int] = 0
    monthly_cost: Optional[int] = 0
    cashback_amount: Optional[int] = 0
    device_type: Optional[str] = None
    device_cost: Optional[int] = 0
    device_resale_value: Optional[int] = 0
    memo: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Contract(**d)