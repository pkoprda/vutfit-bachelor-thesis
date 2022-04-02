import numpy as np
from shapely.ops import unary_union
from folium import Map as FoliumMap
from folium.plugins import MousePosition, Draw
from leafmap import osm_gdf_from_bbox

# FOR DEBUG: pd.options.display.max_colwidth = 300


def create_map(latituge, longitude, zoom_start=2):
    m = FoliumMap(
        [latituge, longitude], zoom_start=zoom_start, min_zoom=2,
        max_zoom=19, width='75%', height='75%', control_scale=True)
    # FIXME: Edit option 'allowIntersection' does not work
    Draw(draw_options={
        'polyline': False, 'polygon': False, 'circle': False,
        'marker': False, 'circlemarker': False},
        edit_options={"rectangle": {"allowIntersection": False}}).add_to(m) 
    formatter = "function(num) {return L.Util.formatNum(num, 4) + ' º ';};"
    MousePosition(
        position='topright', separator=' | ', empty_string='',
        lng_first=True, num_digits=20, prefix='Coordinates:',
        lat_formatter=formatter, lng_formatter=formatter).add_to(m)
    return m


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
    return first_coord > second_coord
