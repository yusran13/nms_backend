from netmiko import ConnectHandler
from telnetlib import Telnet
import time
class CiscoDriver:
    def __init__ (self, device, logger):
        self.device = device
        self.logger = logger

        if self.device["method"] == "SSH":
            self.device["device_type"] = "cisco_ios"
        elif self.device["method"] == "TELNET":
            self.device["device_type"] = "cisco_ios_telnet"

        del self.device["vendor"]
        del self.device["method"]


    def connect_remote(self):
        try:
            net_connect = ConnectHandler(**self.device)
            if net_connect:
                self.logger.info("Connection establish to device {:s}".format(self.device["ip"]))
            else:
                self.logger.warning("Can't connect to device {:s}".format(self.device["ip"]))
            return net_connect
        except:
            self.logger.warning("Can't connect to device {:s}".format(self.device["ip"]))
            return False

    #return ping in millisecond
    def ping_result(self, net_connect, ping_command):
        net_connect.enable()
        self.logger.info("Trying " + ping_command)
        output = net_connect.send_command(ping_command)
        if "....." in output:
           self.logger.warning("PING RTO..!!!")
           average_ping = None

        elif "Invalid source address- IP address" in output:
            self.logger.warning("WRONG SOURCE IP!!!")
            average_ping = None
        else:
            self.logger.info("PING Success....")
            ping_response = output.split("=")
            all_ping = ping_response[1].split("/")
            average_ping = all_ping[1]

        if average_ping:
            return float(average_ping)
        else:
            return average_ping

class ConfigTelnet:
    def __init__(self, ip, username, password, secret, device_type, hostname):
        credential = {
                'ip' : ip,
                'username' : username,
                'password' : password,
                'device_type' : device_type,
                'hostname' : hostname,
                'secret' : secret
                }

        self.credential = credential
        self.telnet = Telnet(credential['ip'])
        self.cisco_prompt = credential['hostname']+'#'
        self.cisco_init()
    def cisco_init(self):
        userpass = self.credential['username']+'\n'+self.credential['password']+'\n'
        enable = 'en'+'\n'+self.credential['secret']+'\n'
        self.telnet.read_until(b'Username')
        self.telnet.write(userpass.encode('ascii'))
        self.telnet.write(enable.encode('ascii'))
        self.telnet.read_until(self.cisco_prompt.encode('ascii'))

        #remove cisco terminal length
        self.telnet.write(b'ter leng 0\n')
        self.telnet.read_until(self.cisco_prompt.encode('ascii'))
    def backup(self):
        self.telnet.write(b'show running-config\n')
        self.telnet.read_until(b'Building configuration...')

        #get entire configuration
        result = self.telnet.read_until(self.cisco_prompt.encode('ascii'))
        result = result.replace('\n','\r')

        return result
    def restore(self, backup):
        result = dict()
        configs = backup.split('\r')
        self.telnet.write(b'tclsh\r')
        self.telnet.write(b'puts [open restore-config.conf w+] {\r')
        for config in configs:
            self.telnet.read_until(b'+>')
            self.telnet.write(config.encode('ascii')+b'\r')
        self.telnet.read_until(b'+>')
        self.telnet.write(b'}\r')
        self.telnet.read_until(b'(tcl)')
        self.telnet.write(b'tclquit\r')
        hasil = self.telnet.read_until(self.cisco_prompt.encode('ascii'))

        #execute restore command
        self.telnet.write(b'configure replace flash:restore-config.conf\r')
        time.sleep(1)
        self.telnet.write(b'y\r')

        return True
    def close(self):
        self.telnet.close()
class ConfigSSH:
    def __init__(self, ip, device_type, username, password, secret, hostname):
        credential = {
                'ip' : ip,
                'device_type' : device_type,
                'username' : username,
                'password' : password,
                'secret' : secret,
                }

        self.hostname = hostname
        self.credential = credential
        self.conn = ConnectHandler(**credential)
    def backup(self):
        #if there is any secret password
        if self.credential['secret'] != None:
            self.conn.enable()

        #grab current config
        config_output = self.conn.send_command('show running-config')
        result = config_output.replace('\n','\r')

        return result
    def restore(self, config):
        if self.credential['secret'] != None:
            self.conn.enable()

        #create tcl script on router
        self.conn.send_command('tclsh', expect_string='')
        self.conn.send_command('puts [open restore-config.conf w+] {\r%s}' % config)
        self.conn.send_command('tclquit', expect_string='')

        #restore config to system
        self.conn.send_command('configure replace flash:restore-config.conf\ry\r\r')
        return True
    def close(self):
        self.conn.disconnect()
