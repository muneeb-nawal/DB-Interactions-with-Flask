import logging as lg
import os

import mysql.connector as connection
from flask import Flask, request, jsonify
import csv

import pymongo
import json
import pandas as pd

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

app = Flask(__name__)

logger = lg.getLogger(__name__) #new logger
logger.setLevel(lg.ERROR)
logger.setLevel(lg.INFO)

formatter = lg.Formatter(' %(name)s : %(asctime)s : %(levelname)s : %(message)s')

filehandler= lg.FileHandler('Flask_DB.log')
filehandler.setFormatter(formatter)

logger.addHandler(filehandler)

stream_handler = lg.StreamHandler() #no need to set log level as its set to error by logger

logger.addHandler(stream_handler)
#lg.basicConfig(filename = '{}.log'.format(__name__), level = lg.INFO,format = '%(asctime)s : %(levelname)s : %(message)s')

from configparser import ConfigParser
file = "config.ini"
config = ConfigParser()
config.read(file)

@app.route('/mysql/showdb', methods=['POST']) # for calling the API from Postman/SOAPUI
def mysql_show_db():
    """ provide host, user, password as inputs"""
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for insert : {mydb.is_connected()}')

        query = "SHOW DATABASES"

        cursor = mydb.cursor() #create a cursor to execute queries
        cursor.execute(query)
        #print(cursor.fetchall())
        result = [i for i in cursor.fetchall()]
        #logger.info(f"All databases : {cursor.fetchall()}")
        return jsonify(result)

    except Exception as e:
        mydb.close()
        print(str(e))

@app.route('/mysql/createdb', methods=['POST']) # for calling the API from Postman/SOAPUI
def mysql_create_db():
    """ provide host, user, password, dbname, [drop = y/n] as inputs"""
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for insert : {mydb.is_connected()}')
        dbname = request.json['dbname']
        query = f"Create database {dbname}"
        cursor = mydb.cursor() #create a cursor to execute queries
        cursor.execute(query)
        logger.info(f"Database {dbname} Created!!")
        mydb.close()
        return f"Database {dbname} Created!!"
    except Exception as e:
        if request.json['drop'] == 'y':
            cursor.execute(f"drop database {dbname}")
            cursor.execute(f"Create database {dbname}")
            mydb.close()
            logger.warning(f"error rectified by drop: {e}")
            return f"Database {dbname} Created!!"
        else:
            mydb.close()
            logger.warning(f"warning: {e}")
            return f"Database {dbname} already present!!"


@app.route('/mysql/createtable', methods=['POST'])  # for calling the API from Postman/SOAPUI
def mysql_create_table():
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for insert : {mydb.is_connected()}')
        dbname = request.json['dbname']
        tbname = request.json['tbname']
        schema = request.json['schema']

        query = f"Create database if not exists {dbname}"
        cursor = mydb.cursor()  # create a cursor to execute queries
        cursor.execute(query)

        query = f"create table if not exists {dbname}.{tbname} ({schema})"

        cursor = mydb.cursor()  # create a cursor to execute queries
        cursor.execute(query)
        logger.info(f"Table {tbname} Created!!")
        mydb.close()
        return f"Table {tbname} Created!!"
    except Exception as e:
        mydb.close()
        logger.warning(f"warning: {e}")
        return f"Table {tbname} already present in {dbname}..!!"


@app.route('/mysql/insert_one', methods=['POST'])  # for calling the API from Postman/SOAPUI
def insert_dbtb_one():
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for insert : {mydb.is_connected()}')

        dbname = request.json['dbname']
        tbname = request.json['tbname']
        tbvalues = request.json['tbvalues']
        query = 'insert into {one}.{two} values ({three})'.format(one=dbname, two=tbname, three=', '.join([value for value in tbvalues]))
        cursor = mydb.cursor()  # create a cursor to execute queries
        cursor.execute(query)
        mydb.commit()
        logger.info(f"data inserted into db:{dbname}; Table : {tbname}")
        mydb.close()
        return f"data inserted into db:{dbname}; Table : {tbname}"
    except Exception as e:
        mydb.close()
        # print(str(e))
        logger.error(e)
        return f"error : {e}"

