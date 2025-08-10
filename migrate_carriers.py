import os
import json
from app import app, db, User, Carrier, Plan

def migrate_carriers():
    with app.app_context():
        username = input("Enter the username to associate the carriers with: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found. Please create the user first.")
            return

        carriers_file = os.path.join(os.path.dirname(__file__), 'data', 'carriers.json')
        if not os.path.exists(carriers_file):
            print("carriers.json not found. No data to migrate.")
            return

        with open(carriers_file, 'r', encoding='utf-8') as f:
            carriers_data = json.load(f)

        for carrier_data in carriers_data:
            existing_carrier = Carrier.query.filter_by(carrier_name=carrier_data['carrier_name'], user_id=user.id).first()
            if existing_carrier:
                print(f"Carrier '{carrier_data['carrier_name']}' for user '{username}' already exists. Skipping.")
                carrier_obj = existing_carrier
            else:
                carrier_obj = Carrier(
                    carrier_name=carrier_data['carrier_name'],
                    user_id=user.id
                )
                db.session.add(carrier_obj)
                db.session.commit() # Commit to get carrier_obj.id

            for plan_data in carrier_data.get('plans', []):
                existing_plan = Plan.query.filter_by(plan_name=plan_data['plan_name'], carrier_id=carrier_obj.id).first()
                if existing_plan:
                    print(f"Plan '{plan_data['plan_name']}' for carrier '{carrier_data['carrier_name']}' already exists. Skipping.")
                else:
                    plan_obj = Plan(
                        plan_name=plan_data['plan_name'],
                        initial_fee=plan_data.get('initial_fee', 0),
                        minimum_maintenance_period=plan_data.get('minimum_maintenance_period', 0),
                        carrier_id=carrier_obj.id
                    )
                    db.session.add(plan_obj)
        
        db.session.commit()
        print("Carrier and Plan data migration successful.")

if __name__ == '__main__':
    migrate_carriers()
