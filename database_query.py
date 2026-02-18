# import os
# import pandas as pd
# import streamlit as st
# from databricks import sql
# from databricks.sdk.core import Config

# def get_db_connection():
#     cfg = Config() 
#     warehouse_id = os.getenv('DATABRICKS_WAREHOUSE_ID')
#     if not warehouse_id:
#         raise Exception("Environment variable 'DATABRICKS_WAREHOUSE_ID' is missing.")
    
#     return sql.connect(
#         server_hostname=cfg.host,
#         http_path=f"/sql/1.0/warehouses/{warehouse_id}",
#         credentials_provider=lambda: cfg.authenticate
#     )

# # --- READ FUNCTION ---
# def getData(tb_nm: str) -> pd.DataFrame:
#     """Reads data from a table name."""
#     query = f"SELECT * FROM {tb_nm}"
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             cursor.execute(query)
#             return cursor.fetchall_arrow().to_pandas()

# def writeData(df: pd.DataFrame, config: dict):
#     """
#     Performs a dynamic SQL MERGE (Update Only) to Databricks.
#     Uses named parameters (:col) to comply with Databricks SQL syntax.
#     """
#     try:
#         working_df = df.reset_index(drop=True).copy()
        
#         table_name = config["table"]
#         keys = config["join_keys"]
#         updates = config["update_columns"]
#         all_cols = list(set(keys + updates))

#         # --- DYNAMIC SQL CASTING (Using :name syntax) ---
#         select_parts = []
#         for c in all_cols:
#             if c == "CreatedTimestamp":
#                 # Cast the incoming string to a SQL Timestamp using named parameter
#                 select_parts.append(f"TO_TIMESTAMP(:{c}, 'yyyy-MM-dd HH:mm:ss') AS {c}")
#             else:
#                 select_parts.append(f":{c} AS {c}")
        
#         select_clause = ", ".join(select_parts)
#         all_cols_str = ", ".join([f"{c}" for c in all_cols])

#         # Build Join Condition
#         on_clause = " AND ".join([f"target.{k} = source.{k}" for k in keys])
        
#         # Build Update Set
#         set_clause = ", ".join([f"target.{c} = source.{c}" for c in updates])

#         # Final MERGE Statement
#         # We use a proper SELECT statement in the USING clause
#         merge_sql = f"""
#             MERGE INTO {table_name} AS target
#             USING (SELECT {select_clause}) AS source
#             ON {on_clause}
#             WHEN MATCHED THEN
#               UPDATE SET {set_clause}
#             WHEN NOT MATCHED THEN
#               INSERT ({all_cols_str}) VALUES ({all_cols_str})
#         """

#         with get_db_connection() as connection:
#             with connection.cursor() as cursor:
#                 # Convert rows to dictionaries
#                 payload = working_df[all_cols].to_dict(orient="records")
                
#                 for record in payload:
#                     # Databricks SQL connector expects parameters as the second argument
#                     cursor.execute(merge_sql, record)
                
#                 connection.commit()
                
#     except Exception as e:
#         raise Exception(f"Database sync failed: {str(e)}")


import os
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config

# --- CONNECTION HELPER ---
def get_db_connection():
    """
    Establishes a connection to the Databricks SQL Warehouse.
    Requires DATABRICKS_WAREHOUSE_ID env var and configured Databricks SDK authentication.
    """
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
# def getData(tb_nm: str, ActiveFlag: str = None) -> pd.DataFrame:
#     """
#     Reads data from a specific table into a Pandas DataFrame.
#     """
#     if ActiveFlag:
#         query = f"SELECT * FROM {tb_nm} WHERE ActiveFlag = '{ActiveFlag}'"
#     else:
#         query = f"SELECT * FROM {tb_nm}"
#     try:
#         with get_db_connection() as conn:
#             with conn.cursor() as cursor:
#                 cursor.execute(query)
#                 # fetchall_arrow() is generally faster for larger datasets
#                 return cursor.fetchall_arrow().to_pandas()
#     except Exception as e:
#         raise Exception(f"Failed to read data from {tb_nm}: {str(e)}")

# database_query.py

