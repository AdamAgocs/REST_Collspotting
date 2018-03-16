'''
Created on 14 Jul 2017

@author: agocsi
'''

from django.conf.urls import url
from restful_module import views

#     url(r'^(?P<project>[A-Za-z0-9_]{5,})/(?P<file>[A-Za-z0-9_.]{8,})$', views.jsonschema_handler, name='jsonschema_handler'),
#     url(r'^(?P<project>[A-Za-z0-9_]{5,})', views.project_details, name='project_details'),

urlpatterns = [
    url(r'^single_node$', views.single_node, name='single_node'),
    url(r'^batch_node$', views.batch_node, name='batch_node'),
    url(r'^single_edge$', views.single_edge, name='single_edge'),
    url(r'^batch_edge$', views.batch_edge, name='batch_edge'),
#     url(r'^insert_node/$', views.insert_node, name='insert_node'),
#     url(r'^update_node/id=', views.update_node, name='update_node'),
#     url(r'^delete_node/id=', views.delete_node, name='delete_node'),
#     url(r'^insert_edge/$', views.insert_edge, name='insert_edge'),
#     url(r'^update_edge/id=', views.update_edge, name='update_edge'),
#     url(r'^delete_edge/id=', views.delete_edge, name='delete_edge'),
#     url(r'^bulk_insert_node/$', views.bulk_insert_node, name='bulk_insert_node'),
#     url(r'^bulk_update_node/id=', views.bulk_update_node, name='bulk_update_node'),
#     url(r'^bulk_delete_node/id=', views.bulk_delete_node, name='bulk_delete_node'),
#     url(r'^bulk_insert_edge/$', views.bulk_insert_edge, name='bulk_insert_edge'),
#     url(r'^bulk_update_edge/id=', views.bulk_update_edge, name='bulk_update_edge'),
#     url(r'^bulk_delete_edge/id=', views.bulk_delete_edge, name='bulk_delete_edge'),
#     url(r'^', views.add_user, name='add_user'),
#     url(r'^login/$', views.login, name='login'),
#     url(r'^logout/$', views.logout, name='logout'),
]