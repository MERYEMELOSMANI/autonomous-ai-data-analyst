import random
import csv
from pathlib import Path
from datetime import datetime, timedelta

def generate_datasets():
    base_dir = Path(__file__).resolve().parent
    base_dir.mkdir(parents=True, exist_ok=True)
    random.seed(42)

    # 1. Sales Performance Dataset
    sales_file = base_dir / "sales_performance.csv"
    categories = ["Electronics", "Home & Kitchen", "Office Supplies", "Apparel", "Beauty & Care"]
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    
    start_date = datetime(2025, 1, 1)
    with open(sales_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "date", "region", "category", "sales_amount", "quantity", "discount_pct", "customer_rating"])
        for i in range(1, 1001):
            dt = start_date + timedelta(days=random.randint(0, 360))
            reg = random.choice(regions)
            cat = random.choice(categories)
            base_price = {"Electronics": 450, "Home & Kitchen": 120, "Office Supplies": 45, "Apparel": 80, "Beauty & Care": 35}[cat]
            qty = random.randint(1, 8)
            disc = random.choice([0.0, 0.05, 0.1, 0.15, 0.25])
            amount = round((base_price * qty * (1 - disc)) + random.uniform(-10, 10), 2)
            rating = round(random.uniform(3.0, 5.0), 1)
            writer.writerow([f"ORD-{i:04d}", dt.strftime("%Y-%m-%d"), reg, cat, amount, qty, disc, rating])
    print(f"Generated {sales_file}")

    # 2. Customer Churn Dataset
    churn_file = base_dir / "customer_churn.csv"
    contracts = ["Month-to-month", "One year", "Two year"]
    with open(churn_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "tenure_months", "contract_type", "monthly_charges", "total_charges", "support_tickets", "churn"])
        for i in range(1, 801):
            tenure = random.randint(1, 72)
            contract = random.choices(contracts, weights=[0.55, 0.25, 0.20])[0]
            monthly = round(random.uniform(25.0, 115.0), 2)
            total = round((tenure * monthly) + random.uniform(-50, 50), 2)
            tickets = random.randint(0, 6)
            # Churn probability higher with high tickets and month-to-month
            churn_prob = 0.15 + (0.35 if contract == "Month-to-month" else 0.05) + (tickets * 0.08)
            churn = 1 if random.random() < min(0.85, churn_prob) else 0
            writer.writerow([f"CUST-{i:04d}", tenure, contract, monthly, total, tickets, churn])
    print(f"Generated {churn_file}")

    # 3. Financial Transactions Dataset
    fin_file = base_dir / "financial_transactions.csv"
    types = ["Payment", "Transfer", "Withdrawal", "Deposit"]
    statuses = ["Completed", "Pending", "Failed"]
    with open(fin_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "account_id", "transaction_type", "amount", "fee", "status", "is_fraud"])
        for i in range(1, 1201):
            t_type = random.choice(types)
            base_amt = random.exponential(scale=150.0) if hasattr(random, "exponential") else random.expovariate(1/150.0)
            amt = round(max(10.0, min(10000.0, base_amt)), 2)
            fee = round(amt * 0.015, 2)
            status = random.choices(statuses, weights=[0.92, 0.05, 0.03])[0]
            is_fraud = 1 if (amt > 3000 and random.random() < 0.4) or (status == "Failed" and random.random() < 0.3) else 0
            writer.writerow([f"TX-{i:05d}", f"ACC-{random.randint(100, 300)}", t_type, amt, fee, status, is_fraud])
    print(f"Generated {fin_file}")

if __name__ == "__main__":
    generate_datasets()
