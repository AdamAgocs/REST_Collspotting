from django.shortcuts import render
import json
from os.path import join, isdir, dirname
from os import mkdir, listdir
from rest_framework.response import Response 
from rest_framework.decorators import api_view, parser_classes
from rest_framework import status
from rest_framework.parsers import JSONParser
from restful_module.validator import JSONSchemaMetaSchemaValidator
from jsonschema.exceptions import SchemaError, ValidationError
from restful_module import interface_errors
from restful_module.interface import Neo4jInterface
from CollspottingRESTfulAPI.settings_neo4j import graph_db
from functools import wraps
import logging


# Create your views here.

#logger
_logger = logging.getLogger(__name__)

#jsonschema validator
_validator = JSONSchemaMetaSchemaValidator()

#database interface 
_interface = Neo4jInterface(graph_db)

__UNACCESSABLE_PROJECTS = ['validators', 'basic']

_logger_messages = {
   'BEG' : 'The {0} function is called with the following parameters: {1}',
   'END' : 'The {0} function is executed',
   'RES' : 'The {0} was called successfully with {1} parameters. The result is: {2}',
   'PAR' : 'The {0} has the following parameter list: {1}',
   'MET' : 'The {0} was called with the following method: {1}'
   }

def __logged_function(method, *args, **kwargs):
    @wraps(method)
    def __decorated_func(*args, **kwargs):
        _logger.debug(_logger_messages['BEG'].format(method.__name__, str({'args' : args, 'kwargs' : kwargs})))
        retVal = method(*args, **kwargs)
        _logger.debug(_logger_messages['END'].format(method.__name__))
        return retVal
    return __decorated_func
    
_logger_restapi_messages_project_details = {
   'NOE': 'The project does not exist: {0}',
   'ARE': 'The project already exists: {0}',
   'K/V': '{0} --> {1}',
   'EXC': 'Raised exception: {0}',
   'INV': 'The project is invalid: {0}',
   'FER': 'Format error: {0}',
   'CRE': 'The project is created'
   }

@api_view(['PUT', 'GET'])
@parser_classes(parser_classes=(JSONParser,))
@__logged_function
def project(request, project):
    dir_name = join(r'static', r'restful_module', project)
    is_valid_project_directory = isdir(dir_name)
    
    if request.method == 'GET':
        if is_valid_project_directory:
            retVal = {}
            try:
                filenames = listdir(dir_name)
                _logger.debug(_logger_restapi_messages_project_details['K/V'].format('filenames', str(filenames)))
                for filename in filenames:
                    retVal[filename] = json.load(open(join(dir_name, filename), 'r', encoding='utf-8'))
                _logger.debug(_logger_messages['RES'].format('project', project, retVal))
                return Response(retVal, status=status.HTTP_200_OK)
            except Exception as ee:
                _logger.exception(_logger_restapi_messages_project_details['EXC'].format(str(ee)))
        else:
            _logger.info(_logger_restapi_messages_project_details['NOE'].format(project))
            return Response({"error": _logger_restapi_messages_project_details['NOE'].format(project)}, status=status.HTTP_412_PRECONDITION_FAILED) 
    
    if request.method == 'PUT':
        if is_valid_project_directory:
            _logger.info(_logger_restapi_messages_project_details['ARE'].format(project))
            return Response({"error": _logger_restapi_messages_project_details['ARE'].format(project)}, status=status.HTTP_409_CONFLICT)
        else:
            try:
                mkdir(dir_name)
                _logger.debug(_logger_messages['RES'].format('project', project, 'Done'))
                return Response({"message" : _logger_restapi_messages_project_details['CRE']}, status=status.HTTP_201_CREATED)
            except FileExistsError as fee:
                _logger.info(_logger_restapi_messages_project_details['INV'].format(project))
                _logger.info(_logger_restapi_messages_project_details['EXC'].format(str(fee)))
                return Response({"error": _logger_restapi_messages_project_details['INV'].format(project)}, status=status.HTTP_409_CONFLICT)
            except Exception as ee:
                _logger.exception(_logger_restapi_messages_project_details['EXC'].format(str(ee)))
                return Response({"error": _logger_restapi_messages_project_details['EXC'].format(str(ee))})
                
                
_logger_restapi_messages_descriptor_handler = {
   'NOE': 'The JSON Schema document does not exist: {0}',
   'K/V': '{0} --> {1}',
   'EXC': 'Raised exception: {0}',
   'INV': 'The following JSON Schema document is invalid: {0}',
   'CRE': 'The JSON Schema document is created',
   'NCO': 'The given RESTful call with PUT method does not contain any JSON document',
   'NGE': 'Invalid JSON document - graph_element has to be: {0}',
   'UNA': 'Unauthorised project: {0}',
   'GRE': 'Graph error: {0}',
   'PRE': 'Project error: {0}'
   }                

