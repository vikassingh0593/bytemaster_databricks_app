# NFG Wastage Reduction Hub

The **NFG Wastage Reduction Hub** is a data analytics web application built to monitor, analyze, and minimize the wastage of raw materials (non-finished goods) during the production of finished Consumer Packaged Goods (CPG). 

This application is built with Python and Streamlit, and is natively hosted and governed within the Databricks ecosystem using Databricks Apps and Unity Catalog.

## 🏗 Architecture



* **Frontend:** Streamlit 
* **Hosting:** Databricks Apps (Serverless)
* **Compute:** Databricks SQL Warehouse
* **Data Governance & Storage:** Unity Catalog (UC) Managed Tables (Delta Lake format)
* **Authentication:** Google Workspace Single Sign-On (SSO)

## 📋 Prerequisites

Before deploying or running this application, ensure the following are configured in your Databricks Workspace:
1. **Google SSO Integration:** Users must be able to log into Databricks using their corporate Google email accounts.
2. **Databricks SQL Warehouse:** A running (or serverless) SQL warehouse to handle queries triggered by the Streamlit app.
3. **Unity Catalog:** Enabled workspace with appropriate catalogs and schemas created for the NFG data.
4. **Databricks CLI:** Installed and configured on your local machine for deployment.

## 🚀 Deployment Checklist

Follow these steps to deploy the application to the Databricks server:

### Phase 1: Data & Governance Setup
- [ ] **Create Managed Tables:** Ensure the raw material and production tables exist as Managed Tables in Unity Catalog. 
- [ ] **Data Ingestion:** Verify that the data pipelines populating these tables are running and up-to-date.
- [ ] **Configure UC Permissions:** Run `GRANT SELECT` statements in Databricks SQL to give the required Google user groups access to the specific database/schema containing the NFG tables.

### Phase 2: Application Configuration
- [ ] **Update `app.yaml`:** Ensure your Databricks App configuration file (`app.yaml`) correctly specifies the source directory, the command to run Streamlit (`streamlit run app.py`), and the assigned SQL Warehouse ID.
- [ ] **Environment Variables:** Define any necessary environment variables (e.g., specific Catalog/Schema names) in the Databricks App settings so the code can dynamically reference them.

### Phase 3: Deployment
- [ ] **Authenticate CLI:** Run `databricks auth login` on your local terminal.
- [ ] **Deploy via CLI:** Navigate to the project root and execute the deployment command: 
  `databricks apps deploy nfg-wastage-hub --source .`
- [ ] **Verify Build:** Check the Databricks Apps UI in your workspace to monitor the build and deployment logs.

### Phase 4: Access Management
- [ ] **Assign App Permissions:** In the Databricks UI, navigate to the deployed "nfg-wastage-hub" app. 
- [ ] **Grant User Access:** Add the specific Google email addresses or groups (e.g., `cpg-analysts@yourcompany.com`) and assign them `CAN USE` permissions. 
- [ ] **Test Access:** Have a user log in via Google SSO and access the provided Databricks App URL to ensure data loads correctly and permissions are enforced.

## 💻 Local Development

To run this application locally for development:

1. Clone the repository.
2. Install the requirements: `pip install -r requirements.txt`
3. Authenticate with Databricks locally using the Databricks CLI (`databricks auth login`) or set up a Personal Access Token (PAT) as an environment variable so the local app can query the remote SQL Warehouse.
4. Run the app: `streamlit run app.py`

## 🤝 Contributing
Branch off `main` for any feature development. Ensure you test your queries against a development schema in Unity Catalog before submitting a Pull Request.


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