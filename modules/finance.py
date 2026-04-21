import json
import os
import datetime

FINANCE_FILE = "memories/finance.json"

def load_finance():
    if os.path.exists(FINANCE_FILE):
        with open(FINANCE_FILE, "r") as f:
            return json.load(f)
    return {"expenses": [], "total_spent": 0}

def save_finance(data):
    os.makedirs("memories", exist_ok=True)
    with open(FINANCE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_expense(amount, category="general"):
    data = load_finance()
    try:
        amount = float(amount)
        data["expenses"].append({
            "amount": amount,
            "category": category,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        data["total_spent"] += amount
        save_finance(data)
        return f"Added expense of {amount} for {category}. Your total spent this month is {data['total_spent']}."
    except:
        return "Please provide a valid number for the amount."

def get_finance_report():
    data = load_finance()
    if not data["expenses"]:
        return "No expenses recorded yet!"
    
    report = f"Finance Report:\nTotal Spent: {data['total_spent']}\nRecent Expenses:\n"
    for e in data["expenses"][-5:]:
        report += f"- {e['amount']} ({e['category']}) on {e['timestamp'].split()[0]}\n"
    return report
