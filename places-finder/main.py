#!/usr/bin/python3

import requests
import sys
import json
import math
import uuid
import subprocess
import geopandas
from shapely.geometry import Polygon, Point, mapping
from shapely.geometry.base import geometry_type_name
import fiona
import pandas
import random
import os.path
import os
import glob
from shapely.geometry.multipolygon import MultiPolygon
from shapely.ops import unary_union
import numpy
import wget
from datetime import datetime
from sqlalchemy import Table, MetaData, Column, Integer, String, TIMESTAMP, create_engine, BigInteger, dialects, inspect
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2 import WKTElement, Geometry

from flask import Flask
import logging



def deg2num(lon_deg, lat_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lon_deg, lat_deg)


def splitter(
        input_pbf,
        gdf,
        region_name,
        zoom=1,
        max_zoom = 18,
        bbox={"xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1},
    ):
    extracts = []
    my_finders = []
    indoor_path = "data/" + region_name + "/indoor/"
    for x in [bbox["xmin"], bbox["xmax"]]:
        for y in [bbox["ymin"], bbox["ymax"]]:
            (lon0, lat0) = num2deg(x, y, zoom)
            (lon1, lat1) = num2deg(x+1, y+1, zoom)
            filename = indoor_path + "split/" + \
                str(zoom) + "_" \
                + str(x) + "_" + str(y) + "_" + str(x + 1) + "_" + str(y + 1) \
                + ".osm.pbf"
            print("setting file: " + filename)
            extracts.append({
                "output": filename,
                "output_format": "pbf",
                "bbox": [lon0, lat0, lon1, lat1]
            })
            my_finders.append({
                "zoom": zoom + 1,
                "input_pbf": filename,
                "bbox": { "xmin": x * 2, "ymin": y * 2, "xmax": (2*x) + 1, "ymax": (2*y) + 1 }
            })
    conf = indoor_path + region_name + '_config.json'
    print("conf:" + conf)
    # print(json.dumps(extracts, sort_keys=True, indent=4))
    with open(conf, 'w') as outfile:
        json.dump({"extracts": extracts}, outfile)
        outfile.flush()
    cmd = "osmium extract " \
        + "--strategy=smart " \
        + "--overwrite " \
        + "--progress " \
        + "--config=" + conf + " " \
        + input_pbf
    # os.remove(input_pbf)

    print("cmd: " + cmd)
    indoor_filter = subprocess.run(cmd,shell=True)
    # indoor_filter.communicate()


    for my_finder in my_finders:
        size = os.path.getsize(my_finder["input_pbf"])
        if size > 100000 and zoom < max_zoom:
            gdf = splitter(
                input_pbf=my_finder["input_pbf"],
                gdf=gdf,
                zoom=my_finder["zoom"],
                max_zoom=max_zoom,
                region_name=region_name,
                bbox=my_finder["bbox"]
            )
            os.remove(my_finder["input_pbf"])
        elif size < 100:
            os.remove(my_finder["input_pbf"])
            #print("removed because size too small")
        else:
            print("Working with file : ",my_finder["input_pbf"])
            gdf = gdf.append(finder(file_name=my_finder["input_pbf"],region_name=region_name))
            #os.remove(my_finder["input_pbf"])
    return gdf

def pbf_extractor(region):
    """
    Generation des fichiers pbf

    Entree :

    region : tableau correspondant a la region
    """
    region_name=region["name"]
    region_poly=region["poly"]
    region_pbf=region["pbf"]
    os.makedirs("data/"+ region_name + "/indoor/split", exist_ok=True) #Creation des répertoires
    os.makedirs("data/"+ region_name + "/geofabrik_files", exist_ok=True)

    indoor_path = "data/" + region_name + "/indoor/"
    geofabrik_path = "data/" + region_name + "/geofabrik_files/"

    poly_file = geofabrik_path + region_name + ".poly"
    old_pbf_file = geofabrik_path + region_name + ".osm.pbf"
    if not os.path.isfile(poly_file):
        """Telechargement du fichier poly s'il n'est pas dans le path"""
        print("download: " + poly_file)
        wget.download(region_poly, poly_file)
    if not os.path.isfile(old_pbf_file):
        """Telechargement du fichier pbf s'il n'est pas dans le path"""
        print("download: " + region_pbf)
        wget.download(region_pbf, old_pbf_file)

    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S") #String de la date et heure
    new_pbf_file = indoor_path + region_name + "_" + dt_string + ".osm.pbf"

    # cmd = [
    #     "osmupdate",
    #      old_pbf_file,
    #      new_pbf_file,
    #      "-B=" + poly_file
    #  ] #Mise a jour du fichier pbf. -B= pour ne garder que la region voulue
    # print(cmd)
    # building_indoor_filter = subprocess.run(cmd)


    #____________MODE DEBUG_______________
    new_pbf_file=old_pbf_file

    building_indoor_pbf = indoor_path + "building_indoor.osm.pbf" #Chemin du fichier pbf
    cmd = \
        "osmium "+ \
        "tags-filter "+\
        "--progress "+\
        "--overwrite "+\
        "--output-format=pbf " +\
        "--output=" + building_indoor_pbf + " " +\
        new_pbf_file + " " +\
        "w/indoor w/building:levels wa/building"
    #Filtrage du fichier pbf pour ne garder que les batiments voulus.
    print(cmd)
    building_indoor_filter = subprocess.run(cmd, shell=True)


    #Decoupage du fichier en 4

    mygdf = splitter(
        input_pbf=building_indoor_pbf,
        gdf=geopandas.GeoDataFrame(),
        zoom=1,
        max_zoom=18,
        region_name=region_name,
        bbox={
            "xmin": 0, "ymin": 0,
            "xmax": 1, "ymax": 1,
        }
    )
    return mygdf

def finder(
    file_name,
    region_name
):
    """
    Entrees :
    file_name : fichier à traiter
    """
    print("Appel finder")
    indoor_path = "data/" + region_name + "/indoor/"
    #
    with subprocess.Popen(
        "osmium export "
        + file_name + " "
        + "--output-format=geojson "
        + "--add-unique-id=type_id ",
        shell=True,
        stdout=subprocess.PIPE
    ) as proc_export:#export en geojson
        gdf = geopandas.read_file(proc_export.stdout) #lecture du fichier geojson en geodataframe

    if 'indoor' not in gdf:
        #print("No indoor data detected")
        return None

    gdf.rename(columns={"id":"openindoor_id"},inplace=True)
    
    tab = numpy.empty([gdf.shape[0],1],dtype=object)
    tab[:,0] = [
        Polygon(mapping(shap)['coordinates']) #Corriger les mauvais LineString
            if shap.geom_type=='LineString' and shap.coords[0] == shap.coords[-1] else
                Polygon(mapping(shap)['coordinates'][0][0]) if shap.geom_type=='MultiPolygon' and len(shap)==1 else #Transformer les MultiPolygons n'ayant qu'un seul Polygon en Polygon
                    MultiPolygon(Polygon(coord[0]) for coord in mapping(shap)['coordinates'])
                        if (
                            shap.geom_type=='MultiLineString'
                            or shap.geom_type=='MultiPolygon'
                        ) else shap
            for shap in gdf.geometry
    ]
    gdf.loc[:, 'geometry'] = tab
    #print("Correction LineStrings to Polygons done")

    gdf_indoor = gdf[gdf['indoor'].notnull()] #Ne garder que les donnees ayant des donnees indoor
    gdf_indoor = gdf_indoor[gdf_indoor['indoor']!='no']
    gdf_indoor = gdf_indoor.drop_duplicates(subset=["geometry"])

    if gdf_indoor.empty:
        print("No indoor data detected")
        return None
    print("Indoor data filtered")

    gdf_building = gdf[gdf["building"].notnull()]
    gdf_building = gdf_building[gdf_building["building"]!='no']
    
    get_polygon_indoor_building = lambda shap : shap.geom_type in ['Polygon','MultiPolygon'] and gdf_indoor.intersects(shap).any()

    gdf_building_indoor = gdf_building[gdf_building["geometry"].apply(get_polygon_indoor_building)].drop_duplicates()




    get_polygon_indoor_building_footprint = lambda shap : not(gdf_building_indoor[gdf_building_indoor.geometry.apply(lambda shap2 : not(shap2.equals(shap)))].contains(shap).any())
    gdf_building_indoor = gdf_building_indoor[gdf_building_indoor.geometry.apply(get_polygon_indoor_building_footprint)]
    gdf_building_indoor.dropna(axis=1,how="all",inplace=True)

    if gdf_building_indoor.empty :
        return None

    get_duplicates = lambda shap : shap.equals

    index_list = []
    for shap in gdf_building_indoor.geometry:
        copies = gdf_building_indoor[gdf_building_indoor.geometry.apply(get_duplicates(shap))].geometry
        if copies.index[0] not in index_list:
            index_list.append(copies.index[0])

    gdf_building_indoor = gdf_building_indoor.loc[index_list]

    gdf_building_indoor["openindoor_centroid"] = gdf_building_indoor.centroid

    return gdf_building_indoor


def upsert(table, conn, keys, data_iter):
    """
    Execute SQL statement inserting data

    Parameters
    ----------
    table : pandas.io.sql.SQLTable
    conn : sqlalchemy.engine.Engine or sqlalchemy.engine.Connection
    keys : list of str
        Column names
    data_iter : Iterable that iterates the values to be inserted
    unique_id : primary key
    """
    # print("table:" + table.table.name)

    # Add contraint if missing

    unique_id="openindoor_id"

    #    ALTER TABLE {1} DROP CONSTRAINT IF EXISTS constraint_{2};   # CAN'T DROP THE KEY BECAUSE OF REFERENCES, DROP FIRST THE KEY FROM building_item
    #    ALTER TABLE {1} ADD CONSTRAINT constraint_{2} PRIMARY KEY({2});

    conn.execute('''
        ALTER TABLE {1} ALTER COLUMN {2} SET NOT NULL;
        ALTER TABLE {1} ALTER COLUMN geometry TYPE geometry;
        ALTER TABLE {1} ALTER COLUMN openindoor_centroid TYPE geometry;
    '''.replace('{1}', table.table.name).replace('{2}', unique_id))

    insert_stmt=insert(table.table)
    # Prepare upsert statement
    my_dict={}
    for key in keys:
        my_dict[key]=insert_stmt.excluded[key]
        # Create column if missing
        conn.execute('''
            ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} {};
        '''.format(
            table.table.name,
            '"' + key + '"',
            insert_stmt.excluded[key].type)
        )
    upsert_stmt=insert_stmt.on_conflict_do_update(
        index_elements = [unique_id],
        set_ = my_dict
    )
    data=[dict(zip(keys, row)) for row in data_iter]
    conn.execute(upsert_stmt, data)

def gdf_to_db(gdf, system, user, password, server, port, db_name, db_table_name):
    
    #ssl_args = {'sslrootcert':'server-ca.pem', 'sslcert':'client-cert.pem', 'sslkey':'client-key.pem'}
    ssl_args = {'sslrootcert': 'server-ca(2).pem', 'sslcert':'client_cert.pem', 'sslkey':'client_key.pem'}
    engine=create_engine(system + "://" + user + ":" + password +"@" + server + ":" + str(port) + "/" + db_name, connect_args=ssl_args)

    # pool = create_engine(
    #     engine.url.URL.create(
    #         drivername=system,
    #         username=user,
    #         password=password,
    #         host=server,
    #         port=port,
    #         database=db_name,
    #     ),**db_config      
    # )

    gdf['geometry']=gdf.geometry.apply(lambda geom: WKTElement(geom.wkt, srid=4326))
    gdf['openindoor_centroid']=gdf['openindoor_centroid'].apply(lambda geom: WKTElement(geom.wkt, srid=4326))
    gdf.rename(columns={"id":"openindoor_id"},inplace=True)


    gdf.to_sql(
        name = db_table_name,
        con = engine,
        if_exists = 'append',
        index = False,
        dtype = {'geometry': Geometry(geometry_type='POLYGON', srid=4326),'openindoor_centroid': Geometry(geometry_type='POINT', srid=4326)},
        method = upsert
)


def main():

    # db_user = os.environ["DB_USER"]
    # db_port = os.environ["DB_PORT"]
    # db_pass = os.environ["DB_PASS"]
    # db_name = os.environ["DB_NAME"]
    # db_host = os.environ["DB_HOST"]

    db_user = os.environ["POSTGRES_USER"]
    db_port = 5432
    db_pass = os.environ["POSTGRES_PASSWORD"]
    db_name = os.environ["POSTGRES_DB"]
    db_host = os.environ["POSTGRES_HOST"]

    mygdf = geopandas.GeoDataFrame()
    with open('regions.json') as regions:
        region_data = json.load(regions)
    for region in region_data['regions']:
        mygdf = mygdf.append(pbf_extractor(region))
    
    with open("keep.json") as keep:
        keep_data = json.load(keep)

    serie = mygdf.isnull().sum().apply(lambda n : n/mygdf.shape[0]*100<95)
    keep_list = serie.loc[serie].index
    keep_list = keep_list.union(keep_data["footprint_key"])
    mygdf.drop(axis=1,columns=(mygdf.columns.difference(keep_list)),inplace=True)


    gdf_to_db(gdf=mygdf,
        system="postgresql",
        user=db_user,
        password=db_pass,
        server=db_host,
        port=db_port,
        db_name=db_name,
        db_table_name="building_footprint")


if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    main()