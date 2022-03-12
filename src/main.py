import numpy as np
import pandas as pd
import folium
import leafmap.leafmap as leafmap
from folium.plugins import HeatMap
from itertools import chain
from shapely.ops import unary_union
from flask import Flask

# FOR DEBUG: pd.options.display.max_colwidth = 300
north=49.2511
south=49.2382
east=16.5973
west=16.5636

app = Flask(__name__)

def create_map(latituge, longitude):
    return folium.Map([latituge, longitude], zoom_start=17, max_zoom=19)

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

@app.route('/')
def index():
    folium_map = create_map(49.242, 16.567)
    gdf = get_geodataframe(north, south, east, west, tags={"highway": True})
    
    coords = list(chain(*get_coords(gdf)))
    longs, lats = list(zip(*coords))

    data = {"lats": lats, "longs": longs}
    df = pd.DataFrame(data)

    folium_map.add_child(HeatMap(df, name="Heat Map", min_opacity=0.2, radius=30, blur=50, max_zoom=1))
    return folium_map._repr_html_()

if __name__ == '__main__':
    app.run(debug=True)
