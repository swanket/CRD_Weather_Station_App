import os
os.environ["WATCHDOG_IGNORE"] = "1"

import streamlit as st
import numpy as np
import polars as pl
import plotly.express as px
import matplotlib.pyplot as plt
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# def running_mean(x,time,winlen):


conn = st.connection("supabase", type = SupabaseConnection)


st.title("Capital Region District Weather Station Explorer")

# st.map(pl.DataFrame(conn.table("stations").select("*").execute().data), latitude="Latitude",longitude="Longitude",size=100)

st.header("1. Map of the Capital Region District")
st.write("Here I have gathered data from five CRD weather stations spanning from 1996 through 2004. The locations of the 5 stations can be seen in the map below.")

fig = px.scatter_map(pl.DataFrame(conn.table("stations").select("*").execute().data), lat="Latitude",lon="Longitude",text="Native ID", color_discrete_sequence=['red'])
st.plotly_chart(fig)

st.header("2. The Database")
st.write("This data was all downloaded from https://services.pacificclimate.org/met-data-portal-pcds/app/#close. I limited my data originally to the nine weather stations measured by the CRD. " \
"I first created a database locally on my personal machine which included all historic data gathered at these nine stations. The data pull from the website gave me a table for each station which " \
"included many NULL values where a reading was skipped that day. To handle this I normalized the database and created the readings table. I gave each variable an specific identifier (variable_ID) " \
"and only included readings with a non-NULL value. This both saved space in the database and made the table much cleaner and user friendly. The variables and their respective identifiers are in " \
"the variables table.")
st.write("After creating the full database locally, I had to move it to a cloud based system (in my case I used supabase) so that my Streamlit app could access it. Because supabase free only allows " \
"up to 500 MB of data I shrunk my database to only include data collected before Jan 1, 2005. This cut down the number of stations to five.")
st.write("Below you can view the four tables in my supabase database. Stations includes data on the stations. Variables includes information on the weather parameters measured. Station_readings " \
"is a boolean matrix which shows which variabels each station measures. Readings gives the date and value of each reading.")


# rows = conn.query("*", table = "stations", ttl = "10m").execute()
stations = conn.table("stations").select("*").execute() # .eq("Native ID","FW001")
table_generator = st.selectbox("Display a table", ("stations", "variables", "readings", "station_readings"))
if st.button("Show me a Table"):
    if table_generator:
        if table_generator == 'stations':
            st.write(pl.DataFrame(stations.data))
        elif table_generator == 'variables':
            st.write(pl.DataFrame(conn.table("variables").select("*").execute().data))
        elif table_generator == 'station_readings':
            st.write(pl.DataFrame(conn.table("station_readings").select("*").execute().data))
        elif table_generator == 'readings':
            st.write(pl.DataFrame(conn.table("readings").select("*").limit(10).execute().data))
        else:
            st.error("Pick a valid table: stations, variables, readings, or station_readings ")
    else: 
        st.error("Enter a table name: stations, variables, readings, or station_readings")

st.header("3. Visualizing the Data")
st.write("Here you can plot data starting on January 1st of the year you specify.")

col1, col2 = st.columns(2)

with col1:
    station_temp = st.selectbox("Pick a Station (Native ID)", ('FW001','FW003','FW004','FW005','FW006'))
    year = st.text_input('And a starting year')
    if station_temp == "FW001":
        variable = st.selectbox('Which variable would you like to plot? (use variable_id)',('9','1','4','5','6','8'))
    elif station_temp == "FW003":
        variable = st.selectbox('Which variable would you like to plot? (use variable_id)',('9','1','6','8'))
    elif station_temp == "FW004":
        variable = st.selectbox('Which variable would you like to plot? (use variable_id)',('9','1','5','6','7','8'))
    elif station_temp == "FW005":
        variable = st.selectbox('Which variable would you like to plot? (use variable_id)',('9','4'))
    elif station_temp == "FW006":
        variable = st.selectbox('Which variable would you like to plot? (use variable_id)',('9','1','5','6','8'))

# with col2:
#     rm = st.checkbox('Would you like to display the running mean?')
    # if rm:
    #     winlen = st.text_input('Window Lenth: ')
    #     # if int(winlen) :

    # else:
    #     st.error("Set a window Length")

if st.button('Plot'):
    if station_temp:
        if year:
            if int(year) >= 2005:
                st.error("Choose a year before 2005.")
            else:
                df = pl.DataFrame(conn.table("readings").select("*").eq("station_id",station_temp).eq("variable_id",variable).gte("record_ts",datetime(int(year),1,1).isoformat()).order("record_ts",desc=False).execute().data)
                # if variable not in df["variable_id"].to_list():
                #     st.error("Must pick a variable that the station records.")
                # fig = px.scatter(df, x="record_ts",y="value", title=f"Temperature at Station {station_temp}",labels={"record_ts":"Timestamp","value":"Air temperature (C)"})
                fig = px.scatter(df, x="record_ts",y="value", labels={"record_ts":"Timestamp","value":f"{pl.DataFrame(conn.table("variables").select("name").eq("variable_id",variable).execute().data)["name"][0]} ({pl.DataFrame(conn.table("variables").select("unit").eq("variable_id",variable).execute().data)["unit"][0]})"})
                st.plotly_chart(fig)

        else:
            st.error("Pick a year.")
    else:
        st.error("Pick a station.")


st.header("4. Some Analysis: Polynomial Regression of Air Temperature")
st.write("Here you can run a polynomial regression on air temperature for any of the stations and any year. This will smooth the data by supressing noise.")

station_poly = st.selectbox("Pick a Station", ('FW001','FW003','FW004','FW005','FW006'))
poly_year = st.slider("Year to fit",1995,2004,1995,1)
poly_degree = st.slider("Degree of the polynomial", 1,6,3,1)
df = pl.DataFrame(conn.table("readings").select("*").eq("station_id",station_poly).eq("variable_id",9).gte("record_ts",datetime(poly_year,1,1).isoformat()).order("record_ts",desc=False).execute().data)
poly = np.polyfit(df["record_ts"],df["value"],deg=poly_degree)
