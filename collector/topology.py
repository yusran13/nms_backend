from snmp_collector import SNMPCollector
from pymongo import MongoClient
from fping_tool import FpingTool
from syslog_catcher import SyslogCatcher
from datetime import datetime, timedelta

def main():
    mongo_client = MongoClient("192.168.100.145", 27017, connect=False)
    #mongo_client = MongoClient("52.221.203.29", 30003, connect=False)

    mongo_db = getattr(mongo_client, "cloud_nms")
    #mongo_db.authenticate("cloud_nms", "SoGcmNJDAB4ykz02nHVufOUFPU0Vhj")
    collector = SNMPCollector(mongo_db)

    device_list = mongo_db.list_devices.find()
    collector.collect_dev_neighbor_snmp_cisco(device_list)

    device_list = mongo_db.list_devices.find()
    cdp_data = collector.get_last_cdp_data(device_list)
    collector.get_hostname_cdp(cdp_data)

    device_list = mongo_db.list_devices.find()
    cdp_data = collector.get_last_cdp_data(device_list)
    collector.generate_topology(cdp_data)


if __name__ == "__main__":
    main()
