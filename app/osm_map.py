from itertools import chain
import numpy as np
from shapely.ops import unary_union
from leafmap import osm_gdf_from_bbox

# FOR DEBUG: pd.options.display.max_colwidth = 300


def create_map(center_lat, center_long, zoom_start=2, create_heatmap=False):
    config_map = f"""\tvar folium_map = L.map("folium_map", {{
    \tcenter: [{center_lat}, {center_long}],
    \tcrs: L.CRS.EPSG3857,
    \tzoom: {zoom_start},
    \tzoomControl: true,
    \tpreferCanvas: false}});
    L.control.scale().addTo(folium_map);\n"""
    with open('app/templates/map.html', 'r') as shandle:
        with open('app/templates/heatmap.html', 'w') as thandle:
            lines = shandle.readlines()[:-1] if create_heatmap else shandle.readlines()
            lines = list(chain(lines[:30], config_map, lines[38:]))
            for line in lines:
                thandle.write(line)


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


def invalid_coords(first_coord, second_coord):
    return first_coord < second_coord
