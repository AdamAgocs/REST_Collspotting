'''
Created on 1 Jul 2017

@author: agocsi
'''

import json
import jsonschema
from restful_module._validators import string_set_requirement_collspotting
from os.path import join
from builtins import classmethod
from string import Template
from urllib.parse import urlparse

class JSONSchemaMetaSchemaValidator():
    original_schema = None
    extended_schema = None
    node_schema = None
    edge_schema = None
    single_validators = {}
    reverse_single_validators = {}
    MAX_SINGLE_VALIDATORS = 10
    
    def __init__(self):
        JSONSchemaMetaSchemaValidator.current_single_validators = 0
        
        JSONSchemaMetaSchemaValidator.node_keys = ['id', '$schema', 'properties', 'graph_element', 'title', 'type', 'required']
        JSONSchemaMetaSchemaValidator.edge_keys = ['id', '$schema', 'properties', 'graph_element', 'title', 'type', 'required', 'target_label', 'source_label', 'direction']
        
        if JSONSchemaMetaSchemaValidator.original_schema == None:
            JSONSchemaMetaSchemaValidator.original_schema = self.__init_original_schema({}, 'draft4')
        if JSONSchemaMetaSchemaValidator.extended_schema == None:
            JSONSchemaMetaSchemaValidator.extended_schema = self.__init_original_schema({u'string_set_requirement': string_set_requirement_collspotting}, 'collspotting_ext')
        if JSONSchemaMetaSchemaValidator.node_schema == None:
            JSONSchemaMetaSchemaValidator.node_schema = self.__init_graph_element_schema(JSONSchemaMetaSchemaValidator.__schema_loader(
                 join(r'validators', r'node_validator.json')), JSONSchemaMetaSchemaValidator.extended_schema.VALIDATORS, "collspotting_node")
        if JSONSchemaMetaSchemaValidator.edge_schema == None:
            JSONSchemaMetaSchemaValidator.edge_schema = self.__init_graph_element_schema(JSONSchemaMetaSchemaValidator.__schema_loader(
                join(r'validators', r'edge_validator.json')), JSONSchemaMetaSchemaValidator.original_schema.VALIDATORS, "collspotting_edge")
            
        JSONSchemaMetaSchemaValidator.validators = {'node': self.node_validate,
                           'edge': self.edge_validate}

    def __init_original_schema(self, validators, version):
        validator = jsonschema.Draft4Validator
        if len(validators.values()) > 0:
            validator = jsonschema.validators.extend(validator, validators, version)
        return validator

    def __init_graph_element_schema(self, meta_schema, validators, version):
        return jsonschema.validators.create(meta_schema, validators, version)

    @classmethod
    def __schema_loader(cls, path):
        return json.load(open(join(r'static', r'restful_module', path), 'r', encoding='utf-8'))

    @classmethod
    def node_validate(cls, project, input):
        try:
            for key in cls.node_keys:
                input[key]
        except KeyError as ke:
            raise ke
        
        try:
            cls.original_schema.check_schema(input)
            cls.extended_schema.check_schema(input)
            cls.node_schema.check_schema(input)
            
            cls.create_node_batch_validator(project, input)
            
        except jsonschema.exceptions.SchemaError as se:
            raise se
        return True
    
    @classmethod
    def create_node_batch_validator(cls, project, node):
        with open(join(r'static', r'restful_module', r'validators', r'template', r'template_node_batch.json'), 'r', encoding='utf-8') as file:
            data = file.read()
        
        id = urlparse(node['id']).path.split('/')[-1].split('.')[0].strip()
        template = Template(data)
        
        with open(join(r'static', r'restful_module', project, 'batch_'+id+'.json'), 'w', encoding='utf-8') as file:
            file.write(template.substitute(project_=project, node_=id, node_title_=node['title']))            

    @classmethod
    def edge_validate(cls, project, input):
        try:
            for key in cls.edge_keys:
                input[key]
        except KeyError as ke:
            raise ke

        try:
            cls.original_schema.check_schema(input)
            cls.extended_schema.check_schema(input)
            cls.edge_schema.check_schema(input)
            
            cls.create_edge_batch_validator(project, input)
        except jsonschema.exceptions.SchemaError as se:
            raise se
        return True

    @classmethod
    def create_edge_batch_validator(cls, project, edge):
        with open(join(r'static', r'restful_module', r'validators', r'template', r'template_edge_batch.json'), 'r', encoding='utf-8') as file:
            data = file.read()
        
        id = urlparse(edge['id']).path.split('/')[-1].split('.')[0].strip()
        template = Template(data)
        
        with open(join(r'static', r'restful_module', project, 'batch_'+id+'.json'), 'w', encoding='utf-8') as file:
            file.write(template.substitute(project_=project, edge_=id, edge_title_=edge['title']))  
    
    @classmethod
    def instance_validator(cls, project, type, instance, validator_type = ''):
        type = validator_type + type
        try:
            jsonschema.validate(instance, cls.single_validators[join(project, type)][0])
        except KeyError:
            try:
                cls.single_validators[join(project, type)] = (cls.__schema_loader(join(project, type+'.json')), cls.current_single_validators)
            except FileNotFoundError as fnfe:
                raise fnfe
            cls.reverse_single_validators[cls.current_single_validators] = join(project, type)
            cls.current_single_validators += 1
            if len(cls.single_validators) > cls.MAX_SINGLE_VALIDATORS:
                first_validator = cls.reverse_single_validators.pop(min(cls.reverse_single_validators.keys()))
                cls.single_validators.pop(first_validator)
            try:
                jsonschema.validate(instance, cls.single_validators[join(project, type)][0])
            except (jsonschema.SchemaError, jsonschema.ValidationError, Exception) as ee:
                raise ee
        except (jsonschema.ValidationError, Exception) as ee:
            raise ee
        
        return True    
