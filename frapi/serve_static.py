from flask import send_from_directory
from frapi import app
import os

@app.route('/images/<path:id>')
def send_images(id):
    static_path = os.path.join(app.root_path, 'static')
    img_path = os.path.join(static_path , 'images/' + id + '.jpg')
    
    if os.path.exists(img_path):
        return send_from_directory(app.config['DATASET_FOLDER'] + '/images', id + '.jpg')

    return send_from_directory(app.config['DATASET_FOLDER'] + '/images', 'notfound.png')
    
    
@app.route('/banner/<path:name>')
def send_banners(name):
    static_path = os.path.join(app.root_path, 'static')
    img_path = os.path.join(static_path , 'banners/' + name)
    
    if os.path.exists(img_path):
        return send_from_directory(app.config['DATASET_FOLDER'] + '/banners', name)

    return send_from_directory(app.config['DATASET_FOLDER'] + '/images', 'notfound.png')