from frapi import app
import os
from flask import flash, request, redirect, url_for, jsonify
from frapi import mysql_connection
from flask_cors import cross_origin
from frapi import utility_function
import json


@app.route('/search-by-id', methods=['POST'])
@cross_origin()
def search_by_id():
    # check if the post request has the file part
    if 'image_id' not in request.form:
        return jsonify({'success': False, 'message': 'Provide an image id'})
    image_id = request.form['image_id']
    mysql = mysql_connection.get_mysql()
    # Create cursor
    cur = mysql.connection.cursor()

    query_string = """SELECT  met.gender, met.article_type, met.product_display_name, sim.similarity, sinds.image_ids FROM product_metadata AS met INNER JOIN similarities AS sim ON met.image_id = sim.image_id INNER JOIN similarity_ids AS sinds ON met.article_type = sinds.article_type WHERE met.image_id = '{id}' limit 1""".format(id=image_id )
    cur.execute(query_string)

    products = cur.fetchall()
    

    if len(products) <= 0:
        return jsonify({'success': False, 'message': 'No query image found'})
    
    article_type = products[0]['article_type']
    gender = products[0]['gender']
    product_display_name = products[0]['product_display_name']
    image_ids = json.loads(products[0]['image_ids'])['ids']
    similarities = json.loads(products[0]['similarity'])['similarity']

    meta_query_string = """SELECT image_id, article_type, gender, product_display_name FROM product_metadata WHERE gender='{gender}' AND article_type = '{article_type}' AND image_id IN ( """

    flag = False
    for id in image_ids:
        if flag:
            meta_query_string = meta_query_string + ','
        else:
            flag = True
        meta_query_string = meta_query_string + str(id)
    
    meta_query_string = meta_query_string + """)"""
    cur.execute( meta_query_string.format(gender=gender, article_type=article_type) )
    product_metas = cur.fetchall()
    cur.close()

    recommendations = []
    i = 0
    for sim in similarities:
        recommendations.append((image_ids[i], sim, article_type, gender))
        i = i + 1
    
    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True )

    data = []
    for rec in recommendations:
        data.append({
            'image_id': rec[0],
            'similarity': rec[1],
            'article_type': rec[2],
            'product_display_name': rec[3]
        })

    return jsonify({
        'success': True,
        'query_image': {
            'image_id': image_id,
            'article_type': article_type,
            'product_display_name': product_display_name,
            
        },
        'meta': product_metas,
        'data': data
    })