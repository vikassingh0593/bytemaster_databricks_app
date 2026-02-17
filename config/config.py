# Databricks notebook source
# DBTITLE 1,Cell 1
# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS bytemaster;
# MAGIC USE CATALOG bytemaster;
# MAGIC DROP SCHEMA IF EXISTS appdata CASCADE;
# MAGIC CREATE SCHEMA appdata;
# MAGIC USE SCHEMA appdata;

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit
import random

# -----------------------------
# Substitution Data
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS Substitution (
    ComponentId STRING ,
    PlantId STRING ,
    MaterialId STRING ,
    Feedback STRING,
    UserEmail STRING ,
    CreatedTimestamp TIMESTAMP
)
USING DELTA""")

# Pools for randomization
Feedback = ["Accepted", "Under Review", "Rejected"]
# UserEmail = 
# ["vikas@email.com", "user2@email.com", "analyst1@email.com", "admin@email.com"]
PlantId = ["M1001", "M1002", "M1003", "M1004"]

# Generate 1,000 lines
Substitution_data = [
    (
        f"C{100 + i}",                   # Customer_ID (C101, C102...)
        f"P{random.randint(1, 20):02d}", # ComponentId (P01 to P20)
        random.choice(PlantId),           # PlantId
        random.choice(Feedback),         # Feedback
        # random.choice(UserEmail)            # Assigned Email
    )
    for i in range(1, 1001)
]

Substitution_df = (
    spark.createDataFrame(
        Substitution_data,
        ["ComponentId", "PlantId", "MaterialId", "Feedback"] #, "UserEmail"]
    )
    .withColumn("UserEmail", lit(None))
    .withColumn("CreatedTimestamp", current_timestamp())
)

# overwrite (identity column auto-generated)
Substitution_df.write.mode("overwrite").saveAsTable("Substitution")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS BatchReplacement (
    ComponentId STRING ,
    PlantId STRING ,
    MaterialId STRING ,
    Feedback STRING,
    UserEmail STRING ,
    CreatedTimestamp TIMESTAMP
)
USING DELTA
         """)
Substitution_df.write.mode("overwrite").saveAsTable("BatchReplacement")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS ProdIncrease (
    ComponentId STRING ,
    PlantId STRING ,
    MaterialId STRING ,
    Feedback STRING,
    UserEmail STRING ,
    CreatedTimestamp TIMESTAMP
)
USING DELTA
         """)
Substitution_df.write.mode("overwrite").saveAsTable("ProdIncrease")


# -----------------------------
# DimComponentExclusion Data
# -----------------------------
# exclusion_data = [
#     ("C101", "P01", "Y"),
#     ("C102", "P02", "N"),
# ]
spark.sql(f"""
CREATE TABLE IF NOT EXISTS DimComponentExclusion (
    ComponentId STRING ,
    PlantId STRING ,
    ActiveFlag STRING ,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA""")

# Generate 1,000 lines of mock exclusion data
exclusion_data = [
    (f"C{100 + i}", f"P{random.randint(1, 50):02d}", random.choice(["Y", "N"]))
    for i in range(1, 1001)
]

exclusion_df = (
    spark.createDataFrame(
        exclusion_data,
        ["ComponentId", "PlantId", "ActiveFlag"]
    )
    .withColumn("UpdatedTimestamp", current_timestamp())
)

exclusion_df.write.mode("overwrite").saveAsTable("DimComponentExclusion")


spark.sql(f"""
CREATE TABLE IF NOT EXISTS DimSubstitution (
    ComponentId STRING ,
    SubstituteOf STRING ,
    PlantId STRING ,
    ActiveFlag STRING ,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA
          """)
# Generate 1,000 lines of mock exclusion data
substitution_data = [
    (f"C{100 + i}", f"C{1000 + i}", f"P{random.randint(1, 50):02d}", random.choice(["Y", "N"]))
    for i in range(1, 1001)
]

substitution_data = (
    spark.createDataFrame(
        exclusion_data,
        ["ComponentId", "PlantId", "ActiveFlag"]
    )
    .withColumn("UpdatedTimestamp", current_timestamp())
)

substitution_data.write.mode("overwrite").saveAsTable("DimSubstitution")

# -----------------------------
# UserSettings Data
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS UserSettings (
    UserEmail STRING,
    NotificationsOn STRING,
    Theme STRING,
    UpdatedTimestamp TIMESTAMP
)
USING DELTA
          """)

user_settings_data = [
    ("vikas@email.com", "Y", "LIGHT"),
    ("user2@email.com", "N", "DARK"),
]

user_settings_df = (
    spark.createDataFrame(
        user_settings_data,
        ["UserEmail", "NotificationsOn", "Theme"]
    )
    .withColumn("UpdatedTimestamp", current_timestamp())
)

user_settings_df.write.mode("overwrite").saveAsTable("UserSettings")


# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bytemaster.appdata.ProdIncrease