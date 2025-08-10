import os
import json
from datetime import date
from app import app, db, User, Contract

def migrate_data():
    with app.app_context():
        username = input("Enter the username to associate the contracts with: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found. Please create the user first.")
            return

        contracts_file = os.path.join(os.path.dirname(__file__), 'data', 'contracts.json')
        if not os.path.exists(contracts_file):
            print("contracts.json not found. No data to migrate.")
            return

        with open(contracts_file, 'r', encoding='utf-8') as f:
            contracts_data = json.load(f)

        for contract_data in contracts_data:
            # Check if contract already exists
            existing_contract = Contract.query.filter_by(contract_id=contract_data['contract_id']).first()
            if existing_contract:
                print(f"Contract with ID {contract_data['contract_id']} already exists. Skipping.")
                continue

            new_contract = Contract(
                contract_id=contract_data['contract_id'],
                previous_contract_id=contract_data.get('previous_contract_id'),
                contract_date=date.fromisoformat(contract_data.get('contract_date')) if contract_data.get('contract_date') else None,
                scheduled_termination_date=date.fromisoformat(contract_data.get('scheduled_termination_date')) if contract_data.get('scheduled_termination_date') else None,
                phone_number=contract_data.get('phone_number'),
                contractor_name=contract_data.get('contractor_name'),
                carrier_name=contract_data.get('carrier_name'),
                plan_name=contract_data.get('plan_name'),
                sim_id_last_5_digits=contract_data.get('sim_id_last_5_digits'),
                initial_fee=contract_data.get('initial_fee', 0),
                first_month_cost=contract_data.get('first_month_cost', 0),
                monthly_cost=contract_data.get('monthly_cost', 0),
                cashback_amount=contract_data.get('cashback_amount', 0),
                device_type=contract_data.get('device_type'),
                device_cost=contract_data.get('device_cost', 0),
                device_resale_value=contract_data.get('device_resale_value', 0),
                memo=contract_data.get('memo'),
                user_id=user.id
            )
            db.session.add(new_contract)

        db.session.commit()
        print("Data migration successful.")

if __name__ == '__main__':
    migrate_data()
