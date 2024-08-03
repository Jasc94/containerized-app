import psycopg2
import yaml

def read_credentials(path):
    with open(path) as _:
        credentials = yaml.safe_load(_)
    return credentials

def connect_to_db(credentials):
    return psycopg2.connect(
        dbname=credentials['dbname'],
        user=credentials['user'],
        password=credentials['password'],
        host=credentials['host'],
        port=credentials['port']
    )