#!/usr/bin/python3

import subprocess
import os
import subprocess
from flask import Flask
import getData
import logging


app = Flask(__name__)

db_user = os.environ["DB_USER"]
db_port = os.environ["DB_PORT"]
db_pass = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]
db_host = os.environ["DB_HOST"]


@app.route("/", methods=['GET',])
def index():
    loadTours()
    return "DONE"

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500



#Load Tours' data in the postgis database
def loadTours():
        process = subprocess.run(["ogr2ogr","-f","GeoJSON", "/places-finder/tours.geojson", "/places-finder/tours.osm.pbf", "multipolygons" ])
        processDB = subprocess.run(["ogr2ogr","-f","PostgreSQL", "PG:dbname="+db_name +" host="+db_host +" port=" +db_port+ " user="+db_user +" password="+db_pass, "/places-finder/tours.geojson", "-nln", "tours" , "-overwrite", "-append", "-update", "-nlt", "MULTIPOLYGON"], capture_output=True)



if __name__ == "__main__":
        port = int(os.environ.get("PORT",8080))
        app.run(debug=True,host='0.0.0.0',port=port)


