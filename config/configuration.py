import yaml
from pydantic import BaseModel, model_validator
from typing import List, Dict

# --- 1. PYDANTIC MODELS ---
class DatabaseModel(BaseModel):
    catalog: str
    schema_name: str

class DatasetModel(BaseModel):
    table: str
    join_keys: List[str]
    update_columns: List[str]
    filter_columns: List[str]

class AppConfig(BaseModel):
    database: DatabaseModel
    datasets: Dict[str, DatasetModel]

    # 🆕 MAGIC HAPPENS HERE: This runs automatically after the YAML is loaded
    @model_validator(mode='after')
    def resolve_table_names(self):
        cat = self.database.catalog
        sch = self.database.schema_name
        
        # Loop through every dataset and format the table string
        for dataset in self.datasets.values():
            # This replaces {catalog} and {schema_name} with the actual values
            dataset.table = dataset.table.format(
                catalog=cat, 
                schema_name=sch
            )
        return self

# --- 2. LOADER FUNCTION ---
def load_dataset_config(file_path: str = "config/config.yml") -> dict:
    with open(file_path, "r") as file:
        raw_yaml = yaml.safe_load(file)
        
    # Validates data AND runs the string replacement
    config = AppConfig(**raw_yaml)
    
    # Dump back to dictionary for Streamlit
    return config.model_dump()["datasets"]

# --- 3. TEST IT OUT ---
DATASET_CONFIG = load_dataset_config()

# If you print this, it will output exactly what you want: 
# "bytemaster.appdata.AlternativeSourcing"
# print(DATASET_CONFIG["AlternativeSourcing"]["table"])