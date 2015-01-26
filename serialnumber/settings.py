import os

DATABASE = os.path.join(os.path.dirname(__file__), 'db', 'serialnumber.db')
DEBUG = bool(os.environ.get('DEBUG'))
SECRET_KEY = '?pcuPdF|C>nCAp7ac=fcq?nLa8=TAb'
USERS = {
    'admin': 'admin',
}
APP_TITLE = 'Serial Numbers'
