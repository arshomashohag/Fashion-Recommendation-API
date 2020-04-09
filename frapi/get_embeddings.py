from frapi import app
from frapi import mysql_connection
from flask import jsonify
import json
import numpy as np
from flask_cors import cross_origin



@app.route('/get-embeddings', defaults={'image_id': None})
@app.route('/get-embeddings/<image_id>')
@cross_origin()
def get_embeddings(image_id):
    # init MYSQL
    mysql = mysql_connection.get_mysql()
    # Create cursor
    cur = mysql.connection.cursor()

    query_string = """SELECT * FROM embeddings"""
    if image_id != None:
        query_string = query_string + " WHERE image_id = {image_id}".format(image_id=image_id)
    
    
    cur.execute(query_string)
    
    
    embeds_values = cur.fetchall()
    # Close connection
    cur.close()

    return_values = list()
    for row in embeds_values:
        cur_value = {
            'image_id': '',
            'embedding': [],
            'id': ''
        }
        for key in row:
            cur_value[key] = row[key]
            if key == 'embedding':
                value = json.loads(row[key])
                for vkey in value:
                     cur_value[key] = value[vkey]
            
        return_values.append(cur_value)

    

    return jsonify(return_values)
