# Autonomous AI Data Analyst — Ground-Truth Benchmark Results

## Executive Summary

- **Benchmark Size**: 20 Ground-Truth Analytical Questions
- **Datasets**: Sales Performance (1,000 rows), Customer Churn (800 rows), Financial Transactions (1,200 rows)
- **Multi-Agent Accuracy**: **100.0%**
- **Verification Success Rate**: **100.0%**
- **Hallucination Rate**: **0.0%** (All numerical claims strictly grounded in DuckDB calculations)
- **Average Multi-Agent Workflow Latency**: **71.75 ms**
- **Average Baseline Latency**: **67.12 ms**

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
| BM-01 | `sales_performance.csv` | What is the total sales amount across all orders? | `536007.73` | ✅ Passed | 123.37 ms |
| BM-02 | `sales_performance.csv` | What is the average sales amount per order? | `536.01` | ✅ Passed | 132.15 ms |
| BM-03 | `sales_performance.csv` | How many total orders are in the dataset? | `1000` | ✅ Passed | 122.02 ms |
| BM-04 | `sales_performance.csv` | Which product category has the highest total revenue? | `Electronics` | ✅ Passed | 120.4 ms |
| BM-05 | `sales_performance.csv` | What is the total revenue for the Electronics category? | `317831.44` | ✅ Passed | 127.66 ms |
| BM-06 | `sales_performance.csv` | What is the average customer rating across all orders? | `3.99` | ✅ Passed | 136.95 ms |
| BM-07 | `sales_performance.csv` | What is the maximum single order sales amount? | `3606.08` | ✅ Passed | 120.1 ms |
| BM-08 | `sales_performance.csv` | What is the total quantity of items sold? | `4412` | ✅ Passed | 187.84 ms |
| BM-09 | `customer_churn.csv` | What is the total count of customers in the dataset? | `800` | ✅ Passed | 46.43 ms |
| BM-10 | `customer_churn.csv` | How many customers churned? | `475` | ✅ Passed | 26.8 ms |
| BM-11 | `customer_churn.csv` | What is the overall churn rate percentage? | `59.38` | ✅ Passed | 24.52 ms |
| BM-12 | `customer_churn.csv` | What is the average tenure in months for churned customers? | `38.34` | ✅ Passed | 23.6 ms |
| BM-13 | `customer_churn.csv` | What is the average monthly charge for all customers? | `70.37` | ✅ Passed | 24.89 ms |
| BM-14 | `customer_churn.csv` | What contract type has the highest churn rate? | `Month-to-month` | ✅ Passed | 27.38 ms |
| BM-15 | `customer_churn.csv` | What is the maximum number of support tickets recorded for any customer? | `6` | ✅ Passed | 24.98 ms |
| BM-16 | `financial_transactions.csv` | What is the total transaction volume in dollars? | `187643.84` | ✅ Passed | 34.96 ms |
| BM-17 | `financial_transactions.csv` | How many fraudulent transactions were flagged? | `6` | ✅ Passed | 32.36 ms |
| BM-18 | `financial_transactions.csv` | What is the average transaction fee collected? | `2.35` | ✅ Passed | 32.34 ms |
| BM-19 | `financial_transactions.csv` | What is the transaction count for completed transactions? | `1112` | ✅ Passed | 31.4 ms |
| BM-20 | `financial_transactions.csv` | Which transaction type has the highest total volume? | `Deposit` | ✅ Passed | 34.88 ms |
