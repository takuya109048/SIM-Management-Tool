# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import json
from services.json_data_store import load_data, save_data, USERS_FILE, CARRIERS_FILE, CONTRACTS_FILE, generate_next_id, generate_contract_id, initialize_data_files
from utils.date_utils import days_between, months_ceil_between

# App initialization
app = Flask(__name__)
# It's recommended to move this to an environment variable or a config file
app.config['SECRET_KEY'] = 'a_very_secret_key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'このページにアクセスするにはログインしてください。'

# Models
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Carrier:
    def __init__(self, id, carrier_name, user_id):
        self.id = id
        self.carrier_name = carrier_name
        self.user_id = user_id
        self.plans = [] # Will be populated separately

class Plan:
    def __init__(self, id, plan_name, initial_fee, minimum_maintenance_period, carrier_id):
        self.id = id
        self.plan_name = plan_name
        self.initial_fee = initial_fee
        self.minimum_maintenance_period = minimum_maintenance_period
        self.carrier_id = carrier_id

class Contract:
    def __init__(self, id, contract_id, contract_date, scheduled_termination_date,\
                 phone_number, contractor_name, carrier_name, plan_name, sim_id_last_5_digits,
                 initial_fee, first_month_cost, monthly_cost, cashback_amount, device_type,
                 device_cost, device_resale_value, memo, user_id):
        self.id = id
        self.contract_id = contract_id
        
        self.contract_date = contract_date
        self.scheduled_termination_date = scheduled_termination_date
        self.phone_number = phone_number
        self.contractor_name = contractor_name
        self.carrier_name = carrier_name
        self.plan_name = plan_name
        self.sim_id_last_5_digits = sim_id_last_5_digits
        self.initial_fee = initial_fee
        self.first_month_cost = first_month_cost
        self.monthly_cost = monthly_cost
        self.cashback_amount = cashback_amount
        self.device_type = device_type
        self.device_cost = device_cost
        self.device_resale_value = device_resale_value
        self.memo = memo
        self.user_id = user_id

    def calculate_financials(self):
        contract_duration_months = None # Initialize to None
        if self.contract_date and self.scheduled_termination_date:
            contract_duration_months = months_ceil_between(self.contract_date, self.scheduled_termination_date)

        total_monthly_costs = (self.monthly_cost or 0) * (contract_duration_months if contract_duration_months is not None else 0) # Handle None for multiplication

        total_cost = (
            (self.initial_fee or 0) +
            (self.first_month_cost or 0) +
            total_monthly_costs +
            (self.device_cost or 0) -
            (self.cashback_amount or 0) -
            (self.device_resale_value or 0)
        )
        
        # If contract_duration_months is None, total_cost should also be None
        if contract_duration_months is None:
            total_cost = None

        return {
            'contract_duration_months': contract_duration_months,
            'total_cost': -total_cost if total_cost is not None else None # Negate only if not None
        }

@login_manager.user_loader
def load_user(user_id):
    users_data = load_data(USERS_FILE)
    for user_dict in users_data:
        if user_dict['id'] == int(user_id):
            return User(**user_dict)
    return None

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users_data = load_data(USERS_FILE)
        user = None
        for u_data in users_data:
            if u_data['username'] == username:
                user = User(**u_data)
                break

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが無効です')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_data(USERS_FILE)
        if any(u['username'] == username for u in users):
            flash('ユーザー名はすでに存在します')
        else:
            new_user_id = generate_next_id(users)
            new_user_data = {
                'id': new_user_id,
                'username': username,
                'password_hash': generate_password_hash(password)
            }
            users.append(new_user_data)
            save_data(USERS_FILE, users)
            flash('登録が完了しました。ログインしてください。')
            return redirect(url_for('login'))
    return render_template('register.html')

