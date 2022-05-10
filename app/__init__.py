#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Peter Koprda

# Libs
from flask import Flask
from flask.logging import create_logger

app = Flask(__name__, instance_relative_config=True)
log = create_logger(app)

from app import view
