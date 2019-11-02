oid_inventory = {
    "sysdesc": {
        "Cisco": "1.3.6.1.2.1.1.1.0",
        "Juniper": "1.3.6.1.2.1.1.1.0",
        "General": "1.3.6.1.2.1.1.1.0"
    },
    "hostname": {
        "Cisco": "1.3.6.1.2.1.1.5.0",
        "Juniper": "1.3.6.1.2.1.1.5.0",
        "General": "1.3.6.1.2.1.1.5.0"
    },
    "location": {
        "General": "1.3.6.1.2.1.1.6.0"
    },
    "uptime": {
        "General": "1.3.6.1.2.1.1.3.0",
        "Cisco": "1.3.6.1.2.1.1.3.0",
        "Juniper": "1.3.6.1.2.1.1.3.0"
    },
    "cpu_util": {
        "Cisco": ".1.3.6.1.4.1.9.9.109.1.1.1.1.8.1",
        "Juniper": "1.3.6.1.4.1.2636.3.1.13.1.8.9.1.0.0"
    },
    "mem_util_used": {
        "Cisco": ".1.3.6.1.4.1.9.9.48.1.1.1.5.1",
        "Juniper": "1.3.6.1.4.1.2636.3.1.13.1.11.9.1.0.0"
    },
    "mem_util_free": {
        "Cisco": ".1.3.6.1.4.1.9.9.48.1.1.1.6.1",
        "Juniper": "1.1.1"
    },
    "total_memory": {
        "Cisco": "1.1.1",
        "Juniper": "1.3.6.1.4.1.2636.3.1.13.1.15.9.1.0.0"
    },
    "ip_addr":{
        "Cisco": ".1.3.6.1.2.1.4.20.1.1",
        "Juniper": ".1.3.6.1.2.1.4.20.1.1"
    },
    "ip_addr_index":{
        "Cisco": "1.3.6.1.2.1.4.20.1.2",
        "Juniper": "1.3.6.1.2.1.4.20.1.2"
    },

    "if_number": {
        "Cisco": ".1.3.6.1.2.1.2.1.0",
        "Juniper": ".1.3.6.1.2.1.2.1.0"
    },
    "if_name":{
        "Cisco":".1.3.6.1.2.1.31.1.1.1.1",
        "Juniper":".1.3.6.1.2.1.31.1.1.1.1"
    },
    "if_descr":{
        "Cisco":".1.3.6.1.2.1.2.2.1.2",
        "Juniper":".1.3.6.1.2.1.2.2.1.2"
    },
    "if_type":{
        "Cisco":".1.3.6.1.2.1.2.2.1.3",
        "Juniper":".1.3.6.1.2.1.2.2.1.3"
    },
    "if_mtu":{
        "Cisco":".1.3.6.1.2.1.2.2.1.4",
        "Juniper":".1.3.6.1.2.1.2.2.1.4"
    },
    "if_speed":{
        "Cisco":".1.3.6.1.2.1.2.2.1.5",
        "Juniper":".1.3.6.1.2.1.2.2.1.5"
    },
    "if_address":{
        "Cisco":".1.3.6.1.2.1.2.2.1.6",
        "Juniper":".1.3.6.1.2.1.2.2.1.6"
    },
    "if_InDisc":{
        "Cisco":".1.3.6.1.2.1.2.2.1.13",
        "Juniper":".1.3.6.1.2.1.2.2.1.13"
    },
    "if_OutDisc":{
        "Cisco":".1.3.6.1.2.1.2.2.1.19",
        "Juniper":".1.3.6.1.2.1.2.2.1.19"
    },
    "if_InErrors":{
        "Cisco":".1.3.6.1.2.1.2.2.1.14",
        "Juniper":".1.3.6.1.2.1.2.2.1.14"
    },
    "if_OutErrors":{
        "Cisco":".1.3.6.1.2.1.2.2.1.20",
        "Juniper":".1.3.6.1.2.1.2.2.1.20"
    },
    "if_InOctets":{
        "Cisco":".1.3.6.1.2.1.2.2.1.10",
        "Juniper":".1.3.6.1.2.1.2.2.1.10"
    },
    "if_OutOctets":{
        "Cisco":".1.3.6.1.2.1.2.2.1.16",
        "Juniper":".1.3.6.1.2.1.2.2.1.16"
    },
    "if_OperStatus":{
        "Cisco":".1.3.6.1.2.1.2.2.1.8",
        "Juniper":".1.3.6.1.2.1.2.2.1.8"
    },
    "if_AdminStatus":{
        "Cisco":".1.3.6.1.2.1.2.2.1.7",
        "Juniper":".1.3.6.1.2.1.2.2.1.7"
    },
    "if_InUcastPkts":{
        "Cisco":".1.3.6.1.2.1.2.2.1.11",
        "Juniper":".1.3.6.1.2.1.2.2.1.11"
    },
    "if_OutUcastPkts":{
        "Cisco":".1.3.6.1.2.1.2.2.1.17",
        "Juniper":".1.3.6.1.2.1.2.2.1.17"
    }
}


