# COMMAND ----------
import yaml

with open("dataset_config.yml", "r") as file:
    CONFIG = yaml.safe_load(file)

# Databricks notebook source
# DBTITLE 1,Cell 1
# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS bytemaster;
# MAGIC USE CATALOG bytemaster;
# MAGIC DROP SCHEMA IF EXISTS appdata CASCADE;
# MAGIC CREATE SCHEMA appdata;
# MAGIC USE SCHEMA appdata;

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import random
from datetime import datetime, timedelta

# COMMAND ----------

import random
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# 1. Your Configuration Lists
PlantIdList = [f"P{str(i).zfill(2)}" for i in range(1, 11)]
MatIdList = [f"M{str(i).zfill(2)}" for i in range(1, 101)]
CompIdList = [f"C{str(i).zfill(2)}" for i in range(1, 101)]
FeedbackList = ["Unactioned", "Accepted", "Rejected", "Under Review"]
UserEmailList = ["vikassingh0593@gmail.com", "vikassingh0597@gmail.com",
                 "user@example.com", "ankitsingh7010@gmail.com"]
RunIdList = [(datetime.today() - timedelta(days=i)).strftime("%Y%m%d") for i in range(0, 30)]

# COMMAND ----------

# DBTITLE 1,Substitution

# 2. SQL Table Definition
spark.sql(f"""
CREATE TABLE IF NOT EXISTS Substitution (
    RunID STRING,
    ComponentId STRING,
    PlantId STRING,
    MaterialId STRING,
    QtyAtRisk DOUBLE,
    PotentialSaving DOUBLE,
    ActualSaving DOUBLE,
    Feedback STRING,
    UserEmail STRING,
    CreatedTimestamp TIMESTAMP
)
USING DELTA""")


def create_model_Data():
    # 3. Data Generation Logic
    Substitution_raw_data = []
    current_run_id = RunIdList[0] # Today's RunID

    for _ in range(1000):
        run_id = random.choice(RunIdList)
        qty_at_risk = round(random.uniform(10, 1000), 2)
        potential_saving = round(random.uniform(0, qty_at_risk), 2)
        
        # Logic: Current RunID vs Historical RunIDs
        if run_id == current_run_id:
            feedback = "Unactioned"
            actual_saving = None
            user_email = None
        else:
            # For past runs, randomize the feedback and savings
            feedback = random.choice(FeedbackList)
            actual_saving = round(random.uniform(0, potential_saving), 2) if feedback == "Accepted" else 0.0
            user_email = random.choice(UserEmailList)

        Substitution_raw_data.append((
            run_id,
            random.choice(CompIdList),
            random.choice(PlantIdList),
            random.choice(MatIdList),
            qty_at_risk,
            potential_saving,
            actual_saving,
            feedback,
            user_email
        ))

    # 4. Create DataFrame with Explicit Schema
    sub_schema = StructType([
        StructField("RunID", StringType(), True),
        StructField("ComponentId", StringType(), True),
        StructField("PlantId", StringType(), True),
        StructField("MaterialId", StringType(), True),
        StructField("QtyAtRisk", DoubleType(), True),
        StructField("PotentialSaving", DoubleType(), True),
        StructField("ActualSaving", DoubleType(), True),
        StructField("Feedback", StringType(), True),
        StructField("UserEmail", StringType(), True)
    ])

    substitution_df = (
        spark.createDataFrame(data=Substitution_raw_data, schema=sub_schema)
        .withColumn("CreatedTimestamp", current_timestamp())
    )
    
    return substitution_df


substitution_df = create_model_Data()

# Overwrite the table
substitution_df.write.format("delta").mode("overwrite").saveAsTable("Substitution")
# substitution_df.display()

# COMMAND ----------

