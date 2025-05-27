import streamlit as st
import numpy as np
import polars as pl
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from st_supabase_connection import SupabaseConnection
from datetime import datetime
from datetime import timedelta
import plotly.graph_objects as go
import pydeck as pdk
import requests


# Connect to the Supabase database
conn = st.connection("supabase", type = SupabaseConnection)

# Set the Title
st.title("Capital Region District Weather Station Explorer")

# Create section 1 and write intro
st.header("1. Map of the Capital Region District")
st.write("Here I have gathered data from five CRD weather stations spanning from 1996 through 2004. The locations of the 5 stations can be seen in the map below.")


# Plot the locations of the 5 stations on an interactive map
fig = px.scatter_map(pl.DataFrame(conn.table("stations").select("*").execute().data), lat="Latitude",lon="Longitude",text="Native ID", color_discrete_sequence=['red'])
st.plotly_chart(fig)

# Create and write section 2
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


# Create a table display button with input paramaeters
stations = conn.table("stations").select("*").execute() # connect to the stations table
table_generator = st.selectbox("Display a table", ("stations", "variables", "readings", "station_readings")) # create a selection box input
if st.button("Show me a Table"): # create a button which displays one of the tables in the database
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
            st.error("Pick a valid table: stations, variables, readings, or station_readings ") # send an error if a table which isn't real is picked
    else: 
        st.error("Enter a table name: stations, variables, readings, or station_readings") # send an error if no table is picked


# Create and write section 3
st.header("3. Visualizing the Data")
st.write("Here you can plot data starting on January 1st of the year you specify.")

# plot a variable starting in a designated year from a designated station

station_temp = st.selectbox("Pick a Station (Native ID)", ('FW001','FW003','FW004','FW005','FW006')) # Pick a station using a selectbox
# year = st.text_input('And a starting year')
year = st.slider('And a starting year',1995,2004,1995,1) # pick a year using a selectbox

# Pick the variable to plot
if station_temp == "FW001":
    variable = st.selectbox('Which variable would you like to plot? (Check the variables table for variable_id descriptions)',('9','1','4','5','6','8'))
elif station_temp == "FW003":
    variable = st.selectbox('Which variable would you like to plot? (Check the variables table for variable_id descriptions)',('9','1','6','8'))
elif station_temp == "FW004":
    variable = st.selectbox('Which variable would you like to plot? (Check the variables table for variable_id descriptions)',('9','1','5','6','7','8'))
elif station_temp == "FW005":
    variable = st.selectbox('Which variable would you like to plot? (Check the variables table for variable_id descriptions)',('9','4'))
elif station_temp == "FW006":
    variable = st.selectbox('Which variable would you like to plot? (Check the variables table for variable_id descriptions)',('9','1','5','6','8'))

# create a button which produces tht plot
if st.button('Plot'):
    if station_temp:
        if year:
            if int(year) >= 2005:
                st.error("Choose a year before 2005.")
            else:
                df = pl.DataFrame(conn.table("readings").select("*").eq("station_id",station_temp).eq("variable_id",variable).gte("record_ts",datetime(int(year),1,1).isoformat()).order("record_ts",desc=False).execute().data)
       
                fig = px.scatter(df, x="record_ts",y="value", labels={"record_ts":"Timestamp","value":f"{pl.DataFrame(conn.table("variables").select("name").eq("variable_id",variable).execute().data)["name"][0]} ({pl.DataFrame(conn.table("variables").select("unit").eq("variable_id",variable).execute().data)["unit"][0]})"})
                st.plotly_chart(fig)

        else:
            st.error("Pick a year.") # error if there is no year picked
    else:
        st.error("Pick a station.") # error if there is no station picked

st.write("Below is an interactive map where you can view air temperature at each station for a given day and time.")

# Load token from Streamlit secrets
MAPBOX_TOKEN = st.secrets["mapbox"]["token"]
pdk.settings.mapbox_api_key = MAPBOX_TOKEN

map_year = st.slider("Year to view",1995,2004,1995,1) # Select a year
# Get min and max datetimes
if map_year == 1995:
    min_ts = datetime(map_year,11,13,11)
    max_ts = datetime(map_year,12,31,23)    
else:
    min_ts = datetime(map_year,1,1)
    max_ts = datetime(map_year,12,31,23)

# Create slider
selected_time = st.slider("Select date and time:",min_value=min_ts,max_value=max_ts,value=min_ts,step=timedelta(hours=1),format="YYYY-MM-DD HH:mm:ss")

