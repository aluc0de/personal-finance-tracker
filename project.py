


import csv
import json
import os
import shutil
import urllib.request
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

DATA_FILE = "finance_data.csv"
CONFIG_FILE = "finance_config.csv"
BUDGET_FILE = "finance_budgets.json"
USER_FILE = "finance_user.csv"

RED = "\033[1;31m"
RESET = "\033[0m"

SKIPPED_ROWS_COUNT = 0

INCOME_CATEGORIES = {
    "1": "Paycheck",
    "2": "Passive Income/Dividends",
    "3": "Business",
    "4": "Gifts",
    "5": "Other Income",
}

EXPENSE_CATEGORIES = {
    "1": "Rent/Mortgage",
    "2": "Food",
    "3": "Utilities",
    "4": "Transportation",
    "5": "Healthcare",
    "6": "Maintenance",
    "7": "Savings",
    "8": "Fun",
    "9": "Other Expenses",
}

POPULAR_CURRENCIES = {
    "1": ("USD", "US Dollar", "$"),
    "2": ("EUR", "Euro", "€"),
    "3": ("GBP", "British Pound", "£"),
    "4": ("JPY", "Japanese Yen", "¥"),
    "5": ("BRL", "Brazilian Real", "R$"),
    "6": ("CNY", "Chinese Yuan", "¥"),
    "7": ("CAD", "Canadian Dollar", "$"),
    "8": ("AUD", "Australian Dollar", "$"),
    "9": ("CHF", "Swiss Franc", "CHF"),
    "10": ("INR", "Indian Rupee", "₹"),
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "CAD": "$",
    "AUD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "BRL": "R$",
    "CHF": "CHF",
    "INR": "₹",
}


def print_error(message):
    print(f"\n{RED}{message}{RESET}\n")


def show_currency_list():
    print("\n--- Available Currencies ---")
    for code, name, symbol in POPULAR_CURRENCIES.values():
        print(f"  {code} - {name} ({symbol})")
    print()


def parse_amount(value):
    """Convert an amount to Decimal, accepting either a dot or comma decimal separator."""
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid amount format.")

    if not amount.is_finite():
        raise ValueError("Amount must be a finite number.")
    return amount


