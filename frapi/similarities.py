from frapi import app, utility_function, mysql_connection
from werkzeug.utils import secure_filename
from flask_cors import cross_origin
from flask import flash, request, redirect, url_for
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
import keras 
from keras.applications.resnet50 import ResNet50
from keras.applications.resnet50 import preprocess_input, decode_predictions
from keras.models import Model
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, array_to_img
from keras.layers import GlobalMaxPooling2D
from sklearn.metrics.pairwise import pairwise_distances
import numpy as np
import os
import pandas as pd
import json
import time 

# Input Shape
img_width, img_height, _ = 224, 224, 3 #load_image(df.iloc[0].image).shape

@app.route('/save-similarities')
@cross_origin()
def save_similarities():
    mysql = mysql_connection.get_mysql()

    # # Pre-Trained Model
    # base_model = ResNet50(weights='imagenet', 
    #                     include_top=False, 
    #                     input_shape = (img_width, img_height, 3))
    # base_model.trainable = False

    # # # Add Layer Embedding
    # model = keras.Sequential([
    #     base_model,
    #     GlobalMaxPooling2D()
    # ])

    start_time = time.time()
    cur = mysql.connection.cursor()


    query_string = """SELECT image_id FROM product_metadata WHERE article_type = '{article_type}'"""
    article_type_query = """SELECT DISTINCT article_type FROM product_metadata"""


    cur.execute(article_type_query)
    articles = cur.fetchall()

    engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                       .format(user="root",
                               pw="Shohag@1234",
                               db="fashion"))
    for article in articles:
        s_time = time.time()
        cur.execute( query_string.format(article_type = article['article_type']) )
        images = cur.fetchall()
        image_ids = []
        embeddings = []
        for row in images:
            embds = utility_function.get_embedding(str( row['image_id'] ) + '.jpg' )
            if len(embds) <= 0:
                embds = [0] * app.config['MODEL_OUTPUT_DIM']

            embeddings.append( embds )
            image_ids.append( row['image_id'] )
        
        sim_scores = 1 - pairwise_distances(embeddings, metric='cosine')
        
        i=0
        sim_map = []
        for row in images:
            sim_map.append( ( row['image_id'], json.dumps({'similarity': sim_scores[i].tolist() } ) ) )
            i = i + 1

        similarity_df = pd.DataFrame(sim_map, columns=['image_id', 'similarity'])
        similarity_df.to_sql('similarities', con = engine, if_exists = 'append', chunksize = 1000, index=False)


        image_ids_df = pd.DataFrame( [(article['article_type'], json.dumps({'ids': image_ids}))], columns=['article_type', 'image_ids'] )
        image_ids_df.to_sql('similarity_ids', con = engine, if_exists = 'append', chunksize = 1000, index=False)
        print( article['article_type'] + ' saved in - ' + str( time.time() - s_time ) )
        
    cur.close()
    print('DB operations ends in - ELT = ' + str( time.time() - start_time ) )
    return "Ok"