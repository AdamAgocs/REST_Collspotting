'''
Created on 14 Jul 2017

@author: agocsi
'''

from django.conf.urls import url
from restful_module import views

urlpatterns = [
     url(r'^(?P<project>[A-Za-z0-9_]{5,})/(?P<file>[A-Za-z0-9_.]{7,})$', views.descriptor_handler, name='descriptor_handler'),
     url(r'^(?P<project>[A-Za-z0-9_]{5,})$', views.project, name='project'),
]
    