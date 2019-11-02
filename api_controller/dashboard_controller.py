import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from bson import ObjectId
from collector.device_snmp_collector import DeviceSNMPCollector
import random
from datetime import datetime, timedelta
from device_controller import DeviceController
import requests


class DashboardController:
    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def register_dashboard(self, parms):
        device_controller = DeviceController(self.db, self.logger)
        parms["date_created"] = datetime.now()
        if len(parms["widget"]):
            for widget in parms["widget"]:
                #check if job already exist or not
                if widget["data_type"] == "cpu":
                    job_id = self.db.jobs.find_one({"device_id": widget["device_id"], "data_type": "cpu"}, {"_id": 1})

                elif widget["data_type"] == "memory":
                    job_id = self.db.jobs.find_one({"device_id": widget["device_id"], "data_type": "memory"}, {"_id": 1})
                elif widget["data_type"] == "interface_util":
                    job_id = self.db.jobs.find_one({"device_id": widget["device_id"], "data_type": "interface_util", "int_name": widget["int_name"]},
                                                   {"_id": 1})
                elif widget["data_type"] == "interface_pl":
                    job_id = self.db.jobs.find_one({"device_id": widget["device_id"], "data_type": "interface_pl",
                                                    "int_name": widget["int_name"]}, {"_id": 1})

                if job_id:
                    self.logger.info("Job already exist")
                    widget["job_id"] = str(job_id["_id"])

                else:
                    widget["device"] = device_controller.get_device_snmp_parm(ObjectId(widget["device_id"]))
                    if widget["device"]:
                        #insert job to database
                        insert_id = self.db.jobs.insert_one(widget)
                        widget["job_id"] = str(insert_id.inserted_id)
                        del [widget["_id"]]
                        requests.post("http://localhost:4243/api/job/new", json=widget, verify=False)
                        del widget["device"]
                        self.logger.info("New Job, insert to database")
                    else:
                        self.logger.info("Device not found")
        self.db.dashboard.insert_one(parms)

    def widget_data(self, parms):
        if parms["data_type"] == "cpu":
            db_collection = self.db["z_cpu"]
            match_query = {
                "device_id": parms["device_id"]
            }
            project_query = {
                        "device_id":0, "_id": 0
            }
            limit = parms["limit"]
        elif parms["data_type"] == "memory":
            db_collection = self.db["z_memory"]
            match_query = {
                "device_id": parms["device_id"]
            }
            project_query = {
                "device_id": 0, "_id": 0
            }
            limit = parms["limit"]
        elif parms["data_type"] == "interface_util":
            db_collection = self.db["z_int_util"]
            match_query = {
                "device_id": parms["device_id"],
                "interface_name": parms["int_name"]
            }
            project_query = {
                "device_id": 0, "_id": 0, "interface_name":0
            }
            limit = parms["limit"]+1
        elif parms["data_type"] == "interface_pl":
            db_collection = self.db["z_int_pl"]
            match_query = {
                "device_id": parms["device_id"],
                "interface_name": parms["int_name"]
            }
            project_query = {
                "device_id": 0, "_id": 0, "interface_name": 0
            }
            limit = parms["limit"]

        #DB QUERY FOR REALTIME WIDGET
        if parms["time_series"][0]=="realtime":
            data = list(db_collection.aggregate([
                {
                    "$match": match_query
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$limit": limit
                },
                {
                    "$project":project_query
                }
            ]))

            #CLEANING THE DATA HERE
            if parms["data_type"] == "interface_util":
                data = self.get_interface_util(data)

            # elif parms["data_type"] == "interface_pl":
            #     data = self.get_interface_pl(data)

            data = self.norm_date(data)
            data.reverse()
            return data

        # DB QUERY FOR LAST X TIMESERIES WIDGET
        elif parms["time_series"][0]=="last":
            count_down = int(parms["time_series"][1])
            period = parms["time_series"][2]
            time_series = range(limit)
            if period == "hour":
                range_time = datetime.now() - timedelta(hours=count_down)
            elif period == "day":
                range_time = datetime.now() - timedelta(days=count_down)
            elif period == "week":
                range_time = datetime.now() - timedelta(weeks=count_down)
            elif period == "month":
                range_time = datetime.now() - timedelta(days=30*count_down)
            elif period == "year":
                range_time = datetime.now() - timedelta(days=365*count_down)

            match_query["timestamp"] = {"$gte": range_time}
            data = list(db_collection.aggregate([
                {
                    "$match": match_query
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$project": project_query
                }
            ]))

            #GET AMOUNT DATA BY LIMIT (DEFAULT = 60)
            if len(data)>limit:
                count = int(len(data)/limit)
                time_series = [data[a*count] for a in time_series]
            else:
                time_series = data

            # CLEANING THE DATA HERE
            if parms["data_type"] == "interface_util":
                time_series = self.get_interface_util(time_series)

            # elif parms["data_type"] == "interface_pl":
            #     time_series = self.get_interface_pl(time_series)

            time_series = self.norm_date(time_series)
            time_series.reverse()
            return time_series

        # DB QUERY FOR LAST TIME RANGE
        elif parms["time_series"][0]=="range":
            time_series = range(limit)
            date_from = datetime.strptime(parms["time_series"][1], '%Y-%m-%d')
            date_to = datetime.strptime(parms["time_series"][2], '%Y-%m-%d')

            match_query["timestamp"] = {
                            "$gte": date_from,
                            "$lte": date_to + timedelta(days=1)
                        }
            data = list(db_collection.aggregate([
                {
                    "$match": match_query
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$project": project_query
                }
            ]))
            # GET AMOUNT DATA BY LIMIT (DEFAULT = 60)
            if len(data) > limit:
                count = int(len(data) / limit)
                time_series = [data[a * count] for a in time_series]
            else:
                time_series = data

            # CLEANING THE DATA HERE
            if parms["data_type"] == "interface_util":
                time_series = self.get_interface_util(time_series)

            # elif parms["data_type"] == "interface_pl":
            #     time_series = self.get_interface_pl(time_series)

            time_series = self.norm_date(time_series)
            time_series.reverse()
            return time_series

    def norm_date(self, list):
        if len(list)>10:
            counter = len(list) /10
            for a in range (len(list)):
                if a%counter:
                    list[a]["timestamp"]=" "
        return list

    def get_interface_util(self, data):
        interface_util = list()
        for index in range(0, len(data)-1):
            delta_time = ((data[index]["timestamp"] - data[index+1]["timestamp"]).seconds)
            delta_in = int(data[index]["interface_util"]["if_InOctets"]) - int(data[index+1]["interface_util"]["if_InOctets"])
            delta_out = int(data[index]["interface_util"]["if_OutOctets"]) - int(data[index+1]["interface_util"]["if_OutOctets"])
            data_dict = {}
            data_dict["timestamp"] = data[index]["timestamp"]
            try:
                data_dict["util_in"] = (delta_in * 8 * 100)/ (delta_time * int(data[index]["interface_util"]["if_speed"]))
            except:
                data_dict["util_in"] = 0
            try:
                data_dict["util_out"] = (delta_out * 8 * 100)/ (delta_time * int(data[index]["interface_util"]["if_speed"]))
            except:
                data_dict["util_out"] = 0

            # TODO: FOR TESTING ONLY, WILL BE DELETED
            if not data_dict["util_in"]:
                data_dict["util_in"] = random.randint(0, 30)
            if not data_dict["util_out"]:
                data_dict["util_out"] = random.randint(0, 30)
            interface_util.append(data_dict)
        return interface_util

    def get_interface_pl(self, data):
        for interface in data:
            try:
                interface["packet_loss_in"] = float(int(interface["interface_util"]["if_InDisc"])*100/(int(interface["interface_util"]["if_InDisc"])+int(interface["interface_util"]["if_InUcastPkts"])))
            except:
                interface["packet_loss_in"] = 0
            try:
                interface["packet_loss_out"] = float(int(interface["interface_util"]["if_OutDisc"])*100/(int(interface["interface_util"]["if_OutDisc"])+int(interface["interface_util"]["if_OutUcastPkts"])))
            except:
                interface["packet_loss_out"] = 0
            # FOR TESTING ONLY, WILL BE DELETED
            if not interface["packet_loss_in"]:
                interface["packet_loss_in"] = random.randint(0, 30)
            if not interface["packet_loss_out"]:
                interface["packet_loss_out"] = random.randint(0, 30)

            del interface["interface_util"]
        return data
