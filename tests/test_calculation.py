import unittest
from datetime import date
from app import Contract # Import Contract from app.py

class TestFinancialCalculations(unittest.TestCase):

    def test_basic_balance_calculation(self):
        """基本的な収支計算が正しいことをテストする"""
        contract = Contract(
            contract_id='c1',
            contract_date=date(2023, 1, 1),
            scheduled_termination_date=date(2023, 7, 1),
            initial_fee=3300,
            first_month_cost=1000,
            monthly_cost=2000,
            cashback_amount=5000,
            device_cost=10000,
            device_resale_value=8000
        )
        # 維持月数 = 7ヶ月 (1/1から7/1まで)
        # 支出 = 3300 + 1000 + (2000 * 7) + 10000 = 28300
        # 収入 = 5000 + 8000 = 13000
        # 収支 = 13000 - 28300 = -15300
        financials = contract.calculate_financials() # Call method on instance
        self.assertEqual(financials['planned_days'], 181)
        self.assertEqual(financials['planned_months'], 7)
        self.assertEqual(financials['balance'], -15300)

    def test_calculation_with_missing_dates(self):
        """日付がNoneの場合に計算結果がNoneになることをテストする"""
        contract = Contract(
            contract_id='c2',
            contract_date=None,
            scheduled_termination_date=None
        )
        financials = contract.calculate_financials() # Call method on instance
        self.assertIsNone(financials['planned_days'])
        self.assertIsNone(financials['planned_months'])
        self.assertIsNone(financials['balance'])

    def test_calculation_with_missing_numeric_values(self):
        """数値データがNoneの場合に0として扱われることをテストする"""
        contract = Contract(
            contract_id='c3',
            contract_date=date(2023, 1, 1),
            scheduled_termination_date=date(2023, 2, 1),
            initial_fee=3300,
            first_month_cost=1000,
            monthly_cost=2000,
            cashback_amount=None, # None
            device_cost=None,       # None
            device_resale_value=None # None
        )
        # 維持月数 = 2ヶ月
        # 支出 = 3300 + 1000 + (2000 * 2) + 0 = 8300
        # 収入 = 0 + 0 = 0
        # 収支 = 0 - 8300 = -8300
        financials = contract.calculate_financials() # Call method on instance
        self.assertEqual(financials['planned_months'], 2)
        self.assertEqual(financials['balance'], -8300)

if __name__ == '__main__':
    unittest.main()
