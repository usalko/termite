#!/usr/bin/env .venv/bin/python3
import os
import gluon.utils.uploads as uploads

def index():
    corpora = [fname[:-len(".csv")] for fname in os.listdir(uploads.spreadsheet_dir(request))]
    return {"corpora": corpora}
