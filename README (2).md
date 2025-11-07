# 🥖 Bakery Performance Analytics Dashboard

A comprehensive **Streamlit-powered interactive dashboard** designed to analyze bakery business performance — including sales, profit, ad spend, customer behavior, and marketing effectiveness.  
This app helps visualize **key financial metrics, performance trends, and relationships** between different business dimensions.

---

## 🚀 Features

### 📊 1. Overview & KPIs
- Displays **key performance indicators** such as:
  - Total Revenue  
  - Total Profit  
  - Total Conversions  
  - Profit Margin (%)  
  - ROAS (Return on Ad Spend)  
  - AOV (Average Order Value)  
- Includes **7 business visualizations** for quick insights:
  - Revenue by Channel  
  - Conversions by Customer Type  
  - Profit by Service Type  
  - Average Conversions per Channel  
  - Ad Spend by Customer Type  
  - Average Revenue (Service × Customer Type)  
  - Cumulative Profit by Channel  

---

### 📈 2. Trends & Performance
- Time-series analysis of business metrics:
  - Daily Revenue & Profit trends  
  - Conversions and Ad Spend trends  
- Breakdown by:
  - Day of Week  
  - Month  
  - Time of Day  
  - Channel  
- Includes metrics like **Average CPC (Cost per Conversion)** and **Monthly Profit Distribution**.

---

### 💸 3. In-Depth Financial Analysis
- Advanced insights into profitability and marketing efficiency:
  - **Ad Spend vs Revenue** (bubble size = Profit)
  - **Average Revenue by Season**
  - **Revenue Distribution Histogram**
  - **Profit Distribution by Channel**
  - **Correlation Heatmap** between all numeric metrics
  - **Ad Spend & Conversions by Channel**
  - **ROAS (Return on Ad Spend)** by Service Type

---

### 📊 4. Relationships & Comparisons
- Compare multiple business dimensions:
  - Monthly Revenue by Channel
  - Profit by Season × Service Type
  - Average Revenue by Day of Week × Customer Type
  - Profit Distribution (Time of Day × Channel)
  - Ad Spend vs Conversions by Service Type
  - Ad Spend Distribution by Season × Service Type
  - Treemap of Revenue by Channel × Customer Type

---

## 📁 File Structure

```
project/
│
├── app.py               # Main Streamlit application
├── requirements.txt      # Required Python packages
└── README.md             # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/bakery-dashboard.git
cd bakery-dashboard
```

### 2. Install Dependencies
It is recommended to use a virtual environment:
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```

---

## 📤 Uploading Data

The dashboard accepts **CSV** or **Excel (.xlsx)** files.

### ✅ Required Columns
Your dataset should include at least:
- `Date` (in a valid date format)
- `Revenue`
- `Ad Spend`
- `Conversions`

### 🧩 Optional Columns (for deeper analysis)
- `Channel`  
- `Service Type`  
- `Customer Type`  
- `Season`  
- `Time of Day`  
- `Day` (automatically generated)  
- `Month` (automatically generated)

> 💡 The dashboard automatically calculates **Profit = Revenue - Ad Spend** and other derived metrics.

---

## 🧠 Key Metrics Explained

| Metric | Description |
|--------|--------------|
| **Profit Margin (%)** | `(Profit / Revenue) × 100` |
| **ROAS (Return on Ad Spend)** | `Revenue / Ad Spend` |
| **AOV (Average Order Value)** | `Revenue / Total Orders` |
| **CPC (Cost per Conversion)** | `Ad Spend / Conversions` |

---

## 🧩 Tech Stack
- **Python 3.9+**
- **Streamlit**
- **Pandas / NumPy**
- **Plotly Express**
- **Matplotlib / Seaborn**

---

## 📸 Preview

Example dashboard layout:
- Filter sidebar for dynamic selection
- Interactive charts with hover insights
- Clean and modern design with responsive layout

---

## 🧾 License
This project is open source and available under the **MIT License**.
