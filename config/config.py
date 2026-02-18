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

# -----------------------------
# Substitution Data
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS Substitution (
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

# Pools for randomization
Feedback_Options = ["Unactioned"]
PlantId_Options = ["M1001", "M1002", "M1003", "M1004"]

# Generate 1,000 lines
Substitution_raw_data = []
for i in range(1, 1001):
    qty_at_risk = round(random.uniform(10, 1000), 2)
    potential_saving = round(random.uniform(0, qty_at_risk), 2)
    
    Substitution_raw_data.append((
        f"C{100 + i}",                   
        random.choice(PlantId_Options),          
        f"M{random.randint(1000, 9999)}",
        qty_at_risk, 
        potential_saving, 
        # Note: ActualSaving and UserEmail are handled via Schema or withColumn below to avoid Type Inference errors
        Feedback_Options[0] 
    ))

# Define schema explicitly to handle potential nulls if included in list, 
# or use withColumn for null columns. Here we use a mixed approach for robustness.
sub_schema = StructType([
    StructField("ComponentId", StringType(), True),
    StructField("PlantId", StringType(), True),
    StructField("MaterialId", StringType(), True),
    StructField("QtyAtRisk", DoubleType(), True),
    StructField("PotentialSaving", DoubleType(), True),
    StructField("Feedback", StringType(), True)
])

Substitution_df = (
    spark.createDataFrame(data=Substitution_raw_data, schema=sub_schema)
    .withColumn("ActualSaving", lit(None).cast("double")) # Add null column explicitly
    .withColumn("UserEmail", lit(None).cast("string"))    # Add null column explicitly
    .withColumn("CreatedTimestamp", current_timestamp())
)

# Reorder columns to match Table definition
Substitution_df = Substitution_df.select(
    "ComponentId", "PlantId", "MaterialId", "QtyAtRisk", "PotentialSaving", 
    "ActualSaving", "Feedback", "UserEmail", "CreatedTimestamp"
)

Substitution_df.write.format("delta").mode("overwrite").saveAsTable("Substitution")

# -----------------------------
# BatchReplacement & ProdIncrease
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS BatchReplacement (
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
Substitution_df.write.format("delta").mode("overwrite").saveAsTable("BatchReplacement")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS ProdIncrease (
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
Substitution_df.write.format("delta").mode("overwrite").saveAsTable("ProdIncrease")


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

# Generate 1,000 lines
# REMOVED the `None` from this list to prevent inference error
exclusion_raw_data = [
    (f"C{100 + i}", f"P{random.randint(1, 50):02d}", random.choice(["Y", "N"]))
    for i in range(1, 1001)
]

exclusion_df = (
    spark.createDataFrame(
        exclusion_raw_data,
        ["ComponentId", "PlantId", "ActiveFlag"] # Removed UserEmail from here
    )
    .withColumn("UserEmail", lit(None).cast("string")) # Added here safely
    .withColumn("UpdatedTimestamp", current_timestamp())
)

exclusion_df.write.format("delta").mode("overwrite").saveAsTable("DimComponentExclusion")


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

# Generate 1,000 lines
# REMOVED the `None` from this list to prevent inference error
substitution_list_data = [
    (f"C{100 + i}", f"C{1000 + i}", f"P{random.randint(1, 50):02d}", random.choice(["Y", "N"]))
    for i in range(1, 1001)
]

substitution_df = (
    spark.createDataFrame(
        substitution_list_data,
        ["ComponentId", "SubstituteOf", "PlantId", "ActiveFlag"] # Removed UserEmail from here
    )
    .withColumn("UserEmail", lit(None).cast("string")) # Added here safely
    .withColumn("UpdatedTimestamp", current_timestamp())
)

substitution_df.write.format("delta").mode("overwrite").saveAsTable("DimSubstitution")

# -----------------------------
# UserSettings Data
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS UserSettings (
    PlantId STRING,
    UserEmail STRING,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA""")

user_settings_data = [
    ("All", "vikassingh0593@gmail.com"),
]

user_settings_df = (
    spark.createDataFrame(
        user_settings_data,
        ["PlantId", "UserEmail"]
    )
    .withColumn("UpdatedTimestamp", current_timestamp())
)

user_settings_df.write.format("delta").mode("overwrite").saveAsTable("UserSettings")

print("Data generation complete.")


# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bytemaster.appdata.ProdIncrease