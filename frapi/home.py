from frapi import app
from frapi import mysql_connection
from flask import jsonify
import numpy as np
from flask_cors import cross_origin


@app.route('/home')
@cross_origin()
def get_home_values():
    mysql = mysql_connection.get_mysql()
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute query
    home_values = {}

    cur.execute("""SELECT DISTINCT gender FROM product_metadata WHERE gender is not null order by gender """ )

    home_values['gender'] = cur.fetchall()

    cur.execute("""SELECT DISTINCT master_category FROM product_metadata WHERE master_category is not null order by master_category """ )

    home_values['master_category'] = cur.fetchall()

    cur.execute("""SELECT DISTINCT sub_category FROM product_metadata WHERE sub_category  is not null order by sub_category """ )

    home_values['sub_category'] = cur.fetchall()

    cur.execute("""SELECT DISTINCT  article_type FROM product_metadata WHERE article_type  is not null order by article_type """ )

    home_values['article_type'] = cur.fetchall()

    cur.execute("""SELECT DISTINCT  base_colour FROM product_metadata WHERE base_colour  is not null order by  base_colour """ )

    home_values['base_colour'] = cur.fetchall()

    cur.execute("""SELECT DISTINCT  p_usage FROM product_metadata WHERE p_usage  is not null order by p_usage """ )

    home_values['usage_type'] = cur.fetchall()

    cur.execute("""SELECT COUNT(id) AS cnt FROM product_metadata""")
    meta_count = cur.fetchall()

    meta_count = meta_count[0]['cnt']
    rand_ids = np.random.randint(1, meta_count, 18)
    rand_ids = rand_ids.tolist()

    query = "SELECT image_id, article_type, product_display_name FROM product_metadata WHERE id IN ("

    for index, id in enumerate(rand_ids):
        query = query + str(id)
        if index < len(rand_ids)-1:
            query = query + ','
    
    query = query + ")"


    cur.execute(query)
    home_values['images'] = cur.fetchall()

    # Close connection
    cur.close()
    return jsonify(home_values)
