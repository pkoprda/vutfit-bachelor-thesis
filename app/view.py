from flask import redirect
from flask import render_template
from flask import request
from flask import jsonify

from app import app
from app import log
from app.osm_map import create_map
from app.osm_map import invalid_coords
from app.osm_map import create_heatlayers


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
            log.info("Creating a Map...")
            create_map(center_lat, center_long, zoom_start=15, clean_map=False)
            create_heatlayers(borders)
            return render_template('index.html', borders=borders)

        return jsonify(borders=borders)

    create_map()
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')
