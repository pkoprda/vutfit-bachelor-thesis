#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Peter Koprda

# Generic/Build-in libs
import glob
import fileinput
from json import load as json_load
from itertools import chain
from itertools import repeat

# Other libs
from numpy import linspace
from pandas import pandas as pd
from pyproj import pyproj
from shapely.ops import unary_union
from shapely.ops import transform
from shapely.geometry import MultiPoint
from geopandas import geopandas as gpd

# Own module
from app import log


def create_map(center_lat=0.0, center_long=0.0, zoom_start=2, clean_map=True):
    """Generates a map of given coords of center point
    and initial zoom level for the map

    Parameters
    -------------
    center_lat : float, optional
        Latitude value of the center point. Defaults to 0.0.

    center_long : float, optional
        Longitude value of the center point. Defaults to 0.0.

    zoom_start : int, optional
        Initial map zoom level. Defaults to 2.

    clean_map : bool, optional
        Whether to create file for heat layer. Defaults to True.

    """

    new_line = f"\t\tcenter: [{center_lat}, {center_long}], zoom: {zoom_start},\n"

    with fileinput.input(files='app/templates/map.html', inplace=True) as map_file:
        for line in map_file:
            if line.strip().startswith("center:"):
                line = line.replace(line, new_line)
            print(line, end='')

    if clean_map:
        with open('app/templates/heatlayers.html', mode='w', encoding='utf-8'):
            ...


def preprocess_tags(row: gpd.GeoSeries, tags: dict) -> float:
    """Finds probability for given geographic object

    Parameters
    -------------
    row : gpd.GeoSeries
        One row in GeoDataFrame

    tags : dict
        Dictionary of given probabilites from json file

    Returns
    -------------
        float: Probability value
    """

    if row['fclass'] == 'building':
        probability = None
        if row['type'] in tags['building']:
            probability = tags['building'][row['type']]
    else:
        probability = recursive_lookup(row['fclass'], tags)
    return probability


def get_coords(gdf: gpd.GeoDataFrame, tags: dict) -> list:
    """Creates two dimensional list of points with probability values

    Parameters
    -------------
    gdf : gpd.GeoDataFrame
        GeoDataFrame of geographic objects from map for given area

    tags : dict
        Dictionary of given probabilites from json file

    Returns
    -------------
        list: List of points
    """

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
                if not center_points.is_empty:
                    if center_points.geom_type == 'Point':
                        center_points = MultiPoint([center_points])
                    xcoords, ycoords = list(zip(*[(p.x, p.y) for p in center_points]))
                    coords.append(list(zip(xcoords, ycoords, repeat(probability))))
            elif geom_obj.geom_type == 'Point':
                coords.append([(row.geometry.x, row.geometry.y, probability)])
            else:
                center_points = gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
                xcoords, ycoords = list(zip(*[(p.x, p.y) for p in center_points]))
                coords.append(list(zip(xcoords, ycoords, repeat(probability))))

    return coords


def invalid_coords(first_coord: float, second_coord: float) -> bool:
    """Check values of latitude or longitude coordinates

    Parameters
    -------------
    first_coord : float
        South or west coordinate

    second_coord : float
        North or east coordinate

    Returns
    -------------
        bool: False if second coordinate is bigger than first,
        True otherwise
    """

    return first_coord < second_coord


def create_dataframe(coords: list) -> pd.DataFrame:
    """Creates Dataframe from list with three columns -
    latitude, longitude and probability values

    Parameters
    -------------
    coords : list
        Two dimensional list of coordinates with probabilities

    Returns
    -------------
        pd.DataFrame: DataFrame with latitude, longitude and probability columns
    """

    try:
        flatten_coords = list(chain(*coords))
    except:
        return pd.DataFrame()

    if not flatten_coords:
        return pd.DataFrame()

    longs, lats, prob = list(zip(*flatten_coords))
    data = {'lats': lats, 'longs': longs, 'weight': prob}
    return pd.DataFrame(data)


def create_heat_layer():
    """Creates empty js file for appending heat points
    """

    with open('app/templates/heatlayers.html', mode='w', encoding='utf-8') as file_heatlayers:
        file_heatlayers.write('<script type="text/javascript">\nL.heatLayer([')


def append_heat_layer(df_heatpoints: pd.DataFrame):
    """Append heat points into created js file

    Parameters
    -------------
    df_heatpoints : pd.DataFrame
        DataFrame with latitudes, longitudes and probability values
    """

    heatmap_layer = f"{str(df_heatpoints.to_numpy().tolist())[1:-1]}, "
    with open('app/templates/heatlayers.html', mode='a', encoding='utf-8') as file_heatlayers:
        file_heatlayers.write(heatmap_layer)


def add_options():
    """Add options about heat layer into created js file
    """

    gradient = {"0.0": "#00008b", "0.05": "#0000a8", "0.1": "#0000c5", "0.15": "#0000e2", "0.2": "#0000ff", "0.25": "#003fff", "0.3": "#007fff", "0.35": "#00bfff", "0.4": "#00ffff", "0.45": "#3fffbf", "0.5": "#7fff7f", "0.55": "#bfff3f", "0.6": "#ffff00", "0.65": "#ffe900", "0.7": "#ffd200", "0.75": "#ffbc00", "0.8": "#ffa500", "0.85": "#ff7c00", "0.9": "#ff5200", "0.95": "#ff2900"}
    options = f"], {{'blur': 50, 'gradient': {gradient}, 'maxZoom': 1, 'minOpacity': 0.2, 'radius': 30}}).addTo(folium_map)\n</script>\n"
    with open('app/templates/heatlayers.html', mode='a', encoding='utf-8') as file_heatlayers:
        file_heatlayers.write(options)


def recursive_lookup(key: str, dict_tags: dict):
    """Finds probability of key in nested dictionary

    Parameters
    -------------
    key : str
        Key for searching in dictionary
    dict_tags : dict
        Nested dictionary of keys with probabilities

    Returns
    -------------
        float: Probability value for searched key
    """

    if key in dict_tags:
        return dict_tags[key]
    for value in dict_tags.values():
        if isinstance(value, dict):
            searched_value = recursive_lookup(key, value)
            if searched_value is not None:
                return searched_value
    return None


def create_heatlayer(borders: dict):
    """Creates dictionary from json file with probabilities
    and processes shapefiles into geodataframes

    Parameters
    -------------
    borders:
        Dictionary of border values
    """

    with open('app/data/tags.json', mode='r', encoding='utf-8') as tags_file:
        tags = json_load(tags_file)

    create_heat_layer()

    for shp_f in glob.glob('app/data/static/*.shp'):
        log.info("Processing file %s", shp_f)
        gdf = gpd.read_file(shp_f, bbox=(borders['east'], borders['south'], borders['west'], borders['north']))

        if not gdf.empty:
            df_heatpoints = create_dataframe(get_coords(gdf, tags))
            if not df_heatpoints.empty:
                append_heat_layer(df_heatpoints)

    add_options()
