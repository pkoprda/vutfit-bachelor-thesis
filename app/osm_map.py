from json import load as json_load
from itertools import chain
from numpy import linspace
from pandas import DataFrame
from shapely.ops import unary_union
from osmnx.geometries import geometries_from_bbox
from folium.plugins import HeatMap
from app import app

# FOR DEBUG: pd.options.display.max_colwidth = 300


def create_map(center_lat, center_long, zoom_start=2):
    with open('app/static/js/config_map.js', 'r') as f:
        data = f.readlines()
    data[1] = f"\tcenter: [{center_lat}, {center_long}], zoom: {zoom_start},\n"

    with open('app/static/js/config_map.js', 'w') as f:
        f.writelines(data)


def get_geodataframe(north, south, east, west, tags):
    return geometries_from_bbox(north, south, east, west, tags)['geometry']


def get_coords(gdf):
    coords = []

    # Polygon
    if 'way' in gdf.index and gdf.loc[['way']].geometry.geom_type[0] == 'Polygon':
        center_points = gdf.loc[['way']].geometry.centroid
        xcoords, ycoords = list(zip(*[(p.x, p.y) for p in center_points]))
        coords.append(list(zip(xcoords, ycoords)))
        return coords

    # LineString
    if 'way' in gdf.index:
        for geom_obj in gdf.loc[['way']].geometry:
            distances = linspace(0, geom_obj.length, 30)
            points = [geom_obj.interpolate(distance) for distance in distances]
            multipoint = unary_union(points)
            xcoords, ycoords = list(zip(*[(p.x, p.y) for p in multipoint]))
            coords.append(list(zip(xcoords, ycoords)))
        return coords

    # Point
    coords = [[(x, y) for x,y in zip(gdf.geometry.x , gdf.geometry.y)]]
    return coords


def invalid_coords(first_coord, second_coord):
    return first_coord < second_coord


def create_dataframe(gdf, error_message, key, value='all', probability=1.0):
    try:
        coords = list(chain(*gdf))
    except:
        error_message += f"{key}: {value}"
        return DataFrame(), error_message

    longs, lats = list(zip(*coords))
    data = {'lats': lats, 'longs': longs, 'weight': probability}
    return DataFrame(data), error_message


def update_list_layers(df, heatmap_layers, gradient):
    heatmap_data = HeatMap(df, name="HeatMap", min_opacity=0.2, radius=30, blur=50, max_zoom=1).data
    heatmap_layers += f"""L.heatLayer({heatmap_data}, {{'blur': 50, 'gradient': {gradient}, 'maxZoom': 1, 'minOpacity': 0.2, 'radius': 30}}).addTo(folium_map)\n"""
    return heatmap_layers


def count_keys(data):
    return sum([count_keys(v) if isinstance(v, dict) else 1 for v in data.values()])


def create_heatlayers(borders, gradient):
    with open('app/data/tags.json', 'r') as tags_file:
        tags = json_load(tags_file)

    error_message = ''
    heatmap_layers = 'var heatmap = true;\n'
    counter = 0
    all = count_keys(tags)

    for key in tags.keys():
        # Exclude tags that are not in box
        try:
            if isinstance(tags[key], bool):
                app.logger.info(f"{counter}/{all}: Creating a GeoDataFrame for '{key}'")
            gdf = get_geodataframe(borders['north'], borders['south'], borders['east'], borders['west'], {key: True})
        except:
            pass

        if gdf.empty:
            counter += 1 if isinstance(tags[key], bool) else len(tags[key].keys())
            app.logger.info(f"{counter}/{all}: No tag with key '{key}' found in this area")
            continue

        if isinstance(tags[key], bool):
            gdf = get_coords(gdf)
            df, error_message = create_dataframe(gdf, error_message, key)
            if not df.empty:
                app.logger.info(f"{counter}/{all}: Creating a Heatlayer for '{key}'")
                heatmap_layers = update_list_layers(df, heatmap_layers, gradient)

        else:
            for value, probability in tags[key].items():
                tag = {key: value}
                counter += 1
                try:
                    app.logger.info(f"{counter}/{all}: Creating a GeoDataFrame for '{key}={value}'")
                    gdf = get_geodataframe(borders['north'], borders['south'], borders['east'], borders['west'], tag)
                except:
                    app.logger.info(f"{counter}/{all}: Could not get GeoDataFrame for tag '{key}={value}'")
                    error_message += f"{key}: {value}"
                    continue

                if gdf.empty:
                    app.logger.info(f"{counter}/{all}: No tag with value '{key}={value}' found in this area")
                    continue
                gdf = get_coords(gdf)

                df, error_message = create_dataframe(gdf, error_message, key, value, probability)
                if not df.empty:
                    app.logger.info(f"{counter}/{all}: Creating a Heatlayer for '{key}={value}'")
                    heatmap_layers = update_list_layers(df, heatmap_layers, gradient)
                    

    return heatmap_layers, error_message
