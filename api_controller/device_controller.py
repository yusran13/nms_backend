import os, sys, random
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from bson import ObjectId
from collector.device_snmp_collector import DeviceSNMPCollector
from datetime import datetime, timedelta


class DeviceController:
    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def add_new_location(self, location):
        location_list = list(self.db.list_location.distinct("name"))
        if location["name"] not in location_list:
            self.db.list_location.insert_one(location)
            self.logger.info("Successfully insert new location - {:s}".format(location["name"]))
            return True
        else:
            self.logger.info("Location {:s} is exist in database, operation canceled".format(location["name"]))
            return False

    def get_location_id(self, name):
        location = self.db.list_location.find_one({"name": name}, {"_id": 1})
        if location:
            return str(location["_id"])
        else:
            return False

    def get_location_name(self, id):
        location = self.db.list_location.find_one({"_id": ObjectId(id)}, {"name": 1})
        return location["name"]

    def check_device (self, hostname):
        device = self.db.list_devices.find_one({"hostname": hostname})
        if device:
            return True
        else:
            return False

    def add_single_device(self, device):
        list_ip = self.db.list_devices.distinct("ip_mgmt")
        if device["ip_mgmt"] not in list_ip:
            location_id = self.get_location_id(device["location"])
            if not location_id:
                self.add_new_location({"name": "Undefined", "coordinate": {"lat": "", "long": ""}})
                location_id = self.get_location_id("Undefined")
            device["location_id"] = location_id
            del device["location"]
            device["added_date"] = datetime.now()
            device["status"] = "DOWN"
            device["type"] = "Undefined"
            device["vendor"] = "Undefined"
            host = DeviceSNMPCollector(device, self.logger)
            sys_info = host.get_sysinfo()
            if sys_info["discovered"]:
                device["hostname"] = sys_info["hostname"]
                device["sysDescr"] = sys_info["sysDescr"]
                device["vendor"] = sys_info["vendor"]
                device["uptime_date"] = sys_info["uptime_date"]
                device["hw_type"] = sys_info["hw_type"]
                device["sw_version"] = sys_info["sw_version"]
                device["type"] = sys_info["type"]
                device["if_list"] = sys_info["if_list"]

            self.db.list_devices.insert_one(device)
            return True
        else:
            self.logger.info("Device with IP {:s} was exist in database".format(device["ip_mgmt"]))
            return False

    def save_device_list(self, list_device):
        # Get Undefined location id if exist, create if not
        location_id = self.get_location_id("Undefined")
        if not location_id:
            self.add_new_location({"name": "Undefined", "coordinate": {"lat": "", "long": ""}})
            location_id = self.get_location_id("Undefined")

        # save every device into db record
        for device in list_device:
             device["location_id"] = location_id
             device["added_date"] = datetime.now()
             device["status"] = "DOWN"
             del device["exist"]
             self.db.list_devices.insert_one(device)

    def get_all_device(self, group_by = None):
        if group_by == "location":
            all_devices = []
            locations = list(self.db.list_location.find({}, {"_id": 1, "name": 1}))

            for location in locations:
                data = {}
                data["location"] = location["name"]
                data["location_id"] = str(location["_id"])
                devices_list_dict = list(self.db.list_devices.find({"location_id": str(location["_id"])},
                                                                   {"hostname": 1, "ip_mgmt": 1, "status": 1}))
                data["devices"] = devices_list_dict
                all_devices.append(data)
            return all_devices

        elif group_by == "type":
            all_devices = []
            device_types = list(self.db.list_devices.distinct("type"))
            for device_type in device_types:
                data = {}
                data["device_type"] = device_type
                devices_list_dict = list(
                    self.db.list_devices.find({"type": device_type}, {"hostname": 1, "ip_mgmt": 1, "status": 1}))
                data["devices"] = devices_list_dict
                all_devices.append(data)
            return all_devices

        elif group_by == "vendor":
            all_devices = []
            device_vendor = list(self.db.list_devices.distinct("vendor"))

            for vendor in device_vendor:
                data = {}
                data["vendor"] = vendor
                devices_list_dict = list(
                    self.db.list_devices.find({"vendor": vendor}, {"hostname": 1, "ip_mgmt": 1, "status": 1}))
                data["devices"] = devices_list_dict
                all_devices.append(data)
            return all_devices

        else:
            device_list = list(self.db.list_devices.find())
            for device in device_list:
                if "location_id" in device.keys():
                    device["location"] = self.db.list_location.find_one({"_id": ObjectId(device["location_id"])})["name"]
            return device_list

    def get_device_detail(self, id):
        device = self.db.list_devices.find_one({"_id": ObjectId(id)})

        if not device:
            return False
        # try:
        if "location_id" in device.keys():
            device_location = self.db.list_location.find_one({"_id": ObjectId(device["location_id"])})
            if device_location:
                del device["location_id"]
                device["location_detail"] = device_location
                del device["location_detail"]["_id"]
            else:
                device["location_detail"] = {
                    "building": None,
                    "city": None,
                    "name": None,
                    "street": None,
                    "coordinate": {
                        "lat": None,
                        "long": None
                    }
                }
        # except:
        #     device = False
        return device

    def all_interface_util(self):
        devices = self.db.list_devices.find({}, {"hostname": 1})
        list_all_interface = []
        for device in devices:
            if "hostname" in device.keys():
                device_interface = list(self.db.device_interface.aggregate([
                {
                    "$match": {
                        "hostname": device["hostname"]
                    }
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$limit": 2
                }
            ]))

                if len(device_interface) == 2:
                    delta_time = (device_interface[0]["timestamp"] - device_interface[1]["timestamp"]).seconds

                    for a, b in zip(device_interface[0]["interface_list"], device_interface[1]["interface_list"]):
                        if int(a["if_speed"]):
                            interface_data = {}
                            interface_data["hostname"] = device["hostname"]
                            interface_data["interface"] = a["if_descr"]
                            delta_rx = int(a["if_InOctets"]) - int(b["if_InOctets"])
                            delta_tx = int(a["if_OutOctets"]) - int(b["if_OutOctets"])
                            interface_data["rx_util"] = (delta_rx * 8 * 100) / (delta_time * int(a["if_speed"]))
                            # TODO: RANDOM VALUE For Testing only, will be delete!!
                            if not interface_data["rx_util"]:
                                interface_data["rx_util"] = random.randint(0, 100)

                            interface_data["tx_util"] = (delta_tx * 8 * 100) / (delta_time * int(a["if_speed"]))
                            # TODO: RANDOM VALUE For Testing only, will be delete!!
                            if not interface_data["tx_util"]:
                                interface_data["tx_util"] = random.randint(0, 100)
                            list_all_interface.append(interface_data)

        return list_all_interface

    def get_device_id(self, hostname):
        device = self.db.list_devices.find_one({"hostname": hostname})
        if device:
            return device["_id"]
        else:
            self.logger.warning("Device not found, return False")
            return None

    def get_device_name(self, id):
        device = self.db.list_devices.find_one({"_id": ObjectId(id)})
        return device["hostname"] if device else None
        # else:
        #     self.logger.warning("Device not found, return False")
        #     return None

    def get_packet_loss(self, src_host, src_if, dst_host, dst_if):
        self.logger.info("Starting get link packet loss from {:s}-{:s} to {:s}-{:s}".
                    format(src_host, src_if, dst_host, dst_if))
        packet_loss = {
            "src": {},
            "dst": {}
        }
        #SRC_HOST
        vendor1 = self.db.list_devices.find_one({"hostname": src_host})["vendor"]
        if vendor1 == "Juniper":
            src_if = src_if+".0"
        data1 = list(self.db.device_interface.aggregate([
            {
                "$match": {"hostname": src_host}
            },
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$limit": 1
            },
            {
                "$project": {
                    "interface_list": {
                        "$filter": {
                            "input": '$interface_list',
                            "as": 'if',
                            "cond": {
                                "$eq": ['$$if.if_descr', src_if]
                            }
                        }
                    },
                    "timestamp": 1,
                    "vendor":1
                }
            }
        ]))[0]
        packet_loss["src"]["hostname"] = src_host
        packet_loss["src"]["interface"] = src_if
        packet_loss["src"]["timestamp"] = data1["timestamp"]
        packet_loss["src"]["pkt_in"] = data1["interface_list"][0]["if_InUcastPkts"]
        packet_loss["src"]["pkt_out"] = data1["interface_list"][0]["if_OutUcastPkts"]
        packet_loss["src"]["byte_in"] = data1["interface_list"][0]["if_InOctets"]
        packet_loss["src"]["byte_out"] = data1["interface_list"][0]["if_OutOctets"]

        # DST_HOST
        vendor2 = self.db.list_devices.find_one({"hostname": dst_host})["vendor"]
        if vendor2 == "Juniper":
            dst_if = dst_if + ".0"
        data2 = list(self.db.device_interface.aggregate([
            {
                "$match": {"hostname": dst_host}
            },
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$limit": 1
            },
            {
                "$project": {
                    "interface_list": {
                        "$filter": {
                            "input": '$interface_list',
                            "as": 'if',
                            "cond": {
                                "$eq": ['$$if.if_descr', dst_if]
                            }
                        }
                    },
                    "timestamp": 1
                }
            }
        ]))[0]
        packet_loss["dst"]["hostname"] = dst_host
        packet_loss["dst"]["interface"] = dst_if
        packet_loss["dst"]["timestamp"] = data2["timestamp"]
        packet_loss["dst"]["pkt_in"] = data2["interface_list"][0]["if_InUcastPkts"]
        packet_loss["dst"]["pkt_out"] = data2["interface_list"][0]["if_OutUcastPkts"]
        packet_loss["dst"]["byte_in"] = data2["interface_list"][0]["if_InOctets"]
        packet_loss["dst"]["byte_out"] = data2["interface_list"][0]["if_OutOctets"]
        packet_loss["timestamp"] = datetime.now()

        # self.db.link_packet_loss.insert_one(packet_loss)
        return packet_loss

    def get_device_by_id(self, id):
        device = self.db.list_devices.find_one({"_id": id})
        if device:
            return device
        else:
            self.logger.warning("Device not found, return False")
            return None

    def get_device_snmp_parm(self, id):
        device = self.db.list_devices.find_one({"_id": id})
        if device:
            data= {
                "ip_mgmt": device["ip_mgmt"],
                "snmp": device["snmp"],
                "vendor": device["vendor"],
                "hostname": device["hostname"]
            }
            return data
        else:
            self.logger.warning("Device not found, return False")
            return None

    def get_device_interface_detail(self, parms):
        device_interface = list(self.db.device_interface.aggregate([
            {
                "$match": {"hostname": parms["hostname"]}
            },
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$limit": parms["limit"] + 1
            },
            {
                "$project": {
                    "interface_list": {
                        "$filter": {
                            "input": '$interface_list',
                            "as": 'if',
                            "cond": {
                                "$eq": ['$$if.if_descr', parms["interface"]]
                            }
                        }
                    },
                    "timestamp": 1,
                    "vendor": 1
                }
            }
        ])
        )

        interface_stat = list()

        for a in range(0, parms["limit"]):
            # print ("Data index ke {:d}".format(a))
            stat = dict()
            stat["timestamp"] = "{:d}:{:02d}".format(device_interface[a]["timestamp"].hour,
                                                     device_interface[a]["timestamp"].minute)
            try:
                stat["packet_loss"] = ((int(device_interface[a]["interface_list"][0]["if_InDisc"]) + int(device_interface[a]["interface_list"][0]["if_OutDisc"])) * 100) / \
                                  ((int(device_interface[a]["interface_list"][0]["if_InDisc"]) + int(device_interface[a]["interface_list"][0]["if_OutDisc"])) +
                                   int(device_interface[a]["interface_list"][0]["if_InUcastPkts"]) + int(device_interface[a]["interface_list"][0]["if_OutUcastPkts"]))
            except:
                stat["packet_loss"] = 0
            # FOR TESTING ONLY, WILL BE DELETED
            if not stat["packet_loss"]:
                stat["packet_loss"] = random.randint(0, 100)
            delta_time = ((device_interface[a]["timestamp"] - device_interface[a + 1]["timestamp"]).seconds)
            delta_in = int(device_interface[a]["interface_list"][0]["if_InOctets"]) - int(
                device_interface[a + 1]["interface_list"][0]["if_InOctets"])
            delta_out = int(device_interface[a]["interface_list"][0]["if_OutOctets"]) - int(
                device_interface[a + 1]["interface_list"][0]["if_OutOctets"])
            try:
                stat["util_in"] = (delta_in * 8 * 100) / (delta_time * int(device_interface[a]["interface_list"][0]["if_speed"]))
            except:
                stat["util_in"] = 0
            # FOR TESTING ONLY, WILL BE DELETED
            if not stat["util_in"]:
                stat["util_in"] = random.randint(0, 100)
            try:
                stat["util_out"] = (delta_out * 8 * 100) / \
                               (delta_time * int(device_interface[a]["interface_list"][0]["if_speed"]))
            except:
                stat["util_out"] = 0
            # FOR TESTING ONLY, WILL BE DELETED
            if not stat["util_out"]:
                stat["util_out"] = random.randint(0, 100)
            interface_stat.append(stat)

        return interface_stat

    def device_health_summary(self):
        device_list = list(self.db.list_devices.find({}))

        # populate most recent timestamp
        device_status_list = list()
        undefined_status_device_list = list()
        treshold_datetime = datetime.now() - timedelta(days=1)
        for device in device_list:
            if "hostname" in device.keys():
                snmp_device_status = list(
                    self.db.device_utilization.aggregate([
                        {
                            "$match": {
                                "hostname": device["hostname"],
                                "timestamp": {"$gte": treshold_datetime}
                            }
                        },
                        {
                            "$sort": {"timestamp": -1}
                        },
                        {
                            "$limit": 1
                        }
                    ])
                )

                if len(snmp_device_status) == 0:
                    undefined_status_device_list.append(device)
                elif snmp_device_status[0]["cpu"]== None or snmp_device_status[0]["mem_used"] == None:
                    undefined_status_device_list.append(device)
                elif len(snmp_device_status) > 0:
                    device_status_list.append(snmp_device_status[0])
                else:
                    undefined_status_device_list.append(device)

            else:
                undefined_status_device_list.append(device)

        # decide healthy status
        critical_count = 0
        warning_count = 0
        healthy_count = 0
        for device_status in device_status_list:
            memory_util = int(device_status["mem_used"])
            device_status["memory_util"] = memory_util
            if memory_util > 70 or int(device_status["cpu"]) > 70:
                device_status["health_status"] = "critical"
                critical_count += 1
            elif memory_util > 40 or int(device_status["cpu"]) > 40:
                device_status["health_status"] = "warning"
                warning_count += 1
            else:
                device_status["health_status"] = "healthy"
                healthy_count += 1
        undefined_count = len(device_list) - len(device_status_list)
        ret_dict = {
            "device_status_detail": device_status_list,
            "undefined_status_device_list": undefined_status_device_list,
            "device_status_summary": {
                "critial": critical_count,
                "warning": warning_count,
                "healthy": healthy_count,
                "undefined": undefined_count
            }
        }

        return ret_dict

    def get_device_status_summary(self):
        status_list = list(
            self.db.list_devices.aggregate([
                {
                    '$group': {
                        '_id': "$status",
                        'count': {"$sum": 1}
                    }
                }
            ])
        )
        status_dict = dict()
        for status in status_list:
            status_dict[status["_id"]] = status["count"]

        up = status_dict["UP"] if "UP" in status_dict else 0
        down = status_dict["DOWN"] if "DOWN" in status_dict else 0
        total = up + down
        summary = {
            "up": up,
            "down": down,
            "total": total
        }
        return summary

    def get_device_packetloss(self, id):
        device = self.db.list_devices.find_one({"_id": ObjectId(id)})
        packet_loss = {}
        if device and 'hostname' in device.keys():
            device_data = list(
                self.db.device_interface.aggregate([
                    {
                        "$match": {"hostname": device["hostname"]}
                    },
                    {
                        "$sort": {"timestamp": -1}
                    },
                    {
                        "$limit": 1
                    }
                ])
            )
            sum_disc_in = 0
            sum_disc_out = 0
            sum_packet_in = 0
            sum_packet_out = 0

            for interface in device_data[0]["interface_list"]:
                sum_disc_in = sum_disc_in + int(interface["if_InDisc"])
                sum_disc_out = sum_disc_out + int(interface["if_OutDisc"])
                sum_packet_in = sum_packet_in + int(interface["if_InUcastPkts"])
                sum_packet_out = sum_packet_out + int(interface["if_OutUcastPkts"])

            packet_loss["hostname"] = device_data[0]["hostname"]
            packet_loss["avg"] = ((sum_disc_in + sum_disc_out) * 100) / (sum_disc_in + sum_disc_out + sum_packet_in + sum_packet_out)

            # TODO: tobe delete, only for demo
            import random
            packet_loss["avg"] = random.uniform(0, 20)

            packet_loss["timestamp"] = device_data[0]["timestamp"]
        return packet_loss

    def device_utilization(self, id):
        device = self.db.list_devices.find_one({"_id": ObjectId(id)})
        device_util = {}
        if device and 'hostname' in device.keys():
            hostname = device['hostname']
            utilization = list(
                self.db.device_utilization.aggregate([
                    {
                        "$match": {"hostname": hostname}
                    },
                    {
                        "$sort": {"timestamp": -1}
                    },
                    {
                        "$limit": 1
                    }
                ])
            )
            # print utilization

            if len(utilization) > 0:
                device_util["utilization"] = utilization[0]
            else:
                self.logger.info("Utilization data not found - Device {:s}".format(hostname))
                device_util["utilization"] = {
                    "mem_used": 0,
                    "cpu": 0
                }

        return device_util

    def get_device_response_time(self, id):
        avg_resp = list(
            self.db.device_response_time.aggregate([
                {
                    "$match": {"device_id": id}
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$limit": 1
                }
            ])
        )
        # response_time = {}
        if len(avg_resp) > 0:
            response_time = avg_resp[0]
        else:
            response_time = {}

        # TODO: tobe delete, only for demo
        import random
        response_time = random.uniform(0, 20)
        return response_time

    def get_device_list_by_hostname(self, list_hostname):
        if list_hostname:
            raw_list = list(self.db.list_devices.find({"hostname": {"$in": list_hostname}}, {"ip_mgmt":1, "_id":0}))
        else:
            raw_list = list(self.db.list_devices.find({}, {"ip_mgmt":1, "_id":0}))
        device_list = [a["ip_mgmt"] for a in raw_list]
        return device_list


    def get_device_list_by_locationid(self, list_id):
        if list_id:
            raw_list = list(self.db.list_devices.find({"location_id": {"$in": list_id}}, {"ip_mgmt":1, "_id":0}))
        else:
            raw_list = list(self.db.list_devices.find({}, {"ip_mgmt":1, "_id":0}))

        device_list = [a["ip_mgmt"] for a in raw_list]
        return device_list

    def get_device_hostname_by_ip (self, ip):
        device = self.db.list_devices.find_one({"ip_mgmt":ip})
        return device["hostname"]

    def get_device_location_by_ip (self, ip):
        device = self.db.list_devices.find_one({"ip_mgmt": ip})
        location_name = self.get_location_name(device["location_id"])
        return location_name

    def get_device_map_ip_hostname(self):
        device_map = {}
        devices = list(self.db.list_devices.find({}))
        for device in devices:
            device_map[device["ip_mgmt"]] = device["hostname"] if "hostname" in device.keys() else ""
        return device_map

    def get_location_map_ip_location(self):
        location_map = {}
        devices = list(self.db.list_devices.find({}))
        for device in devices:
            location_map[device["ip_mgmt"]] = self.get_location_name(device["location_id"])
        return location_map


