# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Optional, Dict, Any
from models.contract import Contract
from config.settings import CONTRACTS_FILE
from utils.json_utils import load_json, save_json
from utils.date_utils import days_between, months_ceil_between

def load_contracts() -> List[Contract]:
    data = load_json(Path(CONTRACTS_FILE))
    return [Contract.from_dict(d) for d in data]

def save_contracts(contracts: List[Contract]):
    data = [c.to_dict() for c in contracts]
    save_json(Path(CONTRACTS_FILE), data)

def add_contract(contract: Contract):
    contracts = load_contracts()
    contracts.append(contract)
    save_contracts(contracts)

def find_contract_by_id(cid: str) -> Optional[Contract]:
    for c in load_contracts():
        if c.contract_id == cid:
            return c
    return None

def calculate_financials(contract: Contract) -> Dict[str, Any]:
    planned_days = days_between(contract.contract_date, contract.scheduled_termination_date)
    planned_months = months_ceil_between(contract.contract_date, contract.scheduled_termination_date)

    balance = None
    if planned_months is not None:
        try:
            initial_fee = contract.initial_fee or 0
            first_month_cost = contract.first_month_cost or 0
            monthly_cost = contract.monthly_cost or 0
            cashback_amount = contract.cashback_amount or 0
            device_cost = contract.device_cost or 0
            device_resale_value = contract.device_resale_value or 0

            balance = ((cashback_amount + device_resale_value) -
                       (initial_fee + first_month_cost + (monthly_cost * planned_months) + device_cost))
        except TypeError:
            balance = None

    return {
        'planned_days': planned_days,
        'planned_months': planned_months,
        'balance': balance
    }




def update_contract(updated_contract: Contract):
    contracts = load_contracts()
    for i, c in enumerate(contracts):
        if c.contract_id == updated_contract.contract_id:
            contracts[i] = updated_contract
            break
    save_contracts(contracts)

def delete_contract(cid: str):
    contracts = load_contracts()
    contracts = [c for c in contracts if c.contract_id != cid]
    save_contracts(contracts)