# DBTITLE 1,BatchReplacement
# -----------------------------
# BatchReplacement & ProdIncrease
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS BatchReplacement (
    RunID STRING,
    ComponentId STRING,
    PlantId STRING,
    MaterialId STRING,
    QtyAtRisk DOUBLE,
    PotentialSaving DOUBLE,
    ActualSaving DOUBLE,
    Feedback STRING,
    UserEmail STRING,
    CreatedTimestamp TIMESTAMP
)
USING DELTA""")

batchReplacement_df= create_model_Data()

batchReplacement_df.write.format("delta").mode("overwrite").saveAsTable("BatchReplacement")
# batchReplacement_df.display()

# COMMAND ----------

# DBTITLE 1,ProdIncrease
spark.sql(f"""
CREATE TABLE IF NOT EXISTS ProdIncrease (
    RunID STRING,
    ComponentId STRING,
    PlantId STRING,
    MaterialId STRING,
    QtyAtRisk DOUBLE,
    PotentialSaving DOUBLE,
    ActualSaving DOUBLE,
    Feedback STRING,
    UserEmail STRING,
    CreatedTimestamp TIMESTAMP
)
USING DELTA""")

prodInc_df= create_model_Data()
prodInc_df.write.format("delta").mode("overwrite").saveAsTable("ProdIncrease")
# prodInc_df.display()

# COMMAND ----------

# DBTITLE 1,Master data
from pyspark.sql.functions import lit, current_timestamp, col
import random

# -----------------------------
# DimComponentExclusion Data
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS DimComponentExclusion (
    ComponentId STRING,
    PlantId STRING,
    ActiveFlag STRING,
    UserEmail STRING,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA""")

# Generate 50 entries using your predefined lists
exclusion_raw_data = [
    (
        random.choice(CompIdList), 
        random.choice(PlantIdList), 
        random.choice(["Y", "N"]),
        random.choice(UserEmailList)
    )
    for _ in range(50)
]

exclusion_df = (
    spark.createDataFrame(
        exclusion_raw_data,
        ["ComponentId", "PlantId", "ActiveFlag", "UserEmail"]
    )
    .withColumn("UpdatedTimestamp", current_timestamp())
)

exclusion_df.write.format("delta").mode("overwrite").saveAsTable("DimComponentExclusion")
# exclusion_df.display()

# -----------------------------
# DimSubstitution Data
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS DimSubstitution (
    ComponentId STRING,
    SubstituteOf STRING,
    PlantId STRING,
    ActiveFlag STRING,
    UserEmail STRING,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA""")

# Generate 1,000 lines of substitution mapping
substitution_list_data = [
    (
        random.choice(CompIdList),   # Original Component
        random.choice(CompIdList),   # Substitute Component
        random.choice(PlantIdList),  # Plant
        random.choice(["Y", "N"]),   # Active Status
        random.choice(UserEmailList) # User who updated it
    )
    for _ in range(1, 1001)
]

substitution_df = (
    spark.createDataFrame(
        substitution_list_data,
        ["ComponentId", "SubstituteOf", "PlantId", "ActiveFlag", "UserEmail"]
    )
    .withColumn("UpdatedTimestamp", current_timestamp())
)

# Optional: filter to ensure a component isn't a substitute of itself
substitution_df = substitution_df.filter(col("ComponentId") != col("SubstituteOf"))

substitution_df.write.format("delta").mode("overwrite").saveAsTable("DimSubstitution")
# substitution_df.display()

# COMMAND ----------

# DBTITLE 1,UserSettings
from pyspark.sql.functions import lit, current_timestamp
import random

# -----------------------------
# UserSettings Data
# -----------------------------
spark.sql(f"""
CREATE OR REPLACE TABLE UserSettings (
    PlantId STRING,
    ApprovedMailID STRING,
    UserEmail STRING,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA""")

# 1. Initialize mapping with your "All" access requirement
# We use a dictionary to group emails by PlantId: {PlantId: [email1, email2]}
plant_user_map = {"All": ["vikassingh0593@gmail.com"]}

# 2. Distribute other users across specific plants
for email in UserEmailList:
    if email != "vikassingh0593@gmail.com":
        # Assign each user to 2 random plants from your list
        assigned_plants = random.sample(PlantIdList, 2)
        for plant in assigned_plants:
            if plant not in plant_user_map:
                plant_user_map[plant] = []
            if email not in plant_user_map[plant]:
                plant_user_map[plant].append(email)

# 3. Format the data for Spark: Convert list of emails to a comma-separated string
user_settings_rows = [
    (plant, ", ".join(emails)) 
    for plant, emails in plant_user_map.items()
]

# 4. Create DataFrame and Write
user_settings_df = (
    spark.createDataFrame(
        user_settings_rows,
        ["PlantId", "ApprovedMailID"]
    )
    .withColumn("UserEmail", lit(None).cast("string")) # Keeping column as per your SQL definition
    .withColumn("UpdatedTimestamp", current_timestamp())
)

user_settings_df.write.format("delta").mode("overwrite").saveAsTable("UserSettings")

print("UserSettings table updated with unique PlantId rows.")

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bytemaster.appdata.usersettings

# COMMAND ----------

