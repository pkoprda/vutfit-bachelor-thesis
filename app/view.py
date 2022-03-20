import pandas as pd
from folium.plugins import HeatMap
from itertools import chain
from flask import render_template, request
from app import app
from app.osm_map import create_map, get_geodataframe, get_coords, valid_coords


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        north = float(request.form['north'])
        south = float(request.form['south'])
        if not valid_coords(north, south):
            return render_template('index.html', error_statement="North coordinate must be larger than south coordinate")

        east = float(request.form['east'])
        west = float(request.form['west'])
        if not valid_coords(east, west):
            return render_template('index.html', error_statement="East coordinate must be larger than west coordinate")

        app.logger.info("Creating a Map...")
        center_lat = (north + south) / 2
        center_long = (east + west) / 2
        folium_map = create_map(center_lat, center_long, zoom_start=16)

        app.logger.info("Creating a GeoDataFrame of OSM entities within a N, S, E, W bounding box...")
        gdf = get_geodataframe(north, south, east, west, tags={"highway": True})

        try:
            app.logger.info("Creating list of coordinates...")
            coords = list(chain(*get_coords(gdf)))
        except KeyError:
            app.logger.info("Could not create list of coordinates. Try different values...")
            return render_template('index.html', error_statement="Could not create heatmap")

        longs, lats = list(zip(*coords))
        data = {"lats": lats, "longs": longs}
        df = pd.DataFrame(data)

        app.logger.info("Creating a HeatMap...")
        folium_map.add_child(HeatMap(
            df, name="Heat Map", min_opacity=0.2,
            radius=30, blur=50, max_zoom=1))
    else:
        folium_map = create_map(0.0, 0.0)

    folium_map.save('app/templates/map.html')
    return render_template('index.html')
