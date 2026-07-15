import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-unit-tests")

from category_map import map_category

def test_groceries_uses_detailed():
    assert map_category("FOOD_AND_DRINK", "FOOD_AND_DRINK_GROCERIES", "Whole Foods") == "Groceries"

def test_restaurant_is_dining():
    assert map_category("FOOD_AND_DRINK", "FOOD_AND_DRINK_RESTAURANT", "Joe's Pizza") == "Dining Out"

def test_rent_is_excluded():
    assert map_category("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_RENT", "Ohana Housing") is None

def test_utilities_kept():
    assert map_category("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY", "Con Ed") == "Utilities"

def test_income_and_transfers_excluded():
    assert map_category("INCOME", "INCOME_WAGES", "Payroll") is None
    assert map_category("TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", "Edward Jones") is None
    assert map_category("LOAN_PAYMENTS", "LOAN_PAYMENTS_STUDENT_LOAN", "Nelnet") is None

def test_vendor_override_wins():
    # Plaid would call Adobe GENERAL_SERVICES; the override forces Software & Tools
    assert map_category("GENERAL_SERVICES", "GENERAL_SERVICES_OTHER", "Adobe Inc") == "Software & Tools"

def test_unknown_primary_falls_to_misc():
    assert map_category("SOMETHING_NEW", None, "Mystery") == "Misc"

def test_general_merchandise_is_misc():
    assert map_category("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_OTHER", "Target") == "Misc"
