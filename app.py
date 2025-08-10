# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import Babel, gettext
from datetime import date
import json
from utils.id_generator import generate_contract_id
from utils.date_utils import days_between, months_ceil_between

# App initialization
app = Flask(__name__)
# It's recommended to move this to an environment variable or a config file
app.config['SECRET_KEY'] = 'a_very_secret_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = gettext('Please log in to access this page.')

def get_locale():
    return 'ja'

babel = Babel(app, locale_selector=get_locale)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Carrier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carrier_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plans = db.relationship('Plan', backref='carrier', lazy=True)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(100), nullable=False)
    initial_fee = db.Column(db.Integer)
    minimum_maintenance_period = db.Column(db.Integer)
    carrier_id = db.Column(db.Integer, db.ForeignKey('carrier.id'), nullable=False)

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(50), unique=True, nullable=False)
    previous_contract_id = db.Column(db.String(50))
    contract_date = db.Column(db.Date)
    scheduled_termination_date = db.Column(db.Date)
    phone_number = db.Column(db.String(20))
    contractor_name = db.Column(db.String(100))
    carrier_name = db.Column(db.String(100))
    plan_name = db.Column(db.String(100))
    sim_id_last_5_digits = db.Column(db.String(5))
    initial_fee = db.Column(db.Integer)
    first_month_cost = db.Column(db.Integer)
    monthly_cost = db.Column(db.Integer)
    cashback_amount = db.Column(db.Integer)
    device_type = db.Column(db.String(100))
    device_cost = db.Column(db.Integer)
    device_resale_value = db.Column(db.Integer)
    memo = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash(gettext('Invalid username or password'))
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
        if User.query.filter_by(username=username).first():
            flash(gettext('Username already exists'))
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(gettext('Registration successful. Please log in.'))
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '')
    contracts_query = Contract.query.filter_by(user_id=current_user.id)

    if search_query:
        contracts_query = contracts_query.filter(
            (Contract.carrier_name.ilike(f'%{search_query}%')) |
            (Contract.phone_number.ilike(f'%{search_query}%'))
        )

    contracts = contracts_query.all()
    contracts_with_financials = []
    for contract in contracts:
        print(f"DEBUG: Type of contract: {type(contract)}")
        print(f"DEBUG: Dir of contract: {dir(contract)}")
        financials = contract.calculate_financials()
        contracts_with_financials.append({
            'contract': contract,
            'financials': financials
        })
    return render_template('index.html', contracts_data=contracts_with_financials, search_query=search_query)


import json
from utils.id_generator import generate_contract_id

@app.route('/contract/new', methods=['GET', 'POST'])
@login_required
def new_contract():
    all_carriers_data_for_js = []
    all_carriers = Carrier.query.filter_by(user_id=current_user.id).all()
    for carrier in all_carriers:
        if carrier is None:
            continue

        carrier_dict = {
            'carrier_name': str(carrier.carrier_name) if carrier.carrier_name is not None else '',
            'plans': []
        }

        if carrier.plans and hasattr(carrier.plans, '__iter__'):
            for plan in carrier.plans:
                if plan is None:
                    continue

                plan_data = {
                    'plan_name': str(plan.plan_name) if plan.plan_name is not None else '',
                    'initial_fee': int(plan.initial_fee) if plan.initial_fee is not None else 0,
                    'minimum_maintenance_period': int(plan.minimum_maintenance_period) if plan.minimum_maintenance_period is not None else 0
                }
                carrier_dict['plans'].append(plan_data)
        all_carriers_data_for_js.append(carrier_dict)

    if request.method == 'POST':
        new_contract_obj = Contract(
            contract_id=generate_contract_id(),
            previous_contract_id=request.form.get('previous_contract_id'),
            contract_date=date.fromisoformat(request.form.get('contract_date')) if request.form.get('contract_date') else None,
            scheduled_termination_date=date.fromisoformat(request.form.get('scheduled_termination_date')) if request.form.get('scheduled_termination_date') else None,
            phone_number=request.form.get('phone_number'),
            contractor_name=request.form.get('contractor_name'),
            carrier_name=request.form.get('carrier_name'),
            plan_name=request.form.get('plan_name'),
            sim_id_last_5_digits=request.form.get('sim_id_last_5_digits'),
            initial_fee=int(request.form.get('initial_fee') or 0),
            first_month_cost=int(request.form.get('first_month_cost') or 0),
            monthly_cost=int(request.form.get('monthly_cost') or 0),
            cashback_amount=int(request.form.get('cashback_amount') or 0),
            device_type=request.form.get('device_type'),
            device_cost=int(request.form.get('device_cost') or 0),
            device_resale_value=int(request.form.get('device_resale_value') or 0),
            memo=request.form.get('memo'),
            user_id=current_user.id
        )
        db.session.add(new_contract_obj)
        db.session.commit()
        flash(gettext('Contract added successfully.'), 'success')
        return redirect(url_for('index'))
    
    return render_template('contract_form.html', form_title=gettext('New Contract'), contract={}, all_carriers=all_carriers_data_for_js)

