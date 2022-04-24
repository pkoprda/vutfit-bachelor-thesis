import fileinput
from json import load as json_load
from itertools import chain
from numpy import linspace
from pandas import DataFrame
from shapely.ops import unary_union
from osmnx.geometries import geometries_from_bbox
from folium.plugins import HeatMap
from app import app

# FOR DEBUG: pd.options.display.max_colwidth = 300


def create_map(center_lat, center_long, zoom_start=2, clean_map=True):
    new_line = f"\t\tcenter: [{center_lat}, {center_long}], zoom: {zoom_start},\n"
    
    with fileinput.input(files='app/templates/map.html', inplace=True) as f:
        for line in f:
            if line.strip().startswith("center:"):
                line = line.replace(line, new_line)
            print(line, end='')

    if clean_map:
        with open('app/templates/heatlayers.html', 'w') as _: pass


def get_geodataframe(north, south, east, west, tags):
    return geometries_from_bbox(north, south, east, west, tags)['geometry']


def get_coords(gdf):
    coords = []

    if 'way' in gdf.index:
        for geom_obj in gdf.loc[['way']].geometry:
            if geom_obj.geom_type == 'LineString':
                distances = linspace(0, geom_obj.length, 30)
                points = [geom_obj.interpolate(distance) for distance in distances]
                center_points = unary_union(points)
            else:
                center_points = gdf.to_crs(epsg=3857).loc[['way']].geometry.centroid.to_crs(epsg=4326)

            xcoords, ycoords = list(zip(*[(p.x, p.y) for p in center_points]))
            coords.append(list(zip(xcoords, ycoords)))
    elif 'node' in gdf.index:
        coords.append([(x, y) for x,y in zip(gdf.geometry.x , gdf.geometry.y)])

    return coords


def invalid_coords(first_coord, second_coord):
    return first_coord < second_coord


def create_dataframe(gdf, probability):
    try:
        coords = list(chain(*gdf))
    except:
        return DataFrame()

    longs, lats = list(zip(*coords))
    data = {'lats': lats, 'longs': longs, 'weight': probability}
    return DataFrame(data)


def create_heatmap_layer(df):
    gradient = {"0.0": "#00008b", "0.05": "#0000a8", "0.1": "#0000c5", "0.15": "#0000e2", "0.2": "#0000ff", "0.25": "#003fff", "0.3": "#007fff", "0.35": "#00bfff", "0.4": "#00ffff", "0.45": "#3fffbf", "0.5": "#7fff7f", "0.55": "#bfff3f", "0.6": "#ffff00", "0.65": "#ffe900", "0.7": "#ffd200", "0.75": "#ffbc00", "0.8": "#ffa500", "0.85": "#ff7c00", "0.9": "#ff5200", "0.95": "#ff2900"}
    heatmap_data = HeatMap(df, name="HeatMap", min_opacity=0.2, radius=30, blur=50, max_zoom=1).data
    heatmap_layer = f"""L.heatLayer({heatmap_data}, {{'blur': 50, 'gradient': {gradient}, 'maxZoom': 1, 'minOpacity': 0.2, 'radius': 30}}).addTo(folium_map)\n"""
    with open('app/templates/heatlayers.html', 'a') as file_heatlayers:
        file_heatlayers.write(heatmap_layer)


def count_keys(data):
    return sum([count_keys(v) if isinstance(v, dict) else 1 for v in data.values()])


def strip_dict(data):
    new_data = {}
    for k, v in data.items():
        if isinstance(v, dict):
            v = strip_dict(v)
        if v:
            new_data[k] = v
    return new_data


def create_heatlayers(borders):
    with open('app/data/tags.json', 'r') as tags_file:
        tags = json_load(tags_file)

    error_message = ''
    with open('app/templates/heatlayers.html', 'w') as file_heatlayers:
        file_heatlayers.write('<script type="text/javascript">\n')

    # Get all possible probabilities
    probabilities = sorted([*set(chain(*set(tags[key].values() for key in tags.keys()))), ], reverse=True)  
    dict_tags = dict((p, dict((key, []) for key in tags.keys())) for p in probabilities)

    for key in tags.keys():
        for value, p in tags[key].items():
            if p in probabilities:
                dict_tags[p][key].append(value)

    dict_tags = strip_dict(dict_tags)

    for probability, tags in dict_tags.items():
        try:
            gdf = get_geodataframe(borders['north'], borders['south'], borders['east'], borders['west'], tags)
        except:
            error_message = f"Could not get GeoDataFrame for tags with probability '{probability}'"
            app.logger.info(error_message)

        if not gdf.empty:
            df = create_dataframe(get_coords(gdf), probability)
            if not df.empty:
                app.logger.info(f"Creating a Heatlayer for tags with probability '{probability}'")
                create_heatmap_layer(df)
    
    with open('app/templates/heatlayers.html', 'a') as file_heatlayers:
        file_heatlayers.write('</script>\n')
    return error_message
