import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from pysnmp.hlapi import *
from pymongo import errors
from datetime import datetime
from api_controller.device_controller import DeviceController
import random
from library.oid_library import IfTypeMap, IfStatusMap


class SNMPCollector:

    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def save_device_utilization(self, cpu, memory_used, memory_free, sysuptime, device):
        try:
            data = {
                "hostname": device["hostname"],
                "vendor": device["vendor"],
                "cpu": cpu,
                "mem_used": memory_used,
                "mem_free": memory_free,
                "uptime": sysuptime,
                "timestamp": datetime.now()
            }
            self.db.device_utilization.insert_one(data)
        except errors.PyMongoError as e:
            print("Could not save device system info for device {:d} to database: {:s}".format(device['hostname'], e))
            raise

    def save_device_snmp_information(self, snmp_info, table_name):
        try:
            self.db[table_name].insert_one(snmp_info)
        except errors.PyMongoError as e:
            print("Could not save {:s} for device {:d} to database: {:s}".format(table_name, snmp_info['hostname'], e))
            raise

    def save_interface_data(self, device):
        try:
            # insert interface data to device_interface collection
            self.db.device_interface.insert_one(device)

            #update interface list to device_list collection, only selected field
            if_list = list()
            for intfc in device["interface_list"]:
                interface = {}
                interface["name"] = intfc["if_descr"]
                interface["ip_address"] = intfc["ip_address"]
                interface["status"] = IfStatusMap().get_if_status(int_status=int(intfc["if_AdminStatus"]))
                interface["type"] = IfTypeMap().get_if_type(int_type = int(intfc["if_type"]))
                if_list.append(interface)
            self.db.list_devices.update_one({"hostname": device['hostname']}, {"$set": {"if_list": if_list}})
        except errors.PyMongoError as e:
            print("Could not save device system info for device {:d} to database: {:s}".format(device['hostname'], e))
            raise

    def save_sysinfo_data(self, data):
        try:
            self.db.list_devices.update_one({"ip_mgmt": data["ip_mgmt"]}, {"$set": data})
        except errors.PyMongoError as e:
            print("Could not save device system info for device {:d} to database: {:s}".format(data['hostname'], e))
            raise

    def collect_device_component_snmp(self, device_list):
        for device in device_list:
            component_list = list()
            for (errorIndication,
                 errorStatus,
                 errorIndex,
                 varBinds) in nextCmd(SnmpEngine(),
                                      CommunityData(device["community"], mpModel=1),
                                      UdpTransportTarget((device["ip_address"], 161)),
                                      ContextData(),
                                      ObjectType(ObjectIdentity('ENTITY-MIB', 'entPhysicalName')),
                                      ObjectType(ObjectIdentity('ENTITY-MIB', 'entPhysicalDescr')),
                                      ObjectType(ObjectIdentity('ENTITY-MIB', 'entPhysicalSerialNum')),
                                      ObjectType(ObjectIdentity('ENTITY-MIB', 'entPhysicalFirmwareRev')),
                                      ObjectType(ObjectIdentity('ENTITY-MIB', 'entPhysicalSoftwareRev')),
                                    lexicographicMode=False):

                if errorIndication:
                    print(errorIndication)
                    break
                elif errorStatus:
                    print('%s at %s' % (errorStatus.prettyPrint(),
                                        errorIndex and varBinds[int(errorIndex)-1][0] or '?'))
                    break
                else:
                    component_dict = dict()
                    for varBind in varBinds:
                        component_dict[varBind[0].prettyPrint().split('.')[0].split("::")[1]] = str(varBind[1].prettyPrint())

                    component_list.append(component_dict)


            timestamp = datetime.now()

            component_snmp_dict = {
                "device_id": device["_id"],
                "timestamp": timestamp,
                "component_list": component_list
            }

            try:
                self.db.snmp_component.insert_one(component_snmp_dict)
            except errors.PyMongoError as e:
                print("Could not save component for device {:d} to database: {:s}".format(device['id'], e))
                raise

    def cron_cpu(self, data):
        data["timestamp"] = datetime.now()
        self.db.z_cpu.insert_one(data)

    def cron_memory(self, data):
        data["timestamp"] = datetime.now()
        self.db.z_memory.insert_one(data)

    def cron_int_util(self, data):
        data["timestamp"] = datetime.now()
        self.db.z_int_util.insert_one(data)

    def cron_int_pl(self, data):
        # TODO: RANDOM VALUE For Testing only, will be delete!!
        if not data["packet_loss_in"]:
            data["packet_loss_in"] = random.randint(0, 100)

        if not data["packet_loss_out"]:
            data["packet_loss_out"] = random.randint(0, 100)

        data["timestamp"] = datetime.now()
        self.db.z_int_pl.insert_one(data)

    def save_neighbor_data(self, neighbors_data):
        device_controller = DeviceController(self.db, self.logger)
        for neighbor in neighbors_data["neighbors"]:
            device = device_controller.check_device(neighbor["device_id"])
            if not device:
                neighbors_data["neighbors"].remove(neighbor)
        self.db.device_neighbor.insert_one(neighbors_data)