@app.route('/contract/edit/<string:contract_id>', methods=['GET', 'POST'])
@login_required
def edit_contract(contract_id):
    contract = Contract.query.filter_by(contract_id=contract_id, user_id=current_user.id).first_or_404()

    all_carriers_data_for_js = []
    all_carriers = Carrier.query.filter_by(user_id=current_user.id).all()
    for carrier in all_carriers:
        if carrier is None:
            continue

        carrier_dict = {
            'carrier_name': str(carrier.carrier_name) if carrier.carrier_name is not None else '',
            'plans': []
        }

        if carrier.plans and hasattr(carrier.plans, '__iter__'):
            for plan in carrier.plans:
                if plan is None:
                    continue

                plan_data = {
                    'plan_name': str(plan.plan_name) if plan.plan_name is not None else '',
                    'initial_fee': int(plan.initial_fee) if plan.initial_fee is not None else 0,
                    'minimum_maintenance_period': int(plan.minimum_maintenance_period) if plan.minimum_maintenance_period is not None else 0
                }
                carrier_dict['plans'].append(plan_data)
        all_carriers_data_for_js.append(carrier_dict)

    if request.method == 'POST':
        contract.previous_contract_id = request.form.get('previous_contract_id')
        contract.contract_date = date.fromisoformat(request.form.get('contract_date')) if request.form.get('contract_date') else None
        contract.scheduled_termination_date = date.fromisoformat(request.form.get('scheduled_termination_date')) if request.form.get('scheduled_termination_date') else None
        contract.phone_number = request.form.get('phone_number')
        contract.contractor_name = request.form.get('contractor_name')
        contract.carrier_name = request.form.get('carrier_name')
        contract.plan_name = request.form.get('plan_name')
        contract.sim_id_last_5_digits = request.form.get('sim_id_last_5_digits')
        contract.initial_fee = int(request.form.get('initial_fee') or 0)
        contract.first_month_cost = int(request.form.get('first_month_cost') or 0)
        contract.monthly_cost = int(request.form.get('monthly_cost') or 0)
        contract.cashback_amount = int(request.form.get('cashback_amount') or 0)
        contract.device_type = request.form.get('device_type')
        contract.device_cost = int(request.form.get('device_cost') or 0)
        contract.device_resale_value = int(request.form.get('device_resale_value') or 0)
        contract.memo = request.form.get('memo')
        # user_id should not be changed during edit

        db.session.commit()
        flash(gettext('Contract updated successfully.'), 'success')
        return redirect(url_for('index'))

    return render_template('contract_form.html', form_title=gettext('Edit Contract'), contract=contract, all_carriers=all_carriers_data_for_js)

@app.route('/contract/delete/<string:contract_id>', methods=['POST'])
@login_required
def delete_contract(contract_id):
    contract = Contract.query.filter_by(contract_id=contract_id, user_id=current_user.id).first_or_404()
    db.session.delete(contract)
    db.session.commit()
    flash(gettext('Contract deleted successfully.'), 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
