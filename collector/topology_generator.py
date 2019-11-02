

class TopologyGenerator:
    def __init__(self):
        pass

    def generateConnectionTable(self, neighbors_data_list):
        list_of_host = list()
        list_of_connection = list()
        for neighbors_data in neighbors_data_list:
            list_of_host.append(neighbors_data["device_id"])

        # print(list_of_host)

        for neighbors_data in neighbors_data_list:
            device_hostname = neighbors_data["device_id"]
            for neighbor in neighbors_data["neighbors"]:
                if neighbor["device_id"] in list_of_host:
                    found = 0
                    for connection in list_of_connection:
                        if {"hostname": neighbor["device_id"], "device_port": neighbor["device_port"]} in connection \
                            or {"hostname": device_hostname, "device_port": neighbor["local_port"]} in connection:
                        # if ".".join([neighbor["device_id"], neighbor["device_port"]]) in connection \
                        #     or ".".join([device_hostname, neighbor["local_port"]]) in connection:
                            if {"hostname": device_hostname, "device_port": neighbor["local_port"]} not in connection:
                             # if not ".".join([device_hostname, neighbor["local_port"]]) in connection:
                                connection.append({"hostname": device_hostname, "device_port": neighbor["local_port"]})
                             #    connection.append(".".join([device_hostname, neighbor["local_port"]]))
                            found = 1
                    if not found:
                        new_connection = list()
                        new_connection.append({"hostname": device_hostname, "device_port": neighbor["local_port"]})
                        new_connection.append({"hostname": neighbor["device_id"], "device_port": neighbor["device_port"]})
                        # new_connection.append(".".join([device_hostname, neighbor["local_port"]]))
                        # new_connection.append(".".join([neighbor["device_id"], neighbor["device_port"]]))
                        list_of_connection.append(new_connection)

        return list_of_connection

    def generateTopology(self, list_of_connection):
        list_of_node = list()
        list_of_edge = list()
        network_idx_counter = 0
        for connection in list_of_connection:
            if len(connection) == 2:
                # peer_1 = connection[0].split(".")
                # peer_2 = connection[1].split(".")
                peer_1 = connection[0]
                peer_2 = connection[1]
                # src_host = peer_1[0]
                # src_int = peer_1[1]
                # dst_host = peer_2[0]
                # dst_int = peer_2[1]
                src_host = peer_1["hostname"]
                src_int = peer_1["device_port"]
                dst_host = peer_2["hostname"]
                dst_int = peer_2["device_port"]
                if src_host not in list_of_node:
                    list_of_node.append(src_host)
                if dst_host not in list_of_node:
                    list_of_node.append(dst_host)
                edge = {
                    "src": {
                        "host": src_host,
                        "interface": src_int
                    },
                    "dst": {
                        "host": dst_host,
                        "interface": dst_int
                    }
                }
                list_of_edge.append(edge)
            elif len(connection) > 2:
                hub_name = "network_"+str(network_idx_counter)
                list_of_node.append(hub_name)
                for member in connection:
                    # member_split = member.split(".")
                    # src_host = member_split[0]
                    # src_int = member_split[1]
                    src_host = member["hostname"]
                    src_int = member["device_port"]
                    if src_host not in list_of_node:
                        list_of_node.append(src_host)
                    edge = {
                        "src": {
                            "host": src_host,
                            "interface": src_int
                        },
                        "dst": {
                            "host": hub_name,
                            "interface": ""
                        }
                    }
                    list_of_edge.append(edge)
                network_idx_counter += 1
        topology = {
            "nodes": list_of_node,
            "edges": list_of_edge
        }
        return topology

    def mergeTopology(self, new_topology, based_line_topology):
        # merge nodes
        if not based_line_topology:
            based_line_topology = {
                "nodes": "",
                "edges": ""
            }
        merge_nodes = list()
        for node in new_topology["nodes"]:
            found_node = ""
            found_node = [x for x in based_line_topology["nodes"] if x["host"] == node and x["status"] in ["existing","new"]]
            if found_node:
                merge_node = {
                    "host": node,
                    "status": "existing"
                }
            else:
                merge_node = {
                    "host": node,
                    "status": "new"
                }
            merge_nodes.append(merge_node)
        for node in based_line_topology["nodes"]:
            if node["status"] in ["existing","new"]:
                found_node = ""
                found_node = [x for x in new_topology["nodes"] if x == node["host"]]
                if not found_node:
                    merge_node = {
                        "host": node["host"],
                        "status": "missing"
                    }
                    merge_nodes.append(merge_node)
        # merge edge
        merge_edges = list()
        for edge in new_topology["edges"]:
            found_edge = ""
            found_edge = [x for x in based_line_topology["edges"] if x["src"]["host"]==edge["src"]["host"]
                          and x["src"]["interface"]==edge["src"]["interface"] and x["dst"]["host"]==edge["dst"]["host"]
                          and x["dst"]["interface"]==edge["dst"]["interface"] and x["status"] in ["existing","new"]]
            if found_edge:
                merge_edge = {
                    "src": edge["src"],
                    "dst": edge["dst"],
                    "status": "existing"
                }
            else:
                merge_edge = {
                    "src": edge["src"],
                    "dst": edge["dst"],
                    "status": "new"
                }
            merge_edges.append(merge_edge)
        for edge in based_line_topology["edges"]:
            if edge["status"] in ["existing","new"]:
                found_edge = ""
                found_edge = [x for x in new_topology["edges"] if x["src"]["host"]==edge["src"]["host"]
                              and x["src"]["interface"]==edge["src"]["interface"] and x["dst"]["host"]==edge["dst"]["host"]
                              and x["dst"]["interface"]==edge["dst"]["interface"]]
                if not found_edge:
                    merge_edge = {
                        "src": edge["src"],
                        "dst": edge["dst"],
                        "status": "missing"
                    }
                    merge_edges.append(merge_edge)
        merge_topology = {
            "nodes": merge_nodes,
            "edges": merge_edges
        }
        return merge_topology