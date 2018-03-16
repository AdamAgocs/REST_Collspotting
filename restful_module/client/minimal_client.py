'''
Created on 12 Mar 2018

@author: agocsi
'''

import requests
from urllib.parse import urljoin
from os.path import join
import json
import timeit
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


delete_all = 'Match (s:student) Delete s'
graph_db.cypher.execute(delete_all)

def load_json_file(path, filename):
    file = join(path, filename) 
    return json.load(open(file, 'r', encoding='utf-8'))


URL_BASIC = 'http://localhost:8000/schemas/ranking'

URL_RESTAPI_BULK_NODE = r'http://localhost:8000/restapi/batch_node'
URL_RESTAPI_BULK_EDGE = r'http://localhost:8000/restapi/batch_edge'
URL_RESTAPI_SINGLE_NODE = 'http://localhost:8000/restapi/single_node'
URL_RESTAPI_SINGLE_EDGE = 'http://localhost:8000/restapi/single_edge'

headers = {'Content-Type':'application/json'}

#create project - project name: ranking
req = requests.Request('PUT', URL_BASIC, headers=headers)
prereq = req.prepare()
   
session = requests.Session()
resp = session.send(prereq)
#end of creating project


#uploading descriptors - project: ranking, descriptors : he, student and student_in
filenames = ['he.json', 'student.json', 'student_in.json']
path = r'C:\\Working\\descriptors\\'

for filename in filenames:
    req = requests.Request('PUT', urljoin(URL_BASIC+'/', filename), headers=headers, data={}, **{'json':load_json_file(path, filename)})
    prereq = req.prepare()
       
    resp = session.send(prereq)
    print(resp)

single_path = r'C:\\Working\\Telcs\\measurement\\' 
measurement = []

def upload_single(type, storage):
    for i in range(0, 50000):
        start = timeit.default_timer()
        
        req = requests.Request('PUT', URL_RESTAPI_SINGLE_NODE, headers=headers, data={}, params={'project': 'ranking', 'type': type}, **{'json':storage[i]})
        prereq = req.prepare()
        resp = session.send(prereq)
        
        end = timeit.default_timer()
        measurement.append(end - start)
        

student_single_json_storage = []
for i in range(0, 50000):
    student_single_json_storage.append(load_json_file(single_path, 'student_data_measurement_{0}.json'.format(i)))

# for i in range(0, 10):
#     graph_db.cypher.execute(delete_all)
#     measurement = []
#     all = []
#     
#     upload_single('student', student_single_json_storage)
#     with open(r'C:\\Working\\Telcs\\measurement\\multiple_{0}_measurement.json'.format(i), 'w', encoding='utf-8') as file:
#         file.write(str(measurement))
#     

def upload_bulk(type, storage, size):
    start = timeit.default_timer()
    
    req = requests.Request('PUT', URL_RESTAPI_BULK_NODE, headers=headers, data={}, params={'project': 'ranking', 'type': type}, **{'json':storage})
    prereq = req.prepare()
    resp = session.send(prereq)
    
    end = timeit.default_timer()
    
    bulk_measurement.append((size, end-start))


# for j in range(0, 10):
#     bulk_measurement = []
#     for i in range(0, 50):
#         graph_db.cypher.execute(delete_all)
#         upload_bulk('student', student_single_json_storage[0:(i+1)*1000], i+1)
#     
#     with open(r'C:\\Working\\Telcs\\measurement\\bulk_multiple_{0}_measurement.json'.format(j), 'w', encoding='utf-8') as file:
#         file.write(str(bulk_measurement))
