import os, sys, json, requests
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from elasticsearch import Elasticsearch
from elasticquery import ElasticQuery, Aggregate, Query

class Netflow:
    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def format_results(self, results, data_type):
        data = {}
        data['statistic'] = results['aggregations'][data_type]['buckets']
        test_bytes = 0
        test_hits = 0
        for a in results['aggregations'][data_type]['buckets']:
            test_bytes = test_bytes + a['bytes_sum']['value']
            test_hits = test_hits + a['doc_count']
        data['total_bytes'] =test_bytes
        data['total_doc'] =test_hits
        return data

    def static_data(self, data_type):
        two_level_widget = ["src_ip_dst_ip",
                            "dst_ip_src_ip",
                            "src_ip_protocol",
                            "dst_ip_protocol",
                            "protocol_src_ip",
                            "protocol_dst_ip",
                            "org_src_port",
                            "org_dst_port",
                            "org_src_ip",
                            "org_dst_ip",
                            "geo_src_protocol"
                            ]
        index = "elastiflow*"
        uri_search = 'http://192.168.100.249:9200/' + index + '/doc/_search'
        headers = {'Content-Type': 'application/json'}
        if data_type in two_level_widget:
            if data_type == "src_ip_dst_ip":
                parent_key = "src_addr"
                child_key = "dst_addr"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "dst_ip_src_ip":
                parent_key = "dst_addr"
                child_key = "src_addr"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "src_ip_protocol":
                parent_key = "src_addr"
                child_key = "dst_port_name"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "dst_ip_protocol":
                parent_key = "dst_addr"
                child_key = "dst_port_name"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "protocol_src_ip":
                parent_key = "dst_port_name"
                child_key = "src_addr"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "protocol_dst_ip":
                parent_key = "dst_port_name"
                child_key = "dst_addr"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "org_src_port":
                parent_key = "client_autonomous_system"
                child_key = "dst_port_name"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "org_dst_port":
                parent_key = "client_autonomous_system"
                child_key = "src_port_name"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "org_src_ip":
                parent_key = "server_autonomous_system"
                child_key = "dst_addr"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "org_dst_ip":
                parent_key = "autonomous_system"
                child_key = "src_addr"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key

            elif data_type == "geo_src_protocol":
                parent_key = "src_country"
                child_key = "dst_port_name"
                parent_field = "flow." + parent_key
                child_field = "flow." + child_key


            """Simple Elasticsearch Query"""
            query = json.dumps({
                "size": 0,
                "aggregations": {
                    parent_key: {
                        "terms": {
                            "field": parent_field
                        },
                        "aggregations": {
                            "bytes_sum":{
                                 "sum": {"field": "flow.bytes"}
                            },
                            "group_by": {
                                "terms": {"field": child_field},
                                "aggregations": {
                                    "bytes_sum": {
                                        "sum": {"field": "flow.bytes"}
                                    }
                                }
                            }
                        }
                    }
                }
            })
            # query = json.dumps({
            #     "query": {
            #         # "match": {"message": string_search}
            #         "match_all": {}
            #     }
            # })
        else:
            geo = ["as_org"]
            if data_type in geo:
                parent_key = data_type
                parent_field = "flow." + "autonomous_system"

            else:
                parent_key = data_type
                parent_field = "flow."+parent_key


            query = json.dumps({
                "size": 0,
                "aggregations": {
                    parent_key: {
                        "terms": {
                            "field": parent_field,
                            "size": 10
                        },
                        "aggregations": {
                            "bytes_sum": {
                                "sum": {"field": "flow.bytes"}
                            }
                        }
                    }
                }
            })

        response = requests.get(uri_search, headers=headers, data=query)
        results = json.loads(response.text)
        results = self.format_results(results, parent_key)
        return results