df = pl.DataFrame(conn.table("readings").select("station_id,record_ts,value,stations(Latitude,Longitude)").eq("variable_id",9).eq("record_ts",selected_time.isoformat()).execute().data)
if df.is_empty():
    st.error("No data for this date.")

# Extract Latitude and Longitude from struct
else:
    df = df.with_columns([pl.col("stations").struct.field("Latitude").alias("Latitude"),pl.col("stations").struct.field("Longitude").alias("Longitude")])
    df = df.drop("stations")

    
    lat_lon_df = pl.DataFrame(conn.table("stations").select("Latitude,Longitude").execute().data)
    distinct_lat_lon = lat_lon_df.unique(subset=["Latitude","Longitude"])
    mean_lat = distinct_lat_lon["Latitude"].mean()
    mean_lon = distinct_lat_lon["Longitude"].mean()
    radius = 20000
    # Overpass query for towns
    query = f"""[out:json];node(around:{radius},{mean_lat},{mean_lon})["place"~"town|city|village"];out center;"""
    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(url, params={'data': query})

    # Extract results cleanly into a Polars DataFrame
    towns = [{"name": e.get("tags", {}).get("name", "Unnamed"),"place_type": e.get("tags", {}).get("place", "unknown"),"latitude": e["lat"],"longitude": e["lon"]} for e in response.json().get("elements", [])]
    towns_df = pl.DataFrame(towns)
    towns_pd = towns_df.to_pandas()
    # st.write(towns_df)

    # Create a pydeck map
    df_pd = df.to_pandas()
    stations_layer = pdk.Layer("ScatterplotLayer",df_pd,get_position='[Longitude, Latitude]',get_color='[200, 30, 0, 160]',get_radius=1000,pickable=True)
    towns_layer = pdk.Layer("ScatterplotLayer",towns_pd,get_position ='[longitude, latitude]', get_color = '[0,100,255,180]',get_radius=2000,pickable = True)

    # Set the viewport
    view_state = pdk.ViewState(latitude=df_pd["Latitude"].mean(),longitude=df_pd["Longitude"].mean(),zoom=7,pitch=0)
 
    # Display the map
    st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/satellite-streets-v11",layers=[stations_layer],initial_view_state=view_state,tooltip={"text": "{station_id}\nTemp: {value} °C"}))
    # st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/light-v10",layers=[stations_layer,towns_layer],initial_view_state=view_state,tooltip={"html": """<b>{station_id}</b><br />Temp: {value}°C<br />POI: {name}<br />Type: {place_type}""","style": {"backgroundColor": "black", "color": "white"}}))

# Create and write section 4
st.header("4. Some Analysis: Polynomial Regression of Air Temperature")
st.write("Here you can run a polynomial regression on air temperature for any of the stations and any year. This regression uses an n-th degree polynomial to model the raw data. This " \
"creates a best fit line for the raw data depending on the degree of the polynomial chosen. Increasing the degree of the polynomial will allow the model to capture fluctuations " \
"and different wavelengths in the data, but you run the risk of introducing wavelengths that do not exist in the real dataset.")

station_poly = st.selectbox("Pick a Station", ('FW001','FW003','FW004','FW005','FW006')) # Select a station
poly_year = st.slider("Year to fit",1995,2004,1995,1) # Select a year
poly_degree = st.slider("Degree of the polynomial", 1,20,3,1) # SElect a degree of the polynomial
df = pl.DataFrame(conn.table("readings").select("*").eq("station_id",station_poly).eq("variable_id",9).gte("record_ts",datetime(poly_year,1,1).isoformat()).order("record_ts",desc=False).execute().data) # Create the dataframe where year >= year chosen and the station is the station chosen
datetimes = [datetime.fromisoformat(ts) for ts in df["record_ts"].to_numpy()] # text time column to datetimes
timestamps = np.array([dt.timestamp() for dt in datetimes]) # convert datetimes to timestamp type
timestamps -= timestamps.min() # normalize timestamps
values = np.array(df["value"].to_numpy(),dtype = float) # create an array with all of the values
poly = np.polyfit(timestamps,values,deg=poly_degree) # create the polynomial fit 
mymodel = np.poly1d(poly) # create a model which uses the polynomial fit
df = df.with_columns(pl.Series("Polyfit",mymodel(timestamps))) # add the polynomial regression to the polars dataframe as a new column called "Polyfit"

# Plot the raw data and the regression
fig = px.line(df,x="record_ts",y="Polyfit",)
fig.add_trace(go.Scatter(x=df["record_ts"].to_list(),
        y=df["value"].to_list(),
        name="Raw Data",
        line=dict(color="red")))
st.plotly_chart(fig)