def getData(tb_nm: str, ActiveFlag: str | None = None) -> pd.DataFrame:
    """
    Reads data from a table name.
    Optional: Filters by ActiveFlag if provided ('Y' or 'N').
    """
    query = f"SELECT * FROM {tb_nm}"
    
    # Add WHERE clause if ActiveFlag is passed
    if ActiveFlag:
        # We use a parameterized query for safety, though f-string is often fine for internal flags
        query += f" WHERE ActiveFlag = '{ActiveFlag}'"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall_arrow().to_pandas()
    except Exception as e:
        raise Exception(f"Failed to read data from {tb_nm}: {str(e)}")

# --- WRITE (UPSERT) FUNCTION ---
def writeData(df: pd.DataFrame, config: dict):
    """
    Performs a dynamic SQL MERGE (Upsert) to Databricks.
    - Matches rows based on 'join_keys'
    - Updates rows if matched
    - Inserts rows if not matched
    """
    try:
        if df.empty:
            return

        working_df = df.reset_index(drop=True).copy()
        
        table_name = config["table"]
        keys = config["join_keys"]
        updates = config["update_columns"]
        
        # Combine keys and updates to ensure we have all necessary columns
        all_cols = list(set(keys + updates))

        # --- DYNAMIC SQL CONSTRUCTION ---
        select_parts = []
        for c in all_cols:
            # Handle specific timestamp formatting if needed, otherwise standard param
            if "Timestamp" in c: 
                # Example: Cast string to timestamp if your DF sends strings
                # If your DF sends datetime objects, simple :name usually works, 
                # but explicit casting is safer for strings.
                select_parts.append(f"cast(:{c} as timestamp) AS {c}")
            else:
                select_parts.append(f":{c} AS {c}")
        
        select_clause = ", ".join(select_parts)
        
        # Columns for the INSERT clause
        # We need to ensure we insert ALL columns (keys + updates)
        insert_cols_str = ", ".join(all_cols)
        insert_vals_str = ", ".join([f"source.{c}" for c in all_cols])

        # Join Condition (Target = Source)
        on_clause = " AND ".join([f"target.{k} = source.{k}" for k in keys])
        
        # Update Set (Target = Source) - Only update non-key columns
        set_clause = ", ".join([f"target.{c} = source.{c}" for c in updates])

        # MERGE Statement
        merge_sql = f"""
            MERGE INTO {table_name} AS target
            USING (SELECT {select_clause}) AS source
            ON {on_clause}
            WHEN MATCHED THEN
              UPDATE SET {set_clause}
            WHEN NOT MATCHED THEN
              INSERT ({insert_cols_str}) VALUES ({insert_vals_str})
        """

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                # Convert DataFrame to list of dicts for iteration
                # Ensure date objects are converted to strings if necessary, 
                # or rely on the connector's default conversion.
                payload = working_df[all_cols].to_dict(orient="records")
                
                for record in payload:
                    cursor.execute(merge_sql, record)
                
                # Explicit commit (though often auto-handled, good practice to be explicit)
                # Note: 'commit' method availability depends on driver version/config
                # If using standard databricks-sql-connector, it's safer to not call commit() 
                # if autocommit is on, but usually it doesn't hurt.
                # connection.commit() 
                
    except Exception as e:
        raise Exception(f"Database sync failed: {str(e)}")

# --- DELETE FUNCTION (NEW) ---
def deleteData(df_or_records, config: dict):
    """
    Deletes rows from the database based on Primary Keys defined in config.
    Accepts either a DataFrame or a list of dictionaries.
    """
    try:
        # Normalize input to a list of dictionaries
        if isinstance(df_or_records, pd.DataFrame):
            if df_or_records.empty:
                return
            records = df_or_records.to_dict(orient="records")
        else:
            records = df_or_records

        if not records:
            return

        table_name = config["table"]
        keys = config["join_keys"] # Primary Keys used to identify rows to delete

        # Construct WHERE clause dynamically: WHERE PK1 = :PK1 AND PK2 = :PK2
        where_parts = [f"{k} = :{k}" for k in keys]
        where_clause = " AND ".join(where_parts)
        
        delete_sql = f"DELETE FROM {table_name} WHERE {where_clause}"

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                for record in records:
                    # We only need the Primary Key values for the DELETE params
                    # Extract only the keys from the record to be clean
                    params = {k: record[k] for k in keys}
                    
                    cursor.execute(delete_sql, params)
                
    except Exception as e:
        raise Exception(f"Database delete failed: {str(e)}")