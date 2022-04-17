import numpy as np
from shapely.ops import unary_union
from leafmap import osm_gdf_from_bbox

# FOR DEBUG: pd.options.display.max_colwidth = 300


def create_map(center_lat, center_long, zoom_start=2, create_heatmap=False):
    with open('app/static/js/config_map.js', 'r') as f:
        data = f.readlines()
    data[1] = f"\tcenter: [{center_lat}, {center_long}], zoom: {zoom_start},\n"

    with open('app/static/js/config_map.js', 'w') as f:
        f.writelines(data)


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
