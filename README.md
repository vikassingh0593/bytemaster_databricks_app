# bytemaster_databricks_app

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