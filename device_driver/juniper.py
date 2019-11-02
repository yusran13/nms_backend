from netmiko import ConnectHandler

class JuniperDriver:
    def __init__ (self, device, logger):
        self.device = device
        self.logger = logger

        if self.device["method"] == "SSH":
            self.device["device_type"] = "juniper"
        elif self.device["method"] == "TELNET":
            self.device["device_type"] = "juniper"
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

    # return ping in millisecond
    def ping_result(self, net_connect, ping_command):
        self.logger.info("Trying " + ping_command)
        output = net_connect.send_command(ping_command)
        print output
        if "....." in output:
           self.logger.warning("PING RTO..!!!")
           average_ping = None

        elif "Can't assign requested address" in output:
           self.logger.warning("WRONG SOURCE IP!!!")
           average_ping = None
        else:
            self.logger.info("PING Success....")
            ping_response = output.split("=")
            print ping_response
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
        self.juniper_prompt = credential['username']+'@'+credential['hostname']
        self.juniper_prompt_oper = credential['username']+'@'+credential['hostname']+'>'
        self.juniper_prompt_conf = credential['username']+'@'+credential['hostname']+'#'
        self.juniper_init()
    def juniper_init(self):
        self.telnet.read_until(b'login:')
        self.telnet.write(self.credential['username'].encode('ascii')+b'\n')
        self.telnet.read_until(b'Password:')
        self.telnet.write(self.credential['password'].encode('ascii')+b'\n')
        self.telnet.read_until(self.juniper_prompt.encode('ascii'))
        self.telnet.write(b'cli\n')
        self.telnet.read_until(self.juniper_prompt_oper.encode('ascii'))
    def backup(self):
        self.telnet.write(b'show configuration | no-more\n')
        self.telnet.read_until(b'\n')
        self.telnet.read_until(b'\n')
        result = self.telnet.read_until(self.juniper_prompt_oper.encode('ascii'))
        result = result.replace('\n','\r')
        result = result.replace(self.juniper_prompt_oper, '')

        return result
    def restore(self, backup):
        self.telnet.write(b'start shell\n')
        self.telnet.read_until(b'%',1)
        self.telnet.write(b'cat <<"EOF" > /var/home/%s/restore-config.conf\r%s\r"EOF"\r' % (self.credential['username'].encode('ascii'), backup.encode('ascii')))

        self.telnet.read_until(b'%')
        self.telnet.write(b'exit\n')
        self.telnet.read_until(self.juniper_prompt_oper.encode('ascii'))
        self.telnet.write(b'configure\n')
        self.telnet.read_until(self.juniper_prompt_conf.encode('ascii'))
        self.telnet.write(b'load override /var/home/%s/restore-config.conf\n' % self.credential['username'].encode('ascii'))
        self.telnet.read_until(self.juniper_prompt_conf.encode('ascii'))
        self.telnet.write(b'commit\n')
        self.telnet.read_until(b'commit complete')

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
        #grab current config
        config_output = self.conn.send_command('show configuration')
        backup = config_output.replace('\n','\r')

        return backup
    def restore(self, config):
        juniper_conf = dict()

        #create file for restore configuration
        self.conn.send_command('start shell', expect_string='')
        self.conn.send_command('cat <<"EOF" > /var/home/%s/restore-config.conf\r%s\r"EOF"' % (self.credential['username'], config))
        self.conn.send_command('cli', expect_string='')

        #restore config to system
        self.conn.send_config_set(['load override /var/home/%s/restore-config.conf' % self.credential['username'],'commit'])

        return True
    def close(self):
        self.conn.disconnect()
