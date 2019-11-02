from pymongo import errors
from netaddr import *
from datetime import datetime, timedelta
from easysnmp import Session
from easysnmp import EasySNMPTimeoutError
from library.oid_library import *
from library.device_library import *
import sys, os, re
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

device_inventory = DeviceTypeInventory()
invent = OIDInventory()
class DeviceSNMPCollector:

    def __init__(self, device, logger):
        self.device = device
        self.logger = logger

    #get device utilization(cpu, memory, uptime)
    def get_system_status(self):
        session = Session(hostname=str(self.device["ip_mgmt"]), community=self.device["snmp"]["community"], version=self.device["snmp"]["version"])
        timestamp = datetime.now()
        try:
            # print self.device["ip_mgmt"]
            cpu_util = session.get(invent.get_oid("cpu_util", self.device["vendor"])).value
            mem_util_used = session.get(invent.get_oid("mem_util_used", self.device["vendor"])).value
            mem_util_free = session.get(invent.get_oid("mem_util_free", self.device["vendor"])).value
            uptime = session.get(invent.get_oid("uptime", self.device["vendor"])).value
            uptime_date = (datetime.now() - timedelta(seconds=int(uptime) / 100)).strftime('%A, %d-%m-%Y, %H:%M:%S')
            mem_util_used = int(mem_util_used)
            #Normalization mempry in Percentation
            if self.device["vendor"]== "Cisco":
                mem_util_used = (mem_util_used*100)/(mem_util_used + int(mem_util_free))
                mem_util_free = 100-mem_util_used

            if self.device["vendor"] == "Juniper":
                mem_util_free = 100-int(mem_util_used)
            system_status_dict = {
                "hostname": self.device["hostname"],
                "vendor": self.device["vendor"],
                "cpu": cpu_util,
                "mem_used" : mem_util_used,
                "mem_free" : mem_util_free,
                "uptime": uptime_date,
                "timestamp": timestamp
            }
            self.logger.info("Finished collecting device utilization for device {:s}".format(self.device["hostname"]))

        except:
            self.logger.warning("Error collecting device utilization for device {:s}".format(self.device["hostname"]))
            system_status_dict = {
                "hostname": self.device["hostname"],
                "vendor": self.device["vendor"],
                "cpu": "N/A",
                "mem_used": "N/A",
                "mem_free": "N/A",
                "uptime": "N/A",
                "timestamp": timestamp
            }
        return system_status_dict

    def get_cpu_snmp(self):
        session = Session(hostname=str(self.device["ip_mgmt"]), community=self.device["snmp"]["community"], version=self.device["snmp"]["version"])
        try:
            cpu_util = session.get(invent.get_oid("cpu_util", self.device["vendor"])).value
            cpu_util = int(cpu_util)
            self.logger.info("Finished collecting CPU utilization for device {:s}".format(self.device["ip_mgmt"]))
        except:
            cpu_util = None
            self.logger.warning("Error collecting CPU utilization for device {:s}".format(self.device["ip_mgmt"]))

        #TODO: tobe delete, only for demo
        import random
        cpu_util = random.randint(10, 40)
        return cpu_util

    def get_memory_snmp(self):
        session = Session(hostname=str(self.device["ip_mgmt"]), community=self.device["snmp"]["community"], version=self.device["snmp"]["version"])
        try:
            mem_util_used = session.get(invent.get_oid("mem_util_used", self.device["vendor"])).value
            mem_util_used = int(mem_util_used)
            if self.device["vendor"] == "Cisco":
                mem_util_free = session.get(invent.get_oid("mem_util_free", self.device["vendor"])).value
                mem_util_used = (mem_util_used * 100) / (mem_util_used + int(mem_util_free))
                mem_util_free = 100 - mem_util_used
            elif self.device["vendor"] == "Juniper":
                mem_util_free = 100 - mem_util_used
            self.logger.info("Finished collecting Memory utilization for device {:s}".format(self.device["ip_mgmt"]))
        except:
            mem_util_used = None
            mem_util_free = None
            self.logger.warning("Error collecting Memory utilization for device {:s}".format(self.device["ip_mgmt"]))

        # TODO: tobe delete, only for demo
        import random
        mem_util_used = random.randint(10, 50)
        mem_util_free = 100 - mem_util_used
        return mem_util_used, mem_util_free

    def get_uptime_snmp(self):
        session = Session(hostname=str(self.device["ip_mgmt"]), community=self.device["snmp"]["community"], version=self.device["snmp"]["version"])
        try:
            uptime = session.get(invent.get_oid("uptime", self.device["vendor"])).value
            uptime_date = (datetime.now() - timedelta(seconds=int(uptime) / 100)).strftime('%A, %d-%m-%Y, %H:%M:%S')
            self.logger.info("Finished collecting System Uptime for device {:s}".format(self.device["ip_mgmt"]))
        except:
            uptime_date = None
            self.logger.warning("Error collecting System Uptime for device {:s}".format(self.device["ip_mgmt"]))
        return uptime_date

    # get interface list
    def get_interface(self):
        interface_list = []
        session = Session(hostname=str(self.device["ip_mgmt"]), community=self.device["snmp"]["community"], version=self.device["snmp"]["version"])
        timestamp = datetime.now()

        try:
            if_name = session.walk(invent.get_oid("if_name", self.device["vendor"]))
            if_descr = session.walk(invent.get_oid("if_descr", self.device["vendor"]))
            if_type = session.walk(invent.get_oid("if_type", self.device["vendor"]))
            if_mtu = session.walk(invent.get_oid("if_mtu", self.device["vendor"]))
            if_speed = session.walk(invent.get_oid("if_speed", self.device["vendor"]))
            if_address = session.walk(invent.get_oid("if_address", self.device["vendor"]))
            if_InDisc = session.walk(invent.get_oid("if_InDisc", self.device["vendor"]))
            if_OutDisc = session.walk(invent.get_oid("if_OutDisc", self.device["vendor"]))
            if_InErrors = session.walk(invent.get_oid("if_InErrors", self.device["vendor"]))
            if_OutErrors = session.walk(invent.get_oid("if_OutErrors", self.device["vendor"]))
            if_InOctets = session.walk(invent.get_oid("if_InOctets", self.device["vendor"]))
            if_OutOctets = session.walk(invent.get_oid("if_OutOctets", self.device["vendor"]))
            if_OperStatus = session.walk(invent.get_oid("if_OperStatus", self.device["vendor"]))
            if_AdminStatus = session.walk(invent.get_oid("if_AdminStatus", self.device["vendor"]))
            if_InUcastPkts = session.walk(invent.get_oid("if_InUcastPkts", self.device["vendor"]))
            if_OutUcastPkts = session.walk(invent.get_oid("if_OutUcastPkts", self.device["vendor"]))
            ip_addr_index = session.walk(invent.get_oid("ip_addr_index", self.device["vendor"]))


            for (a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) in zip(if_name, if_descr, if_type, if_mtu,if_speed, if_address, if_InDisc, if_OutDisc, if_InErrors, if_OutErrors, if_InOctets, if_OutOctets, if_OperStatus, if_AdminStatus, if_InUcastPkts, if_OutUcastPkts):
                stat = {}
                stat["if_name"] = a.value
                stat["if_descr"] = b.value
                stat["if_type"] = c.value
                stat["if_mtu"] = d.value
                stat["if_speed"] = e.value
                mac_addr = ':'.join('{:02x}'.format(ord(x)) for x in f.value)
                stat["if_address"] = mac_addr
                stat["if_InDisc"] = g.value
                stat["if_OutDisc"] = h.value
                stat["if_InErrors"] = i .value
                stat["if_OutErrors"] = j.value
                stat["if_InOctets"] = k.value
                stat["if_OutOctets"] = l.value
                stat["if_OperStatus"] = m.value
                stat["if_AdminStatus"] = n.value
                stat["if_InUcastPkts"] = o.value
                stat["if_OutUcastPkts"] = p.value
                stat["ip_address"] = ""

                for ip_index in ip_addr_index:
                    if b.oid_index == ip_index.value:
                        stat["ip_address"] = ip_index.oid_index
                interface_list.append(stat)

            data = {}
            data["hostname"] = self.device["hostname"]
            data["timestamp"] = timestamp
            data["interface_list"] = interface_list
            self.logger.info("Finished collecting interface data for device {:s}".format(self.device["ip_mgmt"]))
            return data

        except:
            data = {}
            data["hostname"] = self.device["hostname"] if "hostname" in self.device.keys() else None
            data["timestamp"] = timestamp
            data["interface_list"] = False
            self.logger.warning("Error collecting interface data for device {:s}".format(self.device["ip_mgmt"]))
            return data

    #get sysInfo (hostname, description, uptime, os_version, vendor)
    def get_sysinfo(self):
        try:
            session = Session(hostname=str(self.device["ip_mgmt"]), community=self.device["snmp"]["community"],
                              version=self.device["snmp"]["version"])

            sysdesc = session.get(invent.get_oid("sysdesc", "General")).value
            hostname_snmp = session.get(invent.get_oid("hostname", "General")).value
            # norm hostname split by "."
            hostname = hostname_snmp.split(".")[0]

            # finding vendor brand
            if sysdesc.find("Cisco") >= 0:
                vendor = "Cisco"
            elif sysdesc.find("Juniper") >= 0:
                vendor = "Juniper"
            else:
                vendor = "General"

            # finding device uptime_date
            uptime = session.get(invent.get_oid("uptime", vendor)).value
            uptime_date = (datetime.now() - timedelta(seconds=int(uptime) / 100)).strftime('%A, %d-%m-%Y, %H:%M:%S')

            hw_type = self.get_hardware_type(vendor, sysdesc.split(",")[1])
            sw_version = self.get_software_version(vendor, sysdesc.split(",")[2])
            device_type = device_inventory.get_device_type(vendor, hw_type)

            if_descr = session.walk(invent.get_oid("if_descr", vendor))
            ip_addrs = session.walk(invent.get_oid("ip_addr_index", vendor))
            if_list = list()
            for name in if_descr:
                # if_list.append(name.value)
                interface = {}
                interface["name"] = name.value
                interface["ip_address"] = None
                for ip_addr in ip_addrs:
                    if name.oid_index == ip_addr.value:
                        interface["ip_address"] = ip_addr.oid_index

                if_list.append(interface)

            data_dict = {
                "ip_mgmt": self.device["ip_mgmt"],
                "discovered": True,
                "hostname": hostname,
                "sysDescr": sysdesc,
                "vendor": vendor,
                "uptime_date": uptime_date,
                "hw_type": hw_type,
                "sw_version": sw_version,
                "type": device_type,
                "if_list": if_list
            }

            self.logger.info("Finished collecting system info for device {:s}".format(self.device["ip_mgmt"]))

        except:
            data_dict = {
                "ip_mgmt": self.device["ip_mgmt"],
                "discovered": False
            }
            self.logger.warning("Error collecting system info for device {:s}, snmp not discovered".format(self.device["ip_mgmt"]))
        return data_dict

    def get_software_version(self, vendor, description):
        if vendor == "Cisco":
            software = re.search(r'(?<=Version ).*$', description).group(0)
            return software

        elif vendor == "Juniper":
            software = re.search(r'JUNOS [a-zA-Z0-9.]*', description).group(0)
            return software

    def get_hardware_type(self, vendor, description):
        if vendor == "Cisco":
            hardware = re.search(r"\((.*)\)", description).group(1)
            tipe = hardware.split("-")[0]
            return tipe

        elif vendor == "Juniper":
            tipe = re.search(r'(?<=Inc. ).*$', description).group(0)
            return tipe

    def norm_cisco_cdp_ip(self, list_of_int):
        k = 0
        adder = 0
        ip_addr = list()
        for x in list_of_int:
            if x == 195:
                adder = 64
            elif x == 194:
                adder = 0
            else:
                ip_addr.append(str(x + adder))
                adder = 0
        return ip_addr

    def get_lldp_local_int_index_from_rem_oid(self, oid):
        oid_components = oid.split(".")
        return oid_components[len(oid_components)-2]

    def get_lldp_local_int_index_from_loc_oid(self, oid):
        oid_components = oid.split(".")
        return oid_components[len(oid_components)-1]

    def collect_dev_neighbor_snmp(self):
        session = Session(hostname=self.device["ip_mgmt"], community=self.device["snmp"]["community"], version=2)

        neighbor_dict = dict()

        # get neighbor via cdp
        cdp_interface_name_items = ""
        try:
            cdp_interface_name_items = session.walk('.1.3.6.1.4.1.9.9.23.1.1.1.1.6')
        except EasySNMPTimeoutError as e:
            self.logger.warning("error when getting cdpInterfaceName to device {:s}".format(self.device["ip_mgmt"]))
            self.logger.warning(e.message)

        interface_dict = dict()
        neighbor_dict["neighbors"] = list()

        if cdp_interface_name_items:
            for item in cdp_interface_name_items:
                interface_dict[item.oid_index] = item.value.encode('utf-8')

            cdp_cache_address_items = session.walk('.1.3.6.1.4.1.9.9.23.1.2.1.1.4')

            cache_address_list = list()

            ip_addr_raw_list = list()
            for item in cdp_cache_address_items:
                ip_addr_raw = list()
                for x in item.value.encode('utf-8'):
                    ip_addr_raw.append(ord(x))
                ip_addr_raw_list.append(ip_addr_raw)

            ip_addr_list = list()
            for ip_addr_raw in ip_addr_raw_list:
                ip_addr_list.append(".".join(self.norm_cisco_cdp_ip(ip_addr_raw)))

            for item in cdp_cache_address_items:
                cache_address_list.append(item.value.encode('utf-8'))

            cdp_cache_device_id_items = session.walk('.1.3.6.1.4.1.9.9.23.1.2.1.1.6')

            cache_device_id_list = list()

            for item in cdp_cache_device_id_items:
                cache_device_id_list.append(item.value.encode('utf-8'))

            cdp_cache_device_port_items = session.walk('.1.3.6.1.4.1.9.9.23.1.2.1.1.7')

            cache_device_port_list = list()
            cache_device_port_idx_list = list()

            for item in cdp_cache_device_port_items:
                cache_device_port_list.append(item.value.encode('utf-8'))
                cache_device_port_idx_list.append(item.oid_index.split('.')[0])

            cdp_cache_platform_items = session.walk('.1.3.6.1.4.1.9.9.23.1.2.1.1.8')

            cache_platform_list = list()

            for item in cdp_cache_platform_items:
                cache_platform_list.append(item.value.encode('utf-8'))

            neighbor_dict["interface_list"] = interface_dict

            for i in range (0, len(cache_device_id_list)):
                try:
                    device_id = cache_device_id_list[i]
                except errors:
                    device_id = ""
                try:
                    address_raw = cache_address_list[i]
                except errors:
                    address_raw = ""
                try:
                    address = ip_addr_list[i]
                except errors:
                    address = ""
                try:
                    device_port = cache_device_port_list[i]
                except errors:
                    device_port = ""
                try:
                    device_platform = cache_platform_list[i]
                except errors:
                    device_platform = ""
                try:
                    local_port = interface_dict[cache_device_port_idx_list[i]]
                except:
                    local_port
                cdp_cache_dict = {
                    "device_id": device_id,
                    "address": address,
                    "address_raw": address_raw,
                    "device_port": device_port,
                    "device_platform": device_platform,
                    "local_port": local_port,
                    "source": "cdp"
                }

                neighbor_dict["neighbors"].append(cdp_cache_dict)
        else:
            neighbor_dict["neighbors"] = list()

        # get neighbor via lldp
        lldp_neighbor_list = ""
        try:
            lldp_neighbor_list = session.walk(oids=u'1.0.8802.1.1.2.1.4.1.1')
        except EasySNMPTimeoutError as e:
            self.logger.warning("error when getting lldp neighbor list to device {:s}".format(self.device["ip_mgmt"]))
            self.logger.warning(e.message)
        lldp_neighbor_int_list = [x for x in lldp_neighbor_list if x.oid.startswith('iso.0.8802.1.1.2.1.4.1.1.8')]
        lldp_neighbor_hostname_list = [x for x in lldp_neighbor_list if x.oid.startswith('iso.0.8802.1.1.2.1.4.1.1.9')]
        lldp_neighbor_platform_list = [x for x in lldp_neighbor_list if x.oid.startswith('iso.0.8802.1.1.2.1.4.1.1.10')]
        lldp_local_interface_list = ""
        try:
            lldp_local_interface_list = session.walk(oids=u'1.0.8802.1.1.2.1.3.7.1.4')
        except EasySNMPTimeoutError as e:
            self.logger.warning("error when getting lldp local interface list to device {:s}".format(self.device["ip_mgmt"]))
            self.logger.warning(e.message)
        local_interfaces_dict = dict()
        for local_interface in lldp_local_interface_list:
            local_interfaces_dict[self.get_lldp_local_int_index_from_loc_oid(local_interface.oid)] = local_interface.value
        lldp_neighbor_address_list = ""
        try:
            lldp_neighbor_address_list = session.walk(oids=u'1.0.8802.1.1.2.1.4.2.1.3')
        except EasySNMPTimeoutError as e:
            self.logger.warning("error when getting lldp neighbor list to device {:s}".format(self.device["ip_mgmt"]))
            self.logger.warning(e.message)
        lldp_neighbor_address_dict = dict()
        print(self.device['hostname'])
        print('LLDP neightbor address list')
        print(lldp_neighbor_address_list)
        for lldp_neighbor_address in lldp_neighbor_address_list:
            oid_components = lldp_neighbor_address.oid.split('.')
            key = oid_components[len(oid_components)-8]
            ip_address = ".".join(oid_components[len(oid_components)-4 : len(oid_components)])
            lldp_neighbor_address_dict[key] = ip_address
        print('-------')
        print(lldp_neighbor_hostname_list)
        print('-------')
        print(lldp_neighbor_address_dict)
        for idx, hostname in enumerate(lldp_neighbor_hostname_list):
            try:
                lldp_dict = {
                    "device_id": hostname.value,
                    "address": lldp_neighbor_address_dict[self.get_lldp_local_int_index_from_rem_oid(hostname.oid)],
                    "address_raw": "",
                    "device_port": lldp_neighbor_int_list[idx].value,
                    "device_platform": lldp_neighbor_platform_list[idx].value,
                    "local_port": local_interfaces_dict[self.get_lldp_local_int_index_from_rem_oid(hostname.oid)],
                    "source": "lldp"
                }
                neighbor_dict["neighbors"].append(lldp_dict)
            except:
                pass



        timestamp = datetime.now()
        neighbor_dict["timestamp"] = timestamp
        neighbor_dict["device_id"] = self.device["hostname"]
        return neighbor_dict
        # try:
        #     self.db.cdp_neighbor.insert_one(neighbor_dict)
        # except errors.PyMongoError as e:
        #     print("Could not save cdp neighbor for device {:d} to database: {:s}".format(device['id'], e))
        #     raise

    def get_spesific_interface(self, interface_name):
        data = self.get_interface()["interface_list"]
        if data:
            for interface in data:
                if interface["if_descr"] == interface_name:
                    return interface
            return None
        else:
            return None

    def get_interface_packetloss(self, interface_name):
        data = self.get_interface()["interface_list"]
        if data:
            for interface in data:
                if interface["if_descr"] == interface_name:
                    packet_loss = dict()
                    try:
                        packet_loss_in = float(int(interface["if_InDisc"]) * 100 / (int(interface["if_InDisc"]) + int(interface["if_InUcastPkts"])))
                    except:
                        packet_loss_in = 0

                    try:
                        packet_loss_out = float(int(interface["if_OutDisc"]) * 100 / (int(interface["if_OutDisc"]) + int(interface["if_OutUcastPkts"])))
                    except:
                        packet_loss_out = 0

                    packet_loss["packet_loss_in"] = packet_loss_in
                    packet_loss["packet_loss_out"] = packet_loss_out

                    return packet_loss
            return None
        else:
            return None
