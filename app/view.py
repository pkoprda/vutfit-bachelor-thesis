from flask import render_template, request, jsonify
from app import app
from app.osm_map import create_map, invalid_coords, create_heatlayers


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
            app.logger.info("Creating a Map...")
            create_map(center_lat, center_long, zoom_start=15)

            gradient = {"0.0": "#00008b", "0.05": "#0000a8", "0.1": "#0000c5", "0.15": "#0000e2", "0.2": "#0000ff", "0.25": "#003fff", "0.3": "#007fff", "0.35": "#00bfff", "0.4": "#00ffff", "0.45": "#3fffbf", "0.5": "#7fff7f", "0.55": "#bfff3f", "0.6": "#ffff00", "0.65": "#ffe900", "0.7": "#ffd200", "0.75": "#ffbc00", "0.8": "#ffa500", "0.85": "#ff7c00", "0.9": "#ff5200", "0.95": "#ff2900"}
            heatmap_layers, error_message = create_heatlayers(borders, gradient)
            with open('app/static/js/heatmap.js', 'w') as js_heatmap:
                js_heatmap.write(heatmap_layers)

            if not len(error_message):
                return render_template('index.html', borders=borders, error_statement=error_message)

            return render_template('index.html', borders=borders)
        else:
            return jsonify(borders=borders)

    with open('app/static/js/heatmap.js', 'w'): pass    
    create_map(0.0, 0.0)
    return render_template('index.html')
