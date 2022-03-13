from urllib import request
import pandas as pd
import numpy as np
import leafmap
import folium
from shapely.ops import unary_union
from folium.plugins import HeatMap
from itertools import chain
from flask import Flask, render_template, request, redirect

# FOR DEBUG: pd.options.display.max_colwidth = 300

app = Flask(__name__, instance_relative_config=True)

def create_map(latituge, longitude):
    return folium.Map([latituge, longitude], zoom_start=17, max_zoom=19, width='75%', height='75%')

def get_geodataframe(north, south, east, west, tags):
    return leafmap.osm_gdf_from_bbox(north, south, east, west, tags)['geometry']

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


@app.route('/', methods=['GET', 'POST'])
def index():
    north=49.2511
    south=49.2382
    east=16.5973
    west=16.5636
    if request.method == 'POST':
        north = request.form['north']
        south = request.form['south']
        east = request.form['east']
        west = request.form['west']
        return redirect('/')
    else:
        folium_map = create_map(49.242, 16.567)
        gdf = get_geodataframe(north, south, east, west, tags={"highway": True})
        
        coords = list(chain(*get_coords(gdf)))
        longs, lats = list(zip(*coords))

        data = {"lats": lats, "longs": longs}
        df = pd.DataFrame(data)

        folium_map.add_child(HeatMap(df, name="Heat Map", min_opacity=0.2, radius=30, blur=50, max_zoom=1))
        folium_map.save('app/templates/map.html')
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
