# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
from services import contract_service, carrier_service
from models.contract import Contract
from utils.id_generator import generate_contract_id
from datetime import date
from dataclasses import asdict
from flask_babel import Babel, gettext

app = Flask(__name__)

def get_locale():
    return 'ja'

babel = Babel(app, locale_selector=get_locale)

@app.route('/')
def index():
    contracts = contract_service.load_contracts()
    contracts_with_financials = []
    for contract in contracts:
        financials = contract_service.calculate_financials(contract)
        contracts_with_financials.append({
            'contract': contract,
            'financials': financials
        })
    return render_template('index.html', contracts_data=contracts_with_financials)

@app.route('/contract/new', methods=['GET', 'POST'])
def new_contract():
    carriers = carrier_service.load_carriers()
    if request.method == 'POST':
        # Generate a new contract_id
        contract_id = generate_contract_id()
        
        # Create Contract object from form data
        new_contract_obj = Contract(
            contract_id=contract_id,
            previous_contract_id=request.form.get('previous_contract_id'),
            contract_date=date.fromisoformat(request.form.get('contract_date')) if request.form.get('contract_date') else None,
            scheduled_termination_date=date.fromisoformat(request.form.get('scheduled_termination_date')) if request.form.get('scheduled_termination_date') else None,
            phone_number=request.form.get('phone_number'),
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
            memo=request.form.get('memo')
        )
        contract_service.add_contract(new_contract_obj)
        return redirect(url_for('index'))
    return render_template('contract_form.html', form_title=gettext('New Contract'), contract={}, carriers=carriers, all_carriers=[asdict(c) for c in carriers])

@app.route('/contract/edit/<contract_id>', methods=['GET', 'POST'])
def edit_contract(contract_id):
    contract = contract_service.find_contract_by_id(contract_id)
    if not contract:
        return redirect(url_for('index')) # Contract not found

    carriers = carrier_service.load_carriers()

    if request.method == 'POST':
        # Update Contract object from form data
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
        
        contract_service.update_contract(contract)
        return redirect(url_for('index'))
    
    return render_template('contract_form.html', form_title=gettext('Edit Contract'), contract=contract, carriers=carriers, all_carriers=[asdict(c) for c in carriers])

@app.route('/contract/delete/<contract_id>', methods=['POST'])
def delete_contract(contract_id):
    contract_service.delete_contract(contract_id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)