from .base import *
import logging.config

try:
    from .local import *
except ImportError:
    exit('User, fill in local.py, please!'
         '\nUse command: "cp settings/local.py.default settings/local.py"')

try:
    logging.config.dictConfig(LOGGING)
except NameError:
    exit('Define LOGGING in settings')
