import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from config import *
from collector.device_snmp_saved import SNMPCollector
from pymongo import MongoClient
from collector.fping_tool import FpingTool
from collector.device_snmp_collector import DeviceSNMPCollector
from collector.topology_generator import TopologyGenerator

import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s - {%(pathname)s:%(lineno)d}', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


if os.getenv("NMS_CONFIG", "development") == "production":
    print ("Production environment")
    client = DevelopmentConfig

elif os.getenv("NMS_CONFIG", "development") == "jawdat_public":
    print ("Public environment")
    client = JawdatPublic


elif os.getenv("NMS_CONFIG", "development") == "localhost":
    print ("localhost environment")
    client = LocalConfig

else:
    print ("Development environment")
    client = DevelopmentConfig

def main():
    mongo_client = MongoClient(client.DB_SERVER, client.DB_PORT, connect=False)
    mongo_db = getattr(mongo_client, client.DB_COLLECTION)
    mongo_db.authenticate(client.DB_USERNAME, client.DB_PASSWORD)

    saver = SNMPCollector(mongo_db, logging)
    fping = FpingTool(mongo_db, logging)

    device_list = mongo_db.list_devices.find()

    for device in device_list:
        host = DeviceSNMPCollector(device, logging)

        sys_info = host.get_sysinfo()
        if sys_info["discovered"]:
            saver.save_sysinfo_data(sys_info)

        #collect device utilization
        cpu_util = host.get_cpu_snmp()
        memory_used, memory_free = host.get_memory_snmp()
        sys_uptime = host.get_uptime_snmp()
        if cpu_util or memory_used or memory_free or sys_uptime:
            saver.save_device_utilization(cpu_util, memory_used, memory_free, sys_uptime, device)

        #collect interface status
        device_interface = host.get_interface()
        if device_interface["interface_list"]:
            saver.save_interface_data(device_interface)

        fping.get_ping_time_from_collector(device)

        #collect device neighbour snmp, only discover when device use hostname
        if "hostname" in device.keys():
            neighbors = host.collect_dev_neighbor_snmp()
            saver.save_neighbor_data(neighbors)


if __name__ == "__main__":
    main()
