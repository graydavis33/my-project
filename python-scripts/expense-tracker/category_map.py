"""Deterministic Plaid personal_finance_category -> payday-checklist category.
Returns None for anything that isn't a discretionary budget expense (income,
transfers, rent, loan payments) so the scanner drops it."""

from config import CATEGORY_OVERRIDES

# Plaid PRIMARY category -> app category. None = exclude from the budget.
_PRIMARY = {
    "INCOME": None,
    "TRANSFER_IN": None,
    "TRANSFER_OUT": None,
    "LOAN_PAYMENTS": None,
    "BANK_FEES": "Misc",
    "ENTERTAINMENT": "Misc",
    "FOOD_AND_DRINK": "Dining Out",
    "GENERAL_MERCHANDISE": "Misc",
    "GENERAL_SERVICES": "Misc",
    "GOVERNMENT_AND_NON_PROFIT": "Misc",
    "HOME_IMPROVEMENT": "Misc",
    "MEDICAL": "Misc",
    "PERSONAL_CARE": "Misc",
    "RENT_AND_UTILITIES": "Utilities",   # rent split out in _DETAILED
    "TRANSPORTATION": "Misc",
    "TRAVEL": "Misc",
}

# DETAILED category overrides (more specific than primary).
_DETAILED = {
    "FOOD_AND_DRINK_GROCERIES": "Groceries",
    "RENT_AND_UTILITIES_RENT": None,     # rent tracked separately in the app
}


def map_category(primary, detailed, vendor):
    v = (vendor or "").lower()
    for match, cat in CATEGORY_OVERRIDES.items():
        if match.lower() in v:
            return cat
    if detailed in _DETAILED:
        return _DETAILED[detailed]
    return _PRIMARY.get(primary, "Misc")
