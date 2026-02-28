# ♻️ SourceCare Hub: NFG Waste Reduction App

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://nfgwastered.streamlit.app/)

## 📖 Project Overview
The APP is a proof-of-concept data application built to test the capabilities of **Databricks Apps** and **Streamlit** as a unified alternative to traditional low-code BI stacks (such as Power Apps combined with Power BI). 

Designed for the Consumer Packaged Goods (CPG) manufacturing space, this application shifts the focus from simple waste tracking to active material stewardship. It provides a code-first, highly customizable environment directly on top of the data lakehouse.

## ✨ Key Features
* **Unified UI/UX:** Combines the data visualization capabilities of a BI dashboard with the interactive, write-back functionality of a standard web app.
* **Custom User Access Control (UAC):** Implements role-based access to test enterprise-level security and restricted views within a Streamlit environment.
* **Lakehouse Native Design:** Architected to run directly as a Databricks App, eliminating the need for complex data extraction pipelines.
* **Interactive Analytics:** Real-time filtering, dynamic KPIs, and drill-down capabilities for raw material usage and yield optimization.

## 🏗️ Architecture & Tech Stack

* **Frontend:** Streamlit
* **Backend / Data Processing:** Databricks, PySpark, Spark SQL
* **Language:** Python
* **Deployment:** Currently hosted on Streamlit Community Cloud (Demo), designed for Databricks Apps (Production).


## 💻 Local Installation & Setup
To run this project locally and connect it to your own Databricks environment:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/vikas-username/nfg-waste-reduction.git](https://github.com/vikas-username/nfg-waste-reduction.git)
   cd nfg-waste-reduction

## Setup (virtualenv)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install databricks-cli
```

## Export app from Databricks to local
```bash
databricks workspace export-dir /Workspace/Users/vikassingh0593@gmail.com/databricks_apps/bytemaster_2026_01_30-16_47/streamlit-data-app .
```

## Sync code (watch mode)
```bash
databricks sync --watch . /Workspace/Users/vikassingh0593@gmail.com/databricks_apps/bytemaster_2026_01_30-16_47/streamlit-data-app
```

## Run the app locally
```bash
export DATABRICKS_WAREHOUSE_ID=bd30e90188326d9e
export STREAMLIT_THEME_BASE=light
streamlit run app.py --theme.primaryColor=#007bff
```

## Deploy
First time:
```bash
databricks apps deploy bytemaster --source-code-path /Workspace/Users/vikassingh0593@gmail.com/databricks_apps/bytemaster_2026_01_30-16_47/streamlit-data-app
```
Subsequent deploys:
```bash
databricks apps deploy bytemaster
```