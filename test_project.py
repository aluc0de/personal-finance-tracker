


import pytest
from decimal import Decimal
from datetime import date

from project import parse_amount, calculate_balance, generate_summary, add_transaction

# parse_amount

def test_parse_amount_valid():
    assert parse_amount("10.50") == Decimal("10.50")
    assert parse_amount("10,50") == Decimal("10.50")

def test_parse_amount_rejects_invalid():
    with pytest.raises(ValueError):
        parse_amount("abc")
    with pytest.raises(ValueError):
        parse_amount("NaN")

# calculate_balance

def test_calculate_balance_empty():
    assert calculate_balance([]) == Decimal("0.00")

def test_calculate_balance_mixed():
    txs = [
        {"type": "income", "amount": Decimal("100.00")},
        {"type": "expense", "amount": Decimal("30.00")},
    ]
    assert calculate_balance(txs) == Decimal("70.00")

# generate_summary

def test_generate_summary_groups_expenses():
    today = date.today().isoformat()
    txs = [
        {"type": "expense", "category": "Food", "amount": Decimal("10.00"), "date": today},
        {"type": "expense", "category": "Food", "amount": Decimal("5.00"), "date": today},
        {"type": "expense", "category": "Transportation", "amount": Decimal("20.00"), "date": today},
    ]
    summary = generate_summary(txs, period="all")
    assert summary["Food"] == Decimal("15.00")
    assert summary["Transportation"] == Decimal("20.00")

def test_generate_summary_ignores_income():
    today = date.today().isoformat()
    txs = [
        {"type": "income", "category": "Paycheck", "amount": Decimal("1000.00"), "date": today},
        {"type": "expense", "category": "Food", "amount": Decimal("50.00"), "date": today},
    ]
    summary = generate_summary(txs, period="all")
    assert "Paycheck" not in summary
    assert summary["Food"] == Decimal("50.00")

# add_transaction

def test_add_transaction_returns_valid_dict():
    tx = add_transaction("25.50", "Food", "expense")
    assert tx["amount"] == Decimal("25.50")
    assert tx["category"] == "Food"
    assert tx["type"] == "expense"
    assert tx["date"] == date.today().isoformat()

def test_add_transaction_rejects_zero():
    with pytest.raises(ValueError):
        add_transaction("0", "Food", "expense")

def test_add_transaction_rejects_tiny_amount():
    with pytest.raises(ValueError):
        add_transaction("0.004", "Food", "expense")

def test_add_transaction_rejects_invalid_type():
    with pytest.raises(ValueError):
        add_transaction("10.00", "Food", "salary")

def test_add_transaction_rejects_empty_category():
    with pytest.raises(ValueError):
        add_transaction("10.00", "   ", "expense")