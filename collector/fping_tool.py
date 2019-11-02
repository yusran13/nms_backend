import shlex
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime
from pymongo import errors
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))


class FpingTool:
    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def get_simple_cmd_output(self, cmd, stderr=STDOUT):
        """
        Execute a simple external command and get its output.
        """
        args = shlex.split(cmd)
        return Popen(args, stdout=PIPE, stderr=stderr).communicate()[0]


    def get_ping_time_from_collector(self, host):
        ip = host['ip_mgmt'].split(':')[0]
        cmd = "fping {host} -C 3 -q".format(host=ip)
        res = [float(x) for x in self.get_simple_cmd_output(cmd=cmd).strip().split(':')[-1].split() if x != '-']
        len(res)
        timestamp = datetime.now()
        if len(res) > 0:
            avg = sum(res) / len(res)
            avg_response = {
                "hostname": host["hostname"] if "hostname" in host.keys() else None,
                "ip_address": host["ip_mgmt"],
                "timestamp": timestamp,
                "avg": avg,
                "device_id": str(host["_id"])
            }

            try:
                self.db.device_response_time.insert_one(avg_response)
                self.db.list_devices.update_one({"_id": host['_id']}, {"$set": {"status": "UP"}})
                self.logger.info("Device {:s} is UP, finished getting response time".format(host["hostname"]))
            except errors.PyMongoError as e:
                print("Could not save device response time ping for device {:d} to database: {:s}".format(host['hostname'], e))
                raise
        #IF RTO
        else:
            avg_response = {
                "hostname": host["hostname"] if "hostname" in host.keys() else None,
                "ip_address": host["ip_mgmt"],
                "timestamp": timestamp,
                "avg": 1000
            }
            try:
                self.db.device_response_time.insert_one(avg_response)
                # self.db.list_devices.update_one({"_id": host['_id']}, {"$set": {"status": "DOWN"}})
                self.db.list_devices.update_one({"_id": host['_id']}, {"$set": {"status": "UP"}})
                self.logger.warning("Device {:s} is DOWN, finished getting response time".format(host["ip_mgmt"]))
            except errors.PyMongoError as e:
                print("Could not save device response time ping for device {:d} to database: {:s}".format(host['ip_mgmt'], e))
                raise
