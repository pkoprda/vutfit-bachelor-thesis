import folium
import pandas as pd
from folium import Element
from folium.plugins import HeatMap
from itertools import chain
from flask import render_template, request, jsonify
from app import app
from app.osm_map import create_map, get_geodataframe, get_coords, valid_coords


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        borders = {
            'north': round(float(request.form['north']), 5),
            'south': round(float(request.form['south']), 5),
            'east': round(float(request.form['east']), 5),
            'west': round(float(request.form['west']), 5)
        }

        if 'submit' in request.form:
            app.logger.info("Creating a Map...")
            center_lat = (borders['north'] + borders['south']) / 2
            center_long = (borders['east'] + borders['west']) / 2
            folium_map = create_map(center_lat, center_long, zoom_start=15)
            tags_highway = {"highway": True}

            app.logger.info("Creating a GeoDataFrame of OSM entities within a N, S, E, W bounding box...")
            gdf = get_geodataframe(borders['north'], borders['south'], borders['east'], borders['west'], tags_highway)

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
            with open('app/static/js/main.js', 'r') as js_file:
                js_script = js_file.read()
            folium_map.render()
            folium_script = folium_map.get_root().script
            folium_script.add_child(Element(f"folium_map = {folium_map.get_name()}"))
            folium_script.add_child(Element(js_script))
            folium_map.save('app/templates/map.html')
            return render_template('index.html', borders=borders)
        else:
            return jsonify(borders=borders)

    folium_map = create_map(0.0, 0.0)
    with open('app/static/js/main.js', 'r') as js_file:
        js_script = js_file.read()
    folium_map.render()
    folium_script = folium_map.get_root().script
    folium_script.add_child(Element(f"folium_map = {folium_map.get_name()}"))
    folium_script.add_child(Element(js_script))
    folium_map.save('app/templates/map.html')
    return render_template('index.html')
