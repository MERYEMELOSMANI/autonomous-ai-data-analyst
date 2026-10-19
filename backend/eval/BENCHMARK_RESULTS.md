# Autonomous AI Data Analyst — Ground-Truth Benchmark Results

## Executive Summary

- **Benchmark Size**: 20 Ground-Truth Analytical Questions
- **Datasets**: Sales Performance (1,000 rows), Customer Churn (800 rows), Financial Transactions (1,200 rows)
- **Multi-Agent Accuracy**: **100.0%**
- **Verification Success Rate**: **100.0%**
- **Hallucination Rate**: **0.0%** (All numerical claims strictly grounded in DuckDB calculations)
- **Average Multi-Agent Workflow Latency**: **69.4 ms**
- **Average Baseline Latency**: **71.07 ms**

## Comparison: Multi-Agent System vs. Single-Agent Baseline

| Capability | Multi-Agent Orchestration | Single-Agent / Raw Query Baseline |
|---|---|---|
| **Task Completion** | **100.0%** | 100.0% |
| **Independent Verification** | **Yes (Deterministic Re-computation)** | No verification |
| **Data Quality Auditing** | **Yes (Missingness, Duplicates, Outliers)** | None |
| **Interactive Plotly Visualization** | **Yes (Auto-selected & Themed)** | None |
| **Executive Report Synthesis** | **Yes (Structured with Limitations)** | Raw table or query only |
| **Explainability (Inspect Evidence)** | **Full SQL Trace & Verification Proof** | Query string only |

## Detailed Test Case Results

| ID | Dataset | Question | Ground Truth Value | Verified | Multi Latency |
|---|---|---|---|---|---|
| BM-01 | `sales_performance.csv` | What is the total sales amount across all orders? | `536007.73` | ✅ Passed | 131.58 ms |
| BM-02 | `sales_performance.csv` | What is the average sales amount per order? | `536.01` | ✅ Passed | 135.53 ms |
| BM-03 | `sales_performance.csv` | How many total orders are in the dataset? | `1000` | ✅ Passed | 126.04 ms |
| BM-04 | `sales_performance.csv` | Which product category has the highest total revenue? | `Electronics` | ✅ Passed | 130.65 ms |
| BM-05 | `sales_performance.csv` | What is the total revenue for the Electronics category? | `317831.44` | ✅ Passed | 133.27 ms |
| BM-06 | `sales_performance.csv` | What is the average customer rating across all orders? | `3.99` | ✅ Passed | 127.14 ms |
| BM-07 | `sales_performance.csv` | What is the maximum single order sales amount? | `3606.08` | ✅ Passed | 127.45 ms |
| BM-08 | `sales_performance.csv` | What is the total quantity of items sold? | `4412` | ✅ Passed | 138.77 ms |
| BM-09 | `customer_churn.csv` | What is the total count of customers in the dataset? | `800` | ✅ Passed | 23.2 ms |
| BM-10 | `customer_churn.csv` | How many customers churned? | `475` | ✅ Passed | 25.96 ms |
| BM-11 | `customer_churn.csv` | What is the overall churn rate percentage? | `59.38` | ✅ Passed | 22.25 ms |
| BM-12 | `customer_churn.csv` | What is the average tenure in months for churned customers? | `38.34` | ✅ Passed | 23.84 ms |
| BM-13 | `customer_churn.csv` | What is the average monthly charge for all customers? | `70.37` | ✅ Passed | 21.8 ms |
| BM-14 | `customer_churn.csv` | What contract type has the highest churn rate? | `Month-to-month` | ✅ Passed | 29.37 ms |
| BM-15 | `customer_churn.csv` | What is the maximum number of support tickets recorded for any customer? | `6` | ✅ Passed | 27.82 ms |
| BM-16 | `financial_transactions.csv` | What is the total transaction volume in dollars? | `187643.84` | ✅ Passed | 36.37 ms |
| BM-17 | `financial_transactions.csv` | How many fraudulent transactions were flagged? | `6` | ✅ Passed | 33.18 ms |
| BM-18 | `financial_transactions.csv` | What is the average transaction fee collected? | `2.35` | ✅ Passed | 33.32 ms |
| BM-19 | `financial_transactions.csv` | What is the transaction count for completed transactions? | `1112` | ✅ Passed | 30.98 ms |
| BM-20 | `financial_transactions.csv` | Which transaction type has the highest total volume? | `Deposit` | ✅ Passed | 29.43 ms |
