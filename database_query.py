import os
import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

def get_db_connection():
    cfg = Config() 
    warehouse_id = os.getenv('DATABRICKS_WAREHOUSE_ID')
    if not warehouse_id:
        raise Exception("Environment variable 'DATABRICKS_WAREHOUSE_ID' is missing.")
    
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate
    )

# --- READ FUNCTION ---
def getData(tb_nm: str) -> pd.DataFrame:
    """Reads data from a table name."""
    query = f"SELECT * FROM {tb_nm}"
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()

def writeData(df: pd.DataFrame, config: dict):
    """
    Performs a dynamic SQL MERGE (Update Only) to Databricks.
    Uses named parameters (:col) to comply with Databricks SQL syntax.
    """
    try:
        working_df = df.reset_index(drop=True).copy()
        
        table_name = config["table"]
        keys = config["join_keys"]
        updates = config["update_columns"]
        all_cols = list(set(keys + updates))

        # --- DYNAMIC SQL CASTING (Using :name syntax) ---
        select_parts = []
        for c in all_cols:
            if c == "CreatedTimestamp":
                # Cast the incoming string to a SQL Timestamp using named parameter
                select_parts.append(f"TO_TIMESTAMP(:{c}, 'yyyy-MM-dd HH:mm:ss') AS {c}")
            else:
                select_parts.append(f":{c} AS {c}")
        
        select_clause = ", ".join(select_parts)

        # Build Join Condition
        on_clause = " AND ".join([f"target.{k} = source.{k}" for k in keys])
        
        # Build Update Set
        set_clause = ", ".join([f"target.{c} = source.{c}" for c in updates])

        # Final MERGE Statement
        # We use a proper SELECT statement in the USING clause
        merge_sql = f"""
            MERGE INTO {table_name} AS target
            USING (SELECT {select_clause}) AS source
            ON {on_clause}
            WHEN MATCHED THEN
              UPDATE SET {set_clause}
        """

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Convert rows to dictionaries
                payload = working_df[all_cols].to_dict(orient="records")
                
                for record in payload:
                    # Databricks SQL connector expects parameters as the second argument
                    cursor.execute(merge_sql, record)
                
                connection.commit()
                
    except Exception as e:
        raise Exception(f"Database sync failed: {str(e)}")