@api_view(['GET', 'PUT'])
@parser_classes(parser_classes=(JSONParser,))
@__logged_function
def descriptor_handler(request, project, file):
    
    dir_name = join(r'static', r'restful_module', project)
    if request.method == 'GET':
        try:
            retVal = json.load(open(join(dir_name, file), 'r', encoding="utf-8"))
            _logger.debug(_logger_messages['RES'].format('descriptor_handler', {'project': project, 'file':file}, retVal))
            return Response(retVal, status=status.HTTP_200_OK)
        except ValueError:
            _logger.error(_logger_restapi_messages_descriptor_handler['INV'].format(join(project, file)))
            return Response({"error": _logger_restapi_messages_descriptor_handler['INV'].format(join(project, file))}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except FileNotFoundError as fnfe:
            _logger.info(_logger_restapi_messages_descriptor_handler['NOE'].format(join(project, file)))
            return Response({"error": _logger_restapi_messages_descriptor_handler['NOE'].format(join(project, file))}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        if project.lower() in __UNACCESSABLE_PROJECTS:
            _logger.info(_logger_restapi_messages_descriptor_handler['UNA'].format(project))
            return Response({"error": _logger_restapi_messages_descriptor_handler['UNA'].format(project)}, status=status.HTTP_403_FORBIDDEN)
        try:
            is_valid = _validator.validators[request.data['graph_element']](project, request.data)
            try:
                json.dump(request.data, open(join(dir_name, file), 'w', encoding="utf-8"))
                retVal = _interface.ontology_operations[request.data['graph_element']](project, request.data)
                if request.data['graph_element'] == 'node' and retVal[0]:
                    _interface.insert_constraint(retVal[1])
            except Exception as ee:
                _logger.exception(_logger_restapi_messages_descriptor_handler['EXC'].format(str(ee)))
                return Response({"message" : _logger_restapi_messages_descriptor_handler['GRE'].format(str(ee))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            _logger.debug(_logger_messages['RES'].format('descriptor_handler', {'project': project, 'file':file}, request.data))
            return Response({"message" : request.data}, status=status.HTTP_201_CREATED)
        except SchemaError:
            _logger.info(_logger_restapi_messages_descriptor_handler['INV'].format(request.data))
            return Response({"error": _logger_restapi_messages_descriptor_handler['INV'].format(request.data)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except KeyError:
            _logger.info(_logger_restapi_messages_descriptor_handler['NGE'].format(_validator.validators.keys()))
            return Response({"error": _logger_restapi_messages_descriptor_handler['NGE'].format(_validator.validators.keys())}, status=status.HTTP_412_PRECONDITION_FAILED)
        except AttributeError:
            _logger.info(_logger_restapi_messages_descriptor_handler['NCO'])
            return Response({"error" : _logger_restapi_messages_descriptor_handler['NCO']}, status=status.HTTP_417_EXPECTATION_FAILED)
        except FileNotFoundError as fnfe:
            _logger.exception(_logger_restapi_messages_descriptor_handler['PRE'].format(str(fnfe)))
            return Response({"message" : _logger_restapi_messages_descriptor_handler['PRE'].format(str(ee))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

_logger_restapi_messages_single_node = {
   'NNE': 'The requested node does not exist: {0}',
   'NET': 'The given node type does not exist: {0}',
   'K/V': '{0} --> {1}',
   'EXC': 'Raised exception: {0}',
   'INV': 'The following JSON document is invalid for the {0} JSON Schema document: {1}',
   'CRE': 'The JSON Schema document is created',
   'NCO': 'The given RESTful call with PUT method does not contain any JSON document',
   'NGE': 'Invalid JSON document: graph_element has to be: {0}',
   'INP': 'Invalid parameters: The parameters have to be {0}',
   }          
        
@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes(parser_classes=(JSONParser,))
@__logged_function
def single_node(request):
    _logger.info(_logger_messages['MET'].format('single_node', request.method))
    _logger.info(_logger_messages['PAR'].format('single_node', request.query_params))
    if request.method == 'GET':
        try:
            if len(request.query_params) == 1:
                id = str(request.query_params['id'])
            else:
                _logger.info(_logger_restapi_messages_single_node['INP'].format('<id>'))
                return Response({"error": _logger_restapi_messages_single_node['INP'].format('<id>') }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except KeyError as ke:
            _logger.info(_logger_restapi_messages_single_node['INP'].format('<id>'))
            return Response({"error": _logger_restapi_messages_single_node['INP'].format('<id>')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            retVal = _interface.get_single_node(id)
            _logger.debug(_logger_messages['RES'].format('single_node',str(request.query_params), str(retVal)))
            return Response(json.dumps({"message" : retVal}))
        except interface_errors.GraphNonExistElementError:
            _logger.info(_logger_restapi_messages_single_node['NNE'].format(str(request.query_params)))
            return Response({"error" : _logger_restapi_messages_single_node['NNE'].format(str(request.query_params))}, status=status.HTTP_406_NOT_ACCEPTABLE)
    
    elif request.method == 'PUT':
        
        try:
            if len(request.query_params) == 2:    
                type = str(request.query_params['type'])
                project = str(request.query_params['project'])
                if project.lower() in __UNACCESSABLE_PROJECTS:
                    return Response({"Unauthorised project"}, status=status.HTTP_403_FORBIDDEN)
                data = request.data
            else:
                _logger.info(_logger_restapi_messages_single_node['INP'].format('<project> and <type>'))
                return Response({"error" : _logger.info(_logger_restapi_messages_single_node['INP'].format('<project> and <type>'))}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except KeyError as ke:
            _logger.info(_logger_restapi_messages_single_node['INP'].format('<project> and <type>'))
            return Response({"error" : _logger.info(_logger_restapi_messages_single_node['INP'].format('<project> and <type>'))}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                
        try:
            is_valid = _validator.instance_validator(project, type, data)
            if is_valid:
                try:
                    retVal = _interface.insert_single_node(project, type, data)
                    _logger.debug(_logger_messages['RES'].format('single_node', str(request.query_params), str(retVal)))
                    return Response({"message":retVal}, status=status.HTTP_201_CREATED)
                except interface_errors.GraphInterfaceException as grfie:
                    _logger.error(_logger_restapi_messages_single_node['EXC'].format(str(grfie)))
        except FileNotFoundError:
            _logger.info(_logger_restapi_messages_single_node['NET'].format(type))
            return Response({"error": _logger_restapi_messages_single_node['NET'].format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except (SchemaError, ValidationError):
            _logger.info(_logger_restapi_messages_single_node['INV'].format(type, request.data))
            return Response({"error" : _logger_restapi_messages_single_node['INV'].format(type, request.data)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as ee:
            _logger.exception(_logger_restapi_messages_single_node['EXC'].format(str(ee)))

    elif request.method == 'DELETE':
        try:
            if len(request.query_params) == 1:
                id = str(request.query_params['id'])
            else:
                _logger.info(_logger_restapi_messages_single_node['INP'].format('<id>'))
                return Response({"error": _logger_restapi_messages_single_node['INP'].format('<id>') }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except KeyError as ke:
            _logger.info(_logger_restapi_messages_single_node['INP'].format('<id>'))
            return Response({"error": _logger_restapi_messages_single_node['INP'].format('<id>')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            retVal = _interface.delete_single_node(id)
            _logger.debug(_logger_messages['RES'].format('single_node', str(request.query_params), str(retVal)))
            return Response({"message" : retVal}, status=status.HTTP_202_ACCEPTED)
        except interface_errors.GraphNonExistElementError:
            _logger.info(_logger_restapi_messages_single_node['NNE'].format(str(request.query_params)))
            return Response({"error" : _logger_restapi_messages_single_node['NNE'].format(str(request.query_params))}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except interface_errors.GraphInterfaceException as grfie:
            _logger.exception(_logger_restapi_messages_single_node['EXC'].format(str(grfie)))


_logger_restapi_messages_batch_node = {
   'NNE': 'The requested node does not exist: {0}',
   'NET': 'The given node type does not exist: {0}',
   'K/V': '{0} --> {1}',
   'EXC': 'Raised exception: {0}',
   'INV': 'The following JSON document is invalid for the {0} JSON Schema document: {1}',
   'CRE': 'The JSON Schema document is created',
   'NCO': 'The given RESTful call with PUT method does not contain any JSON document',
   'NGE': 'Invalid JSON document: graph_element has to be: {0}',
   'INP': 'Invalid parameters: The parameters have to be {0}'
   }   

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes(parser_classes=(JSONParser,))
def batch_node(request):
    if request.method == 'GET':
        try:
            if len(request.query_params) == 1:
                type = request.query_params['type']
                data =  request.data
            else:
                return Response({"error" : "Invalid parameters! Parameters are <id> and <external>"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except KeyError as ke:
            return Response({"error": "Invalid parameters!: {0}".format(str(ke))}, status=status.HTTP_406_NOT_ACCEPTABLE)

        try:

            retVal = _interface.get_bulk_node(type, data if isinstance(data, list) else None)
            return Response(json.dumps({"message" : retVal}))
        except interface_errors.GraphInterfaceException:
            return Response({"error" : "The given node does not exists"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    
    elif request.method == 'PUT':
        try:
            if len(request.query_params) == 2:    
                type = request.query_params['type']
                project = request.query_params['project']
                if project.lower() in __UNACCESSABLE_PROJECTS:
                    return Response({"Unauthorised project"}, status=status.HTTP_403_FORBIDDEN)
                data = request.data
            else:
                return Response({"error" : "Invalid parameters! Parameters are <project> and <type>"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except KeyError as ke:
            return Response({"error" : "Invalid parameters!: {0}".format(str(ke))}, status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            is_valid = _validator.instance_validator(project, type, data, 'batch_')
            if is_valid:
                try:
                    retVal = _interface.insert_bulk_node(project, type, data)
                    return Response({"message":retVal}, status=status.HTTP_201_CREATED)
                except interface_errors.GraphExistElementError as neee:
                    return Response({"error":neee}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({"error" : "The given instance is invalid for {0} type".format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except FileNotFoundError as fnfe:
            return Response({"error": "{0} type is unknown, please upload it".format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except SchemaError as se:
            return Response({"error" : "Invalid instance. The instance is not valid for {0} JSONSchema document".format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)

    elif request.method == 'DELETE':
        return Response({"messsage" : "START"}, status=status.HTTP_501_NOT_IMPLEMENTED)
        try:
            if len(request.query_params) == 2:
                id = request.query_params['id']
                external = request.query_params['external']
                data = request.data
            else:
                return Response({"error" : "Invalid parameters! Parameters are <id> and <external>"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except KeyError as ke:
            return Response({"error": "Invalid parameters!: {0}".format(str(ke))}, status=status.HTTP_406_NOT_ACCEPTABLE)
                
        try:
            _interface.delete_single_node(id, external)
            return Response({"message" : "Done"}, status=status.HTTP_202_ACCEPTED)
        except interface_errors.GraphNonExistElementError:
            return Response({"error" : "The given node does not exists"})
        
    return Response({"messsage" : "START"}, status=status.HTTP_501_NOT_IMPLEMENTED)

_logger_restapi_messages_single_edge = {
   'NNE': 'The requested node does not exist: {0}',
   'NET': 'The given edge type does not exist: {0}',
   'K/V': '{0} --> {1}',
   'EXC': 'Raised exception: {0}',
   'INV': 'The following JSON document is invalid for the {0} JSON Schema document: {1}',
   'CRE': 'The JSON Schema document is created',
   'NCO': 'The given RESTful call with PUT method does not contain any JSON document',
   'NGE': 'Invalid JSON document: graph_element has to be: {0}',
   'INP': 'Invalid parameter: The parameters have to be {0}'
   }  

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes(parser_classes=(JSONParser,))
def single_edge(request):
    _logger.info(_logger_messages['MET'].format('single_edge', request.method))
    _logger.info(_logger_messages['PAR'].format('single_edge', request.query_params))
    if request.method == 'GET':
        try:
            if len(request.query_params) in [2,3]:
                source_id = str(request.query_params['source_id'])
                target_id = str(request.query_params['target_id'])
                try:
                    type = str(request.query_params['type'])
                    all = False
                except KeyError:
                    all = True
            else:
                _logger.info(_logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)'))
                return Response({"error" : _logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except KeyError as ke:
            _logger.info(_logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)'))
            return Response({"error" : _logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        try:
            if all:
                retVal = _interface.get_single_edge_non_typed(source_id, target_id)
            else:
                retVal = _interface.get_single_edge_typed(source_id, target_id, type)
            _logger.debug(_logger_messages['RES'].format('single_edge',str(request.query_params), str(retVal)))
            return Response(json.dumps({"message" : retVal}))
        except interface_errors.GraphInterfaceException as grfie:
            _logger.exception(_logger_restapi_messages_single_edge['EXC'].format(str(grfie)))
        except interface_errors.GraphNonExistElementError:
            _logger.info(_logger_restapi_messages_single_edge['NNE'].format(str(request.query_params)))
            return Response({"error" : _logger_restapi_messages_single_edge['NNE'].format(str(request.query_params))}, status=status.HTTP_406_NOT_ACCEPTABLE)
        
    elif request.method == 'PUT':
        try:
            if len(request.query_params) == 2:
                project = str(request.query_params['project'])
                type = str(request.query_params['type'])
                if project.lower() in __UNACCESSABLE_PROJECTS:
                    return Response({"Unauthorised project"}, status=status.HTTP_403_FORBIDDEN)
                data = request.data
            else:
                _logger.info(_logger_restapi_messages_single_edge['INP'].format('<project> and <type>'))
                return Response({"error" : _logger_restapi_messages_single_edge['INP'].format('<project> and <type>')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except KeyError as ke:
            _logger.info(_logger_restapi_messages_single_edge['INP'].format('<project> and <type>'))
            return Response({"error" : _logger_restapi_messages_single_edge['INP'].format('<project> and <type>')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        try:
            is_valid = _validator.instance_validator(project, type, data)
            if is_valid:
                try:
                    retVal = _interface.insert_single_edge(project, type, data)
                    _logger.debug(_logger_messages['RES'].format('single_edge', str(request.query_params), str(retVal)))
                    return Response({"message":retVal}, status=status.HTTP_201_CREATED)
                except interface_errors.GraphInterfaceException as grfie:
                    _logger.exception(_logger_restapi_messages_single_edge['EXC'].format(str(grfie)))
        except FileNotFoundError:
            _logger.info(_logger_restapi_messages_single_edge['NET'].format(type))
            return Response({"error": _logger_restapi_messages_single_edge['NET'].format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except SchemaError:
            _logger.info(_logger_restapi_messages_single_edge['INV'].format(type, request.data))
            return Response({"error" : _logger_restapi_messages_single_edge['INV'].format(type, request.data)}, status=status.HTTP_406_NOT_ACCEPTABLE)
            
    elif request.method == 'DELETE':
        try:
            if len(request.query_params) in [2,3]:
                source_id = str(request.query_params['source_id'])
                target_id = str(request.query_params['target_id'])
                try:
                    type = str(request.query_params['type'])
                    all = False
                except KeyError:
                    all = True
            else:
                _logger.info(_logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)'))
                return Response({"error" : _logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except KeyError as ke:
            _logger.info(_logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)'))
            return Response({"error" : _logger_restapi_messages_single_edge['INP'].format('<source_id>, <target_id> and <tpye> (optional)')}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        try:
            if all:
                retVal = _interface.delete_single_edge_non_typed(source_id, target_id)
            else:
                retVal = _interface.delete_single_edge_typed(source_id, target_id, type)
            _logger.debug(_logger_messages['RES'].format('single_edge',str(request.query_params), str(retVal)))
            return Response(json.dumps({"message" : retVal}))
        except interface_errors.GraphNonExistElementError:
            _logger.info(_logger_restapi_messages_single_edge['NNE'].format(str(request.query_params)))
            return Response({"error" : _logger_restapi_messages_single_edge['NNE'].format(str(request.query_params))}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except interface_errors.GraphInterfaceException as grfie:
            _logger.exception(_logger_restapi_messages_single_edge['EXC'].format(str(grfie)))

@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes(parser_classes=(JSONParser,))
def batch_edge(request):
    if request.method == 'GET':
        return Response({"messsage" : "START"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    elif request.method == 'PUT':
        try:
            if len(request.query_params) == 2:
                project = request.query_params['project']
                type = request.query_params['type']
                data = request.data
            else:
                return Response({"error" : "Invalid parameters! Parameters are <project> and <type>"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except KeyError as ke:
            return Response({"error" : "Invalid parameters!: {0}".format(str(ke))}, status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            is_valid = _validator.instance_validator(project, type, data, 'batch_')
            if is_valid:
                try:
                    retVal = _interface.insert_bulk_edge(project, type, data)
                    return Response({"message":retVal}, status=status.HTTP_201_CREATED)
                except interface_errors.GraphExistElementError as neee:
                    return Response({"error":neee}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({"error" : "The given instance is invalid for {0} type".format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except FileNotFoundError as fnfe:
            return Response({"error": "{0} type is unknown, please upload it".format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except SchemaError as se:
            return Response({"error" : "Invalid instance. The instance is not valid for {0} JSONSchema document".format(type)}, status=status.HTTP_406_NOT_ACCEPTABLE)
            
        return Response({"messsage" : "START"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    elif request.method == 'DELETE':
        return Response({"messsage" : "START"}, status=status.HTTP_501_NOT_IMPLEMENTED)
    return Response({"messsage" : "START"}, status=status.HTTP_501_NOT_IMPLEMENTED)
