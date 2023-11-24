import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Function to load data
def load_data():
    try:
        optimal_hub_results = pd.read_csv('Optimal_Hub_Results.csv', encoding='utf-8')
        route_details = pd.read_csv('Route_Details.csv', encoding='utf-8')
        disposal_sites = pd.read_csv('Disposal_Sites.csv', encoding='utf-8')
        removal_sites = pd.read_csv('Removal_Sites.csv', encoding='utf-8')
    except UnicodeDecodeError:
        optimal_hub_results = pd.read_csv('Optimal_Hub_Results.csv', encoding='ISO-8859-1')
        route_details = pd.read_csv('Route_Details.csv', encoding='ISO-8859-1')
        disposal_sites = pd.read_csv('Disposal_Sites.csv', encoding='ISO-8859-1')
        removal_sites = pd.read_csv('Removal_Sites.csv', encoding='ISO-8859-1')
    return optimal_hub_results, route_details, disposal_sites, removal_sites

# Function to calculate disposal site utilization
# Function to calculate disposal site utilization
def calculate_utilization(selected_hub, route_details, disposal_sites):
    selected_hub_routes = route_details[route_details['Hub'] == selected_hub]
    snow_by_disposal_site = selected_hub_routes.groupby('DisposalSite')['SnowTransported'].sum().reset_index()
    utilization_df = pd.merge(snow_by_disposal_site, disposal_sites, left_on='DisposalSite', right_on='NomDepot')
    
    # Setting capacity and utilization based on conditions
    utilization_df['Capacite m3'] = utilization_df['Capacite m3'] / 1e6  # Convert to millions
    for index, row in utilization_df.iterrows():
        if row['Capacite m3'] >= 10:
            utilization_df.at[index, 'Capacite m3'] = "Unlimited"
            utilization_df.at[index, 'Utilization (%)'] = "-"
        else:
            utilization_df.at[index, 'Utilization (%)'] = round((row['SnowTransported'] / (row['Capacite m3'] * 1e6)) * 100,2)

    utilization_df.rename(columns={'SnowTransported': 'Total Snow Disposed (m³)', 'Capacite m3': 'Capacity (M m³)'}, inplace=True)
    return utilization_df

# Function to create a map visualization with interactive popups
def create_map(selected_hub, route_details, disposal_sites, removal_sites):
    map_center = [45.5017, -73.5673]  # Set a default center
    map = folium.Map(location=map_center, zoom_start=11)

    # Marking the optimal hub
    hub_lat, hub_lng = removal_sites.loc[removal_sites['NomSecteur'] == selected_hub, ['Latitude', 'Longitude']].values[0]
    folium.Marker(
        [hub_lat, hub_lng],
        popup=f"Optimal Hub: {selected_hub}",
        icon=folium.Icon(color='green', icon='star')
    ).add_to(map)

    # Marking pickup centers with interactive popups and varied sizes
    for _, row in removal_sites.iterrows():
            if row['NomSecteur'] != selected_hub:
                snow_transported = route_details[(route_details['Hub'] == selected_hub) & (route_details['RemovalSite'] == row['NomSecteur'])]['SnowTransported'].sum()
                marker_size = max(3, min(8, snow_transported / 200000)) if snow_transported > 0 else 1
                folium.CircleMarker(
                    [row['Latitude'], row['Longitude']],
                    radius=marker_size,
                    popup=f"Pickup: {row['NomSecteur']}<br>Priority: {row['Priority']}<br>Snow Transported: {snow_transported} m³",
                    color='blue',
                    fill=True,
                    fill_color='blue'
                ).add_to(map)

    # Marking disposal sites with triangle markers and varied sizes
    for _, row in disposal_sites.iterrows():
        snow_disposed = route_details[(route_details['Hub'] == selected_hub) & (route_details['DisposalSite'] == row['NomDepot'])]['SnowTransported'].sum()
        marker_size = max(3, min(8, snow_disposed / 200000)) if snow_disposed > 0 else 1
        folium.RegularPolygonMarker(
            [row['Latitude'], row['Longitude']],
            number_of_sides=3,
            radius=marker_size,
            popup=f"Disposal: {row['NomDepot']}<br>Cost: {row['Cost ($/m3)']} $/m³<br>Snow Disposed: {snow_disposed} m³",
            color='red',
            fill=True,
            fill_color='red'
        ).add_to(map)

    # Drawing routes
    for _, row in route_details[route_details['Hub'] == selected_hub].iterrows():
        start_point = [row['Start_Lat'], row['Start_Lng']]
        end_point = [row['End_Lat'], row['End_Lng']]
        line_width = row['SnowTransported'] / 200000  # Example scaling for line width
        folium.PolyLine([start_point, end_point], color='blue', weight=line_width).add_to(map)

    return map

# Streamlit app main section
st.title('Snow Removal Optimization')

# Load data
optimal_hub_results, route_details, disposal_sites, removal_sites = load_data()

# Dropdown to select a hub
selected_hub = st.selectbox('Select a Hub', optimal_hub_results['Hub'])

# Display cost for selected hub in millions
hub_cost = optimal_hub_results[optimal_hub_results['Hub'] == selected_hub]['TotalCost'].iloc[0]
st.write(f"Total Cost for {selected_hub}: ${hub_cost / 1e6:.2f} M")

# Display utilization of disposal sites
utilization_df = calculate_utilization(selected_hub, route_details, disposal_sites)
st.write("Utilization of Disposal Sites:")
st.dataframe(utilization_df[['NomDepot', 'Capacity (M m³)', 'Total Snow Disposed (m³)', 'Utilization (%)']])

# Map visualization
map = create_map(selected_hub, route_details, disposal_sites, removal_sites)
st_folium(map, width=900, height=700)

# Run the app by entering following command in terminal: streamlit run streamlit_app.py