def add_default_carrier_data():
    print("--- add_default_carrier_data() called ---")
    users = load_data(USERS_FILE)
    if not users:
        print("No users found. Please register a user first.")
        return

    default_user_id = users[0]['id']
    print(f"Default user ID: {default_user_id}")

    carriers = load_data(CARRIERS_FILE)

    # Check if default carriers already exist for this user
    if not any(c.get('user_id') == default_user_id for c in carriers):
        print("Adding default carrier and plan data...")

        # Create carrier dictionaries with nested plans
        docomo_plans = []
        docomo_plans.append({'id': generate_next_id(docomo_plans), 'plan_name': 'ギガホ プレミア', 'initial_fee': 3300, 'minimum_maintenance_period': 0})
        docomo_plans.append({'id': generate_next_id(docomo_plans), 'plan_name': 'ahamo', 'initial_fee': 0, 'minimum_maintenance_period': 0})
        carrier_docomo = {'id': generate_next_id(carriers), 'carrier_name': 'ドコモ', 'user_id': default_user_id, 'plans': docomo_plans}
        carriers.append(carrier_docomo)

        au_plans = []
        au_plans.append({'id': generate_next_id(au_plans), 'plan_name': '使い放題MAX 5G', 'initial_fee': 3300, 'minimum_maintenance_period': 0})
        au_plans.append({'id': generate_next_id(au_plans), 'plan_name': 'povo2.0', 'initial_fee': 0, 'minimum_maintenance_period': 0})
        carrier_au = {'id': generate_next_id(carriers), 'carrier_name': 'au', 'user_id': default_user_id, 'plans': au_plans}
        carriers.append(carrier_au)

        softbank_plans = []
        softbank_plans.append({'id': generate_next_id(softbank_plans), 'plan_name': 'メリハリ無制限+', 'initial_fee': 3300, 'minimum_maintenance_period': 0})
        softbank_plans.append({'id': generate_next_id(softbank_plans), 'plan_name': 'LINEMO', 'initial_fee': 0, 'minimum_maintenance_period': 0})
        carrier_softbank = {'id': generate_next_id(carriers), 'carrier_name': 'ソフトバンク', 'user_id': default_user_id, 'plans': softbank_plans}
        carriers.append(carrier_softbank)

        rakuten_plans = []
        rakuten_plans.append({'id': generate_next_id(rakuten_plans), 'plan_name': 'Rakuten最強プラン', 'initial_fee': 0, 'minimum_maintenance_period': 0})
        carrier_rakuten = {'id': generate_next_id(carriers), 'carrier_name': '楽天モバイル', 'user_id': default_user_id, 'plans': rakuten_plans}
        carriers.append(carrier_rakuten)

        save_data(CARRIERS_FILE, carriers)
        print("Default carriers and plans saved. Current carriers:", carriers)
    else:
        print("Default carrier and plan data already exists for the first user.")
    print("--- add_default_carrier_data() finished ---")

