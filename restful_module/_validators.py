'''
Created on 30 Jun 2017

@author: agocsi
'''

from jsonschema.exceptions import ValidationError


def string_set_requirement_collspotting(validator, string_set_requirement, instance, schema):
    if not validator.is_type(instance, "array"):
        return
    
    for instance_element in instance:
        if not isinstance(instance_element, str):
            yield ValidationError('%r is not a string property', instance_element) 

    for requirement in string_set_requirement:
        if instance.count(requirement) == 0:
            yield ValidationError('%r is a required string property', requirement)
        
        
    