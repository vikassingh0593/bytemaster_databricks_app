# Databricks notebook source
import datetime
datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        /* 5. BUTTON STYLING – grey for all (primary & secondary) */
        div.stButton > button {
            padding: 2px 5px !important;
            height: 2.2rem !important;
            min-height: 0px !important;
            min-height: 0px !important;
        }
        div[data-baseweb="select"] > div {
            height: 2.2rem !important;
            min-height: 0px !important;
        }
        # /* 5. BUTTON STYLING - BASE */
        # div.stButton > button {
        #     padding: 2px 5px !important;
        #     height: 2.2rem !important;
        #     min-height: 0px !important;
        #     transition: all 0.2s ease-in-out;
        # }
        
        # /* HOVER STATE FOR SECONDARY BUTTONS */
        # div.stButton > button:hover {
        #     border-color: #6c757d !important;
        #     color: #6c757d !important; 
        # }

        # /* OVERRIDE STREAMLIT'S DEFAULT PRIMARY RED BUTTON */
        # div.stButton > button[kind="primary"] {
        #     background-color: #6c757d !important;
        #     border-color: #6c757d !important;
        #     color: white !important;
        # }

        # /* HOVER FOR PRIMARY BUTTONS */
        # div.stButton > button[kind="primary"]:hover {
        #     background-color: #5a6268 !important; /* Slightly darker grey on hover */
        #     border-color: #5a6268 !important;
        # }

        # /* CLICK / ACTIVE / FOCUS STATE FOR ALL BUTTONS */
        # div.stButton > button:active, 
        # div.stButton > button:focus {
        #     background-color: #5a6268 !important; 
        #     border-color: #5a6268 !important;     
        #     color: white !important;              
        #     box-shadow: none !important;          
        # }

        # div[data-baseweb="select"] > div {
        #     height: 2.2rem !important;
        #     min-height: 0px !important;
        # }
    </style>
    """, unsafe_allow_html=True)

# COMMAND ----------

# MAGIC %sql
# MAGIC alter table bytemaster.appdata.DimSubstitution
# MAGIC add column UserEmail string

# COMMAND ----------

# MAGIC %sql
# MAGIC select *
# MAGIC from bytemaster.appdata.DimSubstitution