from flask import Flask
from flask.logging import create_logger

app = Flask(__name__, instance_relative_config=True)
log = create_logger(app)

from app import view
