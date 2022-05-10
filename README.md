# Bachelor thesis
## Estimation of the Probability of Occurrence of Persons in an Area
---

**Author:** Peter Koprda <xkoprd00@stud.fit.vutbr.cz>

**Supervisor:** Ing. Vojtěch Mrázek, Ph.D. (UPSY FIT VUT) <mrazek@fit.vut.cz>

# Requirements

* Python 3
* `pip` package installer
* `wget` command


# Setup
## Create virtual environment

Install virtual environment using `pip`:
```sh
pip install virtualenv
```

Create the new virtual environment for the project:

```sh
python3 -m venv flask-env
```

Activate virtual environment:

```sh
source flask-env/bin/activate
```

## Install libraries
Install dependency libraries:

```sh
pip install -r requirements.txt
```

Export environment variables with commands:

```sh
export FLASK_APP=run.py
export FLASK_ENV=development
```

## Download data
Download OpenStreetMap data extracts from the Geofabrik's free download server:

```sh
wget -P app/data/static/ https://download.geofabrik.de/europe/czech-republic-latest-free.shp.zip
```

Unzip archive:

```sh
unzip app/data/static/czech-republic-latest-free.shp.zip -d app/data/static/
```

## Run the app
Now just run app with command:
```sh
flask run
```
and you are good to go! The page should render at http://127.0.0.1:5000.
