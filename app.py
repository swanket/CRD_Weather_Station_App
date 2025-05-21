import os
os.environ["WATCHDOG_IGNORE"] = "1"

import streamlit as st
import psycopg2
import polars as pl
import plotly.express as px
from st_supabase_connection import SupabaseConnection


# def query_to_polars(query: str) -> pl.DataFrame:
#     creds = st.secrets["postgres"]
#     conn = psycopg2.connect(
#         host=creds["host"],
#         port=creds["port"],
#         dbname=creds["dbname"],
#         user=creds["user"],
#         password=creds["password"]
#     )
#     cur = conn.cursor()
#     cur.execute(query)
#     cols = [desc[0] for desc in cur.description]
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     return pl.DataFrame(rows, schema=cols)

conn = st.connection("connections.supabase", type = SupabaseConnection)
# st_supabase = st.connection(
#     name="supabase_connection", 
#     type=SupabaseConnection, 
#     ttl=None,
#     url=url, 
#     key=key, 
# )

st.title("Weather Station Explorer")

# Example: Select station and number of rows
# limit = st.slider("Number of rows", 10, 500, 100)
# station_filter = st.text_input("Filter by station name (optional)")

# rows = conn.query("*", table = "stations", ttl = "10m").execute()
rows = conn.table("variables").select("*").execute()

st.write('Hello World!')
st.write(f'{rows.data}')

# for row in rows.data:
#     st.write(f'Station {row["Native ID"]} is at {row["Elevation"]} and began recording on {row["Record Start"]}.')

# query = f"SELECT * FROM stations"
# if station_filter:
#     query += f" WHERE station_name ILIKE '%{station_filter}%'"
# query += f" LIMIT {limit}"

# st.code(query)
# df = query_to_polars(query)
# st.dataframe(df.to_pandas())

# # --- PLOTTING ---
# # Only show plot if there are numeric columns
# numeric_cols = [col for col in df.columns if pl.datatypes.is_numeric_dtype(df[col].dtype)]
# if numeric_cols:
#     x_axis = st.selectbox("X-Axis", options=numeric_cols)
#     y_axis = st.selectbox("Y-Axis", options=numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
#     fig = px.scatter(df.to_pandas(), x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
#     st.plotly_chart(fig)
# else:
#     st.info("No numeric columns available for plotting.")