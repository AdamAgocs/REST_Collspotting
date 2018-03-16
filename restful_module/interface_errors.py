'''
Created on 10 Jun 2017

@author: agocsi
'''

__all__ = ['GraphInterfaceException', 'GraphSyntaxError', 'GraphExistElementError', 
           'GraphNonExistElementError', 'GraphBadConnectionError']


class GraphInterfaceException(Exception):
    """
    Base class for all exceptions raised by this RESTfull API interface/module
    """


class GraphSyntaxError(GraphInterfaceException):
    """
    This exception is raised when an invalid input is sent
    """


class GraphExistElementError(GraphInterfaceException):
    """
    This exception is raised when an element (node or relationship) has to be created but the given element is already exist.
    Typically at insert_node, insert_edge, bulk_insert_node, bulk_insert_edge, bulk_insert RESTfull API calls. 
    """


class GraphNonExistElementError(GraphInterfaceException):
    """
    This exception is raised when an element (node or relationship) has to be changed or retrieved but the given element is not exist.
    Typically at update, delete and get type RESTfull API calls  
    """

class GraphBadConnectionError(GraphInterfaceException):
    """
    This exception is raised when an invalid connection parameters are given.
    """