@app.route('/mysql/update_tbcol', methods=['POST'])  # for calling the API from Postman/SOAPUI
def mysql_update():
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for update: {mydb.is_connected()}')

        dbname = request.json['dbname']
        tbname = request.json['tbname']
        colname = request.json['colname']
        newval = request.json['newval']
        oldval = request.json['oldval']
        query = f'update {dbname}.{tbname} set {colname} = {newval} where {colname} = {oldval};'
        cursor = mydb.cursor()  # create a cursor to execute queries
        cursor.execute(query)
        mydb.commit()
        logger.info(f"data updated into db:{dbname}; Table : {tbname}")
        mydb.close()
        return f"data updated into db:{dbname}; Table : {tbname}"
    except Exception as e:
        mydb.close()
        # print(str(e))
        logger.error(e)
        return f"error : {e}"


@app.route('/mysql/insert_csv', methods=['POST'])  # for calling the API from Postman/SOAPUI
def insert_dbtb_csv():
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for insert : {mydb.is_connected()}')

        path = request.json['path']
        dbname = request.json['dbname']
        tbname = request.json['tbname']
        with open(path, 'r') as data:
            next(data)
            db_csv = csv.reader(data, delimiter=',')
            # next(db_csv)
            print(db_csv)
            allvalues = []
            for j in db_csv:
                value = ([i for i in j])
                allvalues.append(value)
            query = f'insert into {dbname}.{tbname} values (%s{",%s"*(len(allvalues[0])-1)});'
            cursor = mydb.cursor()  # create a cursor to execute queries
            cursor.executemany(query, allvalues)
            mydb.commit()
            logger.info(f"data inserted into db:{dbname}; Table : {tbname}")
        mydb.close()
        return f"All data updated into db:{dbname}; Table : {tbname}"
    except Exception as e:
        mydb.close()
        # print(str(e))
        logger.error(e)
        return f"error : {e}"

