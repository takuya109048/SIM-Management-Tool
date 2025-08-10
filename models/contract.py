# -*- coding: utf-8 -*-
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import date
from utils.date_utils import months_ceil_between

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

    def calculate_financials(self):
        contract_duration_months = 0
        if self.contract_date and self.scheduled_termination_date:
            contract_duration_months = months_ceil_between(self.contract_date, self.scheduled_termination_date)

        total_monthly_costs = (self.monthly_cost or 0) * contract_duration_months

        total_cost = (
            (self.initial_fee or 0) +
            (self.first_month_cost or 0) +
            total_monthly_costs +
            (self.device_cost or 0) -
            (self.cashback_amount or 0) -
            (self.device_resale_value or 0)
        )

        return {
            'contract_duration_months': contract_duration_months,
            'total_cost': total_cost
        }

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Contract(**d)