def get_chain_financials(current_contract_data, all_contracts_raw):
    chain_total_cost = 0
    
    phone_number_to_match = current_contract_data.get('phone_number')
    if not phone_number_to_match:
        return 0 # Cannot calculate chain financials without a phone number

    # Get the contract_date of the current contract being processed
    reference_contract_date_str = current_contract_data.get('contract_date')
    reference_contract_date = None
    if reference_contract_date_str:
        try:
            reference_contract_date = date.fromisoformat(reference_contract_date_str)
        except ValueError:
            pass # Handle invalid date string

    # Filter contracts by phone number AND contract_date <= reference_contract_date
    # Only include contracts that started on or before the current contract's date
    filtered_contracts = []
    for c in all_contracts_raw:
        if c.get('phone_number') == phone_number_to_match:
            contract_date_str = c.get('contract_date')
            contract_date_obj = None
            if contract_date_str:
                try:
                    contract_date_obj = date.fromisoformat(contract_date_str)
                except ValueError:
                    pass
            
            # Include if contract_date is valid and <= reference_contract_date, or if reference_contract_date is invalid/missing
            if contract_date_obj and reference_contract_date and contract_date_obj <= reference_contract_date:
                filtered_contracts.append(c)
            elif not reference_contract_date: # If reference_contract_date is invalid/missing, include all contracts with matching phone number
                filtered_contracts.append(c)


    # Sort related contracts by contract_date and then scheduled_termination_date
    # Convert date strings to date objects for proper sorting
    def get_sort_key(contract):
        contract_date_str = contract.get('contract_date')
        scheduled_termination_date_str = contract.get('scheduled_termination_date')
        
        contract_date_obj = None
        if contract_date_str:
            try:
                contract_date_obj = date.fromisoformat(contract_date_str)
            except ValueError:
                pass
        
        scheduled_termination_date_obj = None
        if scheduled_termination_date_str:
            try:
                scheduled_termination_date_obj = date.fromisoformat(scheduled_termination_date_str)
            except ValueError:
                pass
        
        # Use a tuple for sorting: (contract_date, scheduled_termination_date)
        # None dates should be handled gracefully, e.g., by placing them at the end
        return (contract_date_obj if contract_date_obj else date.max, 
                scheduled_termination_date_obj if scheduled_termination_date_obj else date.max)

    filtered_contracts.sort(key=get_sort_key)

    # Calculate total cost for all related contracts
    for contract_data in filtered_contracts: # Iterate over filtered_contracts
        temp_contract_data = contract_data.copy()
        # Remove previous_contract_id if it exists, as Contract.__init__ no longer accepts it
        if 'previous_contract_id' in temp_contract_data:
            del temp_contract_data['previous_contract_id']
        if 'contract_date' in temp_contract_data and temp_contract_data['contract_date']:
            try:
                temp_contract_data['contract_date'] = date.fromisoformat(temp_contract_data['contract_date'])
            except ValueError:
                pass
        if 'scheduled_termination_date' in temp_contract_data and temp_contract_data['scheduled_termination_date']:
            try:
                temp_contract_data['scheduled_termination_date'] = date.fromisoformat(temp_contract_data['scheduled_termination_date'])
            except ValueError:
                pass

        temp_contract_obj = Contract(**temp_contract_data)
        chain_total_cost += temp_contract_obj.calculate_financials()['total_cost']
            
    return chain_total_cost

@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '')
    all_contracts_data = load_data(CONTRACTS_FILE)
    user_contracts_data = [c for c in all_contracts_data if c.get('user_id') == current_user.id]

    contracts = []
    for contract_data in user_contracts_data:
        # Remove previous_contract_id if it exists, as Contract.__init__ no longer accepts it
        if 'previous_contract_id' in contract_data:
            del contract_data['previous_contract_id']
        # Convert date strings back to date objects
        if 'contract_date' in contract_data and contract_data['contract_date']:
            contract_data['contract_date'] = date.fromisoformat(contract_data['contract_date'])
        if 'scheduled_termination_date' in contract_data and contract_data['scheduled_termination_date']:
            contract_data['scheduled_termination_date'] = date.fromisoformat(contract_data['scheduled_termination_date'])
        contracts.append(Contract(**contract_data))

    if search_query:
        contracts = [
            c for c in contracts
            if (c.carrier_name and search_query.lower() in c.carrier_name.lower()) or \
               (c.phone_number and search_query.lower() in c.phone_number.lower())
        ]

    contracts_with_financials = []
    all_contracts_raw = load_data(CONTRACTS_FILE) # Load raw data once for get_chain_financials
    for contract in contracts:
        financials = contract.calculate_financials()
        
        # Find the raw contract data for the current contract to pass to get_chain_financials
        current_contract_raw_data = next((c for c in all_contracts_raw if c.get('contract_id') == contract.contract_id), None)
        
        chain_total_balance = 0
        if current_contract_raw_data:
            chain_total_balance = get_chain_financials(current_contract_raw_data, all_contracts_raw)

        contract_duration_days = None
        if contract.contract_date and contract.scheduled_termination_date:
            contract_duration_days = (contract.scheduled_termination_date - contract.contract_date).days

        contracts_with_financials.append({
            'contract': contract,
            'financials': financials,
            'chain_total_balance': chain_total_balance, # Add chain total balance
            'contract_duration_days': contract_duration_days
        })
    return render_template('index.html', contracts_data=contracts_with_financials, search_query=search_query)


import json


