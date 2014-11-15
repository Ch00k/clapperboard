SQLALCHEMY_DATABASE_URI = \
    'mysql://clap_user:clap_user_pw@localhost/clap_db?unix_socket=/tmp/mysql.sock'
CORS_HEADERS = 'Content-Type'
CORS_RESOURCES = {r'/*': {'origins': '*'}}
AUTH_TOKEN = '123qwe'
DEBUG = True