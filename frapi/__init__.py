
from flask import Flask
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Shohag@1234'
app.config['MYSQL_DB'] = 'fashion'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MODEL_OUTPUT_DIM'] = 2048

# Search by image settings
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}


# Static files
app.config['DATASET_FOLDER'] = 'static'


@app.route('/')
@cross_origin()
def index():
    return 'Welcome to Fashion House'

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
if __name__ == '__main__':
    app.run(debug=True)


# Import rotes
import frapi.mysql_connection
import frapi.home
import frapi.serve_static
import frapi.search_by_image
import frapi.search_by_id
import frapi.embeddings
import frapi.get_embeddings
import frapi.utility_function
import frapi.similarities
