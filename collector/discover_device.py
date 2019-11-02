import threading
from decimal import *
from netaddr import *
from easysnmp import Session
from library.oid_library import *
from device_snmp_collector import DeviceSNMPCollector



class ExportingThread(threading.Thread):

    def __init__(self, tipe, mulai, end, subnetmask, community, db_construct, logger):
        self.progress = 0
        self.discovered_list=[]
        self.tipe=tipe
        self.mulai=mulai
        self.end=end
        self.subnetmask=subnetmask
        self.community=community
        self.db = db_construct
        self.logger = logger
        super(self.__class__, self).__init__()

    def run(self):
        invent = OIDInventory()
        # Your exporting stuff goes here ...
        getcontext().prec = 5
        checked_device=0
        self.logger.info("Starting discover device with SNMP....")
        scan_list = []
        if self.tipe == "network":
            ip_list = IPNetwork(self.mulai+"/"+self.subnetmask)
            for ip in ip_list.iter_hosts():
                scan_list.append(ip)

        elif self.tipe == "range":
            ip_list = list(iter_iprange(self.mulai, self.end))
            for ip in ip_list:
                scan_list.append(ip)

        self.logger.info("Amount of IP address will scanned: {:d}".format(len(scan_list)))

        for ip in scan_list:
            checked_device+=1
            # print (str(ip))
            device = {}
            device["ip_mgmt"] = str(ip)
            device["snmp"] = {}
            device["snmp"]["version"] = 2
            device["snmp"]["community"] = self.community

            host = DeviceSNMPCollector(device, self.logger)
            sys_info = host.get_sysinfo()
            if sys_info["discovered"]:
                sys_info["snmp"] = {
                    "community": self.community,
                    "version": 2
                }

                if self.db.list_devices.find_one({"ip_mgmt": str(ip)}):
                    sys_info["exist"] = "Yes"
                else:
                    sys_info["exist"] = "No"
                # print sys_info
                self.discovered_list.append(sys_info)
                self.logger.info(sys_info)

            self.progress = Decimal(checked_device)/Decimal(len(scan_list))*100
            self.logger.info("Progress = {:f}".format(self.progress))

        self.logger.info("Finished discovering device with SNMP")


