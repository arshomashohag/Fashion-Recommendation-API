from frapi import app, utility_function, mysql_connection
from werkzeug.utils import secure_filename
from flask_cors import cross_origin
from flask import flash, request, redirect, url_for, jsonify
from sklearn.model_selection import train_test_split
import keras 
from keras.applications.resnet50 import ResNet50
from keras.applications.resnet50 import preprocess_input, decode_predictions
from keras.models import Model
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, array_to_img
from keras.layers import GlobalMaxPooling2D
import numpy as np
import os
import pandas as pd
import json
import time

# Input Shape
img_width, img_height, _ = 224, 224, 3 #load_image(df.iloc[0].image).shape

@app.route('/save_embeddings')
@cross_origin()
def save_embeddings():
    static_path = os.path.join(app.root_path, 'static')

    df = pd.read_csv(static_path + "/styles.csv", error_bad_lines=False)
    df['image'] = df.apply(lambda row: str(row['id']) + ".jpg", axis=1)
    df = df.reset_index(drop=True)

    # # Pre-Trained Model
    base_model = ResNet50(weights='imagenet', 
                        include_top=False, 
                        input_shape = (img_width, img_height, 3))
    base_model.trainable = False

    # # Add Layer Embedding
    model = keras.Sequential([
        base_model,
        GlobalMaxPooling2D()
    ])

    start_time = time.time()

    embeddings_map = [(row['id'],  json.dumps({"value": utility_function.get_embedding(model, row['image'])})  ) for ind, row in df.iterrows()]
    embeddings_df = pd.DataFrame(embeddings_map, columns=['image_id', 'embedding'])
    # your code
    elapsed_time = time.time() - start_time

    print('Embeddings ends in - ELT = ' + str(elapsed_time) )
    # create sqlalchemy engine
    engine = mysql_connection.get_engine()

    start_time = time.time()
    embeddings_df.to_sql('embeddings', con = engine, if_exists = 'append', chunksize = 1000, index=False)
    elapsed_time = time.time() - start_time
    engine.close()
    print('DB operations ends in - ELT = ' + str(elapsed_time) )
    return "Ok"


@app.route('/calculate-embeddings', methods=['GET', 'POST'])
@cross_origin()
def calculate_embeddings():
    if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return 'No file uploaded'
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return 'Invalid file'
            if file and utility_function.allowed_file(file.filename):
                # # Pre-Trained Model
                base_model = ResNet50(weights='imagenet', 
                                    include_top=False, 
                                    input_shape = (img_width, img_height, 3))
                base_model.trainable = False

                # # Add Layer Embedding
                model = keras.Sequential([
                    base_model,
                    GlobalMaxPooling2D()
                ])
                filename = secure_filename(file.filename)
                static_path = os.path.join(app.root_path, 'static')
                file.save(os.path.join(static_path+'/query_images', filename))

                embedding = utility_function.get_embedding(model, filename, static_path + '/query_images')
                return json.dumps(embedding)
            else:
                return 'Invalid file type'
                
    return 'Invalid request'

