import os

class DevelopmentConfig(object):
    # DB settings
    DB_COLLECTION = 'cloud_nms'
    DB_SERVER = '192.168.100.145'
    DB_PORT = 27017
    DB_USERNAME = 'jawdat'
    DB_PASSWORD = 'jawdat123'

class LocalConfig(object):
    # DB settings
    DB_COLLECTION = 'cloud_nms'
    DB_SERVER = 'localhost'
    DB_PORT = 27017
    DB_USERNAME = 'jawdat'
    DB_PASSWORD = 'jawdat123'

class JawdatPublic(object):
    # DB settings
    DB_COLLECTION = 'cloud_nms'
    DB_SERVER = '158.140.190.214'
    DB_PORT = 27017
    DB_USERNAME = 'jawdat'
    DB_PASSWORD = 'jawdat123'