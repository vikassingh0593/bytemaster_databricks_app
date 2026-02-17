# Databricks notebook source
import datetime
datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# COMMAND ----------

# MAGIC %sql
# MAGIC alter table bytemaster.appdata.DimSubstitution
# MAGIC add column UserEmail string

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bytemaster.appdata.DimSubstitution