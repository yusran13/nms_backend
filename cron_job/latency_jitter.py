import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from config import *
from pymongo import MongoClient
from device_driver.cisco import *
from device_driver.juniper import *
from api_controller.link_controller import *
from datetime import datetime
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s - {%(pathname)s:%(lineno)d}', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

if os.getenv("NMS_CONFIG", "development") == "production":
    print ("Production environment")
    client = DevelopmentConfig

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
    device_controller = DeviceController(mongo_db, logging)
    link_controller = LinkController(mongo_db, logging)

    list_registered_link = list(mongo_db.link_devices.find())
    for link in list_registered_link:
        source_device = device_controller.get_device_by_id(link["src_id"])
        # print link
        try:
            device = {}
            device["ip"] = source_device["ip_mgmt"]
            device["vendor"] = source_device["vendor"]
            device["username"] = source_device["access_info"]["username"]
            device["password"] = source_device["access_info"]["password"]
            device["secret"] = source_device["access_info"]["secret"]
            device["method"] = source_device["access_info"]["method"]

            latency_sample = []

            if source_device["vendor"] == "Cisco":
                driver = CiscoDriver(device, logging)
                net_connect = driver.connect_remote()
                if net_connect:
                    ping_command = "ping {:s} source {:s}".format(link["dst_ip"], link["src_ip"])

                    for i in range(0, 5):
                        ping_result_ms = driver.ping_result(net_connect, ping_command)
                        if ping_result_ms:
                            latency_sample.append(ping_result_ms)

                    net_connect.disconnect()

            elif source_device["vendor"] == "Juniper":
                driver = JuniperDriver(device, logging)
                net_connect = driver.connect_remote()
                if net_connect:
                    ping_command = "ping {:s} source {:s} rapid".format(link["dst_ip"], link["src_ip"])
                    for i in range(0, 5):
                        ping_result_ms = driver.ping_result(net_connect, ping_command)
                        if ping_result_ms:
                            latency_sample.append(ping_result_ms)
                    net_connect.disconnect()

            if len(latency_sample)>0:
                latency, jitter = link_controller.latency_jitter_calculation(latency_sample)
                data= {}
                data["id_link"] = link["_id"]
                data["latency"] = latency
                data["jitter"] = jitter
                data["timestamp"] = datetime.now()
            else:
                data = {}
                data["id_link"] = link["_id"]
                data["latency"] = "Unknown"
                data["jitter"] = "Unknown"
                data["timestamp"] = datetime.now()
            # print data

            # TODO: tobe delete, only for demo
            import random
            data = {}
            data["id_link"] = link["_id"]
            data["latency"] = random.randint(5, 30)
            data["jitter"] = random.randint(5, 30)
            data["timestamp"] = datetime.now()

            link_controller.save_jitter(data)
        except:
            # TODO: tobe delete, only for demo
            import random
            data = {}
            data["id_link"] = link["_id"]
            data["latency"] = random.randint(5, 30)
            data["jitter"] = random.randint(5, 30)
            data["timestamp"] = datetime.now()

            link_controller.save_jitter(data)

if __name__ == "__main__":
    main()
