'''
Created on 1 Jul 2017

@author: agocsi
'''


'''
Created on 6 Jun 2017

@author: agocsi
'''

from abc import ABCMeta, abstractmethod
from py2neo import Graph
from py2neo.error import GraphError
from restful_module import interface_errors
from string import Template
from urllib.parse import urlparse
import json
import logging
from functools import wraps


from py2neo.packages.httpstream import http
http.socket_timeout = 9999


#logger
_logger = logging.getLogger(__name__)

class GraphInterface(metaclass=ABCMeta):

    @abstractmethod
    def insert_single_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def delete_single_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def get_single_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')

    @abstractmethod
    def insert_single_edge(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')

    @abstractmethod
    def get_single_edge_typed(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def get_single_edge_non_typed(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def delete_single_edge_typed(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def delete_single_edge_non_typed(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def get_bulk_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def insert_bulk_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def delete_bulk_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def insert_bulk_edge(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def insert_meta_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def delete_meta_node(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def insert_meta_edge(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    @abstractmethod
    def insert_constraint(self, *args, **kwargs):
        raise interface_errors.GraphInterfaceException('Non-implemented functionality')
    
    
    
class Neo4jInterface(GraphInterface):
    __templates = {
        'single_node': {
            'delete': Template(
                'MATCH (n) WHERE n.id = "$id_" DELETE n RETURN id(n) AS id'),
            'get': Template(
                'MATCH (n) WHERE n.id="$id_" RETURN n AS node'),
            'insert': Template('MERGE (n:$label_$attr_) RETURN id(n) AS id'),
        },
        'bulk_node': {
            'insert': Template('MERGE (n:$label_$attr_) RETURN id(n) AS id'),
            'get': {
                'all': 'MATCH (n:$label_) RETURN n AS node',
                'non-all': 'MATCH (n:$label_) WHERE n.id IN $ids_ RETURN n AS node'
            },
            'delete': {
                'all': 'MATCH (n:$label_) DELETE n RETURN n.id AS id',
                'non-all': 'MATCH (n:$label_) WHERE n.id IN $ids_ DELETE n RETURN n.id AS id'
            }
        },
        'single_edge': {
            'delete': {
                'non-typed': Template(
                    'MATCH (a)-[r]->(b) WHERE a.id="$source_id_" AND b.id"$target_id_" AND NOT(TYPE(r) STARTS WITH "REVERSE_") DELETE r WITH a, b, COLLECT(r) AS collection MATCH (a)<-[r1]-(b) WHERE (TYPE(r1) STARTS WITH "REVERSE_") RETURN collection'
                ),
                'typed': Template(
                    'MATCH (a)-[r:$edge_label_]->(b) WHERE a.id="$source_id_" AND b.id"$target_id_" DELETE r WITH a, b, r AS edge_id MATCH (a)<-[r1:REVERSE_$edge_label_]-(b) DELETE r1 RETURN edge_id AS id'
                ),
            },
            'insert': {
                'single': Template(
                    'MATCH (a:$source_label_{id:"$source_id_"}) MATCH (b:$target_label_{id:"$target_id_"}) MERGE (a)-[r:$edge_label_$attr_]->(b) RETURN id(r) AS id'),
                'double': Template(
                    'MATCH (a:$source_label_{id:"$source_id_"}) MATCH (b:$target_label_{id:"$target_id_"}) MERGE (a)-[r:$edge_label_$attr_]->(b) MERGE (a)<-[r1:REVERSE_$edge_label_$attr_]-(b) RETURN id(r) AS id'),
            },
            'get': {
                'typed': Template(
                    'MATCH (a)-[r:$edge_label_]->(b) WHERE a.id="$source_id_" AND b.id="$target_id_" RETURN r AS edge'),
                'non-typed': Template(
                    'MATCH (a)-[r]->(b) WHERE a.id="$source_id_" AND b.id="$target_id_" AND not(type(r) STARTS WITH "REVERSE_") RETURN r AS edge'),
            },
        },
        'bulk_edge' : {
            'insert': {
                'single': Template(
                    'MATCH (a:$source_label_{id:"$source_id_"}) MATCH (b:$target_label_{id:"$target_id_"}) MERGE (a)-[r:$edge_label_]->(b) RETURN id(r) AS id'),
                'double': Template(
                    'MATCH (a:$source_label_{id:"$source_id_"}) MATCH (b:$target_label_{id:"$target_id_"}) MERGE (a)-[r:$edge_label_]->(b) MERGE (a)<-[r1:REVERSE_$edge_label_]-(b) RETURN id(r) as id'),
            },
        },
        'ontology': {
            'delete': {
                'edge': Template(
                    'MATCH (a:ontology:$project_{title:"$title_a_"})-[r:$edge_label_]->(b:ontology:$project_{title:"$title_b_"}) DELETE r RETURN id(r) AS id'),
                'isa': Template(
                    'START n=Node($id_) MATCH (n)-[r:ISA]->(o:ontology) WHERE o.title IN $title_list_ DELETE r'),
                'node': Template(
                    'MATCH (n:ontology:$project_)-[r]-() WHERE n.title = "$title_" DELETE r, n RETURN id(n) AS id'),
            },
            'insert': {
                'edge': Template(
                    'MATCH (a:ontology:$project_{title:"$title_a_"}) MATCH (b:ontology:$project_{title:"$title_b_"}) CREATE (a)-[r:$edge_label_]->(b) RETURN id(r) AS id'),
                'isa': Template(
                    'START n=Node($id_) MATCH (o:ontology:$project_) WHERE o.title IN $title_list_ CREATE (n)-[:ISA]->(o)'),
                'node': Template(
                    'CREATE (n:ontology:$project_{title:"$title_"}) RETURN id(n) AS id'),
            },
            'get': {
                'node': Template(
                    'MATCH (n:ontology:$project_) WHERE n.title = "$title_" RETURN id(n) AS id'),
                'parent': Template(
                    'START n=Node($id_) MATCH (n)-[:ISA]->(o) RETURN COLLECT(o.title) AS titles'),
                'ancestor': Template(
                    'MATCH (a:ontology:$project_{title:"$title_"})-[:ISA*]->(b:ontology) RETURN COLLECT(b.title) AS collection'),
                'edge': Template(
                    'MATCH (a:ontology:$project_)-[r:$edge_label_]->(b:ontology:$project_) RETURN a.title AS source_label, b.title AS target_label, EXISTS((a)<-[:REVERSE_$edge_label_]-(b)) AS isdoubled')
            }
        },
        'util' : {
            'constraint' : Template(
                'CREATE CONSTRAINT ON (a:$label_) ASSERT a.id IS UNIQUE')
        }
    }

    __logger_messages = {
        'STMT' : 'The {0} function sent the following statements to the database: {1}',
        'BEG' : 'The {0} function is called with the following parameters: {1} and {2}',
        'END' : 'The {0} function is finished properly with the following result: {1}',
        'EXC' : 'The {0} function raised the following exception: {1}' 
        }

    
    def __init__(self, graph_db):
        self.ontology_operations = {
                            'node' : self.insert_meta_node,
                            'edge' : self.insert_meta_edge,
                           }        
        if isinstance(graph_db, Graph):
            self.graph_db = graph_db
        else:
            raise interface_errors.GraphBadConnectionError('There is no connection to the given Neo4j database')

    @staticmethod
    def converter(dict_, prefix_, connector_, join_element_, parenthesis_):
        template_format = Template('$prefix_{0} $connector_ {1}')
        elements = []
        for key in dict_:
            elements.append(template_format.substitute(prefix_=prefix_, connector_=connector_).format(
                key, json.dumps(dict_[key])))
        return parenthesis_[0] + join_element_.join(elements) + parenthesis_[1]
    
    @staticmethod
    def node_to_dict(node):
        retVal = dict(node.properties)
        retVal['neo_id'] = node._id
        retVal['label'] = sorted(list(node.labels)) if len(node.labels) > 1 else node.labels.pop()
        return retVal

    def __transaction_phase(method):  # @DontTrace
        @wraps(method)
        def decorated_function(self, *args, **kwargs):
            try:
                method(self, *args, **kwargs)
                self.__line_breaker(_logger.info, self.__logger_messages['STMT'].format(method.__name__, self.__tx.statements))
                retVal = self.__tx.process()
            except Exception as ee:
                _logger.exception(self.__logger_messages['EXC'].format(method.__name__, str(ee)))
                self.__tx.rollback()
                raise ee
            
            return retVal
        return decorated_function
    
    def __line_breaker(self, func, text, length = 192, maxIter = 1):
        i = 0
        iter = 0
        while i < len(text) and iter < maxIter:
            func(text[i:i+length])
            i += length
            iter += 1
    
    def __transaction(method):  # @DontTrace
        @wraps(method)
        def decorated_function_begin(self, *args, **kwargs):
            self.__line_breaker(_logger.info, self.__logger_messages['BEG'].format(method.__name__, str(args), str(kwargs)))

            try:
                self.__tx = self.graph_db.cypher.begin()
                retVal = method(self, *args, **kwargs)
            except (interface_errors.GraphExistElementError, interface_errors.GraphNonExistElementError) as expe:
                raise expe
            except Exception as ee:
                _logger.exception(self.__logger_messages['EXC'].format(method.__name__, str(ee)))
                raise ee
            finally:
                self.__tx.commit()
                
            self.__line_breaker(_logger.info, self.__logger_messages['END'].format(method.__name__, retVal))
            return retVal
        return decorated_function_begin

    @__transaction
    def insert_single_node(self, project, type, node):
        try:
            onto_parents = self.__get_ontology_parents(project, type)[0][0]['collection']
            onto_parents.append(type)
        except IndexError:
            onto_parents = [type,]
        
        labels = ":".join(onto_parents)
        attributes = self.converter(
            dict_=node, prefix_='', connector_=':', join_element_=', ', parenthesis_=['{', '}'])

        try:
            retVal = int(self.__insert_node(label_=labels, attributes_=attributes)[0][0]['id'])
        except (GraphError, IndexError) as gie:
            raise interface_errors.GraphInterfaceException('Unexpected Error: {}'.format(str(gie)))
        
        return retVal
    
    @__transaction_phase
    def __get_ontology_parents(self, project, title):
        self.__tx.append(self.__templates['ontology']['get']['ancestor'].substitute(project_=project, title_=title))
    
    @__transaction_phase
    def __insert_node(self, label_, attributes_):
        self.__tx.append(self.__templates['single_node']['insert'].substitute(label_=label_, attr_=attributes_))
    
    
    @__transaction
    def delete_single_node(self, id):
        try:
            return self.__delete_node(id)[0][0]['id']
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException(str(ge))
        except IndexError as ie:
            raise interface_errors.GraphNonExistElementError('Node does not exist')

    @__transaction_phase
    def __delete_node(self, id):
        self.__tx.append(self.__templates['single_node']['delete'].substitute(id_=id))

    @__transaction
    def get_single_node(self, id):
        try:
            return self.__get_node(id)[0][0]['node'].properties
        except GraphError:
            raise interface_errors.GraphNonExistElementError("The given node does not exist: {0}".format(id))
        
    @__transaction_phase
    def __get_node(self, id):
        self.__tx.append(self.__templates['single_node']['get'].substitute(id_=id))

    @__transaction
    def insert_single_edge(self, project, type, edge):
        try:
            retVal = self.__get_edge_parameters(project, type)[0][0]
            source_label = retVal['source_label']
            target_label = retVal['target_label']
            is_doubled = retVal['isdoubled']
        except IndexError:
            raise interface_errors.GraphNonExistElementError('It is strange, the validator does not work')
        
        source_id = edge.pop('source_id')
        target_id = edge.pop('target_id')
        attributes = self.converter(
            dict_=edge, prefix_='', connector_=':', join_element_=', ', parenthesis_=['{', '}'])
        
        try:
            return self.__insert_edge(source_id, source_label, target_id, target_label, type, attributes, is_doubled)[0][0]['id']
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException('Unexpected exception occurred. The exception: {}'.format(str(ge)))
        
    @__transaction_phase
    def __get_edge_parameters(self, project, edge_label):
        self.__tx.append(self.__templates['ontology']['get']['edge'].substitute(project_=project, edge_label_=edge_label))

    @__transaction_phase
    def __insert_edge(self, source_id, source_label, target_id, target_label, edge_label, attributes, is_doubled):
        used_func = self.__templates['single_edge']['insert']['double'] if is_doubled else self.__templates['single_edge']['insert']['single']
        self.__tx.append(used_func.substitute(source_label_=source_label, source_id_=source_id, target_label_=target_label, target_id_=target_id, edge_label_=edge_label, attr_=attributes))

    @__transaction
    def get_single_edge_typed(self, source_id, target_id, type):
        try:
            return self.__get_single_edge(source_id, target_id, type)[0][0]['edge'].properties

        except GraphError:
            raise interface_errors.GraphInterfaceException('Unexpected error')
        except IndexError:
            raise interface_errors.GraphNonExistElementError('The given edge does not exist')
        
    @__transaction
    def get_single_edge_non_typed(self, source_id, target_id):
        try:
            result = self.__get_single_edge(source_id, target_id, None)[0]
            retVal = []
            for res in result:
                retVal.append(res['node'].properties)
            
            return retVal
        except GraphError:
            raise interface_errors.GraphInterfaceException('Unexpected error')
        except IndexError:
            raise interface_errors.GraphNonExistElementError('The given edge does not exist')
        
    @__transaction_phase
    def __get_single_edge(self, source_id, target_id, type):
        if type == None:
            self.__tx.append(self.__templates['single_edge']['get']['non-typed'].substitute(source_id_=source_id, target_id_=target_id))
        else:
            self.__tx.append(self.__templates['single_edge']['get']['typed'].substitute(source_id_=source_id, target_id_=target_id, edge_label_=type))
        
    @__transaction
    def delete_single_edge_typed(self, source_id, target_id, type):
        try:
            return self.__delete_single_edge(source_id, target_id, type)[0][0]['id']
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException('Unexpected error: {0}'.format(str(ge)))
        except IndexError:
            raise interface_errors.GraphNonExistElementError('The given edge does not exist')
    
    @__transaction
    def delete_single_edge_non_typed(self, source_id, target_id):
        try:
            return self.__delete_single_edge(source_id, target_id, None)[0][0]['collection']
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException('Unexpected error: {0}'.format(str(ge)))
        except IndexError:
            raise interface_errors.GraphNonExistElementError('The given edge does not exist')
    
    @__transaction_phase
    def __delete_single_edge(self, source_id, target_id, type):
        if type == None:
            self.__tx.append(self.__templates['single_edge']['delete']['non-typed'].substitute(source_id_=source_id, target_id_=target_id))
        else:
            self.__tx.append(self.__templates['single_edge']['delete']['typed'].substitute(source_id_=source_id, edge_label_=type, target_id_=target_id))
    
    
    @__transaction    
    def insert_meta_node(self, project, node):
        no_parents = False
        is_new = False
        current_parents = []
        try:
            parents = set([urlparse(x['$ref']).path.split('/')[-1].split('.')[0].strip() for x in node['parents']])
        except KeyError:
            no_parents = True
            
        title = urlparse(node['id']).path.split('/')[-1].split('.')[0].strip()
        try:
            id = self.__get_ontology_node(project, title)[0][0]['id']
            
        except IndexError:
            id = -1
        except Exception as ee:
            raise ee
        
        if id == -1:
            id = self.__add_ontology_node(project, title)[0][0]['id']
            is_new = True
        elif not no_parents:
            current_parents = self.__get_ontology_parent_nodes(id)[0][0]['titles']
            removable = list(set(current_parents).difference(parents))
            if len(removable) != 0:
                self.__remove_isa(id, removable)

        if not no_parents:      
            self.__add_isa(project, id, list(parents.difference(set(current_parents))))
        return (is_new, title)
                        
    @__transaction
    def insert_constraint(self, label):
        self.__add_constraint(label)
        
    @__transaction_phase
    def __add_constraint(self, label):
        self.__tx.append(self.__templates['util']['constraint'].substitute(label_=label))
    
    @__transaction_phase
    def __get_ontology_node(self, project, title):
        self.__tx.append(self.__templates['ontology']['get']['node'].substitute(project_=project, title_=title))
        
    @__transaction_phase
    def __add_ontology_node(self, project, title):
        self.__tx.append(self.__templates['ontology']['insert']['node'].substitute(project_=project, title_=title))
    
    @__transaction_phase
    def __get_ontology_parent_nodes(self, id):
        self.__tx.append(self.__templates['ontology']['get']['parent'].substitute(id_=id))
    
    @__transaction_phase
    def __add_isa(self, project, child_id, parents_titles):
        self.__tx.append(self.__templates['ontology']['insert']['isa'].substitute(id_=child_id, project_=project, title_list_=parents_titles))
    
    @__transaction_phase
    def __remove_isa(self, child_id, parents_titles):
        self.__tx.append(self.__templates['ontology']['delete']['isa'].substitute(id_=child_id, title_list_=parents_titles))
    
    @__transaction
    def delete_meta_node(self, project, title):
        try:
            return self.__delete_ontology_node(project, title)[0][0]['id']
        except (GraphError, KeyError, IndexError):
            raise interface_errors.GraphNonExistElementError('The requested node is not exist')

    @__transaction_phase
    def __delete_ontology_node(self, project, title):
        self.__tx.append(self.__templates['ontology']['delete']['node'].substitute(project_=project, title_=title))
   
    @__transaction
    def insert_meta_edge(self, project, edge):
        edge_label = urlparse(edge['id']).path.split('/')[-1].split('.')[0].strip()
        new_source_title = urlparse(edge['source_label']['$ref']).path.split('/')[-1].split('.')[0].strip()
        new_target_title = urlparse(edge['target_label']['$ref']).path.split('/')[-1].split('.')[0].strip()

        result = self.__get_edge_parameters(project, edge_label)
        if len(result[0]) == 1:
            source_title, target_title = result[0][0]['source_label'], result[0][0]['target_label']
            if source_title != new_source_title or target_title != new_source_title:
                self.__delete_one_direction_ontology_edge(project, source_title, target_title, edge_label)
                self.__delete_one_direction_ontology_edge(project, target_title, source_title, "REVERSE_"+edge_label)                
        elif len(result[0]) == 0:
            pass
        
        self.__add_one_direction_ontology_edge(project, new_source_title, new_target_title, edge_label)
        if edge['direction'] == "double":
            self.__add_one_direction_ontology_edge(project, new_target_title, new_source_title, 'REVERSE_'+edge_label)
        
    @__transaction_phase
    def __delete_one_direction_ontology_edge(self, project, source_title, target_title, edge_label):
        self.__tx.append(self.__templates['ontology']['delete']['edge'].substitute(project_=project, title_a_=source_title, edge_label_=edge_label, title_b_=target_title))
    
    @__transaction_phase
    def __add_one_direction_ontology_edge(self, project, source_title, target_title, edge_label):
        self.__tx.append(self.__templates['ontology']['insert']['edge'].substitute(project_=project, title_a_=source_title, edge_label_=edge_label, title_b_=target_title))
    
    @__transaction
    def get_bulk_node(self, type, list_of_node_ids):
        retVal = []
        try:
            result = self.__get_bulk_node(type, list_of_node_ids)[0]
            
            for res in result:
                retVal.append(res['node'].properties)
            return retVal
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException("Unexpected error. The exception is {0}".format(str(ge)))
        except IndexError:
            raise interface_errors.GraphNonExistElementError('The requested graph nodes do not exist')
        
    @__transaction_phase
    def __get_bulk_node(self, type, list_of_node_ids):
        if list_of_node_ids == None:
            self._tx.append(self.__templates['bulk_node']['get']['all'].substitute(label_=type))
        else:
            self._tx.append(self.__templates['bulk_node']['get']['non-all'].substitute(label_=type, ids_=list_of_node_ids))

    @__transaction
    def insert_bulk_node(self, project, type, nodes):
        try:
            onto_parents = self.__get_ontology_parents(project, type)[0][0]['collection']
            onto_parents.append(type)
        except IndexError:
            onto_parents = [type,] 
        
        labels = ":".join(onto_parents)
        list_of_attributes = []
        
        for node in nodes: 
            list_of_attributes.append(self.converter(
               dict_=node, prefix_='', connector_=':', join_element_=', ', parenthesis_=['{', '}']))
        try:
            i = 0
            retVal = [] 

            while i < len(list_of_attributes):
                result = self.__insert_bulk_node(labels, list_of_attributes[i:i+10000])
                for res in result[0]:
                    retVal.append(int(res['id']))
                i += 10000
                print(i)

            return retVal
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException('Unexpected error! The exception is {0}'.format(str(ge)))

    @__transaction_phase
    def __insert_bulk_node(self, label, list_of_attributes):
        for attributes in list_of_attributes:
            self.__tx.append(self.__templates['single_node']['insert'].substitute(label_=label, attr_=attributes))
            
            
    @__transaction
    def delete_bulk_node(self, type, list_of_ids):
        retVal = []
        try:
            result = self.__delete_bulk_node(type, list_of_ids)[0]
            
            for res in result:
                retVal.append(res['id'])
            return retVal
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException("Unexpected error. The exception is {0}".format(str(ge)))
            #It is always raised when a node has, at least, one edge
              
        except IndexError:
            raise interface_errors.GraphNonExistElementError('The requested graph nodes do not exist')
    
    @__transaction
    def __delete_bulk_node(self, type, list_of_node_ids):
        if list_of_node_ids == None:
            self._tx.append(self.__templates['bulk_node']['delete']['all'].substitute(label_=type))
        else:
            self._tx.append(self.__templates['bulk_node']['delete']['non-all'].substitute(label_=type, ids_=list_of_node_ids))      
        
    @__transaction
    def insert_bulk_edge(self, project, type, list_of_edges):
        retVal = self.__get_edge_parameters(project, type)[0][0]

        source_label = retVal['source_label']
        target_label = retVal['target_label']
        is_doubled = retVal['isdoubled']
        
        retVal = []
        try:
            i = 0
            while i < len(list_of_edges):
                result = self.__insert_bulk_edge(source_label, target_label, type, is_doubled, list_of_edges[i:i+10000])[0]
                for res in result:
                    retVal.append(res['id'])
                i += 10000
                print(i)
                
            return retVal
        except IndexError as ie:
            raise interface_errors.GraphSyntaxError(str(ie))
        except GraphError as ge:
            raise interface_errors.GraphInterfaceException("Unexpected error. The exception is {0}".format(str(ge)))

    @__transaction_phase
    def __insert_bulk_edge(self, source_label, target_label, edge_label, is_doubled, list_of_edges):
        used_func = self.__templates['bulk_edge']['insert']['double'] if is_doubled else self.__templates['bulk_edge']['insert']['single']
#         if is_doubled:
        for edge in list_of_edges:
            self.__tx.append(used_func.substitute(source_label_=source_label, source_id_=edge['source_id'], target_label_=target_label, target_id_=edge['target_id'], edge_label_=edge_label))