class OIDInventory:
    def get_oid(self, oid_string, vendor):
        if oid_string in oid_inventory.keys():
            return oid_inventory[oid_string][vendor]
        else:
            print ("oid_string not registered...")
            return ""

if_type_map = {
    1: "ther",
    2: "egular1822",
    3: "dh1822",
    4: "dnX25",
    5: "fc877x25",
    6: "thernetCsmacd",
    7: "so88023Csmacd",
    8: "so88024TokenBus",
    9: "so88025TokenRing",
    10: "iso88026Man",
    11: "starLan",
    12: "proteon10Mbit",
    13: "proteon80Mbit",
    14: "hyperchannel",
    15: "fddi",
    16: "lapb",
    17: "sdlc",
    18: "ds1",
    19: "e1",
    20: "basicISDN",
    21: "primaryISDN",
    22: "propPointToPointSerial",
    23: "ppp",
    24: "softwareLoopback",
    25: "eon",
    26: "ethernet3Mbit",
    27: "nsip",
    28: "slip",
    29: "ultra",
    30: "ds3",
    31: "sip",
    32: "frameRelay",
    33: "rs232",
    34: "para",
    35: "arcnet",
    36: "arcnetPlus",
    37: "atm",
    38: "miox25",
    39: "sonet",
    40: "x25ple",
    41: "iso88022llc",
    42: "localTalk",
    43: "smdsDxi",
    44: "frameRelayService",
    45: "v35",
    46: "hssi",
    47: "hippi",
    48: "modem",
    49: "aal5",
    50: "sonetPath",
    51: "sonetVT",
    52: "smdsIcip",
    53: "propVirtual",
    54: "propMultiplexor",
    55: "ieee80212",
    56: "fibreChannel",
    57: "hippiInterface",
    58: "frameRelayInterconnect",
    59: "aflane8023",
    60: "aflane8025",
    61: "cctEmul",
    62: "fastEther",
    63: "isdn",
    64: "v11",
    65: "v36",
    66: "g703at64k",
    67: "g703at2mb",
    68: "qllc",
    69: "fastEtherFX",
    70: "channel",
    71: "ieee80211",
    72: "ibm370parChan",
    73: "escon",
    74: "dlsw",
    75: "isdns",
    76: "isdnu",
    77: "lapd",
    78: "ipSwitch",
    79: "rsrb",
    80: "atmLogical",
    81: "ds0",
    82: "ds0Bundle",
    83: "bsc",
    84: "async",
    85: "cnr",
    86: "iso88025Dtr",
    87: "eplrs",
    88: "arap",
    89: "propCnls",
    90: "hostPad",
    91: "termPad",
    92: "frameRelayMPI",
    93: "x213",
    94: "adsl",
    95: "radsl",
    96: "sdsl",
    97: "vdsl",
    98: "iso88025CRFPInt",
    99: "myrinet",
    100: "voiceEM",
    101: "voiceFXO",
    102: "voiceFXS",
    103: "voiceEncap",
    104: "voiceOverIp",
    105: "atmDxi",
    106: "atmFuni",
    107: "atmIma",
    108: "pppMultilinkBundle",
    109: "ipOverCdlc",
    110: "ipOverClaw",
    111: "stackToStack",
    112: "virtualIpAddress",
    113: "mpc",
    114: "ipOverAtm",
    115: "iso88025Fiber",
    116: "tdlc",
    117: "gigabitEthernet",
    118: "hdlc",
    119: "lapf",
    120: "v37",
    121: "x25mlp",
    122: "x25huntGroup",
    123: "transpHdlc",
    124: "interleave",
    125: "fast",
    126: "ip",
    127: "docsCableMaclayer",
    128: "docsCableDownstream",
    129: "docsCableUpstream",
    130: "a12MppSwitch",
    131: "tunnel",
    132: "coffee",
    133: "ces",
    134: "atmSubInterface",
    135: "l2vlan",
    136: "l3ipvlan",
    137: "l3ipxvlan",
    138: "digitalPowerline",
    139: "mediaMailOverIp",
    140: "dtm",
    141: "dcn",
    142: "ipForward",
    143: "msdsl",
    144: "ieee1394",
    145: "if-gsn",
    146: "dvbRccMacLayer",
    147: "dvbRccDownstream",
    148: "dvbRccUpstream",
    149: "atmVirtual",
    150: "mplsTunnel",
    151: "srp",
    152: "voiceOverAtm",
    153: "voiceOverFrameRelay",
    154: "idsl",
    155: "compositeLink",
    156: "ss7SigLink",
    157: "propWirelessP2P",
    158: "frForward",
    159: "rfc1483",
    160: "usb",
    161: "ieee8023adLag",
    162: "bgppolicyaccounting",
    163: "frf16MfrBundle",
    164: "h323Gatekeeper",
    165: "h323Proxy",
    166: "mpls",
    167: "mfSigLink",
    168: "hdsl2",
    169: "shdsl",
    170: "ds1FDL",
    171: "pos",
    172: "dvbAsiIn",
    173: "dvbAsiOut",
    174: "plc",
    175: "nfas",
    176: "tr008",
    177: "gr303RDT",
    178: "gr303IDT",
    179: "isup",
    180: "propDocsWirelessMaclayer",
    181: "propDocsWirelessDownstream",
    182: "propDocsWirelessUpstream",
    183: "hiperlan2",
    184: "propBWAp2Mp",
    185: "sonetOverheadChannel",
    186: "digitalWrapperOverheadChannel",
    187: "aal2",
    188: "radioMAC",
    189: "atmRadio",
    190: "imt",
    191: "mvl",
    192: "reachDSL",
    193: "frDlciEndPt",
    194: "atmVciEndPt",
    195: "opticalChannel",
    196: "opticalTransport",
    197: "propAtm",
    198: "voiceOverCable",
    199: "infiniband",
    200: "teLink",
    201: "q2931",
    202: "virtualTg",
    203: "sipTg",
    204: "sipSig",
    205: "docsCableUpstreamChannel",
    206: "econet",
    207: "pon155",
    208: "pon622",
    209: "bridge",
    210: "linegroup",
    211: "voiceEMFGD",
    212: "voiceFGDEANA",
    213: "voiceDID",
    214: "mpegTransport",
    215: "sixToFour",
    216: "gtp",
    217: "pdnEtherLoop1",
    218: "pdnEtherLoop2",
    219: "opticalChannelGroup",
    220: "homepna",
    221: "gfp",
    222: "ciscoISLvlan",
    223: "actelisMetaLOOP",
    224: "fcipLink",
    225: "rpr",
    226: "qam",
    227: "lmp",
    228: "cblVectaStar",
    229: "docsCableMCmtsDownstream",
    230: "adsl2",
    231: "macSecControlledIF",
    232: "macSecUncontrolledIF",
    233: "aviciOpticalEther",
    234: "atmbond",
    235: "voiceFGDOS",
    236: "mocaVersion1",
    237: "ieee80216WMAN",
    238: "adsl2plus",
    239: "dvbRcsMacLayer",
    240: "dvbTdm",
    241: "dvbRcsTdma",
    242: "x86Laps",
    243: "wwanPP",
    244: "wwanPP2",
    245: "voiceEBS",
    246: "ifPwType",
    247: "ilan",
    248: "pip",
    249: "aluELP",
    250: "gpon",
    251: "vdsl2",
    252: "capwapDot11Profile",
    253: "capwapDot11Bss",
    254: "capwapWtpVirtualRadio",
    255: "bits",
    256: "docsCableUpstreamRfPort",
    257: "cableDownstreamRfPort",
    258: "vmwareVirtualNic",
    259: "ieee802154",
    260: "otnOdu",
    261: "otnOtu",
    262: "ifVfiType",
    263: "g9981",
    264: "g9982",
    265: "g9983",
    266: "aluEpon",
    267: "aluEponOnu",
    268: "aluEponPhysicalUni",
    269: "aluEponLogicalLink",
    270: "aluGponOnu",
    271: "aluGponPhysicalUni",
    272: "vmwareNicTeam"
}

class IfTypeMap:
    def get_if_type(self, int_type):
        return if_type_map[int_type]

if_status_map = {
    1:	"up",
    2:	"down",
    3:	"testing"
}

class IfStatusMap:
    def get_if_status(self, int_status):
        return if_status_map[int_status]