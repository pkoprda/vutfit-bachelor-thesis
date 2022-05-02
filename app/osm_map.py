import glob
import fileinput
from json import load as json_load
from itertools import chain, repeat
from numpy import linspace
from pandas import pandas as pd
import pyproj
from shapely.ops import unary_union, transform
from shapely.geometry import MultiPoint
from geopandas import read_file as gpd_read_file
from app import app


def create_map(center_lat, center_long, zoom_start=2, clean_map=True):
    new_line = f"\t\tcenter: [{center_lat}, {center_long}], zoom: {zoom_start},\n"

    with fileinput.input(files='app/templates/map.html', inplace=True) as map_file:
        for line in map_file:
            if line.strip().startswith("center:"):
                line = line.replace(line, new_line)
            print(line, end='')

    if clean_map:
        with open('app/templates/heatlayers.html', 'w') as _: pass


def preprocess_tags(row, tags):
    if row['fclass'] == 'building' and row['type'] in tags['building']:
        probability = tags['building'][row['type']]
    else:
        probability = recursive_lookup(row['fclass'], tags)
    return probability


def get_coords(gdf, tags):
    coords = []
    source_proj = pyproj.CRS('EPSG:4326')
    dst_proj = pyproj.CRS('EPSG:3857')
    project = pyproj.Transformer.from_crs(source_proj, dst_proj, always_xy=True).transform

    for _, row in gdf.iterrows():
        probability = preprocess_tags(row, tags)
        if probability:
            geom_obj = row['geometry']
            if geom_obj.geom_type == 'LineString':
                line_transformed = transform(project, geom_obj)
                num_vert = int(round(line_transformed.length / 20))
                distances = linspace(0, geom_obj.length, num_vert)
                points = [geom_obj.interpolate(distance) for distance in distances]
                center_points = unary_union(points)
                if center_points.is_empty: continue
                if center_points.geom_type == 'Point':
                    center_points = MultiPoint([center_points])
                xcoords, ycoords = list(zip(*[(p.x, p.y) for p in center_points]))
                coords.append(list(zip(xcoords, ycoords, repeat(probability))))
            elif geom_obj.geom_type == 'Point':
                coords.append([(x, y, probability) for x,y in zip(gdf.geometry.x , gdf.geometry.y)])
            else:
                center_points = gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
                xcoords, ycoords = list(zip(*[(p.x, p.y) for p in center_points]))
                coords.append(list(zip(xcoords, ycoords, repeat(probability))))

    return coords


def invalid_coords(first_coord, second_coord):
    return first_coord < second_coord


def create_dataframe(gdf):
    try:
        coords = list(chain(*gdf))
    except:
        return pd.DataFrame()

    if not coords: return pd.DataFrame()

    longs, lats, prob = list(zip(*coords))
    data = {'lats': lats, 'longs': longs, 'weight': prob}
    return pd.DataFrame(data)


def create_heat_layer():
    with open('app/templates/heatlayers.html', 'w') as file_heatlayers:
        file_heatlayers.write('<script type="text/javascript">\nL.heatLayer([')


def append_heat_layer(df):
    heatmap_layer = f"{str(df.to_numpy().tolist())[1:-1]}, "
    with open('app/templates/heatlayers.html', 'a') as file_heatlayers:
        file_heatlayers.write(heatmap_layer)


def added_options():
    gradient = {"0.0": "#00008b", "0.05": "#0000a8", "0.1": "#0000c5", "0.15": "#0000e2", "0.2": "#0000ff", "0.25": "#003fff", "0.3": "#007fff", "0.35": "#00bfff", "0.4": "#00ffff", "0.45": "#3fffbf", "0.5": "#7fff7f", "0.55": "#bfff3f", "0.6": "#ffff00", "0.65": "#ffe900", "0.7": "#ffd200", "0.75": "#ffbc00", "0.8": "#ffa500", "0.85": "#ff7c00", "0.9": "#ff5200", "0.95": "#ff2900"}
    options = f"], {{'blur': 50, 'gradient': {gradient}, 'maxZoom': 1, 'minOpacity': 0.2, 'radius': 30}}).addTo(folium_map)\n</script>\n"
    with open('app/templates/heatlayers.html', 'a') as file_heatlayers:
        file_heatlayers.write(options)


def recursive_lookup(k, d):
    if k in d: return d[k]
    for v in d.values():
        if isinstance(v, dict):
            a = recursive_lookup(k, v)
            if a is not None: return a
    return None


def create_heatlayers(borders):
    with open('app/data/tags.json', 'r') as tags_file:
        tags = json_load(tags_file)

    create_heat_layer()

    for shp_f in glob.glob('app/data/static/*.shp'):
        app.logger.info(f"Processing file {shp_f}")
        gdf = gpd_read_file(shp_f, bbox=(borders['east'], borders['south'], borders['west'], borders['north']))

        if not gdf.empty:
            df = create_dataframe(get_coords(gdf, tags))
            if not df.empty:
                append_heat_layer(df)
    
    added_options()
