library = {
    "Cisco":{
        "Switch": ["3750", "3500", "2970", "2950", "2940", "2900", "2960", "Catalyst Express 500", "9800", "9500", "9400", "9300", "9200", "6800", "4900", "3850", "3650", "Meraki-ms220" ],
        "SwitchL3": ["Nexus-9000", "NXOS", "Nexus-7000", "Nexus-6000", "Nexus-5000", "Nexus-4000", "Nexus-3000", "Nexus-2000", "Nexus-1000V", "3000", "3550", "3560", "3750", "4500", "6500", "7000", "6000", "9148" ],
        "Router": ["C1760", "C1751", "C1721", "C1711", "C1712", "C1701", "C1800", "C2800", "C2801", "C2811", "C2821", "C2851", "C2901", "C2911", "C2921", "2951", "C3825", "C3845", "C3925", "C3945", "3925E", "3945E", "2600XM",
                   "C3725", "C3745", "C2691", "C7201", "C7200", "7200VXR", "C7204", "C4000", "C4400", "C4451", "C1921", "C1905", "C4431", "C4331", "C4321", "C3800", "ASR-1000", "ASR-1001", "ASR-1002", "ASR-1004", "ASR-1006",
                   "ASR-1009", "ASR-1013", "ASR-9000", "ASR-5000", "VIOS"]
    },
    "Juniper": {
        "Switch":
            ["EX2200", "EX2200-C", "EX2300", "EX2300M", "EX2300-C", "EX3300", "EX3400", "EX4200", "EX4300", "EX4300M", "EX RPS", "EX4550", "EX4600", "EX4650",
             "EX9200", "EX9250", "QFX5100", "QFX5110", "QFX5120", "QFX5200-48Y", "QFX5200-32C", "QFX5210-64C", "QFX10002", "QFX10008", "QFX10016", "QFX5100",
             "QFX5110", "QFX5120", "QFX5200-48Y", "QFX5200-32C"],
        "Router":["ACX500", "ACX1000", "ACX1100", "ACX2100", "ACX2200", "ACX4000", "ACX5000", "ACX5400", "ACX6300", "CTP150", "CTP2008", "CTP2024", "CTP2056", "vmx internet router",
                  "MX5", "MX10", "MX40", "MX80", "MX104", "MX150", "MX204", "MX240", "MX480", "MX960", "MX2008", "MX2010", "MX2020", "MX10003", "MX10008", "MX10016",
                  "PTX1000", "PTX3000", "PTX5000", "PTX10001", "PTX10002", "PTX10008", "PTX10016", "T4000"]
    }

}

class DeviceTypeInventory:
    def get_device_type(self, vendor, hw_type):
        device_tipe = "Undefined"
        for tipe in library[vendor].keys():
            if hw_type in library[vendor][tipe]:
                device_tipe = tipe
                break
        return device_tipe