@app.route('/mysql/download_data', methods=['POST']) # for calling the API from Postman/SOAPUI
def mysql_download_data():
    """ provide host, user, password as inputs"""
    try:
        mydb = connection.connect(host=config['mysql']['host'],user=config['mysql']['user'], passwd=config['mysql']['password'],use_pure=True)
        # check if the connection is established
        logger.info(f'connection established for download : {mydb.is_connected()}')
        dbname = request.json['dbname']
        tbname = request.json['tbname']
        filename = request.json['filename']

        query = f"select * from {dbname}.{tbname}"

        cursor = mydb.cursor() #create a cursor to execute queries
        cursor.execute(query)
        #print(cursor.fetchall())
        result = [i for i in cursor.fetchall()]
        with open(f'{filename}.csv', mode='w', newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([i[0] for i in cursor.description])  # write headers
            csv_writer.writerows(result)

        logger.info(f"file downloaded at : {os.getcwd()}")
        return f"file downloaded at : {os.getcwd()}"

    except Exception as e:
        mydb.close()
        logger.info(f"file downloaded at : {os.getcwd()}")
        return f"error : {e}"

@app.route('/mongodb/showdb', methods=['POST'])  # for calling the API from Postman/SOAPUI
def mongo_showdb():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv']) #get SRV from mongo atlas
        logger.info(f"connected to atlas")
        return jsonify(client_atlas.list_database_names())  # dbname can be seen only once data is inserted
    except Exception as e:
        logger.info(f"file downloaded at : {os.getcwd()}")
        return "error: ", e

@app.route('/mongodb/createdb', methods=['POST']) # for calling the API from Postman/SOAPUI
def mongo_createdb():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv'])
        db_name = request.json['db_name']
        # create db
        client_atlas[db_name]
        logger.info(f"{db_name} DB created but, can be seen only once data is inserted")
        return jsonify(client_atlas.list_database_names())  # dbname can be seen only once data is inserted
    except Exception as e:
        logger.info(f"error: {e}")
        return "error: ", e


@app.route('/mongodb/createcoll', methods=['POST']) # for calling the API from Postman/SOAPUI
def mongo_createcoll():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv'])
        db_name = request.json['db_name']
        coll_name = request.json['coll_name']
        #create db
        db_atlas = client_atlas[db_name]
        db_atlas[coll_name]
        logger.info(f"{coll_name} collection created but, can be seen only once data is inserted")
        return f"{coll_name} collection created in DB {db_name}"  # dbname can be seen only once data is inserted
    except Exception as e:
        #print("error: ", e)
        logger.info(f"error: {e}")
        return "error: ", e

@app.route('/mongodb/insertrecord', methods=['POST']) # for calling the API from Postman/SOAPUI
def mongo_insertrecord():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv'])
        db_name = request.json['db_name']
        coll_name = request.json['coll_name']
        record = request.json['record']
        #create db
        db_atlas = client_atlas[db_name]
        collection_mtcars = db_atlas[coll_name]
        collection_mtcars.insert_one(record)
        logger.info(f"record inserted into collection {coll_name}")
        return f"record inserted into collection {coll_name}"  # dbname can be seen only once data is inserted
    except Exception as e:
        #print("error: ", e)
        logger.info(f"error: {e}")
        return "error: ", e

@app.route('/mongodb/insertcsv', methods=['POST']) # for calling the API from Postman/SOAPUI
def mongo_insertcsv():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv'])
        db_name = request.json['db_name']
        coll_name = request.json['coll_name']
        csv_file = request.json['csv_file']
        #create db
        db_atlas = client_atlas[db_name]
        collection_mtcars = db_atlas[coll_name]
        data = pd.read_csv(f"{csv_file}")
        data_json = json.loads(data.to_json(orient='records')) # to_json: saving to json file, json.loads: reading json file
        collection_mtcars.insert_many(data_json)
        logger.info(f"All data uploaded to {coll_name} in DB {db_name}")
        return f"All data uploaded to {coll_name} in DB {db_name}"  # dbname can be seen only once data is inserted
    except Exception as e:
        #print("error: ", e)
        logger.info(f"error: {e}")
        return "error: ", e


@app.route('/mongodb/updatecol', methods=['POST'])  # for calling the API from Postman/SOAPUI
def mongo_updatecol():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv'])
        db_name = request.json['db_name']
        coll_name = request.json['coll_name']
        column_name = request.json['column_name']
        old_value = request.json['old_value']
        new_value = request.json['new_value']

        db_atlas = client_atlas[db_name]
        collection_mtcars = db_atlas[coll_name]
        myquery = {f"{column_name}": f"{old_value}"}
        newvalues = {"$set": {f"{column_name}": f"{new_value}"}}
        collection_mtcars.update_one(myquery, newvalues)
        logger.info(f"collection ({coll_name}) updated ")
        return f"collection ({coll_name}) updated "  # dbname can be seen only once data is inserted
    except Exception as e:
        #print("error: ", e)
        logger.info(f"error: {e}")
        return "error: ", e


@app.route('/mongodb/downloadcsv', methods=['POST'])  # for calling the API from Postman/SOAPUI
def mongo_downloadcsv():
    try:
        client_atlas = pymongo.MongoClient(config['mongodb']['url/srv'])
        db_name = request.json['db_name']
        coll_name = request.json['coll_name']
        exported_csv_name = request.json['exported_csv_name']
        # create db
        db_atlas = client_atlas[db_name]
        collection_mtcars = db_atlas[coll_name]

        lst = collection_mtcars.find()
        df = pd.DataFrame(list(lst))
        df.to_csv(f"{exported_csv_name}.csv")

        logger.info(f"file downloaded at : {os.getcwd()}")
        return f"file downloaded at : {os.getcwd()}"
    except Exception as e:
        #print("error: ", e)
        logger.info(f"error: {e}")
        return "error: ", e


@app.route('/cassandra/createtb', methods=['POST'])  # for calling the API from Postman/SOAPUI
def cassandra_createtb():
    try:
        keyspace = request.json['keyspace']
        tb_name = request.json['tb_name']
        schema = request.json['schema']

        cloud_config = {
            'secure_connect_bundle': config['cassandra']['secure_connect_bundle']
        }
        auth_provider = PlainTextAuthProvider(config['cassandra']['client_id'], config['cassandra']['client_secret'])
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()

        session.execute(f"create table {keyspace}.{tb_name} ({schema});")

        return f"Table created: {keyspace}.{tb_name}"
    except Exception as e:
        logger.info(f"error: {e}")
        return "error: ", e

@app.route('/cassandra/inserttb', methods=['POST'])  # for calling the API from Postman/SOAPUI
def cassandra_inserttb():
    try:
        keyspace = request.json['keyspace']
        tb_name = request.json['tb_name']

        cloud_config = {
            'secure_connect_bundle': config['cassandra']['secure_connect_bundle']
        }
        auth_provider = PlainTextAuthProvider(config['cassandra']['client_id'], config['cassandra']['client_secret'])
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()

        rows = session.execute(f"select * from {keyspace}.{tb_name}")
        session.execute(
            f"INSERT INTO {keyspace}.{tb_name} ({', '.join([i for i in rows.column_names])}) VALUES ({request.json['record']}) IF NOT EXISTS ")

        logger.info(f"Data inserted: {keyspace}.{tb_name}")
        return f"Data inserted: {keyspace}.{tb_name}"
    except Exception as e:
        #print("error: ", e)
        logger.info(f"error: {e}")
        return "error: ", e


@app.route('/cassandra/updatetb', methods=['POST'])  # for calling the API from Postman/SOAPUI
def cassandra_updatetb():
    try:
        keyspace = request.json['keyspace']
        tb_name = request.json['tb_name']
        colname = request.json['colname']
        newval = request.json['newval']
        pk = request.json['pk']
        ids = request.json['ids'] #specify multiple ids with a ','

        cloud_config = {
            'secure_connect_bundle': config['cassandra']['secure_connect_bundle']
        }
        auth_provider = PlainTextAuthProvider(config['cassandra']['client_id'], config['cassandra']['client_secret'])
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()

        session.execute(f"UPDATE {keyspace}.{tb_name}  SET {colname} = {newval}  WHERE {pk} IN ({ids});")

        logger.info(f"Data updated: {keyspace}.{tb_name}")
        return f"Data updated: {keyspace}.{tb_name}"
    except Exception as e:
        logger.info(f"error: {e}")
        return "error: ", e


@app.route('/cassandra/insertcsv', methods=['POST'])  # for calling the API from Postman/SOAPUI
def cassandra_insertcsv():
    try:
        keyspace = request.json['keyspace']
        tb_name = request.json['tb_name']
        path = request.json['path']

        cloud_config = {
            'secure_connect_bundle': config['cassandra']['secure_connect_bundle']
        }
        auth_provider = PlainTextAuthProvider(config['cassandra']['client_id'], config['cassandra']['client_secret'])
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()

        rows = session.execute(f"select * from {keyspace}.{tb_name}")
        colnames = ', '.join([i for i in rows.column_names])
        #colnames = ', '.join([i for i in rows.one()._fields])

        with open(path, 'r') as data:
            next(data)
            db_csv = csv.reader(data, delimiter=',')
            # next(db_csv)
            print(db_csv)
            for j in db_csv:
                values = ', '.join([i for i in j[1:]])
                query = f"INSERT INTO {keyspace}.{tb_name} ({colnames}) VALUES ('{j[0]}',{values}) IF NOT EXISTS; "
                session.execute(query)

        logger.info(f"CSV Data updated: {keyspace}.{tb_name}")
        return f"CSV Data updated: {keyspace}.{tb_name}"
    except Exception as e:
        logger.info(f"error: {e}")
        return "error: ", e

@app.route('/cassandra/downloadcsv', methods=['POST'])  # for calling the API from Postman/SOAPUI
def cassandra_downloadcsv():
    try:
        keyspace = request.json['keyspace']
        tb_name = request.json['tb_name']
        filename = request.json['filename']

        cloud_config = {
            'secure_connect_bundle': config['cassandra']['secure_connect_bundle']
        }
        auth_provider = PlainTextAuthProvider(config['cassandra']['client_id'], config['cassandra']['client_secret'])
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()

        query = f"select * from {keyspace}.{tb_name}"
        df = pd.DataFrame(session.execute(query))
        df.to_csv(f'{filename}.csv')

        logger.info(f"CSV Downloaded at : {os.getcwd()}")
        return f"CSV Downloaded at : {os.getcwd()}"
    except Exception as e:
        logger.info(f"error: {e}")
        return "error: ", e

if __name__ == '__main__':
    app.run()