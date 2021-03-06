from frapi import app
from keras.applications.resnet50 import preprocess_input, decode_predictions
import keras 
from keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from keras.models import Model, load_model
from keras.layers import GlobalMaxPooling2D
from keras.preprocessing import image
import os
from scipy import spatial
import numpy as np
import json
import time
import multiprocessing as mp
from sklearn.metrics.pairwise import pairwise_distances
import tensorflow as tf


# Input Shape
img_width, img_height, _ = 224, 224, 3 #load_image(df.iloc[0].image).shape
static_path = os.path.join(app.root_path, 'static')
    
# base_model = ResNet50(weights='imagenet', 
#                                     include_top=False, 
#                                     input_shape = (img_width, img_height, 3))
# base_model.trainable = False
# global_max_pool = GlobalMaxPooling2D()
#     # # Add Layer Embedding
# model = keras.Sequential([
#                     base_model,
#                     global_max_pool
#                 ])

graph = tf.get_default_graph()

sess = tf.Session(graph=graph)
keras.backend.set_session(sess)

embedding_model = load_model(static_path + '/models/model.h5')
classifier_model = load_model(static_path + '/models/resnet_classifier_subcat.h5')




def img_path(img, path):
    if path == None:
        return static_path + "/images/"+img
    else:
        return static_path + "/query_images/" + img

def get_embedding(img_name, path=None):
    if os.path.exists(img_path(img_name, path)):
        img = image.load_img(img_path(img_name, path), target_size=(img_width, img_height))
        # img to Array
        x   = image.img_to_array(img)
        # Expand Dim (1, w, h)
        x   = np.expand_dims(x, axis=0)
        # Pre process Input
        x   = preprocess_input(x)

        global sess
        global graph

        with graph.as_default():
            keras.backend.set_session(sess)
            y = embedding_model.predict(x).reshape(-1).tolist()
            return y
    else:
        return []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_recommendation(image_id, embeddings):
    print('Called')
    query_embed = []
    image_embeds = []
    return_response = {}
    temp_products = {}
    temp_products['products'] = {}

    for embed in embeddings:
        if str(embed['image_id']) == image_id:
            query_embed = json.loads(embed['embedding'])['value']
            return_response['query_image'] = {'image_id': str(embed['image_id']), 'article_type': embed['article_type'], 'product_display_name': embed['product_display_name']}
        else:
            image_embeds.append((str(embed['image_id']), json.loads(embed['embedding'])['value'] ) )
            temp_products['products'][str(embed['image_id'])] = { 'image_id': str(embed['image_id']),  'article_type': embed['article_type'], 'product_display_name': embed['product_display_name']}
    
    recommendations = []
    for embed in image_embeds:
        if len(embed[1]) > 0:
            recommendations.append((embed[0], 1 - spatial.distance.cosine(query_embed,  embed[1]) ))
        else:
            recommendations.append((embed[0], 0))

    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True )
    recommendations = recommendations[: 100]

    return_response['recommended_products'] = []
    for recn in recommendations:
        return_response['recommended_products'].append( temp_products['products'][recn[0]] )

    return return_response



 
def cosine_similarity(product, query_embed, query_dot):
    embds =  json.loads(product[1]['embedding'])
    if len(embds) > 0:
        sim = np.dot(query_embed, embds) / ( query_dot * (np.dot(embds,embds) ** .5) )
        return ( product[1]['image_id'], sim, product[1]['article_type'], product[1]['product_display_name'] ) 
    else:
        return ( product[1]['image_id'], 0 , product[1]['article_type'], product[1]['product_display_name'] ) 


 

def get_recommendation_for_query_product(image_path, filename, inventory_products): 
    
    print('Starting')
    start_time1 = time.time()
    
    keras.backend.clear_session()
    # model = load_model(static_path + '/models/model.h5')

    query_embed = get_embedding(filename, image_path)
    print(time.time() - start_time1)
    
    

    
    
    # query_embed_dot = np.dot(query_embed, query_embed) ** .5
 
    # Step 1: Init multiprocessing.Pool(mp.cpu_count())
    # pool = mp.Pool()

    # Step 2: Apply parallelism
    
    cosine_start_time = time.time()

    all_embeddings = []

    for product in inventory_products.iterrows():
        embds = json.loads(product[1]['embedding'])
        if len(embds) < app.config['MODEL_OUTPUT_DIM']:
            embds = [0] * app.config['MODEL_OUTPUT_DIM']
        all_embeddings.append(embds)

    sim_scores = 1 - pairwise_distances([query_embed], all_embeddings, metric='cosine')

    sim_scores = sim_scores[0]

    recommendations = []
    i = 0
    for product in inventory_products.iterrows():
        recommendations.append( ( product[1]['image_id'], sim_scores[i] , product[1]['article_type'], product[1]['product_display_name'] ) )
        i = i + 1
     
    
    print('End cosine')
    print(time.time() - cosine_start_time)
    # Step 3: Don't forget to close
    # pool.close()    
    # pool.join()

    # recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True )
    # recommendations = recommendations[: 100]

    response = []
    for rec in recommendations:
        response.append({
            'image_id': rec[0],
            'similarity': rec[1],
            'article_type': rec[2],
            'product_display_name': rec[3]
        })

    return response




def loadImage(path):
    img = image.load_img(path, target_size=(img_width, img_height))
    return img





def get_prediction( name_labels, other_labels, path):
    # Reshape
    img =  loadImage(path)
    # img to Array
    x   = image.img_to_array(img)
    # Expand Dim (1, w, h)
    x   = np.expand_dims(x, axis=0)
    # Pre process Input
    x   = preprocess_input(x)

    global sess
    global graph

    with graph.as_default():
        keras.backend.set_session(sess)
        x   = classifier_model.predict(x).reshape(-1)
        threshold_flag = False

        # result = np.where(x == np.amax(x))
        max_ind = 0
        max_val = -1

        second_max_ind = 0
        second_max_val = -1

        ind = 0
        for prediction in x:
            if prediction > max_val:
                second_max_ind = max_ind
                second_max_val = max_val
                max_val = prediction
                max_ind = ind
            else:
                if prediction > second_max_val:
                    second_max_val = prediction
                    second_max_ind = ind

            if prediction >= app.config['CLASSIFIER_THRESHOLD']:
                threshold_flag = True
            ind = ind + 1
    
        print(x)
        if threshold_flag:
            return [ name_labels[max_ind] ]
        else:
            other_labels.append(name_labels[max_ind])

            if second_max_val > 0.2:
                other_labels.append(name_labels[second_max_ind])
            print(other_labels)
            return other_labels





def classify_image(image_path, image_name):
    labels = ['Bags', 'Belts', 'Bottomwear','Eyewear', 'Flip Flops', 'Fragrance', 'Innerwear', 'Jewellery', 'Lips', 'Sandal','Shoes', 'Socks', 'Topwear', 'Wallets', 'Watches']
    other_labels = ["Dress", "Loungewear and Nightwear", "Saree", "Nails", "Makeup", "Headwear", "Ties", "Accessories", "Scarves", "Cufflinks", "Apparel Set","Free Gifts", "Stoles","Skin Care", "Skin", "Eyes", "Mufflers", "Shoe Accessories", "Sports Equipment", "Gloves", "Hair" , "Bath and Body", "Water Bottle", "Perfumes", "Umbrellas", "Wristbands", "Beauty Accessories", "Sports Accessories", "Vouchers", "Home Furnishing" ]
    keras.backend.clear_session()
    # model = load_model(static_path + '/models/resnet_classifier_subcat.h5')
    
    return get_prediction(labels, other_labels, image_path + '/' + image_name)
