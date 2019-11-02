import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from device_driver import cisco, juniper
from datetime import datetime

def backup_process(x):
    current_dir = os.getcwd()
    config_dir = current_dir+'/config_data'
    access_method = x['access_info']['method']
    cred = {
            'ip' : x['ip_mgmt'],
            'device_type' : x['vendor'],
            'username' : x['access_info']['username'],
            'password' : x['access_info']['password'],
            'secret' : x['access_info']['secret'],
            'hostname' : x['hostname']
            }
    if x.get('name') != None:
        name = x['name']
    else:
        name = x['hostname']+'_'+str(datetime.now().strftime("%Y%m%d%H%M%S"))
    config_path = config_dir+'/'+name
    if cred['device_type'] == 'Cisco' and access_method == 'SSH':
        cred['device_type'] = 'cisco_ios'
        try:
            conn = cisco.ConfigSSH(**cred)
            backup = conn.backup()

        except Exception as msg:
            return {
                'hostname' : x['hostname'],
                'status' : 'FAILED',
                'debug' : str(msg)}

    elif cred['device_type'] == 'Juniper' and access_method == 'SSH':
        cred['device_type'] = 'juniper_junos'
        try:
            conn = juniper.ConfigSSH(**cred)
            backup = conn.backup()

        except Exception as msg:
            return {
                'hostname' : x['hostname'],
                'status' : 'FAILED',
                'debug' : str(msg)}

    elif cred['device_type'] == 'Cisco' and access_method == 'TELNET':
        try:
            conn = cisco.ConfigTelnet(**cred)
            backup = conn.backup()

        except Exception as msg:
            return {
                'hostname' : x['hostname'],
                'status' : 'FAILED',
                'debug' : str(msg)}

    elif cred['device_type'] == 'Juniper' and access_method == 'TELNET':
        try:
            conn = juniper.ConfigTelnet(**cred)
            backup = conn.backup()

        except Exception as msg:
            return {
                'hostname' : x['hostname'],
                'status' : 'FAILED',
                'debug' : str(msg)}

    with open(config_path, 'w') as f:
        f.write(backup)

    result = {
            'name' : name,
            'hostname' : x['hostname'],
            'vendor' : x['vendor'],
            'config_path' : config_path,
            'timestamp' : str(datetime.now().strftime('%Y/%m/%d-%H:%M:%S')),
            'status': 'SUCCESS'
            }
    return {'status': 'SUCCESS', 'hostname': x['hostname'], 'result': result, 'debug': '-'}

def restore_process(x):
    cred = {
            'ip' : x['ip_mgmt'],
            'device_type' : x['vendor'],
            'username' : x['access_info']['username'],
            'password' : x['access_info']['password'],
            'secret' : x['access_info']['secret'],
            'hostname' : x['hostname']
            }
    access_method = x['access_info']['method']
    config = None
    with open(x['config']['config_path'], 'r') as f:
        config = f.read()

    if cred['device_type'] == 'Cisco' and access_method == 'SSH':
        cred['device_type'] = 'cisco_ios'
        try:
            conn = cisco.ConfigSSH(**cred)
            restore_result = conn.restore(config)

        except Exception as msg:
            return {'status' : 'FAILED','debug' : str(msg)}

    elif cred['device_type'] == 'Juniper' and access_method == 'SSH':
        cred['device_type'] = 'juniper_junos'
        try:
            conn = juniper.ConfigSSH(**cred)
            restore_result = conn.restore(config)

        except Exception as msg:
            return {'status' : 'FAILED','debug' : str(msg)}

    elif cred['device_type'] == 'Cisco' and access_method == 'TELNET':
        try:
            conn = cisco.ConfigTelnet(**cred)
            restore_result = conn.restore(config)

        except Exception as msg:
            return {'status' : 'FAILED','debug' : str(msg)}

    elif cred['device_type'] == 'Juniper' and access_method == 'TELNET':
        try:
            conn = juniper.ConfigTelnet(**cred)
            restore_result = conn.restore(config)

        except Exception as msg:
            return {'status': 'FAILED', 'debug': str(msg)}
    return {'status': 'SUCCESS', 'debug': '-'}
