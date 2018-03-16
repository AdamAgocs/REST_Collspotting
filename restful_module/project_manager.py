'''
Created on 20 Feb 2018

@author: agocsi
'''
from json import dump, load
from os.path import join, isdir, listdir
import logging

_logger = logging.getLogger(__name__)

class ProjectException(Exception):
    """
    This exception is raised when the project is invalid
    """


MAX_PROJECT = 10

class ProjectManager():
    def __init__(self):
        self.__projects = {}
        
    def is_exist(self, project_name):
        try:
            return self.__project[project_name]
        except KeyError:
            return False
    
    def create_project(self, project_name):
        if self.is_exist(project_name):
            return False
        try:
            project = Project()
            
        except ProjectException as pe:
            return False
    
    def select_project(self, project_name):
        if not self.is_exist(project_name):
            return False
        pass
    
    def get_descriptors(self, project_name_):
        _project = self.__projects.get(project_name_, None)
        if _project == None:
            return False
        return _project.get_descriptors()
    
class Project():
    def __init__(self, project_name_):
        self.__project_name = join(r'static', r'restful_module', project_name_)
        if not isdir(self.__project_name):
            raise ProjectException('Invalid project')
        
    def get_descriptors(self):
        retVal = {}
        filenames = listdir(self.__project_name)
        
        for filename in filenames:
            retVal[filename] = load(open(join(dir_name, filename), 'r', encoding='utf-8'))
        return retVal
    
    def save_descriptor(self, descriptor):
        