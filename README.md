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

🔥 Core Pipeline
Stage	What Happens
📥 Extract	Raw order data is collected from CSV files
🧹 Clean	Missing and duplicate records are handled
🔄 Transform	Data types, dates and categories are standardized
🧮 Enrich	Sales, discounts and profit are calculated
🗄️ Load	Clean data is stored in MySQL
📊 Analyze	SQL queries generate business insights


🏗️ Data Warehouse
The warehouse follows a Star Schema design.
                    ┌─────────────────┐
                    │   dim_customer  │
                    └────────┬────────┘
                             │
                             │
┌─────────────────┐    ┌─────▼─────────┐    ┌─────────────────┐
│   dim_product   │────│  fact_orders  │────│   dim_location  │
└─────────────────┘    └─────▲─────────┘    └─────────────────┘
                             │
                             │
                    ┌────────┴────────┐
                    │     dim_date    │
                    └─────────────────┘

⭐ Fact Table
fact_orders
Contains transactional metrics:
- Order ID
- Customer ID
- Product ID
- Date ID
- Location ID
- Quantity
- Unit Price
- Discount
- Sales
- Profit
📐 Dimension Tables
dim_customer
Customer-related information.
dim_product
Product, category and sub-category information.
dim_date
Day, month, quarter and year information.
dim_location
City, region and country information.
🧹 Data Transformation
The pipeline performs several data-quality operations.
Duplicate Removal
df = df.drop_duplicates()


Missing Value Handling
df["quantity"] = df["quantity"].fillna(0)df["discount"] = df["discount"].fillna(0)


Date Standardization
df["order_date"] = pd.to_datetime(df["order_date"])


Data Validation
df = df[df["quantity"] > 0]df = df[df["unit_price"] >= 0]


Derived Metrics
Sales
  ↓
Quantity × Unit Price

Discount Amount
  ↓
Sales × Discount

Profit
  ↓
Sales − Cost

🛠️ Tech Stack
🐍 Python
 ├── Pandas
 └── NumPy

🗄️ Database
 └── MySQL

🔌 Connectivity
 └── SQLAlchemy / MySQL Connector

💻 Development
 ├── Jupyter Notebook
 └── VS Code

📂 Project Structure
ETL-Ecommerce-Orders/
│
├── 📁 data/
│   ├── 📁 raw/
│   │   └── ecommerce_orders.csv
│   │
│   └── 📁 processed/
│       └── cleaned_orders.csv
│
├── 📁 notebooks/
│   └── etl_pipeline.ipynb
│
├── 📁 src/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── main.py
│
├── 📁 sql/
│   ├── create_database.sql
│   ├── create_tables.sql
│   └── analysis_queries.sql
│
├── 📁 outputs/
│   └── reports/
│
├── requirements.txt
└── README.md

🚀 Getting Started
1️⃣ Clone the Repository
git clone https://github.com/<username>/ETL-Ecommerce-Orders.git

cd ETL-Ecommerce-Orders

2️⃣ Create Virtual Environment
python -m venv .venv

Activate it:
macOS / Linux
source .venv/bin/activate

Windows
.venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Configure MySQL
Create the database:
CREATE DATABASE ecommerce_dw;

Configure:
Host     : localhost
Port     : 3306
Database : ecommerce_dw
Username : <your_username>
Password : <your_password>

🔐 Never commit passwords or credentials to GitHub.

5️⃣ Run the Pipeline
python src/main.py

And watch the magic happen:
📥 Extracting...
        ↓
🧹 Cleaning...
        ↓
🔄 Transforming...
        ↓
📦 Loading...
        ↓
📊 Ready for Analysis!

📊 What Can We Discover?
Once the data reaches the warehouse, we can answer questions like:
💰 How much revenue was generated?

🏆 Which products sell the most?

👑 Who are the highest-value customers?

🌎 Which regions generate the most revenue?

📈 How do sales change month by month?

💸 Which products generate the highest profit?

🛍️ What is the average order value?

Example:
SELECT
    SUM(sales) AS total_sales,
    SUM(profit) AS total_profit
FROM fact_orders;

🎯 Project Objectives
- Build a complete ETL pipeline.
- Clean and standardize raw e-commerce data.
- Handle missing and duplicate records.
- Transform transactional data into warehouse-ready data.
- Implement a star-schema data warehouse.
- Store processed data in MySQL.
- Enable efficient analytical queries.
- Demonstrate practical data warehousing concepts.
🔮 Future Roadmap
                    CURRENT
                       │
                       ▼
              ┌─────────────────┐
              │  Batch ETL      │
              │ Python + MySQL  │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       ☁️ Cloud     ⏱️ Airflow    📊 BI
      Warehouse     Scheduling   Dashboard
          │            │            │
          └────────────┼────────────┘
                       ▼
                🚀 Advanced ETL
                       │
                       ▼
              Real-time Analytics

Planned Enhancements
- [ ] Incremental data loading
- [ ] Apache Airflow orchestration
- [ ] Real-time data ingestion
- [ ] Cloud data warehouse
- [ ] Power BI dashboard
- [ ] Automated data-quality checks
- [ ] Pipeline monitoring
- [ ] Multiple data sources
🎓 Academic Information
Project: ETL Pipeline for E-commerce Order Data
Domain: Data Warehousing & Data Mining
Institution: Geethanjali College of Engineering and Technology
Department: Computer Science & Engineering – Data Science
Project Type: B.Tech Project Based Learning
👨‍💻 Team
Role	Responsibility
🧑‍💻 Data Engineer	ETL Pipeline
🗄️ Database Engineer	Data Warehouse
📊 Data Analyst	SQL & Analytics
📝 Documentation	Report & Presentation


💡 One-Line Summary
A complete ETL pipeline that turns raw e-commerce transactions into clean, structured, and analytics-ready warehouse data.
