from frapi import app
from flask_mysqldb import MySQL
from sqlalchemy import create_engine

# init MYSQL
mysql = MySQL(app)
engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                       .format(user="root",
                               pw="Shohag@1234",
                               db="fashion"))

def get_mysql():
    return mysql

def get_engine():
    return engine