from frapi import app, mysql_connection
import pandas as pd
import os
from flask import flash, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_cors import cross_origin
from frapi import utility_function
from frapi import mysql_connection
import time
import multiprocessing as mp
 
embeddings = pd.DataFrame()

@app.route('/search-by', methods=['GET', 'POST'])
@cross_origin()
def search_by_image():
    if request.method == 'POST':
        start_time = time.time()
        # check if the post request has the file part
        mysql = mysql_connection.get_mysql()
        # Create cursor
        cur = mysql.connection.cursor()

        filename = ''
        filepath = ''
        # article_type = ''
        # master_category = ''
        sub_category = ''
        # base_colour = ''
        # gender = ''

        query_string = ""
        static_path = os.path.join(app.root_path, 'static') 

        if 'file' in request.files:
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                return jsonify({'success': False, 'message': 'Invalid image'})
            if file and utility_function.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = static_path + '/query_images'
                file.save(os.path.join(filepath, filename))

                if 'sub_category' in request.form:
                    sub_category = request.form['sub_category']
                else:
                    sub_category = utility_function.classify_image(filepath, filename)

            else:
                return jsonify({'success': False, 'message': 'Invalid image'})
        else:
            query_string = """SELECT met.image_id, met.product_display_name, met.article_type FROM product_metadata AS met INNER JOIN embeddings AS em ON met.image_id = em.image_id"""

            where_flag = False
            if 'article_type' in request.form:
                query_string = query_string + " WHERE met.article_type = '{article_type}' ".format(article_type = request.form['article_type'] )
                # article_type = request.form['article_type']
                where_flag = True

            if 'master_category' in request.form:
                if where_flag == False:
                    query_string = query_string + " WHERE "
                    where_flag = True
                else:
                    query_string = query_string + " and "

                query_string = query_string + " met.master_category = '{master_category}'".format(master_category = request.form['master_category'])

                # master_category = request.form['master_category']

            if sub_category or 'sub_category' in request.form:
                if where_flag == False:
                    query_string = query_string + " WHERE "
                    where_flag = True
                else:
                    query_string = query_string + " and "

                if 'sub_category' in request.form:
                    sub_category = request.form['sub_category']
                query_string = query_string + " met.sub_category = '{sub_category}'".format( sub_category = sub_category )
                # sub_category = request.form['sub_category']

            if 'base_colour' in request.form:
                if where_flag == False:
                    query_string = query_string + " WHERE "
                    where_flag = True
                else:
                    query_string = query_string + " and "
                    
                query_string = query_string + " met.base_colour = '{base_colour}'".format(base_colour = request.form['base_colour'])
                # base_colour = request.form['base_colour']
            
            if 'gender' in request.form:
                if where_flag == False:
                    query_string = query_string + " WHERE "
                    where_flag = True
                else:
                    query_string = query_string + " and "
                    
                query_string = query_string + " met.gender = '{gender}'".format(gender = request.form['gender'])
                # gender = request.form['gender']
    
            # return the query result if no product image is uploaded
             
            cur.execute(query_string)
            products = cur.fetchall()
            cur.close()
            return jsonify({
                    'success': True,
                    'data': products
                })


        # calculate similarity between inventory products and the query product

        filter_start_time = time.time()
        products = embeddings[embeddings['sub_category'] == sub_category]

        if 'article_type' in request.form:
            products = products[ products['article_type'] == request.form['article_type']]

        if 'gender' in request.form:
            products = products[products['gender'] == request.form['gender']]
        
        print('End filter')
        print(time.time() - filter_start_time)
        
        recommendation = []
        if len(products.index) > 0:
            recommendation = utility_function.get_recommendation_for_query_product(filepath, filename, products)

        elapsed_time = (time.time() - start_time)
        return jsonify({
          'success': True,
          'data':  recommendation,
          'time': elapsed_time
        })

        # return jsonify({
        #   'success': True,
        #   'time': elapsed_time
        # }) 
    return jsonify({'success': False, 'message': 'Invalid request'})


@app.route('/fetch-embeddings')
@cross_origin()
def fetch_embeddings():
    engine = mysql_connection.get_engine()
    global embeddings
    embeddings = pd.read_sql("""SELECT met.image_id, met.sub_category, met.gender, met.base_colour, met.master_category, met.product_display_name, met.article_type, JSON_UNQUOTE(JSON_EXTRACT(em.embedding, '$.value')) as embedding FROM product_metadata AS met INNER JOIN embeddings AS em ON met.image_id = em.image_id""", con=engine)

    return jsonify({
        'success': True
    })


@app.route('/check-embeddings')
@cross_origin()
def check_embeddings():
    print(embeddings.head(2))
    return 'Ok'


