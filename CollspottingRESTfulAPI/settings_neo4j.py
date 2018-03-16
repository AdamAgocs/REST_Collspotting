'''
Created on 11 Oct 2017

@author: agocsi
'''

#database

from py2neo import authenticate, Graph
from urllib.request import urljoin

DATABASE_PROTOCOL = 'http'
DATABASE_URL = 'localhost'
DATABASE_PORT = '7575'
DATABASE_PATH = '/db/data'
DATABASE_USERNAME = 'neo4j'
DATABASE_PASSWORD = 'adam8411'

authenticate(':'.join([DATABASE_URL, DATABASE_PORT]), DATABASE_USERNAME, DATABASE_PASSWORD)
graph_db = Graph(DATABASE_PROTOCOL + '://' + DATABASE_URL + ':' + DATABASE_PORT + DATABASE_PATH)

project = 'ranking'
default_node = 'he'
