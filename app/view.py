import pandas as pd
from folium.plugins import HeatMap
from itertools import chain
from flask import render_template, request, jsonify
from app import app
from app.osm_map import create_map, get_geodataframe, get_coords, invalid_coords


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        borders = {
            'north': round(float(request.form['north']), 5),
            'south': round(float(request.form['south']), 5),
            'east': round(float(request.form['east']), 5),
            'west': round(float(request.form['west']), 5)
        }
        center_lat = (borders['north'] + borders['south']) / 2
        center_long = (borders['east'] + borders['west']) / 2

        if invalid_coords(borders['north'], borders['south']):
            create_map(center_lat, center_long, zoom_start=15)
            return render_template('index.html', borders=borders, error_statement="North coordinate must be larger than south coordinate")
        if invalid_coords(borders['east'], borders['west']):
            create_map(center_lat, center_long, zoom_start=15)
            return render_template('index.html', border=borders, error_statement="East coordinate must be larger than west coordinate")

        if 'submit' in request.form:
            tags_highway = {"highway": True}
            try:
                app.logger.info("Creating a GeoDataFrame of OSM entities within a N, S, E, W bounding box...")
                gdf = get_geodataframe(borders['north'], borders['south'], borders['east'], borders['west'], tags_highway)
            except:
                app.logger.info("Could not get GeoDataFrame from that area. Try different values...")
                create_map(center_lat, center_long, zoom_start=15, create_heatmap=False)
                return render_template('index.html', borders=borders, error_statement="Could not create heatmap")

            try:
                app.logger.info("Creating list of coordinates...")
                coords = list(chain(*get_coords(gdf)))
            except KeyError:
                app.logger.info("Could not create list of coordinates. Try different values...")
                create_map(center_lat, center_long, zoom_start=15, create_heatmap=False)
                return render_template('index.html', borders=borders, error_statement="Could not create heatmap")

            app.logger.info("Creating a Map...")
            create_map(center_lat, center_long, zoom_start=15, create_heatmap=True)

            longs, lats = list(zip(*coords))
            data = {"lats": lats, "longs": longs}
            df = pd.DataFrame(data)

            app.logger.info("Creating a HeatMap...")
            heatmap_list = HeatMap(df, name="HeatMap", min_opacity=0.2, radius=30, blur=50, max_zoom=1).data
            heatmap_data = f"""\n\tvar heatmap = L.heatLayer({heatmap_list}, {{'blur': 50, 'maxZoom': 1, 'minOpacity': 0.2, 'radius': 30}}).addTo(folium_map)\n</script>\n"""
            with open('app/templates/heatmap.html', 'a') as js_heatmap:
                js_heatmap.write(heatmap_data)
            return render_template('index.html', borders=borders)
        else:
            return jsonify(borders=borders)

    create_map(0.0, 0.0)
    return render_template('index.html')