@app.route('/contract/new', methods=['GET', 'POST'])
@login_required
def new_contract():
    print("--- new_contract route called ---")
    all_carriers_data_for_js = []
    all_carriers_data = load_data(CARRIERS_FILE)

    user_carriers_data = [c for c in all_carriers_data if c.get('user_id') == current_user.id]
    print(f"User carriers data (raw): {user_carriers_data}")

    for carrier_data in user_carriers_data:
        carrier_dict = {
            'carrier_name': carrier_data.get('carrier_name', ''),
            'plans': []
        }
        # Plans are now directly in carrier_data['plans']
        if 'plans' in carrier_data and isinstance(carrier_data['plans'], list):
            for plan_data in carrier_data['plans']:
                plan_dict = {
                    'plan_name': plan_data.get('plan_name', ''),
                    'initial_fee': plan_data.get('initial_fee', 0),
                    'minimum_maintenance_period': plan_data.get('minimum_maintenance_period', 0)
                }
                carrier_dict['plans'].append(plan_dict)
        all_carriers_data_for_js.append(carrier_dict)
    
    print(f"all_carriers_data_for_js (prepared for JS): {all_carriers_data_for_js}")

    # Ensure all elements are plain dictionaries and values are serializable
    final_carriers_data_for_js = []
    for carrier_dict in all_carriers_data_for_js:
        new_carrier_dict = {
            'carrier_name': carrier_dict.get('carrier_name', ''),
            'plans': []
        }
        for plan_dict in carrier_dict.get('plans', []):
            new_carrier_dict['plans'].append({
                'plan_name': plan_dict.get('plan_name', ''),
                'initial_fee': plan_dict.get('initial_fee', 0),
                'minimum_maintenance_period': plan_dict.get('minimum_maintenance_period', 0)
            })
        final_carriers_data_for_js.append(new_carrier_dict)

    print(f"final_carriers_data_for_js (after explicit conversion): {final_carriers_data_for_js}")

    all_user_contracts = [c for c in load_data(CONTRACTS_FILE) if c.get('user_id') == current_user.id]
    
    

    if request.method == 'POST':
        contracts = load_data(CONTRACTS_FILE)
        new_contract_id_val = generate_contract_id()
        new_contract_data = {
            'id': generate_next_id(contracts),
            'contract_id': new_contract_id_val,
            'contract_date': request.form.get('contract_date'),
            'scheduled_termination_date': request.form.get('scheduled_termination_date'),
            'phone_number': request.form.get('phone_number'),
            'contractor_name': request.form.get('contractor_name'),
            'carrier_name': request.form.get('carrier_name'),
            'plan_name': request.form.get('plan_name'),
            'sim_id_last_5_digits': request.form.get('sim_id_last_5_digits'),
            'initial_fee': int(request.form.get('initial_fee') or 0),
            'first_month_cost': int(request.form.get('first_month_cost') or 0),
            'monthly_cost': int(request.form.get('monthly_cost') or 0),
            'cashback_amount': int(request.form.get('cashback_amount') or 0),
            'device_type': request.form.get('device_type'),
            'device_cost': int(request.form.get('device_cost') or 0),
            'device_resale_value': int(request.form.get('device_resale_value') or 0),
            'memo': request.form.get('memo'),
            'user_id': current_user.id
        }
        contracts.append(new_contract_data)
        save_data(CONTRACTS_FILE, contracts)
        flash('契約が正常に追加されました。', 'success')
        return redirect(url_for('index'))
    
    return render_template('contract_form.html', form_title='新規契約', contract={}, all_carriers=final_carriers_data_for_js)

