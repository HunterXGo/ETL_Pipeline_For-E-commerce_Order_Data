# 🛒 E-Commerce ETL Pipeline

<p align="center">
  <b>Turning messy order data into meaningful business intelligence.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas&logoColor=white">
  <img src="https://img.shields.io/badge/MySQL-Data%20Warehouse-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
  <img src="https://img.shields.io/badge/ETL-Pipeline-00C853?style=for-the-badge">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Completed-success?style=flat-square">
  <img src="https://img.shields.io/badge/Domain-Data%20Warehousing-blue?style=flat-square">
  <img src="https://img.shields.io/badge/Project-B.Tech%20PBL-orange?style=flat-square">
</p>

---

## ⚡ The Idea

E-commerce data is rarely born clean.

Orders come with missing values, duplicates, inconsistent formats, invalid records, and raw transactional information that isn't immediately useful for analytics.

This project builds an **ETL pipeline** that transforms that raw data into a structured **data warehouse** ready for analysis.

> **Raw Data → Clean Data → Data Warehouse → Business Insights**

---

## 🧠 What Does This Pipeline Do?

```text
                         🛒 E-COMMERCE DATA
                                │
                                ▼
                    ┌─────────────────────┐
                    │      📥 EXTRACT     │
                    │                     │
                    │  CSV / Raw Dataset  │
                    │  Python + Pandas    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     ⚙️ TRANSFORM    │
                    │                     │
                    │  • Clean Data       │
                    │  • Remove Duplicates│
                    │  • Handle Nulls     │
                    │  • Validate Data    │
                    │  • Convert Types    │
                    │  • Calculate Sales  │
                    │  • Calculate Profit │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      📦 LOAD        │
                    │                     │
                    │       MySQL         │
                    │   Data Warehouse    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      📊 ANALYZE     │
                    │                     │
                    │  Sales • Products   │
                    │  Customers • Profit │
                    │  Trends • Regions   │
                    └─────────────────────┘
