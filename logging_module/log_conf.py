'''
Created on 28 May 2015

@author: agocsi
'''

import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
#     'filters': {
#         'special': {
#             '()': 'logging.SpecialFilter',
#             'foo': 'bar',
#         }
#     },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
#             'filters': ['special']
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'logging_module\Application_layer.log'
        },
        'file2' : {
            'level' : 'INFO',
            'class' : 'logging.FileHandler',
            'formatter' : 'verbose',
            'filename' : 'logging_module\Transactions.log'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null', 'file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'restful_module' : {
           'handlers' : ['console', 'file'],
           'level' : 'DEBUG',
           'propagate' : True
        },
        'restful_module.interface' : {
            'handlers' : ['file2'],
            'level' : 'DEBUG',
            'propagate' : True
        },
    }
}