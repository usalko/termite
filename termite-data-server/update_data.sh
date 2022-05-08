#!/bin/bash

export PYTHONPATH=.:web2py
PYTHON=.venv/bin/python3

$PYTHON update_data.py
