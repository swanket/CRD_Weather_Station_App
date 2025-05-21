import os
os.environ["WATCHDOG_IGNORE"] = "1"

import streamlit as st
import psycopg2
import polars as pl
import plotly.express as px
from st_supabase_connection import SupabaseConnection
from datetime import datetime


conn = st.connection("supabase", type = SupabaseConnection)


st.title("Capital Region District Weather Station Explorer")


# rows = conn.query("*", table = "stations", ttl = "10m").execute()
stations = conn.table("stations").select("*").execute() # .eq("Native ID","FW001")

table_generator = st.text_input("Display a table: stations, variables, readings, or station_readings (optional)")
if st.button("Show me a Table"):
    if table_generator:
        if table_generator == 'stations':
            st.write(pl.DataFrame(stations.data))
        if table_generator == 'variables':
            st.write(pl.DataFrame(conn.table("variables").select("*").execute().data))
        if table_generator == 'station_readings':
            st.write(pl.DataFrame(conn.table("station_readings").select("*").execute().data))
        else:
            st.error("Pick a valid table: stations, variables, readings, or station_readings ")
    else: 
        st.error("Enter a table name: stations, variables, readings, or station_readings")


station_temp = st.text_input("Pick a Station to Plot Air Temperature")
year = st.text_input('And a starting year')
if int(year) >= 2005:
    st.error("Choose a year before 2005.")
# start_year = datetime(int(year),1,1)
if st.button('Plot'):
    if station_temp:
        if year:
            df = pl.DataFrame(conn.table("readings").select("*").eq("station_id",station_temp).eq("variable_id","9").gte("record_ts",datetime(int(year),1,1).isoformat()).order("record_ts",desc=False).execute().data)
            # air_temp = df["value"]
            # time = df["record_ts"]
            # st.write(f'{df.shape}')
            # st.write(df["record_ts","value"][0:10,:])
            # x_axis = st.selectbox("X-Axis", options=numeric_cols)
            # y_axis = st.selectbox("Y-Axis", options=numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
            fig = px.scatter(df, x="record_ts",y="value", title=f"Temperature at Station {station_temp}",labels={"record_ts":"Timestamp","value":"Air temperature (C)"})
            st.plotly_chart(fig)
        else:
            st.error("Pick a year.")
    else:
        st.error("Pick a station.")

# for row in stations.data:
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