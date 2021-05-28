#!/usr/bin/python3

import subprocess
import os


db_user = os.environ["DB_USER"]
db_port = os.environ["DB_Port"]
db_pass = os.environ["PASS_DB"]
db_name = os.environ["DB_NAME"]
db_host = os.environ["DB_HOST"]
db = os.environ("DB")

#Load Tours' data in the postgis database
def main():
        process = subprocess.run(["ogr2ogr","-f","GeoJSON", "/places-finder/tours.geojson", "/places-finder/tours.osm.pbf", "multipolygons" ])
        processDB = subprocess.run(["ogr2ogr","-f","PostgreSQL", "PG:dbname="+db_name +"host="+db_host +"port=" +db_port+ "user="+db_user +"password="+db_pass,downloadDest + linksPart[i][len(endDir):-7] + "geojson", "-nln", "auvergne" , "-overwrite", "-append", "-update", "-nlt", "MULTIPOLYGON"], capture_output=True)