def load_user():
    if not os.path.exists(USER_FILE):
        return None
    try:
        with open(USER_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                return row.get("name", "").strip()
    except Exception:
        pass
    return None


def save_user(name):
    with open(USER_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name"])
        writer.writeheader()
        writer.writerow({"name": name})


def main():
    transactions = load_data()

    currency, currency_symbol = load_currency()
    if currency is None:
        while True:
            try:
                currency, currency_symbol = prompt_currency()
                save_currency(currency, currency_symbol)
                print(f"\nCurrency set to {currency} ({currency_symbol}).\n")
                break
            except ValueError as e:
                print_error(f"Error: {e}")

    user_name = load_user()
    if user_name is None:
        while True:
            name_input = input("\nPlease enter your name: ").strip()
            if not name_input:
                print_error("Name cannot be empty.")
                continue
            user_name = name_input.title()
            save_user(user_name)
            print(f"\nHello there, {user_name}!\n")
            break
    else:
        print(f"\nHello there, {user_name}!")

    print(f"\n--- Personal Finance Tracker ({currency} - {currency_symbol}) ---")
    while True:
        print(
            "\n[1] Add Transaction\n"
            "[2] View Balance\n"
            "[3] View Category Summary (Filtered by Period)\n"
            "[4] List Recent Transactions\n"
            "[5] Balance in Foreign Currency\n"
            "[6] Manage Category Budgets\n"
            "[7] Export Monthly Report\n"
            "[8] Help\n"
            "[9] Change Base Currency\n"
            "[10] Exit"
        )
        choice = input("\nChoose an option: ").strip()

        if choice.lower() == "delete":
            if delete_data():
                transactions = []
                currency = None
                currency_symbol = None
                print_error("All data deleted. Restart the program to set up again.")
                break
            continue

        if choice.lower() == "batcave":
            show_batcave()
            continue

        choice = choice.lower()

        if choice == "1":
            try:
                print("\nSelect type:\n[1] Income\n[2] Expense\n[0] Go Back")
                type_choice = input("\nChoose type option: ").strip()
                if type_choice.lower() == "back" or type_choice == "0":
                    print("\nReturning to the main menu.\n")
                    continue
                if type_choice == "1":
                    t_type = "income"
                elif type_choice == "2":
                    t_type = "expense"
                else:
                    raise ValueError("Invalid type option.")

                current_categories = get_current_categories(transactions, t_type)
                print("\nSelect a category:")
                for key, cat in current_categories.items():
                    print(f"[{key}] {cat}")
                print("[0] Go Back")

                cat_choice = input("\nChoose category option: ").strip()
                if cat_choice.lower() == "back" or cat_choice == "0":
                    print("\nReturning to the main menu.\n")
                    continue

                if cat_choice in current_categories:
                    category = current_categories[cat_choice]
                    
                    if (t_type == "income" and cat_choice == "5") or (t_type == "expense" and cat_choice == "9"):
                        custom_cat = input("\nEnter new category name (type 'back' to return): ").strip()
                        if custom_cat.lower() == "back":
                            print("\nReturning to the main menu.\n")
                            continue
                        if not custom_cat:
                            raise ValueError("Category cannot be empty.")
                        category = custom_cat.title()
                        print("\nNew category created!\n")
                else:
                    raise ValueError("Invalid category option.")

                amount_input = input("\nEnter amount (type 'back' to return): ").strip()
                if amount_input.lower() == "back":
                    print("\nReturning to the main menu.\n")
                    continue

                new_transaction = add_transaction(amount_input, category, t_type)

                if t_type == "expense":
                    check_budget_warning(transactions, category, new_transaction["amount"])
                    sign = "-"
                else:
                    sign = "+"

                append_transaction(new_transaction)
                transactions.append(new_transaction)

                print(
                    f"\nTransaction added successfully! ({sign}{currency_symbol} {new_transaction['amount']:.2f})\n"
                )

            except ValueError as e:
                print_error(f"Error: {e}")
            except OSError as e:
                print_error(f"Could not save transaction: {e}")

        elif choice == "2":
            balance = calculate_balance(transactions)
            color_prefix = RED if balance < 0 else ""
            color_suffix = RESET if balance < 0 else ""
            print(f"\nCurrent Total Balance: {color_prefix}{currency_symbol} {balance:.2f}{color_suffix}\n")

        elif choice == "3":
            print("\nSelect period:\n[1] This month\n[2] Last month\n[3] All time\n[0] Go Back")
            period_choice = input("\nChoose option: ").strip()
            if period_choice.lower() == "back" or period_choice == "0":
                print("\nReturning to the main menu.\n")
                continue
            if period_choice == "1":
                period = "this_month"
            elif period_choice == "2":
                period = "last_month"
            elif period_choice == "3":
                period = "all"
            else:
                print_error("Error: Invalid period option.")
                continue

            summary = generate_summary(transactions, period=period)
            print(f"\n--- Summary by Category ({period.replace('_', ' ').title()}) ---")
            if not summary:
                print("\n(no expenses found for this period)\n")
            else:
                sorted_summary = sorted(summary.items(), key=lambda x: x[1], reverse=True)
                print()
                for cat, total in sorted_summary:
                    print(f"{cat:<25} | {currency_symbol} {total:>8.2f}")
                print()

        elif choice == "4":
            list_transactions(transactions, currency_symbol)

        elif choice == "5":
            query_foreign_balance(transactions, currency)

        elif choice == "6":
            manage_budgets(transactions, currency_symbol)

        elif choice == "7":
            export_report(transactions, currency, currency_symbol)

        elif choice == "8" or choice.lower() == "help":
            show_help()

        elif choice == "9":
            currency, currency_symbol = convert_currency(
                transactions, currency, currency_symbol
            )

        elif choice == "10":
            print(f"\nGoodbye, {user_name}!\n")
            break

        else:
            print_error("Invalid choice. Please try again.")


def load_currency():
    if not os.path.exists(CONFIG_FILE):
        return None, None
    try:
        with open(CONFIG_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row["currency"].strip()
                symbol = row.get("symbol", "").strip()
                if not symbol:
                    symbol = CURRENCY_SYMBOLS.get(code, code)
                return code, symbol
    except Exception as e:
        print_error(f"Warning: could not read {CONFIG_FILE}: {e}")
    return None, None


def save_currency(code, symbol):
    with open(CONFIG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["currency", "symbol"])
        writer.writeheader()
        writer.writerow({"currency": code, "symbol": symbol})


def prompt_currency():
    while True:
        print("\n--- Select your currency ---\n")
        for key, (code, name, symbol) in POPULAR_CURRENCIES.items():
            print(f"[{key}] {code} - {name} ({symbol})")
        print("[11] Other (type code manually)")

        choice = input("\nChoose currency option (type '?' for list): ").strip().upper()

        if choice == "BACK":
            raise ValueError("No currency selected.")

        if choice == "?" or choice == "HELP":
            continue

        if choice in POPULAR_CURRENCIES:
            return POPULAR_CURRENCIES[choice][0], POPULAR_CURRENCIES[choice][2]

        if choice == "11":
            code = input("\nEnter ISO currency code (e.g. SEK, ZAR) (type 'back' to return): ").strip().upper()
            if code == "BACK":
                raise ValueError("No currency selected.")
            if len(code) == 3 and code.isalpha():
                symbol = input(
                    f"\nEnter symbol for {code} (e.g. kr, R$, $) (type 'back' to return): "
                ).strip()
                if symbol.lower() == "back":
                    raise ValueError("No currency selected.")
                if not symbol:
                    symbol = code
                return code, symbol
            raise ValueError("Invalid currency code. Use 3 letters.")

        if len(choice) == 3 and choice.isalpha():
            code = choice
            symbol = CURRENCY_SYMBOLS.get(code, "")
            if not symbol:
                symbol = input(
                    f"\nEnter symbol for {code} (e.g. kr, R$, $) (type 'back' to return): "
                ).strip()
                if symbol.lower() == "back":
                    raise ValueError("No currency selected.")
                if not symbol:
                    symbol = code
            return code, symbol

        raise ValueError("Invalid currency option.")


def fetch_live_rate(base_currency, target_currency):
    if base_currency == target_currency:
        return 1.0, None

    url = f"https://open.er-api.com/v6/latest/{base_currency}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("result") == "success":
                rates = data["rates"]
                if target_currency in rates:
                    return rates[target_currency], None
                else:
                    return (
                        None,
                        f"Currency '{target_currency}' not found or invalid.",
                    )
            else:
                return None, "API returned an error response."
    except Exception:
        return (
            None,
            "Could not connect to the exchange rate service. Check your internet connection.",
        )


def load_data():
    global SKIPPED_ROWS_COUNT
    SKIPPED_ROWS_COUNT = 0
    transactions = []

    if not os.path.exists(DATA_FILE):
        return transactions

    try:
        with open(DATA_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for line_num, row in enumerate(reader, start=2):
                try:
                    amount = parse_amount(row.get("amount", "")).quantize(Decimal("0.01"))
                    category = (row.get("category") or "").strip()
                    t_type = (row.get("type") or "").strip().lower()
                    transaction_date = (row.get("date") or "").strip()

                    if not transaction_date:
                        raise ValueError("missing date")
                    date.fromisoformat(transaction_date)

                    if t_type not in ("income", "expense"):
                        raise ValueError("type must be 'income' or 'expense'")
                    if not category:
                        raise ValueError("category cannot be empty")
                    if amount <= 0:
                        raise ValueError("amount must be greater than zero")

                    transactions.append({
                        "amount": amount,
                        "category": category,
                        "type": t_type,
                        "date": transaction_date,
                    })
                except (InvalidOperation, KeyError, TypeError, ValueError) as e:
                    SKIPPED_ROWS_COUNT += 1
                    print_error(
                        f"Warning: skipping invalid transaction on line {line_num} "
                        f"in {DATA_FILE}: {e}"
                    )
    except (OSError, csv.Error) as e:
        print_error(f"Warning: could not read {DATA_FILE}: {e}")

    return transactions


def append_transaction(transaction):
    try:
        is_empty = os.path.getsize(DATA_FILE) == 0
    except FileNotFoundError:
        is_empty = True

    with open(DATA_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=["amount", "category", "type", "date"]
        )
        if is_empty:
            writer.writeheader()
        writer.writerow({
            "amount": transaction["amount"],
            "category": transaction["category"],
            "type": transaction["type"],
            "date": transaction["date"],
        })


def add_transaction(amount, category, t_type):
    dec_amount = parse_amount(amount).quantize(Decimal("0.01"))

    if dec_amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if t_type not in ("income", "expense"):
        raise ValueError("Type must be either 'income' or 'expense'.")
    if not category or not category.strip():
        raise ValueError("Category cannot be empty.")

    current_date = date.today().isoformat()
    return {
        "amount": dec_amount,
        "category": category.strip().title(),
        "type": t_type,
        "date": current_date,
    }


def calculate_balance(transactions):
    balance = Decimal("0.00")
    for t in transactions:
        if t["type"] == "income":
            balance += t["amount"]
        elif t["type"] == "expense":
            balance -= t["amount"]
    return balance


def generate_summary(transactions, period="all"):
    summary = {}
    today = date.today()
    for t in transactions:
        if t["type"] == "expense":
            try:
                t_date = date.fromisoformat(t["date"])
            except ValueError:
                t_date = today

            if period == "this_month":
                if t_date.year != today.year or t_date.month != today.month:
                    continue
            elif period == "last_month":
                first_of_this = today.replace(day=1)
                last_month_day = first_of_this - timedelta(days=1)
                if t_date.year != last_month_day.year or t_date.month != last_month_day.month:
                    continue

            cat = t["category"]
            summary[cat] = summary.get(cat, Decimal("0.00")) + t["amount"]
    return summary


def get_current_categories(transactions, t_type):
    if t_type == "income":
        categories = INCOME_CATEGORIES.copy()
    else:
        categories = EXPENSE_CATEGORIES.copy()
    
    for t in transactions:
        cat = t["category"]
        if t["type"] == t_type and cat not in categories.values():
            new_key = str(len(categories) + 1)
            categories[new_key] = cat
    return categories


def list_transactions(transactions, currency_symbol):
    print("\n--- Recent Transactions ---")
    if not transactions:
        print("\n(no transactions recorded yet)\n")
        return
    recent = transactions[-10:][::-1]
    print()
    for i, t in enumerate(recent, 1):
        sign = "+" if t["type"] == "income" else "-"
        print(f"{i}. [{t['date']}] {t['type'].upper()} | {t['category']} : {sign}{currency_symbol} {t['amount']:.2f}")
    print()


def load_budgets():
    if not os.path.exists(BUDGET_FILE):
        return {}

    try:
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("the file must contain a JSON object")

        budgets = {}
        for category, value in data.items():
            amount = parse_amount(value).quantize(Decimal("0.01"))
            if amount <= 0:
                raise ValueError(f"budget for '{category}' must be greater than zero")
            budgets[category] = amount
        return budgets
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        print_error(f"Warning: could not load budgets from {BUDGET_FILE}: {e}")
        return {}


def save_budgets(budgets):
    data = {k: str(v) for k, v in budgets.items()}
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def check_budget_warning(transactions, category, new_amount):
    budgets = load_budgets()
    if category not in budgets:
        return

    summary = generate_summary(transactions, period="this_month")
    current_spent = summary.get(category, Decimal("0.00")) + new_amount
    limit = budgets[category]

    if current_spent > limit:
        print_error(f"BUDGET WARNING: You have exceeded your monthly budget for '{category}'!\n    Budget Limit: {limit:.2f} | Spent this month: {current_spent:.2f}")
    elif current_spent >= limit * Decimal("0.8"):
        print_error(f"BUDGET NOTICE: You are close to your monthly budget for '{category}' ({current_spent:.2f} / {limit:.2f})")


def manage_budgets(transactions, currency_symbol):
    while True:
        print("\n--- Budget Management ---")
        print("[1] View Current Budgets\n[2] Set/Update Budget\n[3] Remove Budget\n[4] Back to Main Menu\n[0] Go Back")
        choice = input("\nChoose option: ").strip()
        if choice.lower() == "back" or choice == "0" or choice == "4":
            print("\nReturning to the main menu.\n")
            break
        if choice == "1":
            budgets = load_budgets()
            if not budgets:
                print("\n(no budgets set)\n")
            else:
                print()
                for cat, limit in budgets.items():
                    print(f"- {cat}: {currency_symbol} {limit:.2f}")
                print()
        elif choice == "2":
            current_cats = get_current_categories(transactions, "expense")
            print("\nSelect category to set budget:")
            for key, cat in current_cats.items():
                print(f"[{key}] {cat}")
            print("[0] Go Back")
            cat_choice = input("\nChoose category option: ").strip()
            if cat_choice.lower() == "back" or cat_choice == "0":
                print("\nReturning to the budget menu.\n")
                continue
            if cat_choice in current_cats:
                cat_name = current_cats[cat_choice]
                limit_input = input(f"\nEnter monthly budget limit for {cat_name} (type 'back' to return): ").strip()
                if limit_input.lower() == "back":
                    print("\nReturning to the budget menu.\n")
                    continue
                try:
                    limit_val = parse_amount(limit_input).quantize(Decimal("0.01"))
                    if limit_val <= 0:
                        raise ValueError
                    budgets = load_budgets()
                    budgets[cat_name] = limit_val
                    save_budgets(budgets)
                    print(f"\nBudget for '{cat_name}' set to {currency_symbol} {limit_val:.2f} successfully!\n")
                except (InvalidOperation, ValueError):
                    print_error("Error: Invalid amount. Budget must be greater than zero.")
            else:
                print_error("Error: Invalid category.")
        elif choice == "3":
            budgets = load_budgets()
            if not budgets:
                print("\n(no budgets set to remove)\n")
                continue
            print("\nSelect category to remove budget:")
            budget_keys = list(budgets.keys())
            for idx, cat in enumerate(budget_keys, 1):
                print(f"[{idx}] {cat} (Current limit: {currency_symbol} {budgets[cat]})")
            print("[0] Go Back")
            rem_choice = input("\nChoose option to remove: ").strip()
            if rem_choice.lower() == "back" or rem_choice == "0":
                print("\nReturning to the budget menu.\n")
                continue
            try:
                rem_idx = int(rem_choice) - 1
                if 0 <= rem_idx < len(budget_keys):
                    cat_to_remove = budget_keys[rem_idx]
                    del budgets[cat_to_remove]
                    save_budgets(budgets)
                    print(f"\nBudget for '{cat_to_remove}' successfully removed.\n")
                else:
                    print_error("Error: Invalid selection.")
            except ValueError:
                print_error("Error: Invalid input.")
        else:
            print_error("Error: Invalid choice.")


def export_report(transactions, currency, currency_symbol):
    today_str = date.today().isoformat()
    filename = f"finance_report_{today_str}.md"
    balance = calculate_balance(transactions)
    summary_month = generate_summary(transactions, period="this_month")
    summary_all = generate_summary(transactions, period="all")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Personal Finance Report\n")
            f.write(f"**Date:** {today_str}\n\n")
            f.write("## Total Balance\n")
            f.write(f"**{currency_symbol} {balance:.2f}** ({currency})\n\n")

            f.write("## Expenses Summary (This Month)\n")
            if summary_month:
                for cat, total in sorted(summary_month.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{cat}**: {currency_symbol} {total:.2f}\n")
            else:
                f.write("(No expenses recorded this month)\n")
            f.write("\n")

            f.write("## Expenses Summary (All Time)\n")
            if summary_all:
                for cat, total in sorted(summary_all.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{cat}**: {currency_symbol} {total:.2f}\n")
            else:
                f.write("(No expenses recorded)\n")
            f.write("\n")

            f.write("## Recent Transactions\n")
            for t in transactions[-10:][::-1]:
                sign = "+" if t["type"] == "income" else "-"
                f.write(f"- [{t['date']}] **{t['type'].upper()}** | {t['category']} : {sign}{currency_symbol} {t['amount']:.2f}\n")

        print(f"\nReport successfully exported to '{filename}'!\n")
    except Exception as e:
        print_error(f"Error exporting report: {e}")


def query_foreign_balance(transactions, current_currency):
    balance = calculate_balance(transactions)
    print("\n--- Check Balance in Another Currency ---")
    
    target = input("\nEnter target currency code (e.g. USD) (type '?' to see list, or 'back' to return): ").strip().upper()

    if target == "BACK":
        print("\nReturning to the main menu.\n")
        return

    if target == "?" or target == "HELP":
        show_currency_list()
        target = input("Enter target currency code: ").strip().upper()
        if target == "BACK":
            print("\nReturning to the main menu.\n")
            return

    if len(target) != 3 or not target.isalpha():
        print_error("Error: Invalid currency code format. Use 3 letters.")
        return

    print(f"\nFetching live exchange rate from {current_currency} to {target}...")
    rate, error_msg = fetch_live_rate(current_currency, target)

    if rate is None:
        print_error(f"Error: {error_msg}")
        return

    converted_balance = balance * Decimal(str(rate))
    target_sym = CURRENCY_SYMBOLS.get(target)
    if target_sym is None:
        target_sym = target
        print(f"\nNote: no known symbol for '{target}'; showing code instead.\n")

    color_prefix = RED if balance < 0 else ""
    color_suffix = RESET if balance < 0 else ""
    print(
        f"\nCurrent Total Balance: {color_prefix}{balance:.2f} {current_currency} = "
        f"{target_sym} {converted_balance:.2f}{color_suffix} "
        f"(Rate: 1 {current_currency} = {rate:.4f} {target})\n"
    )


def convert_currency(transactions, old_currency, old_symbol):
    global SKIPPED_ROWS_COUNT
    print(f"\n--- Change base currency (currently: {old_currency}) ---")

    try:
        new_currency, new_symbol = prompt_currency()
    except ValueError as e:
        print_error(f"Error: {e}")
        return old_currency, old_symbol

    if new_currency == old_currency:
        print("\nSame currency. Nothing to do.\n")
        return old_currency, old_symbol

    if not transactions and not load_budgets():
        save_currency(new_currency, new_symbol)
        print(
            f"\nCurrency changed to {new_currency} ({new_symbol}). (no transactions or budgets to convert)\n"
        )
        return new_currency, new_symbol

    print(
        f"\nAttempting to fetch live exchange rate from {old_currency} to {new_currency}..."
    )
    live_rate, error_msg = fetch_live_rate(old_currency, new_currency)

    if live_rate is not None:
        print(f"\nFound live rate: 1 {old_currency} = {live_rate:.4f} {new_currency}")
        use_live = (
            input("\nDo you want to use this live rate? (yes/no): ")
            .strip()
            .lower()
        )
        if use_live == "back":
            print("\nReturning to the main menu.\n")
            return old_currency, old_symbol
        if use_live == "yes":
            rate = Decimal(str(live_rate))
        else:
            rate_str = input(
                f"\nEnter custom conversion rate: 1 {old_currency} = ? {new_currency} (type 'back' to return): "
            ).strip()
            if rate_str.lower() == "back":
                print("\nReturning to the main menu.\n")
                return old_currency, old_symbol
            try:
                rate = parse_amount(rate_str)
                if rate <= 0:
                    raise ValueError
            except (InvalidOperation, ValueError):
                print_error("Error: Invalid rate. Conversion cancelled.")
                return old_currency, old_symbol
    else:
        print_error(f"Could not fetch live rate automatically: {error_msg}")
        rate_str = input(
            f"\nEnter conversion rate manually: 1 {old_currency} = ? {new_currency} (type 'back' to return): "
        ).strip()
        if rate_str.lower() == "back":
            print("\nReturning to the main menu.\n")
            return old_currency, old_symbol
        try:
            rate = parse_amount(rate_str)
            if rate <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            print_error("Error: Invalid rate. Conversion cancelled.")
            return old_currency, old_symbol

    print(
        f"\nThis will multiply ALL {len(transactions)} transaction amounts by {rate}"
    )
    print(f"and change currency from {old_currency} to {new_currency}.")
    confirm = input("\nType 'yes' to confirm: ").strip().lower()
    if confirm == "back":
        print("\nConversion cancelled.\n")
        return old_currency, old_symbol
    if confirm != "yes":
        print("\nConversion cancelled.\n")
        return old_currency, old_symbol

    if SKIPPED_ROWS_COUNT > 0:
        print_error(f"WARNING: There are {SKIPPED_ROWS_COUNT} corrupted/skipped lines in your data file.\nRewriting the file now will cause those skipped lines to be PERMANENTLY LOST.")
        final_proceed = input("\nDo you still want to proceed? (yes/no): ").strip().lower()
        if final_proceed == "back":
            print("\nConversion cancelled.\n")
            return old_currency, old_symbol
        if final_proceed != "yes":
            print("\nConversion cancelled.\n")
            return old_currency, old_symbol

    new_transactions = []
    for t in transactions:
        new_t = t.copy()
        new_t["amount"] = (t["amount"] * rate).quantize(Decimal("0.01"))
        new_transactions.append(new_t)

    budgets = load_budgets()
    converted_budgets = {
        category: (amount * rate).quantize(Decimal("0.01"))
        for category, amount in budgets.items()
    }

    backup_path = DATA_FILE + ".bak"
    if os.path.exists(DATA_FILE):
        shutil.copy2(DATA_FILE, backup_path)

    try:
        with open(DATA_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["amount", "category", "type", "date"])
            writer.writeheader()
            for t in new_transactions:
                writer.writerow(t)

        if converted_budgets:
            save_budgets(converted_budgets)

        save_currency(new_currency, new_symbol)
    except OSError as e:
        print_error(f"Conversion failed: {e}. Restoring backup...")
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DATA_FILE)
        return old_currency, old_symbol

    transactions.clear()
    transactions.extend(new_transactions)

    SKIPPED_ROWS_COUNT = 0
    print(f"\nAll transactions and budgets converted to {new_currency} ({new_symbol}).\n")
    return new_currency, new_symbol


def delete_data():
    confirm1 = (
        input(f"\n{RED}Do you want to delete all data? (yes/no): {RESET}").strip().lower()
    )
    if confirm1 == "back":
        print("\nDeletion cancelled.\n")
        return False
    if confirm1 != "yes":
        print("\nDeletion cancelled.\n")
        return False
    confirm2 = input(f"\n{RED}Are you sure? (yes/no): {RESET}").strip().lower()
    if confirm2 == "back":
        print("\nDeletion cancelled.\n")
        return False
    if confirm2 != "yes":
        print("\nDeletion cancelled.\n")
        return False
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(BUDGET_FILE):
        os.remove(BUDGET_FILE)
    if os.path.exists(USER_FILE):
        os.remove(USER_FILE)
    return True


def show_help():
    print("\n" + "=" * 40)
    print("        USER GUIDE / INSTRUCTIONS")
    print("=" * 40)
    print("1. Add Transaction: Select type, category, and amount.")
    print("2. View Balance: Net balance in base currency.")
    print("3. View Category Summary: Filtered expenses by period (sorted by value).")
    print("4. List Recent Transactions: View your 10 latest transactions history.")
    print("5. Balance in Foreign Currency: Check balance via live rates.")
    print("6. Manage Category Budgets: Set and check monthly spending limits.")
    print("7. Export Monthly Report: Generate a summary file.")
    print("8. Help: Obviously... Shows this menu.")
    print("9. Change Base Currency: Convert transactions to another currency.")
    print("10. Exit: Closes the program.")
    print("Type 'Delete' at the main menu to erase all data.")
    print("Type '0' or 'back' at any prompt to go back.")
    print("=" * 40 + "\n")


def show_batcave():
    yellow = "\033[1;33m"
    white = "\033[1;37m"
    grey = "\033[90m"
    print(f"\n{grey}==============================================={RESET}")
    print(f"{yellow}        I AM VENGEANCE. I AM THE NIGHT.        {RESET}")
    print(f"{white}         I AM ALUC0DE THE DEVELOPER.          {RESET}")
    print(f"{grey}==============================================={RESET}\n")


if __name__ == "__main__":
    main()