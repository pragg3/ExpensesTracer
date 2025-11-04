import pandas as pd
from datetime import datetime

def calculate_summary(expenses, total_money):
    today = datetime.now().strftime("%Y-%m-%d")
    spent = sum(e["amount"] for e in expenses if not e["date"] or e["date"] <= today)
    remaining = total_money - spent
    df = pd.DataFrame(expenses)
    return spent, remaining, df