@app.route('/contract/edit/<string:contract_id>', methods=['GET', 'POST'])
@login_required
def edit_contract(contract_id):
    contracts = load_data(CONTRACTS_FILE)
    contract_data = next((c for c in contracts if c.get('contract_id') == contract_id and c.get('user_id') == current_user.id), None)
    if not contract_data:
        # Simulate 404 if contract not found
        flash('契約が見つかりません。', 'danger')
        return redirect(url_for('index'))

    # Convert contract_data dict to Contract object for form display and calculate_financials
    # Remove previous_contract_id if it exists, as Contract.__init__ no longer accepts it
    if 'previous_contract_id' in contract_data:
        del contract_data['previous_contract_id']
    contract = Contract(**contract_data)
    if 'contract_date' in contract_data and contract_data['contract_date']:
        contract.contract_date = date.fromisoformat(contract_data['contract_date'])
    if 'scheduled_termination_date' in contract_data and contract_data['scheduled_termination_date']:
        contract.scheduled_termination_date = date.fromisoformat(contract_data['scheduled_termination_date'])


    all_carriers_data_for_js = []
    all_carriers_data = load_data(CARRIERS_FILE)

    user_carriers_data = [c for c in all_carriers_data if c.get('user_id') == current_user.id]

    for carrier_data in user_carriers_data:
        carrier_dict = {
            'carrier_name': carrier_data.get('carrier_name', ''),
            'plans': []
        }
        # Plans are now directly in carrier_data['plans']
        if 'plans' in carrier_data and isinstance(carrier_data['plans'], list):
            for plan_data in carrier_data['plans']:
                plan_dict = {
                    'plan_name': plan_data.get('plan_name', ''),
                    'initial_fee': plan_data.get('initial_fee', 0),
                    'minimum_maintenance_period': plan_data.get('minimum_maintenance_period', 0)
                }
                carrier_dict['plans'].append(plan_dict)
        all_carriers_data_for_js.append(carrier_dict)

    # Ensure all elements are plain dictionaries and values are serializable
    final_carriers_data_for_js = []
    for carrier_dict in all_carriers_data_for_js:
        new_carrier_dict = {
            'carrier_name': carrier_dict.get('carrier_name', ''),
            'plans': []
        }
        for plan_dict in carrier_dict.get('plans', []):
            new_carrier_dict['plans'].append({
                'plan_name': plan_dict.get('plan_name', ''),
                'initial_fee': plan_dict.get('initial_fee', 0),
                'minimum_maintenance_period': plan_dict.get('minimum_maintenance_period', 0)
            })
        final_carriers_data_for_js.append(new_carrier_dict)

    # Load all contracts for the current user
    all_user_contracts = [c for c in load_data(CONTRACTS_FILE) if c.get('user_id') == current_user.id]
    
    

    if request.method == 'POST':
        # Update the contract_data dictionary
        contract_data['contract_date'] = request.form.get('contract_date')
        contract_data['scheduled_termination_date'] = request.form.get('scheduled_termination_date')
        contract_data['phone_number'] = request.form.get('phone_number')
        contract_data['contractor_name'] = request.form.get('contractor_name')
        contract_data['carrier_name'] = request.form.get('carrier_name')
        contract_data['plan_name'] = request.form.get('plan_name')
        contract_data['sim_id_last_5_digits'] = request.form.get('sim_id_last_5_digits')
        contract_data['initial_fee'] = int(request.form.get('initial_fee') or 0)
        contract_data['first_month_cost'] = int(request.form.get('first_month_cost') or 0)
        contract_data['monthly_cost'] = int(request.form.get('monthly_cost') or 0)
        contract_data['cashback_amount'] = int(request.form.get('cashback_amount') or 0)
        contract_data['device_type'] = request.form.get('device_type')
        contract_data['device_cost'] = int(request.form.get('device_cost') or 0)
        contract_data['device_resale_value'] = int(request.form.get('device_resale_value') or 0)
        contract_data['memo'] = request.form.get('memo')

        # Save the updated list of contracts back to the file
        save_data(CONTRACTS_FILE, contracts)
        flash('契約が正常に更新されました。', 'success')
        return redirect(url_for('index'))

    return render_template('contract_form.html', form_title='契約編集', contract=contract, all_carriers=final_carriers_data_for_js)

@app.route('/contract/delete/<string:contract_id>', methods=['POST'])
@login_required
def delete_contract(contract_id):
    contracts = load_data(CONTRACTS_FILE)
    initial_len = len(contracts)
    contracts[:] = [c for c in contracts if not (c.get('contract_id') == contract_id and c.get('user_id') == current_user.id)]

    if len(contracts) < initial_len:
        save_data(CONTRACTS_FILE, contracts)
        flash('契約が正常に削除されました。', 'success')
    else:
        flash('契約が見つからないか、認証されていません。', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    initialize_data_files()
    add_default_carrier_data()
    app.run(debug=True)
