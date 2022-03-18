from urllib import request
import pandas as pd
import numpy as np
from leafmap import osm_gdf_from_bbox
from folium import Map as FoliumMap
from shapely.ops import unary_union
from folium.plugins import HeatMap
from itertools import chain
from flask import Flask, render_template, request

# FOR DEBUG: pd.options.display.max_colwidth = 300

app = Flask(__name__, instance_relative_config=True)

def create_map(latituge, longitude, zoom_start=2):
    return FoliumMap([latituge, longitude], zoom_start=zoom_start, min_zoom=2, max_zoom=19, width='75%', height='75%')

def get_geodataframe(north, south, east, west, tags):
    return osm_gdf_from_bbox(north, south, east, west, tags)['geometry']

def get_coords(gdf):
    coords = []
    for geom_obj in gdf.loc[['way']].geometry:
        if geom_obj.geom_type == 'Polygon':
            coords.append(geom_obj.exterior.coords)
        elif geom_obj.geom_type == 'LineString':
            distances = np.linspace(0, geom_obj.length, 30)
            points = [geom_obj.interpolate(distance) for distance in distances]
            multipoint = unary_union(points)
            xcoords, ycoords = list(zip(*[(p.x, p.y) for p in multipoint]))        
            coords.append(list(zip(xcoords, ycoords)))
    return coords

def valid_coords(first_coord, second_coord):
    if first_coord <= second_coord:
        return False
    return True

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
        folium_map.add_child(HeatMap(df, name="Heat Map", min_opacity=0.2, radius=30, blur=50, max_zoom=1))
    else:
        folium_map = create_map(0.0, 0.0)

    folium_map.save('app/templates/map.html')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
